"""
Risk scoring for Vunoh diaspora tasks.

Score range: 0 - 100
  0  - 29  : Low risk    (green)
  30 - 59  : Medium risk (amber)
  60 - 100 : High risk   (red)

The score is built from several independent signals that reflect real
considerations for a diaspora remittance and services platform operating
in Kenya. Each signal contributes a fixed number of points. The signals
are additive and capped at 100.
"""


EMPLOYEE_MAP = {
    "send_money": "Finance Team",
    "hire_service": "Operations Team",
    "verify_document": "Legal Team",
    "airport_transfer": "Logistics Team",
    "check_status": "Support Team",
}

RISK_LABELS = {
    "low": (0, 29),
    "medium": (30, 59),
    "high": (60, 100),
}


def score_request(intent: str, entities: dict, customer_history: list = None) -> dict:
    score = 0
    reasons = []

    # --- Intent baseline ---
    # Land title verification and large money transfers carry inherent legal
    # and fraud risk. General errands and status checks are low baseline.
    intent_base = {
        "verify_document": 20,
        "send_money": 15,
        "hire_service": 8,
        "airport_transfer": 5,
        "check_status": 0,
    }
    score += intent_base.get(intent, 10)

    # --- Document type ---
    if intent == "verify_document":
        doc_type = str(entities.get("document_type", "")).lower()
        if "land" in doc_type or "title" in doc_type or "deed" in doc_type:
            score += 25
            reasons.append("Land title verification is high-risk due to fraud prevalence in Kenya")
        elif "id" in doc_type or "passport" in doc_type:
            score += 10
            reasons.append("Identity document verification requires careful handling")
        else:
            score += 5

    # --- Amount risk (send_money) ---
    if intent == "send_money":
        amount = _parse_amount(entities.get("amount", 0))
        if amount >= 100000:
            score += 30
            reasons.append("Transfer above KES 100,000 triggers enhanced due diligence")
        elif amount >= 50000:
            score += 20
            reasons.append("Transfer above KES 50,000 requires recipient verification")
        elif amount >= 10000:
            score += 10
            reasons.append("Transfer above KES 10,000 — standard monitoring")
        else:
            score += 3

    # --- Urgency ---
    urgency = str(entities.get("urgency", "")).lower()
    if urgency in ("urgent", "asap", "immediately", "emergency", "today"):
        score += 15
        reasons.append("Urgency flag raises risk — rushed transfers are a common fraud vector")

    # --- Recipient known / unknown ---
    recipient = entities.get("recipient") or entities.get("service_provider")
    if not recipient:
        score += 10
        reasons.append("Recipient or provider not identified in request")

    # --- Location specificity ---
    location = entities.get("location", "")
    if not location:
        score += 5
        reasons.append("No location specified — increases operational uncertainty")

    # --- Customer history ---
    
    if customer_history:
        completed = [t for t in customer_history if t.get("status") == "Completed"]
        any_high = any(t.get("risk_score", 0) >= 60 for t in customer_history)

        if len(completed) >= 3 and not any_high:
            score -= 15
            reasons.append("Returning customer with 3+ completed tasks and clean history — reduced risk")
        elif len(completed) >= 1 and not any_high:
            score -= 7
            reasons.append("Returning customer with prior completed task — slightly reduced risk")
        elif any_high:
            score += 8
            reasons.append("Prior high-risk task on this account — heightened caution applied")

    final_score = min(max(score, 0), 100)

    return {
        "score": final_score,
        "label": _get_label(final_score),
        "reasons": reasons,
        "employee_assignment": EMPLOYEE_MAP.get(intent, "Support Team"),
    }


def _parse_amount(raw) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = str(raw).replace(",", "").replace("KES", "").replace("ksh", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _get_label(score: int) -> str:
    if score <= 29:
        return "low"
    elif score <= 59:
        return "medium"
    return "high"
