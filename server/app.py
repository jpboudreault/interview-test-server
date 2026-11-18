import hmac
import json
import logging
import math
import os
import random
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"
STATIC = ROOT / "static"

PUBLIC_PATHS = {"/tax-calculator/tax-year/{tax_year}"}

RATE_LIMIT_CALLS = 2
RATE_LIMIT_WINDOW = 3.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("tax-api")

app = Flask(__name__, static_folder=None)
CORS(app, expose_headers=["Retry-After", "X-Correlation-ID"])

_calls = defaultdict(deque)
_calls_lock = threading.Lock()


def error(message, code, status):
    return jsonify(errors=[{"message": message, "field": "", "code": code}]), status


def unreliable(delay=True):
    # Callers must cope with latency and random failures.
    if delay:
        time.sleep(random.randint(0, 5))
    if random.randint(1, 4) == 1:
        return error("Database not found!", "INTERNAL_SERVER_ERROR", 500)
    return None


def load_brackets(tax_year):
    path = FIXTURES / f"tax-brackets--{tax_year}.json"
    if not tax_year.isdigit() or not path.is_file():
        return None
    return json.loads(path.read_text())


def brackets_response(tax_year, delay=True):
    failure = unreliable(delay)
    if failure:
        return failure
    brackets = load_brackets(tax_year)
    if brackets is None:
        return error("That url was not found", "NOT_FOUND", 404)
    return jsonify(tax_brackets=brackets)


def client_id():
    return request.headers.get("Fly-Client-IP") or request.remote_addr


def retry_after(client):
    """Seconds the client must wait, or 0 if the call is allowed (sliding window)."""
    now = time.monotonic()
    with _calls_lock:
        calls = _calls[client]
        while calls and now - calls[0] >= RATE_LIMIT_WINDOW:
            calls.popleft()
        if len(calls) >= RATE_LIMIT_CALLS:
            return max(1, math.ceil(RATE_LIMIT_WINDOW - (now - calls[0])))
        calls.append(now)
        return 0


@app.after_request
def correlation(response):
    correlation_id = request.headers.get("X-Correlation-ID")
    if correlation_id:
        response.headers["X-Correlation-ID"] = correlation_id
    log.info("%s %s %s correlation_id=%s", request.method, request.path, response.status_code, correlation_id or "-")
    return response


@app.get("/")
def landing():
    return send_from_directory(STATIC, "index.html")


@app.get("/deck")
def deck():
    return send_from_directory(STATIC, "deck.html")


def load_spec():
    return json.loads((STATIC / "openapi.json").read_text())


@app.get("/docs", strict_slashes=False)
@app.get("/docs/full", strict_slashes=False)
def docs():
    return send_from_directory(STATIC, "docs.html")


@app.get("/openapi.json")
def openapi_public():
    spec = load_spec()
    spec["paths"] = {p: v for p, v in spec["paths"].items() if p in PUBLIC_PATHS}
    # Swagger UI shows an "Authorize" button whenever a security scheme is declared.
    spec["components"].pop("securitySchemes", None)
    return jsonify(spec)


@app.get("/openapi-full.json")
def openapi_full():
    return jsonify(load_spec())


@app.get("/tax-calculator/tax-year/<tax_year>")
def tax_brackets(tax_year):
    return brackets_response(tax_year)


@app.get("/tax-calculator/rate-limited/tax-year/<tax_year>")
def rate_limited_tax_brackets(tax_year):
    wait = retry_after(client_id())
    if wait:
        response, status = error("Too many requests", "RATE_LIMITED", 429)
        response.headers["Retry-After"] = str(wait)
        return response, status
    # No added latency here, otherwise sequential callers would rarely hit the limit.
    return brackets_response(tax_year, delay=False)


@app.get("/tax-calculator/secure/tax-year/<tax_year>")
def secure_tax_brackets(tax_year):
    expected = os.environ.get("TAX_API_KEY")
    if not expected:
        return error("API key is not configured on the server", "NOT_CONFIGURED", 503)
    provided = request.headers.get("X-API-Key")
    if not provided:
        return error("Missing X-API-Key header", "UNAUTHORIZED", 401)
    if not hmac.compare_digest(provided.encode(), expected.encode()):
        return error("Invalid API key", "FORBIDDEN", 403)
    return brackets_response(tax_year)


@app.get("/tax-calculator/v2/tax-year/<tax_year>")
def tax_brackets_v2(tax_year):
    failure = unreliable()
    if failure:
        return failure
    brackets = load_brackets(tax_year)
    if brackets is None:
        return error("That url was not found", "NOT_FOUND", 404)
    return jsonify(
        tax_year=int(tax_year),
        brackets=[
            {"lower": b["min"], "upper": b.get("max"), "rate_percent": round(b["rate"] * 100, 2)}
            for b in brackets
        ],
    )


@app.get("/tax-calculator/tax-year/<tax_year>/credits")
def credits(tax_year):
    failure = unreliable()
    if failure:
        return failure
    data = json.loads((FIXTURES / "credits.json").read_text()).get(tax_year)
    if data is None:
        return error("That url was not found", "NOT_FOUND", 404)
    return jsonify(data)


@app.errorhandler(404)
def not_found(_):
    return error("That url was not found", "NOT_FOUND", 404)


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5001)), debug=True)
