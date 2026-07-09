/* Shared helpers used across pages */

async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin", // send the session cookie with every request
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || "Something went wrong");
  }
  return data;
}

async function logout(e) {
  if (e) e.preventDefault();
  try {
    await apiFetch("/api/logout", { method: "POST" });
  } finally {
    window.location.href = "/";
  }
}

function showMessage(el, message, isError = true) {
  el.textContent = message;
  el.style.display = "block";
  el.className = isError ? "error-msg" : "success-msg";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}
