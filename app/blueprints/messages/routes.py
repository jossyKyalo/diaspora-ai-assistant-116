from flask import jsonify
from app.blueprints.messages import messages_bp
from app.services import supabase_service


@messages_bp.route("/<task_id>", methods=["GET"])
def get_messages(task_id):
    try:
        msgs = supabase_service.get_messages_for_task(task_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not msgs:
        return jsonify({"error": "Messages not found"}), 404

    return jsonify(msgs), 200
