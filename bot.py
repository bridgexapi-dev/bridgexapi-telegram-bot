import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bridgexapi import BridgeXAPI

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("bridgexapi-telegram-bot")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BRIDGEXAPI_API_KEY = os.getenv("BRIDGEXAPI_API_KEY", "").strip()
BRIDGEXAPI_BASE_URL = os.getenv("BRIDGEXAPI_BASE_URL", "https://hi.bridgexapi.io").rstrip("/")
DEFAULT_CALLER_ID = os.getenv("DEFAULT_CALLER_ID", "BRIDGEXAPI").strip()
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "20"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in environment.")

if not BRIDGEXAPI_API_KEY:
    raise RuntimeError("BRIDGEXAPI_API_KEY is missing in environment.")

bot = TeleBot(BOT_TOKEN, parse_mode="Markdown")
client = BridgeXAPI(
    api_key=BRIDGEXAPI_API_KEY,
    base_url=BRIDGEXAPI_BASE_URL,
    timeout=REQUEST_TIMEOUT,
)
http = requests.Session()


class BridgeXHTTP:
    def __init__(self, api_key: str, base_url: str, timeout: float = 20.0) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def headers(self) -> dict[str, str]:
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    def get_balance(self) -> dict[str, Any]:
        return self._get("/api/v1/balance")

    def get_routes(self) -> Any:
        return self._get("/api/v1/routes")

    def get_route_pricing(self, route_id: int) -> Any:
        return self._get(f"/api/v1/routes/{route_id}/pricing")

    def _get(self, path: str) -> Any:
        response = http.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            timeout=self.timeout,
        )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"BridgeXAPI returned non-JSON for {path} (status {response.status_code})."
            ) from exc

        if not response.ok:
            detail = data.get("detail") if isinstance(data, dict) else data
            raise RuntimeError(
                str(detail) if detail else f"Request failed with status {response.status_code}."
            )

        return data


bridge_http = BridgeXHTTP(
    api_key=BRIDGEXAPI_API_KEY,
    base_url=BRIDGEXAPI_BASE_URL,
    timeout=REQUEST_TIMEOUT,
)

START_TEXT = """*BridgeXAPI Telegram Bot*

Live Telegram interface for:
- balance
- routes
- route pricing
- SMS sending

Use `/setup` if this is your first time.
Use `/menu` to open the action buttons.
"""

HELP_TEXT = """*BridgeXAPI Telegram Bot*

This bot talks to the live BridgeXAPI endpoints.

## Get your API key

1. Go to:
`https://dashboard.bridgexapi.io`

2. Open:
`Developer -> Console`

3. Copy your API key

4. Put it in your `.env` file:
`BRIDGEXAPI_API_KEY=your_api_key_here`

## Commands

`/start` - intro
`/help` - show help
`/setup` - show setup instructions
`/menu` - show action buttons
`/balance` - fetch live API balance
`/routes` - fetch live route catalog
`/pricing` - choose a route and fetch live pricing
`/send <route_id> <number> <message>` - send one SMS

## Example

`/send 3 31651860670 Your verification code is 4839`

## Notes

- number should be digits only
- message should be plain ASCII text
- caller ID comes from DEFAULT_CALLER_ID in your environment
"""

SETUP_TEXT = """*BridgeXAPI Bot Setup*

1. Open:
`https://dashboard.bridgexapi.io`

2. Go to:
`Developer -> Console`

3. Copy your API key

4. Create a `.env` file based on `.env.example`

5. Fill in:

`BOT_TOKEN=your_telegram_bot_token`
`BRIDGEXAPI_API_KEY=your_api_key_here`
`BRIDGEXAPI_BASE_URL=https://hi.bridgexapi.io`
`DEFAULT_CALLER_ID=BRIDGEXAPI`
`REQUEST_TIMEOUT=20`

6. Restart the bot:
`py bot.py`
"""


