from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Numeric, DateTime, Index, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Proposal(Base):
    __tablename__ = 'proposals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String(50), unique=True, nullable=False, index=True)
    edit_token = Column(String(100), unique=True, nullable=True, index=True)
    submission_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    status = Column(String(50), nullable=False, default='Pending', index=True)
    # Valid statuses: 'Pending', 'Under Review', 'Approved', 'Rejected', 'Modification Required'

    # Course Identification & Proposer
    course_title = Column(String(255), nullable=False, index=True)
    potential_instructors = Column(Text, nullable=False)
    proposer_name = Column(String(255), nullable=False, index=True)
    faculty_email = Column(String(255), nullable=False, index=True)

    # Classification & Structure
    course_type = Column(String(50), nullable=False, index=True)
    course_type_other = Column(String(100), nullable=True)
    course_level = Column(String(20), nullable=False, index=True)
    course_level_secondary = Column(String(20), nullable=True)
    course_l_t_p_c = Column(String(50), nullable=False)
    lecture_hours = Column(Numeric(4, 1), default=0.0)
    tutorial_hours = Column(Numeric(4, 1), default=0.0)
    practical_hours = Column(Numeric(4, 1), default=0.0)
    credits = Column(Numeric(4, 1), default=0.0)
    course_duration = Column(String(50), nullable=False)
    expected_frequency = Column(String(50), nullable=False)
    expected_frequency_other = Column(String(100), nullable=True)

    # Curricular Classifications & Elective Baskets
    elective_basket_btech = Column(String(50), nullable=True)
    discipline_elective_btech = Column(String(50), nullable=True)
    discipline_basket_btech = Column(String(255), nullable=True)
    minors = Column(Text, nullable=True)
    minor_basket_thematic_area = Column(String(255), nullable=True)
    minor_reason = Column(Text, nullable=True)  # Reason for Adding the Course as a Minor
    discipline_elective_msc = Column(String(50), nullable=True)
    courses_discipline_mtech = Column(String(50), nullable=True)
    mtech_sub_specialization = Column(String(255), nullable=True)
    discipline_elective_mdes = Column(String(50), nullable=True)

    # Course Nature
    is_modification = Column(Boolean, nullable=False, default=False, index=True)
    existing_course_code = Column(String(50), nullable=True)

    # Academic Syllabus & Detailed Content
    prior_knowledge = Column(Text, nullable=True)
    course_contents = Column(Text, nullable=False)
    texts_and_references = Column(Text, nullable=False)
    learning_outcomes = Column(Text, nullable=False)
    overlap_courses = Column(Text, nullable=True)
    other_relevant_info = Column(Text, nullable=True)

    # PDF Reference
    pdf_path = Column(String(500), nullable=True)
    pdf_filename = Column(String(255), nullable=True)

    # Notification Tracking
    email_notification_status = Column(String(50), nullable=False, default='Pending')
    email_error_log = Column(Text, nullable=True)

    # Security Department Notification Tracking (Requirement 6)
    security_email_status = Column(String(50), nullable=False, default='Pending')
    security_email_error = Column(Text, nullable=True)

    # Reviewer Decision & Comments
    reviewer_comments = Column(Text, nullable=True)
    last_decision_notified = Column(String(50), nullable=True)

    # SAPC Official Record & Approval (Requirement 8)
    sapc_number = Column(String(100), nullable=True, index=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)

    # Dynamic Custom Fields JSON storage (Requirement 5)
    custom_fields_data = Column(Text, nullable=True)

    # Related Additional Recipients (CC)
    recipients = relationship("ProposalRecipient", backref="proposal", cascade="all, delete-orphan", lazy="joined")

    # Complete Proposal Edit History (Requirement 2)
    edit_history = relationship("ProposalEditHistory", backref="proposal", cascade="all, delete-orphan", lazy="select", order_by="desc(ProposalEditHistory.edited_at)")

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'proposal_id': self.proposal_id,
            'edit_token': self.edit_token,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'status': self.status,
            'course_title': self.course_title,
            'potential_instructors': self.potential_instructors,
            'proposer_name': self.proposer_name,
            'faculty_email': self.faculty_email,
            'course_type': self.course_type,
            'course_type_other': self.course_type_other,
            'course_level': self.course_level,
            'course_level_secondary': self.course_level_secondary,
            'course_l_t_p_c': self.course_l_t_p_c,
            'lecture_hours': float(self.lecture_hours) if self.lecture_hours is not None else 0.0,
            'tutorial_hours': float(self.tutorial_hours) if self.tutorial_hours is not None else 0.0,
            'practical_hours': float(self.practical_hours) if self.practical_hours is not None else 0.0,
            'credits': float(self.credits) if self.credits is not None else 0.0,
            'course_duration': self.course_duration,
            'expected_frequency': self.expected_frequency,
            'expected_frequency_other': self.expected_frequency_other,
            'elective_basket_btech': self.elective_basket_btech,
            'discipline_elective_btech': self.discipline_elective_btech,
            'discipline_basket_btech': self.discipline_basket_btech,
            'minors': self.minors,
            'minor_basket_thematic_area': self.minor_basket_thematic_area,
            'minor_reason': self.minor_reason,
            'discipline_elective_msc': self.discipline_elective_msc,
            'courses_discipline_mtech': self.courses_discipline_mtech,
            'mtech_sub_specialization': self.mtech_sub_specialization,
            'discipline_elective_mdes': self.discipline_elective_mdes,
            'is_modification': self.is_modification,
            'existing_course_code': self.existing_course_code,
            'prior_knowledge': self.prior_knowledge,
            'course_contents': self.course_contents,
            'texts_and_references': self.texts_and_references,
            'learning_outcomes': self.learning_outcomes,
            'overlap_courses': self.overlap_courses,
            'other_relevant_info': self.other_relevant_info,
            'pdf_path': self.pdf_path,
            'pdf_filename': self.pdf_filename,
            'email_notification_status': self.email_notification_status,
            'email_error_log': self.email_error_log,
            'security_email_status': self.security_email_status,
            'security_email_error': self.security_email_error,
            'reviewer_comments': self.reviewer_comments,
            'last_decision_notified': self.last_decision_notified,
            'sapc_number': self.sapc_number,
            'approval_date': self.approval_date.isoformat() if self.approval_date else None,
            'custom_fields_data': self.custom_fields_data,
            'additional_recipients': [r.email for r in self.recipients] if hasattr(self, 'recipients') and self.recipients else [],
            'additional_recipients_detail': [r.to_dict() for r in self.recipients] if hasattr(self, 'recipients') and self.recipients else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ProposalEditHistory(Base):
    __tablename__ = 'proposal_edit_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String(50), ForeignKey('proposals.proposal_id', ondelete='CASCADE'), nullable=False, index=True)
    edited_by = Column(String(255), nullable=False)
    edited_by_role = Column(String(50), nullable=False, default='Professor') # 'Professor' or 'Academic Office'
    changes_summary = Column(Text, nullable=True)
    changes_json = Column(Text, nullable=True)
    edited_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'proposal_id': self.proposal_id,
            'edited_by': self.edited_by,
            'edited_by_role': self.edited_by_role,
            'changes_summary': self.changes_summary,
            'changes_json': self.changes_json,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
        }


class ProposalRecipient(Base):
    __tablename__ = 'proposal_recipients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String(50), ForeignKey('proposals.proposal_id', ondelete='CASCADE'), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    delivery_status = Column(String(50), nullable=False, default='Pending')  # 'Pending', 'Sent', 'Failed'
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'proposal_id': self.proposal_id,
            'email': self.email,
            'delivery_status': self.delivery_status,
            'error_message': self.error_message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
