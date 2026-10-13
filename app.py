import streamlit as st
from config.settings import APP_NAME, PUBLIC_DEMO
from auth.service import authenticate, logout
from database.repositories import create_patient, list_patients, create_screening, list_screenings
from services.image_service import read_uploaded_image, validate_image
from ai.inference import predict_image, model_available
from services.report_service import build_pdf
from auth.passwords import hash_password
from database.connection import SessionLocal
from database.models import User
from services.audit_service import audit_event
from datetime import datetime, timezone
import uuid

st.set_page_config(page_title=APP_NAME, page_icon="", layout="wide")

def init_state():
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("last_screening", None)

def login_view():
    st.title("Drishti Care")
    st.caption("AI-assisted retinal screening")
    #st.warning("Research/demo software only. Not for diagnosis or clinical decisions. Use synthetic data in public demos.")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
    if submitted:
        user = authenticate(username.strip(), password)
        if user:
            st.session_state.user = {
                "id": user["id"], "username": user["username"], "role": user["role"]
            }
            st.rerun()
        st.error("Unable to sign in. Check credentials or contact the administrator.")

def main():
    init_state()
    if not st.session_state.user:
        login_view()
        return

    user = st.session_state.user
    with st.sidebar:
        st.title("Drishti Care")
        st.write(f"Signed in: **{user['username']}**")
        st.caption(f"Role: {user['role']}")
        if PUBLIC_DEMO:
            st.info("Public demo mode")
        page = st.radio("Navigation", ["Dashboard", "Register patient", "New screening", "Screening history", "Admin"])
        if st.button("Log out", use_container_width=True):
            logout()
            st.rerun()

    if page == "Dashboard":
        st.title("Dashboard")
        #st.info("This dashboard tracks workflow records; it does not establish clinical effectiveness.")
        try:
            records = list_screenings(user["id"], user["role"], limit=1000)
            st.metric("Screening records available", len(records))
        except Exception as exc:
            st.error("Could not load records. Check database connectivity.")
            st.caption(str(exc))
        #st.write("**Model status:**", "Trained artifact found" if model_available() else "Not configured — train the model first")
        #st.write("**Capture status:** upload and browser camera are supported for software testing.")
        #st.write("A standard webcam cannot reliably capture a retinal fundus image.")

    elif page == "Register patient":
        st.title("Register patient")
        #st.caption("For a public demo, enter synthetic test data only.")
        with st.form("patient_form"):
            patient_ref = st.text_input("Patient reference")
            age = st.number_input("Age", min_value=0, max_value=120, value=45)
            #consent = st.checkbox("Consent confirmed for this demo workflow")
            submit = st.form_submit_button("Save patient")
        if submit:
            if not patient_ref.strip():
                st.error("Patient reference is required.")
            #elif not consent:
                st.error("Confirm consent before saving.")
            else:
                try:
                    patient_id = create_patient(patient_ref.strip(), int(age), user["id"])
                    audit_event(user["id"], "patient_created", patient_id)
                    st.success(f"Patient record created: {patient_ref}")
                except ValueError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error("Could not save patient. Check database connection and logs.")
                    st.caption(str(exc))

    elif page == "New screening":
        st.title("New screening")
        #st.warning("Do not use this demo output for patient care. Only purpose-built retinal fundus imaging can provide the intended input.")
        patients = list_patients(user["id"], user["role"])
        if not patients:
            st.info("Register a synthetic patient first.")
            return
        patient_map = {f"{p['patient_ref']} (ID {p['id'][:8]})": p for p in patients}
        selected_label = st.selectbox("Patient", list(patient_map))
        eye = st.selectbox("Eye", ["Right", "Left"])
        method = st.radio("Image source", ["Upload retinal image", "Browser camera demo"], horizontal=True)
        if method == "Upload retinal image":
            source = st.file_uploader("Upload JPG or PNG", type=["jpg", "jpeg", "png"])
        else:
            source = st.camera_input("Camera capture")
        if source:
            try:
                image_bytes, image = read_uploaded_image(source)
                valid, reason = validate_image(image)
                st.image(image, caption=f"{eye} eye — review before continuing", use_container_width=True)
                if not valid:
                    st.error(f"Image rejected: {reason}")
                    return
                #st.info("Basic file checks passed. This does not establish that the image is a gradable retinal fundus photograph.")
                if st.button("Run AI screening", type="primary"):
                    prediction = predict_image(image)
                    patient = patient_map[selected_label]
                    status = prediction["status"]
                    screening_id = create_screening(
                        patient_id=patient["id"], operator_id=user["id"], eye=eye,
                        status=status, result=prediction
                    )
                    audit_event(user["id"], "screening_created", screening_id)
                    st.session_state.last_screening = {
                        "screening_id": screening_id, "patient_ref": patient["patient_ref"],
                        "eye": eye, "created_at": datetime.now(timezone.utc).isoformat(),
                        **prediction
                    }
                    st.rerun()
            except Exception as exc:
                st.error("Could not process this image.")
                st.caption(str(exc))

        if st.session_state.last_screening:
            r = st.session_state.last_screening
            st.divider()
            st.subheader("Most recent screening workflow")
            st.write("Record:", r["screening_id"])
            st.write("Status:", r["status"])
            if r["status"] == "model_not_configured":
                #st.warning("No trained model artifact is installed. No prediction was made.")
                pass
            elif r["status"] == "completed":
                st.write("Research model output:", r.get("grade_label", "Unknown"))
                st.caption("Not a diagnosis. Do not use for clinical decisions.")
            if st.button("Generate one-page demo PDF"):
                pdf = build_pdf(r)
                st.download_button("Download PDF report", data=pdf,
                                   file_name=f"drishti-demo-{r['screening_id'][:8]}.pdf",
                                   mime="application/pdf")

    elif page == "Screening history":
        st.title("Screening history")
        try:
            rows = list_screenings(user["id"], user["role"], limit=200)
            if not rows:
                st.info("No screening records found.")
            else:
                st.dataframe(rows, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error("Could not load history.")
            st.caption(str(exc))

    elif page == "Admin":
        st.title("Administration")
        if user["role"] != "admin":
            st.error("Administrator permission is required.")
            return
        st.subheader("Create a user")
        with st.form("create_user_form"):
            new_username = st.text_input("New username")
            new_password = st.text_input("Temporary password", type="password")
            role = st.selectbox("Role", ["operator", "reviewer", "admin"])
            submit_user = st.form_submit_button("Create user")
        if submit_user:
            if len(new_username.strip()) < 3 or len(new_password) < 12:
                st.error("Username must be at least 3 characters and password at least 12 characters.")
            else:
                try:
                    with SessionLocal() as db:
                        if db.query(User).filter_by(username=new_username.strip()).first():
                            st.error("Username already exists.")
                        else:
                            db.add(User(id=str(uuid.uuid4()), username=new_username.strip(), password_hash=hash_password(new_password), role=role, is_active=True))
                            db.commit()
                            audit_event(user["id"], "user_created", new_username.strip())
                            st.success("User created.")
                except Exception as exc:
                    st.error("Could not create user.")
                    st.caption(str(exc))
        st.caption("Create only accounts for authorized demo users. Add stronger administrative controls before production.")

if __name__ == "__main__":
    main()
