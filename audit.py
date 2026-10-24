import hashlib, json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.models import AuditEvent

def record_event(db: Session, actor_id, actor_email, action, resource_type="document", resource_id="", outcome="success", details=""):
    last = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
    previous = last.event_hash if last else "GENESIS"
    stamp = datetime.now(timezone.utc)
    body = {"timestamp": stamp.isoformat(), "actor_id": actor_id, "actor_email": actor_email,
            "action": action, "resource_type": resource_type, "resource_id": str(resource_id),
            "outcome": outcome, "details": details, "previous_hash": previous}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    event = AuditEvent(timestamp=stamp, actor_id=actor_id, actor_email=actor_email, action=action,
        resource_type=resource_type, resource_id=str(resource_id), outcome=outcome, details=details,
        previous_hash=previous, event_hash=digest)
    db.add(event); db.commit(); db.refresh(event)
    return event

def verify_chain(db: Session):
    events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    previous = "GENESIS"
    for event in events:
        if event.previous_hash != previous:
            return False, event.id
        stamp = event.timestamp
        if stamp is not None and stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        body = {"timestamp": stamp.isoformat() if stamp else "", "actor_id": event.actor_id,
                "actor_email": event.actor_email, "action": event.action,
                "resource_type": event.resource_type, "resource_id": event.resource_id,
                "outcome": event.outcome, "details": event.details,
                "previous_hash": event.previous_hash}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if digest != event.event_hash:
            return False, event.id
        previous = event.event_hash
    return True, None
