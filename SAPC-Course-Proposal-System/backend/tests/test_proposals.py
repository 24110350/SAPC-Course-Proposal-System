import json
import pytest
from app.models.proposal import Proposal
from app.models.deadline import DeadlineSetting
from datetime import datetime, timezone, timedelta

def test_health_check(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'healthy'

def test_successful_proposal_submission(client, valid_proposal_payload):
    res = client.post('/api/proposals', json=valid_proposal_payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert 'proposal' in data
    p = data['proposal']
    assert p['course_title'] == valid_proposal_payload['course_title']
    assert p['faculty_email'] == valid_proposal_payload['faculty_email']
    assert p['proposal_id'].startswith('SAPC-')
    assert p['pdf_path'] is not None
    assert p['email_notification_status'] in ['Sent', 'Pending']

def test_validation_missing_required_fields(client):
    res = client.post('/api/proposals', json={
        "course_title": "Incomplete Course"
    })
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert 'errors' in data
    assert 'potential_instructors' in data['errors']
    assert 'proposer_name' in data['errors']
    assert 'faculty_email' in data['errors']
    assert 'course_type' in data['errors']
    assert 'course_level' in data['errors']

def test_validation_invalid_email(client, valid_proposal_payload):
    payload = valid_proposal_payload.copy()
    payload['faculty_email'] = 'not-a-valid-email'
    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert 'faculty_email' in data['errors']

def test_validation_modification_requires_existing_code(client, valid_proposal_payload):
    payload = valid_proposal_payload.copy()
    payload['is_modification'] = True
    payload['existing_course_code'] = ''
    payload['course_title'] = 'Modification Without Existing Code'
    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert 'existing_course_code' in data['errors']

def test_validation_modification_with_existing_code_succeeds(client, valid_proposal_payload):
    payload = valid_proposal_payload.copy()
    payload['is_modification'] = True
    payload['existing_course_code'] = 'CS-401'
    payload['course_title'] = 'Modified Algorithmic Game Theory'
    res = client.post('/api/proposals', json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert data['proposal']['is_modification'] is True
    assert data['proposal']['existing_course_code'] == 'CS-401'

def test_duplicate_proposal_rejection(client, valid_proposal_payload):
    payload = valid_proposal_payload.copy()
    payload['course_title'] = 'Unique Test Course for Duplicate Check'
    payload['proposer_name'] = 'Dr. Unique Professor'
    
    # First submission
    res1 = client.post('/api/proposals', json=payload)
    assert res1.status_code == 201
    
    # Immediate duplicate submission attempt
    res2 = client.post('/api/proposals', json=payload)
    assert res2.status_code == 409
    data2 = res2.get_json()
    assert data2['success'] is False
    assert data2['error'] == 'DUPLICATE_PROPOSAL'

def test_proposal_listing_and_filtering(client):
    res = client.get('/api/proposals')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert isinstance(data['proposals'], list)
    assert data['total'] >= 1
    assert 'stats' in data

    # Filter by status
    res_pending = client.get('/api/proposals?status=Pending')
    assert res_pending.status_code == 200
    for p in res_pending.get_json()['proposals']:
        assert p['status'] == 'Pending'

def test_proposal_search(client, valid_proposal_payload):
    payload = valid_proposal_payload.copy()
    payload['course_title'] = 'Quantum Computing with Neutral Atoms'
    payload['proposer_name'] = 'Dr. Satyendra Bose'
    client.post('/api/proposals', json=payload)

    # Search by title keyword
    res = client.get('/api/proposals?q=Quantum')
    assert res.status_code == 200
    items = res.get_json()['proposals']
    assert any('Quantum' in p['course_title'] for p in items)

    # Search by proposer
    res_prop = client.get('/api/proposals?q=Satyendra')
    assert res_prop.status_code == 200
    items_prop = res_prop.get_json()['proposals']
    assert any('Satyendra' in p['proposer_name'] for p in items_prop)

def test_update_status(client, admin_headers, valid_proposal_payload):
    payload = valid_proposal_payload.copy()
    payload['course_title'] = 'Status Update Lifecycle Test Course'
    create_res = client.post('/api/proposals', json=payload)
    assert create_res.status_code == 201
    prop_id = create_res.get_json()['proposal']['proposal_id']

    # Update status to Under Review
    patch_res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Under Review', 'remarks': 'Under committee evaluation'}
    )
    assert patch_res.status_code == 200
    data = patch_res.get_json()
    assert data['proposal']['status'] == 'Under Review'

    # Verify detail route shows history
    detail_res = client.get(f'/api/proposals/{prop_id}')
    assert detail_res.status_code == 200
    detail = detail_res.get_json()['proposal']
    assert detail['status'] == 'Under Review'
    assert len(detail['history']) >= 2
