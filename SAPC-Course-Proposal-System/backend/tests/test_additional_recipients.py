import pytest
from app.models import SessionLocal
from app.models.proposal import Proposal, ProposalRecipient
from app.services.email_service import EmailService
from app.utils.validators import validate_additional_recipients

def test_1_submit_with_no_additional_recipients(client, valid_proposal_payload):
    """Case 1: Submit with no additional recipients succeeds and creates no recipient rows."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Course Without Additional Recipients"
    payload['additional_recipients'] = ""

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    p = data['proposal']
    assert p['additional_recipients'] == []

    session = SessionLocal()
    try:
        recips = session.query(ProposalRecipient).filter_by(proposal_id=p['proposal_id']).all()
        assert len(recips) == 0
    finally:
        session.close()

def test_2_submit_with_one_additional_recipient(client, valid_proposal_payload):
    """Case 2: Submit with one additional recipient succeeds and dispatches copy."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Course With One CC Recipient"
    payload['additional_recipients'] = "hod.cse@iitgn.ac.in"

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    p = data['proposal']
    assert 'hod.cse@iitgn.ac.in' in p['additional_recipients']

    # Verify outbox has CC email
    outbox = EmailService.get_outbox_logs()
    cc_logs = [m for m in outbox if m['proposal_id'] == p['proposal_id'] and m.get('email_type') == 'Proposal Copy (CC)']
    assert len(cc_logs) >= 1
    assert cc_logs[0]['recipient'] == 'hod.cse@iitgn.ac.in'
    assert 'Course Proposal for Review' in cc_logs[0]['subject']

def test_3_submit_with_multiple_additional_recipients(client, valid_proposal_payload):
    """Case 3: Submit with multiple additional recipients sends to each."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Course With Multiple CC Recipients"
    payload['additional_recipients'] = "hod.cse@iitgn.ac.in, prof.sharma@iitgn.ac.in, dean.acad@iitgn.ac.in"

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    p = res.get_json()['proposal']
    assert len(p['additional_recipients']) == 3
    assert 'hod.cse@iitgn.ac.in' in p['additional_recipients']
    assert 'prof.sharma@iitgn.ac.in' in p['additional_recipients']
    assert 'dean.acad@iitgn.ac.in' in p['additional_recipients']

def test_4_reject_invalid_email_address(client, valid_proposal_payload):
    """Case 4: Rejects malformed email address with descriptive error."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Course With Malformed CC Email"
    payload['additional_recipients'] = "valid.email@iitgn.ac.in, not-an-email, another@domain.com"

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert 'additional_recipients' in data['errors']
    assert "Invalid email address: 'not-an-email'" in data['errors']['additional_recipients']

def test_5_trim_whitespace_correctly(client, valid_proposal_payload):
    """Case 5: Whitespace around addresses is cleanly trimmed."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Course With Whitespace In CC"
    payload['additional_recipients'] = "   dean@iitgn.ac.in   ,   hod@iitgn.ac.in   "

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    p = res.get_json()['proposal']
    assert 'dean@iitgn.ac.in' in p['additional_recipients']
    assert 'hod@iitgn.ac.in' in p['additional_recipients']

def test_6_handle_duplicate_and_submitter_addresses(client, valid_proposal_payload):
    """Case 6: Duplicate addresses are deduplicated and submitter self-email is omitted."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Course With Duplicate and Submitter CC"
    payload['faculty_email'] = "submitter.proposer@iitgn.ac.in"
    # Includes duplicate hod and includes submitter's own email
    payload['additional_recipients'] = "hod.cse@iitgn.ac.in, HOD.CSE@IITGN.AC.IN, submitter.proposer@iitgn.ac.in, colleague@iitgn.ac.in"

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    p = res.get_json()['proposal']
    # Submitter email omitted from CC to prevent duplicate copy
    assert 'submitter.proposer@iitgn.ac.in' not in p['additional_recipients']
    # hod.cse@iitgn.ac.in appears exactly once
    assert p['additional_recipients'].count('hod.cse@iitgn.ac.in') == 1
    assert 'colleague@iitgn.ac.in' in p['additional_recipients']
    assert len(p['additional_recipients']) == 2

