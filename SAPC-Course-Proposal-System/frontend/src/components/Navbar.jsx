import React from 'react';
import { FileText, LayoutDashboard, Clock, User, LogOut, CheckCircle, AlertTriangle } from 'lucide-react';

export default function Navbar({
  currentView,
  setCurrentView,
  deadlineData,
  currentUser,
  onOpenLogin,
  onLogout
}) {
  const isOpen = deadlineData?.is_open;

  return (
    <header className="navbar">
      <div className="navbar-inner">
        {/* Brand / Institution */}
        <div className="brand-section">
          <div className="brand-crest" title="IIT Gandhinagar SAPC">
            IITGN
          </div>
          <div className="brand-titles">
            <h1>SAPC Course Proposal Platform</h1>
            <p>Academic Office — Senate Academic Programme Committee (SAPC) | Project 13</p>
          </div>
        </div>

        {/* View Switcher & Controls */}
        <div className="nav-controls">
          {/* Submission Status Pill */}
          <div
            className={`banner-status-badge ${isOpen ? 'open' : 'closed'}`}
            style={{ marginRight: 6 }}
            title={deadlineData?.status_message || ''}
          >
            {isOpen ? <CheckCircle size={14} /> : <AlertTriangle size={14} />}
            <span>{isOpen ? 'Submissions Open' : 'Submissions Closed'}</span>
          </div>

          <button
            className={`nav-tab-btn ${currentView === 'form' ? 'active' : ''}`}
            onClick={() => setCurrentView('form')}
          >
            <FileText size={16} />
            <span>Course Proposal Form</span>
          </button>

          <button
            className={`nav-tab-btn ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            <LayoutDashboard size={16} />
            <span>Academic Office Dashboard</span>
          </button>

          {/* Admin Authentication */}
          {currentUser ? (
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span className="auth-btn logged-in" title={`Logged in as ${currentUser.username}`}>
                <User size={14} />
                <span>Admin ({currentUser.username})</span>
              </span>
              <button
                className="auth-btn"
                onClick={onLogout}
                title="Log Out of Academic Office Admin"
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <button
              className="auth-btn"
              onClick={onOpenLogin}
              title="Academic Office Administrator Login"
            >
              <User size={14} />
              <span>Admin Login</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
