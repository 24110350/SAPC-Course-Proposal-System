import pytest
from datetime import datetime, timezone
from app.models.proposal import Proposal
from app.models.deadline import DeadlineSetting
from app.models.user import AdminUser, ProposalStatusHistory

def test_database_proposal_crud(db_session):
    p = Proposal(
        proposal_id='SAPC-DB-TEST-001',
        submission_date=datetime.now(timezone.utc),
        status='Pending',
        course_title='Database Management Systems Lab',
        potential_instructors='Dr. Database Expert',
        proposer_name='Dr. Database Expert',
        faculty_email='db.expert@test.iitgn.ac.in',
        course_type='CS',
        course_level='3',
        course_l_t_p_c='0-0-3-2',
        lecture_hours=0.0,
        tutorial_hours=0.0,
        practical_hours=3.0,
        credits=2.0,
        course_duration='4 Quads (Full Semester)',
        expected_frequency='Each Semester',
        course_contents='SQL queries; transaction isolation levels; index optimization.',
        texts_and_references='Silberschatz et al. Database System Concepts.',
        learning_outcomes='Master relational database query execution and indexing.'
    )
    db_session.add(p)
    db_session.commit()

    # Query back
    fetched = db_session.query(Proposal).filter_by(proposal_id='SAPC-DB-TEST-001').first()
    assert fetched is not None
    assert fetched.course_title == 'Database Management Systems Lab'
    assert fetched.credits == 2.0

    # Update
    fetched.status = 'Approved'
    db_session.commit()

    updated = db_session.query(Proposal).filter_by(proposal_id='SAPC-DB-TEST-001').first()
    assert updated.status == 'Approved'

def test_database_admin_password_hashing(db_session):
    admin = AdminUser(username='testadmin', role='Academic Office')
    admin.set_password('SecretPass123!')
    db_session.add(admin)
    db_session.commit()

    queried = db_session.query(AdminUser).filter_by(username='testadmin').first()
    assert queried is not None
    assert queried.check_password('SecretPass123!') is True
    assert queried.check_password('WrongPass') is False
