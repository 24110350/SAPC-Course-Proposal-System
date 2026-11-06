import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import DeadlineBanner from './components/DeadlineBanner';
import CourseProposalForm from './components/CourseProposalForm';
import AcademicDashboard from './components/AcademicDashboard';
import ProposalDetailModal from './components/ProposalDetailModal';
import DeadlineManagerModal from './components/DeadlineManagerModal';
import AdminLoginModal from './components/AdminLoginModal';
import OutboxModal from './components/OutboxModal';
import { api } from './services/api';

export default function App() {
  const [currentView, setCurrentView] = useState('form'); // 'form' | 'dashboard'
  const [deadlineData, setDeadlineData] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);

  // Proposal Edit State (Requirement 2)
  const [editingProposalId, setEditingProposalId] = useState(null);
  const [editingToken, setEditingToken] = useState(null);

  // Modals state
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isDeadlineManagerOpen, setIsDeadlineManagerOpen] = useState(false);
  const [isOutboxOpen, setIsOutboxOpen] = useState(false);
  const [selectedProposalId, setSelectedProposalId] = useState(null);

  // Fetch deadline information
  const refreshDeadline = useCallback(async () => {
    try {
      const res = await api.getDeadline();
      if (res.success && res.deadline) {
        setDeadlineData(res.deadline);
      }
    } catch (err) {
      console.error('Could not fetch deadline:', err);
    }
  }, []);

  // Check existing auth token
  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('sapc_token');
    if (!token) return;
    try {
      const res = await api.getCurrentUser(token);
      if (res.success && res.user) {
        setCurrentUser(res.user);
      } else {
        localStorage.removeItem('sapc_token');
      }
    } catch (err) {
      localStorage.removeItem('sapc_token');
    }
  }, []);

  useEffect(() => {
    refreshDeadline();
    checkAuth();

    // Check URL parameters for proposal edit token (?edit_token=...) or edit ID (?edit_id=...)
    try {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('edit_token');
      const editId = params.get('edit_id');
      if (token) {
        setEditingToken(token);
        setCurrentView('form');
      } else if (editId) {
        setEditingProposalId(editId);
        setCurrentView('form');
      }
    } catch (e) {
      // Ignore URL parsing errors
    }

    // Periodic deadline polling every 60 seconds
    const interval = setInterval(refreshDeadline, 60000);
    return () => clearInterval(interval);
  }, [refreshDeadline, checkAuth]);

  const handleLogout = () => {
    localStorage.removeItem('sapc_token');
    setCurrentUser(null);
  };

  const handleStartEdit = (proposalId) => {
    setSelectedProposalId(null);
    setEditingProposalId(proposalId);
    setEditingToken(null);
    setCurrentView('form');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCancelEdit = () => {
    setEditingProposalId(null);
    setEditingToken(null);
    try {
      if (window.location.search) {
        window.history.replaceState({}, '', window.location.pathname);
      }
    } catch (e) {}
  };

  return (
    <div className="app-container">
      {/* Institutional Top Navbar */}
      <Navbar
        currentView={currentView}
        setCurrentView={(view) => {
          if (view === 'dashboard') {
            handleCancelEdit();
          }
          setCurrentView(view);
        }}
        deadlineData={deadlineData}
        currentUser={currentUser}
        onOpenLogin={() => setIsLoginOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Workspace */}
      <main className="main-content">
        {/* Deadline Information Banner */}
        <DeadlineBanner
          deadlineData={deadlineData}
          onConfigureDeadline={() => setIsDeadlineManagerOpen(true)}
          isAdmin={!!currentUser}
        />

        {/* View Routing */}
        {currentView === 'form' ? (
          <CourseProposalForm
            deadlineData={deadlineData}
            editProposalId={editingProposalId}
            editToken={editingToken}
            currentUser={currentUser}
            onCancelEdit={handleCancelEdit}
            onSubmissionSuccess={(proposal) => {
              refreshDeadline();
              handleCancelEdit();
            }}
          />
        ) : (
          <AcademicDashboard
            currentUser={currentUser}
            onOpenLogin={() => setIsLoginOpen(true)}
            onOpenDeadlineManager={() => setIsDeadlineManagerOpen(true)}
            onOpenOutbox={() => setIsOutboxOpen(true)}
            onViewProposalDetail={(id) => setSelectedProposalId(id)}
            onEditProposal={handleStartEdit}
          />
        )}
      </main>

      {/* Institutional Footer */}
      <footer style={{ background: '#002147', color: '#94a3b8', padding: '24px 20px', textAlign: 'center', fontSize: 12.5, borderTop: '2px solid #c29b38' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ textAlign: 'left' }}>
            <strong style={{ color: '#ffffff' }}>Indian Institute of Technology Gandhinagar</strong> — Academic Office<br />
            Senate Academic Programme Committee (SAPC) — Course Proposal & Curriculum Platform
          </div>
          <div style={{ textAlign: 'right' }}>
            CS202 Project 13 (Group 11) — Phase 1 Production Release<br />
            Official Routing: <u>ar.ug@iitgn.ac.in</u> | <u>doaa@iitgn.ac.in</u>
          </div>
        </div>
      </footer>

      {/* Modals */}
      <AdminLoginModal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onLoginSuccess={(user) => setCurrentUser(user)}
      />

      <DeadlineManagerModal
        isOpen={isDeadlineManagerOpen}
        onClose={() => setIsDeadlineManagerOpen(false)}
        currentDeadline={deadlineData}
        onDeadlineUpdated={(newDeadline) => setDeadlineData(newDeadline)}
      />

      <OutboxModal
        isOpen={isOutboxOpen}
        onClose={() => setIsOutboxOpen(false)}
      />

      <ProposalDetailModal
        proposalId={selectedProposalId}
        onClose={() => setSelectedProposalId(null)}
        currentUser={currentUser}
        onEditProposal={handleStartEdit}
        onStatusUpdated={() => {
          // Triggers refreshed data
        }}
      />
    </div>
  );
}
