from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from .proposal import Base

class AdminUser(Base):
    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='Academic Office')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ProposalStatusHistory(Base):
    __tablename__ = 'proposal_status_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String(50), ForeignKey('proposals.proposal_id', ondelete='CASCADE'), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    remarks = Column(Text, nullable=True)
    changed_by = Column(String(100), nullable=False)
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'proposal_id': self.proposal_id,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'remarks': self.remarks,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None
        }
