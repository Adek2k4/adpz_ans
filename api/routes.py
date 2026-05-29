import json
import os
import re
from datetime import datetime

from flask import Blueprint, jsonify, request


api_bp = Blueprint("api", __name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

FILES = {
    "students": "api_students.json",
    "internships": "api_internships.json",
    "documents": "api_documents.json",
    "journal_entries": "api_journal_entries.json",
    "effects": "api_effects.json",
}


def _load_items(key):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, FILES[key])
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return []


def _save_items(key, items):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, FILES[key])
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2)


def _next_id(items):
    if not items:
        return 1
    return max(item.get("id", 0) for item in items) + 1


def _json_error(message, status, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status


def _get_payload():
    payload = request.get_json(silent=True)
    if payload is None:
        return None, _json_error("Brak danych JSON w zadaniu.", 400)
    return payload, None


def _validate_student(payload, partial=False):
    errors = {}
    name = payload.get("name")
    email = payload.get("email")

    if not partial or name is not None:
        if not name or not str(name).strip():
            errors["name"] = "Imie jest wymagane."
    if not partial or email is not None:
        if not email or not str(email).strip():
            errors["email"] = "Email jest wymagany."
        elif not EMAIL_RE.match(str(email)):
            errors["email"] = "Nieprawidlowy format email."
    return errors


def _validate_internship(payload, partial=False):
    errors = {}
    required = ["student_id", "company", "start_date", "end_date", "status"]
    for key in required:
        value = payload.get(key)
        if partial and value is None:
            continue
        if value in (None, ""):
            errors[key] = "Pole jest wymagane."

    if "student_id" in payload and payload.get("student_id") not in (None, ""):
        if not isinstance(payload.get("student_id"), int):
            errors["student_id"] = "student_id musi byc liczba."
    return errors


def _validate_document(payload, partial=False):
    errors = {}
    required = ["internship_id", "type", "status"]
    for key in required:
        value = payload.get(key)
        if partial and value is None:
            continue
        if value in (None, ""):
            errors[key] = "Pole jest wymagane."
    if "internship_id" in payload and payload.get("internship_id") not in (None, ""):
        if not isinstance(payload.get("internship_id"), int):
            errors["internship_id"] = "internship_id musi byc liczba."
    return errors


def _filter_by_query(items, key_name, query_name):
    value = request.args.get(query_name)
    if value is None:
        return items
    try:
        value_int = int(value)
    except ValueError:
        return items
    return [item for item in items if item.get(key_name) == value_int]


@api_bp.route("/api/students", methods=["GET", "POST"])
def students_collection():
    if request.method == "GET":
        items = _load_items("students")
        return jsonify({"data": items})

    payload, error = _get_payload()
    if error:
        return error

    errors = _validate_student(payload)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    items = _load_items("students")
    item = {
        "id": _next_id(items),
        "name": payload["name"].strip(),
        "email": payload["email"].strip(),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    items.append(item)
    _save_items("students", items)
    return jsonify({"data": item}), 201


@api_bp.route("/api/students/<int:item_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def students_resource(item_id):
    items = _load_items("students")
    item = next((entry for entry in items if entry.get("id") == item_id), None)
    if not item:
        return _json_error("Nie znaleziono studenta.", 404)

    if request.method == "GET":
        return jsonify({"data": item})

    if request.method == "DELETE":
        items = [entry for entry in items if entry.get("id") != item_id]
        _save_items("students", items)
        return jsonify({"ok": True})

    payload, error = _get_payload()
    if error:
        return error

    partial = request.method == "PATCH"
    errors = _validate_student(payload, partial=partial)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    if "name" in payload:
        item["name"] = payload["name"].strip()
    if "email" in payload:
        item["email"] = payload["email"].strip()

    _save_items("students", items)
    return jsonify({"data": item})


@api_bp.route("/api/internships", methods=["GET", "POST"])
def internships_collection():
    if request.method == "GET":
        items = _load_items("internships")
        items = _filter_by_query(items, "student_id", "student_id")
        return jsonify({"data": items})

    payload, error = _get_payload()
    if error:
        return error

    errors = _validate_internship(payload)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    items = _load_items("internships")
    item = {
        "id": _next_id(items),
        "student_id": payload["student_id"],
        "company": payload["company"].strip(),
        "start_date": payload["start_date"],
        "end_date": payload["end_date"],
        "status": payload["status"],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    items.append(item)
    _save_items("internships", items)
    return jsonify({"data": item}), 201


@api_bp.route("/api/internships/<int:item_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def internships_resource(item_id):
    items = _load_items("internships")
    item = next((entry for entry in items if entry.get("id") == item_id), None)
    if not item:
        return _json_error("Nie znaleziono praktyki.", 404)

    if request.method == "GET":
        return jsonify({"data": item})

    if request.method == "DELETE":
        items = [entry for entry in items if entry.get("id") != item_id]
        _save_items("internships", items)
        return jsonify({"ok": True})

    payload, error = _get_payload()
    if error:
        return error

    partial = request.method == "PATCH"
    errors = _validate_internship(payload, partial=partial)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    for key in ["student_id", "company", "start_date", "end_date", "status"]:
        if key in payload:
            item[key] = payload[key]

    _save_items("internships", items)
    return jsonify({"data": item})


@api_bp.route("/api/documents", methods=["GET", "POST"])
def documents_collection():
    if request.method == "GET":
        items = _load_items("documents")
        items = _filter_by_query(items, "internship_id", "internship_id")
        return jsonify({"data": items})

    payload, error = _get_payload()
    if error:
        return error

    errors = _validate_document(payload)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    items = _load_items("documents")
    item = {
        "id": _next_id(items),
        "internship_id": payload["internship_id"],
        "type": payload["type"].strip(),
        "status": payload["status"].strip(),
        "notes": payload.get("notes", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    items.append(item)
    _save_items("documents", items)
    return jsonify({"data": item}), 201


@api_bp.route("/api/documents/<int:item_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def documents_resource(item_id):
    items = _load_items("documents")
    item = next((entry for entry in items if entry.get("id") == item_id), None)
    if not item:
        return _json_error("Nie znaleziono dokumentu.", 404)

    if request.method == "GET":
        return jsonify({"data": item})

    if request.method == "DELETE":
        items = [entry for entry in items if entry.get("id") != item_id]
        _save_items("documents", items)
        return jsonify({"ok": True})

    payload, error = _get_payload()
    if error:
        return error

    partial = request.method == "PATCH"
    errors = _validate_document(payload, partial=partial)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    for key in ["internship_id", "type", "status", "notes"]:
        if key in payload:
            item[key] = payload[key]

    _save_items("documents", items)
    return jsonify({"data": item})


@api_bp.route("/api/journal-entries", methods=["GET", "POST"])
def journal_entries_collection():
    if request.method == "GET":
        items = _load_items("journal_entries")
        items = _filter_by_query(items, "internship_id", "internship_id")
        return jsonify({"data": items})

    payload, error = _get_payload()
    if error:
        return error

    errors = _validate_journal_entry(payload)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    items = _load_items("journal_entries")
    item = {
        "id": _next_id(items),
        "internship_id": int(payload["internship_id"]),
        "date": payload["date"],
        "activity": payload["activity"].strip(),
        "hours": int(payload["hours"]),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    items.append(item)
    _save_items("journal_entries", items)
    return jsonify({"data": item}), 201


@api_bp.route("/api/journal-entries/<int:item_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def journal_entries_resource(item_id):
    items = _load_items("journal_entries")
    item = next((entry for entry in items if entry.get("id") == item_id), None)
    if not item:
        return _json_error("Nie znaleziono wpisu dziennika.", 404)

    if request.method == "GET":
        return jsonify({"data": item})

    if request.method == "DELETE":
        items = [entry for entry in items if entry.get("id") != item_id]
        _save_items("journal_entries", items)
        return jsonify({"ok": True})

    payload, error = _get_payload()
    if error:
        return error

    partial = request.method == "PATCH"
    errors = _validate_journal_entry(payload, partial=partial)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    if "internship_id" in payload:
        item["internship_id"] = int(payload["internship_id"])
    if "date" in payload:
        item["date"] = payload["date"]
    if "activity" in payload:
        item["activity"] = payload["activity"].strip()
    if "hours" in payload:
        item["hours"] = int(payload["hours"])

    _save_items("journal_entries", items)
    return jsonify({"data": item})


@api_bp.route("/api/effects", methods=["GET", "POST"])
def effects_collection():
    if request.method == "GET":
        items = _load_items("effects")
        items = _filter_by_query(items, "internship_id", "internship_id")
        return jsonify({"data": items})

    payload, error = _get_payload()
    if error:
        return error

    errors = _validate_effect(payload)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    achieved_value = payload.get("achieved", False)
    if not isinstance(achieved_value, bool):
        achieved_value = str(achieved_value).lower() in ("true", "1")

    items = _load_items("effects")
    item = {
        "id": _next_id(items),
        "internship_id": int(payload["internship_id"]),
        "code": payload["code"].strip(),
        "description": payload["description"].strip(),
        "achieved": achieved_value,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    items.append(item)
    _save_items("effects", items)
    return jsonify({"data": item}), 201


@api_bp.route("/api/effects/<int:item_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def effects_resource(item_id):
    items = _load_items("effects")
    item = next((entry for entry in items if entry.get("id") == item_id), None)
    if not item:
        return _json_error("Nie znaleziono efektu.", 404)

    if request.method == "GET":
        return jsonify({"data": item})

    if request.method == "DELETE":
        items = [entry for entry in items if entry.get("id") != item_id]
        _save_items("effects", items)
        return jsonify({"ok": True})

    payload, error = _get_payload()
    if error:
        return error

    partial = request.method == "PATCH"
    errors = _validate_effect(payload, partial=partial)
    if errors:
        return _json_error("Bledne dane.", 400, errors)

    if "internship_id" in payload:
        item["internship_id"] = int(payload["internship_id"])
    if "code" in payload:
        item["code"] = payload["code"].strip()
    if "description" in payload:
        item["description"] = payload["description"].strip()
    if "achieved" in payload:
        achieved_value = payload.get("achieved")
        if not isinstance(achieved_value, bool):
            achieved_value = str(achieved_value).lower() in ("true", "1")
        item["achieved"] = achieved_value

    _save_items("effects", items)
    return jsonify({"data": item})
