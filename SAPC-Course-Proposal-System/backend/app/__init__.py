import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify
from flask_cors import CORS
from .config import Config
from .models import init_db, SessionLocal, remove_session
from .models.proposal import Proposal
from .models.user import ProposalStatusHistory
from .services.pdf_service import PDFGenerator
from .routes.proposals import proposals_bp
from .routes.deadline import deadline_bp
from .routes.export import export_bp
from .routes.auth import auth_bp
from .routes.form_config import form_config_bp
from .routes.excel_import import excel_import_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for all API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Ensure PDF storage directory exists
    pdf_dir = Path(app.config['PDF_STORAGE_DIR'])
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Database and Tables
    init_db(app)

    # Register Blueprints
    app.register_blueprint(proposals_bp)
    app.register_blueprint(deadline_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(form_config_bp)
    app.register_blueprint(excel_import_bp)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        remove_session()

    @app.route('/')
    def index():
        return jsonify({
            'name': 'SAPC Course Proposal System API',
            'institution': 'Indian Institute of Technology Gandhinagar',
            'project': 'Project 13 - CS202',
            'phase': 'Phase 1 - Proposal Submission & Management',
            'version': '1.0.0',
            'status': 'Operational',
            'endpoints': {
                'health': '/api/health',
                'proposals': '/api/proposals',
                'deadline': '/api/deadline',
                'export': '/api/proposals/export',
                'auth': '/api/auth'
            }
        })

    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': 'connected'
        })

    # Auto-seed sample proposals if DB is empty
    with app.app_context():
        _seed_demo_data_if_needed(app)

    return app

