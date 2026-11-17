// Shared API helper — same-origin calls to the FastAPI backend.
async function apiRequest(method, path, body) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) options.body = JSON.stringify(body);
  let response;
  try {
    response = await fetch("/api/v1" + path, options);
  } catch (e) {
    throw new Error("Cannot reach the server. Is the backend running?");
  }
  const payload = await response.json().catch(() => null);
  if (!payload || !payload.success) {
    throw new Error(payload ? payload.message : "Server returned an invalid response");
  }
  return payload.data;
}
const apiGet = (path) => apiRequest("GET", path);
const apiPost = (path, body) => apiRequest("POST", path, body);
const apiPatch = (path, body) => apiRequest("PATCH", path, body);

function showResult(el, text, ok) {
  el.textContent = text;
  el.className = "result " + (ok ? "ok" : "err");
}
function nav(active) {
  const links = [
    ["index.html", "Dashboard"], ["inventory.html", "Inventory"],
    ["store.html", "Store Object"], ["locate.html", "Locate Object"],
    ["dispatch.html", "Dispatch Stock"], ["warehouse.html", "Warehouse Map"],
    ["comparison.html", "AI Comparison"],
  ];
  document.getElementById("nav").innerHTML = links
    .map(([href, label]) => `<a href="${href}">${label}</a>`).join("");
}
