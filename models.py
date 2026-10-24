from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
def utcnow(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    email: Mapped[str]=mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(512))
    role: Mapped[str]=mapped_column(String(20), default="viewer", index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=utcnow)
class Document(Base):
    __tablename__="documents"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    name: Mapped[str]=mapped_column(String(255), index=True)
    category: Mapped[str]=mapped_column(String(100), default="General", index=True)
    description: Mapped[str]=mapped_column(Text, default="")
    original_filename: Mapped[str]=mapped_column(String(255))
    stored_filename: Mapped[str]=mapped_column(String(80), unique=True)
    content_type: Mapped[str]=mapped_column(String(150), default="application/octet-stream")
    size_bytes: Mapped[int]=mapped_column(Integer)
    owner_id: Mapped[int]=mapped_column(ForeignKey("users.id"), index=True)
    deleted: Mapped[bool]=mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    owner=relationship("User", foreign_keys=[owner_id])
class Permission(Base):
    __tablename__="permissions"
    __table_args__=(UniqueConstraint("document_id","user_id",name="uq_doc_user_permission"),)
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    document_id: Mapped[int]=mapped_column(ForeignKey("documents.id"), index=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"), index=True)
    permission: Mapped[str]=mapped_column(String(20), default="read")
    granted_by: Mapped[int]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=utcnow)
    user=relationship("User", foreign_keys=[user_id])
class AuditEvent(Base):
    __tablename__="audit_events"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    actor_id: Mapped[int|None]=mapped_column(Integer, nullable=True, index=True)
    actor_email: Mapped[str]=mapped_column(String(320), default="")
    action: Mapped[str]=mapped_column(String(100), index=True)
    resource_type: Mapped[str]=mapped_column(String(50), default="document")
    resource_id: Mapped[str]=mapped_column(String(100), default="")
    outcome: Mapped[str]=mapped_column(String(20), default="success")
    details: Mapped[str]=mapped_column(Text, default="")
    previous_hash: Mapped[str]=mapped_column(String(64), default="")
    event_hash: Mapped[str]=mapped_column(String(64), default="")
