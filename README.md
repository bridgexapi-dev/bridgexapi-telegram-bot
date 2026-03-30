# BridgeXAPI Telegram Bot Example

A Telegram bot that talks to the live BridgeXAPI endpoints.

## Features

- `/balance` fetches live API balance
- `/routes` fetches live route catalog
- `/pricing` shows route buttons for live pricing lookup
- `/send <route_id> <number> <message>` sends one SMS
- inline buttons for balance, routes, and pricing

## Commands

```bash
/start
/help
/menu
/balance
/routes
/pricing
/send 3 31651860670 Your verification code is 4839
```

## Setup

```bash
git clone <your-repo-url>
cd bridgexapi-telegram-bot
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Install

```bash
pip install -r requirements.txt
```

### Configure environment

Copy `.env.example` to `.env` and fill in your values.

```env
BOT_TOKEN=your_telegram_bot_token
BRIDGEXAPI_API_KEY=your_bridgexapi_api_key
BRIDGEXAPI_BASE_URL=https://hi.bridgexapi.io
DEFAULT_CALLER_ID=BRIDGEXAPI
REQUEST_TIMEOUT=20
```

## Run

```bash
python bot.py
```

## Notes

- pricing and route data are fetched from the live API
- route buttons are wired for route ids 1, 2, 3, and 4
- `/send` requires the route id explicitly so the user controls routing
- caller ID stays explicit through environment config
- numbers should be digits only
- messages should be plain ASCII text

## Docs

- docs: https://docs.bridgexapi.io
- dashboard: https://dashboard.bridgexapi.io
