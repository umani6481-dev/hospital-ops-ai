// ============================================================
// Hospital Operations AI — Frontend App (vanilla JS SPA)
// ============================================================

const app = document.getElementById("app");
let charts = {}; // keep chart instances so we can destroy on re-render

function destroyCharts() {
  Object.values(charts).forEach((c) => c && c.destroy());
  charts = {};
}

function toast(message, type = "info") {
  const colors = { info: "#1B4F72", success: "#1E8A5F", error: "#C0392B", warning: "#C77B26" };
  const el = document.createElement("div");
  el.className = "toast fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-lg text-white text-sm font-medium";
  el.style.background = colors[type] || colors.info;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

function riskClass(risk) {
  const r = (risk || "").toLowerCase();
  if (r === "critical") return "risk-critical";
  if (r === "high") return "risk-high";
  if (r === "moderate" || r === "medium") return "risk-moderate";
  return "risk-normal";
}

function riskDot(risk) {
  const r = (risk || "").toLowerCase();
  if (r === "critical" || r === "high") return "🔴";
  if (r === "moderate" || r === "medium") return "🟡";
  return "🟢";
}

// ---------------- ROUTER ----------------
const ROUTES = {
  "#/dashboard": renderDashboard,
  "#/predictions": renderPredictions,
  "#/departments": renderDepartments,
  "#/beds": renderBeds,
  "#/emergency": renderEmergency,
  "#/alerts": renderAlerts,
  "#/models": renderModels,
  "#/patients": renderPatients,
  "#/appointments": renderAppointments,
  "#/audit": renderAudit,
};

window.addEventListener("hashchange", route);
window.addEventListener("DOMContentLoaded", route);

function route() {
  if (!Auth.isLoggedIn()) return renderLogin();
  const hash = window.location.hash || "#/dashboard";
  const view = ROUTES[hash] || renderDashboard;
  renderShell(hash);
  view();
}

// ---------------- LOGIN ----------------
function renderLogin() {
  destroyCharts();
  app.innerHTML = `
  <div class="min-h-screen flex items-center justify-center px-4" style="background:linear-gradient(135deg,#0B2230 0%,#0E7C86 100%);">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-flex items-center gap-2 text-white">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2 L2 7 L12 12 L22 7 Z"/><path d="M2 17 L12 22 L22 17"/><path d="M2 12 L12 17 L22 12"/></svg>
          <span class="font-display text-2xl font-bold">Hospital Ops AI</span>
        </div>
        <p class="text-teal-100 mt-1 text-sm" style="color:#BEE3E0;">Operations Intelligence Platform</p>
      </div>
      <div class="card p-8 shadow-2xl">
        <h1 class="font-display text-xl font-semibold mb-1">Sign in</h1>
        <p class="text-sm text-gray-500 mb-6">Use a demo account or your credentials</p>
        <form id="login-form" class="space-y-4">
          <div>
            <label class="text-xs font-medium text-gray-600">Email</label>
            <input required type="email" id="login-email" class="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2" style="--tw-ring-color:#0E7C86" placeholder="admin@hospital-ops.demo" />
          </div>
          <div>
            <label class="text-xs font-medium text-gray-600">Password</label>
            <input required type="password" id="login-password" class="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2" style="--tw-ring-color:#0E7C86" placeholder="••••••••" />
          </div>
          <div id="login-error" class="text-red-600 text-xs hidden"></div>
          <button type="submit" class="w-full py-2.5 rounded-lg text-white font-medium text-sm" style="background:#0E7C86;">Sign in</button>
        </form>
        <div class="mt-6 border-t pt-4">
          <p class="text-xs text-gray-500 mb-2 font-medium">Demo accounts</p>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <button class="demo-btn text-left px-2 py-1.5 rounded bg-gray-50 hover:bg-gray-100" data-email="admin@hospital-ops.demo" data-pass="Admin@123">Admin</button>
            <button class="demo-btn text-left px-2 py-1.5 rounded bg-gray-50 hover:bg-gray-100" data-email="manager@hospital-ops.demo" data-pass="Manager@123">Hospital Manager</button>
            <button class="demo-btn text-left px-2 py-1.5 rounded bg-gray-50 hover:bg-gray-100" data-email="deptmanager@hospital-ops.demo" data-pass="DeptMgr@123">Dept Manager</button>
            <button class="demo-btn text-left px-2 py-1.5 rounded bg-gray-50 hover:bg-gray-100" data-email="staff@hospital-ops.demo" data-pass="Staff@123">Staff</button>
          </div>
        </div>
      </div>
      <p class="text-center text-xs mt-4" style="color:#BEE3E0;">Operations decision-support only — not a medical diagnosis system.</p>
    </div>
  </div>`;

  document.querySelectorAll(".demo-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById("login-email").value = btn.dataset.email;
      document.getElementById("login-password").value = btn.dataset.pass;
    });
  });

  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    const errBox = document.getElementById("login-error");
    errBox.classList.add("hidden");
    try {
      const data = await Api.login(email, password);
      Auth.setTokens(data.access_token, data.refresh_token);
      const user = await Api.me();
      Auth.setUser(user);
      window.location.hash = "#/dashboard";
      route();
    } catch (err) {
      errBox.textContent = err.message || "Login failed";
      errBox.classList.remove("hidden");
    }
  });
}

