from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from .proposal import Base

class DeadlineSetting(Base):
    __tablename__ = 'deadline_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_start = Column(DateTime(timezone=True), nullable=False)
    submission_deadline = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    announcement_message = Column(Text, nullable=True)
    updated_by = Column(String(100), default='Academic Office Admin')
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def is_currently_open(self, check_time=None):
        """
        Server-side validation of submission window.
        Boundary conditions:
        - Submission is open if check_time >= submission_start AND check_time <= submission_deadline
        - is_active must be True
        """
        if not self.is_active:
            return False, "Course proposal submissions are currently suspended by the Academic Office."

        if check_time is None:
            check_time = datetime.now(timezone.utc)
        elif check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=timezone.utc)

        start = self.submission_start
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        deadline = self.submission_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if check_time < start:
            return False, f"Course proposal submissions have not yet opened. Submissions open on {start.strftime('%d %B %Y, %I:%M %p UTC')}."

        if check_time > deadline:
            return False, f"Course proposal submissions are currently closed. Submission deadline was {deadline.strftime('%d %B %Y, %I:%M %p UTC')}."

        return True, "Submissions are currently open."

    def to_dict(self, check_time=None):
        if check_time is None:
            check_time = datetime.now(timezone.utc)
        elif check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=timezone.utc)

        is_open, reason = self.is_currently_open(check_time)
        
        deadline = self.submission_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
            
        remaining_seconds = max(0, int((deadline - check_time).total_seconds()))

        return {
            'id': self.id,
            'submission_start': self.submission_start.isoformat(),
            'submission_deadline': self.submission_deadline.isoformat(),
            'is_active': self.is_active,
            'announcement_message': self.announcement_message,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_open': is_open,
            'status_message': reason,
            'time_remaining_seconds': remaining_seconds,
            'server_time': check_time.isoformat()
        }
