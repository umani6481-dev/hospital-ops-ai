from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Department
from app.api.predictions import _dept_context
from ml.prediction import predict_service as ps
from app.services.chatbot_service import get_chatbot_reply

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


class ChatbotRequest(BaseModel):
    message: str


class ChatbotResponse(BaseModel):
    reply: str


def _find_departments(db: Session, message: str):
    """If the user named a specific department, use only that one;
    otherwise fall back to every department."""
    all_depts = db.query(Department).all()
    lowered = message.lower()
    matched = [d for d in all_depts if d.name.lower() in lowered]
    return matched if matched else all_depts


def _try_live_data_answer(db: Session, message: str):
    """
    If the question is asking for a live number (beds available, demand,
    overload risk, waiting time), run the actual trained ML models and
    build a natural-language answer with real numbers. Returns None if
    the question isn't a live-data question, so the caller can fall back
    to the static knowledge base.
    """
    lowered = message.lower()

    is_bed_question = any(k in lowered for k in ["bed", "beds"]) and any(
        k in lowered for k in ["available", "availability", "free", "tomorrow", "kal", "kitne", "how many"]
    )
    is_demand_question = (not is_bed_question) and any(
        k in lowered for k in ["demand", "patients", "patient volume"]
    ) and any(
        k in lowered for k in ["tomorrow", "kal", "how many", "kitne", "forecast", "predict"]
    )
    is_overload_question = any(k in lowered for k in ["overload", "overloaded"]) or (
        "risk" in lowered and "department" in lowered
    )
    is_waiting_question = any(k in lowered for k in ["wait", "waiting", "queue"])

    if not (is_bed_question or is_demand_question or is_overload_question or is_waiting_question):
        return None

    try:
        depts = _find_departments(db, message)
        if not depts:
            return None

        lines = []
        for d in depts[:6]:  # keep the reply readable
            ctx = _dept_context(db, d)

            if is_bed_question:
                r = ps.predict_bed_availability(
                    department_name=d.name, total_beds=ctx["total_beds"], capacity=d.capacity,
                    prev_day_demand=ctx["prev_day_demand"], prev_week_demand=ctx["prev_week_demand"],
                    ma_7=ctx["ma_7"], ma_14=ctx["ma_14"],
                )
                lines.append(
                    f"{d.name}: ~{r['predicted_available_beds']} of {r['total_beds']} beds "
                    f"expected free tomorrow ({r['risk']} risk)."
                )
            elif is_demand_question:
                r = ps.predict_demand(
                    department_name=d.name, capacity=d.capacity, doctors_available=ctx["doctors_available"],
                    prev_day_demand=ctx["prev_day_demand"], prev_week_demand=ctx["prev_week_demand"],
                    ma_7=ctx["ma_7"], ma_14=ctx["ma_14"],
                )
                lines.append(
                    f"{d.name}: ~{r['predicted_patients']} patients expected tomorrow "
                    f"(range {r['confidence_interval']['low']}-{r['confidence_interval']['high']})."
                )
            elif is_overload_question:
                demand = ps.predict_demand(
                    department_name=d.name, capacity=d.capacity, doctors_available=ctx["doctors_available"],
                    prev_day_demand=ctx["prev_day_demand"], prev_week_demand=ctx["prev_week_demand"],
                    ma_7=ctx["ma_7"], ma_14=ctx["ma_14"],
                )
                r = ps.predict_overload(
                    department_name=d.name, expected_patients=demand["predicted_patients"], capacity=d.capacity,
                    doctors_available=ctx["doctors_available"],
                )
                lines.append(
                    f"{d.name}: {r['risk_level']} overload risk tomorrow "
                    f"({r['overload_probability']}% confidence)."
                )
            elif is_waiting_question:
                occ_ratio = ctx["occupied_beds"] / max(1, ctx["total_beds"])
                expected = int(ctx["ma_7"])
                r = ps.predict_waiting_time(
                    department_name=d.name, expected_patients=expected, capacity=d.capacity,
                    occupancy_ratio=occ_ratio, doctors_available=ctx["doctors_available"],
                )
                lines.append(
                    f"{d.name}: current estimated wait is {r['current_waiting_time_minutes']} min "
                    f"({r['risk']} risk)."
                )

        return "\n".join(lines)
    except ps.ModelNotTrainedError:
        return "The prediction models aren't trained yet — please run the training commands from the README first."
    except Exception:
        return None


@router.post("/ask", response_model=ChatbotResponse)
def ask_chatbot(payload: ChatbotRequest, db: Session = Depends(get_db)):
    """
    Answers questions about this dashboard. First checks whether the
    question is asking for live prediction data (beds, demand, overload,
    waiting time) and if so, runs the real trained models. Otherwise
    falls back to the static feature knowledge base.
    """
    live_answer = _try_live_data_answer(db, payload.message)
    if live_answer:
        return ChatbotResponse(reply=live_answer)

    reply = get_chatbot_reply(payload.message)
    return ChatbotResponse(reply=reply)