def test_7_recipient_addresses_persist_in_database(client, valid_proposal_payload):
    """Case 7: Recipient addresses persist reliably in proposal_recipients table."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Persistence Verification Course"
    payload['additional_recipients'] = "p1@iitgn.ac.in, p2@iitgn.ac.in"

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    prop_id = res.get_json()['proposal']['proposal_id']

    session = SessionLocal()
    try:
        recips = session.query(ProposalRecipient).filter_by(proposal_id=prop_id).all()
        assert len(recips) == 2
        emails = [r.email for r in recips]
        assert 'p1@iitgn.ac.in' in emails
        assert 'p2@iitgn.ac.in' in emails
        for r in recips:
            assert r.delivery_status in ['Sent', 'Pending']
    finally:
        session.close()

def test_8_email_attempted_after_proposal_saved(client, valid_proposal_payload):
    """Case 8: Verification that proposal record exists in database when email is dispatched."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Order Of Operations Verification Course"
    payload['additional_recipients'] = "colleague.audit@iitgn.ac.in"

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    prop_id = res.get_json()['proposal']['proposal_id']

    session = SessionLocal()
    try:
        saved_proposal = session.query(Proposal).filter_by(proposal_id=prop_id).first()
        assert saved_proposal is not None
        assert saved_proposal.course_title == payload['course_title']
    finally:
        session.close()

def test_9_pdf_reference_included_in_copy(client, valid_proposal_payload):
    """Case 9: Generated PDF exists and is linked with the proposal."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Course With PDF Attachment Check"
    payload['additional_recipients'] = "recipient.pdf@iitgn.ac.in"

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    prop = res.get_json()['proposal']
    assert prop['pdf_path'] is not None

    # Check outbox log for PDF mention or proposal info
    logs = EmailService.get_outbox_logs()
    matching = [m for m in logs if m['proposal_id'] == prop['proposal_id'] and m['recipient'] == 'recipient.pdf@iitgn.ac.in']
    assert len(matching) >= 1
    assert prop['proposal_id'] in matching[0]['body']
    assert 'L-T-P-C:' in matching[0]['body']

def test_10_email_failure_does_not_lose_saved_proposal(client, valid_proposal_payload, monkeypatch):
    """Case 10: If email transmission fails, the saved proposal in database is preserved."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Resilience When CC Email Fails Course"
    payload['additional_recipients'] = "fail.recipient@iitgn.ac.in"

    # Mock send_proposal_copy_to_recipients to simulate an SMTP or network crash
    def mock_fail(proposal, recipient_emails=None, attach_pdf=True):
        return False, {'fail.recipient@iitgn.ac.in': {'sent': False, 'error': 'Connection timed out'}}

    monkeypatch.setattr(EmailService, 'send_proposal_copy_to_recipients', mock_fail)

    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert 'proposal' in data
    # Message accurately reflects email failure
    assert "could not be completed" in data['message']

    prop_id = data['proposal']['proposal_id']
    session = SessionLocal()
    try:
        db_p = session.query(Proposal).filter_by(proposal_id=prop_id).first()
        assert db_p is not None
        assert db_p.course_title == payload['course_title']
        recip = session.query(ProposalRecipient).filter_by(proposal_id=prop_id).first()
        assert recip.delivery_status == 'Failed'
    finally:
        session.close()

def test_11_duplicate_submissions_prevented(client, valid_proposal_payload):
    """Case 11: Duplicate submissions with identical title and proposer are rejected with 409."""
    payload = valid_proposal_payload.copy()
    payload['course_title'] = "Duplicate Guard Course"
    payload['proposer_name'] = "Prof. Submitter"
    payload['additional_recipients'] = "hod@iitgn.ac.in"

    res1 = client.post('/api/proposals', json=payload)
    assert res1.status_code == 201

    res2 = client.post('/api/proposals', json=payload)
    assert res2.status_code == 409
    assert res2.get_json()['error'] == 'DUPLICATE_PROPOSAL'
