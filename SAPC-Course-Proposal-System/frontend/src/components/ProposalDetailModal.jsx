import React, { useState, useEffect } from 'react';
import {
  X, Download, ExternalLink, Calendar, User, Clock, FileText,
  CheckCircle, AlertTriangle, Mail, Edit3, History, Shield, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import { STATUS_OPTIONS } from '../constants/sapcOptions';
import EmailComposeModal from './EmailComposeModal';

export default function ProposalDetailModal({
  proposalId,
  onClose,
  currentUser,
  onStatusUpdated,
  onEditProposal
}) {
  const [proposal, setProposal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Status update within modal
  const [selectedStatus, setSelectedStatus] = useState('');
  const [statusRemarks, setStatusRemarks] = useState('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  // Course modification history (Requirement 7)
  const [courseHistory, setCourseHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Proposal edit history (Requirement 2)
  const [editHistory, setEditHistory] = useState([]);

  // Compose email modal (Requirement 3)
  const [isComposeEmailOpen, setIsComposeEmailOpen] = useState(false);

  // Resending security email
  const [isResendingSecurity, setIsResendingSecurity] = useState(false);
  const [resendFeedback, setResendFeedback] = useState(null);

  useEffect(() => {
    if (!proposalId) return;

    const fetchDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getProposalDetail(proposalId);
        if (res.success && res.proposal) {
          setProposal(res.proposal);
          setSelectedStatus(res.proposal.status);
          setEditHistory(res.proposal.edit_history || []);
        } else {
          setError('Proposal not found');
        }
      } catch (err) {
        setError(err.message || 'Failed to fetch proposal details');
      } finally {
        setLoading(false);
      }
    };

    const fetchHistory = async () => {
      setLoadingHistory(true);
      try {
        const res = await api.getCourseHistory(proposalId);
        if (res.success && res.history) {
          setCourseHistory(res.history);
        }
      } catch (err) {
        console.warn('Could not load course history:', err);
      } finally {
        setLoadingHistory(false);
      }
    };

    fetchDetail();
    fetchHistory();
    setResendFeedback(null);
  }, [proposalId]);

  const handleStatusSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('sapc_token');
    if (!token) {
      alert('You must be logged in as an Academic Office administrator to change status.');
      return;
    }

    setIsUpdatingStatus(true);
    try {
      const res = await api.updateProposalStatus(proposalId, selectedStatus, statusRemarks, token);
      if (res.success) {
        setProposal(res.proposal);
        setStatusRemarks('');
        if (onStatusUpdated) onStatusUpdated();
        alert(res.message || `Status updated to '${selectedStatus}' successfully.`);
      }
    } catch (err) {
      alert(err.message || 'Failed to update status');
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleResendSecurity = async () => {
    const token = localStorage.getItem('sapc_token');
    if (!token) return;
    setIsResendingSecurity(true);
    setResendFeedback(null);
    try {
      const res = await api.resendNotificationEmail(proposalId, token, 'security');
      if (res.success) {
        setResendFeedback('Security department notification successfully resent!');
        // Refresh proposal
        const pRes = await api.getProposalDetail(proposalId);
        if (pRes.success) setProposal(pRes.proposal);
      } else {
        setResendFeedback(`Resend failed: ${res.error || 'Server error'}`);
      }
    } catch (e) {
      setResendFeedback(`Resend failed: ${e.message}`);
    } finally {
      setIsResendingSecurity(false);
    }
  };

  if (!proposalId) return null;

  let parsedCustomFields = {};
  if (proposal?.custom_fields_data) {
    try {
      parsedCustomFields = typeof proposal.custom_fields_data === 'string'
        ? JSON.parse(proposal.custom_fields_data)
        : proposal.custom_fields_data;
    } catch (e) {
      parsedCustomFields = {};
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={e => e.stopPropagation()} style={{ maxWidth: 900, maxHeight: '92vh', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <div style={{ fontSize: 12, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              IIT Gandhinagar — ACAD-SAPC-01
            </div>
            <div className="modal-title">
              Proposal Details: {proposal?.proposal_id || proposalId}
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body" style={{ flex: 1, overflowY: 'auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>
              Loading proposal details...
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: 30, color: '#b91c1c' }}>
              <AlertTriangle size={24} style={{ marginBottom: 6 }} />
              <div>{error}</div>
            </div>
          ) : proposal ? (
            <div>
              {/* Top Banner with Title, SAPC Number, and Badges */}
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 18, marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10 }}>
                  <div>
                    <h3 style={{ fontSize: 18, fontWeight: 800, color: '#002147', marginBottom: 6 }}>
                      {proposal.course_title}
                    </h3>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                      <span className="badge badge-approved" style={{ fontSize: 11 }}>
                        {proposal.course_type}
                      </span>
                      <span className="badge badge-review" style={{ fontSize: 11 }}>
                        Level {proposal.course_level}
                        {proposal.course_level_secondary ? ` & Level ${proposal.course_level_secondary}` : ''}
                      </span>
                      <span className="badge" style={{ background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', fontSize: 11 }}>
                        L-T-P-C: {proposal.course_l_t_p_c} ({proposal.credits} Credits)
                      </span>
                      {proposal.is_modification ? (
                        <span className="badge badge-rejected" style={{ fontSize: 11 }}>
                          Modification (Code: {proposal.existing_course_code || 'N/A'})
                        </span>
                      ) : (
                        <span className="badge badge-approved" style={{ fontSize: 11 }}>
                          New Course
                        </span>
                      )}
                      {proposal.sapc_number && (
                        <span className="badge" style={{ background: '#002147', color: '#ffffff', fontSize: 11 }}>
                          SAPC No: {proposal.sapc_number}
                        </span>
                      )}
                      {proposal.approval_date && (
                        <span className="badge badge-approved" style={{ fontSize: 11 }}>
                          Approved on: {String(proposal.approval_date || '').slice(0, 10)}
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 12, color: '#64748b' }}>Current Status:</div>
                    <div style={{ marginTop: 2 }}>
                      <span className="badge badge-pending" style={{ fontSize: 13, padding: '4px 10px' }}>
                        {proposal.status}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Form Grid Sections */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                {/* Proposer Info */}
                <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 6, padding: 14 }}>
                  <div style={{ fontWeight: 700, color: '#002147', fontSize: 13, borderBottom: '1px solid #f1f5f9', paddingBottom: 6, marginBottom: 8 }}>
                    Proposer & Instructors
                  </div>
                  <div style={{ fontSize: 12.5, marginBottom: 6 }}>
                    <strong>Name of Proposer:</strong> {proposal.proposer_name}
                  </div>
                  <div style={{ fontSize: 12.5, marginBottom: 6 }}>
                    <strong>Potential Instructor(s):</strong> {proposal.potential_instructors}
                  </div>
                  <div style={{ fontSize: 12.5, marginBottom: 6 }}>
                    <strong>Faculty Email:</strong> {proposal.faculty_email}
                  </div>
                  {proposal.additional_recipients && proposal.additional_recipients.length > 0 && (
                    <div style={{ fontSize: 12, marginBottom: 6, paddingTop: 6, borderTop: '1px dashed #e2e8f0' }}>
                      <strong>Additional Recipients (CC):</strong>
                      <div style={{ marginTop: 4, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {proposal.additional_recipients_detail && proposal.additional_recipients_detail.length > 0 ? (
                          proposal.additional_recipients_detail.map((r, i) => (
                            <span key={i} className={`badge ${r.delivery_status === 'Sent' ? 'badge-approved' : r.delivery_status === 'Failed' ? 'badge-rejected' : 'badge-pending'}`} style={{ fontSize: 11 }}>
                              {r.email} ({r.delivery_status})
                            </span>
                          ))
                        ) : (
                          proposal.additional_recipients.map((em, i) => (
                            <span key={i} className="badge badge-pending" style={{ fontSize: 11 }}>
                              {em}
                            </span>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                  <div style={{ fontSize: 12.5, marginBottom: 6 }}>
                    <strong>Submitted On:</strong> {new Date(proposal.submission_date).toLocaleString('en-IN')}
                  </div>

                  {/* Security Department Notification Status (Requirement 6) */}
                  <div style={{ fontSize: 12, paddingTop: 6, borderTop: '1px dashed #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <Shield size={13} style={{ display: 'inline', marginRight: 4, color: '#002147' }} />
                      <strong>Security Dept:</strong>{' '}
                      <span className={`badge ${proposal.security_email_status === 'Sent' ? 'badge-approved' : 'badge-pending'}`} style={{ fontSize: 10.5 }}>
                        {proposal.security_email_status || 'Pending'}
                      </span>
                    </div>
                    {currentUser && (
                      <button
                        onClick={handleResendSecurity}
                        disabled={isResendingSecurity}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '2px 8px', fontSize: 11 }}
                      >
                        {isResendingSecurity ? 'Sending...' : 'Resend'}
                      </button>
                    )}
                  </div>
                  {resendFeedback && (
                    <div style={{ fontSize: 11, color: '#15803d', marginTop: 4 }}>{resendFeedback}</div>
                  )}
                </div>

                {/* Offering Info */}
                <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 6, padding: 14 }}>
                  <div style={{ fontWeight: 700, color: '#002147', fontSize: 13, borderBottom: '1px solid #f1f5f9', paddingBottom: 6, marginBottom: 8 }}>
                    Duration, Electives & Minors
                  </div>
                  <div style={{ fontSize: 12.5, marginBottom: 6 }}>
                    <strong>Course Duration:</strong> {proposal.course_duration}
                  </div>
                  <div style={{ fontSize: 12.5, marginBottom: 6 }}>
                    <strong>Frequency of Offering:</strong> {proposal.expected_frequency}
                    {proposal.expected_frequency_other ? ` (${proposal.expected_frequency_other})` : ''}
                  </div>
                  <div style={{ fontSize: 12.5, marginBottom: 6 }}>
                    <strong>BTech Elective Basket:</strong> {proposal.elective_basket_btech || 'None'}
                  </div>
                  <div style={{ fontSize: 12.5, marginBottom: 6 }}>
                    <strong>Discipline Elective (BTech):</strong> {proposal.discipline_elective_btech || 'None'}
                  </div>
                  <div style={{ fontSize: 12.5, marginBottom: 6 }}>
                    <strong>Minor(s):</strong> {proposal.minors || 'None'}
                    {proposal.minor_basket_thematic_area ? ` [Thematic Area: ${proposal.minor_basket_thematic_area}]` : ''}
                  </div>

                  {/* Requirement 4: Reason for Adding the Course as a Minor */}
                  {proposal.minor_reason && (
                    <div style={{ fontSize: 12, marginTop: 8, padding: '8px 10px', background: '#f8fafc', borderLeft: '3px solid #002147', borderRadius: '0 4px 4px 0' }}>
                      <strong style={{ color: '#002147' }}>Reason for Adding as Minor:</strong>
                      <div style={{ color: '#334155', marginTop: 2, whiteSpace: 'pre-wrap' }}>
                        {proposal.minor_reason}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Dynamic Custom Fields (Requirement 5) */}
              {Object.keys(parsedCustomFields).length > 0 && (
                <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 6, padding: 14, marginBottom: 20 }}>
                  <div style={{ fontWeight: 700, color: '#002147', fontSize: 13, borderBottom: '1px solid #f1f5f9', paddingBottom: 6, marginBottom: 8 }}>
                    Additional Institutional Custom Fields
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                    {Object.entries(parsedCustomFields).map(([k, v]) => (
                      <div key={k} style={{ fontSize: 12.5 }}>
                        <strong style={{ textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}:</strong>{' '}
                        <span>{String(v || '—')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Syllabus & Course Content Blocks */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontWeight: 700, color: '#002147', fontSize: 13, marginBottom: 4 }}>
                  Course Contents (separated by semicolons):
                </div>
                <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0', fontSize: 12.5, whiteSpace: 'pre-wrap' }}>
                  {proposal.course_contents}
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <div style={{ fontWeight: 700, color: '#002147', fontSize: 13, marginBottom: 4 }}>
                  Texts and References (MLA/APA format):
                </div>
                <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0', fontSize: 12.5, whiteSpace: 'pre-wrap' }}>
                  {proposal.texts_and_references}
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <div style={{ fontWeight: 700, color: '#002147', fontSize: 13, marginBottom: 4 }}>
                  Learning Outcomes:
                </div>
                <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0', fontSize: 12.5, whiteSpace: 'pre-wrap' }}>
                  {proposal.learning_outcomes}
                </div>
              </div>

              {proposal.overlap_courses && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 700, color: '#002147', fontSize: 13, marginBottom: 4 }}>
                    Overlap with Other Approved Courses:
                  </div>
                  <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid #e2e8f0', fontSize: 12.5 }}>
                    {proposal.overlap_courses}
                  </div>
                </div>
              )}

              {/* Course Modification History Timeline (Requirement 7) */}
              {courseHistory.length > 1 && (
                <div style={{ marginTop: 24, borderTop: '2px solid #e2e8f0', paddingTop: 16, marginBottom: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <History size={16} color="#002147" />
                    <span style={{ fontWeight: 800, color: '#002147', fontSize: 14 }}>
                      Chronological Course Modification History ({courseHistory.length} versions)
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 12 }}>
                    Linked via existing course code <code>{proposal.existing_course_code || 'N/A'}</code> and title. Historical versions are immutably archived.
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {courseHistory.map((ver, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: ver.is_current ? '#eff6ff' : '#f8fafc',
                          border: ver.is_current ? '1.5px solid #3b82f6' : '1px solid #e2e8f0',
                          borderRadius: 6,
                          padding: 12,
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          flexWrap: 'wrap',
                          gap: 10
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                            <strong style={{ color: '#002147', fontSize: 13 }}>{ver.course_title}</strong>
                            <code style={{ fontSize: 11 }}>{ver.proposal_id}</code>
                            {ver.is_current && (
                              <span className="badge badge-approved" style={{ fontSize: 10.5 }}>Current Version</span>
                            )}
                            <span className={`badge ${ver.is_approved ? 'badge-approved' : 'badge-pending'}`} style={{ fontSize: 10.5 }}>
                              {ver.status}
                            </span>
                          </div>
                          <div style={{ fontSize: 11.5, color: '#475569' }}>
                            Submitted by <strong>{ver.proposer_name}</strong> on {new Date(ver.submission_date).toLocaleDateString('en-IN')}
                            {ver.existing_course_code ? ` • Code: ${ver.existing_course_code}` : ''}
                            {ver.sapc_number ? ` • SAPC: ${ver.sapc_number}` : ''}
                          </div>
                        </div>

                        <div style={{ display: 'flex', gap: 6 }}>
                          <a
                            href={ver.pdf_url}
                            className="btn btn-secondary btn-sm"
                            download={`${ver.proposal_id}.pdf`}
                            style={{ padding: '4px 10px', fontSize: 11.5 }}
                          >
                            <Download size={12} />
                            <span>Download PDF</span>
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Proposal Edit History (Requirement 2) */}
              {editHistory && editHistory.length > 0 && (
                <div style={{ marginTop: 24, borderTop: '1px solid #e2e8f0', paddingTop: 16, marginBottom: 20 }}>
                  <div style={{ fontWeight: 700, color: '#002147', fontSize: 14, marginBottom: 12 }}>
                    Proposal Modification & Edit History ({editHistory.length} edits)
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {editHistory.map((eh, idx) => (
                      <div key={idx} style={{ background: '#f8fafc', padding: 10, borderRadius: 6, borderLeft: '3px solid #3b82f6', fontSize: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                          <span style={{ fontWeight: 700, color: '#1e293b' }}>
                            Edited by: {eh.edited_by} ({eh.edited_by_role})
                          </span>
                          <span style={{ color: '#64748b' }}>
                            {new Date(eh.edited_at).toLocaleString('en-IN')}
                          </span>
                        </div>
                        <div style={{ color: '#475569' }}>
                          {eh.changes_summary || 'Fields modified.'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Status Audit History Timeline */}
              {proposal.history && proposal.history.length > 0 && (
                <div style={{ marginTop: 16, borderTop: '1px solid #e2e8f0', paddingTop: 16 }}>
                  <div style={{ fontWeight: 700, color: '#002147', fontSize: 14, marginBottom: 12 }}>
                    Status Review Audit Trail
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {proposal.history.map((h, idx) => (
                      <div key={idx} style={{ background: '#f8fafc', padding: 10, borderRadius: 6, borderLeft: '3px solid #002147', fontSize: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                          <span style={{ fontWeight: 700, color: '#1e293b' }}>
                            Status: {h.new_status} {h.previous_status ? `(Previous: ${h.previous_status})` : ''}
                          </span>
                          <span style={{ color: '#64748b' }}>
                            {new Date(h.changed_at).toLocaleString('en-IN')}
                          </span>
                        </div>
                        <div style={{ color: '#475569' }}>
                          Changed by: <strong>{h.changed_by}</strong> — {h.remarks || 'No remarks entered.'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Admin Status Update Form */}
              {currentUser && (
                <form onSubmit={handleStatusSubmit} style={{ marginTop: 24, padding: 16, background: '#f1f5f9', borderRadius: 8, border: '1px solid #cbd5e1' }}>
                  <div style={{ fontWeight: 700, color: '#002147', fontSize: 13.5, marginBottom: 10 }}>
                    Update Proposal Status (Academic Office Authority)
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr auto', gap: 10, alignItems: 'center' }}>
                    <select
                      className="form-control"
                      value={selectedStatus}
                      onChange={e => setSelectedStatus(e.target.value)}
                    >
                      {STATUS_OPTIONS.map(s => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>

                    <input
                      type="text"
                      className="form-control"
                      placeholder="Enter review remarks / notes for record..."
                      value={statusRemarks}
                      onChange={e => setStatusRemarks(e.target.value)}
                    />

                    <button
                      type="submit"
                      className="btn btn-primary btn-sm"
                      disabled={isUpdatingStatus}
                    >
                      {isUpdatingStatus ? 'Updating...' : 'Save Status'}
                    </button>
                  </div>
                  <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 8 }}>
                    Decision Notification Rule: Saving as <strong>Approved</strong>, <strong>Rejected</strong>, or <strong>Modification Required</strong> dispatches an official notification email to the submitter (<code>{proposal.faculty_email}</code>).
                  </div>
                </form>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer with Actions (Requirements 1, 2, 3) */}
        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {proposal ? (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {/* Feature 1: Download PDF */}
              <a
                href={api.getPdfDownloadUrl(proposal.proposal_id)}
                className="btn btn-primary btn-sm"
                download={`${proposal.proposal_id}.pdf`}
              >
                <Download size={14} />
                <span>Download PDF</span>
              </a>

              <a
                href={api.getPdfViewUrl(proposal.proposal_id)}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary btn-sm"
              >
                <ExternalLink size={14} />
                <span>View PDF</span>
              </a>

              {/* Feature 3: Compose Email */}
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setIsComposeEmailOpen(true)}
              >
                <Mail size={14} />
                <span>Compose Email</span>
              </button>

              {/* Feature 2: Edit Proposal (for Admin or authorized users) */}
              {currentUser && onEditProposal && (
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    onClose();
                    onEditProposal(proposal.proposal_id);
                  }}
                >
                  <Edit3 size={14} />
                  <span>Edit Proposal</span>
                </button>
              )}
            </div>
          ) : <div />}

          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Close
          </button>
        </div>

        {/* Compose Email Modal (Requirement 3) */}
        {proposal && (
          <EmailComposeModal
            isOpen={isComposeEmailOpen}
            onClose={() => setIsComposeEmailOpen(false)}
            proposal={proposal}
            authKey={localStorage.getItem('sapc_token')}
          />
        )}
      </div>
    </div>
  );
}
