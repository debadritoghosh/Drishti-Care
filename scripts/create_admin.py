import getpass, uuid
from database.connection import SessionLocal
from database.models import User
from auth.passwords import hash_password

if SessionLocal is None:
    raise SystemExit("DATABASE_URL missing. Configure .env first.")
username = input("Admin username (3+ chars): ").strip()
password = getpass.getpass("Admin password (12+ chars): ")
confirm = getpass.getpass("Confirm password: ")
if len(username) < 3: raise SystemExit("Username must be at least 3 characters.")
if password != confirm: raise SystemExit("Passwords do not match.")
with SessionLocal() as db:
    if db.query(User).filter_by(username=username).first():
        raise SystemExit("Username already exists.")
    db.add(User(id=str(uuid.uuid4()), username=username, password_hash=hash_password(password), role="admin", is_active=True))
    db.commit()
print("Admin created. Store credentials securely.")
