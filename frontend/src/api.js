const configuredBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:5000`;

export function apiUrl(path) {
  return `${configuredBaseUrl.replace(/\/$/, "")}${path}`;
}

export async function fetchAssets({ search = "", page = 1, limit = 10 } = {}) {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (search) params.set("search", search);
  const response = await fetch(apiUrl(`/api/assets?${params}`));
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Unable to load assets.");
  return data;
}

export async function fetchAsset(id) {
  const response = await fetch(apiUrl(`/api/assets/${id}`));
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
