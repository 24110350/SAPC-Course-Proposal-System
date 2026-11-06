import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from app.config import TestConfig
from app.models import Base, engine, SessionLocal, remove_session
from app.models.proposal import Proposal
from app.models.deadline import DeadlineSetting
from app.models.user import AdminUser
from app.utils.auth_helper import generate_auth_token

@pytest.fixture(scope='session')
def app():
    app = create_app(TestConfig)
    return app

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        session = SessionLocal()
        yield session
        session.rollback()
        session.close()
        remove_session()

@pytest.fixture(scope='function')
def admin_token(app):
    with app.app_context():
        return generate_auth_token(username='admin', role='Academic Office')

@pytest.fixture(scope='function')
def admin_headers(admin_token):
    return {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }

@pytest.fixture(scope='function')
def valid_proposal_payload():
    return {
        "course_title": "Advanced Algorithmic Game Theory",
        "potential_instructors": "Dr. Aarav Patel",
        "proposer_name": "Dr. Aarav Patel",
        "faculty_email": "aarav.patel@test.iitgn.ac.in",
        "course_type": "CS",
        "course_level": "4",
        "course_l_t_p_c": "3-1-0-4",
        "lecture_hours": 3.0,
        "tutorial_hours": 1.0,
        "practical_hours": 0.0,
        "credits": 4.0,
        "course_duration": "4 Quads (Full Semester)",
        "expected_frequency": "Each Year",
        "elective_basket_btech": "Science",
        "discipline_elective_btech": "CS",
        "discipline_basket_btech": "Theoretical Computer Science",
        "minors": "CS, MA",
        "minor_basket_thematic_area": "Computational Theory",
        "discipline_elective_msc": "MA",
        "courses_discipline_mtech": "CS",
        "mtech_sub_specialization": "Theory of Computation",
        "is_modification": False,
        "existing_course_code": None,
        "prior_knowledge": "Design and Analysis of Algorithms; Linear Algebra; Probability and Statistics",
        "course_contents": "Strategic form games; Nash equilibrium existence proofs; Mechanism design and VCG mechanisms; Algorithmic mechanism design in auctions; Routing games and the Price of Anarchy; Cooperative game theory and Core concepts; Repeated games and Folk theorems.",
        "texts_and_references": "1. Nisan, N., Roughgarden, T., Tardos, E., & Vazirani, V. V. (Eds.). (2007). Algorithmic Game Theory. Cambridge University Press.; 2. Roughgarden, T. (2016). Twenty Lectures on Algorithmic Game Theory. Cambridge University Press.",
        "learning_outcomes": "1. Analyze strategic interactions mathematically; 2. Formulate computationally efficient auction mechanisms; 3. Bound the price of anarchy in network congestion environments.",
        "overlap_courses": "None with approved courses.",
        "other_relevant_info": "Highly beneficial for students interested in theoretical CS, economics, and multi-agent AI systems."
    }
