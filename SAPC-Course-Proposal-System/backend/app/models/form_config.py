from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from .proposal import Base

class FormFieldOption(Base):
    __tablename__ = 'form_field_options'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)
    # categories: 'course_type', 'course_level', 'course_duration', 'expected_frequency',
    # 'elective_basket_btech', 'discipline_elective_btech', 'minors',
    # 'discipline_elective_msc', 'courses_discipline_mtech', 'discipline_elective_mdes'
    value = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'value': self.value,
            'label': self.label,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class CustomFormField(Base):
    __tablename__ = 'custom_form_fields'

    id = Column(Integer, primary_key=True, autoincrement=True)
    field_name = Column(String(100), unique=True, nullable=False)
    field_label = Column(String(255), nullable=False)
    field_type = Column(String(50), nullable=False, default='text') # 'text', 'textarea', 'number', 'select'
    options_json = Column(Text, nullable=True) # JSON list of string options if field_type == 'select'
    is_required = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'field_name': self.field_name,
            'field_label': self.field_label,
            'field_type': self.field_type,
            'options_json': self.options_json,
            'is_required': self.is_required,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
