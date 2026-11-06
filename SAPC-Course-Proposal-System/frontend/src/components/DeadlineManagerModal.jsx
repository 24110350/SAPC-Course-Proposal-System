import React, { useState, useEffect } from 'react';
import { X, Calendar, Clock, Save, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

export default function DeadlineManagerModal({ isOpen, onClose, currentDeadline, onDeadlineUpdated }) {
  const [formData, setFormData] = useState({
    submission_start: '',
    submission_deadline: '',
    is_active: true,
    announcement_message: ''
  });
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    if (currentDeadline) {
      // Format ISO string to YYYY-MM-DDTHH:mm for datetime-local input
      const formatDT = (isoStr) => {
        if (!isoStr) return '';
        const d = new Date(isoStr);
        const pad = (n) => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
      };

      setFormData({
        submission_start: formatDT(currentDeadline.submission_start),
        submission_deadline: formatDT(currentDeadline.submission_deadline),
        is_active: currentDeadline.is_active !== false,
        announcement_message: currentDeadline.announcement_message || ''
      });
    }
  }, [currentDeadline, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);

    const token = localStorage.getItem('sapc_token');
    if (!token) {
      setFeedback({ type: 'error', message: 'Admin authentication required.' });
      setIsSaving(false);
      return;
    }

    try {
      const payload = {
        submission_start: new Date(formData.submission_start).toISOString(),
        submission_deadline: new Date(formData.submission_deadline).toISOString(),
        is_active: formData.is_active,
        announcement_message: formData.announcement_message
      };

      const res = await api.updateDeadline(payload, token);
      if (res.success) {
        setFeedback({ type: 'success', message: 'Deadline settings updated successfully!' });
        if (onDeadlineUpdated) onDeadlineUpdated(res.deadline);
        setTimeout(() => {
          onClose();
        }, 1200);
      }
    } catch (err) {
      setFeedback({ type: 'error', message: err.message || 'Failed to update deadline.' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={e => e.stopPropagation()} style={{ maxWidth: 560 }}>
        <div className="modal-header">
          <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Calendar size={18} />
            <span>Configure Course Proposal Submission Window</span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {feedback && (
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: 6,
                  marginBottom: 16,
                  fontSize: 13,
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  backgroundColor: feedback.type === 'success' ? '#dcfce7' : '#fee2e2',
                  color: feedback.type === 'success' ? '#15803d' : '#b91c1c'
                }}
              >
                {feedback.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                <span>{feedback.message}</span>
              </div>
            )}

            <p style={{ fontSize: 13, color: '#64748b', marginBottom: 18 }}>
              Configure the active submission period for course proposals. The Flask backend strictly enforces these boundary timestamps.
            </p>

            {/* Start Date */}
            <div className="form-group">
              <label className="form-label">
                <span>Submission Window Opens <span className="req">*</span></span>
              </label>
              <input
                type="datetime-local"
                className="form-control"
                value={formData.submission_start}
                onChange={e => setFormData({ ...formData, submission_start: e.target.value })}
                required
              />
            </div>

            {/* Deadline Date */}
            <div className="form-group">
              <label className="form-label">
                <span>Submission Window Closes (Deadline) <span className="req">*</span></span>
              </label>
              <input
                type="datetime-local"
                className="form-control"
                value={formData.submission_deadline}
                onChange={e => setFormData({ ...formData, submission_deadline: e.target.value })}
                required
              />
              <span className="input-hint">
                Proposals submitted after this exact timestamp will be automatically rejected by the server.
              </span>
            </div>

            {/* Active Switch */}
            <div className="form-group" style={{ marginTop: 10 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13.5, fontWeight: 600 }}>
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
                  style={{ width: 18, height: 18 }}
                />
                <span>Enable Proposal Submissions (Active)</span>
              </label>
              <span className="input-hint" style={{ marginLeft: 28 }}>
                Unchecking this will immediately suspend submissions regardless of the deadline date.
              </span>
            </div>

            {/* Announcement Message */}
            <div className="form-group" style={{ marginTop: 14 }}>
              <label className="form-label">
                <span>Academic Office Announcement / Notice Banner</span>
              </label>
              <textarea
                className="form-control"
                rows={2}
                placeholder="e.g. Submissions for upcoming semester are open until 15 October..."
                value={formData.announcement_message}
                onChange={e => setFormData({ ...formData, announcement_message: e.target.value })}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary btn-sm" disabled={isSaving}>
              <Save size={14} />
              <span>{isSaving ? 'Saving...' : 'Save Configuration'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
