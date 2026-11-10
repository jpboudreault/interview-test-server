import json
import os
import random
import time
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"
STATIC = ROOT / "static"

app = Flask(__name__, static_folder=None)
CORS(app)


def error(message, code, status):
    return jsonify(errors=[{"message": message, "field": "", "code": code}]), status


@app.get("/")
def landing():
    return send_from_directory(STATIC, "index.html")


@app.get("/deck")
def deck():
    return send_from_directory(STATIC, "deck.html")


@app.get("/tax-calculator/tax-year/<tax_year>")
def tax_brackets(tax_year):
    # Unreliable on purpose: callers must cope with latency and random failures.
    time.sleep(random.randint(0, 5))
    if random.randint(1, 4) == 1:
        return error("Database not found!", "INTERNAL_SERVER_ERROR", 500)

    path = FIXTURES / f"tax-brackets--{tax_year}.json"
    if not tax_year.isdigit() or not path.is_file():
        return error("That url was not found", "NOT_FOUND", 404)

    return jsonify(tax_brackets=json.loads(path.read_text()))


@app.errorhandler(404)
def not_found(_):
    return error("That url was not found", "NOT_FOUND", 404)


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5001)), debug=True)
