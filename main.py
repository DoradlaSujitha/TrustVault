from pathlib import Path
import uuid
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.audit import record_event, verify_chain
from backend.config import settings
from backend.database import Base, engine, get_db
from backend.models import AuditEvent, Document, Permission, User
from backend.schemas import DocumentOut, DocumentUpdate, LoginRequest, PermissionCreate, UserOut
from backend.security import create_access_token, get_current_user, require_admin, verify_password
Base.metadata.create_all(bind=engine); Path(settings.storage_dir).mkdir(parents=True,exist_ok=True)
app=FastAPI(title="TrustVault API",version="1.0.0",description="Secure document sharing hackathon prototype")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
def can_read(db,doc,user):
    if doc.owner_id==user.id: return True
    p=db.query(Permission).filter_by(document_id=doc.id,user_id=user.id).first()
    return bool(p and p.permission in ("read","edit"))
def can_edit(db,doc,user):
    if doc.owner_id==user.id: return True
    p=db.query(Permission).filter_by(document_id=doc.id,user_id=user.id).first()
    return bool(p and p.permission=="edit")
def denied(db,user,action,doc):
    record_event(db,user.id,user.email,action,"document",str(doc.id),"denied","Access denied")
    raise HTTPException(status_code=404,detail="Document not found or access denied")
def to_out(doc):
    return DocumentOut(id=doc.id,name=doc.name,category=doc.category,description=doc.description,original_filename=doc.original_filename,content_type=doc.content_type,size_bytes=doc.size_bytes,owner_id=doc.owner_id,owner_email=doc.owner.email,created_at=doc.created_at,updated_at=doc.updated_at)
@app.get("/")
def root(): return {"name":"TrustVault API","status":"running","docs":"/docs"}
@app.post("/auth/login")
def login(body:LoginRequest,db:Session=Depends(get_db)):
    email=str(body.email).lower(); user=db.query(User).filter(User.email==email).first()
    if not user or not verify_password(body.password,user.password_hash):
        record_event(db,user.id if user else None,email,"login","auth",str(user.id) if user else "","denied","Invalid credentials")
        raise HTTPException(status_code=401,detail="Invalid email or password")
    record_event(db,user.id,user.email,"login","auth",str(user.id),"success","")
    return {"access_token":create_access_token(user),"token_type":"bearer","user":UserOut.model_validate(user)}
