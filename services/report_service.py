from reports.pdf_template import generate_screening_pdf

def build_pdf(record: dict) -> bytes:
    return generate_screening_pdf(record)
