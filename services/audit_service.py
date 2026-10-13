import uuid
from database.connection import SessionLocal
from database.models import AuditLog

def audit_event(actor_id: str, action: str, record_ref: str):
    if SessionLocal is None:
        return
    try:
        with SessionLocal() as db:
            db.add(AuditLog(id=str(uuid.uuid4()), actor_id=actor_id, action=action[:100], record_ref=str(record_ref)[:100]))
            db.commit()
    except Exception:
        # Audit failure should be surfaced to operational monitoring in production.
        # Do not leak sensitive record content into logs.
        pass
