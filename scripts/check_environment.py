import sys
print("Python:", sys.version)
try:
    import streamlit, sqlalchemy, torch, torchvision, PIL, reportlab
    print("Streamlit:", streamlit.__version__)
    print("SQLAlchemy:", sqlalchemy.__version__)
    print("PyTorch:", torch.__version__)
    print("Torchvision:", torchvision.__version__)
    print("CUDA available:", torch.cuda.is_available())
    print("Pillow:", PIL.__version__)
    print("ReportLab:", reportlab.Version)
except Exception as e:
    print("Environment check failed:", repr(e))
    raise
