/**
 * Shared API helper for REST calls.
 * All mutations (create/update/advance) go through /api/ endpoints.
 */

/**
 * Call a REST API endpoint, show spinner, handle errors.
 * @param {string} url
 * @param {string} method  GET|POST|PUT|DELETE
 * @param {object|FormData|null} body
 * @returns {Promise<object>} parsed JSON response
 */
async function apiCall(url, method, body) {
  const opts = { method: method || 'GET', headers: {} };
  if (body instanceof FormData) {
    opts.body = body;                       // browser sets multipart Content-Type
  } else if (body !== null && body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const resp = await fetch(url, opts);
  let data;
  try { data = await resp.json(); } catch { data = {}; }
  if (!resp.ok) {
    const msg = data.error || `HTTP ${resp.status}`;
    const err = new Error(msg);
    err.details = data.details || null;
    throw err;
  }
  return data;
}

/**
 * Submit a regular HTML form via the REST API (POST/PUT).
 * On success executes onSuccess(data); on error shows an alert.
 *
 * @param {HTMLFormElement} form
 * @param {string} url           API endpoint
 * @param {string} method        POST or PUT
 * @param {function} onSuccess   callback(data) called on success
 */
function submitForm(form, url, method, onSuccess) {
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const btn = form.querySelector('[type="submit"]');
    if (btn) { btn.disabled = true; btn.dataset.origText = btn.textContent; btn.textContent = 'Zapisywanie…'; }
    try {
      const data = await apiCall(url, method, new FormData(form));
      if (btn) { btn.disabled = false; btn.textContent = btn.dataset.origText; }
      if (onSuccess) onSuccess(data);
    } catch (err) {
      if (btn) { btn.disabled = false; btn.textContent = btn.dataset.origText; }
      showError(form, err.message);
    }
  });
}

/** Show an inline error banner above the submit button. */
function showError(container, msg) {
  let el = container.querySelector('.js-api-error');
  if (!el) {
    el = document.createElement('div');
    el.className = 'notice error js-api-error';
    const btn = container.querySelector('[type="submit"]');
    if (btn) btn.before(el); else container.append(el);
  }
  el.textContent = msg;
}

/** Show a temporary success notice at the top of <main>. */
function flashSuccess(msg) {
  const main = document.querySelector('main');
  if (!main) return;
  const el = document.createElement('div');
  el.className = 'notice';
  el.textContent = msg;
  main.prepend(el);
  setTimeout(() => el.remove(), 4000);
}
