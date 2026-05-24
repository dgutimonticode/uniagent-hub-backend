from typing import Any

from flask import jsonify


def success_response(data: Any = None, message: str = "Success", status: int = 200):
    return jsonify({"data": data, "message": message}), status


def error_response(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status
