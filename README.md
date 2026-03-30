# BridgeXAPI Telegram Bot

Example Telegram bot that connects directly to the BridgeXAPI messaging infrastructure.

No dashboards.
No hidden routing.
Everything is exposed through the API.

---

## What this is

This project is a minimal, working example of how to interact with BridgeXAPI from a Telegram interface.

It is not a mock.

All data is fetched live from the API:

* balance
* routes
* pricing
* message submission

---

## Features

* `/balance` → fetch live API balance
* `/routes` → fetch route catalog
* `/pricing` → interactive route pricing lookup
* `/send <route_id> <number> <message>` → send SMS
* inline buttons for navigation

---

## Example

```bash
/send 3 31651860670 Your verification code is 4839
```

This directly maps to:

```python
client.send_sms(
    route_id=3,
    caller_id="BRIDGEXAPI",
    numbers=["31651860670"],
    message="Your verification code is 4839"
)
```

Routing is explicit.

---

## Setup

This bot uses the BridgeXAPI platform.

You need a BridgeXAPI account and API key.

### 1. Create account

https://dashboard.bridgexapi.io

### 2. Get API key

Go to:

**Developer → Console**

Copy your API key.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy `.env.example` → `.env`

```env
BOT_TOKEN=your_telegram_bot_token
BRIDGEXAPI_API_KEY=your_bridgexapi_api_key
BRIDGEXAPI_BASE_URL=https://hi.bridgexapi.io
DEFAULT_CALLER_ID=BRIDGEXAPI
REQUEST_TIMEOUT=20
```

### 5. Run

```bash
python bot.py
```

---

## Commands

```
/start
/help
/menu
/balance
/routes
/pricing
/send <route_id> <number> <message>
```

---

## Notes

* routing is controlled via `route_id`
* pricing depends on route + destination prefix
* numbers must be digits only
* messages should be ASCII
* no UI abstraction — direct API interaction

---

## Docs

https://docs.bridgexapi.io
https://dashboard.bridgexapi.io

---

## About BridgeXAPI

BridgeXAPI is a messaging infrastructure API for developers.

* single endpoint
* multiple routes
* explicit routing control
* real pricing per destination

Built for systems, not dashboards.
