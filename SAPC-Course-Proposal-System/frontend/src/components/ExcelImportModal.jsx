import React, { useState } from 'react';
import { X, FileSpreadsheet, Upload, Download, CheckCircle, AlertTriangle, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function ExcelImportModal({ isOpen, onClose, token, onImportSuccess }) {
  if (!isOpen) return null;

  const [selectedFile, setSelectedFile] = useState(null);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [confirmResult, setConfirmResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setPreviewData(null);
      setConfirmResult(null);
      setError(null);
    }
  };

  const handlePreview = async () => {
    if (!selectedFile) {
      setError('Please select an Excel (.xlsx) file to upload.');
      return;
    }
    setIsPreviewing(true);
    setError(null);
    try {
      const res = await api.previewExcelImport(selectedFile, token);
      if (res.success) {
        setPreviewData(res);
      } else {
        setError(res.error || 'Failed to preview Excel file.');
      }
    } catch (err) {
      setError(err.message || 'Failed to parse Excel file.');
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleConfirm = async () => {
    if (!previewData || !previewData.valid_rows || previewData.valid_rows.length === 0) {
      setError('No valid rows available to import.');
      return;
    }
    setIsConfirming(true);
    setError(null);
    try {
      const res = await api.confirmExcelImport(previewData.valid_rows, token);
      if (res.success) {
        setConfirmResult(res);
        if (onImportSuccess) onImportSuccess();
      } else {
        setError(res.error || 'Failed to apply import.');
      }
    } catch (err) {
      setError(err.message || 'Failed to complete import.');
    } finally {
      setIsConfirming(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewData(null);
    setConfirmResult(null);
    setError(null);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={e => e.stopPropagation()} style={{ maxWidth: 940, maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ background: '#002147', color: '#c29b38', padding: 8, borderRadius: 6 }}>
              <FileSpreadsheet size={18} />
            </div>
            <div>
              <div className="modal-title" style={{ fontSize: 16 }}>
                Import SAPC Numbers & Approvals via Excel (.xlsx)
              </div>
              <div style={{ fontSize: 12, color: '#64748b' }}>
                Batch match proposals, update SAPC numbers, approval dates, status, and remarks
              </div>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body" style={{ flex: 1, overflowY: 'auto', padding: 18 }}>
          {/* Top Instructions & Template Link */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '12px 16px', borderRadius: 6, border: '1px solid #e2e8f0', marginBottom: 16 }}>
            <div>
              <strong style={{ fontSize: 13, color: '#002147' }}>Standard Excel Format:</strong>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                Columns: <code>Proposal ID</code>, <code>Course Title</code>, <code>SAPC Number</code>, <code>Approval Date (YYYY-MM-DD)</code>, <code>Status</code>, <code>Reviewer Remarks</code>
              </div>
            </div>
            <a
              href={`${api.getExcelImportTemplateUrl()}?token=${encodeURIComponent(token)}`}
              className="btn btn-secondary btn-sm"
              download="SAPC_Import_Template.xlsx"
            >
              <Download size={14} />
              <span>Download Template</span>
            </a>
          </div>

          {error && (
            <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', color: '#991b1b', padding: 12, borderRadius: 6, display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, marginBottom: 16 }}>
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}

          {confirmResult ? (
            /* Successful Import Summary */
            <div style={{ textAlign: 'center', padding: '30px 20px', background: '#f0fdf4', borderRadius: 8, border: '1px solid #86efac' }}>
              <div style={{ display: 'inline-flex', padding: 12, background: '#dcfce7', borderRadius: '50%', color: '#16a34a', marginBottom: 12 }}>
                <CheckCircle size={36} />
              </div>
              <h3 style={{ fontSize: 18, color: '#166534', fontWeight: 800, marginBottom: 6 }}>
                Excel Import Successfully Completed!
              </h3>
              <p style={{ color: '#15803d', fontSize: 14, marginBottom: 18 }}>
                {confirmResult.message}
              </p>
              <button onClick={handleReset} className="btn btn-primary btn-sm">
                <RefreshCw size={14} />
                <span>Import Another File</span>
              </button>
            </div>
          ) : !previewData ? (
            /* Step 1: File Upload */
            <div style={{ border: '2px dashed #cbd5e1', borderRadius: 8, padding: 36, textAlign: 'center', background: '#f8fafc' }}>
              <Upload size={36} color="#002147" style={{ marginBottom: 12 }} />
              <div style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', marginBottom: 6 }}>
                Select Excel (.xlsx) File to Preview
              </div>
              <div style={{ fontSize: 12.5, color: '#64748b', marginBottom: 18 }}>
                The system will automatically match rows against existing proposals and validate dates and statuses.
              </div>
              <input
                type="file"
                id="excelFileInput"
                accept=".xlsx,.xlsm"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <div style={{ display: 'flex', gap: 10, justifyContent: 'center', alignItems: 'center' }}>
                <label htmlFor="excelFileInput" className="btn btn-secondary btn-sm" style={{ cursor: 'pointer' }}>
                  <span>Choose File...</span>
                </label>
                {selectedFile && (
                  <span style={{ fontSize: 13, color: '#002147', fontWeight: 600 }}>
                    {selectedFile.name}
                  </span>
                )}
                {selectedFile && (
                  <button
                    onClick={handlePreview}
                    className="btn btn-primary btn-sm"
                    disabled={isPreviewing}
                  >
                    {isPreviewing ? 'Validating...' : 'Validate & Preview Rows'}
                  </button>
                )}
              </div>
            </div>
          ) : (
            /* Step 2: Row Preview & Summary */
            <div>
              {/* Summary Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 16 }}>
                <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0', textAlign: 'center' }}>
                  <div style={{ fontSize: 11.5, color: '#64748b', textTransform: 'uppercase' }}>Total Rows</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: '#002147' }}>{previewData.total_rows}</div>
                </div>
                <div style={{ background: '#f0fdf4', padding: 12, borderRadius: 6, border: '1px solid #bbf7d0', textAlign: 'center' }}>
                  <div style={{ fontSize: 11.5, color: '#16a34a', textTransform: 'uppercase' }}>Valid Matches</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: '#15803d' }}>{previewData.valid_count}</div>
                </div>
                <div style={{ background: '#fef2f2', padding: 12, borderRadius: 6, border: '1px solid #fecaca', textAlign: 'center' }}>
                  <div style={{ fontSize: 11.5, color: '#dc2626', textTransform: 'uppercase' }}>Invalid / Unmatched</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: '#b91c1c' }}>{previewData.invalid_count}</div>
                </div>
              </div>

              {/* Table of Rows */}
              <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: 6, maxHeight: 340 }}>
                <table className="sapc-table" style={{ width: '100%', fontSize: 12 }}>
                  <thead>
                    <tr>
                      <th>Row</th>
                      <th>Proposal ID</th>
                      <th>Matched Course</th>
                      <th>SAPC Number</th>
                      <th>Approval Date</th>
                      <th>Status</th>
                      <th>Validation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.valid_rows.map((r, idx) => (
                      <tr key={`v-${idx}`} style={{ background: '#f0fdf4' }}>
                        <td>{r.row_number}</td>
                        <td><code>{r.proposal_id}</code></td>
                        <td><strong>{r.course_title}</strong></td>
                        <td><span className="badge badge-approved">{r.sapc_number || '—'}</span></td>
                        <td>{r.approval_date || '—'}</td>
                        <td><span className="badge badge-approved">{r.new_status}</span></td>
                        <td><span style={{ color: '#15803d', fontWeight: 700 }}>✓ Valid</span></td>
                      </tr>
                    ))}
                    {previewData.invalid_rows.map((r, idx) => (
                      <tr key={`inv-${idx}`} style={{ background: '#fff1f2' }}>
                        <td>{r.row_number}</td>
                        <td><code>{r.proposal_id}</code></td>
                        <td>{r.course_title}</td>
                        <td>{r.sapc_number || '—'}</td>
                        <td>{r.approval_date || '—'}</td>
                        <td>{r.new_status || '—'}</td>
                        <td style={{ color: '#b91c1c' }}>
                          <AlertTriangle size={13} style={{ display: 'inline', marginRight: 4 }} />
                          {r.errors.join('; ')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            {previewData && !confirmResult && (
              <button onClick={handleReset} className="btn btn-secondary btn-sm" disabled={isConfirming}>
                Select Different File
              </button>
            )}
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-secondary btn-sm" onClick={onClose}>
              {confirmResult ? 'Done' : 'Close'}
            </button>
            {previewData && !confirmResult && previewData.valid_count > 0 && (
              <button
                className="btn btn-primary btn-sm"
                onClick={handleConfirm}
                disabled={isConfirming}
              >
                {isConfirming ? (
                  <span>Applying Updates...</span>
                ) : (
                  <>
                    <CheckCircle size={14} />
                    <span>Confirm & Apply {previewData.valid_count} Update(s)</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
