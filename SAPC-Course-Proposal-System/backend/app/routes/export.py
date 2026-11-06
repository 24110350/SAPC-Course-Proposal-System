from datetime import datetime, timezone
import io
from flask import Blueprint, request, jsonify, Response, send_file
from sqlalchemy import or_, desc, asc
from ..models import SessionLocal
from ..models.proposal import Proposal
from ..services.export_service import ExportService
from ..utils.auth_helper import admin_required

export_bp = Blueprint('export', __name__, url_prefix='/api/proposals/export')

@export_bp.route('', methods=['GET'])
@admin_required
def export_proposals():
    """
    Exports proposals matching current filter/search criteria as Excel (.xlsx) or CSV.
    """
    fmt = request.args.get('format', 'xlsx').lower()
    session = SessionLocal()
    try:
        query = session.query(Proposal)

        # Apply same filters as dashboard
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

        sort_by = request.args.get('sort_by', 'submission_date')
        order = request.args.get('order', 'desc').lower()

        sort_col = getattr(Proposal, sort_by, Proposal.submission_date)
        if order == 'asc':
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        proposals = query.all()
        date_tag = datetime.now().strftime('%Y%m%d_%H%M')

        if fmt == 'csv':
            csv_bytes = ExportService.generate_csv(proposals)
            filename = f"SAPC_Proposals_{date_tag}.csv"
            return Response(
                csv_bytes,
                mimetype='text/csv; charset=utf-8',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        elif fmt == 'xlsx':
            xlsx_bytes = ExportService.generate_excel(proposals)
            filename = f"SAPC_Proposals_{date_tag}.xlsx"
            return Response(
                xlsx_bytes,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        else:
            return jsonify({'success': False, 'error': f"Unsupported export format '{fmt}'. Use 'xlsx' or 'csv'."}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
