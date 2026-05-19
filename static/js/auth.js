// ── auth.js ── Token & session helpers

const _KEYS = { access: 'cu_access', refresh: 'cu_refresh', user: 'cu_user' };

function getAccessToken()  { return localStorage.getItem(_KEYS.access); }
function getRefreshToken() { return localStorage.getItem(_KEYS.refresh); }

function setTokens(access, refresh) {
  localStorage.setItem(_KEYS.access, access);
  localStorage.setItem(_KEYS.refresh, refresh);
}

function clearTokens() {
  Object.values(_KEYS).forEach(k => localStorage.removeItem(k));
}

function setUser(obj) {
  localStorage.setItem(_KEYS.user, JSON.stringify(obj));
}

function getUser() {
  try { return JSON.parse(localStorage.getItem(_KEYS.user)); } catch { return null; }
}

function isLoggedIn() { return !!getAccessToken(); }

function decodeToken(token) {
  try { return JSON.parse(atob(token.split('.')[1])); } catch { return null; }
}

function requireAuth() {
  if (!isLoggedIn()) window.location.href = '/';
}

function redirectIfLoggedIn() {
  if (isLoggedIn()) window.location.href = '/dashboard/';
}
