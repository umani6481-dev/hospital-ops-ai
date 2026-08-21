from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Alert, User, AuditLog
from app.schemas.schemas import AlertOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(acknowledged: bool | None = None, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    q = db.query(Alert)
    if acknowledged is not None:
        q = q.filter(Alert.acknowledged == acknowledged)
    return q.order_by(Alert.created_at.desc()).limit(100).all()


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.add(AuditLog(user_id=user.id, action="acknowledge_alert", entity="alert", entity_id=alert_id))
    db.commit()
    db.refresh(alert)
    return alert
