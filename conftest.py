import os,tempfile
_TEST_DIR=tempfile.mkdtemp(prefix="trustvault-tests-")
os.environ["DATABASE_URL"]="sqlite:///"+os.path.join(_TEST_DIR,"test.db").replace(chr(92), "/")
os.environ["STORAGE_DIR"]=os.path.join(_TEST_DIR,"storage")
os.environ["JWT_SECRET_KEY"]="test-secret-that-is-at-least-32-bytes-long"
import pytest
from fastapi.testclient import TestClient
from backend.database import Base,engine,SessionLocal
from backend.main import app
from backend.models import User
from backend.security import hash_password
@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine); os.makedirs(os.environ["STORAGE_DIR"],exist_ok=True)
    db=SessionLocal(); db.add_all([User(email="owner@example.com",password_hash=hash_password("owner-pass"),role="owner"),User(email="viewer@example.com",password_hash=hash_password("viewer-pass"),role="viewer"),User(email="admin@example.com",password_hash=hash_password("admin-pass"),role="admin")]); db.commit(); db.close()
    with TestClient(app) as c: yield c
def token(client,email,password):
    r=client.post("/auth/login",json={"email":email,"password":password}); assert r.status_code==200,r.text; return r.json()["access_token"]