// ---------------- SHELL (sidebar + topbar) ----------------
const NAV = [
  { href: "#/dashboard", label: "Dashboard", icon: "M3 12l9-9 9 9M5 10v10h14V10" },
  { href: "#/predictions", label: "AI Predictions", icon: "M13 2L3 14h7l-1 8 10-12h-7l1-8z" },
  { href: "#/departments", label: "Departments", icon: "M3 21h18M5 21V7l7-4 7 4v14M9 9h1m4 0h1m-6 4h1m4 0h1" },
  { href: "#/beds", label: "Beds", icon: "M3 18v-6a2 2 0 012-2h14a2 2 0 012 2v6M3 18h18M3 18v2h18v-2M7 10V6a2 2 0 012-2h6a2 2 0 012 2v4" },
  { href: "#/emergency", label: "Emergency", icon: "M12 2l2.5 6H21l-5 4 2 7-6-4-6 4 2-7-5-4h6.5z" },
  { href: "#/alerts", label: "Alerts", icon: "M12 2C8 2 5 5 5 9v5l-2 3v1h18v-1l-2-3V9c0-4-3-7-7-7zM9 20a3 3 0 006 0" },
  { href: "#/models", label: "Model Performance", icon: "M3 3v18h18M7 15l4-6 4 3 5-8" },
  { href: "#/patients", label: "Patients", icon: "M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" },
  { href: "#/appointments", label: "Appointments", icon: "M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2z" },
  { href: "#/audit", label: "Audit Logs", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z" },
];

function renderShell(activeHash) {
  const user = Auth.getUser() || {};
  app.innerHTML = `
  <div class="flex min-h-screen">
    <aside class="w-64 shrink-0 border-r flex flex-col" style="background:var(--ink); border-color:#123847;">
      <div class="px-5 py-5 flex items-center gap-2 border-b" style="border-color:#123847;">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#4FD1C5" stroke-width="2"><path d="M12 2 L2 7 L12 12 L22 7 Z"/><path d="M2 17 L12 22 L22 17"/><path d="M2 12 L12 17 L22 12"/></svg>
        <span class="font-display text-white font-semibold text-[15px] leading-tight">Hospital<br/>Operations AI</span>
      </div>
      <nav class="flex-1 overflow-y-auto py-3 px-2 space-y-0.5" id="sidebar-nav"></nav>
      <div class="px-4 py-4 border-t text-xs" style="border-color:#123847; color:#8FB8BC;">
        <div class="font-medium text-white">${user.full_name || "User"}</div>
        <div class="capitalize">${(user.role || "").replace("_", " ")}</div>
        <button id="logout-btn" class="mt-2 text-teal-300 hover:underline">Sign out</button>
      </div>
    </aside>
    <main class="flex-1 min-w-0">
      <header class="h-14 border-b bg-white flex items-center justify-between px-6 sticky top-0 z-10" style="border-color:var(--line);">
        <div class="text-sm text-gray-500" id="page-title">Hospital Operations AI</div>
        <div class="flex items-center gap-3">
          <span class="text-xs px-2 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">Demo / Synthetic Data</span>
          <button id="refresh-btn" class="text-xs px-3 py-1.5 rounded-lg border hover:bg-gray-50">Refresh</button>
        </div>
      </header>
      <div id="page-content" class="p-6 fade-in"></div>
    </main>
  </div>`;

  const navEl = document.getElementById("sidebar-nav");
  NAV.forEach((item) => {
    const a = document.createElement("a");
    a.href = item.href;
    a.className = "sidebar-link flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-teal-50/80 hover:bg-white/5" + (item.href === activeHash ? " active" : "");
    a.style.color = item.href === activeHash ? "#fff" : "#B9D6D4";
    a.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="${item.icon}"/></svg>${item.label}`;
    navEl.appendChild(a);
  });

  document.getElementById("logout-btn").addEventListener("click", async () => {
    try { await Api.logout(); } catch (e) {}
    Auth.clear();
    window.location.hash = "#/dashboard";
    route();
  });
  document.getElementById("refresh-btn").addEventListener("click", () => route());
}

function content() { return document.getElementById("page-content"); }
function setTitle(t) { const el = document.getElementById("page-title"); if (el) el.textContent = t; }

function statCard(label, value, sub, accent = "var(--teal)") {
  return `<div class="card p-4">
    <div class="text-xs text-gray-500 mb-1">${label}</div>
    <div class="font-display text-2xl font-bold" style="color:${accent}">${value}</div>
    ${sub ? `<div class="text-xs text-gray-400 mt-1">${sub}</div>` : ""}
  </div>`;
}

function loadingBlock() {
  return `<div class="flex items-center justify-center py-24 text-gray-400 text-sm">Loading…</div>`;
}

function errorBlock(msg) {
  return `<div class="card p-6 text-center text-red-600 text-sm">${msg}</div>`;
}

// ---------------- DASHBOARD ----------------
async function renderDashboard() {
  setTitle("Hospital Operations Dashboard");
  content().innerHTML = loadingBlock();
  try {
    const [overview, deptAnalytics, emergency, demand, overload, alerts] = await Promise.all([
      Api.overview(), Api.departmentAnalytics(), Api.emergencyAnalytics(),
      Api.demandPredictions().catch(() => []), Api.overloadPredictions().catch(() => []),
      Api.alerts(false).catch(() => []),
    ]);

    const totalDemandToday = demand.reduce((s, d) => s + (d.predicted_patients || 0), 0);
    const peakDept = overload.slice().sort((a, b) => (b.overload_probability || 0) - (a.overload_probability || 0))[0];

    content().innerHTML = `
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      ${statCard("Bed Occupancy", overview.occupancy_rate + "%", `${overview.occupied_beds}/${overview.total_beds} beds occupied`)}
      ${statCard("Patients (30d)", overview.patients_last_30_days.toLocaleString(), "Visits recorded")}
      ${statCard("Avg Wait Time", (overview.avg_waiting_time_minutes ?? "–") + " min", "Across all departments", "var(--blue)")}
      ${statCard("Emergency Arrivals (24h)", emergency.arrivals_last_24h, `Peak risk: ${peakDept ? peakDept.department : "–"}`, "var(--red)")}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <div class="card p-5 lg:col-span-2">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-display font-semibold text-sm">Patient Demand Forecast (Tomorrow, by department)</h3>
          <span class="text-xs text-gray-400">AI-generated</span>
        </div>
        <canvas id="chart-demand" height="110"></canvas>
      </div>
      <div class="card p-5">
        <h3 class="font-display font-semibold text-sm mb-3">Department Risk</h3>
        <div class="space-y-2">
          ${overload.map(o => `
            <div class="flex items-center justify-between text-sm py-1.5 border-b last:border-0" style="border-color:var(--line)">
              <span>${o.department}</span>
              <span class="px-2 py-0.5 rounded-full text-xs font-medium ${riskClass(o.risk_level)}">${riskDot(o.risk_level)} ${o.risk_level}</span>
            </div>`).join("")}
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card p-5">
        <h3 class="font-display font-semibold text-sm mb-3">Bed Occupancy by Department</h3>
        <canvas id="chart-occupancy" height="140"></canvas>
      </div>
      <div class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-display font-semibold text-sm">Active AI Alerts</h3>
          <a href="#/alerts" class="text-xs" style="color:var(--teal)">View all →</a>
        </div>
        <div class="space-y-2 max-h-64 overflow-y-auto">
          ${alerts.length === 0 ? `<div class="text-sm text-gray-400 py-6 text-center">No active alerts. Run the forecast job to generate predictions.</div>` :
            alerts.slice(0, 6).map(a => `
            <div class="p-3 rounded-lg text-sm ${riskClass(a.severity === 'critical' ? 'critical' : a.severity === 'high' ? 'high' : 'moderate')}">
              <div class="font-medium">⚠ ${a.title}</div>
              <div class="text-xs mt-0.5 opacity-80">${a.message}</div>
            </div>`).join("")}
        </div>
      </div>
    </div>
    `;

    destroyCharts();
    const ctx1 = document.getElementById("chart-demand");
    if (ctx1) {
      charts.demand = new Chart(ctx1, {
        type: "bar",
        data: {
          labels: demand.map(d => d.department),
          datasets: [{
            label: "Predicted Patients",
            data: demand.map(d => d.predicted_patients),
            backgroundColor: "#0E7C86",
            borderRadius: 6,
          }],
        },
        options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
      });
    }
    const ctx2 = document.getElementById("chart-occupancy");
    if (ctx2) {
      charts.occupancy = new Chart(ctx2, {
        type: "doughnut",
        data: {
          labels: deptAnalytics.map(d => d.name),
          datasets: [{
            data: deptAnalytics.map(d => d.occupancy_rate),
            backgroundColor: ["#0E7C86", "#1B4F72", "#4FD1C5", "#C77B26", "#1E8A5F", "#8E6CC7"],
          }],
        },
        options: { plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 10 } } } } },
      });
    }
  } catch (err) {
    content().innerHTML = errorBlock(err.message);
  }
}

// ---------------- AI PREDICTIONS ----------------
async function renderPredictions() {
  setTitle("AI Predictions & Forecasting");
  content().innerHTML = loadingBlock();
  try {
    const [demand, overload, waiting, beds] = await Promise.all([
      Api.demandPredictions(), Api.overloadPredictions(), Api.waitingTimePredictions(), Api.bedPredictions(),
    ]);

    const totalToday = demand.reduce((s, d) => s + d.predicted_patients, 0);

    content().innerHTML = `
    <div class="card p-5 mb-6" style="background:linear-gradient(135deg,#0B2230,#0E7C86); color:white; border:none;">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div class="text-xs opacity-70 mb-1">Total Predicted Demand — Tomorrow</div>
          <div class="font-display text-3xl font-bold">${totalToday.toLocaleString()} patients</div>
        </div>
        <button id="run-forecast-btn" class="px-4 py-2 rounded-lg bg-white text-sm font-medium" style="color:var(--ink)">
          ⚡ Run Forecast Job & Generate Alerts
        </button>
      </div>
    </div>

    <h3 class="font-display font-semibold text-sm mb-3">Patient Demand Forecast — by Department</h3>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      ${demand.map(d => `
      <div class="card p-4">
        <div class="text-sm font-medium mb-1">${d.department}</div>
        <div class="font-display text-2xl font-bold" style="color:var(--teal)">${d.predicted_patients}</div>
        <div class="text-xs text-gray-400 mb-2">Confidence: ${d.confidence_interval.low}–${d.confidence_interval.high}</div>
        <div class="text-xs text-gray-500 space-y-0.5">
          ${d.explanation.slice(0, 3).map(e => `<div>• ${e.factor}</div>`).join("")}
        </div>
      </div>`).join("")}
    </div>

    <h3 class="font-display font-semibold text-sm mb-3">Department Overload Risk</h3>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      ${overload.map(o => `
      <div class="card p-4">
        <div class="flex items-center justify-between mb-2">
          <div class="text-sm font-medium">${o.department}</div>
          <span class="px-2 py-0.5 rounded-full text-xs font-medium ${riskClass(o.risk_level)}">${riskDot(o.risk_level)} ${o.risk_level}</span>
        </div>
        <div class="font-display text-2xl font-bold" style="color:var(--blue)">${o.overload_probability}%</div>
        <div class="text-xs text-gray-400 mb-2">${o.expected_patients} expected / ${o.capacity} capacity</div>
        <div class="text-xs text-gray-500 space-y-0.5">
          <div class="font-medium text-gray-600 mb-0.5">Main factors:</div>
          ${o.explanation.slice(0, 3).map(e => `<div>+ ${e.factor}</div>`).join("")}
        </div>
      </div>`).join("")}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div>
        <h3 class="font-display font-semibold text-sm mb-3">Predicted Waiting Time</h3>
        <div class="space-y-3">
          ${waiting.map(w => `
          <div class="card p-4">
            <div class="flex items-center justify-between mb-2">
              <div class="text-sm font-medium">${w.department}</div>
              <span class="px-2 py-0.5 rounded-full text-xs font-medium ${riskClass(w.risk)}">${w.risk}</span>
            </div>
            <div class="flex gap-6">
              <div><div class="text-xs text-gray-400">Current</div><div class="font-display font-bold" style="color:var(--teal)">${w.current_waiting_time_minutes} min</div></div>
              <div><div class="text-xs text-gray-400">In 2 hours</div><div class="font-display font-bold" style="color:var(--blue)">${w.predicted_in_2_hours_minutes} min</div></div>
            </div>
          </div>`).join("")}
        </div>
      </div>
      <div>
        <h3 class="font-display font-semibold text-sm mb-3">Bed Availability Forecast</h3>
        <div class="space-y-3">
          ${beds.map(b => `
          <div class="card p-4">
            <div class="flex items-center justify-between mb-2">
              <div class="text-sm font-medium">${b.department}</div>
              <span class="px-2 py-0.5 rounded-full text-xs font-medium ${riskClass(b.risk)}">${b.risk}</span>
            </div>
            <div class="flex gap-6">
              <div><div class="text-xs text-gray-400">Predicted Available</div><div class="font-display font-bold" style="color:var(--teal)">${b.predicted_available_beds}</div></div>
              <div><div class="text-xs text-gray-400">Total Beds</div><div class="font-display font-bold text-gray-500">${b.total_beds}</div></div>
            </div>
          </div>`).join("")}
        </div>
      </div>
    </div>
    `;

    document.getElementById("run-forecast-btn").addEventListener("click", async (e) => {
      e.target.disabled = true;
      e.target.textContent = "Running…";
      try {
        const result = await Api.runForecast();
        toast(`Forecast complete: ${result.alerts_generated} alerts, ${result.predictions_generated} predictions generated`, "success");
        renderPredictions();
      } catch (err) {
        toast(err.message, "error");
        e.target.disabled = false;
        e.target.textContent = "⚡ Run Forecast Job & Generate Alerts";
      }
    });
  } catch (err) {
    content().innerHTML = errorBlock(err.message + " — have you trained the ML models? Run the training commands from the README.");
  }
}

// ---------------- DEPARTMENTS ----------------
async function renderDepartments() {
  setTitle("Departments");
  content().innerHTML = loadingBlock();
  try {
    const deptAnalytics = await Api.departmentAnalytics();
    content().innerHTML = `
    <div class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs text-gray-500 border-b" style="border-color:var(--line)">
            <th class="px-4 py-3">Department</th>
            <th class="px-4 py-3">Capacity</th>
            <th class="px-4 py-3">Beds (Total)</th>
            <th class="px-4 py-3">Beds Occupied</th>
            <th class="px-4 py-3">Occupancy Rate</th>
            <th class="px-4 py-3">Visits (30d)</th>
          </tr>
        </thead>
        <tbody>
          ${deptAnalytics.map(d => `
          <tr class="border-b last:border-0" style="border-color:var(--line)">
            <td class="px-4 py-3 font-medium">${d.name}</td>
            <td class="px-4 py-3">${d.capacity}</td>
            <td class="px-4 py-3">${d.beds_total}</td>
            <td class="px-4 py-3">${d.beds_occupied}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <div class="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full rounded-full" style="width:${Math.min(100, d.occupancy_rate)}%; background:${d.occupancy_rate > 85 ? 'var(--red)' : d.occupancy_rate > 65 ? 'var(--amber)' : 'var(--teal)'}"></div>
                </div>
                <span class="text-xs">${d.occupancy_rate}%</span>
              </div>
            </td>
            <td class="px-4 py-3">${d.visits_last_30_days}</td>
          </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
  } catch (err) { content().innerHTML = errorBlock(err.message); }
}

// ---------------- BEDS ----------------
async function renderBeds() {
  setTitle("Bed Management");
  content().innerHTML = loadingBlock();
  try {
    const [beds, departments, bedStats] = await Promise.all([Api.beds(), Api.departments(), Api.bedAnalytics()]);
    const deptMap = Object.fromEntries(departments.map(d => [d.id, d.name]));
    const statusColors = { available: "risk-normal", occupied: "risk-high", reserved: "risk-moderate", cleaning: "bg-blue-50 text-blue-600", maintenance: "bg-gray-100 text-gray-500" };

    content().innerHTML = `
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      ${statCard("Available", bedStats.available || 0, null, "var(--green)")}
      ${statCard("Occupied", bedStats.occupied || 0, null, "var(--red)")}
      ${statCard("Reserved", bedStats.reserved || 0, null, "var(--amber)")}
      ${statCard("Cleaning", bedStats.cleaning || 0)}
      ${statCard("Maintenance", bedStats.maintenance || 0)}
    </div>
    <div class="card p-5">
      <h3 class="font-display font-semibold text-sm mb-4">All Beds</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 max-h-[500px] overflow-y-auto">
        ${beds.map(b => `
        <div class="border rounded-lg p-2.5 text-xs" style="border-color:var(--line)">
          <div class="font-medium mb-1 truncate">${deptMap[b.department_id] || "—"}</div>
          <select data-bed-id="${b.id}" class="bed-status-select w-full text-xs rounded px-1.5 py-1 border ${statusColors[b.status] || ""}" style="border-color:var(--line)">
            ${["available", "occupied", "reserved", "cleaning", "maintenance"].map(s => `<option value="${s}" ${b.status === s ? "selected" : ""}>${s}</option>`).join("")}
          </select>
        </div>`).join("")}
      </div>
    </div>`;

    document.querySelectorAll(".bed-status-select").forEach(sel => {
      sel.addEventListener("change", async () => {
        try {
          await Api.updateBedStatus(sel.dataset.bedId, sel.value);
          toast("Bed status updated", "success");
        } catch (err) { toast(err.message, "error"); }
      });
    });
  } catch (err) { content().innerHTML = errorBlock(err.message); }
}

// ---------------- EMERGENCY ----------------
async function renderEmergency() {
  setTitle("Emergency Department");
  content().innerHTML = loadingBlock();
  try {
    const [emergency, waiting] = await Promise.all([
      Api.emergencyAnalytics(),
      Api.waitingTimePredictions().catch(() => []),
    ]);
    const erWait = waiting.find(w => w.department.toLowerCase().includes("emergency"));
    content().innerHTML = `
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      ${statCard("Arrivals (24h)", emergency.arrivals_last_24h, null, "var(--red)")}
      ${statCard("Avg Waiting Time", (emergency.avg_waiting_time_minutes ?? "–") + " min")}
      ${statCard("Max Waiting Time", (emergency.max_waiting_time_minutes ?? "–") + " min")}
      ${statCard("Currently Waiting", emergency.patients_currently_waiting)}
    </div>
    ${erWait ? `
    <div class="card p-5">
      <h3 class="font-display font-semibold text-sm mb-3">AI Predicted Waiting Time — Emergency</h3>
      <div class="flex gap-8">
        <div><div class="text-xs text-gray-400">Current</div><div class="font-display text-2xl font-bold" style="color:var(--teal)">${erWait.current_waiting_time_minutes} min</div></div>
        <div><div class="text-xs text-gray-400">In 2 hours</div><div class="font-display text-2xl font-bold" style="color:var(--blue)">${erWait.predicted_in_2_hours_minutes} min</div></div>
        <div><div class="text-xs text-gray-400">Risk</div><span class="px-2 py-1 rounded-full text-xs font-medium ${riskClass(erWait.risk)}">${erWait.risk}</span></div>
      </div>
    </div>` : ""}
    `;
  } catch (err) { content().innerHTML = errorBlock(err.message); }
}

// ---------------- ALERTS ----------------
async function renderAlerts() {
  setTitle("Alerts");
  content().innerHTML = loadingBlock();
  try {
    const alerts = await Api.alerts();
    content().innerHTML = `
    <div class="space-y-3">
      ${alerts.length === 0 ? `<div class="card p-10 text-center text-gray-400 text-sm">No alerts yet. Go to AI Predictions and click "Run Forecast Job".</div>` :
      alerts.map(a => `
      <div class="card p-4 flex items-start justify-between gap-4 ${a.acknowledged ? "opacity-50" : ""}">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="px-2 py-0.5 rounded-full text-xs font-medium ${riskClass(a.severity)}">${a.severity}</span>
            <span class="font-medium text-sm">${a.title}</span>
          </div>
          <p class="text-xs text-gray-500">${a.message}</p>
          <p class="text-xs text-gray-300 mt-1">${new Date(a.created_at).toLocaleString()}</p>
        </div>
        ${!a.acknowledged ? `<button data-id="${a.id}" class="ack-btn shrink-0 text-xs px-3 py-1.5 rounded-lg border hover:bg-gray-50">Acknowledge</button>` : `<span class="text-xs text-gray-400 shrink-0">✓ Acknowledged</span>`}
      </div>`).join("")}
    </div>`;

    document.querySelectorAll(".ack-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        try { await Api.acknowledgeAlert(btn.dataset.id); toast("Alert acknowledged", "success"); renderAlerts(); }
        catch (err) { toast(err.message, "error"); }
      });
    });
  } catch (err) { content().innerHTML = errorBlock(err.message); }
}

// ---------------- MODEL PERFORMANCE ----------------
async function renderModels() {
  setTitle("ML Model Performance");
  content().innerHTML = loadingBlock();
  try {
    const perf = await Api.modelPerformance();
    content().innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      ${Object.entries(perf).map(([name, meta]) => `
      <div class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-display font-semibold text-sm capitalize">${name.replace(/_/g, " ")}</h3>
          ${meta.status === "not_trained" ? `<span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">Not trained</span>` :
            `<span class="text-xs px-2 py-0.5 rounded-full risk-normal">${meta.algorithm}</span>`}
        </div>
        ${meta.status === "not_trained" ? `<p class="text-xs text-gray-400">Run the corresponding training script from the README.</p>` : `
        <div class="grid grid-cols-2 gap-3 mb-3">
          ${Object.entries(meta.metrics).map(([k, v]) => `
            <div class="bg-gray-50 rounded-lg p-2.5">
              <div class="text-xs text-gray-400">${k}</div>
              <div class="font-display font-bold text-sm">${v}</div>
            </div>`).join("")}
        </div>
        <div class="text-xs text-gray-400">
          <div>Version: ${meta.version}</div>
          <div>Dataset: ${meta.dataset_version}</div>
          <div>Last trained: ${new Date(meta.trained_at).toLocaleString()}</div>
        </div>`}
      </div>`).join("")}
    </div>`;
  } catch (err) { content().innerHTML = errorBlock(err.message); }
}

// ---------------- PATIENTS ----------------
async function renderPatients() {
  setTitle("Patients (Synthetic / Demo)");
  content().innerHTML = loadingBlock();
  try {
    const patients = await Api.patients();
    content().innerHTML = `
    <div class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead><tr class="text-left text-xs text-gray-500 border-b" style="border-color:var(--line)">
          <th class="px-4 py-3">Age Group</th><th class="px-4 py-3">Gender</th><th class="px-4 py-3">Region</th><th class="px-4 py-3">Registered</th>
        </tr></thead>
        <tbody>
          ${patients.map(p => `<tr class="border-b last:border-0" style="border-color:var(--line)">
            <td class="px-4 py-3">${p.age_group}</td><td class="px-4 py-3">${p.gender}</td><td class="px-4 py-3">${p.region}</td>
            <td class="px-4 py-3 text-gray-400">${new Date(p.registration_date).toLocaleDateString()}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>`;
  } catch (err) { content().innerHTML = errorBlock(err.message); }
}

// ---------------- APPOINTMENTS ----------------
async function renderAppointments() {
  setTitle("Appointments");
  content().innerHTML = loadingBlock();
  try {
    const appts = await Api.appointments();
    content().innerHTML = `
    <div class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead><tr class="text-left text-xs text-gray-500 border-b" style="border-color:var(--line)">
          <th class="px-4 py-3">Date</th><th class="px-4 py-3">Type</th><th class="px-4 py-3">Status</th><th class="px-4 py-3">Wait (min)</th>
        </tr></thead>
        <tbody>
          ${appts.slice(0, 100).map(a => `<tr class="border-b last:border-0" style="border-color:var(--line)">
            <td class="px-4 py-3">${new Date(a.appointment_date).toLocaleDateString()}</td>
            <td class="px-4 py-3">${a.appointment_type}</td>
            <td class="px-4 py-3"><span class="px-2 py-0.5 rounded-full text-xs ${a.status === 'no_show' ? 'risk-critical' : a.status === 'cancelled' ? 'bg-gray-100 text-gray-500' : 'risk-normal'}">${a.status}</span></td>
            <td class="px-4 py-3">${a.waiting_time_minutes ?? "–"}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>`;
  } catch (err) { content().innerHTML = errorBlock(err.message); }
}

// ---------------- AUDIT LOGS ----------------
async function renderAudit() {
  setTitle("Audit Logs");
  content().innerHTML = loadingBlock();
  try {
    const logs = await Api.auditLogs();
    content().innerHTML = `
    <div class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead><tr class="text-left text-xs text-gray-500 border-b" style="border-color:var(--line)">
          <th class="px-4 py-3">Action</th><th class="px-4 py-3">Entity</th><th class="px-4 py-3">User</th><th class="px-4 py-3">Time</th>
        </tr></thead>
        <tbody>
          ${logs.map(l => `<tr class="border-b last:border-0" style="border-color:var(--line)">
            <td class="px-4 py-3 font-medium">${l.action}</td>
            <td class="px-4 py-3 text-gray-500">${l.entity || "–"}</td>
            <td class="px-4 py-3 text-gray-400 text-xs">${(l.user_id || "").slice(0, 8)}</td>
            <td class="px-4 py-3 text-gray-400">${new Date(l.created_at).toLocaleString()}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>`;
  } catch (err) { content().innerHTML = errorBlock(err.message + " (admin only)"); }
}
