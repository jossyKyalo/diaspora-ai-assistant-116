from flask import render_template, jsonify, request
from app.blueprints.dashboard import dashboard_bp
from app.services import supabase_service


@dashboard_bp.route("/", methods=["GET"])
def index():
    return render_template("dashboard/index.html")


@dashboard_bp.route("/api/tasks", methods=["GET"])
def get_tasks():
    try:
        customer_identifier = request.args.get("customer_identifier")
        tasks = supabase_service.get_tasks_by_customer(customer_identifier)
        for task in tasks:
            import json
            if isinstance(task.get("entities"), str):
                try:
                    task["entities"] = json.loads(task["entities"])
                except Exception:
                    task["entities"] = {}
            if isinstance(task.get("steps"), str):
                try:
                    task["steps"] = json.loads(task["steps"])
                except Exception:
                    task["steps"] = []
            if isinstance(task.get("risk_reasons"), str):
                try:
                    task["risk_reasons"] = json.loads(task["risk_reasons"])
                except Exception:
                    task["risk_reasons"] = []
        return jsonify(tasks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
