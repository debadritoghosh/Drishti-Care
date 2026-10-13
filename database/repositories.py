import json
import uuid
from sqlalchemy import select, desc
from database.connection import SessionLocal
from database.models import Patient, Screening, User

def _session():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured. Configure .env and initialize MySQL.")
    return SessionLocal()

def create_patient(patient_ref: str, age: int, created_by: str) -> str:
    if not patient_ref or len(patient_ref) > 100:
        raise ValueError("Patient reference must contain 1–100 characters.")
    if age < 0 or age > 120:
        raise ValueError("Age is outside the allowed range.")
    with _session() as db:
        if db.query(Patient).filter_by(patient_ref=patient_ref).first():
            raise ValueError("Patient reference already exists.")
        row = Patient(id=str(uuid.uuid4()), patient_ref=patient_ref, age=age, created_by=created_by, consent_confirmed=True)
        db.add(row)
        db.commit()
        return row.id

def list_patients(user_id: str, role: str):
    with _session() as db:
        q = db.query(Patient)
        if role not in ("admin", "reviewer"):
            q = q.filter(Patient.created_by == user_id)
        return [{"id": p.id, "patient_ref": p.patient_ref, "age": p.age} for p in q.order_by(Patient.created_at.desc()).limit(500).all()]

def create_screening(patient_id: str, operator_id: str, eye: str, status: str, result: dict) -> str:
    with _session() as db:
        patient = db.get(Patient, patient_id)
        if not patient:
            raise ValueError("Patient record not found.")
        row = Screening(id=str(uuid.uuid4()), patient_id=patient_id, operator_id=operator_id,
                        eye=eye, status=status, result_json=json.dumps(result))
        db.add(row)
        db.commit()
        return row.id

def list_screenings(user_id: str, role: str, limit: int = 200):
    with _session() as db:
        q = db.query(Screening, Patient.patient_ref).join(Patient, Screening.patient_id == Patient.id)
        if role not in ("admin", "reviewer"):
            q = q.filter(Screening.operator_id == user_id)
        rows = q.order_by(Screening.created_at.desc()).limit(limit).all()
        return [{
            "screening_id": s.id,
            "patient_ref": patient_ref,
            "eye": s.eye,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else "",
        } for s, patient_ref in rows]
