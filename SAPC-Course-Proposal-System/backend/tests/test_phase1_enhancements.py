import os
import io
import json
import pytest
from datetime import datetime, timezone, timedelta
import openpyxl
from app import create_app
from app.config import TestConfig
from app.models import init_db, SessionLocal, remove_session
from app.models.proposal import Proposal, ProposalEditHistory
from app.models.deadline import DeadlineSetting
from app.models.form_config import FormFieldOption, CustomFormField
from app.utils.auth_helper import generate_auth_token

@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app
    remove_session()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(app):
    with app.app_context():
        return generate_auth_token(username='admin', role='Academic Office')

@pytest.fixture
def sample_proposal_data():
    return {
        'course_title': 'Introduction to Deep Learning and Neural Systems',
        'potential_instructors': 'Dr. Alok Verma; Dr. Preeti Rao',
        'proposer_name': 'Dr. Alok Verma',
        'faculty_email': 'alok.verma@demo.iitgn.ac.in',
        'course_type': 'CS',
        'course_level': '4',
        'course_duration': '4 Quads (Full Semester)',
        'expected_frequency': 'Each Year',
        'lecture_hours': 3,
        'tutorial_hours': 0,
        'practical_hours': 2,
        'credits': 4,
        'elective_basket_btech': 'Science',
        'discipline_elective_btech': 'CS',
        'minors': 'AI, CS',
        'minor_reason': 'Provides foundational neural network fundamentals essential for the Minor in AI.',
        'is_modification': False,
        'course_contents': 'Foundations of artificial neural networks; forward and backpropagation; optimization; CNNs; RNNs; transformers.',
        'texts_and_references': 'Goodfellow et al., Deep Learning, MIT Press, 2016.',
        'learning_outcomes': 'Design, train, and evaluate modern deep learning architectures for real-world tasks.'
    }

# ==============================================================================
# Feature 1: Official PDF Download for Professor & Admin
# ==============================================================================
def test_feature1_professor_pdf_download(client, sample_proposal_data):
    res = client.post('/api/proposals', json=sample_proposal_data)
    assert res.status_code == 201
    prop_id = res.get_json()['proposal']['proposal_id']

    # Download endpoint accessible to professor without requiring admin login
    pdf_res = client.get(f'/api/proposals/{prop_id}/pdf')
    assert pdf_res.status_code == 200
    assert pdf_res.headers['Content-Type'] == 'application/pdf'
    assert f"{prop_id}.pdf" in pdf_res.headers['Content-Disposition']

    # Inline view endpoint also accessible
    view_res = client.get(f'/api/proposals/{prop_id}/pdf/view')
    assert view_res.status_code == 200
    assert view_res.headers['Content-Type'] == 'application/pdf'

# ==============================================================================
# Feature 2: Professor Secure Editing via Unguessable Token & Admin Editing
# ==============================================================================
def test_feature2_professor_and_admin_editing(client, admin_token, sample_proposal_data):
    # 1. Create proposal
    res = client.post('/api/proposals', json=sample_proposal_data)
    assert res.status_code == 201
    data = res.get_json()
    prop_id = data['proposal']['proposal_id']
    edit_token = data['edit_token']
    assert edit_token and len(edit_token) >= 32

    # 2. Fetch proposal by edit token
    token_res = client.get(f'/api/proposals/by-token/{edit_token}')
    assert token_res.status_code == 200
    assert token_res.get_json()['proposal']['proposal_id'] == prop_id

    # 3. Invalid / guessed token rejected
    bad_token_res = client.get('/api/proposals/by-token/wrong_token_guess_123')
    assert bad_token_res.status_code == 404

    # 4. Professor updates proposal using valid edit_token
    update_payload = dict(sample_proposal_data)
    update_payload['course_title'] = 'Introduction to Deep Learning and Neural Systems (Updated)'
    update_payload['credits'] = 5
    update_payload['practical_hours'] = 4

    put_res = client.put(f'/api/proposals/{prop_id}?edit_token={edit_token}', json=update_payload)
    assert put_res.status_code == 200
    updated_prop = put_res.get_json()['proposal']
    assert updated_prop['course_title'] == 'Introduction to Deep Learning and Neural Systems (Updated)'
    assert updated_prop['credits'] == 5

    # 5. Unauthorized edit attempt without token or with wrong token rejected
    unauth_put = client.put(f'/api/proposals/{prop_id}?edit_token=fake_token_xyz', json=update_payload)
    assert unauth_put.status_code == 403

    # 6. Admin can edit proposal using Admin JWT token
    admin_update_payload = dict(update_payload)
    admin_update_payload['course_title'] = 'Introduction to Deep Learning and Neural Systems (Admin Approved Version)'
    admin_put = client.put(
        f'/api/proposals/{prop_id}',
        headers={'Authorization': f'Bearer {admin_token}'},
        json=admin_update_payload
    )
    assert admin_put.status_code == 200
    assert admin_put.get_json()['proposal']['course_title'] == 'Introduction to Deep Learning and Neural Systems (Admin Approved Version)'

    # 7. Edit history contains records for both Professor and Admin edits
    hist_res = client.get(f'/api/proposals/{prop_id}/edit-history')
    assert hist_res.status_code == 200
    hist = hist_res.get_json()['history']
    assert len(hist) >= 2
    roles = [h['edited_by_role'] for h in hist]
    assert 'Professor' in roles
    assert 'Academic Office' in roles

