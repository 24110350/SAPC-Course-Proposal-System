import pytest
from datetime import datetime, timezone, timedelta
from app.models.deadline import DeadlineSetting
from app.models import SessionLocal

def test_deadline_status_endpoint(client):
    res = client.get('/api/deadline')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'deadline' in data
    assert 'is_open' in data['deadline']
    assert 'submission_deadline' in data['deadline']

def test_boundary_before_deadline():
    """Submission made well before the deadline must be accepted."""
    start = datetime(2026, 10, 1, 9, 0, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 10, 15, 23, 59, 59, tzinfo=timezone.utc)
    setting = DeadlineSetting(submission_start=start, submission_deadline=deadline, is_active=True)

    check_time = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    is_open, msg = setting.is_currently_open(check_time)
    assert is_open is True
    assert "open" in msg.lower()

def test_boundary_slightly_before_deadline():
    """Submission made 10 seconds before deadline must be accepted."""
    start = datetime(2026, 10, 1, 9, 0, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 10, 15, 23, 59, 59, tzinfo=timezone.utc)
    setting = DeadlineSetting(submission_start=start, submission_deadline=deadline, is_active=True)

    check_time = deadline - timedelta(seconds=10)
    is_open, msg = setting.is_currently_open(check_time)
    assert is_open is True

def test_boundary_exactly_at_deadline():
    """Submission made exactly at the deadline timestamp must be accepted."""
    start = datetime(2026, 10, 1, 9, 0, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 10, 15, 23, 59, 59, tzinfo=timezone.utc)
    setting = DeadlineSetting(submission_start=start, submission_deadline=deadline, is_active=True)

    is_open, msg = setting.is_currently_open(deadline)
    assert is_open is True

def test_boundary_immediately_after_deadline():
    """Submission made 1 second after deadline must be rejected."""
    start = datetime(2026, 10, 1, 9, 0, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 10, 15, 23, 59, 59, tzinfo=timezone.utc)
    setting = DeadlineSetting(submission_start=start, submission_deadline=deadline, is_active=True)

    check_time = deadline + timedelta(seconds=1)
    is_open, msg = setting.is_currently_open(check_time)
    assert is_open is False
    assert "closed" in msg.lower()

def test_boundary_well_after_deadline():
    """Submission made days after deadline must be rejected."""
    start = datetime(2026, 10, 1, 9, 0, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 10, 15, 23, 59, 59, tzinfo=timezone.utc)
    setting = DeadlineSetting(submission_start=start, submission_deadline=deadline, is_active=True)

    check_time = deadline + timedelta(days=5)
    is_open, msg = setting.is_currently_open(check_time)
    assert is_open is False
    assert "closed" in msg.lower()

def test_boundary_check_api_endpoint(client):
    """Test boundary check API endpoint with various timestamps."""
    deadline_ts = "2026-10-15T23:59:59+00:00"
    
    # Configure known deadline
    session = SessionLocal()
    setting = session.query(DeadlineSetting).order_by(DeadlineSetting.id.desc()).first()
    setting.submission_start = datetime(2026, 10, 1, 9, 0, 0, tzinfo=timezone.utc)
    setting.submission_deadline = datetime(2026, 10, 15, 23, 59, 59, tzinfo=timezone.utc)
    setting.is_active = True
    session.commit()
    session.close()

    # Case 1: 1 second before
    res1 = client.post('/api/deadline/boundary-check', json={'check_time': "2026-10-15T23:59:58+00:00"})
    assert res1.status_code == 200
    assert res1.get_json()['is_open'] is True

    # Case 2: exactly at deadline
    res2 = client.post('/api/deadline/boundary-check', json={'check_time': "2026-10-15T23:59:59+00:00"})
    assert res2.status_code == 200
    assert res2.get_json()['is_open'] is True

    # Case 3: 1 second after
    res3 = client.post('/api/deadline/boundary-check', json={'check_time': "2026-10-16T00:00:00+00:00"})
    assert res3.status_code == 200
    assert res3.get_json()['is_open'] is False

def test_submission_rejection_when_deadline_passed(client, valid_proposal_payload):
    """
    Simulate closed deadline by configuring deadline in the past.
    Verifies that the Flask backend independently blocks proposal submission with HTTP 403.
    """
    session = SessionLocal()
    setting = session.query(DeadlineSetting).order_by(DeadlineSetting.id.desc()).first()
    orig_deadline = setting.submission_deadline
    orig_start = setting.submission_start

    try:
        # Set deadline to 2 days ago
        now = datetime.now(timezone.utc)
        setting.submission_start = now - timedelta(days=10)
        setting.submission_deadline = now - timedelta(days=2)
        session.commit()

        payload = valid_proposal_payload.copy()
        payload['course_title'] = "Attempted Submission After Closed Deadline"
        res = client.post('/api/proposals', json=payload)
        assert res.status_code == 403
        data = res.get_json()
        assert data['success'] is False
        assert data['error'] == 'SUBMISSION_CLOSED'
        assert "closed" in data['message'].lower()
    finally:
        # Restore active deadline
        setting.submission_start = orig_start
        setting.submission_deadline = orig_deadline
        session.commit()
        session.close()

def test_admin_updates_deadline(client, admin_headers):
    """
    Verifies that an authorized Academic Office administrator can update
    the deadline and the updated configuration takes effect immediately.
    """
    new_start = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    new_deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    new_message = "Extended submission period by Academic Office Senate decision."

    res = client.put('/api/deadline', headers=admin_headers, json={
        'submission_start': new_start,
        'submission_deadline': new_deadline,
        'is_active': True,
        'announcement_message': new_message
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['deadline']['announcement_message'] == new_message
    assert data['deadline']['is_open'] is True
