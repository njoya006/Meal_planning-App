// Minimal CSRF helpers for ChopSmo frontend
// Usage:
// 1) Include this script on pages that perform API calls.
//    <script src="/static/js/csrf_helpers.js"></script>
// 2) Ensure you call fetchCsrfToken() once at app load to guarantee the csrftoken cookie exists.
// 3) Use loginWithEmail(email,password) to perform a login POST that includes cookies and X-CSRFToken.

function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return match ? match.pop() : null;
}

async function fetchCsrfToken() {
  try {
    // Calls the API endpoint that ensures a CSRF cookie is set (server provides /api/csrf-token/)
    await fetch('/api/csrf-token/', {
      method: 'GET',
      credentials: 'include'
    });
    return getCookie('csrftoken');
  } catch (e) {
    console.warn('fetchCsrfToken failed', e);
    return null;
  }
}

async function loginWithEmail(email, password, opts = {}) {
  const url = opts.url || '/api/users/login/';
  let csrftoken = getCookie('csrftoken');
  if (!csrftoken) {
    csrftoken = await fetchCsrfToken();
  }

  const res = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: Object.assign({
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken || ''
    }, opts.headers || {}),
    body: JSON.stringify({ email, password })
  });

  // Return the response (caller can parse JSON or check status)
  return res;
}

// Expose helpers globally for quick console testing
window.CsrfHelpers = {
  getCookie,
  fetchCsrfToken,
  loginWithEmail
};

// Auto-run a csrf token fetch in the background (non-blocking) so pages that include
// this file will proactively obtain a csrftoken cookie.
(async function prefetch() {
  try { await fetchCsrfToken(); } catch (e) { /* ignore */ }
})();
