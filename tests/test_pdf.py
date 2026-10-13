from reports.pdf_template import generate_screening_pdf

def test_pdf_has_pdf_header_and_content():
    pdf = generate_screening_pdf({
        "screening_id": "test-id", "patient_ref": "SYNTHETIC-001",
        "eye": "Right", "status": "model_not_configured",
        "model_version": None, "grade_label": None, "created_at": "2026-01-01T00:00:00Z"
    })
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