def main_menu() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Balance", callback_data="balance"),
        InlineKeyboardButton("Routes", callback_data="routes"),
    )
    markup.add(
        InlineKeyboardButton("Pricing", callback_data="pricing_menu"),
        InlineKeyboardButton("Help", callback_data="help"),
    )
    return markup


def pricing_menu() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Route 1", callback_data="pricing:1"),
        InlineKeyboardButton("Route 2", callback_data="pricing:2"),
    )
    markup.add(
        InlineKeyboardButton("Route 3", callback_data="pricing:3"),
        InlineKeyboardButton("Route 4", callback_data="pricing:4"),
    )
    markup.add(InlineKeyboardButton("Back", callback_data="menu"))
    return markup


def humanize_error(exc: Exception) -> str:
    text = str(exc).strip()

    if "Invalid or inactive API Key" in text:
        return (
            "❌ Invalid or inactive API key.\n\n"
            "Get your API key from:\n"
            "`https://dashboard.bridgexapi.io`\n"
            "`Developer -> Console`\n\n"
            "Then update your `.env` file and restart the bot."
        )

    if "Missing API Key" in text:
        return (
            "❌ Missing API key.\n\n"
            "Set `BRIDGEXAPI_API_KEY` in your `.env` file and restart the bot."
        )

    return f"❌ {text}"


def parse_send_command(text: str) -> tuple[int, str, str]:
    parts = text.strip().split(maxsplit=3)
    if len(parts) < 4:
        raise ValueError("Usage: /send <route_id> <number> <message>")

    _, route_id_raw, number, message = parts

    if not route_id_raw.isdigit():
        raise ValueError("route_id must be numeric.")

    route_id = int(route_id_raw)
    if route_id < 1 or route_id > 8:
        raise ValueError("route_id must be between 1 and 8.")

    if not number.isdigit():
        raise ValueError("Number must contain digits only.")

    if len(number) < 10 or len(number) > 15:
        raise ValueError("Number must usually be between 10 and 15 digits.")

    if not message.strip():
        raise ValueError("Message cannot be empty.")

    return route_id, number, message.strip()


