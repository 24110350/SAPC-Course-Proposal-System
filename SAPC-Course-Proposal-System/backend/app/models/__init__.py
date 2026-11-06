import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
from .proposal import Base, Proposal, ProposalRecipient, ProposalEditHistory
from .deadline import DeadlineSetting
from .user import AdminUser, ProposalStatusHistory
from .form_config import FormFieldOption, CustomFormField

engine = None
_SessionFactory = None

def init_db(app):
    global engine, _SessionFactory
    database_url = app.config['DATABASE_URL']
    
    # Engine configuration
    connect_args = {}
    if database_url.startswith('sqlite'):
        connect_args = {'check_same_thread': False}
        
    engine = create_engine(database_url, connect_args=connect_args)
    _SessionFactory = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Ensure backward-compatible schema migration for existing databases
    try:
        inspector = inspect(engine)
        if 'proposals' in inspector.get_table_names():
            existing_cols = {c['name'] for c in inspector.get_columns('proposals')}
            with engine.begin() as conn:
                if 'reviewer_comments' not in existing_cols:
                    conn.execute(text("ALTER TABLE proposals ADD COLUMN reviewer_comments TEXT"))
                if 'last_decision_notified' not in existing_cols:
                    conn.execute(text("ALTER TABLE proposals ADD COLUMN last_decision_notified VARCHAR(50)"))
                if 'edit_token' not in existing_cols:
                    conn.execute(text("ALTER TABLE proposals ADD COLUMN edit_token VARCHAR(100)"))
                if 'minor_reason' not in existing_cols:
                    conn.execute(text("ALTER TABLE proposals ADD COLUMN minor_reason TEXT"))
                if 'sapc_number' not in existing_cols:
                    conn.execute(text("ALTER TABLE proposals ADD COLUMN sapc_number VARCHAR(100)"))
                if 'approval_date' not in existing_cols:
                    conn.execute(text("ALTER TABLE proposals ADD COLUMN approval_date TIMESTAMP"))
                if 'custom_fields_data' not in existing_cols:
                    conn.execute(text("ALTER TABLE proposals ADD COLUMN custom_fields_data TEXT"))
                if 'security_email_status' not in existing_cols:
                    conn.execute(text("ALTER TABLE proposals ADD COLUMN security_email_status VARCHAR(50) DEFAULT 'Pending'"))
                if 'security_email_error' not in existing_cols:
                    conn.execute(text("ALTER TABLE proposals ADD COLUMN security_email_error TEXT"))
    except Exception as e:
        app.logger.warning(f"Schema auto-migration check note: {e}")

    # Seed default admin, deadline, and form field options if not present
    session = _SessionFactory()
    try:
        # Check Admin
        admin_user = session.query(AdminUser).filter_by(username=app.config['ADMIN_USERNAME']).first()
        if not admin_user:
            admin_user = AdminUser(
                username=app.config['ADMIN_USERNAME'],
                role='Academic Office'
            )
            admin_user.set_password(app.config['ADMIN_PASSWORD'])
            session.add(admin_user)

        # Check Deadline
        deadline = session.query(DeadlineSetting).first()
        if not deadline:
            now = datetime.now(timezone.utc)
            deadline = DeadlineSetting(
                submission_start=now - timedelta(days=2),
                submission_deadline=now + timedelta(days=14),
                is_active=True,
                announcement_message='SAPC Course Proposal Submissions for the upcoming Academic Semester are now OPEN. All submissions must be received before the deadline.',
                updated_by='Academic Office Admin'
            )
            session.add(deadline)

        # Check and Seed FormFieldOption defaults
        opt_count = session.query(FormFieldOption).count()
        if opt_count == 0:
            DEFAULT_OPTIONS = {
                'course_type': [
                    ('BE', 'Biological Engineering (BE)'), ('CE', 'Civil Engineering (CE)'),
                    ('CG', 'Cognitive Science (CG)'), ('CH', 'Chemistry (CH)'),
                    ('CL', 'Chemical Engineering (CL)'), ('CS', 'Computer Science & Engineering (CS)'),
                    ('DES', 'Design (DES)'), ('EE', 'Electrical Engineering (EE)'),
                    ('EH', 'Earth Sciences / Earth System Science (EH)'), ('ES', 'Engineering Sciences (ES)'),
                    ('FP', 'Foundation Programme (FP)'), ('GE', 'General Engineering (GE)'),
                    ('HS', 'Humanities & Social Sciences (HS)'), ('IN', 'Instrumentation (IN)'),
                    ('MA', 'Mathematics (MA)'), ('ME', 'Mechanical Engineering (ME)'),
                    ('MS', 'Management (MS)'), ('MSE', 'Materials Engineering (MSE)'),
                    ('MTE', 'Maritime Engineering (MTE)'), ('PE', 'Physical Education (PE)'),
                    ('PH', 'Physics (PH)'), ('e-Masters', 'e-Masters Degree'), ('Others', 'Others (Specify)')
                ],
                'course_level': [
                    ('1', 'Level 1 (UG 1st Year)'), ('2', 'Level 2 (UG 2nd Year)'),
                    ('3', 'Level 3 (UG 3rd Year)'), ('4', 'Level 4 (UG 4th Year)'),
                    ('5', 'Level 5 (UG Advanced / Dual Degree)'), ('6', 'Level 6 (Postgraduate / PhD)')
                ],
                'course_duration': [
                    ('1 Quad', '1 Quad'),
                    ('2 Quads (Half Semester)', '2 Quads (Half Semester)'),
                    ('3 Quads', '3 Quads'),
                    ('4 Quads (Full Semester)', '4 Quads (Full Semester)')
                ],
                'expected_frequency': [
                    ('Each Semester', 'Each Semester'),
                    ('Each Year', 'Each Year'),
                    ('Once in Two Years', 'Once in Two Years'),
                    ('Others', 'Others (Specify)')
                ],
                'elective_basket_btech': [
                    ('None', 'None / N/A'), ('BS', 'Basic Science (BS)'),
                    ('HS', 'Humanities & Social Sciences (HS)'), ('Mathematics', 'Mathematics'),
                    ('Science', 'Science')
                ],
                'discipline_elective_btech': [
                    ('None', 'None / N/A'), ('AI', 'Artificial Intelligence (AI)'),
                    ('CL', 'Chemical Engineering (CL)'), ('CE', 'Civil Engineering (CE)'),
                    ('CS', 'Computer Science & Engineering (CS)'), ('EE', 'Electrical Engineering (EE)'),
                    ('ICDT', 'Integrated Circuit Design & Tech (ICDT)'), ('MSE', 'Materials Engineering (MSE)'),
                    ('ME', 'Mechanical Engineering (ME)')
                ],
                'minors': [
                    ('AI', 'Artificial Intelligence (AI)'), ('AM', 'Automobile Engineering (AM)'),
                    ('AR', 'Archaeological Sciences (AR)'), ('BE', 'Biological Sciences (BE)'),
                    ('BM', 'Biomedical Engineering (BM)'), ('CE', 'Civil Engineering (CE)'),
                    ('CG', 'Cognitive Sciences (CG)'), ('CH', 'Chemistry (CH)'),
                    ('CL', 'Chemical Engineering (CL)'), ('CM', 'Computational Mechanics (CM)'),
                    ('CS', 'Computer Science & Engineering (CS)'), ('DA', 'Data Analytics (DA)'),
                    ('DES', 'Design (DES)'), ('EE', 'Electrical Engineering (EE)'),
                    ('EH', 'Earth Sciences / ESS (EH)'), ('HS', 'Humanities & Social Sciences (HS)'),
                    ('ICDT', 'Integrated Circuit Design & Tech (ICDT)'), ('MA', 'Mathematics (MA)'),
                    ('ME', 'Mechanical Engineering (ME)'), ('MS', 'Management (MS)'),
                    ('MSE', 'Materials Engineering (MSE)'), ('PH', 'Physics (PH)'),
                    ('QT', 'Quantum Technologies (QT)'), ('RB', 'Robotics (RB)'),
                    ('SD', 'Sustainable Development (SD)'), ('SY', 'Safety Engineering (SY)')
                ],
                'discipline_elective_msc': [
                    ('None', 'None / N/A'), ('CG', 'Cognitive Sciences (CG)'),
                    ('CH', 'Chemistry (CH)'), ('MA', 'Mathematics (MA)'), ('PH', 'Physics (PH)')
                ],
                'courses_discipline_mtech': [
                    ('None', 'None / N/A'), ('AI', 'Artificial Intelligence (AI)'),
                    ('BE', 'Biological Engineering (BE)'), ('CE', 'Civil Engineering (CE)'),
                    ('CL', 'Chemical Engineering (CL)'), ('CS', 'Computer Science & Engineering (CS)'),
                    ('EE', 'Electrical Engineering (EE)'), ('EH', 'Earth System Science (EH)'),
                    ('ICDT', 'Integrated Circuit Design & Tech (ICDT)'), ('ME', 'Mechanical Engineering (ME)'),
                    ('MSE', 'Materials Engineering (MSE)'), ('MTE', 'Maritime Engineering (MTE)')
                ],
                'discipline_elective_mdes': [
                    ('None', 'None / N/A'), ('IDT', 'Industrial Design & Tech (IDT)')
                ]
            }

            for cat, items in DEFAULT_OPTIONS.items():
                for idx, (val, lbl) in enumerate(items):
                    session.add(FormFieldOption(
                        category=cat,
                        value=val,
                        label=lbl,
                        is_active=True,
                        display_order=idx
                    ))

        session.commit()
    except Exception as e:
        session.rollback()
        app.logger.error(f"Error seeding initial data: {e}")
    finally:
        session.close()

    return engine, _SessionFactory

def SessionLocal():
    """Returns a new scoped SQLAlchemy session"""
    if _SessionFactory is None:
        raise RuntimeError("Database not initialized. Call init_db(app) first.")
    return _SessionFactory()

def remove_session():
    if _SessionFactory is not None:
        _SessionFactory.remove()
