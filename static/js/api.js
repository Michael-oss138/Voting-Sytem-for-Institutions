// ── api.js ── fetch wrapper + shared UI helpers

async function apiFetch(endpoint, options = {}) {
  const token = getAccessToken();
  const res = await fetch(endpoint, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  // Auto-redirect on 401
  if (res.status === 401) { clearTokens(); window.location.href = '/'; }
  return res;
}

function apiGet(endpoint)         { return apiFetch(endpoint, { method: 'GET' }); }
function apiPost(endpoint, body)  { return apiFetch(endpoint, { method: 'POST', body: JSON.stringify(body) }); }

// ── UI helpers ──

function showAlert(id, msg, type = 'error') {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `alert alert-${type} show`;
  if (type !== 'error') setTimeout(() => el.classList.remove('show'), 4500);
}

function statusBadge(status) {
  const labels = { opened: 'Open', closed: 'Closed', draft: 'Draft', approved: 'Approved', rejected: 'Rejected' };
  return `<span class="badge badge-${status}">${labels[status] || status}</span>`;
}

function formatDate(str) {
  if (!str) return '—';
  return new Date(str).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
}

function setLoading(btnId, loading, defaultText) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading ? 'Please wait…' : defaultText;
}
