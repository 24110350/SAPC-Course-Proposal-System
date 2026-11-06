"""
End-to-End Full Stack Integration Test Suite
Verifies the complete integration flow specified in Section 20 of project requirements:
React Form Payload -> Flask Backend API -> Database Storage -> Server-side PDF -> Faculty Email Notification -> Academic Dashboard Table
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

import pytest
from app import create_app
from app.config import TestConfig
from app.utils.auth_helper import generate_auth_token

@pytest.fixture(scope='module')
def test_app():
    app = create_app(TestConfig)
    return app

@pytest.fixture(scope='module')
def client(test_app):
    return test_app.test_client()

@pytest.fixture(scope='module')
def admin_headers(test_app):
    with test_app.app_context():
        token = generate_auth_token('admin', 'Academic Office')
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

def test_full_end_to_end_lifecycle(client, admin_headers):
    # 1. Check Deadline Window is Open
    deadline_res = client.get('/api/deadline')
    assert deadline_res.status_code == 200
    assert deadline_res.get_json()['success'] is True
    assert deadline_res.get_json()['deadline']['is_open'] is True

    # 2. Submit a Complete Proposal with All ACAD-SAPC-01 Fields
    payload = {
        "course_title": "End-to-End Quantum Machine Learning",
        "potential_instructors": "Dr. E2E Instructor; Prof. Co-Instructor",
        "proposer_name": "Dr. E2E Instructor",
        "faculty_email": "e2e.instructor@test.iitgn.ac.in",
        "course_type": "CS",
        "course_level": "4",
        "course_level_secondary": "6",
        "course_l_t_p_c": "3-0-2-4",
        "lecture_hours": 3.0,
        "tutorial_hours": 0.0,
        "practical_hours": 2.0,
        "credits": 4.0,
        "course_duration": "4 Quads (Full Semester)",
        "expected_frequency": "Each Year",
        "elective_basket_btech": "Science",
        "discipline_elective_btech": "CS",
        "discipline_basket_btech": "Quantum Computing Basket",
        "minors": "CS, QT",
        "minor_basket_thematic_area": "Quantum Systems",
        "discipline_elective_msc": "PH",
        "courses_discipline_mtech": "CS",
        "mtech_sub_specialization": "Quantum Computation",
        "discipline_elective_mdes": None,
        "is_modification": False,
        "existing_course_code": None,
        "prior_knowledge": "Linear algebra, quantum mechanics basics, machine learning algorithms",
        "course_contents": "Quantum bits and superposition; Quantum logic gates; Variational quantum eigensolvers; Quantum neural networks; Parameterized quantum circuits; Barren plateaus in quantum optimization; Quantum support vector machines; Applications in quantum chemistry.",
        "texts_and_references": "1. Schuld, M., & Petruccione, F. (2021). Machine Learning with Quantum Computers (2nd ed.). Springer.; 2. Nielsen, M. A., & Chuang, I. L. (2010). Quantum Computation and Quantum Information. Cambridge University Press.",
        "learning_outcomes": "1. Design parameterized quantum circuits; 2. Implement variational quantum classifiers; 3. Evaluate quantum advantage in machine learning workloads.",
        "overlap_courses": "None with approved courses.",
        "other_relevant_info": "Will utilize Qiskit and Pennylane simulations on GPU clusters.",
        "additional_recipients": "hod.cse@test.iitgn.ac.in, colleague@test.iitgn.ac.in"
    }

    submit_res = client.post('/api/proposals', json=payload)
    assert submit_res.status_code == 201
    submit_data = submit_res.get_json()
    assert submit_data['success'] is True
    
    proposal = submit_data['proposal']
    prop_id = proposal['proposal_id']
    assert prop_id.startswith('SAPC-')
    assert proposal['course_title'] == payload['course_title']
    assert proposal['status'] == 'Pending'
    assert proposal['pdf_path'] is not None

    # 3. Verify Server-Side Generated PDF is Downloadable
    pdf_res = client.get(f'/api/proposals/{prop_id}/pdf')
    assert pdf_res.status_code == 200
    assert pdf_res.mimetype == 'application/pdf'
    assert len(pdf_res.data) > 1000
    assert pdf_res.data[:4] == b'%PDF'

    # 4. Verify Automatic Email Notification Status & CC Dispatches
    assert proposal['email_notification_status'] in ['Sent', 'Pending']
    assert len(proposal['additional_recipients']) == 2
    assert 'hod.cse@test.iitgn.ac.in' in proposal['additional_recipients']

    # 5. Verify Academic Office Dashboard Table Retrieves Proposal
    dash_res = client.get(f'/api/proposals?q={prop_id}')
    assert dash_res.status_code == 200
    dash_data = dash_res.get_json()
    assert dash_data['total'] >= 1
    found = any(p['proposal_id'] == prop_id for p in dash_data['proposals'])
    assert found is True

    # 6. Verify Academic Office Can Update Status to Approved and Trigger Decision Email
    status_res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Approved', 'remarks': 'Senate Academic Programme Committee approved without objections.'}
    )
    assert status_res.status_code == 200
    status_data = status_res.get_json()
    assert status_data['proposal']['status'] == 'Approved'
    assert status_data['decision_notification']['sent'] is True
    assert status_data['proposal']['reviewer_comments'] == 'Senate Academic Programme Committee approved without objections.'

    # 6b. Verify saving same status again avoids duplicate decision email
    repeat_res = client.patch(
        f'/api/proposals/{prop_id}/status',
        headers=admin_headers,
        json={'status': 'Approved', 'remarks': 'Repeated save with same status'}
    )
    assert repeat_res.status_code == 200
    assert repeat_res.get_json()['decision_notification'] is None

    # 7. Verify Proposal Details and Audit History
    detail_res = client.get(f'/api/proposals/{prop_id}')
    assert detail_res.status_code == 200
    detail = detail_res.get_json()['proposal']
    assert detail['status'] == 'Approved'
    assert len(detail['history']) >= 2

    # 8. Verify Excel and CSV Exports Include the Proposal
    excel_res = client.get('/api/proposals/export?format=xlsx', headers=admin_headers)
    assert excel_res.status_code == 200
    assert len(excel_res.data) > 500

    csv_res = client.get('/api/proposals/export?format=csv', headers=admin_headers)
    assert csv_res.status_code == 200
    assert prop_id in csv_res.data.decode('utf-8')
