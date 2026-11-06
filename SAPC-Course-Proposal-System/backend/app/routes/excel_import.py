import io
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response
import openpyxl
from dateutil import parser as date_parser
from ..models import SessionLocal
from ..models.proposal import Proposal, ProposalEditHistory
from ..models.user import ProposalStatusHistory
from ..services.pdf_service import PDFGenerator
from ..utils.auth_helper import admin_required

excel_import_bp = Blueprint('excel_import', __name__, url_prefix='/api/proposals/import')

VALID_STATUSES = ['Pending', 'Under Review', 'Approved', 'Rejected', 'Modification Required']

@excel_import_bp.route('/template', methods=['GET'])
@admin_required
def download_import_template():
    """
    Downloads pre-formatted Excel template for SAPC Numbers and Approvals.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SAPC_Import_Template"

    headers = [
        "Proposal ID", "Course Title", "SAPC Number", "Approval Date (YYYY-MM-DD)", "Status", "Reviewer Remarks"
    ]
    ws.append(headers)

    # Sample demo rows
    ws.append(["SAPC-2026-0001", "Distributed Systems and Cloud Computing", "SAPC-68-01", "2026-11-04", "Approved", "Approved in 68th SAPC Meeting."])
    ws.append(["SAPC-2026-0002", "Advanced Machine Learning", "SAPC-68-02", "2026-11-04", "Approved", "Recommended for approval."])

    # Styling header
    header_fill = openpyxl.styles.PatternFill(start_color="002147", end_color="002147", fill_type="solid")
    header_font = openpyxl.styles.Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    for col in range(1, len(headers) + 1):
        c = ws.cell(row=1, column=col)
        c.fill = header_fill
        c.font = header_font
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 28

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    return Response(
        out.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename="SAPC_Import_Template.xlsx"'}
    )

@excel_import_bp.route('/preview', methods=['POST'])
@admin_required
def preview_excel_import():
    """
    Parses and validates uploaded Excel workbook against existing database proposals.
    Provides row-by-row matching status, validation errors, and preview data.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded. Please upload a .xlsx file.'}), 400

    file = request.files['file']
    if not file.filename.lower().endswith(('.xlsx', '.xlsm')):
        return jsonify({'success': False, 'error': 'Invalid file format. Please upload an Excel (.xlsx) file.'}), 400

    session = SessionLocal()
    try:
        wb = openpyxl.load_workbook(file, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            return jsonify({'success': False, 'error': 'The uploaded Excel file contains no data rows.'}), 400

        header_row = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        
        # Header column index mapping
        def find_col(*aliases):
            for i, h in enumerate(header_row):
                h_low = h.lower().replace('_', ' ').replace('-', ' ').strip()
                for a in aliases:
                    if a.lower() in h_low:
                        return i
            return -1

        col_id = find_col("proposal id", "proposal_id", "id")
        col_title = find_col("course title", "title", "course")
        col_sapc = find_col("sapc number", "sapc no", "sapc_number", "agenda")
        col_date = find_col("approval date", "approved date", "approval_date", "date")
        col_status = find_col("status")
        col_remarks = find_col("reviewer remarks", "remarks", "comments")

        if col_id == -1 and col_title == -1:
            return jsonify({
                'success': False,
                'error': f"Excel must contain at least 'Proposal ID' or 'Course Title' column. Found headers: {', '.join(header_row)}"
            }), 400

        valid_rows = []
        invalid_rows = []

        for row_idx, r in enumerate(rows[1:], start=2):
            if not r or all(c is None or str(c).strip() == "" for c in r):
                continue # skip empty row

            prop_id_val = str(r[col_id]).strip() if col_id != -1 and r[col_id] is not None else ""
            title_val = str(r[col_title]).strip() if col_title != -1 and r[col_title] is not None else ""
            sapc_val = str(r[col_sapc]).strip() if col_sapc != -1 and r[col_sapc] is not None else ""
            date_raw = r[col_date] if col_date != -1 else None
            status_val = str(r[col_status]).strip() if col_status != -1 and r[col_status] is not None else ""
            remarks_val = str(r[col_remarks]).strip() if col_remarks != -1 and r[col_remarks] is not None else ""

            row_errors = []

            # 1. Proposal Matching
            proposal = None
            if prop_id_val:
                proposal = session.query(Proposal).filter(Proposal.proposal_id.ilike(prop_id_val)).first()
            if not proposal and title_val:
                proposal = session.query(Proposal).filter(Proposal.course_title.ilike(title_val)).first()

            if not proposal:
                row_errors.append(f"No existing proposal found matching ID '{prop_id_val}' or Title '{title_val}'.")

            # 2. Status Validation
            if status_val and status_val not in VALID_STATUSES:
                row_errors.append(f"Invalid status '{status_val}'. Allowed: {', '.join(VALID_STATUSES)}.")

            # 3. Approval Date Validation
            parsed_date = None
            if date_raw is not None and str(date_raw).strip() != "":
                if isinstance(date_raw, datetime):
                    parsed_date = date_raw
                else:
                    try:
                        parsed_date = date_parser.parse(str(date_raw))
                    except Exception:
                        row_errors.append(f"Invalid Approval Date format '{date_raw}'. Expected YYYY-MM-DD.")

            row_summary = {
                'row_number': row_idx,
                'proposal_id': proposal.proposal_id if proposal else (prop_id_val or "Unknown"),
                'course_title': proposal.course_title if proposal else (title_val or "—"),
                'matched': proposal is not None,
                'current_status': proposal.status if proposal else "—",
                'sapc_number': sapc_val,
                'approval_date': parsed_date.strftime('%Y-%m-%d') if parsed_date else (str(date_raw) if date_raw else ""),
                'new_status': status_val or (proposal.status if proposal else ""),
                'remarks': remarks_val,
                'errors': row_errors,
                'is_valid': len(row_errors) == 0
            }

            if row_summary['is_valid']:
                valid_rows.append(row_summary)
            else:
                invalid_rows.append(row_summary)

        return jsonify({
            'success': True,
            'total_rows': len(valid_rows) + len(invalid_rows),
            'valid_count': len(valid_rows),
            'invalid_count': len(invalid_rows),
            'valid_rows': valid_rows,
            'invalid_rows': invalid_rows
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': f"Failed to parse Excel file: {str(e)}"}), 500
    finally:
        session.close()

@excel_import_bp.route('/confirm', methods=['POST'])
@admin_required
def confirm_excel_import():
    """
    Applies confirmed Excel import rows to database proposals safely.
    Regenerates PDFs and records status/edit history.
    """
    data = request.get_json() or {}
    rows_to_import = data.get('rows', [])
    if not rows_to_import:
        return jsonify({'success': False, 'error': 'No valid rows provided for import.'}), 400

    admin_username = request.user.get('sub', 'Academic Office Admin')
    session = SessionLocal()
    updated_count = 0
    errors = []

    try:
        from flask import current_app
        for r in rows_to_import:
            prop_id = r.get('proposal_id')
            if not prop_id:
                continue

            proposal = session.query(Proposal).filter(Proposal.proposal_id == prop_id).first()
            if not proposal:
                errors.append(f"Proposal {prop_id} could not be found.")
                continue

            changes = []
            # SAPC Number
            new_sapc = (r.get('sapc_number') or '').strip()
            if new_sapc and new_sapc != proposal.sapc_number:
                changes.append(f"SAPC Number updated from '{proposal.sapc_number or 'None'}' to '{new_sapc}'")
                proposal.sapc_number = new_sapc

            # Approval Date
            new_date_str = r.get('approval_date')
            if new_date_str:
                try:
                    new_date = date_parser.parse(str(new_date_str))
                    proposal.approval_date = new_date
                    changes.append(f"Approval date set to {new_date.strftime('%Y-%m-%d')}")
                except Exception:
                    pass

            # Status
            new_status = (r.get('new_status') or '').strip()
            if new_status and new_status in VALID_STATUSES and new_status != proposal.status:
                prev_status = proposal.status
                proposal.status = new_status
                changes.append(f"Status changed from '{prev_status}' to '{new_status}'")
                
                # Record Status History
                sh = ProposalStatusHistory(
                    proposal_id=prop_id,
                    previous_status=prev_status,
                    new_status=new_status,
                    remarks=r.get('remarks') or f"Status updated via Excel Import by {admin_username}",
                    changed_by=admin_username
                )
                session.add(sh)

            # Reviewer Remarks
            remarks = (r.get('remarks') or '').strip()
            if remarks:
                proposal.reviewer_comments = remarks

            proposal.updated_at = datetime.now(timezone.utc)

            # Record Edit History
            if changes:
                eh = ProposalEditHistory(
                    proposal_id=prop_id,
                    edited_by=admin_username,
                    edited_by_role='Academic Office',
                    changes_summary="; ".join(changes),
                    changes_json=json.dumps(r)
                )
                session.add(eh)

            # Regenerate PDF with updated fields
            try:
                pdf_path, pdf_filename = PDFGenerator.generate_proposal_pdf(
                    proposal.to_dict(),
                    output_dir=current_app.config['PDF_STORAGE_DIR']
                )
                proposal.pdf_path = pdf_path
                proposal.pdf_filename = pdf_filename
            except Exception as pe:
                current_app.logger.warning(f"Could not regenerate PDF for {prop_id} during import: {pe}")

            updated_count += 1

        session.commit()
        return jsonify({
            'success': True,
            'message': f"Successfully updated {updated_count} proposal(s) from Excel import.",
            'updated_count': updated_count,
            'errors': errors
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': f"Failed to apply import updates: {str(e)}"}), 500
    finally:
        session.close()
