import uuid
import json
from datetime import datetime
from flask import request, jsonify
from app.blueprints.tasks import tasks_bp
from app.services import ai_service, risk_service, supabase_service


def generate_task_code() -> str:
    prefix = "VNH"
    suffix = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{suffix}"


@tasks_bp.route("/submit", methods=["POST"])
def submit_task():
    body = request.get_json()
    if not body or not body.get("message"):
        return jsonify({"error": "Message is required"}), 400

    user_message = body["message"].strip()

    try:
        extracted = ai_service.extract_intent(user_message)
    except Exception as e:
        return jsonify({"error": f"Intent extraction failed: {str(e)}"}), 500

    intent = extracted.get("intent", "check_status")
    entities = extracted.get("entities", {})

    risk_result = risk_service.score_request(intent, entities)

    task_code = generate_task_code()

    try:
        steps = ai_service.generate_steps(intent, entities, task_code)
    except Exception as e:
        steps = []

    try:
        messages = ai_service.generate_messages(
            intent, entities, task_code, risk_result["label"]
        )
    except Exception as e:
        messages = {"whatsapp": "", "email": "", "sms": ""}

    task_data = {
        "task_code": task_code,
        "original_message": user_message,
        "intent": intent,
        "entities": json.dumps(entities),
        "risk_score": risk_result["score"],
        "risk_label": risk_result["label"],
        "risk_reasons": json.dumps(risk_result["reasons"]),
        "steps": json.dumps(steps),
        "employee_assignment": risk_result["employee_assignment"],
        "status": "Pending",
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        saved_task = supabase_service.create_task(task_data)
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    try:
        supabase_service.save_messages(saved_task["id"], messages)
    except Exception as e:
        pass

    return jsonify({
        "task_code": task_code,
        "task_id": saved_task["id"],
        "intent": intent,
        "entities": entities,
        "risk": risk_result,
        "steps": steps,
        "messages": messages,
        "employee_assignment": risk_result["employee_assignment"],
        "status": "Pending",
    }), 201


@tasks_bp.route("/<task_id>/status", methods=["PATCH"])
def update_status(task_id):
    body = request.get_json()
    new_status = body.get("status")

    valid_statuses = ["Pending", "In Progress", "Completed"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Status must be one of {valid_statuses}"}), 400

    try:
        updated = supabase_service.update_task_status(task_id, new_status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not updated:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"task_id": task_id, "status": new_status}), 200


@tasks_bp.route("/<task_code>/detail", methods=["GET"])
def task_detail(task_code):
    try:
        task = supabase_service.get_task_by_code(task_code)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not task:
        return jsonify({"error": "Task not found"}), 404

    try:
        msgs = supabase_service.get_messages_for_task(task["id"])
    except Exception:
        msgs = None

    task["messages"] = msgs
    return jsonify(task), 200
