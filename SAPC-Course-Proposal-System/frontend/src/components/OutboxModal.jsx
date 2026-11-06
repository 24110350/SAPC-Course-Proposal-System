import React, { useState, useEffect } from 'react';
import { X, Mail, CheckCircle, Clock, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function OutboxModal({ isOpen, onClose }) {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchOutbox = async () => {
    setLoading(true);
    const token = localStorage.getItem('sapc_token');
    if (!token) return;

    try {
      const res = await api.getEmailOutbox(token);
      if (res.success) {
        setEmails(res.emails || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchOutbox();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={e => e.stopPropagation()} style={{ maxWidth: 740 }}>
        <div className="modal-header">
          <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Mail size={18} />
            <span>Outbound Automated Email Notifications Log</span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div style={{ fontSize: 13, color: '#64748b' }}>
              Showing automated notifications logged by the notification service ({emails.length} records)
            </div>
            <button className="btn btn-secondary btn-sm" onClick={fetchOutbox}>
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 30, color: '#64748b' }}>
              Loading outbound notification logs...
            </div>
          ) : emails.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 30, color: '#64748b' }}>
              No notification emails dispatched yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {emails.map((m, idx) => (
                <div key={idx} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontWeight: 700, color: '#002147', fontSize: 13.5 }}>
                      {m.subject}
                    </span>
                    <span style={{ fontSize: 11.5, color: '#64748b' }}>
                      {new Date(m.timestamp).toLocaleString('en-IN')}
                    </span>
                  </div>

                  <div style={{ fontSize: 12, color: '#334155', marginBottom: 8 }}>
                    <strong>To:</strong> {m.recipient} | <strong>Proposal ID:</strong> {m.proposal_id} | <strong>Status:</strong> {m.status}
                  </div>

                  <pre style={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 6, padding: 10, fontSize: 11.5, whiteSpace: 'pre-wrap', fontFamily: 'monospace', color: '#1e293b' }}>
                    {m.body}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
