export const API_URL =
  process.env.REACT_APP_API_URL || 'http://localhost:8000';

const TOKEN_KEY = 'job_recommender_token';

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const setToken = (token) => {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
};

export const getStoredUser = () => {
  try {
    return JSON.parse(localStorage.getItem('job_recommender_user') || 'null');
  } catch {
    return null;
  }
};

export const setStoredUser = (user) => {
  if (user) localStorage.setItem('job_recommender_user', JSON.stringify(user));
  else localStorage.removeItem('job_recommender_user');
};

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  let body = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    body = await response.json();
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    if (body && typeof body.detail === 'string') message = body.detail;
    else if (body && Array.isArray(body.detail)) {
      message = body.detail.map((e) => e.msg).join('. ');
    }
    if (response.status === 401) {
      setToken(null);
      setStoredUser(null);
    }
    throw new ApiError(message, response.status, body);
  }
  return body;
}

export const api = {
  register: (data) => request('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  login: (data) => request('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  me: () => request('/api/auth/me'),
  listJobs: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
    ).toString();
    return request(`/api/jobs${qs ? `?${qs}` : ''}`);
  },
  searchJobs: (q, location) => {
    const qs = new URLSearchParams({ q });
    if (location) qs.set('location', location);
    return request(`/api/jobs/search?${qs}`);
  },
  getJob: (id) => request(`/api/jobs/${id}`),
  createJob: (data) => request('/api/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  uploadResume: (file) => {
    const form = new FormData();
    form.append('file', file);
    return request('/api/resume/upload', { method: 'POST', body: form });
  },
  analyzeResumeText: (resumeText) => request('/api/resume/analyze-text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_text: resumeText }),
  }),
  getResumeProfile: () => request('/api/resume/profile'),
  getRecommendations: (limit = 10) =>
    request(`/api/resume/recommendations?limit=${limit}`),
  aiStatus: () => request('/api/ai/status'),
};