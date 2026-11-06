// API Service Client for SAPC Course Proposal System

const BASE_URL = '/api';

export const api = {
  // Deadline & Submission Window
  async getDeadline() {
    const res = await fetch(`${BASE_URL}/deadline`);
    if (!res.ok) throw new Error('Failed to fetch deadline status');
    return res.json();
  },

  async updateDeadline(payload, token) {
    const res = await fetch(`${BASE_URL}/deadline`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || data.message || 'Failed to update deadline');
    return data;
  },

  // Proposals
  async submitProposal(payload) {
    const res = await fetch(`${BASE_URL}/proposals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      const err = new Error(data.message || data.error || 'Failed to submit proposal');
      err.data = data;
      throw err;
    }
    return data;
  },

  async getProposalByToken(editToken) {
    const res = await fetch(`${BASE_URL}/proposals/by-token/${editToken}`);
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || 'Failed to retrieve proposal with authorization token.');
    }
    return res.json();
  },

  async updateProposal(proposalId, payload, authKey) {
    // authKey can be an Admin Bearer token or proposal edit_token
    const headers = { 'Content-Type': 'application/json' };
    let url = `${BASE_URL}/proposals/${proposalId}`;
    if (authKey) {
      if (authKey.startsWith('eyJ') || authKey.length > 50) {
        // likely JWT token
        headers['Authorization'] = `Bearer ${authKey}`;
      } else {
        // proposal edit token
        url += `?edit_token=${encodeURIComponent(authKey)}`;
      }
    }
    const res = await fetch(url, {
      method: 'PUT',
      headers,
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      const err = new Error(data.message || data.error || 'Failed to update proposal');
      err.data = data;
      throw err;
    }
    return data;
  },

  async getProposals(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, value);
      }
    });

    const res = await fetch(`${BASE_URL}/proposals?${searchParams.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch proposals');
    return res.json();
  },

  async getProposalDetail(proposalId) {
    const res = await fetch(`${BASE_URL}/proposals/${proposalId}`);
    if (!res.ok) throw new Error(`Failed to fetch proposal ${proposalId}`);
    return res.json();
  },

  async getProposalEditHistory(proposalId) {
    const res = await fetch(`${BASE_URL}/proposals/${proposalId}/edit-history`);
    if (!res.ok) throw new Error('Failed to fetch edit history');
    return res.json();
  },

  async getCourseHistory(proposalId) {
    const res = await fetch(`${BASE_URL}/proposals/${proposalId}/course-history`);
    if (!res.ok) throw new Error('Failed to fetch course history');
    return res.json();
  },

  async updateProposalStatus(proposalId, status, remarks, token) {
    const res = await fetch(`${BASE_URL}/proposals/${proposalId}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ status, remarks })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to update status');
    return data;
  },

  async resendNotificationEmail(proposalId, token, type = 'all') {
    const res = await fetch(`${BASE_URL}/proposals/${proposalId}/resend-email?type=${type}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to resend email');
    return data;
  },

  async sendCustomProposalEmail(proposalId, payload, authKey) {
    const headers = { 'Content-Type': 'application/json' };
    let url = `${BASE_URL}/proposals/${proposalId}/send-email`;
    if (authKey) {
      if (authKey.startsWith('eyJ') || authKey.length > 50) {
        headers['Authorization'] = `Bearer ${authKey}`;
      } else {
        url += `?edit_token=${encodeURIComponent(authKey)}`;
      }
    }
    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || data.message || 'Failed to dispatch email');
    return data;
  },

  // Dynamic Form Configuration
  async getFormConfig() {
    const res = await fetch(`${BASE_URL}/form-config`);
    if (!res.ok) throw new Error('Failed to fetch form configuration');
    return res.json();
  },

  async getFormConfigAdmin(token) {
    const res = await fetch(`${BASE_URL}/form-config/admin`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch admin form configuration');
    return res.json();
  },

  async addFormOption(payload, token) {
    const res = await fetch(`${BASE_URL}/form-config/options`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to add option');
    return data;
  },

  async updateFormOption(optionId, payload, token) {
    const res = await fetch(`${BASE_URL}/form-config/options/${optionId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to update option');
    return data;
  },

  async deleteFormOption(optionId, token) {
    const res = await fetch(`${BASE_URL}/form-config/options/${optionId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to delete option');
    return data;
  },

  async addCustomField(payload, token) {
    const res = await fetch(`${BASE_URL}/form-config/custom-fields`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to add custom field');
    return data;
  },

  async updateCustomField(fieldId, payload, token) {
    const res = await fetch(`${BASE_URL}/form-config/custom-fields/${fieldId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to update custom field');
    return data;
  },

  async deleteCustomField(fieldId, token) {
    const res = await fetch(`${BASE_URL}/form-config/custom-fields/${fieldId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to delete custom field');
    return data;
  },

  // Excel Import
  async previewExcelImport(file, token) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/proposals/import/preview`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to preview Excel import');
    return data;
  },

  async confirmExcelImport(rows, token) {
    const res = await fetch(`${BASE_URL}/proposals/import/confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ rows })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to confirm Excel import');
    return data;
  },

  getExcelImportTemplateUrl() {
    return `${BASE_URL}/proposals/import/template`;
  },

  // Auth
  async login(username, password) {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Login failed');
    return data;
  },

  async getCurrentUser(token) {
    const res = await fetch(`${BASE_URL}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Unauthorized');
    return res.json();
  },

  async getEmailOutbox(token) {
    const res = await fetch(`${BASE_URL}/auth/outbox`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to retrieve email logs');
    return res.json();
  },

  // Helpers for direct download links
  getPdfDownloadUrl(proposalId) {
    return `${BASE_URL}/proposals/${proposalId}/pdf`;
  },

  getPdfViewUrl(proposalId) {
    return `${BASE_URL}/proposals/${proposalId}/pdf/view`;
  },

  getExportUrl(format = 'xlsx', params = {}, token = '') {
    const searchParams = new URLSearchParams({ format });
    if (token) searchParams.append('token', token);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '' && key !== 'page' && key !== 'per_page') {
        searchParams.append(key, value);
      }
    });
    return `${BASE_URL}/proposals/export?${searchParams.toString()}`;
  }
};
