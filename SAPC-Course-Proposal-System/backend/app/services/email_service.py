import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timezone
from pathlib import Path
from ..config import Config

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_proposal_submission_notification(proposal, attach_pdf=True):
        """
        Sends an automated notification email to the faculty member whose email
        was provided in the proposal.
        
        Returns: (success: bool, error_message: str or None)
        """
        recipient_email = proposal.faculty_email
        if not recipient_email or "@" not in recipient_email:
            return False, f"Invalid recipient email address: '{recipient_email}'"

        course_title = proposal.course_title
        proposer_name = proposal.proposer_name
        proposal_id = proposal.proposal_id
        
        sub_date = proposal.submission_date
        if isinstance(sub_date, datetime):
            sub_date_str = sub_date.strftime('%d %B %Y, %I:%M %p UTC')
        elif sub_date:
            sub_date_str = str(sub_date)[:19].replace('T', ' ')
        else:
            sub_date_str = datetime.now(timezone.utc).strftime('%d %B %Y, %I:%M %p UTC')

        edit_token = getattr(proposal, 'edit_token', None)
        edit_section_text = ""
        edit_section_html = ""
        if edit_token:
            edit_url = f"{Config.FRONTEND_BASE_URL}/?edit_token={edit_token}&proposal_id={proposal_id}"
            edit_section_text = f"\n\nSecure Proposal Edit Link (Unguessable URL):\n{edit_url}\nYou can use this secure link to edit your proposal prior to the submission deadline.\n"
            edit_section_html = f"""
      <div style="background: #e0f2fe; border: 1px solid #7dd3fc; border-radius: 6px; padding: 14px; margin: 16px 0;">
        <strong style="color: #0369a1;">Secure Proposal Edit Access:</strong><br/>
        <span style="font-size: 13px; color: #0c4a6e;">You may update your proposal before the submission deadline using your unguessable link:</span><br/>
        <a href="{edit_url}" style="color: #0284c7; word-break: break-all; font-family: monospace; font-size: 13px;">{edit_url}</a>
      </div>
"""

        subject = f"SAPC Course Proposal Submitted — {course_title}"
        
        body_text = f"""Dear {proposer_name},

A course proposal has been successfully submitted through the SAPC Course Proposal System.

Course:
{course_title}

Proposal ID:
{proposal_id}

Submitted By:
{proposer_name}

Submission Date:
{sub_date_str}{edit_section_text}

The submitted proposal is available in the Academic Office dashboard.

Regards,
SAPC Course Proposal System
IIT Gandhinagar
"""

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #2d3748; margin: 0; padding: 20px; background-color: #f7fafc; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background-color: #002147; color: #ffffff; padding: 24px; text-align: center; }}
    .header h2 {{ margin: 0; font-size: 18px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .header p {{ margin: 4px 0 0; font-size: 12px; color: #cbd5e0; }}
    .content {{ padding: 28px; }}
    .info-card {{ background: #f8fafc; border-left: 4px solid #002147; padding: 16px; margin: 18px 0; border-radius: 0 6px 6px 0; }}
    .info-row {{ margin-bottom: 8px; }}
    .info-label {{ font-weight: bold; color: #4a5568; font-size: 13px; }}
    .info-val {{ color: #1a202c; font-size: 14px; margin-top: 2px; }}
    .footer {{ background: #edf2f7; padding: 16px; text-align: center; font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>IIT Gandhinagar — Academic Office</h2>
      <p>Senate Academic Programme Committee (SAPC) — Form ACAD-SAPC-01</p>
    </div>
    <div class="content">
      <p>Dear <b>{proposer_name}</b>,</p>
      <p>A course proposal has been successfully submitted through the SAPC Course Proposal System.</p>
      
      <div class="info-card">
        <div class="info-row">
          <div class="info-label">Course:</div>
          <div class="info-val"><b>{course_title}</b></div>
        </div>
        <div class="info-row">
          <div class="info-label">Proposal ID:</div>
          <div class="info-val"><code>{proposal_id}</code></div>
        </div>
        <div class="info-row">
          <div class="info-label">Submitted By:</div>
          <div class="info-val">{proposer_name}</div>
        </div>
        <div class="info-row">
          <div class="info-label">Submission Date:</div>
          <div class="info-val">{sub_date_str}</div>
        </div>
      </div>
      {edit_section_html}
      <p>The submitted proposal is available in the Academic Office dashboard.</p>
      <p>Regards,<br/>
      <strong>SAPC Course Proposal System</strong><br/>
      Indian Institute of Technology Gandhinagar</p>
    </div>
    <div class="footer">
      Official routing: ar.ug@iitgn.ac.in | doaa@iitgn.ac.in<br/>
      This is an automated notification from the SAPC Course Proposal System.
    </div>
  </div>
</body>
</html>
"""

        # Dispatch based on backend setting
        if Config.MAIL_BACKEND == 'smtp' and Config.MAIL_HOST and Config.MAIL_USERNAME:
            return EmailService._send_smtp(
                recipient_email=recipient_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                pdf_path=proposal.pdf_path if attach_pdf else None,
                proposal_id=proposal_id,
                cc_list=[Config.SAPC_UG_OFFICE_EMAIL, Config.SAPC_DOAA_EMAIL] if (Config.SAPC_UG_OFFICE_EMAIL or Config.SAPC_DOAA_EMAIL) else []
            )
        else:
            return EmailService._record_local_outbox(
                recipient_email=recipient_email,
                subject=subject,
                body_text=body_text,
                proposal_id=proposal_id,
                course_title=course_title,
                cc=[Config.SAPC_UG_OFFICE_EMAIL, Config.SAPC_DOAA_EMAIL],
                email_type='Submission Confirmation'
            )

    @staticmethod
    def send_decision_notification(proposal, decision, reviewer_comments=None, attach_pdf=True):
        """
        Sends an official decision email to the submitter (faculty_email) when a reviewer
        makes an authorized decision (Approved, Rejected, Modification Required).

        Returns: (success: bool, error_message: str or None)
        """
        valid_decisions = ['Approved', 'Rejected', 'Modification Required']
        if decision not in valid_decisions:
            return False, f"Invalid decision '{decision}'. Must be one of {valid_decisions}."

        recipient_email = proposal.faculty_email
        if not recipient_email or "@" not in recipient_email:
            return False, f"Invalid submitter recipient email address: '{recipient_email}'"

        course_title = proposal.course_title
        proposal_id = proposal.proposal_id
        proposer_name = proposal.proposer_name
        course_code = (
            getattr(proposal, 'existing_course_code', None) or 
            f"{proposal.course_type}-{proposal.course_level}00" if getattr(proposal, 'course_level', None) else 
            getattr(proposal, 'course_type', 'N/A')
        )
        comments = (reviewer_comments or getattr(proposal, 'reviewer_comments', None) or '').strip()
        comments_display = comments if comments else "No specific comments were provided by the reviewer."

        # Define subjects based on requirement specifications
        if decision == 'Approved':
            subject = f"SAPC Course Proposal Approved — {course_title} — {proposal_id}"
            status_color = "#15803d"
            status_bg = "#dcfce7"
            next_steps = "The course proposal has been approved by the SAPC Academic Office. It will proceed to official curriculum cataloging and semester scheduling."
        elif decision == 'Rejected':
            subject = f"SAPC Course Proposal Rejected — {course_title} — {proposal_id}"
            status_color = "#b91c1c"
            status_bg = "#fee2e2"
            next_steps = "The proposal was not approved in its current formulation. Please review the reviewer comments above. If you wish to discuss this decision or submit an appeal, please contact the Academic Office at ar.ug@iitgn.ac.in."
        else:  # Modification Required
            subject = f"Modifications Required — {course_title} — {proposal_id}"
            status_color = "#b45309"
            status_bg = "#fef3c7"
            next_steps = "Modifications have been requested by the reviewer. Please review the comments above, revise your course proposal accordingly, and coordinate with the Academic Office."

        body_text = f"""Dear {proposer_name},

This is an official communication regarding your course proposal submitted through the SAPC Course Proposal System, IIT Gandhinagar.

Course: {course_title}
Proposal ID: {proposal_id}
Course Code: {course_code}
Decision: {decision}

Reviewer Comments:
{comments_display}

Next Steps:
{next_steps}

Regards,
Academic Office
Senate Academic Programme Committee (SAPC)
Indian Institute of Technology Gandhinagar
"""

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #2d3748; margin: 0; padding: 20px; background-color: #f7fafc; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background-color: #002147; color: #ffffff; padding: 24px; text-align: center; }}
    .header h2 {{ margin: 0; font-size: 18px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .header p {{ margin: 4px 0 0; font-size: 12px; color: #cbd5e0; }}
    .content {{ padding: 28px; }}
    .badge {{ display: inline-block; padding: 6px 14px; font-weight: 700; border-radius: 6px; font-size: 14px; color: {status_color}; background-color: {status_bg}; }}
    .info-card {{ background: #f8fafc; border-left: 4px solid #002147; padding: 16px; margin: 18px 0; border-radius: 0 6px 6px 0; }}
    .info-row {{ margin-bottom: 8px; }}
    .info-label {{ font-weight: bold; color: #4a5568; font-size: 13px; }}
    .info-val {{ color: #1a202c; font-size: 14px; margin-top: 2px; }}
    .comments-box {{ background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 14px; margin: 16px 0; }}
    .footer {{ background: #edf2f7; padding: 16px; text-align: center; font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>IIT Gandhinagar — Academic Office</h2>
      <p>Senate Academic Programme Committee (SAPC) — Decision Notification</p>
    </div>
    <div class="content">
      <p>Dear <b>{proposer_name}</b>,</p>
      <p>An authorized review decision has been recorded for your course proposal:</p>
      
      <div style="text-align: center; margin: 16px 0;">
        <span class="badge">Decision: {decision}</span>
      </div>

      <div class="info-card">
        <div class="info-row">
          <div class="info-label">Course Title:</div>
          <div class="info-val"><b>{course_title}</b></div>
        </div>
        <div class="info-row">
          <div class="info-label">Proposal ID:</div>
          <div class="info-val"><code>{proposal_id}</code></div>
        </div>
        <div class="info-row">
          <div class="info-label">Course Code:</div>
          <div class="info-val">{course_code}</div>
        </div>
      </div>

      <div class="comments-box">
        <div style="font-weight: 700; color: #92400e; margin-bottom: 4px; font-size: 13px;">Reviewer Comments / Remarks:</div>
        <div style="color: #1e293b; font-size: 13.5px; white-space: pre-wrap;">{comments_display}</div>
      </div>

      <p><b>Next Steps:</b><br/>{next_steps}</p>

      <p style="margin-top: 24px;">Regards,<br/>
      <strong>Academic Office</strong><br/>
      Senate Academic Programme Committee (SAPC)<br/>
      Indian Institute of Technology Gandhinagar</p>
    </div>
    <div class="footer">
      Official routing: ar.ug@iitgn.ac.in | doaa@iitgn.ac.in<br/>
      This is an official decision notification from the SAPC Course Proposal Platform.
    </div>
  </div>
</body>
</html>
"""

        # Dispatch
        if Config.MAIL_BACKEND == 'smtp' and Config.MAIL_HOST and Config.MAIL_USERNAME:
            return EmailService._send_smtp(
                recipient_email=recipient_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                pdf_path=proposal.pdf_path if attach_pdf else None,
                proposal_id=proposal_id
            )
        else:
            return EmailService._record_local_outbox(
                recipient_email=recipient_email,
                subject=subject,
                body_text=body_text,
                proposal_id=proposal_id,
                course_title=course_title,
                email_type='Decision Notification'
            )

    @staticmethod
    def send_proposal_copy_to_recipients(proposal, recipient_emails=None, attach_pdf=True):
        """
        Sends a proposal copy email to additional recipients (CC: HOD, colleagues, professors).
        Each recipient is messaged individually to maintain privacy (recipients do not see each
        other's addresses). Submitter's email is set as Reply-To.
        
        Returns: (overall_success: bool, recipient_results: dict)
        where recipient_results maps email -> {'sent': bool, 'error': str or None}
        """
        if recipient_emails is None:
            if hasattr(proposal, 'recipients') and proposal.recipients:
                recipient_emails = [r.email for r in proposal.recipients]
            else:
                recipient_emails = []

        if not recipient_emails:
            return True, {}

        course_title = proposal.course_title
        proposal_id = proposal.proposal_id
        proposer_name = proposal.proposer_name
        proposer_email = proposal.faculty_email
        course_code = (
            getattr(proposal, 'existing_course_code', None) or 
            f"{proposal.course_type}-{proposal.course_level}00" if getattr(proposal, 'course_level', None) else 
            getattr(proposal, 'course_type', 'N/A')
        )
        ltpc = getattr(proposal, 'course_l_t_p_c', 'N/A')
        credits_val = getattr(proposal, 'credits', 'N/A')
        level_val = getattr(proposal, 'course_level', 'N/A')
        duration_val = getattr(proposal, 'course_duration', 'N/A')

        subject = f"Course Proposal for Review — {course_title} — {proposal_id}"

        body_text = f"""Dear Colleague,

Please find the attached course proposal submitted through the SAPC Course Proposal Platform for your review.

Course: {course_title}
Proposal ID: {proposal_id}
Course Code: {course_code}
Submitted By: {proposer_name} ({proposer_email})
L-T-P-C: {ltpc} ({credits_val} Credits)
Course Level: Level {level_val}
Course Duration: {duration_val}

Regards,
{proposer_name}
(Dispatched via SAPC Course Proposal Platform, IIT Gandhinagar)
"""

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #2d3748; margin: 0; padding: 20px; background-color: #f7fafc; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background-color: #002147; color: #ffffff; padding: 24px; text-align: center; }}
    .header h2 {{ margin: 0; font-size: 18px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .header p {{ margin: 4px 0 0; font-size: 12px; color: #cbd5e0; }}
    .content {{ padding: 28px; }}
    .info-card {{ background: #f8fafc; border-left: 4px solid #002147; padding: 16px; margin: 18px 0; border-radius: 0 6px 6px 0; }}
    .info-row {{ margin-bottom: 8px; }}
    .info-label {{ font-weight: bold; color: #4a5568; font-size: 13px; }}
    .info-val {{ color: #1a202c; font-size: 14px; margin-top: 2px; }}
    .footer {{ background: #edf2f7; padding: 16px; text-align: center; font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>IIT Gandhinagar — Academic Office</h2>
      <p>Senate Academic Programme Committee (SAPC) — Proposal Copy</p>
    </div>
    <div class="content">
      <p>Dear Colleague,</p>
      <p>Please find the attached course proposal submitted through the SAPC Course Proposal Platform for your review.</p>

      <div class="info-card">
        <div class="info-row">
          <div class="info-label">Course:</div>
          <div class="info-val"><b>{course_title}</b></div>
        </div>
        <div class="info-row">
          <div class="info-label">Proposal ID:</div>
          <div class="info-val"><code>{proposal_id}</code></div>
        </div>
        <div class="info-row">
          <div class="info-label">Course Code:</div>
          <div class="info-val">{course_code}</div>
        </div>
        <div class="info-row">
          <div class="info-label">Submitted By:</div>
          <div class="info-val">{proposer_name} ({proposer_email})</div>
        </div>
        <div class="info-row">
          <div class="info-label">Structure (L-T-P-C):</div>
          <div class="info-val">{ltpc} ({credits_val} Credits)</div>
        </div>
        <div class="info-row">
          <div class="info-label">Level & Duration:</div>
          <div class="info-val">Level {level_val} | {duration_val}</div>
        </div>
      </div>

      <p>An official PDF copy of the complete course proposal is attached to this email.</p>

      <p style="margin-top: 24px;">Regards,<br/>
      <strong>{proposer_name}</strong><br/>
      <span style="font-size: 12px; color: #64748b;">(Dispatched via SAPC Course Proposal Platform, IIT Gandhinagar)</span></p>
    </div>
    <div class="footer">
      This copy was sent at the submitter's request. Reply directly to {proposer_email}.
    </div>
  </div>
</body>
</html>
"""

        results = {}
        all_success = True

        for email in recipient_emails:
            clean_email = email.strip()
            if not clean_email or "@" not in clean_email:
                results[clean_email] = {'sent': False, 'error': f"Invalid recipient email: '{clean_email}'"}
                all_success = False
                continue

            if Config.MAIL_BACKEND == 'smtp' and Config.MAIL_HOST and Config.MAIL_USERNAME:
                sent, err = EmailService._send_smtp(
                    recipient_email=clean_email,
                    subject=subject,
                    body_text=body_text,
                    body_html=body_html,
                    pdf_path=proposal.pdf_path if attach_pdf else None,
                    proposal_id=proposal_id,
                    reply_to=proposer_email
                )
            else:
                sent, err = EmailService._record_local_outbox(
                    recipient_email=clean_email,
                    subject=subject,
                    body_text=body_text,
                    proposal_id=proposal_id,
                    course_title=course_title,
                    reply_to=proposer_email,
                    email_type='Proposal Copy (CC)'
                )

            results[clean_email] = {'sent': sent, 'error': err}
            if not sent:
                all_success = False

        return all_success, results

    @staticmethod
    def send_security_dept_notification(proposal, attach_pdf=True):
        """
        Sends an official PDF copy of the submitted proposal to the configured
        Security Department email address (Requirement 6).
        Returns: (success: bool, error_message: str or None)
        """
        security_email = Config.SECURITY_DEPT_EMAIL.strip()
        if not security_email or "@" not in security_email:
            return False, f"Invalid Security Department email configured: '{security_email}'"

        course_title = proposal.course_title
        proposer_name = proposal.proposer_name
        proposal_id = proposal.proposal_id
        course_type = proposal.course_type
        
        sub_date = proposal.submission_date
        if isinstance(sub_date, datetime):
            sub_date_str = sub_date.strftime('%d %B %Y, %I:%M %p UTC')
        elif sub_date:
            sub_date_str = str(sub_date)[:19].replace('T', ' ')
        else:
            sub_date_str = datetime.now(timezone.utc).strftime('%d %B %Y, %I:%M %p UTC')

        subject = f"[SAPC Security Notification] New Course Proposal Submitted — {course_title} ({proposal_id})"
        
        body_text = f"""Dear Security Department,

A new course proposal has been formally submitted in the SAPC Course Proposal System:

Course Title: {course_title}
Proposal ID: {proposal_id}
Department / Type: {course_type}
Proposer: {proposer_name} ({proposal.faculty_email})
Submission Date: {sub_date_str}

An official ACAD-SAPC-01 PDF copy is attached for Security Department records and institutional archive.

Regards,
Academic Office / SAPC
Indian Institute of Technology Gandhinagar
"""

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #2d3748; margin: 0; padding: 20px; background-color: #f7fafc; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background-color: #1e293b; color: #ffffff; padding: 20px; text-align: center; border-bottom: 3px solid #c29b38; }}
    .header h2 {{ margin: 0; font-size: 16px; letter-spacing: 0.5px; }}
    .content {{ padding: 24px; }}
    .info-card {{ background: #f8fafc; border-left: 4px solid #1e293b; padding: 14px; margin: 16px 0; border-radius: 0 6px 6px 0; }}
    .info-row {{ margin-bottom: 6px; }}
    .info-label {{ font-weight: bold; color: #4a5568; font-size: 12.5px; }}
    .info-val {{ color: #0f172a; font-size: 13.5px; }}
    .footer {{ background: #f1f5f9; padding: 12px; text-align: center; font-size: 11px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>IIT Gandhinagar — Institutional Security Archive Notice</h2>
      <p style="margin: 4px 0 0; font-size: 12px; color: #94a3b8;">Senate Academic Programme Committee (SAPC)</p>
    </div>
    <div class="content">
      <p>Dear <b>Security Department</b>,</p>
      <p>This automated institutional notice confirms the submission of a new course proposal for institutional record keeping.</p>
      
      <div class="info-card">
        <div class="info-row"><span class="info-label">Proposal ID:</span> <span class="info-val"><code>{proposal_id}</code></span></div>
        <div class="info-row"><span class="info-label">Course Title:</span> <span class="info-val"><b>{course_title}</b></span></div>
        <div class="info-row"><span class="info-label">Discipline / Type:</span> <span class="info-val">{course_type}</span></div>
        <div class="info-row"><span class="info-label">Proposer:</span> <span class="info-val">{proposer_name} ({proposal.faculty_email})</span></div>
        <div class="info-row"><span class="info-label">Submission Date:</span> <span class="info-val">{sub_date_str}</span></div>
      </div>
      
      <p>An official ACAD-SAPC-01 PDF document is attached for departmental reference.</p>
      <p>Academic Office, IIT Gandhinagar</p>
    </div>
    <div class="footer">
      Automated routing to {security_email} | SAPC Course Proposal System
    </div>
  </div>
</body>
</html>
"""

        try:
            if Config.MAIL_BACKEND == 'smtp' and Config.MAIL_HOST and Config.MAIL_USERNAME:
                return EmailService._send_smtp(
                    recipient_email=security_email,
                    subject=subject,
                    body_text=body_text,
                    body_html=body_html,
                    pdf_path=proposal.pdf_path if attach_pdf else None,
                    proposal_id=proposal_id,
                    reply_to=proposal.faculty_email
                )
            else:
                return EmailService._record_local_outbox(
                    recipient_email=security_email,
                    subject=subject,
                    body_text=body_text,
                    proposal_id=proposal_id,
                    course_title=course_title,
                    reply_to=proposal.faculty_email,
                    email_type='Security Department Notification'
                )
        except Exception as e:
            return False, f"Security notification dispatch exception: {str(e)}"

    @staticmethod
    def send_custom_proposal_email(proposal, to_emails, cc_emails, subject, message_body, attach_pdf=True, sender_name=None, sender_role=None):
        """
        Sends a manual custom composed email with the proposal PDF attached (Requirement 3).
        Validates recipients, logs to outbox, and returns execution summary.
        """
        import re
        email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

        # Clean 'to' recipients
        clean_to = []
        for em in to_emails:
            e = em.strip()
            if e and email_regex.match(e):
                clean_to.append(e)

        if not clean_to:
            return False, "At least one valid recipient (To) address is required.", {}

        # Clean 'cc' recipients
        clean_cc = []
        if cc_emails:
            for em in cc_emails:
                e = em.strip()
                if e and email_regex.match(e) and e not in clean_to and e not in clean_cc:
                    clean_cc.append(e)

        sender_label = sender_name or proposal.proposer_name
        role_label = f" ({sender_role})" if sender_role else ""

        full_text_body = f"""{message_body}

--------------------------------------------------------------------------------
Proposal Details:
Course: {proposal.course_title}
Proposal ID: {proposal.proposal_id}
Proposer: {proposal.proposer_name} ({proposal.faculty_email})
Status: {proposal.status}
{"An official ACAD-SAPC-01 PDF copy is attached." if attach_pdf else ""}
--------------------------------------------------------------------------------
Dispatched by: {sender_label}{role_label}
SAPC Course Proposal System — IIT Gandhinagar
"""

        escaped_msg = message_body.replace('\n', '<br/>')
        full_html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #2d3748; margin: 0; padding: 20px; background-color: #f7fafc; }}
    .container {{ max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background-color: #002147; color: #ffffff; padding: 20px; text-align: center; border-bottom: 3px solid #c29b38; }}
    .content {{ padding: 24px; }}
    .msg-box {{ background: #f8fafc; border-left: 4px solid #002147; padding: 16px; margin: 16px 0; border-radius: 0 6px 6px 0; font-size: 14px; color: #1e293b; }}
    .proposal-card {{ background: #f1f5f9; border-radius: 6px; padding: 14px; margin-top: 18px; font-size: 12.5px; }}
    .footer {{ background: #edf2f7; padding: 12px; text-align: center; font-size: 11px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h3 style="margin: 0; font-size: 16px;">IIT Gandhinagar — Academic Office</h3>
      <p style="margin: 4px 0 0; font-size: 12px; color: #cbd5e0;">Senate Academic Programme Committee (SAPC)</p>
    </div>
    <div class="content">
      <div class="msg-box">
        {escaped_msg}
      </div>

      <div class="proposal-card">
        <strong>Reference Proposal:</strong> {proposal.course_title}<br/>
        <strong>Proposal ID:</strong> <code>{proposal.proposal_id}</code> | <strong>Status:</strong> {proposal.status}<br/>
        <strong>Proposer:</strong> {proposal.proposer_name} ({proposal.faculty_email})
        {"<br/><em>Official ACAD-SAPC-01 PDF copy is attached.</em>" if attach_pdf else ""}
      </div>

      <p style="margin-top: 20px; font-size: 13px; color: #475569;">
        Dispatched by <strong>{sender_label}</strong>{role_label} via SAPC Course Proposal Platform.
      </p>
    </div>
    <div class="footer">
      SAPC Course Proposal System — Indian Institute of Technology Gandhinagar
    </div>
  </div>
</body>
</html>
"""

        delivery_results = {}
        all_ok = True

        for to_addr in clean_to:
            if Config.MAIL_BACKEND == 'smtp' and Config.MAIL_HOST and Config.MAIL_USERNAME:
                sent, err = EmailService._send_smtp(
                    recipient_email=to_addr,
                    subject=subject,
                    body_text=full_text_body,
                    body_html=full_html_body,
                    pdf_path=proposal.pdf_path if attach_pdf else None,
                    proposal_id=proposal.proposal_id,
                    reply_to=proposal.faculty_email,
                    cc_list=clean_cc
                )
            else:
                sent, err = EmailService._record_local_outbox(
                    recipient_email=to_addr,
                    subject=subject,
                    body_text=full_text_body,
                    proposal_id=proposal.proposal_id,
                    course_title=proposal.course_title,
                    cc=clean_cc,
                    reply_to=proposal.faculty_email,
                    email_type='Manual Proposal Email'
                )
            delivery_results[to_addr] = {'sent': sent, 'error': err}
            if not sent:
                all_ok = False

        return all_ok, None if all_ok else "One or more email deliveries failed", delivery_results


    @staticmethod
    def _send_smtp(recipient_email, subject, body_text, body_html, pdf_path=None, proposal_id=None, reply_to=None, cc_list=None):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{Config.MAIL_SENDER_NAME} <{Config.MAIL_FROM}>"
            msg['To'] = recipient_email
            
            if reply_to:
                msg['Reply-To'] = reply_to

            # Optional CC list
            final_cc_list = []
            if cc_list:
                final_cc_list = [c for c in cc_list if c]
                if final_cc_list:
                    msg['Cc'] = ", ".join(final_cc_list)

            part1 = MIMEText(body_text, 'plain')
            part2 = MIMEText(body_html, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Optional attachment
            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, 'rb') as f:
                    attach = MIMEApplication(f.read(), _subtype="pdf")
                    attach.add_header('Content-Disposition', 'attachment', filename=f"{proposal_id}.pdf")
                    msg.attach(attach)

            all_recipients = [recipient_email] + final_cc_list

            if Config.MAIL_USE_SSL:
                server = smtplib.SMTP_SSL(Config.MAIL_HOST, Config.MAIL_PORT, timeout=10)
            else:
                server = smtplib.SMTP(Config.MAIL_HOST, Config.MAIL_PORT, timeout=10)
                if Config.MAIL_USE_TLS:
                    server.starttls()

            if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)

            server.sendmail(Config.MAIL_FROM, all_recipients, msg.as_string())
            server.quit()
            logger.info(f"Notification email sent successfully via SMTP to {recipient_email} for proposal {proposal_id}")
            return True, None
        except Exception as e:
            err = f"SMTP Transmission failed: {str(e)}"
            logger.error(err)
            return False, err

    @staticmethod
    def _record_local_outbox(recipient_email, subject, body_text, proposal_id, course_title=None, cc=None, reply_to=None, email_type='Submission Notification'):
        """
        Local development & test outbox recorder.
        Persists email to outbox_emails.json and logs to stdout.
        """
        try:
            log_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'proposal_id': proposal_id,
                'recipient': recipient_email,
                'reply_to': reply_to,
                'cc': cc or [],
                'email_type': email_type,
                'subject': subject,
                'body': body_text,
                'status': 'Simulated Delivered (Local Mailbox)'
            }
            
            # Read existing
            log_file = Path(Config.MAIL_LOG_FILE)
            records = []
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except Exception:
                    records = []
                    
            records.insert(0, log_entry)
            # Keep last 150 entries
            records = records[:150]
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2)

            logger.info(f"[LOCAL OUTBOX] Proposal {proposal_id} ({email_type}) logged for {recipient_email}")
            return True, None
        except Exception as e:
            err = f"Failed to record local email outbox: {str(e)}"
            logger.error(err)
            return False, err

    @staticmethod
    def get_outbox_logs():
        """Returns the list of dispatched emails from local mailbox"""
        log_file = Path(Config.MAIL_LOG_FILE)
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
