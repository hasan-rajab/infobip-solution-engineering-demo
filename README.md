# Infobip Solution Engineering Demo

**A customer-messaging integration case showing how a simple conversational workflow can be made safe, observable and integration-ready.**

This portfolio demo was built around a solution-engineering problem:

> **How would you connect a customer-facing WhatsApp channel to approved knowledge and escalation logic without pretending the bot can answer account-specific questions it cannot verify?**

The result is a lightweight Python service that parses Infobip-style inbound webhooks, deduplicates messages, routes approved synthetic FAQs, escalates sensitive/unknown requests and can send outbound WhatsApp responses through the Infobip API.

> **Scope:** this is a synthetic customer-service demo, not a live banking application. No real bank accounts or customer data are connected.

---

## Customer value

A messaging solution like this is useful only if it improves service without creating a new control problem.

The demo focuses on four practical outcomes:

1. **faster self-service** for approved, low-risk questions;
2. **controlled escalation** for sensitive, account-specific or unknown requests;
3. **integration reliability** through message-ID deduplication and health checks;
4. **privacy-conscious observability** through audit events that omit message text.

In a real customer engagement I would measure containment rate, escalation rate, first-response time, duplicate-processing rate, delivery failures and customer satisfaction.

---

## Architecture

```text
Customer / WhatsApp
        ↓
Infobip channel
        ↓
HTTPS webhook
        ↓
Python service
  ├── sender validation
  ├── message-ID deduplication
  ├── approved FAQ routing
  ├── sensitive / unknown escalation
  └── privacy-conscious audit event
        ↓
Infobip outbound API
        ↓
WhatsApp response
```

A simulation UI and health endpoint make the flow easy to demonstrate without exposing secrets.

---

## Verified evidence

Before this repository was deployed, a real authenticated Infobip WhatsApp **trial-template API request returned HTTP 200 and the message was confirmed delivered to the verified handset**.

The repository intentionally does **not** contain:
- the API key;
- the recipient phone number;
- live customer data.

It also includes **six automated tests** covering the service behavior.

This verified milestone demonstrates outbound API connectivity. It should **not** be described as a completed production two-way WhatsApp deployment until a real inbound webhook is configured and validated end to end.

---

## Control decisions

### Unknown does not mean improvise
Only approved synthetic FAQ paths are answered automatically. Unknown or account-specific questions are escalated.

### Duplicate events should not create duplicate actions
Inbound message IDs are tracked so repeated webhook delivery does not generate repeated responses.

### Audit without copying conversation content
The demo records operational events while omitting message text from the audit surface.

### Secrets remain outside source control
Configuration is supplied through environment variables.

---

## Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | demo UI |
| GET | `/health` | service health |
| GET | `/audit` | privacy-conscious operational events |
| POST | `/simulate` | safe synthetic message flow |
| POST | `/webhook` | live inbound path for configured sender |

---

## Configuration

Required environment variables:

- `INFOBIP_API_KEY`
- `INFOBIP_BASE_URL`
- `INFOBIP_WHATSAPP_SENDER`

See `.env.example` for non-secret placeholders.

Run locally:

```bash
python app.py
```

Then open `http://localhost:8000/`.

Run tests:

```bash
python -m unittest -v test_app.py
```

---

## Production hardening path

The trial-sender demo uses the sender's direct **Forward to HTTP** configuration. A stronger implementation would add:

- Infobip Subscriptions;
- HMAC/signature verification;
- durable deduplication storage;
- enterprise identity for operator/admin surfaces;
- centralized logging and alerting;
- real CRM/core-system integration;
- explicit data-retention policy;
- failure/retry handling and delivery observability.

The demo is therefore evidence of **solution engineering, API integration and safe conversational-workflow design**, not a claim of production banking automation.
