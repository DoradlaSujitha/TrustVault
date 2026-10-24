from tests.conftest import token
def upload(client,t): return client.post("/documents",headers={"Authorization":f"Bearer {t}"},data={"name":"Demo","category":"Academic","description":"test"},files={"file":("demo.txt",b"hello trustvault","text/plain")})
def test_owner_upload_download(client):
    t=token(client,"owner@example.com","owner-pass"); r=upload(client,t); assert r.status_code==200,r.text; d=client.get(f"/documents/{r.json()['id']}/download",headers={"Authorization":f"Bearer {t}"}); assert d.status_code==200 and d.content==b"hello trustvault"
def test_viewer_denied_without_grant(client):
    o=token(client,"owner@example.com","owner-pass"); v=token(client,"viewer@example.com","viewer-pass"); did=upload(client,o).json()["id"]; assert client.get(f"/documents/{did}/download",headers={"Authorization":f"Bearer {v}"}).status_code==404
def test_grant_and_immediate_revoke(client):
    o=token(client,"owner@example.com","owner-pass"); v=token(client,"viewer@example.com","viewer-pass"); did=upload(client,o).json()["id"]
    assert client.post(f"/documents/{did}/permissions",headers={"Authorization":f"Bearer {o}"},json={"email":"viewer@example.com","permission":"read"}).status_code==200
    assert client.get(f"/documents/{did}/download",headers={"Authorization":f"Bearer {v}"}).status_code==200
    uid=client.get("/auth/me",headers={"Authorization":f"Bearer {v}"}).json()["id"]
    assert client.delete(f"/documents/{did}/permissions/{uid}",headers={"Authorization":f"Bearer {o}"}).status_code==200
    assert client.get(f"/documents/{did}/download",headers={"Authorization":f"Bearer {v}"}).status_code==404
def test_read_only_cannot_edit_or_delete(client):
    o=token(client,"owner@example.com","owner-pass"); v=token(client,"viewer@example.com","viewer-pass"); did=upload(client,o).json()["id"]
    client.post(f"/documents/{did}/permissions",headers={"Authorization":f"Bearer {o}"},json={"email":"viewer@example.com","permission":"read"})
    assert client.patch(f"/documents/{did}",headers={"Authorization":f"Bearer {v}"},json={"name":"changed"}).status_code==404
    assert client.delete(f"/documents/{did}",headers={"Authorization":f"Bearer {v}"}).status_code==404
def test_admin_audit_only_and_denied_attempt_logged(client):
    o=token(client,"owner@example.com","owner-pass"); v=token(client,"viewer@example.com","viewer-pass"); a=token(client,"admin@example.com","admin-pass"); did=upload(client,o).json()["id"]
    assert client.get("/admin/audit",headers={"Authorization":f"Bearer {o}"}).status_code==403
    client.get(f"/documents/{did}/download",headers={"Authorization":f"Bearer {v}"})
    r=client.get("/admin/audit",headers={"Authorization":f"Bearer {a}"}); assert r.status_code==200
    assert any(x["action"]=="download" and x["outcome"]=="denied" for x in r.json())


def test_invalid_pdf_signature_rejected(client):
    t = token(client, "owner@example.com", "owner-pass")
    r = client.post(
        "/documents",
        headers={"Authorization": f"Bearer {t}"},
        data={"name": "Bad PDF", "category": "Academic", "description": ""},
        files={"file": ("bad.pdf", b"not a pdf", "application/pdf")},
    )
    assert r.status_code == 400
    assert "signature" in r.json()["detail"].lower()


def test_audit_chain_detects_tampering(client):
    from backend.database import SessionLocal
    from backend.models import AuditEvent

    token(client, "owner@example.com", "owner-pass")  # creates a valid audit event
    db = SessionLocal()
    try:
        event = db.query(AuditEvent).first()
        assert event is not None
        event.details = "tampered after recording"
        db.commit()
    finally:
        db.close()

    admin = token(client, "admin@example.com", "admin-pass")
    result = client.get("/admin/audit/verify", headers={"Authorization": f"Bearer {admin}"})
    assert result.status_code == 200
    assert result.json()["valid"] is False
