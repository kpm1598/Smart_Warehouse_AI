nav();
(async () => {
  const locs = await apiGet("/warehouse/locations");
  document.getElementById("goal").innerHTML = locs
    .filter(l => l.location_code !== "RECEIVING")
    .map(l => `<option>${l.location_code}</option>`).join("");
})();
document.getElementById("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const el = document.getElementById("result");
  try {
    const d = await apiPost("/ai/search/compare", {
      start_location: "RECEIVING",
      goal_location: document.getElementById("goal").value,
      depth_limit: parseInt(document.getElementById("depth").value, 10),
    });
    showResult(el, `Comparison complete for RECEIVING -> ${d.goal_location}`, true);
    const rows = [
      ["Search type", d.dls.search_type, d.greedy.search_type],
      ["Heuristic", d.dls.heuristic_used ? "Yes" : "No", d.greedy.heuristic_used ? "Yes" : "No"],
      ["Depth limit", d.dls.depth_limit, "—"],
      ["Status", d.dls.status, d.greedy.status],
      ["Nodes explored", d.dls.nodes_explored, d.greedy.nodes_explored],
      ["Path", d.dls.path.join(" -> ") || "(none)", d.greedy.path.join(" -> ") || "(none)"],
      ["Path distance", d.dls.path_distance, d.greedy.path_distance],
      ["Execution time (ms)", d.dls.execution_time_ms, d.greedy.execution_time_ms],
    ];
    document.getElementById("table").innerHTML =
      `<table><thead><tr><th>Metric</th><th>DLS</th><th>Greedy Best-First</th></tr></thead><tbody>` +
      rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td></tr>`).join("") + `</tbody></table>`;
  } catch (err) { showResult(el, "ERROR: " + err.message, false); }
});
