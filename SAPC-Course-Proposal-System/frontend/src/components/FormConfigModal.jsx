import React, { useState, useEffect, useCallback } from 'react';
import { X, Settings, Plus, ToggleLeft, ToggleRight, Check, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

const CATEGORIES = [
  { id: 'course_type', label: 'Course Types' },
  { id: 'course_level', label: 'Course Levels' },
  { id: 'course_duration', label: 'Durations' },
  { id: 'expected_frequency', label: 'Offering Frequencies' },
  { id: 'elective_basket_btech', label: 'BTech Baskets' },
  { id: 'discipline_elective_btech', label: 'BTech Electives' },
  { id: 'minors', label: 'Minors' },
  { id: 'discipline_elective_msc', label: 'MSc Electives' },
  { id: 'courses_discipline_mtech', label: 'MTech Disciplines' },
  { id: 'discipline_elective_mdes', label: 'MDes Electives' },
  { id: 'custom_fields', label: '★ Custom Fields' }
];

export default function FormConfigModal({ isOpen, onClose, token, onConfigChanged }) {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState('course_type');
  const [allOptions, setAllOptions] = useState([]);
  const [customFields, setCustomFields] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New option state
  const [newValue, setNewValue] = useState('');
  const [newLabel, setNewLabel] = useState('');

  // New custom field state
  const [newFieldName, setNewFieldName] = useState('');
  const [newFieldLabel, setNewFieldLabel] = useState('');
  const [newFieldType, setNewFieldType] = useState('text');
  const [newFieldRequired, setNewFieldRequired] = useState(false);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getFormConfigAdmin(token);
      if (res.success) {
        setAllOptions(res.options || []);
        setCustomFields(res.custom_fields || []);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch form configuration.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (isOpen) {
      fetchConfig();
      setSuccessMsg(null);
      setError(null);
    }
  }, [isOpen, fetchConfig]);

  const handleAddOption = async (e) => {
    e.preventDefault();
    if (!newValue.trim()) return;
    setActionLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.addFormOption({
        category: activeTab,
        value: newValue.trim(),
        label: newLabel.trim() || newValue.trim(),
        is_active: true
      }, token);
      if (res.success) {
        setSuccessMsg(`Option '${newValue}' added successfully.`);
        setNewValue('');
        setNewLabel('');
        await fetchConfig();
        if (onConfigChanged) onConfigChanged();
      }
    } catch (err) {
      setError(err.message || 'Failed to add option.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleOption = async (opt) => {
    setActionLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.updateFormOption(opt.id, { is_active: !opt.is_active }, token);
      if (res.success) {
        setSuccessMsg(`Option '${opt.value}' ${!opt.is_active ? 'activated' : 'deactivated'}.`);
        await fetchConfig();
        if (onConfigChanged) onConfigChanged();
      }
    } catch (err) {
      setError(err.message || 'Failed to update option.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddCustomField = async (e) => {
    e.preventDefault();
    if (!newFieldName.trim() || !newFieldLabel.trim()) return;
    setActionLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.addCustomField({
        field_name: newFieldName.trim(),
        field_label: newFieldLabel.trim(),
        field_type: newFieldType,
        is_required: newFieldRequired,
        is_active: true
      }, token);
      if (res.success) {
        setSuccessMsg(`Custom field '${newFieldLabel}' created successfully.`);
        setNewFieldName('');
        setNewFieldLabel('');
        setNewFieldRequired(false);
        await fetchConfig();
        if (onConfigChanged) onConfigChanged();
      }
    } catch (err) {
      setError(err.message || 'Failed to add custom field.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleCustomField = async (cf) => {
    setActionLoading(true);
    setError(null);
    try {
      const res = await api.updateCustomField(cf.id, { is_active: !cf.is_active }, token);
      if (res.success) {
        setSuccessMsg(`Custom field '${cf.field_label}' ${!cf.is_active ? 'activated' : 'deactivated'}.`);
        await fetchConfig();
        if (onConfigChanged) onConfigChanged();
      }
    } catch (err) {
      setError(err.message || 'Failed to update custom field.');
    } finally {
      setActionLoading(false);
    }
  };

  const currentCategoryOptions = allOptions.filter(o => o.category === activeTab);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={e => e.stopPropagation()} style={{ maxWidth: 880, maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ background: '#002147', color: '#c29b38', padding: 8, borderRadius: 6 }}>
              <Settings size={18} />
            </div>
            <div>
              <div className="modal-title" style={{ fontSize: 16 }}>
                Dynamic Form Configuration (Academic Office)
              </div>
              <div style={{ fontSize: 12, color: '#64748b' }}>
                Add, customize, and deactivate form options and custom fields in real-time
              </div>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Tab Selector */}
        <div style={{ display: 'flex', gap: 4, padding: '10px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', overflowX: 'auto' }}>
          {CATEGORIES.map(cat => (
            <button
              key={cat.id}
              onClick={() => { setActiveTab(cat.id); setSuccessMsg(null); setError(null); }}
              style={{
                padding: '6px 12px',
                borderRadius: 6,
                fontSize: 12,
                fontWeight: activeTab === cat.id ? 700 : 500,
                background: activeTab === cat.id ? '#002147' : 'transparent',
                color: activeTab === cat.id ? '#ffffff' : '#475569',
                border: 'none',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Feedback Alerts */}
        {successMsg && (
          <div style={{ background: '#dcfce7', borderLeft: '4px solid #16a34a', color: '#166534', padding: '8px 16px', fontSize: 12.5 }}>
            {successMsg}
          </div>
        )}
        {error && (
          <div style={{ background: '#fee2e2', borderLeft: '4px solid #dc2626', color: '#991b1b', padding: '8px 16px', fontSize: 12.5 }}>
            {error}
          </div>
        )}

        <div className="modal-body" style={{ flex: 1, overflowY: 'auto', padding: 18 }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>
              <RefreshCw size={24} className="spin" style={{ marginBottom: 8 }} />
              <div>Loading configuration...</div>
            </div>
          ) : activeTab === 'custom_fields' ? (
            /* Custom Fields Management */
            <div>
              <div style={{ background: '#f1f5f9', padding: 14, borderRadius: 8, marginBottom: 16 }}>
                <div style={{ fontWeight: 700, fontSize: 13, color: '#002147', marginBottom: 8 }}>
                  Create New Custom Field for Proposal Form
                </div>
                <form onSubmit={handleAddCustomField} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 120px auto', gap: 10, alignItems: 'center' }}>
                  <input
                    type="text"
                    className="form-control form-control-sm"
                    placeholder="Field Identifier (e.g. lab_equipment)"
                    value={newFieldName}
                    onChange={e => setNewFieldName(e.target.value)}
                    required
                  />
                  <input
                    type="text"
                    className="form-control form-control-sm"
                    placeholder="Display Label (e.g. Lab Equipment Needed)"
                    value={newFieldLabel}
                    onChange={e => setNewFieldLabel(e.target.value)}
                    required
                  />
                  <select
                    className="form-control form-control-sm"
                    value={newFieldType}
                    onChange={e => setNewFieldType(e.target.value)}
                  >
                    <option value="text">Text</option>
                    <option value="textarea">Textarea</option>
                    <option value="number">Number</option>
                  </select>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={actionLoading}>
                    <Plus size={14} />
                    <span>Add Field</span>
                  </button>
                </form>
              </div>

              <div style={{ fontWeight: 700, fontSize: 13, color: '#002147', marginBottom: 8 }}>
                Configured Custom Fields ({customFields.length})
              </div>
              {customFields.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 24, color: '#94a3b8', fontSize: 13 }}>
                  No custom fields configured yet. Add fields above to dynamically expand the proposal form.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {customFields.map(cf => (
                    <div
                      key={cf.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '10px 14px',
                        background: cf.is_active ? '#ffffff' : '#f8fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: 6,
                        opacity: cf.is_active ? 1 : 0.65
                      }}
                    >
                      <div>
                        <strong>{cf.field_label}</strong>{' '}
                        <code style={{ fontSize: 11, color: '#64748b' }}>({cf.field_name})</code>{' '}
                        <span className="badge" style={{ background: '#f1f5f9', color: '#475569', fontSize: 11 }}>
                          Type: {cf.field_type}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleToggleCustomField(cf)}
                        className={`btn btn-sm ${cf.is_active ? 'btn-secondary' : 'btn-primary'}`}
                        disabled={actionLoading}
                        style={{ fontSize: 11.5 }}
                      >
                        {cf.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Category Options Management */
            <div>
              {/* Add Option Form */}
              <div style={{ background: '#f1f5f9', padding: 14, borderRadius: 8, marginBottom: 16 }}>
                <div style={{ fontWeight: 700, fontSize: 13, color: '#002147', marginBottom: 8 }}>
                  Add Option to {CATEGORIES.find(c => c.id === activeTab)?.label}
                </div>
                <form onSubmit={handleAddOption} style={{ display: 'grid', gridTemplateColumns: '150px 1fr auto', gap: 10, alignItems: 'center' }}>
                  <input
                    type="text"
                    className="form-control form-control-sm"
                    placeholder="Value (e.g. CS / 1 Quad)"
                    value={newValue}
                    onChange={e => setNewValue(e.target.value)}
                    required
                  />
                  <input
                    type="text"
                    className="form-control form-control-sm"
                    placeholder="Full Display Label (e.g. Computer Science & Engg)"
                    value={newLabel}
                    onChange={e => setNewLabel(e.target.value)}
                  />
                  <button type="submit" className="btn btn-primary btn-sm" disabled={actionLoading}>
                    <Plus size={14} />
                    <span>Add Option</span>
                  </button>
                </form>
              </div>

              {/* Options Table */}
              <div style={{ fontWeight: 700, fontSize: 13, color: '#002147', marginBottom: 8 }}>
                Active & Inactive Options ({currentCategoryOptions.length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {currentCategoryOptions.map(opt => (
                  <div
                    key={opt.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      background: opt.is_active ? '#ffffff' : '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: 6,
                      opacity: opt.is_active ? 1 : 0.65
                    }}
                  >
                    <div>
                      <strong style={{ color: '#002147' }}>{opt.value}</strong> —{' '}
                      <span style={{ color: '#475569', fontSize: 13 }}>{opt.label}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span className={`badge ${opt.is_active ? 'badge-approved' : 'badge-rejected'}`} style={{ fontSize: 10.5 }}>
                        {opt.is_active ? 'Active in Form' : 'Deactivated'}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleToggleOption(opt)}
                        className={`btn btn-sm ${opt.is_active ? 'btn-secondary' : 'btn-primary'}`}
                        disabled={actionLoading}
                        style={{ fontSize: 11 }}
                      >
                        {opt.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 11.5, color: '#64748b' }}>
            Note: Deactivating an option preserves historical proposals with that value while hiding it from future submissions.
          </span>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
