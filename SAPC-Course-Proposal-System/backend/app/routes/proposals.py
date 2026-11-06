import os
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app
from sqlalchemy import or_, desc, asc
from ..models import SessionLocal
from ..models.proposal import Proposal, ProposalRecipient, ProposalEditHistory
from ..models.deadline import DeadlineSetting
from ..models.user import ProposalStatusHistory
from ..services.pdf_service import PDFGenerator
from ..services.email_service import EmailService
from ..utils.validators import validate_proposal_payload, generate_next_proposal_id
from ..utils.auth_helper import admin_required, verify_auth_token

proposals_bp = Blueprint('proposals', __name__, url_prefix='/api/proposals')

@proposals_bp.route('', methods=['POST'])
def submit_proposal():
    """
    Submits a new course proposal or modification of existing course.
    1. Enforces server-side deadline
    2. Enforces server-side payload validation
    3. Handles duplicate detection
    4. Persists record in PostgreSQL/DB
    5. Generates official PDF
    6. Triggers automated faculty email notification (with error resilience)
    """
    session = SessionLocal()
    try:
        # Step 1: Deadline Verification
        now = datetime.now(timezone.utc)
        deadline_setting = session.query(DeadlineSetting).order_by(DeadlineSetting.id.desc()).first()
        if deadline_setting:
            is_open, reason = deadline_setting.is_currently_open(now)
            if not is_open:
                return jsonify({
                    'success': False,
                    'error': 'SUBMISSION_CLOSED',
                    'message': reason,
                    'deadline': deadline_setting.to_dict(now)
                }), 403

        # Step 2: Validate Payload
        data = request.get_json() or {}
        is_valid, validation_errors = validate_proposal_payload(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_FAILED',
                'message': 'Proposal form contains errors. Please correct the highlighted fields.',
                'errors': validation_errors
            }), 400

        # Step 3: Duplicate Submission Check
        course_title = data['course_title'].strip()
        proposer_name = data['proposer_name'].strip()
        existing = (
            session.query(Proposal)
            .filter(
                Proposal.course_title.ilike(course_title),
                Proposal.proposer_name.ilike(proposer_name)
            )
            .first()
        )
        if existing:
            return jsonify({
                'success': False,
                'error': 'DUPLICATE_PROPOSAL',
                'message': f"A proposal with course title '{course_title}' by '{proposer_name}' has already been submitted (ID: {existing.proposal_id}). If you need to make changes, please contact the Academic Office."
            }), 409

        # Step 4: Generate unique Proposal ID, unguessable Edit Token, and Create Record
        proposal_id = generate_next_proposal_id(session, Proposal)
        edit_token = secrets.token_urlsafe(32)
        
        # Parse numeric credits
        l = float(data.get('lecture_hours', 0.0) or 0.0)
        t = float(data.get('tutorial_hours', 0.0) or 0.0)
        p = float(data.get('practical_hours', 0.0) or 0.0)
        c = float(data.get('credits', 0.0) or 0.0)

        custom_fields_raw = data.get('custom_fields_data')
        if isinstance(custom_fields_raw, dict):
            custom_fields_str = json.dumps(custom_fields_raw)
        else:
            custom_fields_str = (custom_fields_raw or '').strip() or None

        proposal = Proposal(
            proposal_id=proposal_id,
            edit_token=edit_token,
            submission_date=now,
            status='Pending',
            course_title=course_title,
            potential_instructors=data['potential_instructors'].strip(),
            proposer_name=proposer_name,
            faculty_email=data['faculty_email'].strip().lower(),
            course_type=data['course_type'].strip(),
            course_type_other=(data.get('course_type_other') or '').strip() if data.get('course_type') == 'Others' else None,
            course_level=str(data['course_level']).strip(),
            course_level_secondary=str(data.get('course_level_secondary', '')).strip() or None,
            course_l_t_p_c=data.get('course_l_t_p_c', f"{l}-{t}-{p}-{c}"),
            lecture_hours=l,
            tutorial_hours=t,
            practical_hours=p,
            credits=c,
            course_duration=data['course_duration'].strip(),
            expected_frequency=data['expected_frequency'].strip(),
            expected_frequency_other=(data.get('expected_frequency_other') or '').strip() if data.get('expected_frequency') == 'Others' else None,
            elective_basket_btech=data.get('elective_basket_btech') or None,
            discipline_elective_btech=data.get('discipline_elective_btech') or None,
            discipline_basket_btech=(data.get('discipline_basket_btech') or '').strip() or None,
            minors=data.get('minors') or None,
            minor_basket_thematic_area=(data.get('minor_basket_thematic_area') or '').strip() or None,
            minor_reason=(data.get('minor_reason') or '').strip() or None,
            discipline_elective_msc=data.get('discipline_elective_msc') or None,
            courses_discipline_mtech=data.get('courses_discipline_mtech') or None,
            mtech_sub_specialization=(data.get('mtech_sub_specialization') or '').strip() or None,
            discipline_elective_mdes=data.get('discipline_elective_mdes') or None,
            is_modification=bool(data.get('is_modification', False)),
            existing_course_code=(data.get('existing_course_code') or '').strip() or None,
            prior_knowledge=(data.get('prior_knowledge') or '').strip() or None,
            course_contents=data['course_contents'].strip(),
            texts_and_references=data['texts_and_references'].strip(),
            learning_outcomes=data['learning_outcomes'].strip(),
            overlap_courses=(data.get('overlap_courses') or '').strip() or None,
            other_relevant_info=(data.get('other_relevant_info') or '').strip() or None,
            custom_fields_data=custom_fields_str,
            email_notification_status='Pending',
            security_email_status='Pending'
        )

        session.add(proposal)
        session.flush() # assign primary key

        # Persist Additional Recipients (CC)
        recipient_records = []
        raw_recipients = data.get('additional_recipients') or []
        for recip_email in raw_recipients:
            recip = ProposalRecipient(
                proposal_id=proposal_id,
                email=recip_email,
                delivery_status='Pending'
            )
            session.add(recip)
            recipient_records.append(recip)
        session.flush()

        # Step 5: Server-side PDF Generation
        try:
            pdf_path, pdf_filename = PDFGenerator.generate_proposal_pdf(
                proposal.to_dict(),
                output_dir=current_app.config['PDF_STORAGE_DIR']
            )
            proposal.pdf_path = pdf_path
            proposal.pdf_filename = pdf_filename
        except Exception as pdf_err:
            current_app.logger.error(f"Failed to generate PDF for {proposal_id}: {pdf_err}")
            # Note: Do not abort submission; record warning
            proposal.pdf_path = None
            proposal.pdf_filename = None

        # Step 6: Automated Email Notification (Resilient: failure does not rollback proposal)
        email_sent, email_err = EmailService.send_proposal_submission_notification(proposal)
        if email_sent:
            proposal.email_notification_status = 'Sent'
            proposal.email_error_log = None
        else:
            proposal.email_notification_status = 'Failed'
            proposal.email_error_log = email_err

        # Step 7: Send Proposal Copy to Additional Recipients (CC)
        cc_delivery_results = {}
        any_cc_failed = False
        if recipient_records:
            _, cc_delivery_results = EmailService.send_proposal_copy_to_recipients(
                proposal,
                recipient_emails=[r.email for r in recipient_records],
                attach_pdf=True
            )
            for recip in recipient_records:
                res_info = cc_delivery_results.get(recip.email, {})
                if res_info.get('sent'):
                    recip.delivery_status = 'Sent'
                    recip.error_message = None
                    recip.sent_at = datetime.now(timezone.utc)
                else:
                    recip.delivery_status = 'Failed'
                    recip.error_message = res_info.get('error')
                    any_cc_failed = True

        # Step 8: Send PDF to Security Department (Requirement 6, resilient)
        sec_sent, sec_err = EmailService.send_security_dept_notification(proposal, attach_pdf=True)
        if sec_sent:
            proposal.security_email_status = 'Sent'
            proposal.security_email_error = None
        else:
            proposal.security_email_status = 'Failed'
            proposal.security_email_error = sec_err

        # Initial Status History Record
        history = ProposalStatusHistory(
            proposal_id=proposal_id,
            previous_status=None,
            new_status='Pending',
            remarks='Course proposal submitted by proposer.',
            changed_by=proposer_name
        )
        session.add(history)

        session.commit()

        edit_link = f"{current_app.config['FRONTEND_BASE_URL']}/?edit_token={edit_token}&proposal_id={proposal_id}"

        overall_email_ok = email_sent and (not any_cc_failed)
        if overall_email_ok:
            submission_msg = 'Course proposal successfully submitted to SAPC Academic Office.'
        else:
            submission_msg = 'Your proposal was submitted successfully, but email delivery could not be completed for all recipients. The system has recorded the failure for follow-up.'

        return jsonify({
            'success': True,
            'message': submission_msg,
            'proposal': proposal.to_dict(),
            'edit_token': edit_token,
            'edit_link': edit_link,
            'email_notification': {
                'status': proposal.email_notification_status,
                'recipient': proposal.faculty_email,
                'error': proposal.email_error_log
            },
            'security_notification': {
                'status': proposal.security_email_status,
                'recipient': current_app.config['SECURITY_DEPT_EMAIL'],
                'error': proposal.security_email_error
            },
            'additional_recipients_delivery': cc_delivery_results
        }), 201

    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Unexpected submission error: {e}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_SERVER_ERROR',
            'message': f"An unexpected error occurred while processing proposal: {str(e)}"
        }), 500
    finally:
        session.close()