# ==============================================================================
# Feature 3: Manual Compose & Send Email with PDF Attachment
# ==============================================================================
def test_feature3_compose_and_send_proposal_email(client, admin_token, sample_proposal_data):
    res = client.post('/api/proposals', json=sample_proposal_data)
    prop_id = res.get_json()['proposal']['proposal_id']
    edit_token = res.get_json()['edit_token']

    # 1. Professor sends proposal email using edit_token
    email_payload = {
        'to': 'colleague@iitgn.ac.in',
        'cc': 'hod.cse@iitgn.ac.in',
        'subject': 'Please review my SAPC proposal',
        'message': 'Here is the syllabus for our new elective course for review.',
        'attach_pdf': True
    }

    send_res = client.post(
        f'/api/proposals/{prop_id}/send-email?edit_token={edit_token}',
        json=email_payload
    )
    assert send_res.status_code == 200
    assert send_res.get_json()['success'] is True

    # 2. Admin sends proposal email using Admin JWT
    admin_email_payload = {
        'to': 'reviewer@iitgn.ac.in',
        'subject': 'SAPC Course Proposal Review Request',
        'message': 'Kindly review the attached course proposal.',
        'attach_pdf': True
    }
    admin_send_res = client.post(
        f'/api/proposals/{prop_id}/send-email',
        headers={'Authorization': f'Bearer {admin_token}'},
        json=admin_email_payload
    )
    assert admin_send_res.status_code == 200
    assert admin_send_res.get_json()['success'] is True

    # 3. Check outbox logs
    outbox_res = client.get('/api/auth/outbox', headers={'Authorization': f'Bearer {admin_token}'})
    assert outbox_res.status_code == 200
    emails = outbox_res.get_json()['emails']
    manual_emails = [e for e in emails if e.get('email_type') == 'Manual Proposal Email']
    assert len(manual_emails) >= 2

# ==============================================================================
# Feature 4: Reason for Adding the Course as a Minor Field
# ==============================================================================
def test_feature4_minor_reason_persistence_and_pdf(client, sample_proposal_data):
    minor_text = "Crucial foundational course for the Minor in Artificial Intelligence."
    sample_proposal_data['minor_reason'] = minor_text
    
    res = client.post('/api/proposals', json=sample_proposal_data)
    assert res.status_code == 201
    prop = res.get_json()['proposal']
    assert prop['minor_reason'] == minor_text

    # Detail view returns minor_reason
    prop_id = prop['proposal_id']
    detail_res = client.get(f'/api/proposals/{prop_id}')
    assert detail_res.status_code == 200
    assert detail_res.get_json()['proposal']['minor_reason'] == minor_text

# ==============================================================================
# Feature 5: Dynamic Database-Backed Form Configuration
# ==============================================================================
def test_feature5_dynamic_form_config(client, admin_token):
    # 1. Public config returns active categories and custom fields
    pub_res = client.get('/api/form-config')
    assert pub_res.status_code == 200
    cat_data = pub_res.get_json()['categories']
    assert 'course_type' in cat_data
    assert 'course_level' in cat_data

    # 2. Admin adds a new course type option
    add_res = client.post(
        '/api/form-config/options',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'category': 'course_type', 'value': 'ROB', 'label': 'Robotics & Automation (ROB)'}
    )
    assert add_res.status_code in (200, 201)
    new_opt_id = add_res.get_json()['option']['id']

    # 3. New option appears in active form configuration
    pub_res2 = client.get('/api/form-config')
    rob_match = [o for o in pub_res2.get_json()['categories']['course_type'] if o['value'] == 'ROB']
    assert len(rob_match) == 1

    # 4. Admin deactivates the option
    del_res = client.delete(
        f'/api/form-config/options/{new_opt_id}',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert del_res.status_code == 200

    # 5. Deactivated option no longer appears in public form config
    pub_res3 = client.get('/api/form-config')
    rob_match2 = [o for o in pub_res3.get_json()['categories']['course_type'] if o['value'] == 'ROB']
    assert len(rob_match2) == 0

    # 6. Admin custom fields CRUD
    cf_res = client.post(
        '/api/form-config/custom-fields',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'field_name': 'target_students', 'field_label': 'Target Student Cohort', 'field_type': 'text'}
    )
    assert cf_res.status_code == 201
    cf_id = cf_res.get_json()['custom_field']['id']

    pub_cf = client.get('/api/form-config').get_json()['custom_fields']
    assert any(cf['field_name'] == 'target_students' for cf in pub_cf)

    # Deactivate custom field
    client.delete(f'/api/form-config/custom-fields/{cf_id}', headers={'Authorization': f'Bearer {admin_token}'})
    pub_cf2 = client.get('/api/form-config').get_json()['custom_fields']
    assert not any(cf['field_name'] == 'target_students' for cf in pub_cf2)

