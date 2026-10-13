from database.connection import engine
from database.models import Base

if engine is None:
    raise SystemExit("DATABASE_URL missing. Configure .env first.")
Base.metadata.create_all(bind=engine)
print("Database tables created.")