@proposals_bp.route('', methods=['GET'])
def list_proposals():
    """
    Structured database-backed proposal listing for Academic Office dashboard.
    Supports search, filter, sort, and pagination directly against database.
    """
    session = SessionLocal()
    try:
        query = session.query(Proposal)

        # Search Query across multiple fields
        q = request.args.get('q', '').strip()
        if q:
            search_pattern = f"%{q}%"
            query = query.filter(
                or_(
                    Proposal.proposal_id.ilike(search_pattern),
                    Proposal.course_title.ilike(search_pattern),
                    Proposal.proposer_name.ilike(search_pattern),
                    Proposal.faculty_email.ilike(search_pattern),
                    Proposal.existing_course_code.ilike(search_pattern)
                )
            )

        # Filters
        status = request.args.get('status')
        if status and status != 'ALL':
            query = query.filter(Proposal.status == status)

        course_type = request.args.get('course_type')
        if course_type and course_type != 'ALL':
            query = query.filter(Proposal.course_type == course_type)

        course_level = request.args.get('course_level')
        if course_level and course_level != 'ALL':
            query = query.filter(Proposal.course_level == course_level)

        nature = request.args.get('nature')
        if nature == 'NEW':
            query = query.filter(Proposal.is_modification == False)
        elif nature == 'MODIFICATION':
            query = query.filter(Proposal.is_modification == True)

        # Sorting
        sort_by = request.args.get('sort_by', 'submission_date')
        order = request.args.get('order', 'desc').lower()

        sort_col = getattr(Proposal, sort_by, Proposal.submission_date)
        if order == 'asc':
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        # Total count before pagination
        total = query.count()

        # Pagination
        page = max(1, int(request.args.get('page', 1)))
        per_page = max(1, min(100, int(request.args.get('per_page', 20))))
        proposals = query.offset((page - 1) * per_page).limit(per_page).all()

        # Summary statistics for dashboard cards/metrics
        stats = {
            'total': session.query(Proposal).count(),
            'pending': session.query(Proposal).filter(Proposal.status == 'Pending').count(),
            'under_review': session.query(Proposal).filter(Proposal.status == 'Under Review').count(),
            'approved': session.query(Proposal).filter(Proposal.status == 'Approved').count(),
            'modification_required': session.query(Proposal).filter(Proposal.status == 'Modification Required').count(),
            'rejected': session.query(Proposal).filter(Proposal.status == 'Rejected').count(),
        }

        return jsonify({
            'success': True,
            'proposals': [p.to_dict() for p in proposals],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'stats': stats
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@proposals_bp.route('/<proposal_id>', methods=['GET'])
def get_proposal_detail(proposal_id):
    """
    Returns full details for a single proposal including audit history.
    """
    session = SessionLocal()
    try:
        proposal = session.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        if not proposal:
            return jsonify({'success': False, 'error': f"Proposal '{proposal_id}' not found."}), 404

        history = (
            session.query(ProposalStatusHistory)
            .filter(ProposalStatusHistory.proposal_id == proposal_id)
            .order_by(desc(ProposalStatusHistory.changed_at))
            .all()
        )

        edit_history = (
            session.query(ProposalEditHistory)
            .filter(ProposalEditHistory.proposal_id == proposal_id)
            .order_by(desc(ProposalEditHistory.edited_at))
            .all()
        )

        p_data = proposal.to_dict()
        p_data['history'] = [h.to_dict() for h in history]
        p_data['edit_history'] = [eh.to_dict() for eh in edit_history]

        return jsonify({
            'success': True,
            'proposal': p_data
        }), 200
    finally:
        session.close()

@proposals_bp.route('/<proposal_id>/status', methods=['PATCH'])
@admin_required
def update_proposal_status(proposal_id):
    """
    Admin-only endpoint: Update proposal review status (Pending, Under Review, Approved, Rejected, Modification Required).
    Records change in proposal_status_history.
    """
    data = request.get_json() or {}
    new_status = data.get('status')
    remarks = data.get('remarks', '')

    valid_statuses = ['Pending', 'Under Review', 'Approved', 'Rejected', 'Modification Required']
    if new_status not in valid_statuses:
        return jsonify({
            'success': False,
            'error': f"Invalid status '{new_status}'. Allowed: {', '.join(valid_statuses)}"
        }), 400

    session = SessionLocal()
    try:
        proposal = session.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        if not proposal:
            return jsonify({'success': False, 'error': f"Proposal '{proposal_id}' not found."}), 404

        prev_status = proposal.status
        is_status_changed = (new_status != prev_status)
        is_decision = new_status in ['Approved', 'Rejected', 'Modification Required']

        proposal.status = new_status
        proposal.reviewer_comments = remarks
        proposal.updated_at = datetime.now(timezone.utc)

        # Audit history entry
        changed_by = request.user.get('sub', 'Academic Office Admin')
        history = ProposalStatusHistory(
            proposal_id=proposal_id,
            previous_status=prev_status,
            new_status=new_status,
            remarks=remarks,
            changed_by=changed_by
        )
        session.add(history)

        # Re-generate PDF with updated status
        try:
            pdf_path, pdf_filename = PDFGenerator.generate_proposal_pdf(
                proposal.to_dict(),
                output_dir=current_app.config['PDF_STORAGE_DIR']
            )
            proposal.pdf_path = pdf_path
            proposal.pdf_filename = pdf_filename
        except Exception as e:
            current_app.logger.warning(f"Failed to refresh PDF for {proposal_id}: {e}")

        # Trigger decision email only when an authorized reviewer genuinely changes
        # to a decision status (Approved, Rejected, Modification Required).
        # Avoid duplicate decision emails when the same status is saved repeatedly.
        decision_notification_result = None
        if is_decision and is_status_changed:
            dec_sent, dec_err = EmailService.send_decision_notification(
                proposal=proposal,
                decision=new_status,
                reviewer_comments=remarks,
                attach_pdf=True
            )
            if dec_sent:
                proposal.last_decision_notified = new_status
                decision_notification_result = {'sent': True, 'error': None}
            else:
                decision_notification_result = {'sent': False, 'error': dec_err}
                current_app.logger.error(f"Decision email delivery failed for {proposal_id}: {dec_err}")

        session.commit()

        if decision_notification_result is not None:
            if decision_notification_result['sent']:
                resp_message = f"Status of proposal {proposal_id} updated to '{new_status}'. Decision notification email dispatched to submitter ({proposal.faculty_email})."
            else:
                resp_message = f"Status of proposal {proposal_id} updated to '{new_status}', but the decision notification email could not be delivered to the submitter ({proposal.faculty_email}). The failure has been recorded."
        else:
            resp_message = f"Status of proposal {proposal_id} updated to '{new_status}'."

        return jsonify({
            'success': True,
            'message': resp_message,
            'proposal': proposal.to_dict(),
            'decision_notification': decision_notification_result
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@proposals_bp.route('/<proposal_id>/resend-email', methods=['POST'])
@admin_required
def resend_email_notification(proposal_id):
    """
    Admin-only endpoint: Manually retry sending automated notification email(s).
    Supports query parameter `?type=submission|decision|cc|all`.
    """
    session = SessionLocal()
    try:
        proposal = session.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        if not proposal:
            return jsonify({'success': False, 'error': f"Proposal '{proposal_id}' not found."}), 404

        req_type = request.args.get('type', 'all').lower()
        results = {}

        # 1. Submission email
        if req_type in ('submission', 'all'):
            email_sent, email_err = EmailService.send_proposal_submission_notification(proposal)
            proposal.email_notification_status = 'Sent' if email_sent else 'Failed'
            proposal.email_error_log = None if email_sent else email_err
            results['submission_notification'] = {'sent': email_sent, 'error': email_err}

        # 2. Decision notification (if in decision state)
        if proposal.status in ['Approved', 'Rejected', 'Modification Required']:
            if req_type in ('decision', 'all'):
                dec_sent, dec_err = EmailService.send_decision_notification(
                    proposal=proposal,
                    decision=proposal.status,
                    reviewer_comments=proposal.reviewer_comments,
                    attach_pdf=True
                )
                if dec_sent:
                    proposal.last_decision_notified = proposal.status
                results['decision_notification'] = {'sent': dec_sent, 'error': dec_err}

        # 3. Additional Recipients (CC)
        if req_type in ('cc', 'all'):
            recips = session.query(ProposalRecipient).filter(ProposalRecipient.proposal_id == proposal_id).all()
            if recips:
                cc_sent, cc_results = EmailService.send_proposal_copy_to_recipients(
                    proposal,
                    recipient_emails=[r.email for r in recips],
                    attach_pdf=True
                )
                for r in recips:
                    r_res = cc_results.get(r.email, {})
                    if r_res.get('sent'):
                        r.delivery_status = 'Sent'
                        r.error_message = None
                        r.sent_at = datetime.now(timezone.utc)
                    else:
                        r.delivery_status = 'Failed'
                        r.error_message = r_res.get('error')
                results['additional_recipients'] = cc_results

        # 4. Security Department notification (Requirement 6)
        if req_type in ('security', 'all'):
            sec_sent, sec_err = EmailService.send_security_dept_notification(proposal, attach_pdf=True)
            proposal.security_email_status = 'Sent' if sec_sent else 'Failed'
            proposal.security_email_error = None if sec_sent else sec_err
            results['security_notification'] = {'sent': sec_sent, 'error': sec_err}

        session.commit()

        overall_ok = all(
            v.get('sent', True) if isinstance(v, dict) and 'sent' in v else True
            for v in results.values()
        )

        return jsonify({
            'success': overall_ok,
            'message': 'Notification email(s) dispatched successfully.' if overall_ok else 'One or more notification retries failed.',
            'email_notification_status': proposal.email_notification_status,
            'email_error_log': proposal.email_error_log,
            'results': results,
            'proposal': proposal.to_dict()
        }), 200 if overall_ok else 500
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@proposals_bp.route('/<proposal_id>/pdf', methods=['GET'])
def download_proposal_pdf(proposal_id):
    """
    Downloads the official generated PDF as attachment.
    If PDF does not exist on disk, it is dynamically generated from PostgreSQL record.
    """
    session = SessionLocal()
    try:
        proposal = session.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        if not proposal:
            return jsonify({'success': False, 'error': f"Proposal '{proposal_id}' not found."}), 404

        pdf_path = proposal.pdf_path
        if not pdf_path or not Path(pdf_path).exists():
            # Generate on demand
            pdf_path, pdf_filename = PDFGenerator.generate_proposal_pdf(
                proposal.to_dict(),
                output_dir=current_app.config['PDF_STORAGE_DIR']
            )
            proposal.pdf_path = pdf_path
            proposal.pdf_filename = pdf_filename
            session.commit()

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"{proposal_id}.pdf",
            mimetype='application/pdf'
        )
    finally:
        session.close()

@proposals_bp.route('/<proposal_id>/pdf/view', methods=['GET'])
def view_proposal_pdf(proposal_id):
    """
    Renders the official generated PDF inline inside browser tab.
    """
    session = SessionLocal()
    try:
        proposal = session.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        if not proposal:
            return jsonify({'success': False, 'error': f"Proposal '{proposal_id}' not found."}), 404

        pdf_path = proposal.pdf_path
        if not pdf_path or not Path(pdf_path).exists():
            pdf_path, pdf_filename = PDFGenerator.generate_proposal_pdf(
                proposal.to_dict(),
                output_dir=current_app.config['PDF_STORAGE_DIR']
            )
            proposal.pdf_path = pdf_path
            proposal.pdf_filename = pdf_filename
            session.commit()

        return send_file(
            pdf_path,
            as_attachment=False,
            download_name=f"{proposal_id}.pdf",
            mimetype='application/pdf'
        )
    finally:
        session.close()


def check_proposal_authorization(proposal, req):
    """
    Checks if request is authorized to edit or email this proposal:
    1. Admin user via Bearer JWT token or ?token=...
    2. Professor via proposal-specific unguessable edit_token (?edit_token=... or header X-Edit-Token or JSON body edit_token)
    Returns: (is_authorized: bool, role: str, actor_name: str, error_tuple: tuple or None)
    """
    # 1. Check Admin JWT
    auth_header = req.headers.get('Authorization', '')
    admin_token = None
    if auth_header.startswith('Bearer '):
        admin_token = auth_header.split(' ', 1)[1].strip()
    elif 'token' in req.args:
        admin_token = req.args.get('token')

    if admin_token:
        valid, payload, _ = verify_auth_token(admin_token)
        if valid and payload:
            return True, 'Academic Office', payload.get('sub', 'Academic Office Admin'), None

    # 2. Check Professor Edit Token
    token_candidate = (
        req.args.get('edit_token') or 
        req.args.get('token') or 
        req.headers.get('X-Edit-Token') or 
        (req.get_json(silent=True) or {}).get('edit_token')
    )

    if token_candidate and proposal.edit_token and token_candidate.strip() == proposal.edit_token.strip():
        return True, 'Professor', proposal.proposer_name, None

    return False, None, None, (jsonify({
        'success': False,
        'error': 'UNAUTHORIZED',
        'message': 'Valid administrator credentials or proposal-specific authorization token required.'
    }), 403)


@proposals_bp.route('/by-token/<edit_token>', methods=['GET'])
def get_proposal_by_token(edit_token):
    """
    Retrieves proposal data for professor editing using unguessable token.
    """
    session = SessionLocal()
    try:
        proposal = session.query(Proposal).filter(Proposal.edit_token == edit_token).first()
        if not proposal:
            return jsonify({'success': False, 'error': 'Invalid or expired proposal authorization token.'}), 404

        now = datetime.now(timezone.utc)
        deadline_setting = session.query(DeadlineSetting).order_by(DeadlineSetting.id.desc()).first()
        is_open = True
        deadline_reason = None
        if deadline_setting:
            is_open, deadline_reason = deadline_setting.is_currently_open(now)

        return jsonify({
            'success': True,
            'proposal': proposal.to_dict(),
            'is_open': is_open,
            'deadline_message': deadline_reason
        }), 200
    finally:
        session.close()


@proposals_bp.route('/<proposal_id>', methods=['PUT'])
def update_proposal(proposal_id):
    """
    Updates an existing proposal.
    - Authorized for Professors (using unguessable edit_token, before deadline)
    - Authorized for Admins (using JWT Bearer token, any time)
    - Regenerates PDF and records complete ProposalEditHistory.
    """
    session = SessionLocal()
    try:
        proposal = session.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        if not proposal:
            return jsonify({'success': False, 'error': f"Proposal '{proposal_id}' not found."}), 404

        # Authorization check
        is_auth, role, actor_name, err_resp = check_proposal_authorization(proposal, request)
        if not is_auth:
            return err_resp

        now = datetime.now(timezone.utc)

        # Professor deadline enforcement
        if role == 'Professor':
            deadline_setting = session.query(DeadlineSetting).order_by(DeadlineSetting.id.desc()).first()
            if deadline_setting:
                is_open, reason = deadline_setting.is_currently_open(now)
                if not is_open:
                    return jsonify({
                        'success': False,
                        'error': 'SUBMISSION_CLOSED',
                        'message': f"Submission deadline has passed. {reason}"
                    }), 403

        data = request.get_json() or {}
        is_valid, validation_errors = validate_proposal_payload(data, session=session)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_FAILED',
                'message': 'Proposal form contains errors. Please correct the highlighted fields.',
                'errors': validation_errors
            }), 400

        # Compute diff for audit history
        changes = []
        diff_dict = {}

        fields_to_track = [
            ('course_title', 'Course Title'),
            ('potential_instructors', 'Potential Instructors'),
            ('course_type', 'Course Type'),
            ('course_level', 'Course Level'),
            ('course_level_secondary', 'Secondary Level'),
            ('course_duration', 'Duration'),
            ('expected_frequency', 'Expected Frequency'),
            ('elective_basket_btech', 'BTech Elective Basket'),
            ('discipline_elective_btech', 'BTech Discipline Elective'),
            ('discipline_basket_btech', 'BTech Discipline Basket'),
            ('minors', 'Minors'),
            ('minor_basket_thematic_area', 'Minor Basket/Thematic Area'),
            ('minor_reason', 'Reason for Adding as Minor'),
            ('discipline_elective_msc', 'MSc Elective'),
            ('courses_discipline_mtech', 'MTech Discipline'),
            ('mtech_sub_specialization', 'MTech Sub-specialization'),
            ('discipline_elective_mdes', 'MDes Elective'),
            ('is_modification', 'Course Nature'),
            ('existing_course_code', 'Existing Course Code'),
            ('prior_knowledge', 'Prior Knowledge'),
            ('course_contents', 'Course Contents'),
            ('texts_and_references', 'Texts and References'),
            ('learning_outcomes', 'Learning Outcomes'),
            ('overlap_courses', 'Overlap Courses'),
            ('other_relevant_info', 'Other Relevant Info'),
        ]

        for attr, label in fields_to_track:
            new_val = data.get(attr)
            old_val = getattr(proposal, attr)

            new_str = str(new_val).strip() if new_val is not None else ""
            old_str = str(old_val).strip() if old_val is not None else ""

            if attr == 'is_modification':
                new_str = str(bool(new_val))
                old_str = str(bool(old_val))

            if new_str != old_str:
                changes.append(f"{label} updated")
                diff_dict[attr] = {'old': old_val, 'new': new_val}

        # Apply updates
        proposal.course_title = data['course_title'].strip()
        proposal.potential_instructors = data['potential_instructors'].strip()
        proposal.course_type = data['course_type'].strip()
        proposal.course_type_other = (data.get('course_type_other') or '').strip() if data.get('course_type') == 'Others' else None
        proposal.course_level = str(data['course_level']).strip()
        proposal.course_level_secondary = str(data.get('course_level_secondary', '')).strip() or None

        l = float(data.get('lecture_hours', 0.0) or 0.0)
        t = float(data.get('tutorial_hours', 0.0) or 0.0)
        p = float(data.get('practical_hours', 0.0) or 0.0)
        c = float(data.get('credits', 0.0) or 0.0)

        proposal.lecture_hours = l
        proposal.tutorial_hours = t
        proposal.practical_hours = p
        proposal.credits = c
        proposal.course_l_t_p_c = data.get('course_l_t_p_c', f"{l}-{t}-{p}-{c}")
        proposal.course_duration = data['course_duration'].strip()
        proposal.expected_frequency = data['expected_frequency'].strip()
        proposal.expected_frequency_other = (data.get('expected_frequency_other') or '').strip() if data.get('expected_frequency') == 'Others' else None

        proposal.elective_basket_btech = data.get('elective_basket_btech') or None
        proposal.discipline_elective_btech = data.get('discipline_elective_btech') or None
        proposal.discipline_basket_btech = (data.get('discipline_basket_btech') or '').strip() or None
        proposal.minors = data.get('minors') or None
        proposal.minor_basket_thematic_area = (data.get('minor_basket_thematic_area') or '').strip() or None
        proposal.minor_reason = (data.get('minor_reason') or '').strip() or None

        proposal.discipline_elective_msc = data.get('discipline_elective_msc') or None
        proposal.courses_discipline_mtech = data.get('courses_discipline_mtech') or None
        proposal.mtech_sub_specialization = (data.get('mtech_sub_specialization') or '').strip() or None
        proposal.discipline_elective_mdes = data.get('discipline_elective_mdes') or None

        proposal.is_modification = bool(data.get('is_modification', False))
        proposal.existing_course_code = (data.get('existing_course_code') or '').strip() or None

        proposal.prior_knowledge = (data.get('prior_knowledge') or '').strip() or None
        proposal.course_contents = data['course_contents'].strip()
        proposal.texts_and_references = data['texts_and_references'].strip()
        proposal.learning_outcomes = data['learning_outcomes'].strip()
        proposal.overlap_courses = (data.get('overlap_courses') or '').strip() or None
        proposal.other_relevant_info = (data.get('other_relevant_info') or '').strip() or None

        custom_raw = data.get('custom_fields_data')
        if custom_raw is not None:
            if isinstance(custom_raw, dict):
                proposal.custom_fields_data = json.dumps(custom_raw)
            else:
                proposal.custom_fields_data = (custom_raw or '').strip() or None

        proposal.updated_at = now

        # Record Edit History
        summary_text = "; ".join(changes) if changes else "Proposal re-saved without attribute changes."
        edit_history_record = ProposalEditHistory(
            proposal_id=proposal_id,
            edited_by=actor_name,
            edited_by_role=role,
            changes_summary=summary_text,
            changes_json=json.dumps(diff_dict)
        )
        session.add(edit_history_record)

        # Regenerate official PDF with updated fields
        try:
            pdf_path, pdf_filename = PDFGenerator.generate_proposal_pdf(
                proposal.to_dict(),
                output_dir=current_app.config['PDF_STORAGE_DIR']
            )
            proposal.pdf_path = pdf_path
            proposal.pdf_filename = pdf_filename
        except Exception as pe:
            current_app.logger.error(f"Failed to regenerate PDF on edit for {proposal_id}: {pe}")

        session.commit()

        return jsonify({
            'success': True,
            'message': f"Proposal {proposal_id} successfully updated and official PDF regenerated.",
            'proposal': proposal.to_dict(),
            'changes': changes
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': f"Failed to update proposal: {str(e)}"}), 500
    finally:
        session.close()


@proposals_bp.route('/<proposal_id>/edit-history', methods=['GET'])
def get_proposal_edit_history(proposal_id):
    """
    Returns complete chronological edit history for a proposal.
    """
    session = SessionLocal()
    try:
        proposal = session.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        if not proposal:
            return jsonify({'success': False, 'error': f"Proposal '{proposal_id}' not found."}), 404

        history = (
            session.query(ProposalEditHistory)
            .filter(ProposalEditHistory.proposal_id == proposal_id)
            .order_by(desc(ProposalEditHistory.edited_at))
            .all()
        )

        return jsonify({
            'success': True,
            'proposal_id': proposal_id,
            'count': len(history),
            'history': [h.to_dict() for h in history]
        }), 200
    finally:
        session.close()


@proposals_bp.route('/<proposal_id>/course-history', methods=['GET'])
def get_course_history(proposal_id):
    """
    Requirement 7: Links course modification proposals to previous proposals using existing course code.
    Shows chronological history, previous approved versions, details, and PDF links.
    Never overwrites old proposals.
    """
    session = SessionLocal()
    try:
        target = session.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        if not target:
            return jsonify({'success': False, 'error': f"Proposal '{proposal_id}' not found."}), 404

        # Search for linked proposals sharing course code or title
        conditions = []
        if target.existing_course_code:
            code = target.existing_course_code.strip()
            conditions.append(Proposal.existing_course_code.ilike(code))
            conditions.append(Proposal.course_title.ilike(f"%{code}%"))

        title_clean = target.course_title.replace('DEMO / SAMPLE DATA:', '').strip()
        if title_clean:
            conditions.append(Proposal.course_title.ilike(f"%{title_clean}%"))

        query = session.query(Proposal)
        if conditions:
            query = query.filter(or_(*conditions))
        else:
            query = query.filter(Proposal.proposal_id == proposal_id)

        all_matches = query.order_by(asc(Proposal.submission_date)).all()

        results = []
        approved_count = 0
        for p in all_matches:
            is_approved = (p.status == 'Approved')
            if is_approved:
                approved_count += 1
            results.append({
                'proposal_id': p.proposal_id,
                'course_title': p.course_title,
                'status': p.status,
                'submission_date': p.submission_date.isoformat() if p.submission_date else None,
                'proposer_name': p.proposer_name,
                'faculty_email': p.faculty_email,
                'is_modification': p.is_modification,
                'existing_course_code': p.existing_course_code,
                'course_type': p.course_type,
                'course_level': p.course_level,
                'credits': float(p.credits or 0.0),
                'pdf_filename': p.pdf_filename,
                'pdf_url': f"/api/proposals/{p.proposal_id}/pdf",
                'is_current': (p.proposal_id == proposal_id),
                'is_approved': is_approved,
                'sapc_number': p.sapc_number,
                'approval_date': p.approval_date.isoformat() if p.approval_date else None
            })

        return jsonify({
            'success': True,
            'proposal_id': proposal_id,
            'course_code': target.existing_course_code,
            'total_versions': len(results),
            'approved_versions_count': approved_count,
            'history': results
        }), 200
    finally:
        session.close()


@proposals_bp.route('/<proposal_id>/send-email', methods=['POST'])
def send_custom_email(proposal_id):
    """
    Requirement 3: Allows professors and admins to compose and send emails
    with the correct proposal PDF attached, including To, CC, editable subject and message.
    Preserves existing automatic notifications and logging.
    """
    session = SessionLocal()
    try:
        proposal = session.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        if not proposal:
            return jsonify({'success': False, 'error': f"Proposal '{proposal_id}' not found."}), 404

        # Check authorization (Admin or Professor with valid edit_token)
        is_auth, role, actor_name, err_resp = check_proposal_authorization(proposal, request)
        if not is_auth:
            return err_resp

        data = request.get_json() or {}
        raw_to = data.get('to') or []
        if isinstance(raw_to, str):
            raw_to = [s.strip() for s in raw_to.split(',') if s.strip()]

        raw_cc = data.get('cc') or []
        if isinstance(raw_cc, str):
            raw_cc = [s.strip() for s in raw_cc.split(',') if s.strip()]

        subject = (data.get('subject') or '').strip()
        if not subject:
            subject = f"SAPC Course Proposal: {proposal.course_title} ({proposal.proposal_id})"

        message = (data.get('message') or '').strip()
        if not message:
            return jsonify({'success': False, 'error': 'Email message body is required.'}), 400

        attach_pdf = bool(data.get('attach_pdf', True))

        # Ensure PDF exists
        if attach_pdf and (not proposal.pdf_path or not Path(proposal.pdf_path).exists()):
            pdf_path, pdf_filename = PDFGenerator.generate_proposal_pdf(
                proposal.to_dict(),
                output_dir=current_app.config['PDF_STORAGE_DIR']
            )
            proposal.pdf_path = pdf_path
            proposal.pdf_filename = pdf_filename
            session.commit()

        success, err, results = EmailService.send_custom_proposal_email(
            proposal=proposal,
            to_emails=raw_to,
            cc_emails=raw_cc,
            subject=subject,
            message_body=message,
            attach_pdf=attach_pdf,
            sender_name=actor_name,
            sender_role=role
        )

        return jsonify({
            'success': success,
            'message': 'Proposal email sent successfully.' if success else f"Email dispatch failed: {err}",
            'results': results,
            'error': err
        }), 200 if success else 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
