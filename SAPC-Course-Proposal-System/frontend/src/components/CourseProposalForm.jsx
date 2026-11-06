import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText, Send, CheckCircle, AlertCircle, Download, ExternalLink,
  BookOpen, HelpCircle, Layers, Award, Info, RefreshCw, Copy, Check,
  Edit3, Mail, ArrowLeft
} from 'lucide-react';
import {
  COURSE_TYPES, COURSE_LEVELS, COURSE_DURATIONS, OFFERING_FREQUENCIES,
  BTECH_ELECTIVE_BASKETS, BTECH_DISCIPLINE_ELECTIVES, MINORS_LIST,
  MSC_ELECTIVES, MTECH_DISCIPLINES, MDES_ELECTIVES, DISCIPLINE_ABBREVIATIONS
} from '../constants/sapcOptions';
import { api } from '../services/api';
import EmailComposeModal from './EmailComposeModal';

export default function CourseProposalForm({
  deadlineData,
  onSubmissionSuccess,
  editProposalId = null,
  editToken = null,
  onCancelEdit = null,
  currentUser = null
}) {
  const isSubmissionClosed = deadlineData && !deadlineData.is_open;

  // Form State
  const initialFormState = {
    course_title: '',
    potential_instructors: '',
    proposer_name: '',
    faculty_email: '',
    additional_recipients: '',
    course_type: 'CS',
    course_type_other: '',
    course_level: '3',
    course_level_secondary: '',
    lecture_hours: 3,
    tutorial_hours: 0,
    practical_hours: 0,
    credits: 3,
    course_duration: '4 Quads (Full Semester)',
    expected_frequency: 'Each Year',
    expected_frequency_other: '',
    elective_basket_btech: 'None',
    discipline_elective_btech: 'None',
    discipline_basket_btech: '',
    minors: [],
    minor_basket_thematic_area: '',
    minor_reason: '', // Requirement 4
    discipline_elective_msc: 'None',
    courses_discipline_mtech: 'None',
    mtech_sub_specialization: '',
    discipline_elective_mdes: 'None',
    is_modification: false,
    existing_course_code: '',
    prior_knowledge: '',
    course_contents: '',
    texts_and_references: '',
    learning_outcomes: '',
    overlap_courses: '',
    other_relevant_info: '',
    custom_fields_data: {}
  };

  const [formData, setFormData] = useState(initialFormState);
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [showAbbreviations, setShowAbbreviations] = useState(false);

  // Edit Mode State (Requirement 2)
  const [isEditMode, setIsEditMode] = useState(false);
  const [currentEditProposalId, setCurrentEditProposalId] = useState(null);
  const [currentEditToken, setCurrentEditToken] = useState(null);
  const [editLoading, setEditLoading] = useState(false);
  const [editSuccessMsg, setEditSuccessMsg] = useState(null);
  const [copiedLink, setCopiedLink] = useState(false);

  // Compose Email Modal (Requirement 3)
  const [isComposeModalOpen, setIsComposeModalOpen] = useState(false);

  // Dynamic Form Configuration (Requirement 5)
  const [dynamicOptions, setDynamicOptions] = useState({});
  const [customFields, setCustomFields] = useState([]);

  // Fetch dynamic form options on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await api.getFormConfig();
        if (res.success) {
          if (res.categories) setDynamicOptions(res.categories);
          if (res.custom_fields) setCustomFields(res.custom_fields);
        }
      } catch (err) {
        console.warn('Form config offline fallback to defaults:', err);
      }
    };
    fetchConfig();
  }, []);

  // Check URL query parameters or props for edit token
  const loadProposalForEditing = useCallback(async (token, propId) => {
    setEditLoading(true);
    setEditSuccessMsg(null);
    try {
      let p = null;
      if (token) {
        const res = await api.getProposalByToken(token);
        if (res.success && res.proposal) {
          p = res.proposal;
        }
      } else if (propId) {
        const res = await api.getProposalDetail(propId);
        if (res.success && res.proposal) {
          p = res.proposal;
        }
      }

      if (p) {
        setIsEditMode(true);
        setCurrentEditProposalId(p.proposal_id);
        setCurrentEditToken(token || p.edit_token || '');

        let parsedMinors = [];
        if (p.minors) {
          parsedMinors = p.minors.split(',').map(s => s.trim()).filter(Boolean);
        }

        let parsedCustom = {};
        if (p.custom_fields_data) {
          try {
            parsedCustom = typeof p.custom_fields_data === 'string'
              ? JSON.parse(p.custom_fields_data)
              : p.custom_fields_data;
          } catch (e) {
            parsedCustom = {};
          }
        }

        setFormData({
          course_title: p.course_title || '',
          potential_instructors: p.potential_instructors || '',
          proposer_name: p.proposer_name || '',
          faculty_email: p.faculty_email || '',
          additional_recipients: Array.isArray(p.additional_recipients) ? p.additional_recipients.join(', ') : '',
          course_type: p.course_type || 'CS',
          course_type_other: p.course_type_other || '',
          course_level: String(p.course_level || '3'),
          course_level_secondary: p.course_level_secondary || '',
          lecture_hours: p.lecture_hours || 3,
          tutorial_hours: p.tutorial_hours || 0,
          practical_hours: p.practical_hours || 0,
          credits: p.credits || 3,
          course_duration: p.course_duration || '4 Quads (Full Semester)',
          expected_frequency: p.expected_frequency || 'Each Year',
          expected_frequency_other: p.expected_frequency_other || '',
          elective_basket_btech: p.elective_basket_btech || 'None',
          discipline_elective_btech: p.discipline_elective_btech || 'None',
          discipline_basket_btech: p.discipline_basket_btech || '',
          minors: parsedMinors,
          minor_basket_thematic_area: p.minor_basket_thematic_area || '',
          minor_reason: p.minor_reason || '',
          discipline_elective_msc: p.discipline_elective_msc || 'None',
          courses_discipline_mtech: p.courses_discipline_mtech || 'None',
          mtech_sub_specialization: p.mtech_sub_specialization || '',
          discipline_elective_mdes: p.discipline_elective_mdes || 'None',
          is_modification: Boolean(p.is_modification),
          existing_course_code: p.existing_course_code || '',
          prior_knowledge: p.prior_knowledge || '',
          course_contents: p.course_contents || '',
          texts_and_references: p.texts_and_references || '',
          learning_outcomes: p.learning_outcomes || '',
          overlap_courses: p.overlap_courses || '',
          other_relevant_info: p.other_relevant_info || '',
          custom_fields_data: parsedCustom
        });
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } catch (err) {
      alert(err.message || 'Could not load proposal for editing. Invalid or expired token.');
    } finally {
      setEditLoading(false);
    }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get('edit_token');
    const propIdFromUrl = params.get('proposal_id');

    if (tokenFromUrl) {
      loadProposalForEditing(tokenFromUrl, propIdFromUrl);
    } else if (editProposalId) {
      loadProposalForEditing(editToken, editProposalId);
    }
  }, [editProposalId, editToken, loadProposalForEditing]);

  // Dynamic Options Resolution helpers
  const getOptionsList = (categoryKey, fallbackList) => {
    if (dynamicOptions && dynamicOptions[categoryKey] && dynamicOptions[categoryKey].length > 0) {
      const list = dynamicOptions[categoryKey].map(o => o.value);
      // Ensure current form value is included even if inactive
      const curr = formData[categoryKey];
      if (curr && !list.includes(curr) && curr !== 'None') {
        list.push(curr);
      }
      return list;
    }
    return fallbackList;
  };

  const activeCourseTypes = getOptionsList('course_type', COURSE_TYPES);
  const activeCourseLevels = getOptionsList('course_level', COURSE_LEVELS);
  const activeDurations = getOptionsList('course_duration', COURSE_DURATIONS);
  const activeFrequencies = getOptionsList('expected_frequency', OFFERING_FREQUENCIES);
  const activeBtechBaskets = getOptionsList('elective_basket_btech', BTECH_ELECTIVE_BASKETS);
  const activeBtechElectives = getOptionsList('discipline_elective_btech', BTECH_DISCIPLINE_ELECTIVES);
  const activeMinors = getOptionsList('minors', MINORS_LIST);
  const activeMscElectives = getOptionsList('discipline_elective_msc', MSC_ELECTIVES);
  const activeMtechDisciplines = getOptionsList('courses_discipline_mtech', MTECH_DISCIPLINES);
  const activeMdesElectives = getOptionsList('discipline_elective_mdes', MDES_ELECTIVES);

  // Field change handler
  const handleChange = (field, value) => {
    setFormData(prev => {
      const updated = { ...prev, [field]: value };

      if (['lecture_hours', 'tutorial_hours', 'practical_hours'].includes(field)) {
        const l = field === 'lecture_hours' ? Number(value) : Number(prev.lecture_hours);
        const t = field === 'tutorial_hours' ? Number(value) : Number(prev.tutorial_hours);
        const p = field === 'practical_hours' ? Number(value) : Number(prev.practical_hours);
        const calculatedCredits = l + t + Math.round(p * 0.5);
        updated.credits = Math.max(1, calculatedCredits);
      }

      return updated;
    });

    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleCustomFieldChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      custom_fields_data: {
        ...(prev.custom_fields_data || {}),
        [fieldName]: value
      }
    }));
  };

  // Toggle minor selection
  const handleMinorToggle = (minorCode) => {
    setFormData(prev => {
      const current = prev.minors || [];
      const updated = current.includes(minorCode)
        ? current.filter(m => m !== minorCode)
        : [...current, minorCode];
      return { ...prev, minors: updated };
    });
  };

  // Validate form client-side
  const validateForm = () => {
    const errs = {};
    if (!formData.course_title.trim()) errs.course_title = 'Title of the Course is required.';
    if (!formData.potential_instructors.trim()) errs.potential_instructors = 'Name of Potential Instructor(s) is required.';
    if (!formData.proposer_name.trim()) errs.proposer_name = 'Name of Proposer is required.';
    
    if (!formData.faculty_email.trim()) {
      errs.faculty_email = 'Faculty / Recipient Email is required for notification.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.faculty_email)) {
      errs.faculty_email = 'Please enter a valid institutional email address.';
    }

    if (formData.additional_recipients && formData.additional_recipients.trim()) {
      const rawRecips = formData.additional_recipients.split(/[,;\n]/).map(s => s.trim()).filter(Boolean);
      if (rawRecips.length > 10) {
        errs.additional_recipients = 'A maximum of 10 additional recipients is allowed.';
      } else {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        for (const email of rawRecips) {
          if (!emailRegex.test(email)) {
            errs.additional_recipients = `Invalid email address: '${email}'. Please enter valid email addresses separated by commas.`;
            break;
          }
        }
      }
    }

    if (formData.course_type === 'Others' && !formData.course_type_other.trim()) {
      errs.course_type_other = 'Please specify other course type.';
    }

    if (formData.expected_frequency === 'Others' && !formData.expected_frequency_other.trim()) {
      errs.expected_frequency_other = 'Please specify offering frequency.';
    }

    if (formData.is_modification && !formData.existing_course_code.trim()) {
      errs.existing_course_code = 'Existing Course Code is required for course modifications.';
    }

    if (!formData.course_contents.trim()) {
      errs.course_contents = 'Course Contents are required (one paragraph separated by semicolons).';
    } else if (formData.course_contents.trim().length < 20) {
      errs.course_contents = 'Course Contents must be detailed (at least 20 characters).';
    }

    if (!formData.texts_and_references.trim()) {
      errs.texts_and_references = 'Texts and References in standard format (MLA, APA etc.) are required.';
    }

    if (!formData.learning_outcomes.trim()) {
      errs.learning_outcomes = 'Learning Outcomes are required.';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // Form Submit
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (isSubmissionClosed && !isEditMode && !currentUser) {
      alert('Course proposal submissions are currently closed.');
      return;
    }

    if (!validateForm()) {
      const firstError = document.querySelector('.is-invalid');
      if (firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    setIsSubmitting(true);
    setErrors({});
    setEditSuccessMsg(null);

    try {
      const payload = {
        ...formData,
        additional_recipients: formData.additional_recipients ? formData.additional_recipients.trim() : '',
        course_l_t_p_c: `${formData.lecture_hours}-${formData.tutorial_hours}-${formData.practical_hours}-${formData.credits}`,
        minors: formData.minors.length > 0 ? formData.minors.join(', ') : null,
        elective_basket_btech: formData.elective_basket_btech === 'None' ? null : formData.elective_basket_btech,
        discipline_elective_btech: formData.discipline_elective_btech === 'None' ? null : formData.discipline_elective_btech,
        discipline_elective_msc: formData.discipline_elective_msc === 'None' ? null : formData.discipline_elective_msc,
        courses_discipline_mtech: formData.courses_discipline_mtech === 'None' ? null : formData.courses_discipline_mtech,
        discipline_elective_mdes: formData.discipline_elective_mdes === 'None' ? null : formData.discipline_elective_mdes,
        custom_fields_data: formData.custom_fields_data || {}
      };

      if (isEditMode && currentEditProposalId) {
        // Edit mode update
        const authKey = currentEditToken || localStorage.getItem('sapc_token');
        const res = await api.updateProposal(currentEditProposalId, payload, authKey);
        setEditSuccessMsg(`Proposal ${currentEditProposalId} updated successfully! The official ACAD-SAPC-01 PDF has been regenerated.`);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        if (onSubmissionSuccess) onSubmissionSuccess(res.proposal);
      } else {
        // New Proposal submission
        const res = await api.submitProposal(payload);
        setSubmissionResult(res);
        if (onSubmissionSuccess) onSubmissionSuccess(res.proposal);
      }
    } catch (err) {
      if (err.data && err.data.errors) {
        setErrors(err.data.errors);
      } else {
        alert(err.message || 'Submission failed. Please check connection and try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Exit edit mode
  const handleExitEdit = () => {
    setIsEditMode(false);
    setCurrentEditProposalId(null);
    setCurrentEditToken(null);
    setFormData(initialFormState);
    setEditSuccessMsg(null);
    setErrors({});
    if (onCancelEdit) onCancelEdit();
    // Clear URL params without full page reload
    const url = new URL(window.location.href);
    url.searchParams.delete('edit_token');
    url.searchParams.delete('proposal_id');
    window.history.replaceState({}, '', url.pathname);
  };

  // Reset for another proposal
  const handleReset = () => {
    setFormData(initialFormState);
    setSubmissionResult(null);
    setIsEditMode(false);
    setCurrentEditProposalId(null);
    setCurrentEditToken(null);
    setErrors({});
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const copyEditLinkToClipboard = (url) => {
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  // If already submitted successfully, display official confirmation screen
  if (submissionResult) {
    const p = submissionResult.proposal;
    const emailStatus = submissionResult.email_notification?.status;
    const secStatus = submissionResult.security_notification?.status;
    const editTokenVal = submissionResult.edit_token || p.edit_token;
    const editUrl = `${window.location.origin}/?edit_token=${encodeURIComponent(editTokenVal)}&proposal_id=${encodeURIComponent(p.proposal_id)}`;

    return (
      <div className="paper-card" style={{ maxWidth: 840, margin: '20px auto', textAlign: 'center' }}>
        <div style={{ display: 'inline-flex', padding: 16, background: '#dcfce7', borderRadius: '50%', color: '#15803d', marginBottom: 16 }}>
          <CheckCircle size={48} />
        </div>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: '#002147', marginBottom: 8 }}>
          Course Proposal Submitted Successfully!
        </h2>
        <p style={{ color: '#475569', fontSize: 15, marginBottom: 20 }}>
          Your proposal has been logged in the SAPC Academic Office database and the official PDF has been generated.
        </p>

        {/* Proposal Summary Card */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 20, textAlign: 'left', margin: '0 auto 20px', maxWidth: 660 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 10, borderBottom: '1px solid #e2e8f0', marginBottom: 10 }}>
            <span style={{ fontWeight: 600, color: '#475569' }}>Proposal ID:</span>
            <span style={{ fontWeight: 800, color: '#002147', fontFamily: 'monospace', fontSize: 16 }}>{p.proposal_id}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 10, borderBottom: '1px solid #e2e8f0', marginBottom: 10 }}>
            <span style={{ fontWeight: 600, color: '#475569' }}>Course Title:</span>
            <span style={{ fontWeight: 700 }}>{p.course_title}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 10, borderBottom: '1px solid #e2e8f0', marginBottom: 10 }}>
            <span style={{ fontWeight: 600, color: '#475569' }}>Proposer:</span>
            <span>{p.proposer_name}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 10, borderBottom: '1px solid #e2e8f0', marginBottom: 10 }}>
            <span style={{ fontWeight: 600, color: '#475569' }}>Faculty Recipient Email:</span>
            <span>{p.faculty_email}</span>
          </div>
          {p.additional_recipients && p.additional_recipients.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 10, borderBottom: '1px solid #e2e8f0', marginBottom: 10 }}>
              <span style={{ fontWeight: 600, color: '#475569' }}>Additional Recipients (CC):</span>
              <span style={{ fontSize: 13, color: '#1e293b' }}>{p.additional_recipients.join(', ')}</span>
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 10, borderBottom: '1px solid #e2e8f0', marginBottom: 10 }}>
            <span style={{ fontWeight: 600, color: '#475569' }}>Email Notification:</span>
            <span className={`badge ${emailStatus === 'Sent' ? 'badge-approved' : 'badge-pending'}`}>
              {emailStatus === 'Sent' ? 'Notification Dispatched' : 'Notification Logged'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 10, borderBottom: '1px solid #e2e8f0', marginBottom: 10 }}>
            <span style={{ fontWeight: 600, color: '#475569' }}>Security Dept Notification:</span>
            <span className={`badge ${secStatus === 'Sent' ? 'badge-approved' : 'badge-pending'}`}>
              {secStatus === 'Sent' ? 'Dispatched to Security Dept' : 'Security Logged'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 600, color: '#475569' }}>Initial Status:</span>
            <span className="badge badge-pending">Pending SAPC Review</span>
          </div>
        </div>

        {/* Secure Edit Link Container (Requirement 2) */}
        {editTokenVal && (
          <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8, padding: 18, textAlign: 'left', margin: '0 auto 24px', maxWidth: 660 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#0369a1', fontWeight: 700, fontSize: 14, marginBottom: 4 }}>
              <Edit3 size={16} />
              <span>Professor Secure Proposal Edit Access (Unguessable URL)</span>
            </div>
            <div style={{ fontSize: 12.5, color: '#0c4a6e', marginBottom: 10 }}>
              Save this unique link to update or correct your proposal prior to the deadline:
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="text"
                readOnly
                value={editUrl}
                className="form-control"
                style={{ fontSize: 12, background: '#ffffff', color: '#0369a1', fontFamily: 'monospace' }}
              />
              <button
                type="button"
                onClick={() => copyEditLinkToClipboard(editUrl)}
                className="btn btn-secondary btn-sm"
                style={{ minWidth: 100 }}
              >
                {copiedLink ? (
                  <>
                    <Check size={14} color="#16a34a" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={14} />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Action Buttons (Requirements 1, 2, 3) */}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
          {/* Feature 1: Download Official PDF */}
          <a
            href={api.getPdfDownloadUrl(p.proposal_id)}
            className="btn btn-primary"
            download={`${p.proposal_id}.pdf`}
          >
            <Download size={16} />
            <span>Download Official PDF</span>
          </a>

          <a
            href={api.getPdfViewUrl(p.proposal_id)}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
          >
            <ExternalLink size={16} />
            <span>View PDF</span>
          </a>

          {/* Feature 3: Compose Email */}
          <button
            onClick={() => setIsComposeModalOpen(true)}
            className="btn btn-secondary"
          >
            <Mail size={16} />
            <span>Compose & Send Email</span>
          </button>

          {/* Feature 2: Edit Proposal Now */}
          {editTokenVal && (
            <button
              onClick={() => loadProposalForEditing(editTokenVal, p.proposal_id)}
              className="btn btn-secondary"
            >
              <Edit3 size={16} />
              <span>Edit Proposal</span>
            </button>
          )}

          <button onClick={handleReset} className="btn btn-secondary">
            <RefreshCw size={16} />
            <span>Submit Another</span>
          </button>
        </div>

        {/* Compose Email Modal */}
        <EmailComposeModal
          isOpen={isComposeModalOpen}
          onClose={() => setIsComposeModalOpen(false)}
          proposal={p}
          authKey={editTokenVal}
        />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="paper-card">
        {/* Active Edit Mode Banner (Requirement 2) */}
        {isEditMode && (
          <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 6, padding: '12px 18px', marginBottom: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ background: '#1d4ed8', color: '#ffffff', padding: 6, borderRadius: '50%' }}>
                <Edit3 size={16} />
              </div>
              <div>
                <strong style={{ color: '#1e3a8a', fontSize: 14 }}>
                  Editing Submitted Proposal: {currentEditProposalId}
                </strong>
                <div style={{ fontSize: 12, color: '#3b82f6' }}>
                  {currentUser ? 'Editing with Academic Office Authority' : 'Editing with Secure Authorization Token'}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <a
                href={api.getPdfDownloadUrl(currentEditProposalId)}
                className="btn btn-secondary btn-sm"
                download={`${currentEditProposalId}.pdf`}
              >
                <Download size={13} />
                <span>Download Current PDF</span>
              </a>
              <button
                type="button"
                onClick={() => setIsComposeModalOpen(true)}
                className="btn btn-secondary btn-sm"
              >
                <Mail size={13} />
                <span>Email Proposal</span>
              </button>
              <button
                type="button"
                onClick={handleExitEdit}
                className="btn btn-secondary btn-sm"
              >
                <ArrowLeft size={13} />
                <span>Cancel Editing</span>
              </button>
            </div>
          </div>
        )}

        {editSuccessMsg && (
          <div style={{ background: '#dcfce7', border: '1px solid #86efac', color: '#166534', padding: '12px 16px', borderRadius: 6, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 10, fontSize: 13.5 }}>
            <CheckCircle size={18} />
            <span>{editSuccessMsg}</span>
          </div>
        )}

        {/* Academic Header reproduced from ACAD-SAPC-01 */}
        <div className="paper-header">
          <div className="institute-name">INDIAN INSTITUTE OF TECHNOLOGY GANDHINAGAR</div>
          <div className="academic-office-sub">
            Academic Office — Senate Academic Programme Committee (SAPC)
          </div>
          <div className="form-title">
            {isEditMode ? `UPDATE COURSE PROPOSAL (${currentEditProposalId})` : 'Proposal for New Courses / Modification of Existing Courses'}
          </div>
          <div className="form-code">ACAD-SAPC-01</div>
        </div>

        {/* Section 1: Course Identity */}
        <div className="form-section">
          <div className="section-legend">
            <span className="section-legend-number">1</span>
            <span>Course Identification & Proposer Information</span>
          </div>

          <div className="form-group">
            <label className="form-label">
              <span>Title of the Course <span className="req">*</span></span>
              <span className="optional">(as it will appear on official transcripts)</span>
            </label>
            <input
              type="text"
              className={`form-control ${errors.course_title ? 'is-invalid' : ''}`}
              placeholder="e.g. Distributed Systems and Cloud Computing"
              value={formData.course_title}
              onChange={e => handleChange('course_title', e.target.value)}
              disabled={isSubmissionClosed && !isEditMode && !currentUser}
            />
            {errors.course_title && <div className="invalid-feedback">{errors.course_title}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">
              <span>Name of Potential Instructor(s) <span className="req">*</span></span>
              <span className="optional">(separate multiple instructors with semicolons)</span>
            </label>
            <input
              type="text"
              className={`form-control ${errors.potential_instructors ? 'is-invalid' : ''}`}
              placeholder="e.g. Dr. Vikram Sharma; Dr. Ananya Sen"
              value={formData.potential_instructors}
              onChange={e => handleChange('potential_instructors', e.target.value)}
              disabled={isSubmissionClosed && !isEditMode && !currentUser}
            />
            {errors.potential_instructors && <div className="invalid-feedback">{errors.potential_instructors}</div>}
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">
                <span>Name of Proposer <span className="req">*</span></span>
              </label>
              <input
                type="text"
                className={`form-control ${errors.proposer_name ? 'is-invalid' : ''}`}
                placeholder="e.g. Dr. Vikram Sharma"
                value={formData.proposer_name}
                onChange={e => handleChange('proposer_name', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              />
              {errors.proposer_name && <div className="invalid-feedback">{errors.proposer_name}</div>}
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Faculty / Recipient Email <span className="req">*</span></span>
                <span className="optional">(receives official PDF copy & notifications)</span>
              </label>
              <input
                type="email"
                className={`form-control ${errors.faculty_email ? 'is-invalid' : ''}`}
                placeholder="e.g. vikram.sharma@iitgn.ac.in"
                value={formData.faculty_email}
                onChange={e => handleChange('faculty_email', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              />
              {errors.faculty_email && <div className="invalid-feedback">{errors.faculty_email}</div>}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              <span>Additional Recipients (CC)</span>
              <span className="optional">(optional — comma-separated email addresses for HOD, discipline colleagues)</span>
            </label>
            <input
              type="text"
              className={`form-control ${errors.additional_recipients ? 'is-invalid' : ''}`}
              placeholder="e.g. hod.cse@iitgn.ac.in, colleague@iitgn.ac.in"
              value={formData.additional_recipients}
              onChange={e => handleChange('additional_recipients', e.target.value)}
              disabled={isSubmissionClosed && !isEditMode && !currentUser}
            />
            {errors.additional_recipients && <div className="invalid-feedback">{errors.additional_recipients}</div>}
          </div>

          {/* Course Modification Checkbox */}
          <div style={{ marginTop: 12, padding: '12px 16px', background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', margin: 0 }}>
              <input
                type="checkbox"
                checked={formData.is_modification}
                onChange={e => handleChange('is_modification', e.target.checked)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
                style={{ width: 18, height: 18 }}
              />
              <span style={{ fontWeight: 600, fontSize: 13.5, color: '#1e293b' }}>
                This is a Modification of an Existing Approved Course (ACAD-SAPC-01 Part 1)
              </span>
            </label>

            {formData.is_modification && (
              <div style={{ marginTop: 10, paddingLeft: 28 }}>
                <label className="form-label">
                  <span>Existing Course Code <span className="req">*</span></span>
                  <span className="optional">(e.g. CS202, ES112)</span>
                </label>
                <input
                  type="text"
                  className={`form-control ${errors.existing_course_code ? 'is-invalid' : ''}`}
                  placeholder="e.g. CS202"
                  value={formData.existing_course_code}
                  onChange={e => handleChange('existing_course_code', e.target.value)}
                  style={{ maxWidth: 300 }}
                  disabled={isSubmissionClosed && !isEditMode && !currentUser}
                />
                {errors.existing_course_code && <div className="invalid-feedback">{errors.existing_course_code}</div>}
              </div>
            )}
          </div>
        </div>

        {/* Section 2: Structure, Level, L-T-P-C */}
        <div className="form-section">
          <div className="section-legend">
            <span className="section-legend-number">2</span>
            <span>Classification, Level, Contact Hours (L-T-P-C) & Duration</span>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">
                <span>Course Type (✓ One) <span className="req">*</span></span>
              </label>
              <select
                className="form-control"
                value={formData.course_type}
                onChange={e => handleChange('course_type', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              >
                {activeCourseTypes.map(t => (
                  <option key={t} value={t}>{t} — {DISCIPLINE_ABBREVIATIONS[t] || t}</option>
                ))}
              </select>
              {formData.course_type === 'Others' && (
                <div style={{ marginTop: 8 }}>
                  <input
                    type="text"
                    className={`form-control ${errors.course_type_other ? 'is-invalid' : ''}`}
                    placeholder="Specify Course Type"
                    value={formData.course_type_other}
                    onChange={e => handleChange('course_type_other', e.target.value)}
                    disabled={isSubmissionClosed && !isEditMode && !currentUser}
                  />
                  {errors.course_type_other && <div className="invalid-feedback">{errors.course_type_other}</div>}
                </div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Course Level (✓ One) <span className="req">*</span></span>
                <span className="optional">(Level 1–5: UG, Level 6: PG)</span>
              </label>
              <div style={{ display: 'flex', gap: 10 }}>
                <select
                  className="form-control"
                  value={formData.course_level}
                  onChange={e => handleChange('course_level', e.target.value)}
                  disabled={isSubmissionClosed && !isEditMode && !currentUser}
                >
                  {activeCourseLevels.map(lvl => (
                    <option key={lvl} value={lvl}>Level {lvl} {lvl === '6' ? '(PG)' : '(UG)'}</option>
                  ))}
                </select>
                <select
                  className="form-control"
                  value={formData.course_level_secondary}
                  onChange={e => handleChange('course_level_secondary', e.target.value)}
                  disabled={isSubmissionClosed && !isEditMode && !currentUser}
                >
                  <option value="">No Secondary Level</option>
                  {activeCourseLevels.map(lvl => (
                    <option key={lvl} value={lvl}>& Level {lvl}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* L-T-P-C Breakdown */}
          <div className="form-group">
            <label className="form-label">
              <span>Course L-T-P-C Breakdown <span className="req">*</span></span>
              <span className="optional">(L: Lectures, T: Tutorials, P: Practicals/Lab, C: Credits)</span>
            </label>
            <div className="ltpc-input-grid">
              <div>
                <span className="input-hint">L (Lectures/wk)</span>
                <input
                  type="number"
                  min="0"
                  max="10"
                  step="0.5"
                  className="form-control"
                  value={formData.lecture_hours}
                  onChange={e => handleChange('lecture_hours', e.target.value)}
                  disabled={isSubmissionClosed && !isEditMode && !currentUser}
                />
              </div>
              <div>
                <span className="input-hint">T (Tutorials/wk)</span>
                <input
                  type="number"
                  min="0"
                  max="5"
                  step="0.5"
                  className="form-control"
                  value={formData.tutorial_hours}
                  onChange={e => handleChange('tutorial_hours', e.target.value)}
                  disabled={isSubmissionClosed && !isEditMode && !currentUser}
                />
              </div>
              <div>
                <span className="input-hint">P (Practicals/wk)</span>
                <input
                  type="number"
                  min="0"
                  max="12"
                  step="0.5"
                  className="form-control"
                  value={formData.practical_hours}
                  onChange={e => handleChange('practical_hours', e.target.value)}
                  disabled={isSubmissionClosed && !isEditMode && !currentUser}
                />
              </div>
              <div>
                <span className="input-hint">C (Credits)</span>
                <input
                  type="number"
                  min="1"
                  max="20"
                  step="0.5"
                  className="form-control"
                  value={formData.credits}
                  onChange={e => handleChange('credits', e.target.value)}
                  disabled={isSubmissionClosed && !isEditMode && !currentUser}
                />
              </div>
            </div>
          </div>

          {/* Duration & Frequency */}
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">
                <span>Course Duration (✓ One) <span className="req">*</span></span>
              </label>
              <select
                className="form-control"
                value={formData.course_duration}
                onChange={e => handleChange('course_duration', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              >
                {activeDurations.map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Expected Frequency of Offering (✓ One) <span className="req">*</span></span>
              </label>
              <select
                className="form-control"
                value={formData.expected_frequency}
                onChange={e => handleChange('expected_frequency', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              >
                {activeFrequencies.map(f => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Section 3: Curricular Electives, Baskets & Minors */}
        <div className="form-section">
          <div className="section-legend">
            <span className="section-legend-number">3</span>
            <span>Curricular Classifications, Elective Baskets & Minors</span>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">
                <span>Elective Basket for BTech</span>
                <span className="optional">(✓ One, if applicable)</span>
              </label>
              <select
                className="form-control"
                value={formData.elective_basket_btech}
                onChange={e => handleChange('elective_basket_btech', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              >
                {activeBtechBaskets.map(b => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Discipline-specific Elective for BTech</span>
                <span className="optional">(✓ One, if applicable)</span>
              </label>
              <select
                className="form-control"
                value={formData.discipline_elective_btech}
                onChange={e => handleChange('discipline_elective_btech', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              >
                {activeBtechElectives.map(d => (
                  <option key={d} value={d}>{d} — {DISCIPLINE_ABBREVIATIONS[d] || d}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Minor(s) in */}
          <div className="form-group">
            <label className="form-label">
              <span>Minor(s) in</span>
              <span className="optional">(✓, if applicable — select all relevant minors)</span>
            </label>
            <div className="minor-chips-grid">
              {activeMinors.map(m => {
                const isSelected = formData.minors.includes(m);
                return (
                  <div
                    key={m}
                    className={`option-chip ${isSelected ? 'selected' : ''}`}
                    onClick={() => (!isSubmissionClosed || isEditMode || currentUser) && handleMinorToggle(m)}
                    title={DISCIPLINE_ABBREVIATIONS[m] || m}
                  >
                    {m}
                  </div>
                );
              })}
            </div>
            <div style={{ marginTop: 8 }}>
              <input
                type="text"
                className="form-control"
                placeholder="Basket / Thematic Area for Minor (if applicable)"
                value={formData.minor_basket_thematic_area}
                onChange={e => handleChange('minor_basket_thematic_area', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              />
            </div>

            {/* Requirement 4: Reason for Adding the Course as a Minor */}
            <div style={{ marginTop: 12 }}>
              <label className="form-label" style={{ fontSize: 13, fontWeight: 700, color: '#002147' }}>
                <span>Reason for Adding the Course as a Minor</span>
                <span className="optional">(multiline rationale and academic justification)</span>
              </label>
              <textarea
                className="form-control"
                rows={3}
                placeholder="Explain the curricular relevance, prerequisites, and justification for offering this course as part of the minor..."
                value={formData.minor_reason}
                onChange={e => handleChange('minor_reason', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              />
            </div>
          </div>

          {/* PG Curricular Fields */}
          <div className="grid-3">
            <div className="form-group">
              <label className="form-label">
                <span>Elective for MSc</span>
              </label>
              <select
                className="form-control"
                value={formData.discipline_elective_msc}
                onChange={e => handleChange('discipline_elective_msc', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              >
                {activeMscElectives.map(m => (
                  <option key={m} value={m}>{m} — {DISCIPLINE_ABBREVIATIONS[m] || m}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Courses for MTech</span>
              </label>
              <select
                className="form-control"
                value={formData.courses_discipline_mtech}
                onChange={e => handleChange('courses_discipline_mtech', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              >
                {activeMtechDisciplines.map(m => (
                  <option key={m} value={m}>{m} — {DISCIPLINE_ABBREVIATIONS[m] || m}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Elective for MDes</span>
              </label>
              <select
                className="form-control"
                value={formData.discipline_elective_mdes}
                onChange={e => handleChange('discipline_elective_mdes', e.target.value)}
                disabled={isSubmissionClosed && !isEditMode && !currentUser}
              >
                {activeMdesElectives.map(m => (
                  <option key={m} value={m}>{m} — {DISCIPLINE_ABBREVIATIONS[m] || m}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Section 4: Course Contents & Academic Syllabus */}
        <div className="form-section">
          <div className="section-legend">
            <span className="section-legend-number">4</span>
            <span>Course Contents & Academic Syllabus</span>
          </div>

          <div className="form-group">
            <label className="form-label">
              <span>Prior Knowledge / Expertise Expected</span>
              <span className="optional">Prerequisites / background knowledge</span>
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="e.g. Basic Probability and Linear Algebra, Data Structures"
              value={formData.prior_knowledge}
              onChange={e => handleChange('prior_knowledge', e.target.value)}
              disabled={isSubmissionClosed && !isEditMode && !currentUser}
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              <span>Course Contents (separated by semicolons) <span className="req">*</span></span>
              <span className="optional">Detailed bulleted topics</span>
            </label>
            <textarea
              className={`form-control ${errors.course_contents ? 'is-invalid' : ''}`}
              rows={4}
              placeholder="Introduction to core concepts; Architecture and components; Algorithms; Case studies; Experimental design."
              value={formData.course_contents}
              onChange={e => handleChange('course_contents', e.target.value)}
              disabled={isSubmissionClosed && !isEditMode && !currentUser}
            />
            {errors.course_contents && <div className="invalid-feedback">{errors.course_contents}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">
              <span>Texts and References <span className="req">*</span></span>
              <span className="optional">(MLA / APA format)</span>
            </label>
            <textarea
              className={`form-control ${errors.texts_and_references ? 'is-invalid' : ''}`}
              rows={3}
              placeholder="Author(s), Title, Publisher, Edition, Year."
              value={formData.texts_and_references}
              onChange={e => handleChange('texts_and_references', e.target.value)}
              disabled={isSubmissionClosed && !isEditMode && !currentUser}
            />
            {errors.texts_and_references && <div className="invalid-feedback">{errors.texts_and_references}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">
              <span>Learning Outcomes <span className="req">*</span></span>
              <span className="optional">(Cognitive / practical outcomes)</span>
            </label>
            <textarea
              className={`form-control ${errors.learning_outcomes ? 'is-invalid' : ''}`}
              rows={3}
              placeholder="Upon completing this course, students will be able to..."
              value={formData.learning_outcomes}
              onChange={e => handleChange('learning_outcomes', e.target.value)}
              disabled={isSubmissionClosed && !isEditMode && !currentUser}
            />
            {errors.learning_outcomes && <div className="invalid-feedback">{errors.learning_outcomes}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">
              <span>Overlap with Other Approved Courses</span>
              <span className="optional">Course code, title, and overlap percentage</span>
            </label>
            <textarea
              className="form-control"
              rows={2}
              placeholder="State any overlap or note 'None / No significant overlap with existing courses.'"
              value={formData.overlap_courses}
              onChange={e => handleChange('overlap_courses', e.target.value)}
              disabled={isSubmissionClosed && !isEditMode && !currentUser}
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              <span>Any Other Relevant Information Not Covered Above</span>
              <span className="optional">Applications of concepts, industry relevance</span>
            </label>
            <textarea
              className="form-control"
              rows={2}
              placeholder="Industrial relevance, lab setup requirements, software tools used, etc."
              value={formData.other_relevant_info}
              onChange={e => handleChange('other_relevant_info', e.target.value)}
              disabled={isSubmissionClosed && !isEditMode && !currentUser}
            />
          </div>
        </div>

        {/* Section 5: Dynamic Custom Fields (Requirement 5) */}
        {customFields && customFields.length > 0 && (
          <div className="form-section">
            <div className="section-legend">
              <span className="section-legend-number">5</span>
              <span>Additional Institutional Information (Custom Fields)</span>
            </div>
            <div className="grid-2">
              {customFields.map(cf => (
                <div key={cf.id} className="form-group">
                  <label className="form-label">
                    <span>{cf.field_label}</span>
                    {cf.is_required ? <span className="req">*</span> : <span className="optional">(optional)</span>}
                  </label>
                  {cf.field_type === 'textarea' ? (
                    <textarea
                      className="form-control"
                      rows={2}
                      value={formData.custom_fields_data?.[cf.field_name] || ''}
                      onChange={e => handleCustomFieldChange(cf.field_name, e.target.value)}
                      disabled={isSubmissionClosed && !isEditMode && !currentUser}
                    />
                  ) : (
                    <input
                      type={cf.field_type === 'number' ? 'number' : 'text'}
                      className="form-control"
                      value={formData.custom_fields_data?.[cf.field_name] || ''}
                      onChange={e => handleCustomFieldChange(cf.field_name, e.target.value)}
                      disabled={isSubmissionClosed && !isEditMode && !currentUser}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Institutional Sign-off Footer */}
        <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: 6, padding: '12px 16px', fontSize: 12, color: '#475569', marginBottom: 24 }}>
          <strong>Institutional Governance Notice:</strong> Course proposals are to be approved by the Chairman, Senate on recommendation of the SAPC.<br />
          Completed proposals are officially routed to <u>ar.ug@iitgn.ac.in</u>, with a copy to <u>doaa@iitgn.ac.in</u> and <u>security@iitgn.ac.in</u>.
        </div>

        {/* Form Action Controls */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, alignItems: 'center' }}>
          {isSubmissionClosed && !isEditMode && !currentUser ? (
            <div style={{ color: '#dc2626', fontWeight: 700, fontSize: 13.5, display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertCircle size={16} />
              <span>Course proposal submissions are currently closed.</span>
            </div>
          ) : (
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting || editLoading}
              style={{ minWidth: 220 }}
            >
              {isSubmitting ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  <span>{isEditMode ? 'Updating & Regenerating PDF...' : 'Processing & Generating PDF...'}</span>
                </>
              ) : isEditMode ? (
                <>
                  <Edit3 size={16} />
                  <span>Save & Update Proposal (ACAD-SAPC-01)</span>
                </>
              ) : (
                <>
                  <Send size={16} />
                  <span>Submit Course Proposal</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Compose Email Modal for Edit Mode */}
      {isEditMode && currentEditProposalId && (
        <EmailComposeModal
          isOpen={isComposeModalOpen}
          onClose={() => setIsComposeModalOpen(false)}
          proposal={{
            proposal_id: currentEditProposalId,
            course_title: formData.course_title,
            proposer_name: formData.proposer_name,
            faculty_email: formData.faculty_email
          }}
          authKey={currentEditToken || (currentUser ? localStorage.getItem('sapc_token') : '')}
        />
      )}
    </form>
  );
}
