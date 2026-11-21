const configuredBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD ? "" : `${window.location.protocol}//${window.location.hostname}:5000`);

export function apiUrl(path) {
  const base = configuredBaseUrl.replace(/\/$/, "");
  if (base.endsWith("/api") && path.startsWith("/api/")) {
    return `${base}${path.slice("/api".length)}`;
  }
  return `${base}${path}`;
}

export async function fetchAssets({ search = "", page = 1, limit = 10 } = {}) {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (search) params.set("search", search);
  const response = await fetch(apiUrl(`/api/assets?${params}`), { cache: "no-store" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Unable to load assets.");
  return data;
}

export async function fetchAsset(id) {
  const response = await fetch(apiUrl(`/api/assets/${id}`), { cache: "no-store" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Unable to load asset.");
  return data;
}

export async function createAsset(formData) {
  const response = await fetch(apiUrl("/api/assets"), {
    method: "POST",
    body: formData,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Unable to create asset.");
  return data;
}
