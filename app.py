import json
import os
import threading
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).parent
KB = json.loads((BASE_DIR / "knowledge.json").read_text(encoding="utf-8"))
SEEN = set()
AUDIT = []
LOCK = threading.Lock()

SENSITIVE = (
    "balance","transfer","account number","password","otp","fraud","stolen",
    "رصيد","تحويل","رقم الحساب","كلمة المرور","رمز","احتيال","مسروق"
)

def respond(text):
    clean=(text or "").strip()
    low=clean.lower()
    if any(term in low for term in SENSITIVE):
        return {"status":"escalated","answer":"This request needs an authorized representative. Do not share passwords, OTPs, or account credentials.","source":"Safety policy"}
    for item in KB:
        if any(k.lower() in low for k in item["keywords"]):
            return {"status":"answered","answer":item["answer"],"source":item["source"]}
    return {"status":"escalated","answer":"I could not answer that from the approved demo knowledge base. An authorized representative should review it.","source":"Escalation policy"}

def process_message(message_id, text):
    if not message_id:
        return {"status":"invalid","error":"Missing messageId"}
    with LOCK:
        if message_id in SEEN:
            return {"messageId":message_id,"status":"duplicate"}
        SEEN.add(message_id)
    result=respond(text)
    event={"messageId":message_id,"status":result["status"],"source":result["source"]}
    with LOCK:
        AUDIT.append(event)
    return {"messageId":message_id,**result}

def extract_messages(payload):
    out=[]
    if not isinstance(payload,dict):
        return out
    for event in payload.get("results",[]) or []:
        mid=event.get("messageId") or event.get("message",{}).get("id")
        message=event.get("message") or {}
        text=message.get("text")
        if isinstance(text,dict):
            text=text.get("text")
        if not text:
            text=event.get("text")
            if isinstance(text,dict):
                text=text.get("text")
        sender=event.get("from") or event.get("sender")
        if isinstance(sender,dict):
            sender=sender.get("phoneNumber") or sender.get("number")
        if mid and text:
            out.append((str(mid),str(text),str(sender) if sender else None))
    return out

def send_whatsapp_text(to, text):
    key=os.getenv("INFOBIP_API_KEY")
    base=os.getenv("INFOBIP_BASE_URL","").rstrip("/")
    sender=os.getenv("INFOBIP_WHATSAPP_SENDER")
    if not (key and base and sender and to):
        return {"sent":False,"reason":"live Infobip configuration incomplete"}
    body=json.dumps({"from":sender,"to":to,"messageId":str(uuid.uuid4()),"content":{"text":text}}).encode()
    req=urllib.request.Request(
        base+"/whatsapp/1/message/text",
        data=body,
        headers={"Authorization":f"App {key}","Content-Type":"application/json","Accept":"application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req,timeout=20) as res:
            data=res.read().decode()
            return {"sent":200 <= res.status < 300,"httpStatus":res.status,"response":json.loads(data) if data else {}}
    except urllib.error.HTTPError as exc:
        data=exc.read().decode()
        return {"sent":False,"httpStatus":exc.code,"response":data[:1000]}
    except Exception as exc:
        return {"sent":False,"error":type(exc).__name__}

def handle_event(payload, live=False):
    if live:
        expected_to=os.getenv("INFOBIP_WHATSAPP_SENDER")
        raw_results=payload.get("results",[]) if isinstance(payload,dict) else []
        if expected_to and raw_results and any(str(e.get("to","")) != expected_to for e in raw_results if e.get("to")):
            return {"results":[],"mode":"LIVE","error":"Unexpected destination sender"}
    messages=extract_messages(payload)
    if not messages:
        return {"results":[],"mode":"LIVE" if live else "LOCAL_SIMULATION","error":"No supported text messages found"}
    results=[]
    for mid,text,sender in messages:
        result=process_message(mid,text)
        if live and sender and result.get("status") not in ("duplicate","invalid"):
            result["outbound"]=send_whatsapp_text(sender,result["answer"])
        results.append(result)
    return {"results":results,"mode":"LIVE" if live else "LOCAL_SIMULATION"}

class Handler(BaseHTTPRequestHandler):
    def _json(self,status,payload):
        raw=json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/":
            raw=(BASE_DIR/"index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif path=="/health":
            self._json(200,{"ok":True,"service":"infobip-solution-engineering-demo","liveConfigured":bool(os.getenv("INFOBIP_API_KEY") and os.getenv("INFOBIP_BASE_URL") and os.getenv("INFOBIP_WHATSAPP_SENDER"))})
        elif path=="/audit":
            with LOCK:
                events=list(AUDIT[-100:])
            self._json(200,{"events":events})
        else:
            self._json(404,{"error":"not found"})

    def do_POST(self):
        path=urlparse(self.path).path
        if path not in ("/webhook","/simulate"):
            return self._json(404,{"error":"not found"})
        # Trial sender resource-level forwarding does not attach our custom
        # X-Webhook-Token header. Keep this endpoint HTTPS-only at Render and
        # validate the destination sender inside the payload before replying.
        try:
            size=int(self.headers.get("Content-Length","0"))
            if size<=0 or size>100000:
                return self._json(400,{"error":"invalid body size"})
            payload=json.loads(self.rfile.read(size))
        except Exception:
            return self._json(400,{"error":"invalid JSON"})
        result=handle_event(payload,live=(path=="/webhook"))
        self._json(200,result)

if __name__=="__main__":
    port=int(os.getenv("PORT","8000"))
    server=ThreadingHTTPServer(("0.0.0.0",port),Handler)
    print(f"Listening on 0.0.0.0:{port}")
    server.serve_forever()
