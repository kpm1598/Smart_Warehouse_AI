nav();
document.getElementById("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const el = document.getElementById("result");
  try {
    const d = await apiPost("/inventory/dispatch", {
      product_name: document.getElementById("name").value,
      quantity: parseInt(document.getElementById("qty").value, 10),
    });
    const lines = d.locations_affected.map(l => `Location: ${l.location} — taken ${l.quantity_dispatched}, remaining there ${l.remaining_at_location}`).join("\n");
    showResult(el, `DISPATCH SUCCESSFUL\nProduct: ${d.product}\nDispatched: ${d.quantity_dispatched}\nRemaining Stock: ${d.remaining_stock}\n${lines}`, true);
  } catch (err) { showResult(el, "ERROR: " + err.message, false); }
});