def normalize_routes_payload(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if isinstance(data, dict):
        for key in ("routes", "items", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []


def normalize_pricing_payload(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if isinstance(data, dict):
        for key in ("pricing", "items", "prices", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []


def format_routes(data: Any) -> str:
    routes = normalize_routes_payload(data)
    if not routes:
        return f"*Routes*\n\n```{data}```"

    lines = ["*Live routes*"]
    for item in routes[:20]:
        route_id = item.get("route_id", "?")
        name = item.get("name") or item.get("route") or "Unnamed route"
        is_active = item.get("is_active")
        suffix = ""
        if is_active is not None:
            suffix = " — active" if is_active else " — inactive"
        lines.append(f"- Route `{route_id}`: {name}{suffix}")
    return "\n".join(lines)


def format_pricing(route_id: int, data: Any) -> str:
    items = normalize_pricing_payload(data)
    if not items:
        return f"*Route {route_id} pricing*\n\n```{data}```"

    lines = [f"*Route {route_id} pricing*", ""]
    for item in items[:20]:
        country = item.get("country") or item.get("destination") or item.get("country_name") or "Unknown"
        prefix = item.get("country_prefix") or item.get("prefix") or item.get("code") or "-"
        price = item.get("price")
        price_text = str(price) if price is not None else "hidden"
        lines.append(f"- {country} (`{prefix}`): `{price_text}`")
    return "\n".join(lines)


def format_balance(data: Any) -> str:
    if not isinstance(data, dict):
        return f"*Balance*\n\n```{data}```"

    account = data.get("account") if isinstance(data.get("account"), dict) else {}
    username = account.get("username") or data.get("username") or "unknown"
    balance = data.get("balance")
    sandbox = data.get("sandbox")

    lines = ["*Live API balance*"]
    lines.append(f"- User: `{username}`")
    if balance is not None:
        lines.append(f"- Balance: `{balance}`")
    if sandbox is not None:
        lines.append(f"- Sandbox: `{sandbox}`")
    return "\n".join(lines)


@bot.message_handler(commands=["start"])
def handle_start(message: Message) -> None:
    bot.reply_to(message, START_TEXT, reply_markup=main_menu())


@bot.message_handler(commands=["help"])
def handle_help(message: Message) -> None:
    bot.reply_to(message, HELP_TEXT, reply_markup=main_menu())


@bot.message_handler(commands=["setup"])
def handle_setup(message: Message) -> None:
    bot.reply_to(message, SETUP_TEXT, reply_markup=main_menu())


@bot.message_handler(commands=["menu"])
def handle_menu(message: Message) -> None:
    bot.reply_to(message, "Choose an action:", reply_markup=main_menu())


@bot.message_handler(commands=["balance"])
def handle_balance(message: Message) -> None:
    try:
        data = bridge_http.get_balance()
        bot.reply_to(message, format_balance(data), reply_markup=main_menu())
    except Exception as exc:
        logger.exception("Failed to fetch balance")
        bot.reply_to(message, humanize_error(exc), reply_markup=main_menu())


@bot.message_handler(commands=["routes"])
def handle_routes(message: Message) -> None:
    try:
        data = bridge_http.get_routes()
        bot.reply_to(message, format_routes(data), reply_markup=main_menu())
    except Exception as exc:
        logger.exception("Failed to fetch routes")
        bot.reply_to(message, humanize_error(exc), reply_markup=main_menu())


@bot.message_handler(commands=["pricing"])
def handle_pricing(message: Message) -> None:
    bot.reply_to(message, "Choose a route:", reply_markup=pricing_menu())


@bot.message_handler(commands=["send"])
def handle_send(message: Message) -> None:
    try:
        route_id, number, sms_text = parse_send_command(message.text or "")
    except ValueError as exc:
        bot.reply_to(message, f"❌ {exc}\n\n{HELP_TEXT}", reply_markup=main_menu())
        return

    try:
        result = client.send_sms(
            route_id=route_id,
            caller_id=DEFAULT_CALLER_ID,
            numbers=[number],
            message=sms_text,
        )
        bot.reply_to(
            message,
            (
                "✅ SMS submitted\n\n"
                f"*Route:* `{route_id}`\n"
                f"*Caller ID:* `{DEFAULT_CALLER_ID}`\n"
                f"*Number:* `{number}`\n"
                f"*Result:* `{result}`"
            ),
            reply_markup=main_menu(),
        )
    except Exception as exc:
        logger.exception("Failed to send SMS")
        bot.reply_to(message, humanize_error(exc), reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: CallbackQuery) -> None:
    data = call.data or ""

    try:
        if data == "menu":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Choose an action:",
                reply_markup=main_menu(),
            )
        elif data == "help":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=HELP_TEXT,
                reply_markup=main_menu(),
            )
        elif data == "balance":
            payload = bridge_http.get_balance()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=format_balance(payload),
                reply_markup=main_menu(),
            )
        elif data == "routes":
            payload = bridge_http.get_routes()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=format_routes(payload),
                reply_markup=main_menu(),
            )
        elif data == "pricing_menu":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Choose a route:",
                reply_markup=pricing_menu(),
            )
        elif data.startswith("pricing:"):
            route_id = int(data.split(":", 1)[1])
            payload = bridge_http.get_route_pricing(route_id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=format_pricing(route_id, payload),
                reply_markup=pricing_menu(),
            )
        else:
            bot.answer_callback_query(call.id, "Unknown action.")
            return

        bot.answer_callback_query(call.id)
    except Exception as exc:
        logger.exception("Callback failed")
        bot.answer_callback_query(call.id, "Request failed.")
        bot.send_message(
            call.message.chat.id,
            humanize_error(exc),
            reply_markup=main_menu(),
        )


@bot.message_handler(func=lambda _: True)
def handle_fallback(message: Message) -> None:
    bot.reply_to(message, HELP_TEXT, reply_markup=main_menu())


if __name__ == "__main__":
    logger.info("Starting BridgeXAPI Telegram bot")
    bot.infinity_polling(skip_pending=True)