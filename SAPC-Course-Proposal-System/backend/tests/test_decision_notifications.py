import pytest
from app.models import SessionLocal
from app.models.proposal import Proposal
from app.services.email_service import EmailService

def create_sample_proposal(client, valid_proposal_payload, title="Decision Test Course"):
    payload = valid_proposal_payload.copy()
    payload['course_title'] = title
    payload['faculty_email'] = "faculty.proposer@iitgn.ac.in"
    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    return res.get_json()['proposal']['proposal_id']

def test_12_approved_status_triggers_email(client, admin_headers, valid_proposal_payload):
    """Case 12: Changing status to Approved triggers an email to the submitter."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course To Be Approved")

    patch_res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Approved', 'remarks': 'Meets all academic curriculum criteria.'}
    )
    assert patch_res.status_code == 200
    data = patch_res.get_json()
    assert data['proposal']['status'] == 'Approved'
    assert data['decision_notification']['sent'] is True

    # Check outbox log
    outbox = EmailService.get_outbox_logs()
    dec_logs = [m for m in outbox if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification']
    assert len(dec_logs) >= 1
    assert dec_logs[0]['recipient'] == 'faculty.proposer@iitgn.ac.in'
    assert 'SAPC Course Proposal Approved' in dec_logs[0]['subject']
    assert 'Decision: Approved' in dec_logs[0]['body']
    assert 'Meets all academic curriculum criteria.' in dec_logs[0]['body']

def test_13_rejected_status_triggers_email(client, admin_headers, valid_proposal_payload):
    """Case 13: Changing status to Rejected triggers an email to submitter with comments."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course To Be Rejected")

    patch_res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Rejected', 'remarks': 'Significant content overlap with existing course CS-501.'}
    )
    assert patch_res.status_code == 200
    data = patch_res.get_json()
    assert data['proposal']['status'] == 'Rejected'
    assert data['decision_notification']['sent'] is True

    outbox = EmailService.get_outbox_logs()
    dec_logs = [m for m in outbox if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification']
    assert len(dec_logs) >= 1
    assert 'SAPC Course Proposal Rejected' in dec_logs[0]['subject']
    assert 'Significant content overlap with existing course CS-501.' in dec_logs[0]['body']

def test_14_modification_required_triggers_email(client, admin_headers, valid_proposal_payload):
    """Case 14: Changing status to Modification Required triggers email with requested changes."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course Needing Modification")

    patch_res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Modification Required', 'remarks': 'Please revise syllabus to include practical laboratory component.'}
    )
    assert patch_res.status_code == 200
    data = patch_res.get_json()
    assert data['proposal']['status'] == 'Modification Required'
    assert data['decision_notification']['sent'] is True

    outbox = EmailService.get_outbox_logs()
    dec_logs = [m for m in outbox if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification']
    assert len(dec_logs) >= 1
    assert 'Modifications Required' in dec_logs[0]['subject']
    assert 'Please revise syllabus to include practical laboratory component.' in dec_logs[0]['body']

def test_15_pending_status_does_not_trigger_decision_email(client, admin_headers, valid_proposal_payload):
    """Case 15: Setting status to Pending does not dispatch a decision email."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course Kept As Pending")

    # Change to Under Review first then back to Pending
    client.patch(f'/api/proposals/{prop_id}/status', headers=admin_headers, json={'status': 'Under Review'})
    
    outbox_before = len([m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification'])

    patch_res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Pending', 'remarks': 'Awaiting further documents'}
    )
    assert patch_res.status_code == 200
    assert patch_res.get_json()['decision_notification'] is None

    outbox_after = len([m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification'])
    assert outbox_after == outbox_before

def test_16_under_review_status_does_not_trigger_decision_email(client, admin_headers, valid_proposal_payload):
    """Case 16: Setting status to Under Review does not dispatch a decision email."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course Under Active Review")

    patch_res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Under Review', 'remarks': 'Circulating to committee members.'}
    )
    assert patch_res.status_code == 200
    assert patch_res.get_json()['decision_notification'] is None

    outbox = EmailService.get_outbox_logs()
    dec_logs = [m for m in outbox if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification']
    assert len(dec_logs) == 0

def test_17_saving_same_decision_repeatedly_does_not_trigger_duplicate_emails(client, admin_headers, valid_proposal_payload):
    """Case 17: Saving the same decision status repeatedly does not send duplicate emails."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course Repeat Save Test")
    
    count_before = len([m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification'])

    # First decision: Approved
    res1 = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Approved', 'remarks': 'Approved first time'}
    )
    assert res1.status_code == 200
    assert res1.get_json()['decision_notification']['sent'] is True

    count_after_first = len([m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification'])
    assert count_after_first == count_before + 1

    # Second save with identical status: Approved
    res2 = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Approved', 'remarks': 'Saved again without status change'}
    )
    assert res2.status_code == 200
    # No new decision email sent
    assert res2.get_json()['decision_notification'] is None

    count_after_second = len([m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification'])
    assert count_after_second == count_after_first  # Exactly unchanged!

def test_18_changing_decision_to_different_decision_sends_new_notification(client, admin_headers, valid_proposal_payload):
    """Case 18: Changing decision from Rejected to Approved sends a new notification."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course Decision Reversal Test")

    count_before = len([m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification'])

    # Step 1: Reject proposal
    res1 = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Rejected', 'remarks': 'Initial rejection due to prerequisites'}
    )
    assert res1.status_code == 200
    assert res1.get_json()['decision_notification']['sent'] is True

    count_after_reject = len([m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification'])
    assert count_after_reject == count_before + 1

    # Step 2: Later decision: Approved
    res2 = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Approved', 'remarks': 'Appeal reviewed and course approved.'}
    )
    assert res2.status_code == 200
    assert res2.get_json()['decision_notification']['sent'] is True

    count_after_approve = len([m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification'])
    assert count_after_approve == count_before + 2

    # Verify latest notification has Approved in subject
    logs = [m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification']
    assert 'Approved' in logs[0]['subject']

def test_19_reviewer_comments_included_when_available(client, admin_headers, valid_proposal_payload):
    """Case 19: Reviewer comments are prominently included in the decision email body."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course Comments Check")
    custom_comment = "Specific SAPC committee note: Course code recommended is CS-620."

    res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Modification Required', 'remarks': custom_comment}
    )
    assert res.status_code == 200

    logs = [m for m in EmailService.get_outbox_logs() if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification']
    assert len(logs) >= 1
    assert custom_comment in logs[0]['body']

def test_20_unauthorized_users_cannot_change_decision_status(client, valid_proposal_payload):
    """Case 20: Unauthorized requests cannot update status or trigger decision emails."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course Unauthorized Test")

    # No auth header
    res_no_auth = client.patch(
        f'/api/proposals/{prop_id}/status',
        json={'status': 'Approved', 'remarks': 'Illegitimate update'}
    )
    assert res_no_auth.status_code == 401

    # Fake auth header
    res_bad_auth = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers={'Authorization': 'Bearer bad-token-here'},
        json={'status': 'Approved'}
    )
    assert res_bad_auth.status_code == 401

    # Ensure status in DB remained Pending
    session = SessionLocal()
    try:
        p = session.query(Proposal).filter_by(proposal_id=prop_id).first()
        assert p.status == 'Pending'
    finally:
        session.close()

def test_21_email_failure_does_not_corrupt_proposal_status(client, admin_headers, valid_proposal_payload, monkeypatch):
    """Case 21: An email dispatch failure does not corrupt or roll back a saved decision."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course Email Failure Status Check")

    # Simulate email service error
    def mock_email_fail(*args, **kwargs):
        return False, "SMTP Connection refused by mail gateway"

    monkeypatch.setattr(EmailService, 'send_decision_notification', mock_email_fail)

    res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Approved', 'remarks': 'Approved despite network email glitch'}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    # Proposal status was safely saved as Approved
    assert data['proposal']['status'] == 'Approved'
    assert data['decision_notification']['sent'] is False
    assert "SMTP Connection refused" in data['decision_notification']['error']

    # Verify DB has Approved status
    session = SessionLocal()
    try:
        p = session.query(Proposal).filter_by(proposal_id=prop_id).first()
        assert p.status == 'Approved'
    finally:
        session.close()

def test_22_existing_email_outbox_continues_working(client, admin_headers, valid_proposal_payload):
    """Case 22: Admin outbox endpoint correctly displays logged decision emails."""
    prop_id = create_sample_proposal(client, valid_proposal_payload, "Course Outbox Verification")

    client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Approved', 'remarks': 'Outbox audit test'}
    )

    outbox_res = client.get('/api/auth/outbox', headers=admin_headers)
    assert outbox_res.status_code == 200
    outbox_data = outbox_res.get_json()
    assert outbox_data['success'] is True
    assert outbox_data['count'] > 0
    
    # Check that decision notification is present
    emails = outbox_data['emails']
    matching = [m for m in emails if m['proposal_id'] == prop_id and m.get('email_type') == 'Decision Notification']
    assert len(matching) >= 1
    assert matching[0]['status'] == 'Simulated Delivered (Local Mailbox)'