@app.get("/auth/me",response_model=UserOut)
def me(user:User=Depends(get_current_user)): return user
@app.post("/documents",response_model=DocumentOut)
async def upload_document(name:str=Form(...),category:str=Form("General"),description:str=Form(""),file:UploadFile=File(...),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    if not name.strip() or len(name)>255: raise HTTPException(400,"Name must be 1–255 characters")
    if len(category)>100 or len(description)>2000: raise HTTPException(400,"Category or description too long")
    content=await file.read(settings.max_upload_mb*1024*1024+1)
    if not content: raise HTTPException(400,"Empty files are not allowed")
    if len(content)>settings.max_upload_mb*1024*1024: raise HTTPException(413,f"File exceeds {settings.max_upload_mb} MB limit")
    ctype=file.content_type or "application/octet-stream"
    if ctype=="application/pdf" and not content.startswith(b"%PDF-"): raise HTTPException(400,"PDF signature does not match file contents")
    if ctype=="image/png" and not content.startswith(bytes([137,80,78,71,13,10,26,10])): raise HTTPException(400,"PNG signature does not match file contents")
    stored=uuid.uuid4().hex; (Path(settings.storage_dir)/stored).write_bytes(content)
    doc=Document(name=name.strip(),category=category.strip() or "General",description=description.strip(),original_filename=Path(file.filename or "upload.bin").name[:255],stored_filename=stored,content_type=ctype,size_bytes=len(content),owner_id=user.id)
    db.add(doc); db.commit(); db.refresh(doc); record_event(db,user.id,user.email,"upload","document",str(doc.id),details=f"bytes={len(content)}"); return to_out(doc)
@app.get("/documents",response_model=list[DocumentOut])
def list_documents(q:str="",category:str="",owner_email:str="",db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    query=db.query(Document).filter(Document.deleted.is_(False))
    if q: query=query.filter(or_(Document.name.ilike(f"%{q}%"),Document.description.ilike(f"%{q}%"),Document.original_filename.ilike(f"%{q}%")))
    if category: query=query.filter(Document.category.ilike(f"%{category}%"))
    if owner_email: query=query.join(User,Document.owner_id==User.id).filter(User.email.ilike(f"%{owner_email}%"))
    return [to_out(d) for d in query.order_by(Document.created_at.desc()).all() if can_read(db,d,user)]
@app.get("/documents/{document_id}",response_model=DocumentOut)
def get_document(document_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    doc=db.get(Document,document_id)
    if not doc or doc.deleted: raise HTTPException(404,"Document not found")
    if not can_read(db,doc,user): denied(db,user,"view_metadata",doc)
    record_event(db,user.id,user.email,"view_metadata","document",str(doc.id)); return to_out(doc)
@app.get("/documents/{document_id}/download")
def download_document(document_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    doc=db.get(Document,document_id)
    if not doc or doc.deleted:
        record_event(db,user.id,user.email,"download","document",str(document_id),"denied","Missing or deleted document"); raise HTTPException(404,"Document not found")
    if not can_read(db,doc,user): denied(db,user,"download",doc)
    path=Path(settings.storage_dir)/doc.stored_filename
    if not path.exists(): record_event(db,user.id,user.email,"download","document",str(doc.id),"denied","Stored file missing"); raise HTTPException(404,"File not found")
    record_event(db,user.id,user.email,"download","document",str(doc.id)); return FileResponse(path,media_type=doc.content_type,filename=doc.original_filename)
@app.patch("/documents/{document_id}",response_model=DocumentOut)
def update_document(document_id:int,body:DocumentUpdate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    doc=db.get(Document,document_id)
    if not doc or doc.deleted: raise HTTPException(404,"Document not found")
    if not can_edit(db,doc,user): denied(db,user,"update_metadata",doc)
    for key,value in body.model_dump(exclude_unset=True).items():
        if value is not None: setattr(doc,key,value)
    db.commit(); db.refresh(doc); record_event(db,user.id,user.email,"update_metadata","document",str(doc.id)); return to_out(doc)
@app.delete("/documents/{document_id}")
def delete_document(document_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    doc=db.get(Document,document_id)
    if not doc or doc.deleted: raise HTTPException(404,"Document not found")
    if not can_edit(db,doc,user): denied(db,user,"delete",doc)
    doc.deleted=True; db.commit(); record_event(db,user.id,user.email,"delete","document",str(doc.id)); return {"status":"deleted","document_id":doc.id}
@app.post("/documents/{document_id}/permissions")
def grant_permission(document_id:int,body:PermissionCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    doc=db.get(Document,document_id)
    if not doc or doc.deleted: raise HTTPException(404,"Document not found")
    if doc.owner_id!=user.id: denied(db,user,"grant_permission",doc)
    target=db.query(User).filter(User.email==str(body.email).lower()).first()
    if not target: record_event(db,user.id,user.email,"grant_permission","document",str(doc.id),"denied","Target user not found"); raise HTTPException(404,"Target user not found")
    if target.id==user.id: raise HTTPException(400,"Owner already has access")
    perm=db.query(Permission).filter_by(document_id=doc.id,user_id=target.id).first()
    if perm: perm.permission=body.permission; perm.granted_by=user.id
    else: db.add(Permission(document_id=doc.id,user_id=target.id,permission=body.permission,granted_by=user.id))
    db.commit(); record_event(db,user.id,user.email,"grant_permission","document",str(doc.id),details=f"user={target.email};permission={body.permission}")
    return {"status":"granted","document_id":doc.id,"user_email":target.email,"permission":body.permission}
@app.delete("/documents/{document_id}/permissions/{target_user_id}")
def revoke_permission(document_id:int,target_user_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    doc=db.get(Document,document_id)
    if not doc or doc.deleted: raise HTTPException(404,"Document not found")
    if doc.owner_id!=user.id: denied(db,user,"revoke_permission",doc)
    perm=db.query(Permission).filter_by(document_id=doc.id,user_id=target_user_id).first()
    if not perm: record_event(db,user.id,user.email,"revoke_permission","document",str(doc.id),"denied","Permission not found"); raise HTTPException(404,"Permission not found")
    target=db.get(User,target_user_id); db.delete(perm); db.commit(); record_event(db,user.id,user.email,"revoke_permission","document",str(doc.id),details=f"user={target.email if target else target_user_id}")
    return {"status":"revoked","document_id":doc.id,"user_id":target_user_id}
@app.get("/admin/audit")
def admin_audit(limit:int=100,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    events=db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(max(1,min(limit,500))).all()
    return [{"id":e.id,"timestamp":e.timestamp,"actor_id":e.actor_id,"actor_email":e.actor_email,"action":e.action,"resource_type":e.resource_type,"resource_id":e.resource_id,"outcome":e.outcome,"details":e.details,"previous_hash":e.previous_hash,"event_hash":e.event_hash} for e in events]
@app.get("/admin/audit/verify")
def admin_verify_audit(db:Session=Depends(get_db),user:User=Depends(require_admin)):
    valid,failed=verify_chain(db); return {"valid":valid,"failed_event_id":failed,"events_checked":db.query(AuditEvent).count()}
