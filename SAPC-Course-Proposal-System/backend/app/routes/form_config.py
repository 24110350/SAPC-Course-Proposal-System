from flask import Blueprint, request, jsonify
from ..models import SessionLocal
from ..models.form_config import FormFieldOption, CustomFormField
from ..utils.auth_helper import admin_required

form_config_bp = Blueprint('form_config', __name__, url_prefix='/api/form-config')

@form_config_bp.route('', methods=['GET'])
def get_active_form_config():
    """
    Public endpoint: Returns active dropdown options grouped by category,
    and active custom fields for the proposal form.
    """
    session = SessionLocal()
    try:
        options = (
            session.query(FormFieldOption)
            .filter(FormFieldOption.is_active == True)
            .order_by(FormFieldOption.category, FormFieldOption.display_order, FormFieldOption.id)
            .all()
        )

        grouped = {}
        for opt in options:
            if opt.category not in grouped:
                grouped[opt.category] = []
            grouped[opt.category].append({
                'id': opt.id,
                'value': opt.value,
                'label': opt.label
            })

        custom_fields = (
            session.query(CustomFormField)
            .filter(CustomFormField.is_active == True)
            .order_by(CustomFormField.display_order, CustomFormField.id)
            .all()
        )

        return jsonify({
            'success': True,
            'categories': grouped,
            'custom_fields': [cf.to_dict() for cf in custom_fields]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@form_config_bp.route('/admin', methods=['GET'])
@admin_required
def get_all_form_config_admin():
    """
    Admin-only endpoint: Returns ALL options (active and inactive) and custom fields
    for administrative configuration management.
    """
    session = SessionLocal()
    try:
        options = (
            session.query(FormFieldOption)
            .order_by(FormFieldOption.category, FormFieldOption.display_order, FormFieldOption.id)
            .all()
        )
        custom_fields = (
            session.query(CustomFormField)
            .order_by(CustomFormField.display_order, CustomFormField.id)
            .all()
        )
        return jsonify({
            'success': True,
            'options': [opt.to_dict() for opt in options],
            'custom_fields': [cf.to_dict() for cf in custom_fields]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@form_config_bp.route('/options', methods=['POST'])
@admin_required
def add_option():
    """
    Admin-only: Adds a new option to a category.
    """
    data = request.get_json() or {}
    category = (data.get('category') or '').strip()
    value = (data.get('value') or '').strip()
    label = (data.get('label') or '').strip() or value
    is_active = bool(data.get('is_active', True))
    display_order = int(data.get('display_order', 0) or 0)

    if not category or not value:
        return jsonify({'success': False, 'error': 'Category and Value are required.'}), 400

    session = SessionLocal()
    try:
        # Check duplicate in same category
        existing = (
            session.query(FormFieldOption)
            .filter(FormFieldOption.category == category, FormFieldOption.value == value)
            .first()
        )
        if existing:
            # Reactivate if inactive
            existing.is_active = True
            existing.label = label
            session.commit()
            return jsonify({'success': True, 'message': 'Option reactivated.', 'option': existing.to_dict()}), 200

        new_opt = FormFieldOption(
            category=category,
            value=value,
            label=label,
            is_active=is_active,
            display_order=display_order
        )
        session.add(new_opt)
        session.commit()
        return jsonify({'success': True, 'message': 'Option added successfully.', 'option': new_opt.to_dict()}), 201
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@form_config_bp.route('/options/<int:option_id>', methods=['PUT', 'PATCH'])
@admin_required
def update_option(option_id):
    """
    Admin-only: Updates an option label, active status, or display order.
    """
    data = request.get_json() or {}
    session = SessionLocal()
    try:
        opt = session.query(FormFieldOption).filter(FormFieldOption.id == option_id).first()
        if not opt:
            return jsonify({'success': False, 'error': 'Option not found.'}), 404

        if 'label' in data:
            opt.label = data['label'].strip()
        if 'value' in data and data['value'].strip():
            opt.value = data['value'].strip()
        if 'is_active' in data:
            opt.is_active = bool(data['is_active'])
        if 'display_order' in data:
            opt.display_order = int(data['display_order'])

        session.commit()
        return jsonify({'success': True, 'message': 'Option updated successfully.', 'option': opt.to_dict()}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@form_config_bp.route('/options/<int:option_id>', methods=['DELETE'])
@admin_required
def delete_or_deactivate_option(option_id):
    """
    Admin-only: Safe soft-deactivates an option to preserve historical proposals.
    """
    session = SessionLocal()
    try:
        opt = session.query(FormFieldOption).filter(FormFieldOption.id == option_id).first()
        if not opt:
            return jsonify({'success': False, 'error': 'Option not found.'}), 404

        opt.is_active = False
        session.commit()
        return jsonify({'success': True, 'message': f"Option '{opt.value}' deactivated successfully.", 'option': opt.to_dict()}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@form_config_bp.route('/custom-fields', methods=['POST'])
@admin_required
def add_custom_field():
    """
    Admin-only: Adds a new custom field to the proposal form.
    """
    data = request.get_json() or {}
    field_name = (data.get('field_name') or '').strip().lower().replace(' ', '_')
    field_label = (data.get('field_label') or '').strip()
    field_type = (data.get('field_type') or 'text').strip().lower()
    options_json = data.get('options_json')
    is_required = bool(data.get('is_required', False))
    is_active = bool(data.get('is_active', True))
    display_order = int(data.get('display_order', 0) or 0)

    if not field_name or not field_label:
        return jsonify({'success': False, 'error': 'Field name and field label are required.'}), 400

    session = SessionLocal()
    try:
        existing = session.query(CustomFormField).filter(CustomFormField.field_name == field_name).first()
        if existing:
            return jsonify({'success': False, 'error': f"Custom field with identifier '{field_name}' already exists."}), 409

        cf = CustomFormField(
            field_name=field_name,
            field_label=field_label,
            field_type=field_type,
            options_json=options_json,
            is_required=is_required,
            is_active=is_active,
            display_order=display_order
        )
        session.add(cf)
        session.commit()
        return jsonify({'success': True, 'message': 'Custom field added successfully.', 'custom_field': cf.to_dict()}), 201
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@form_config_bp.route('/custom-fields/<int:field_id>', methods=['PUT', 'PATCH'])
@admin_required
def update_custom_field(field_id):
    """
    Admin-only: Updates custom field properties.
    """
    data = request.get_json() or {}
    session = SessionLocal()
    try:
        cf = session.query(CustomFormField).filter(CustomFormField.id == field_id).first()
        if not cf:
            return jsonify({'success': False, 'error': 'Custom field not found.'}), 404

        if 'field_label' in data:
            cf.field_label = data['field_label'].strip()
        if 'field_type' in data:
            cf.field_type = data['field_type'].strip().lower()
        if 'options_json' in data:
            cf.options_json = data['options_json']
        if 'is_required' in data:
            cf.is_required = bool(data['is_required'])
        if 'is_active' in data:
            cf.is_active = bool(data['is_active'])
        if 'display_order' in data:
            cf.display_order = int(data['display_order'])

        session.commit()
        return jsonify({'success': True, 'message': 'Custom field updated successfully.', 'custom_field': cf.to_dict()}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@form_config_bp.route('/custom-fields/<int:field_id>', methods=['DELETE'])
@admin_required
def delete_or_deactivate_custom_field(field_id):
    """
    Admin-only: Safe soft-deactivates custom field.
    """
    session = SessionLocal()
    try:
        cf = session.query(CustomFormField).filter(CustomFormField.id == field_id).first()
        if not cf:
            return jsonify({'success': False, 'error': 'Custom field not found.'}), 404

        cf.is_active = False
        session.commit()
        return jsonify({'success': True, 'message': f"Custom field '{cf.field_name}' deactivated successfully.", 'custom_field': cf.to_dict()}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
