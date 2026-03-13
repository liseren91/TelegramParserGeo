"""
Simple web UI for one-shot Telegram channels parsing.
"""
import asyncio
import logging
import os
import threading
import time
from io import TextIOWrapper

from flask import Flask, jsonify, render_template, request

from main import normalize_channel_usernames, update_posts_for_channels
import config

_here = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(_here, "templates"))
logger = logging.getLogger(__name__)
_run_lock = threading.Lock()
_cooldown_lock = threading.Lock()
_cooldown_until_ts = 0.0


def _extract_channels_from_text(raw_text):
    if not raw_text:
        return []
    return [line.strip() for line in raw_text.replace(",", "\n").splitlines() if line.strip()]


def _extract_channels_from_uploaded_file(file_storage):
    if not file_storage or not file_storage.filename:
        return []

    wrapped = TextIOWrapper(file_storage.stream, encoding="utf-8", errors="ignore")
    raw_text = wrapped.read()
    return _extract_channels_from_text(raw_text)


def _get_cooldown_seconds_remaining():
    with _cooldown_lock:
        remaining = int(_cooldown_until_ts - time.time())
    return max(0, remaining)


def _set_cooldown_seconds(seconds):
    global _cooldown_until_ts
    with _cooldown_lock:
        _cooldown_until_ts = max(_cooldown_until_ts, time.time() + max(0, seconds))


@app.route("/", methods=["GET"])
def index():
    sheet_id = config.GOOGLE_SHEET_ID
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}" if sheet_id else None
    return render_template("index.html", sheet_url=sheet_url)


@app.route("/api/parse", methods=["POST"])
def parse_channels():
    cooldown_seconds = _get_cooldown_seconds_remaining()
    if cooldown_seconds > 0:
        return jsonify({
            "ok": False,
            "error": (
                f"Telegram FloodWait активен. Повторите через {cooldown_seconds} сек."
            ),
            "cooldown_seconds": cooldown_seconds
        }), 429

    if not _run_lock.acquire(blocking=False):
        return jsonify({
            "ok": False,
            "error": "Парсинг уже запущен. Дождитесь завершения текущего прогона."
        }), 409

    try:
        channels_text = request.form.get("channels", "")
        channels_from_text = _extract_channels_from_text(channels_text)
        channels_from_file = _extract_channels_from_uploaded_file(request.files.get("channels_file"))

        normalized_channels = normalize_channel_usernames(channels_from_text + channels_from_file)
        if not normalized_channels:
            return jsonify({
                "ok": False,
                "error": "Не найдено валидных каналов. Добавьте username, @username или ссылку t.me."
            }), 400

        result = asyncio.run(update_posts_for_channels(normalized_channels, lookback_hours=10))

        flood_wait_seconds = int(result.get("flood_wait_seconds") or 0)
        if flood_wait_seconds > 0:
            total_cooldown = flood_wait_seconds + config.PARSER_FLOOD_WAIT_BUFFER_SEC
            _set_cooldown_seconds(total_cooldown)
            result["cooldown_seconds"] = total_cooldown

        return jsonify({
            "ok": True,
            "result": result
        })
    except Exception as exc:
        logger.error("Web parse request failed: %s", exc, exc_info=True)
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500
    finally:
        _run_lock.release()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8010))
    app.run(host="0.0.0.0", port=port, debug=False)
