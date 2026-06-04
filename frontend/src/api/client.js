const BASE = ''  // relative URLs — works in both dev (Vite proxy) and prod (FastAPI)

function authHeaders() {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: authHeaders(),
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Request failed')
  return data
}

export const api = {
  // Auth
  register: (name, email, password) =>
    request('POST', '/auth/register', { name, email, password }),

  login: (email, password) =>
    request('POST', '/auth/login', { email, password }),

  // Chat
  sendMessage: (message, caseId) =>
    request('POST', '/chat/', { message, case_id: caseId || null }),

  resumeSession: (caseId) =>
    fetch(`${BASE}/chat/resume?case_id=${caseId}`, {
      method: 'POST',
      headers: authHeaders(),
    }).then(r => r.json()),

  // Cases
  getCases: () => request('GET', '/cases/'),

  getCase: (caseId) => request('GET', `/cases/${caseId}`),

  // Upload — uses FormData, no JSON
  uploadDocument: async (file, caseId, documentType) => {
    const form = new FormData()
    form.append('file', file)
    form.append('case_id', caseId)
    form.append('document_type', documentType)

    const token = localStorage.getItem('token')
    const res = await fetch(`${BASE}/upload/`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Upload failed')
    return data
  },
}
