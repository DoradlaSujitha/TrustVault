from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.config import settings
from backend.database import get_db
from backend.models import User
_hasher=PasswordHasher()
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")
def hash_password(password): return _hasher.hash(password)
def verify_password(password, password_hash):
    try: return _hasher.verify(password_hash, password)
    except VerificationError: return False
def create_access_token(user):
    now=datetime.now(timezone.utc)
    return jwt.encode({"sub":str(user.id),"iat":now,"exp":now+timedelta(minutes=settings.access_token_minutes)}, settings.jwt_secret_key, algorithm="HS256")
def get_current_user(token: str=Depends(oauth2_scheme), db: Session=Depends(get_db)):
    try: user_id=int(jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate":"Bearer"})
    user=db.get(User,user_id)
    if not user: raise HTTPException(status_code=401, detail="User not found")
    return user
def require_admin(user: User=Depends(get_current_user)):
    if user.role!="admin": raise HTTPException(status_code=403, detail="Administrator role required")
    return user
