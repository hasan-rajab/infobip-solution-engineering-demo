# Infobip Solution Engineering Demo

Portfolio-grade synthetic customer-messaging integration built to demonstrate solution-engineering fundamentals with Infobip WhatsApp APIs.

## Verified milestone

Before this repository was deployed, a real authenticated Infobip WhatsApp trial-template API request returned HTTP 200 and the message was confirmed delivered to the verified handset. This repository does not contain the API key or recipient phone number.

## What the service demonstrates

- Public HTTPS-ready Python service
- Infobip-style inbound webhook parsing
- Message-ID deduplication
- Approved synthetic FAQ routing
- Sensitive/account-specific and unknown-query escalation
- Privacy-conscious in-memory audit events that omit message text
- Real outbound WhatsApp text API client for live webhook replies
- Health endpoint and simulation UI
- Six automated tests

## Honest scope

This is a synthetic portfolio demonstration, not a real banking application. No real bank accounts are connected. A live two-way claim should only be made after the deployed webhook is configured in Infobip and an actual inbound WhatsApp message is received and replied to successfully.

## Environment variables

Set these in the hosting provider, never in source control:

- `INFOBIP_API_KEY`
- `INFOBIP_BASE_URL`
- `INFOBIP_WHATSAPP_SENDER`

See `.env.example` for non-secret placeholders.

## Local run

`python app.py`

Then open `http://localhost:8000/`.

## Tests

`python -m unittest -v test_app.py`

## Endpoints

- `GET /` demo UI
- `GET /health`
- `GET /audit`
- `POST /simulate` safe local/deployed simulation
- `POST /webhook` live inbound path for the configured Infobip sender


## Webhook security note

For the Infobip trial sender, the first live test uses the sender's direct **Forward to HTTP** configuration over HTTPS. The application validates that inbound payloads target the configured Infobip sender before sending a reply. For a stronger production-style setup, switch the sender to **Apply subscription** and use Infobip Subscriptions with HMAC authentication/signature verification. Do not describe this demo as production-secure until that hardening is implemented and tested.
