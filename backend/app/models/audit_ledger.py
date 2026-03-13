from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLedgerEntry(Base):
    __tablename__ = "audit_ledger_entries"
    __table_args__ = (
        UniqueConstraint("entry_hash", name="uq_audit_ledger_entry_hash"),
    )

    id = Column(Integer, primary_key=True, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=True, index=True)

    request_method = Column(String(16), nullable=True)
    request_path = Column(String(512), nullable=True)
    ip_address = Column(String(128), nullable=True)
    user_agent = Column(String(512), nullable=True)

    details = Column(JSON, nullable=False, default=dict)

    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)

    user = relationship("User")
