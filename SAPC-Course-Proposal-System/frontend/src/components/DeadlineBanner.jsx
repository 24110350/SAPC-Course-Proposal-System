import React from 'react';
import { Calendar, AlertCircle, CheckCircle, Clock } from 'lucide-react';

export default function DeadlineBanner({ deadlineData, onConfigureDeadline, isAdmin }) {
  if (!deadlineData) return null;

  const isOpen = deadlineData.is_open;
  const deadlineStr = deadlineData.submission_deadline
    ? new Date(deadlineData.submission_deadline).toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    : 'Not configured';

  const startStr = deadlineData.submission_start
    ? new Date(deadlineData.submission_start).toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    : 'Not configured';

  // Compute remaining time in hours or days
  const remainingSecs = deadlineData.time_remaining_seconds || 0;
  const daysRemaining = Math.floor(remainingSecs / 86400);
  const hoursRemaining = Math.floor((remainingSecs % 86400) / 3600);

  return (
    <div className={`deadline-banner ${isOpen ? 'open' : 'closed'}`}>
      <div className="banner-left">
        <div style={{ marginTop: 2 }}>
          {isOpen ? (
            <Clock size={24} color="#15803d" />
          ) : (
            <AlertCircle size={24} color="#b91c1c" />
          )}
        </div>
        <div>
          <div className="banner-title">
            {isOpen
              ? `Course Proposal Window is Open (Closes: ${deadlineStr})`
              : 'Course Proposal Submissions are Currently Closed'}
          </div>
          <div className="banner-sub">
            {isOpen ? (
              <span>
                Submission period: <strong>{startStr}</strong> until <strong>{deadlineStr}</strong>
                {daysRemaining > 0 && ` (${daysRemaining} days and ${hoursRemaining} hours remaining)`}
              </span>
            ) : (
              <span>{deadlineData.status_message}</span>
            )}
            {deadlineData.announcement_message && (
              <div style={{ marginTop: 4, fontStyle: 'italic', color: '#1e293b' }}>
                Note: {deadlineData.announcement_message}
              </div>
            )}
          </div>
        </div>
      </div>

      {isAdmin && (
        <button
          className="btn btn-secondary btn-sm"
          onClick={onConfigureDeadline}
          style={{ whiteSpace: 'nowrap' }}
        >
          <Calendar size={14} />
          <span>Adjust Deadline</span>
        </button>
      )}
    </div>
  );
}
