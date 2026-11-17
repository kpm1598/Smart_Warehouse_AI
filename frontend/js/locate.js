nav();
document.getElementById("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const el = document.getElementById("result");
  try {
    const name = encodeURIComponent(document.getElementById("name").value);
    const qty = document.getElementById("qty").value;
    const d = await apiGet(`/inventory/locate?product_name=${name}&requested_quantity=${qty}`);
    const ok = d.status === "CAN_BE_FULFILLED";
    showResult(el, ok ? "STATUS: REQUEST CAN BE FULFILLED" : `STATUS: INSUFFICIENT STOCK\nShortage: ${d.shortage} units`, ok);
    document.getElementById("details").innerHTML =
      `<h2>${d.product} — total available: ${d.total_available}</h2>` +
      `<table><thead><tr><th>Location</th><th>Available Quantity</th></tr></thead><tbody>` +
      d.locations.map(l => `<tr><td>${l.location}</td><td>${l.available_quantity}</td></tr>`).join("") +
      `</tbody></table>`;
  } catch (err) { showResult(el, "ERROR: " + err.message, false); document.getElementById("details").innerHTML = ""; }
});
