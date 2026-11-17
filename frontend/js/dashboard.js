nav();
(async () => {
  const s = await apiGet("/dashboard/summary");
  const cards = [
    [s.unique_products, "Unique Products"],
    [s.total_stock_units, "Total Stock Units"],
    [s.storage_locations, "Storage Locations"],
    [s.occupied_locations, "Occupied Locations"],
    [s.total_remaining_capacity, "Remaining Capacity"],
  ];
  document.getElementById("cards").innerHTML = cards
    .map(([v, l]) => `<div class="card"><div class="value">${v}</div><div class="label">${l}</div></div>`).join("");
  document.getElementById("activity").innerHTML = s.recent_activity
    .map(a => `<tr><td>${a.movement_type}</td><td>${a.product}</td><td>${a.location}</td><td>${a.quantity}</td><td>${a.created_at || ""}</td></tr>`).join("");
})().catch(e => { document.querySelector("main").innerHTML += `<div class="result err">${e.message}</div>`; });
