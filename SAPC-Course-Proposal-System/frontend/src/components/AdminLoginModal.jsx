import React, { useState } from 'react';
import { X, Lock, User, AlertCircle, Key } from 'lucide-react';
import { api } from '../services/api';

export default function AdminLoginModal({ isOpen, onClose, onLoginSuccess }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('Admin@IITGN2026');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(username, password);
      if (res.success && res.token) {
        localStorage.setItem('sapc_token', res.token);
        if (onLoginSuccess) onLoginSuccess(res.user);
        onClose();
      } else {
        setError('Login failed. Please verify credentials.');
      }
    } catch (err) {
      setError(err.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleFillDemo = () => {
    setUsername('admin');
    setPassword('Admin@IITGN2026');
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={e => e.stopPropagation()} style={{ maxWidth: 440 }}>
        <div className="modal-header">
          <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Lock size={18} />
            <span>Academic Office Admin Login</span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
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
                  backgroundColor: '#fee2e2',
                  color: '#b91c1c'
                }}
              >
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: 12, marginBottom: 16, fontSize: 12 }}>
              <div style={{ fontWeight: 700, color: '#002147', marginBottom: 2 }}>
                Evaluator / Demo Credentials:
              </div>
              <div style={{ color: '#475569' }}>
                Username: <code>admin</code> | Password: <code>Admin@IITGN2026</code>
              </div>
              <button
                type="button"
                onClick={handleFillDemo}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#0b3c68',
                  textDecoration: 'underline',
                  fontSize: 11.5,
                  cursor: 'pointer',
                  fontWeight: 600,
                  marginTop: 4,
                  padding: 0
                }}
              >
                Auto-fill demo credentials
              </button>
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Username</span>
              </label>
              <div style={{ position: 'relative' }}>
                <User size={15} style={{ position: 'absolute', left: 10, top: 11, color: '#94a3b8' }} />
                <input
                  type="text"
                  className="form-control"
                  style={{ paddingLeft: 32 }}
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Password</span>
              </label>
              <div style={{ position: 'relative' }}>
                <Key size={15} style={{ position: 'absolute', left: 10, top: 11, color: '#94a3b8' }} />
                <input
                  type="password"
                  className="form-control"
                  style={{ paddingLeft: 32 }}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary btn-sm" disabled={loading}>
              <Lock size={14} />
              <span>{loading ? 'Authenticating...' : 'Log In'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
