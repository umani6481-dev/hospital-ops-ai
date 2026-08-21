// Thin API client for the Hospital Operations AI backend.
const API_BASE = window.HOSPITAL_API_BASE || "http://localhost:8000";

const Auth = {
  getAccess() { return localStorage.getItem("hop_access"); },
  getRefresh() { return localStorage.getItem("hop_refresh"); },
  setTokens(access, refresh) {
    localStorage.setItem("hop_access", access);
    if (refresh) localStorage.setItem("hop_refresh", refresh);
  },
  clear() {
    localStorage.removeItem("hop_access");
    localStorage.removeItem("hop_refresh");
    localStorage.removeItem("hop_user");
  },
  getUser() {
    const raw = localStorage.getItem("hop_user");
    return raw ? JSON.parse(raw) : null;
  },
  setUser(user) { localStorage.setItem("hop_user", JSON.stringify(user)); },
  isLoggedIn() { return !!this.getAccess(); },
};

async function apiRequest(path, options = {}) {
  const headers = Object.assign(
    { "Content-Type": "application/json" },
    options.headers || {}
  );
  if (Auth.getAccess()) headers["Authorization"] = `Bearer ${Auth.getAccess()}`;

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && Auth.getRefresh()) {
    // try refresh once
    const refreshed = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: Auth.getRefresh() }),
    });
    if (refreshed.ok) {
      const data = await refreshed.json();
      Auth.setTokens(data.access_token, data.refresh_token);
      headers["Authorization"] = `Bearer ${data.access_token}`;
      res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    } else {
      Auth.clear();
      window.location.reload();
      return null;
    }
  }

  if (!res.ok) {
    let detail = res.statusText;
    try { const j = await res.json(); detail = j.detail || detail; } catch (e) {}
    throw new Error(detail);
  }
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  return res.text();
}

const Api = {
  login: (email, password) => apiRequest("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => apiRequest("/api/auth/me"),
  logout: () => apiRequest("/api/auth/logout", { method: "POST" }),

  overview: () => apiRequest("/api/analytics/overview"),
  departmentAnalytics: () => apiRequest("/api/analytics/departments"),
  emergencyAnalytics: () => apiRequest("/api/analytics/emergency"),
  bedAnalytics: () => apiRequest("/api/analytics/beds"),

  departments: () => apiRequest("/api/departments"),
  beds: (deptId) => apiRequest(`/api/beds${deptId ? `?department_id=${deptId}` : ""}`),
  updateBedStatus: (bedId, status) => apiRequest(`/api/beds/${bedId}`, { method: "PUT", body: JSON.stringify({ status }) }),

  demandPredictions: () => apiRequest("/api/predictions/demand"),
  overloadPredictions: () => apiRequest("/api/predictions/overload"),
  waitingTimePredictions: () => apiRequest("/api/predictions/waiting-time"),
  bedPredictions: () => apiRequest("/api/predictions/beds"),
  noShowPrediction: (deptId, leadDays) => apiRequest(`/api/predictions/no-show?department_id=${deptId}&lead_time_days=${leadDays}`),

  alerts: (ack) => apiRequest(`/api/alerts${ack !== undefined ? `?acknowledged=${ack}` : ""}`),
  acknowledgeAlert: (id) => apiRequest(`/api/alerts/${id}/acknowledge`, { method: "POST" }),

  modelPerformance: () => apiRequest("/api/models/performance"),
  runForecast: () => apiRequest("/api/admin/run-forecast", { method: "POST" }),
  auditLogs: () => apiRequest("/api/audit-logs"),

  patients: () => apiRequest("/api/patients?limit=50"),
  appointments: () => apiRequest("/api/appointments"),
};
