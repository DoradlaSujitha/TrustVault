import os
from backend.database import Base, SessionLocal, engine
from backend.models import User
from backend.security import hash_password
Base.metadata.create_all(bind=engine)
def main():
    configs=[("SEED_ADMIN_EMAIL","SEED_ADMIN_PASSWORD","admin@example.com","ChangeMe-Admin-123!","admin"),("SEED_OWNER_EMAIL","SEED_OWNER_PASSWORD","owner@example.com","ChangeMe-Owner-123!","owner"),("SEED_VIEWER_EMAIL","SEED_VIEWER_PASSWORD","viewer@example.com","ChangeMe-Viewer-123!","viewer")]
    db=SessionLocal()
    try:
        for ek,pk,de,dp,role in configs:
            email=os.getenv(ek,de).lower(); password=os.getenv(pk,dp)
            if db.query(User).filter_by(email=email).first(): print(f"Already exists: {email}"); continue
            db.add(User(email=email,password_hash=hash_password(password),role=role)); print(f"Created {role}: {email}")
        db.commit()
    finally: db.close()
if __name__=="__main__": main()
