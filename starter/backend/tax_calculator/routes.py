import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify(status="ok")


@api.post("/tax")
def tax():
    payload = request.get_json(silent=True) or {}
    logger.info("tax request %s", payload)
    return jsonify(income=payload.get("income"), tax_year=payload.get("tax_year"), total_tax=0)