# ==============================================================================
# Feature 6: Security Department Notification & Resilience
# ==============================================================================
def test_feature6_security_department_notification(client, admin_token, sample_proposal_data):
    res = client.post('/api/proposals', json=sample_proposal_data)
    assert res.status_code == 201
    data = res.get_json()
    assert 'security_notification' in data
    assert data['security_notification']['status'] in ('Sent', 'Pending')

    prop_id = data['proposal']['proposal_id']

    # Admin resend security email
    resend_res = client.post(
        f'/api/proposals/{prop_id}/resend-email?type=security',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert resend_res.status_code == 200
    assert 'security_notification' in resend_res.get_json()['results']

# ==============================================================================
# Feature 7: Course Modification History Linking
# ==============================================================================
def test_feature7_linked_course_history(client, sample_proposal_data):
    # 1. Submit original course
    orig_data = dict(sample_proposal_data)
    orig_data['course_title'] = 'Computer Networks and Protocols'
    res1 = client.post('/api/proposals', json=orig_data)
    assert res1.status_code == 201
    p1_id = res1.get_json()['proposal']['proposal_id']

    # 2. Submit modification of existing course CS301
    mod_data = dict(sample_proposal_data)
    mod_data['course_title'] = 'Advanced Computer Networks'
    mod_data['is_modification'] = True
    mod_data['existing_course_code'] = 'CS301'
    res2 = client.post('/api/proposals', json=mod_data)
    assert res2.status_code == 201
    p2_id = res2.get_json()['proposal']['proposal_id']

    # 3. Submit second modification of same course CS301
    mod_data2 = dict(sample_proposal_data)
    mod_data2['course_title'] = 'Advanced Computer Networks (Quad Format)'
    mod_data2['is_modification'] = True
    mod_data2['existing_course_code'] = 'CS301'
    res3 = client.post('/api/proposals', json=mod_data2)
    assert res3.status_code == 201
    p3_id = res3.get_json()['proposal']['proposal_id']

    # Query course history for p3_id
    history_res = client.get(f'/api/proposals/{p3_id}/course-history')
    assert history_res.status_code == 200
    h_data = history_res.get_json()
    assert h_data['total_versions'] >= 2
    ids = [v['proposal_id'] for v in h_data['history']]
    assert p2_id in ids
    assert p3_id in ids
    assert p2_id != p3_id  # Old proposals are preserved and never overwritten!

# ==============================================================================
# Feature 8: Excel Import with Validation, Matching, and Export Enhancement
# ==============================================================================
def test_feature8_excel_import_and_export(client, admin_token, sample_proposal_data):
    # 1. Create a proposal to match
    res = client.post('/api/proposals', json=sample_proposal_data)
    assert res.status_code == 201
    prop_id = res.get_json()['proposal']['proposal_id']

    # 2. Create an Excel workbook in memory with valid and invalid rows
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Proposal ID", "SAPC Number", "Approval Date", "Status", "Reviewer Remarks"])
    # Valid row matching prop_id
    ws.append([prop_id, "SAPC-68-15", "2026-11-04", "Approved", "Approved in 68th Senate meeting."])
    # Invalid row with non-existent proposal ID
    ws.append(["SAPC-9999-9999", "SAPC-68-99", "2026-11-04", "Approved", "Should fail matching."])

    excel_io = io.BytesIO()
    wb.save(excel_io)
    excel_io.seek(0)

    # 3. Preview import endpoint
    preview_res = client.post(
        '/api/proposals/import/preview',
        headers={'Authorization': f'Bearer {admin_token}'},
        data={'file': (excel_io, 'test_import.xlsx')},
        content_type='multipart/form-data'
    )
    assert preview_res.status_code == 200
    prev_data = preview_res.get_json()
    assert prev_data['valid_count'] == 1
    assert prev_data['invalid_count'] == 1
    assert prev_data['valid_rows'][0]['proposal_id'] == prop_id

    # 4. Confirm import endpoint
    confirm_res = client.post(
        '/api/proposals/import/confirm',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'rows': prev_data['valid_rows']}
    )
    assert confirm_res.status_code == 200
    assert confirm_res.get_json()['updated_count'] == 1

    # 5. Verify database proposal updated with SAPC Number and Approval Date
    detail_res = client.get(f'/api/proposals/{prop_id}')
    assert detail_res.status_code == 200
    p = detail_res.get_json()['proposal']
    assert p['sapc_number'] == "SAPC-68-15"
    assert "2026-11-04" in p['approval_date']
    assert p['status'] == "Approved"

    # 6. Verify Excel and CSV export contains new columns
    exp_res = client.get(
        '/api/proposals/export?format=csv',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert exp_res.status_code == 200
    csv_text = exp_res.data.decode('utf-8')
    assert "SAPC Number" in csv_text
    assert "Approval Date" in csv_text
    assert "Reason for Minor" in csv_text
    assert "SAPC-68-15" in csv_text
