nav();
async function load() {
  const map = await apiGet("/warehouse/map");
  const cells = {};
  map.nodes.forEach(n => {
    const row = document.createElement("div");
    row.className = "cell" + (n.max_capacity === 0 ? " receiving" : "");
    const pct = n.max_capacity ? Math.round(100 * n.occupied_capacity / n.max_capacity) : 0;
    row.style.gridRow = n.row_number + 1;
    row.style.gridColumn = n.column_number + 1;
    row.innerHTML = `<div class="code">${n.location_code}</div>` +
      (n.max_capacity ? `${n.occupied_capacity} / ${n.max_capacity} units<div class="bar"><div style="width:${pct}%"></div></div>remaining ${n.remaining_capacity}` : "start point");
    cells[n.location_code] = row;
    document.getElementById("map").appendChild(row);
  });
  document.getElementById("edges").innerHTML = map.edges.map(e =>
    `<tr><td>${e.source}</td><td>${e.destination}</td><td>${e.distance}</td>` +
    `<td>${e.is_blocked ? "BLOCKED" : "open"}</td>` +
    `<td><button class="small" onclick="toggleEdge(${e.connection_id}, ${!e.is_blocked})">${e.is_blocked ? "Unblock" : "Block"}</button></td></tr>`).join("");
}
async function toggleEdge(id, blocked) {
  await apiPatch(`/warehouse/connections/${id}`, { is_blocked: blocked });
  document.getElementById("map").innerHTML = "";
  load();
}
load().catch(e => alert(e.message));
