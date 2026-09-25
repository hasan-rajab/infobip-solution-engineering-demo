import unittest
import app

class DemoTests(unittest.TestCase):
    def setUp(self):
        app.SEEN.clear(); app.AUDIT.clear()

    def event(self,mid,text):
        return {"results":[{"messageId":mid,"from":"synthetic-user","message":{"text":text}}]}

    def test_grounded(self):
        r=app.handle_event(self.event("1","What is AMEEN?"))
        self.assertEqual(r["results"][0]["status"],"answered")

    def test_sensitive(self):
        r=app.handle_event(self.event("2","What is my balance?"))
        self.assertEqual(r["results"][0]["status"],"escalated")

    def test_unknown(self):
        r=app.handle_event(self.event("3","Tell me the weather"))
        self.assertEqual(r["results"][0]["status"],"escalated")

    def test_duplicate(self):
        app.handle_event(self.event("4","What is AMEEN?"))
        r=app.handle_event(self.event("4","What is AMEEN?"))
        self.assertEqual(r["results"][0]["status"],"duplicate")

    def test_invalid(self):
        r=app.handle_event({"bad":"payload"})
        self.assertEqual(r["results"],[])

    def test_audit_privacy(self):
        secret="private-message-text"
        app.handle_event(self.event("6",secret))
        self.assertNotIn(secret,str(app.AUDIT))

if __name__=="__main__":
    unittest.main()
