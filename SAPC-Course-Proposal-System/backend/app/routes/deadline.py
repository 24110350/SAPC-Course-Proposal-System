from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from ..models import SessionLocal
from ..models.deadline import DeadlineSetting
from ..utils.auth_helper import admin_required

deadline_bp = Blueprint('deadline', __name__, url_prefix='/api/deadline')

@deadline_bp.route('', methods=['GET'])
def get_deadline_status():
    """
    Public endpoint: Checks whether course proposal submission is currently open.
    Enforces server-side deadline logic.
    """
    session = SessionLocal()
    try:
        setting = session.query(DeadlineSetting).order_by(DeadlineSetting.id.desc()).first()
        if not setting:
            return jsonify({
                'success': True,
                'is_open': True,
                'status_message': 'No deadline configured. Submissions are open.',
                'server_time': datetime.now(timezone.utc).isoformat()
            }), 200

        # Optional simulated check_time for automated boundary testing
        check_time_str = request.args.get('check_time')
        check_time = None
        if check_time_str:
            try:
                check_time = datetime.fromisoformat(check_time_str.replace('Z', '+00:00'))
            except Exception:
                pass

        data = setting.to_dict(check_time=check_time)
        return jsonify({
            'success': True,
            'deadline': data
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@deadline_bp.route('', methods=['PUT'])
@admin_required
def update_deadline_settings():
    """
    Admin-only endpoint: Update submission start date, deadline date, active status,
    and announcement message.
    """
    data = request.get_json() or {}
    session = SessionLocal()
    try:
        setting = session.query(DeadlineSetting).order_by(DeadlineSetting.id.desc()).first()
        if not setting:
            setting = DeadlineSetting()
            session.add(setting)

        # Parse start and deadline
        if 'submission_start' in data:
            setting.submission_start = datetime.fromisoformat(data['submission_start'].replace('Z', '+00:00'))
        if 'submission_deadline' in data:
            setting.submission_deadline = datetime.fromisoformat(data['submission_deadline'].replace('Z', '+00:00'))
        if 'is_active' in data:
            setting.is_active = bool(data['is_active'])
        if 'announcement_message' in data:
            setting.announcement_message = data['announcement_message']

        setting.updated_by = request.user.get('sub', 'admin')
        session.commit()

        return jsonify({
            'success': True,
            'message': 'Deadline configuration updated successfully.',
            'deadline': setting.to_dict()
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': f"Failed to update deadline: {str(e)}"}), 400
    finally:
        session.close()

@deadline_bp.route('/boundary-check', methods=['POST'])
def boundary_check():
    """
    Dedicated endpoint for testing deadline boundary behaviors
    (submission before deadline, exactly at deadline, immediately after deadline).
    """
    data = request.get_json() or {}
    check_time_str = data.get('check_time')
    if not check_time_str:
        return jsonify({'success': False, 'error': 'Missing check_time'}), 400

    try:
        check_time = datetime.fromisoformat(check_time_str.replace('Z', '+00:00'))
    except Exception as e:
        return jsonify({'success': False, 'error': f"Invalid datetime format: {e}"}), 400

    session = SessionLocal()
    try:
        setting = session.query(DeadlineSetting).order_by(DeadlineSetting.id.desc()).first()
        if not setting:
            return jsonify({'is_open': True, 'message': 'No deadline configured'}), 200

        is_open, reason = setting.is_currently_open(check_time)
        return jsonify({
            'success': True,
            'check_time': check_time.isoformat(),
            'submission_start': setting.submission_start.isoformat(),
            'submission_deadline': setting.submission_deadline.isoformat(),
            'is_open': is_open,
            'reason': reason
        }), 200
    finally:
        session.close()
