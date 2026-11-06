import React, { useState, useEffect } from 'react';
import { X, Mail, Send, Paperclip, CheckCircle, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

export default function EmailComposeModal({ isOpen, onClose, proposal, authKey, defaultTo = '' }) {
  if (!isOpen || !proposal) return null;

  const [toInput, setToInput] = useState(defaultTo || proposal.faculty_email || '');
  const [ccInput, setCcInput] = useState('');
  const [subject, setSubject] = useState(`SAPC Course Proposal: ${proposal.course_title} (${proposal.proposal_id})`);
  const [message, setMessage] = useState(
    `Dear Colleague,\n\nPlease find attached the official ACAD-SAPC-01 course proposal for "${proposal.course_title}" (Proposal ID: ${proposal.proposal_id}) for your reference and review.\n\nRegards,\n${proposal.proposer_name}`
  );
  const [attachPdf, setAttachPdf] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [resultMessage, setResultMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    if (proposal) {
      setToInput(defaultTo || proposal.faculty_email || '');
      setSubject(`SAPC Course Proposal: ${proposal.course_title} (${proposal.proposal_id})`);
      setResultMessage(null);
      setErrorMessage(null);
    }
  }, [proposal, defaultTo]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!toInput.trim()) {
      setErrorMessage('Please provide at least one recipient email address.');
      return;
    }
    if (!message.trim()) {
      setErrorMessage('Please enter a message body.');
      return;
    }

    setIsSending(true);
    setErrorMessage(null);
    setResultMessage(null);

    try {
      const payload = {
        to: toInput,
        cc: ccInput,
        subject: subject.trim(),
        message: message.trim(),
        attach_pdf: attachPdf
      };

      const res = await api.sendCustomProposalEmail(proposal.proposal_id, payload, authKey);
      if (res.success) {
        setResultMessage(res.message || 'Email dispatched successfully.');
        setTimeout(() => {
          onClose();
        }, 1800);
      } else {
        setErrorMessage(res.error || 'Failed to dispatch email.');
      }
    } catch (err) {
      setErrorMessage(err.message || 'Failed to send email. Check network or server.');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={e => e.stopPropagation()} style={{ maxWidth: 640 }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ background: '#002147', color: '#c29b38', padding: 8, borderRadius: 6 }}>
              <Mail size={18} />
            </div>
            <div>
              <div className="modal-title" style={{ fontSize: 16 }}>
                Compose & Dispatch Proposal Email
              </div>
              <div style={{ fontSize: 12, color: '#64748b' }}>
                Proposal: {proposal.proposal_id} — {proposal.course_title}
              </div>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} disabled={isSending}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSend}>
          <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {resultMessage && (
              <div style={{ background: '#dcfce7', border: '1px solid #86efac', color: '#166534', padding: 12, borderRadius: 6, display: 'flex', alignItems: 'center', gap: 8, fontSize: 13.5 }}>
                <CheckCircle size={18} />
                <span>{resultMessage}</span>
              </div>
            )}

            {errorMessage && (
              <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', color: '#991b1b', padding: 12, borderRadius: 6, display: 'flex', alignItems: 'center', gap: 8, fontSize: 13.5 }}>
                <AlertTriangle size={18} />
                <span>{errorMessage}</span>
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>
                To Recipients <span style={{ color: '#dc2626' }}>*</span> (comma-separated):
              </label>
              <input
                type="text"
                className="form-control"
                placeholder="faculty@iitgn.ac.in, hod@iitgn.ac.in"
                value={toInput}
                onChange={e => setToInput(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>
                CC Recipients (optional, comma-separated):
              </label>
              <input
                type="text"
                className="form-control"
                placeholder="dean.academic@iitgn.ac.in, colleagues@iitgn.ac.in"
                value={ccInput}
                onChange={e => setCcInput(e.target.value)}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>
                Subject Line:
              </label>
              <input
                type="text"
                className="form-control"
                value={subject}
                onChange={e => setSubject(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>
                Message Body:
              </label>
              <textarea
                className="form-control"
                rows={5}
                value={message}
                onChange={e => setMessage(e.target.value)}
                required
              />
            </div>

            <div style={{ background: '#f8fafc', padding: '10px 14px', borderRadius: 6, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Paperclip size={16} color="#002147" />
                <span style={{ fontSize: 13, fontWeight: 600, color: '#334155' }}>
                  Attach official ACAD-SAPC-01 PDF (<code>{proposal.proposal_id}.pdf</code>)
                </span>
              </div>
              <input
                type="checkbox"
                id="attachPdfCheck"
                checked={attachPdf}
                onChange={e => setAttachPdf(e.target.checked)}
                style={{ width: 17, height: 17, cursor: 'pointer' }}
              />
            </div>
          </div>

          <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 11.5, color: '#64748b' }}>
              Dispatched with institutional audit tracking in outbox.
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" className="btn btn-secondary btn-sm" onClick={onClose} disabled={isSending}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary btn-sm" disabled={isSending}>
                {isSending ? (
                  <span>Sending...</span>
                ) : (
                  <>
                    <Send size={14} />
                    <span>Send Email</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
