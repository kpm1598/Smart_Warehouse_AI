nav();
let allRows = [];
async function load() {
  allRows = await apiGet("/inventory");
  const locs = [...new Set(allRows.map(r => r.location))].sort();
  const sel = document.getElementById("locFilter");
  sel.innerHTML = '<option value="">All locations</option>' + locs.map(l => `<option>${l}</option>`).join("");
  render();
}
function render() {
  const q = document.getElementById("search").value.toLowerCase();
  const loc = document.getElementById("locFilter").value;
  const rows = allRows.filter(r => r.product.toLowerCase().includes(q) && (!loc || r.location === loc));
  document.getElementById("rows").innerHTML = rows
    .map(r => `<tr><td>${r.product}</td><td>${r.location}</td><td>${r.quantity}</td></tr>`).join("");
  document.getElementById("totals").textContent =
    `Unique products: ${new Set(rows.map(r => r.product)).size} · Total units shown: ${rows.reduce((a, r) => a + r.quantity, 0)}`;
}
document.getElementById("search").addEventListener("input", render);
document.getElementById("locFilter").addEventListener("change", render);
load().catch(e => alert(e.message));