def _seed_demo_data_if_needed(app):
    session = SessionLocal()
    try:
        count = session.query(Proposal).count()
        if count == 0:
            app.logger.info("Initializing demo course proposals for instant evaluation...")
            now = datetime.now(timezone.utc)
            
            sample_proposals = [
                {
                    'proposal_id': 'SAPC-2026-0001',
                    'submission_date': now - timedelta(hours=36),
                    'status': 'Approved',
                    'course_title': 'DEMO / SAMPLE DATA: Distributed Systems and Cloud Computing',
                    'potential_instructors': 'Dr. Vikram Sharma; Dr. Ananya Sen',
                    'proposer_name': 'Dr. Vikram Sharma',
                    'faculty_email': 'vikram.sharma@demo.iitgn.ac.in',
                    'course_type': 'CS',
                    'course_level': '4',
                    'course_level_secondary': '6',
                    'course_l_t_p_c': '3-0-2-4',
                    'lecture_hours': 3.0,
                    'tutorial_hours': 0.0,
                    'practical_hours': 2.0,
                    'credits': 4.0,
                    'course_duration': '4 Quads (Full Semester)',
                    'expected_frequency': 'Each Year',
                    'elective_basket_btech': None,
                    'discipline_elective_btech': 'CS',
                    'discipline_basket_btech': 'Systems and Networking Basket',
                    'minors': 'CS, DA',
                    'minor_basket_thematic_area': 'High Performance Computing',
                    'courses_discipline_mtech': 'CS',
                    'mtech_sub_specialization': 'Distributed Systems Specialization',
                    'is_modification': False,
                    'prior_knowledge': 'Data Structures and Algorithms; Basic Computer Networks; Operating Systems fundamentals',
                    'course_contents': 'Introduction to distributed system models; Inter-process communication and remote procedure calls; Logical clocks, vector clocks, and causal ordering; Distributed mutual exclusion algorithms; Consensus protocols including Paxos and Raft; Fault tolerance and replication architectures; Distributed file systems and key-value stores; Cloud resource virtualization and container orchestration.',
                    'texts_and_references': '1. Coulouris, G., Dollimore, J., & Kindberg, T. (2012). Distributed Systems: Concepts and Design (5th ed.). Addison-Wesley.; 2. Tanenbaum, A. S., & Van Steen, M. (2017). Distributed Systems: Principles and Paradigms (3rd ed.). CreateSpace.',
                    'learning_outcomes': 'Students will be able to: 1. Formulate and analyze consistency models in distributed environments; 2. Implement consensus algorithms such as Raft; 3. Architect fault-tolerant distributed services using modern container clusters; 4. Evaluate latency-throughput trade-offs under high network concurrency.',
                    'overlap_courses': 'Minor conceptual overlap (approx 10%) with Operating Systems in process synchronization; no significant overlap with other approved courses.',
                    'other_relevant_info': 'Includes hands-on engineering lab projects using Go and Kubernetes. Highly relevant for cloud infrastructure industry and systems research.',
                    'email_notification_status': 'Sent'
                },
                {
                    'proposal_id': 'SAPC-2026-0002',
                    'submission_date': now - timedelta(hours=20),
                    'status': 'Under Review',
                    'course_title': 'DEMO / SAMPLE DATA: Digital Signal Processing for Communications',
                    'potential_instructors': 'Prof. K. Rameshwar',
                    'proposer_name': 'Prof. K. Rameshwar',
                    'faculty_email': 'k.rameshwar@demo.iitgn.ac.in',
                    'course_type': 'EE',
                    'course_level': '3',
                    'course_level_secondary': None,
                    'course_l_t_p_c': '3-1-0-4',
                    'lecture_hours': 3.0,
                    'tutorial_hours': 1.0,
                    'practical_hours': 0.0,
                    'credits': 4.0,
                    'course_duration': '4 Quads (Full Semester)',
                    'expected_frequency': 'Each Semester',
                    'elective_basket_btech': None,
                    'discipline_elective_btech': 'EE',
                    'discipline_basket_btech': 'Signal Processing and Communications',
                    'minors': 'EE, ICDT',
                    'minor_basket_thematic_area': 'Signal Processing Thematic Area',
                    'courses_discipline_mtech': 'EE',
                    'mtech_sub_specialization': 'Communications Engineering',
                    'is_modification': True,
                    'existing_course_code': 'EE-302',
                    'prior_knowledge': 'Signals and Systems (EE-201); Engineering Mathematics (Linear Algebra and Complex Variables)',
                    'course_contents': 'Review of discrete-time signals and systems; Z-transform and system functions; Discrete Fourier Transform (DFT) and Fast Fourier Transform (FFT) computational structures; Design of Finite Impulse Response (FIR) filters; Design of Infinite Impulse Response (IIR) filters; Multi-rate digital signal processing and filter banks; Modern adaptive filtering algorithms; Applications in 5G wireless channel estimation.',
                    'texts_and_references': '1. Oppenheim, A. V., & Schafer, R. W. (2010). Discrete-Time Signal Processing (3rd ed.). Pearson.; 2. Proakis, J. G., & Manolakis, D. G. (2007). Digital Signal Processing: Principles, Algorithms, and Applications (4th ed.). Prentice Hall.',
                    'learning_outcomes': '1. Apply DFT/FFT algorithms to analyze complex multi-carrier signals; 2. Synthesize FIR and IIR digital filter topologies meeting industrial attenuation specifications; 3. Formulate adaptive filtering strategies for communication interference cancellation.',
                    'overlap_courses': 'Replaces and updates curriculum of existing EE-302 to integrate modern multi-rate signal processing and 5G modulation standards.',
                    'other_relevant_info': 'Modification updates 30% of content to incorporate software-defined radio experiments and adaptive filtering for telecom industries.',
                    'email_notification_status': 'Sent'
                },
                {
                    'proposal_id': 'SAPC-2026-0003',
                    'submission_date': now - timedelta(hours=8),
                    'status': 'Pending',
                    'course_title': 'DEMO / SAMPLE DATA: Technology, Ethics, and Society',
                    'potential_instructors': 'Dr. Maya Kulkarni',
                    'proposer_name': 'Dr. Maya Kulkarni',
                    'faculty_email': 'maya.kulkarni@demo.iitgn.ac.in',
                    'course_type': 'HS',
                    'course_level': '2',
                    'course_level_secondary': None,
                    'course_l_t_p_c': '3-0-0-3',
                    'lecture_hours': 3.0,
                    'tutorial_hours': 0.0,
                    'practical_hours': 0.0,
                    'credits': 3.0,
                    'course_duration': '4 Quads (Full Semester)',
                    'expected_frequency': 'Each Year',
                    'elective_basket_btech': 'HS',
                    'minors': 'HS, SD',
                    'minor_basket_thematic_area': 'Ethics and Technology Policy',
                    'is_modification': False,
                    'prior_knowledge': 'None required; open to all undergraduate disciplines',
                    'course_contents': 'Historical overview of technological revolutions and social transitions; Ethical frameworks: Utilitarianism, Deontology, and Virtue Ethics in technological decision making; AI governance, algorithmic bias, and automated decision systems; Surveillance capitalism, personal privacy, and data dignity; Environmental and climate implications of computational infrastructure; Bioethics and genetic enhancement policies; Public policy formulations for emerging disruptive technologies.',
                    'texts_and_references': '1. Winner, L. (1986). The Whale and the Reactor: A Search for Limits in an Age of High Technology. University of Chicago Press.; 2. Sandel, M. J. (2012). What Money Can’t Buy: The Moral Limits of Markets. Farrar, Straus and Giroux.; 3. Zuboff, S. (2019). The Age of Surveillance Capitalism. PublicAffairs.',
                    'learning_outcomes': '1. Critique technological innovations using classical and contemporary philosophical frameworks; 2. Articulate ethical impact assessments for automated algorithmic deployments; 3. Formulate balanced policy proposals safeguarding citizen privacy and environmental equity.',
                    'overlap_courses': 'Complementary to CS ethics seminars; no formal curricular overlap with approved engineering courses.',
                    'other_relevant_info': 'Fulfills the mandatory HSS Elective Basket for BTech students across all engineering branches.',
                    'email_notification_status': 'Pending'
                },
                {
                    'proposal_id': 'SAPC-2026-0004',
                    'submission_date': now - timedelta(hours=2),
                    'status': 'Modification Required',
                    'course_title': 'DEMO / SAMPLE DATA: Rapid Prototyping and Additive Manufacturing',
                    'potential_instructors': 'Dr. Rajesh Nair; Dr. Priya Verma',
                    'proposer_name': 'Dr. Rajesh Nair',
                    'faculty_email': 'rajesh.nair@demo.iitgn.ac.in',
                    'course_type': 'ME',
                    'course_level': '3',
                    'course_level_secondary': None,
                    'course_l_t_p_c': '2-0-2-3',
                    'lecture_hours': 2.0,
                    'tutorial_hours': 0.0,
                    'practical_hours': 2.0,
                    'credits': 3.0,
                    'course_duration': '2 Quads (Half Semester)',
                    'expected_frequency': 'Each Semester',
                    'discipline_elective_btech': 'ME',
                    'discipline_basket_btech': 'Manufacturing Science Basket',
                    'minors': 'ME, RB',
                    'minor_basket_thematic_area': 'Advanced Manufacturing',
                    'courses_discipline_mtech': 'ME',
                    'mtech_sub_specialization': 'Thermal and Design Specialization',
                    'is_modification': False,
                    'prior_knowledge': 'Manufacturing Processes (ME-201); Mechanics of Materials',
                    'course_contents': 'Classification of additive manufacturing technologies; Stereolithography (SLA) photopolymerization processes; Fused Deposition Modeling (FDM) extrusion kinetics; Selective Laser Sintering (SLS) powder bed fusion; Design for Additive Manufacturing (DfAM) principles; Lattice structures and topology optimization; Post-processing surface treatments and metrology; Industrial applications in aerospace and biomedical implants.',
                    'texts_and_references': '1. Gibson, I., Rosen, D., Stucker, B., & Khorasani, M. (2021). Additive Manufacturing Technologies (3rd ed.). Springer.; 2. Chua, C. K., & Leong, K. F. (2017). 3D Printing and Additive Manufacturing: Principles and Applications (5th ed.). World Scientific.',
                    'learning_outcomes': '1. Select appropriate additive manufacturing technologies based on material constraints; 2. Execute topology optimization for lightweight structural mechanical components; 3. Calibrate slicing parameters and post-processing finishing cycles.',
                    'overlap_courses': 'Partial overlap (approx 15%) with general manufacturing lab; specialized focus on modern 3D sintering.',
                    'other_relevant_info': 'Reviewer note: SAPC requested clarification on lab consumable budget and machine availability before final approval.',
                    'email_notification_status': 'Sent'
                }
            ]

            for s_data in sample_proposals:
                p = Proposal(**s_data)
                session.add(p)
                session.flush()

                # Generate initial PDF on disk
                try:
                    pdf_path, pdf_filename = PDFGenerator.generate_proposal_pdf(
                        p.to_dict(),
                        output_dir=app.config['PDF_STORAGE_DIR']
                    )
                    p.pdf_path = pdf_path
                    p.pdf_filename = pdf_filename
                except Exception as e:
                    app.logger.warning(f"Could not generate PDF for seed proposal {p.proposal_id}: {e}")

                # Initial status history
                history = ProposalStatusHistory(
                    proposal_id=p.proposal_id,
                    previous_status=None,
                    new_status=p.status,
                    remarks=f"Initial seeded demonstration proposal in state '{p.status}'.",
                    changed_by="Academic Office Admin"
                )
                session.add(history)

            session.commit()
            app.logger.info("Demo course proposals and PDFs generated successfully.")
    except Exception as e:
        session.rollback()
        app.logger.error(f"Error seeding demo data: {e}")
    finally:
        session.close()
