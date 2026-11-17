nav();
document.getElementById("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const el = document.getElementById("result");
  try {
    const d = await apiPost("/inventory/store", {
      product_name: document.getElementById("name").value,
      quantity: parseInt(document.getElementById("qty").value, 10),
    });
    showResult(el, `STORAGE SUCCESSFUL\nProduct: ${d.product}\nQuantity Stored: ${d.quantity_stored}\nAssigned Location: ${d.assigned_location}\nRemaining Capacity: ${d.remaining_capacity}\nAlgorithm: ${d.algorithm}\nPath: ${d.path.join(" -> ")}`, true);
  } catch (err) { showResult(el, "ERROR: " + err.message, false); }
});
