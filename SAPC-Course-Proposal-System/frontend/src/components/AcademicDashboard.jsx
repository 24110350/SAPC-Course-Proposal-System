import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, Filter, ArrowUpDown, ArrowUp, ArrowDown, Download,
  ExternalLink, Eye, RefreshCw, FileSpreadsheet, FileText,
  Calendar, Mail, CheckCircle, AlertTriangle, Clock, ChevronLeft, ChevronRight,
  UploadCloud, Settings, Edit3
} from 'lucide-react';
import { api } from '../services/api';
import { COURSE_TYPES, COURSE_LEVELS, STATUS_OPTIONS } from '../constants/sapcOptions';
import ExcelImportModal from './ExcelImportModal';
import FormConfigModal from './FormConfigModal';

export default function AcademicDashboard({
  currentUser,
  onOpenLogin,
  onOpenDeadlineManager,
  onOpenOutbox,
  onViewProposalDetail,
  onEditProposal
}) {
  const [proposals, setProposals] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    under_review: 0,
    approved: 0,
    modification_required: 0,
    rejected: 0
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals for Requirement 5 (Dynamic Form Config) & Requirement 8 (Excel Import)
  const [isExcelImportOpen, setIsExcelImportOpen] = useState(false);
  const [isFormConfigOpen, setIsFormConfigOpen] = useState(false);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [natureFilter, setNatureFilter] = useState('ALL');

  // Sorting
  const [sortBy, setSortBy] = useState('submission_date');
  const [sortOrder, setSortOrder] = useState('desc');

  // Pagination
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Fetch proposals from PostgreSQL backend
  const loadProposals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        q: searchQuery,
        status: statusFilter,
        course_type: typeFilter,
        course_level: levelFilter,
        nature: natureFilter,
        sort_by: sortBy,
        order: sortOrder,
        page,
        per_page: perPage
      };

      const res = await api.getProposals(params);
      if (res.success) {
        setProposals(res.proposals || []);
        setStats(res.stats || {});
        setTotalPages(res.total_pages || 1);
        setTotalCount(res.total || 0);
      }
    } catch (err) {
      setError(err.message || 'Failed to load proposals.');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, statusFilter, typeFilter, levelFilter, natureFilter, sortBy, sortOrder, page, perPage]);

  useEffect(() => {
    loadProposals();
  }, [loadProposals]);

  // Handle Sort Toggle
  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
    setPage(1);
  };

  // Status Change Handler
  const handleStatusChange = async (proposalId, newStatus) => {
    const token = localStorage.getItem('sapc_token');
    if (!token) {
      alert('Please log in as Academic Office Admin to change proposal status.');
      onOpenLogin();
      return;
    }

    try {
      const res = await api.updateProposalStatus(proposalId, newStatus, 'Status updated from dashboard table', token);
      if (res && res.message && ['Approved', 'Rejected', 'Modification Required'].includes(newStatus)) {
        alert(res.message);
      }
      loadProposals();
    } catch (err) {
      alert(err.message || 'Failed to update proposal status.');
    }
  };

  // Resend Email Handler
  const handleResendEmail = async (proposalId) => {
    const token = localStorage.getItem('sapc_token');
    if (!token) {
      alert('Please log in as Academic Office Admin to retry notifications.');
      onOpenLogin();
      return;
    }

    try {
      await api.resendNotificationEmail(proposalId, token);
      alert('Notification email successfully resent.');
      loadProposals();
    } catch (err) {
      alert(err.message || 'Failed to send notification email.');
    }
  };

  // Export handlers
  const handleExport = (format) => {
    const token = localStorage.getItem('sapc_token');
    if (!token) {
      alert('Please log in as Academic Office Admin to export submissions.');
      onOpenLogin();
      return;
    }
    const params = {
      q: searchQuery,
      status: statusFilter,
      course_type: typeFilter,
      course_level: levelFilter,
      nature: natureFilter,
      sort_by: sortBy,
      order: sortOrder
    };
    const url = api.getExportUrl(format, params, token);
    window.open(url, '_blank');
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Approved':
        return <span className="badge badge-approved">{status}</span>;
      case 'Under Review':
        return <span className="badge badge-review">{status}</span>;
      case 'Modification Required':
        return <span className="badge badge-modification">{status}</span>;
      case 'Rejected':
        return <span className="badge badge-rejected">{status}</span>;
      default:
        return <span className="badge badge-pending">{status || 'Pending'}</span>;
    }
  };

  return (
    <div>
      {/* Metrics Banner */}
      <div className="metrics-grid">
        <div className="metric-card" style={{ borderLeft: '4px solid #002147' }}>
          <div className="num">{stats.total || 0}</div>
          <div className="label">Total Proposals</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #eab308' }}>
          <div className="num" style={{ color: '#854d0e' }}>{stats.pending || 0}</div>
          <div className="label">Pending Review</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #0284c7' }}>
          <div className="num" style={{ color: '#0369a1' }}>{stats.under_review || 0}</div>
          <div className="label">Under Review</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #16a34a' }}>
          <div className="num" style={{ color: '#15803d' }}>{stats.approved || 0}</div>
          <div className="label">Approved</div>
        </div>
        <div className="metric-card" style={{ borderLeft: '4px solid #f97316' }}>
          <div className="num" style={{ color: '#c2410c' }}>{stats.modification_required || 0}</div>
          <div className="label">Modification Required</div>
        </div>
      </div>

      {/* Main Dashboard Card */}
      <div className="paper-card">
        {/* Header Toolbar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14, marginBottom: 20 }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 800, color: '#002147' }}>
              Academic Office — Course Proposals Management
            </h2>
            <p style={{ fontSize: 13, color: '#64748b' }}>
              Database-backed records directly linked to PostgreSQL (Showing {proposals.length} of {totalCount} records)
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleExport('xlsx')}
              title="Export current proposals dataset to Microsoft Excel (.xlsx)"
            >
              <FileSpreadsheet size={15} color="#15803d" />
              <span>Export Excel</span>
            </button>

            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleExport('csv')}
              title="Export current proposals dataset to CSV (.csv)"
            >
              <FileText size={15} color="#0369a1" />
              <span>Export CSV</span>
            </button>

            {currentUser && (
              <>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setIsExcelImportOpen(true)}
                  title="Import proposals from Excel (.xlsx) with SAPC Number & Approval Date"
                >
                  <UploadCloud size={15} color="#002147" />
                  <span>Import Excel</span>
                </button>

                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setIsFormConfigOpen(true)}
                  title="Configure dynamic form fields, options, and categories"
                >
                  <Settings size={15} color="#002147" />
                  <span>Form Config</span>
                </button>

                <button
                  className="btn btn-secondary btn-sm"
                  onClick={onOpenDeadlineManager}
                  title="Configure submission window dates & deadlines"
                >
                  <Calendar size={15} color="#002147" />
                  <span>Configure Deadline</span>
                </button>

                <button
                  className="btn btn-secondary btn-sm"
                  onClick={onOpenOutbox}
                  title="View outbound email delivery logs"
                >
                  <Mail size={15} color="#475569" />
                  <span>Email Outbox</span>
                </button>
              </>
            )}

            <button
              className="btn btn-secondary btn-sm"
              onClick={loadProposals}
              title="Refresh proposals table"
            >
              <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Filter and Search Controls */}
        <div style={{ background: '#f8fafc', padding: 14, borderRadius: 8, border: '1px solid #e2e8f0', marginBottom: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
            {/* Search */}
            <div style={{ gridColumn: 'span 2' }}>
              <div style={{ position: 'relative' }}>
                <Search size={16} style={{ position: 'absolute', left: 10, top: 11, color: '#94a3b8' }} />
                <input
                  type="text"
                  className="form-control"
                  style={{ paddingLeft: 34 }}
                  placeholder="Search Proposal ID, Course Title, Proposer, Email, Code..."
                  value={searchQuery}
                  onChange={e => {
                    setSearchQuery(e.target.value);
                    setPage(1);
                  }}
                />
              </div>
            </div>

            {/* Status Filter */}
            <div>
              <select
                className="form-control"
                value={statusFilter}
                onChange={e => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="ALL">All Statuses</option>
                {STATUS_OPTIONS.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Department / Course Type */}
            <div>
              <select
                className="form-control"
                value={typeFilter}
                onChange={e => {
                  setTypeFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="ALL">All Disciplines / Types</option>
                {COURSE_TYPES.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            {/* Level Filter */}
            <div>
              <select
                className="form-control"
                value={levelFilter}
                onChange={e => {
                  setLevelFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="ALL">All Levels</option>
                {COURSE_LEVELS.map(l => (
                  <option key={l} value={l}>Level {l}</option>
                ))}
              </select>
            </div>

            {/* Nature (New / Modification) */}
            <div>
              <select
                className="form-control"
                value={natureFilter}
                onChange={e => {
                  setNatureFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="ALL">All Course Natures</option>
                <option value="NEW">New Course Proposals</option>
                <option value="MODIFICATION">Modifications of Existing Courses</option>
              </select>
            </div>
          </div>
        </div>

        {/* Structured Data Table */}
        {error ? (
          <div style={{ padding: 24, textAlign: 'center', color: '#b91c1c' }}>
            <AlertTriangle size={24} style={{ marginBottom: 6 }} />
            <div>{error}</div>
          </div>
        ) : loading && proposals.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>
            <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px' }} />
            <div>Loading proposals from PostgreSQL database...</div>
          </div>
        ) : proposals.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>
            <FileText size={32} style={{ margin: '0 auto 10px', color: '#cbd5e1' }} />
            <div style={{ fontWeight: 600, fontSize: 15 }}>No proposals match your search/filter criteria.</div>
            <p style={{ fontSize: 13, marginTop: 4 }}>Try clearing the filters or searching with a different term.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="sortable" onClick={() => handleSort('proposal_id')}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      Proposal ID
                      {sortBy === 'proposal_id' ? (sortOrder === 'asc' ? <ArrowUp size={13} /> : <ArrowDown size={13} />) : <ArrowUpDown size={13} color="#94a3b8" />}
                    </span>
                  </th>
                  <th className="sortable" onClick={() => handleSort('course_title')}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      Course Title & Nature
                      {sortBy === 'course_title' ? (sortOrder === 'asc' ? <ArrowUp size={13} /> : <ArrowDown size={13} />) : <ArrowUpDown size={13} color="#94a3b8" />}
                    </span>
                  </th>
                  <th className="sortable" onClick={() => handleSort('proposer_name')}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      Proposer
                      {sortBy === 'proposer_name' ? (sortOrder === 'asc' ? <ArrowUp size={13} /> : <ArrowDown size={13} />) : <ArrowUpDown size={13} color="#94a3b8" />}
                    </span>
                  </th>
                  <th>Faculty Email</th>
                  <th>L-T-P-C</th>
                  <th className="sortable" onClick={() => handleSort('submission_date')}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      Submitted
                      {sortBy === 'submission_date' ? (sortOrder === 'asc' ? <ArrowUp size={13} /> : <ArrowDown size={13} />) : <ArrowUpDown size={13} color="#94a3b8" />}
                    </span>
                  </th>
                  <th className="sortable" onClick={() => handleSort('status')}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      Status
                      {sortBy === 'status' ? (sortOrder === 'asc' ? <ArrowUp size={13} /> : <ArrowDown size={13} />) : <ArrowUpDown size={13} color="#94a3b8" />}
                    </span>
                  </th>
                  <th>Email Sent</th>
                  <th style={{ textAlign: 'center' }}>Official PDF</th>
                  <th style={{ textAlign: 'center' }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {proposals.map(p => {
                  const subDate = p.submission_date ? new Date(p.submission_date).toLocaleDateString('en-IN', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric'
                  }) : '—';

                  const isSent = p.email_notification_status === 'Sent';
                  const isFailed = p.email_notification_status === 'Failed';

                  return (
                    <tr key={p.proposal_id}>
                      {/* Proposal ID */}
                      <td style={{ fontFamily: 'monospace', fontWeight: 700, color: '#002147' }}>
                        <button
                          type="button"
                          onClick={() => onViewProposalDetail(p.proposal_id)}
                          style={{ background: 'none', border: 'none', color: '#0b3c68', fontWeight: 700, cursor: 'pointer', textDecoration: 'underline', font: 'inherit' }}
                        >
                          {p.proposal_id}
                        </button>
                      </td>

                      {/* Course Title */}
                      <td style={{ maxWidth: 260 }}>
                        <div style={{ fontWeight: 600, color: '#1e293b' }}>{p.course_title}</div>
                        <div style={{ display: 'flex', gap: 6, marginTop: 3 }}>
                          {p.is_modification ? (
                            <span style={{ fontSize: 10.5, background: '#fee2e2', color: '#991b1b', padding: '1px 6px', borderRadius: 4, fontWeight: 700 }}>
                              MODIFICATION ({p.existing_course_code || 'Code N/A'})
                            </span>
                          ) : (
                            <span style={{ fontSize: 10.5, background: '#e0f2fe', color: '#0369a1', padding: '1px 6px', borderRadius: 4, fontWeight: 700 }}>
                              NEW COURSE
                            </span>
                          )}
                          <span style={{ fontSize: 10.5, background: '#f1f5f9', color: '#475569', padding: '1px 6px', borderRadius: 4, fontWeight: 600 }}>
                            {p.course_type} | Level {p.course_level}
                          </span>
                          {p.sapc_number && (
                            <span style={{ fontSize: 10.5, background: '#fef3c7', color: '#92400e', padding: '1px 6px', borderRadius: 4, fontWeight: 700, border: '1px solid #fde68a' }} title={`SAPC Approved: ${p.approval_date || 'N/A'}`}>
                              SAPC: {p.sapc_number}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Proposer */}
                      <td>
                        <div style={{ fontWeight: 600 }}>{p.proposer_name}</div>
                        <div style={{ fontSize: 11.5, color: '#64748b' }}>{p.potential_instructors}</div>
                      </td>

                      {/* Faculty Email */}
                      <td style={{ fontSize: 12.5, color: '#334155' }}>
                        {p.faculty_email}
                      </td>

                      {/* L-T-P-C */}
                      <td style={{ fontFamily: 'monospace', fontSize: 12 }}>
                        {p.course_l_t_p_c} <span style={{ color: '#64748b' }}>({p.credits} cr)</span>
                      </td>

                      {/* Submitted Date */}
                      <td style={{ fontSize: 12, color: '#475569' }}>
                        {subDate}
                      </td>

                      {/* Status */}
                      <td>
                        {currentUser ? (
                          <select
                            className="form-control"
                            style={{ padding: '4px 8px', fontSize: 11.5, fontWeight: 700, width: 140 }}
                            value={p.status}
                            onChange={e => handleStatusChange(p.proposal_id, e.target.value)}
                          >
                            {STATUS_OPTIONS.map(s => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                        ) : (
                          getStatusBadge(p.status)
                        )}
                      </td>

                      {/* Email Status */}
                      <td>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          {isSent ? (
                            <span className="badge badge-approved" title="Notification email successfully delivered">
                              <CheckCircle size={12} />
                              <span>Sent</span>
                            </span>
                          ) : isFailed ? (
                            <span className="badge badge-rejected" title={p.email_error_log || 'Notification failed'}>
                              <AlertTriangle size={12} />
                              <span>Failed</span>
                            </span>
                          ) : (
                            <span className="badge badge-pending">Pending</span>
                          )}

                          {isFailed && currentUser && (
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              style={{ padding: '2px 5px', fontSize: 10 }}
                              onClick={() => handleResendEmail(p.proposal_id)}
                              title="Retry sending notification email"
                            >
                              Retry
                            </button>
                          )}
                        </div>
                      </td>

                      {/* PDF Download/View */}
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'inline-flex', gap: 6 }}>
                          <a
                            href={api.getPdfDownloadUrl(p.proposal_id)}
                            className="btn btn-secondary btn-sm"
                            download={`${p.proposal_id}.pdf`}
                            title="Download official PDF"
                          >
                            <Download size={13} color="#002147" />
                          </a>
                          <a
                            href={api.getPdfViewUrl(p.proposal_id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-secondary btn-sm"
                            title="View PDF inline in browser"
                          >
                            <ExternalLink size={13} color="#475569" />
                          </a>
                        </div>
                      </td>

                      {/* View Details / Actions */}
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'inline-flex', gap: 6 }}>
                          <button
                            type="button"
                            className="btn btn-primary btn-sm"
                            style={{ padding: '5px 8px' }}
                            onClick={() => onViewProposalDetail(p.proposal_id)}
                            title="View complete proposal details and audit trail"
                          >
                            <Eye size={14} />
                          </button>
                          {currentUser && onEditProposal && (
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              style={{ padding: '5px 8px' }}
                              onClick={() => onEditProposal(p.proposal_id)}
                              title="Edit proposal content (Admin)"
                            >
                              <Edit3 size={14} color="#002147" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 18, flexWrap: 'wrap', gap: 10 }}>
          <div style={{ fontSize: 12.5, color: '#64748b' }}>
            Showing Page <strong>{page}</strong> of <strong>{totalPages}</strong> ({totalCount} total proposals)
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 12.5, color: '#64748b' }}>Per page:</span>
            <select
              className="form-control"
              style={{ width: 70, padding: '4px 6px', fontSize: 12 }}
              value={perPage}
              onChange={e => {
                setPerPage(Number(e.target.value));
                setPage(1);
              }}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>

            <button
              className="btn btn-secondary btn-sm"
              disabled={page <= 1}
              onClick={() => setPage(prev => Math.max(1, prev - 1))}
            >
              <ChevronLeft size={14} />
              <span>Prev</span>
            </button>
            <button
              className="btn btn-secondary btn-sm"
              disabled={page >= totalPages}
              onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
            >
              <span>Next</span>
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Requirement 8: Excel Import Modal */}
      <ExcelImportModal
        isOpen={isExcelImportOpen}
        onClose={() => setIsExcelImportOpen(false)}
        onImportSuccess={() => loadProposals()}
      />

      {/* Requirement 5: Form Config Modal */}
      <FormConfigModal
        isOpen={isFormConfigOpen}
        onClose={() => setIsFormConfigOpen(false)}
      />
    </div>
  );
}
