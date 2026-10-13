from database.connection import SessionLocal
from database.models import User
from auth.passwords import verify_password
from services.audit_service import audit_event

def authenticate(username: str, password: str):
    if SessionLocal is None:
        return None
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=username, is_active=True).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        result = {"id": user.id, "username": user.username, "role": user.role}
    audit_event(result["id"], "login_success", result["username"])
    return result

def logout():
    # Streamlit session state is cleared by the UI caller.
    import streamlit as st
    st.session_state.user = None
    st.session_state.last_screening = None
