from supabase import create_client, Client
from flask import current_app
 


def get_client() -> Client:
    url = current_app.config["SUPABASE_URL"]
    key = current_app.config["SUPABASE_KEY"]
    return create_client(url, key)


def create_task(task_data: dict) -> dict:
    client = get_client()

    if "customer_identifier" in task_data and task_data["customer_identifier"]:
        task_data["customer_identifier"] = task_data["customer_identifier"].strip().lower()

    response = client.table("tasks").insert(task_data).execute()
    return response.data[0] if response.data else None


def get_all_tasks() -> list:
    client = get_client()
    response = (
        client.table("tasks")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []

def get_tasks_by_customer(customer_identifier):
    client = get_client()

    if not customer_identifier:
        response = (
            client.table("tasks")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    response = (
        client.table("tasks")
        .select("*")
        .eq("customer_identifier", customer_identifier.strip().lower())
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []

def get_task_by_code(task_code: str) -> dict:
    client = get_client()
    response = (
        client.table("tasks")
        .select("*")
        .eq("task_code", task_code)
        .single()
        .execute()
    )
    return response.data


def update_task_status(task_id: str, new_status: str) -> dict:
    client = get_client()
    response = (
        client.table("tasks")
        .update({"status": new_status})
        .eq("id", task_id)
        .execute()
    )
    return response.data[0] if response.data else None


def save_messages(task_id: str, messages: dict) -> dict:
    client = get_client()
    payload = {
        "task_id": task_id,
        "whatsapp_message": messages.get("whatsapp"),
        "email_message": messages.get("email"),
        "sms_message": messages.get("sms"),
    }
    response = client.table("task_messages").insert(payload).execute()
    return response.data[0] if response.data else None



def get_messages_for_task(task_id: str) -> dict:
    client = get_client()
    response = (
        client.table("task_messages")
        .select("*")
        .eq("task_id", task_id)
        .single()
        .execute()
    )
    return response.data
