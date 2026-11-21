import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { apiUrl, createAsset, fetchAsset, fetchAssets } from "./api";
import { buildDistribution } from "./chart";
import "./styles.css";

const CATEGORIES = [
  "Machinery",
  "Tools",
  "Electronics",
  "Furniture",
  "Vehicles",
  "Safety Equipment",
];

function Icon({ name }) {
  const icons = {
    grid: "▦",
    plus: "+",
    search: "⌕",
    warehouse: "■",
  };
  return <span className="icon" aria-hidden="true">{icons[name] || ""}</span>;
}

function Navigation({ setView }) {
  return (
    <header className="topbar">
      <button className="brand" onClick={() => setView("dashboard")} aria-label="Open dashboard">
        <span className="brand-mark"><Icon name="warehouse" /></span>
        <span><small>WAREHOUSE</small> <strong>ASSET CONTROL</strong></span>
      </button>
    </header>
  );
}

function StatusMessage({ message, type }) {
  if (!message) return null;
  return <div className={`status ${type}`} role={type === "error" ? "alert" : "status"}>{message}</div>;
}

function AssetForm({ onCreated, onCancel }) {
  const [assetIdentifier, setAssetIdentifier] = useState("");
  const [category, setCategory] = useState("");
  const [photograph, setPhotograph] = useState(null);
  const [preview, setPreview] = useState("");
  const [status, setStatus] = useState({ message: "", type: "" });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

  function handleFile(event) {
    const file = event.target.files?.[0];
    setStatus({ message: "", type: "" });
    if (!file) {
      setPhotograph(null);
      setPreview("");
      return;
    }
    if (!["image/png", "image/jpeg"].includes(file.type)) {
      setPhotograph(null);
      setPreview("");
      event.target.value = "";
      setStatus({ message: "Only PNG, JPG, and JPEG image files are accepted.", type: "error" });
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setPhotograph(null);
      setPreview("");
      event.target.value = "";
      setStatus({ message: "File must be 5 MB or smaller.", type: "error" });
      return;
    }
    setPhotograph(file);
    setPreview(URL.createObjectURL(file));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmed = assetIdentifier.trim();
    if (!trimmed) {
      setStatus({ message: "Asset ID is required.", type: "error" });
      return;
    }
    if (!/^[A-Za-z0-9][A-Za-z0-9._/-]{0,63}$/.test(trimmed)) {
      setStatus({ message: "Enter a valid Asset ID using letters, numbers, periods, underscores, slashes, or hyphens.", type: "error" });
      return;
    }
    if (!category) {
      setStatus({ message: "Asset category is required.", type: "error" });
      return;
    }
    if (!photograph) {
      setStatus({ message: "An asset photograph is required.", type: "error" });
      return;
    }

    const formData = new FormData();
    formData.set("asset_identifier", trimmed);
    formData.set("category", category);
    formData.set("photograph", photograph);
    setSubmitting(true);
    try {
      const created = await createAsset(formData);
      setStatus({ message: `Asset ${created.asset_identifier} created successfully.`, type: "success" });
      onCreated(created);
    } catch (error) {
      setStatus({ message: error.message, type: "error" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page-shell">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Asset registry</p>
          <h1>Create new asset</h1>
        </div>
        <button type="button" className="button secondary" onClick={onCancel}>Cancel</button>
      </div>
      <form className="asset-form card" onSubmit={handleSubmit} noValidate>
        <StatusMessage message={status.message} type={status.type} />
        <div className="form-grid">
          <div className="field">
            <label htmlFor="assetIdentifier">Asset ID / Identification Number <span aria-hidden="true">*</span></label>
            <input
              id="assetIdentifier"
              value={assetIdentifier}
              onChange={(event) => setAssetIdentifier(event.target.value)}
              placeholder="e.g. WH-MCH-001"
              maxLength={64}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="category">Asset Category <span aria-hidden="true">*</span></label>
            <select id="category" value={category} onChange={(event) => setCategory(event.target.value)} required>
              <option value="">Select a category</option>
              {CATEGORIES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
        </div>
        <div className="field">
          <label htmlFor="photograph">Asset Photograph <span aria-hidden="true">*</span></label>
          <input
            className="file-input"
            id="photograph"
            type="file"
            accept=".png,.jpg,.jpeg,image/png,image/jpeg"
            onChange={handleFile}
            required
          />
          <small>PNG, JPG, or JPEG. Maximum size 5 MB.</small>
        </div>
        {preview && (
          <div className="preview-wrap">
            <p>Image preview</p>
            <img src={preview} alt="Preview of the selected asset photograph" />
          </div>
        )}
        <div className="form-actions">
          <button type="button" className="button secondary" onClick={onCancel}>Cancel</button>
          <button type="submit" className="button primary" disabled={submitting}>
            {submitting ? "Saving…" : "Save asset"}
          </button>
        </div>
      </form>
    </main>
  );
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(`${value.replace(" ", "T")}Z`);
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function Dashboard({ onOpen, refreshToken }) {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], pagination: { page: 1, pages: 1, total: 0 } });
  const [distribution, setDistribution] = useState([]);
  const [activeChartSegment, setActiveChartSegment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    fetchAssets({ search: query, page, limit: 10 })
      .then((result) => active && setData(result))
      .catch((problem) => active && setError(problem.message))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [query, page, refreshToken]);

  useEffect(() => {
    let active = true;

    async function loadDistribution() {
      const records = [];
      let result;
      let distributionPage = 1;
      do {
        result = await fetchAssets({ search: query, page: distributionPage, limit: 100 });
        records.push(...result.items);
        distributionPage += 1;
      } while (result.pagination.pages >= distributionPage);

      if (!active) return;
      setDistribution(buildDistribution(records));
      setActiveChartSegment(0);
    }

    loadDistribution().catch(() => {
      if (active) setDistribution([]);
    });
    return () => { active = false; };
  }, [query, refreshToken]);

  function submitSearch(event) {
    event.preventDefault();
    setPage(1);
    setQuery(search.trim());
  }

  const distributionTotal = distribution.reduce((total, item) => total + item.count, 0);
  const chartWidth = 720;
  const chartHeight = 230;
  const chartPadding = { top: 22, right: 22, bottom: 28, left: 28 };
  const chartMaximum = Math.max(...distribution.map((item) => item.count), 1);
  const chartCoordinates = distribution.map((item, index) => ({
    ...item,
    x: chartPadding.left + (index * (chartWidth - chartPadding.left - chartPadding.right)) / Math.max(distribution.length - 1, 1),
    y: chartPadding.top + ((chartMaximum - item.count) / chartMaximum) * (chartHeight - chartPadding.top - chartPadding.bottom),
  }));
  const chartLine = chartCoordinates.map((item) => `${item.x},${item.y}`).join(" ");
  const chartArea = chartCoordinates.length
    ? `M ${chartCoordinates[0].x} ${chartHeight - chartPadding.bottom} L ${chartCoordinates.map((item) => `${item.x} ${item.y}`).join(" L ")} L ${chartCoordinates.at(-1).x} ${chartHeight - chartPadding.bottom} Z`
    : "";
  const activeChartIndex = activeChartSegment ?? 0;
  const activeChartItem = distribution[activeChartIndex];

  return (
    <main className="page-shell">
      <div className="page-heading">
        <div>
          <p className="eyebrow"><span className="live-dot" /> Live inventory</p>
          <h1>Asset Dashboard</h1>
        </div>
        <button className="button primary" onClick={() => document.querySelector('[data-add-asset]')?.click()}>
          <span aria-hidden="true">+</span> Add asset
        </button>
      </div>

      <section className="metric-grid" aria-label="Inventory summary">
        <article className="metric-card">
          <div className="metric-icon">▦</div>
          <div><small>Total assets</small><strong>{data.pagination.total}</strong></div>
          <span className="trend">Live</span>
        </article>
        <article className="metric-card">
          <div className="metric-icon warm">◆</div>
          <div><small>Categories</small><strong>{distribution.length}</strong></div>
          <span className="trend">Active</span>
        </article>
        <article className="metric-card">
          <div className="metric-icon blue">◉</div>
          <div><small>Latest page</small><strong>{data.pagination.page}<em> / {data.pagination.pages}</em></strong></div>
          <span className="trend">Synced</span>
        </article>
      </section>

      <section className="card dashboard-card" aria-label="Asset records">
        <div className="toolbar">
          <form className="search-box" onSubmit={submitSearch}>
            <label className="sr-only" htmlFor="assetSearch">Search by Asset ID</label>
            <Icon name="search" />
            <input
              id="assetSearch"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by Asset ID"
            />
            <button type="submit" aria-label="Search">Search</button>
          </form>
          <span className="record-count">{data.pagination.total} records</span>
        </div>

        {error && <StatusMessage message={error} type="error" />}
        {loading ? (
          <div className="empty-state"><div className="spinner" /> Loading assets…</div>
        ) : data.items.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">▦</span>
            <h2>{query ? "No matching assets" : "No assets yet"}</h2>
            <p>{query ? `No records match “${query}”.` : "Add the first asset to begin your warehouse registry."}</p>
          </div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Photograph</th>
                    <th>Asset ID</th>
                    <th>Category</th>
                    <th>Created</th>
                    <th><span className="sr-only">Actions</span></th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((asset) => (
                    <tr key={asset.id}>
                      <td data-label="Photograph">
                        <img
                          className="thumbnail"
                          src={apiUrl(asset.photograph_url)}
                          alt={`Photograph of asset ${asset.asset_identifier}`}
                        />
                      </td>
                      <td data-label="Asset ID"><strong>{asset.asset_identifier}</strong></td>
                      <td data-label="Category"><span className="category-pill">{asset.category}</span></td>
                      <td data-label="Created">{formatDate(asset.created_at)}</td>
                      <td>
                        <button
                          type="button"
                          className="row-button"
                          aria-label={`View details for asset ${asset.asset_identifier}`}
                          onClick={() => onOpen(asset.id)}
                        >
                          View →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination">
              <button className="button secondary" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</button>
              <div className="page-numbers" aria-label="Pagination">
                {Array.from({ length: data.pagination.pages }, (_, index) => index + 1).map((pageNumber) => (
                  <button
                    key={pageNumber}
                    type="button"
                    className={pageNumber === data.pagination.page ? "page-number active" : "page-number"}
                    aria-current={pageNumber === data.pagination.page ? "page" : undefined}
                    onClick={() => setPage(pageNumber)}
                  >
                    {pageNumber}
                  </button>
                ))}
              </div>
              <button className="button secondary" disabled={page >= data.pagination.pages} onClick={() => setPage((value) => value + 1)}>Next</button>
            </div>
          </>
        )}
      </section>
      {distribution.length > 0 && (
        <section className="card distribution-card" aria-label="Asset category analytics chart">
          <div className="distribution-heading">
            <div>
              <p className="eyebrow">Inventory analytics</p>
              <h2>Asset category activity</h2>
              <p className="distribution-subtitle">Review the current mix of registered warehouse assets.</p>
            </div>
            <button className="chart-menu" type="button" aria-label="Chart options">•••</button>
          </div>
          <div className="analytics-metrics">
            <div><span>Total assets</span><strong>{distributionTotal}</strong></div>
            <div><span>Largest category</span><strong>{activeChartItem.category} <em>{activeChartItem.count} IDs</em></strong></div>
          </div>
          <div className="distribution-content">
            <div className="analytics-chart" onMouseLeave={() => setActiveChartSegment(null)}>
              <div className="chart-tooltip" style={{ left: `${Math.min(88, Math.max(12, (chartCoordinates[activeChartIndex].x / chartWidth) * 100))}%` }}>
                <span>{activeChartItem.category}</span><strong>{activeChartItem.count} asset IDs</strong><small>{Math.round((activeChartItem.count / distributionTotal) * 100)}% of inventory</small>
              </div>
              <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} role="img" aria-label={`Asset category distribution: ${distribution.map((item) => `${item.category} ${item.count}`).join(", ")}`}>
                {[0, 1, 2, 3].map((row) => <line className="chart-grid-line" key={row} x1={chartPadding.left} x2={chartWidth - chartPadding.right} y1={chartPadding.top + row * ((chartHeight - chartPadding.top - chartPadding.bottom) / 3)} y2={chartPadding.top + row * ((chartHeight - chartPadding.top - chartPadding.bottom) / 3)} />)}
                {chartCoordinates.map((item) => <line className="chart-grid-line vertical" key={item.category} x1={item.x} x2={item.x} y1={chartPadding.top} y2={chartHeight - chartPadding.bottom} />)}
                <path className="chart-area" d={chartArea} />
                <polyline className="chart-line" points={chartLine} />
                {chartCoordinates.map((item, index) => <circle key={item.category} className={activeChartIndex === index ? "chart-point active" : "chart-point"} cx={item.x} cy={item.y} r="6" fill="#ea580c" onMouseEnter={() => setActiveChartSegment(index)} onFocus={() => setActiveChartSegment(index)} onClick={() => setActiveChartSegment(index)} tabIndex="0" role="button" aria-label={`${item.category}: ${item.count} asset IDs`} />)}
              </svg>
              <div className="chart-axis">{distribution.map((item, index) => <button type="button" className={activeChartIndex === index ? "active" : ""} key={item.category} onClick={() => setActiveChartSegment(index)}>{item.category}</button>)}</div>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}

function AssetDetail({ id, onBack }) {
  const [asset, setAsset] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAsset(id).then(setAsset).catch((problem) => setError(problem.message));
  }, [id]);

  if (error) return <main className="page-shell"><StatusMessage message={error} type="error" /><button className="button secondary" onClick={onBack}>Back to dashboard</button></main>;
  if (!asset) return <main className="page-shell"><div className="empty-state"><div className="spinner" /> Loading asset…</div></main>;

  return (
    <main className="page-shell">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Asset details</p>
          <h1>{asset.asset_identifier}</h1>
        </div>
        <button className="button secondary" onClick={onBack}>← Back to dashboard</button>
      </div>
      <section className="detail-grid">
        <div className="card detail-photo">
          <img src={apiUrl(asset.photograph_url)} alt={`Photograph of asset ${asset.asset_identifier}`} />
        </div>
        <div className="card detail-info">
          <dl>
            <div><dt>Full Asset ID</dt><dd>{asset.asset_identifier}</dd></div>
            <div><dt>Category</dt><dd><span className="category-pill">{asset.category}</span></dd></div>
            <div><dt>Created date and time</dt><dd>{formatDate(asset.created_at)}</dd></div>
          </dl>
          <button className="button secondary" onClick={onBack}>← Return to dashboard</button>
        </div>
      </section>
    </main>
  );
}

function App() {
  const [view, setView] = useState("dashboard");
  const [detailId, setDetailId] = useState(null);
  const [refreshToken, setRefreshToken] = useState(0);
  const [dashboardResetToken, setDashboardResetToken] = useState(0);

  function openDetail(id) {
    setDetailId(id);
    setView("detail");
  }

  function createdAsset(asset) {
    setRefreshToken((value) => value + 1);
    openDetail(asset.id);
  }

  function navigate(nextView) {
    setDetailId(null);
    if (nextView === "dashboard") {
      setDashboardResetToken((value) => value + 1);
    }
    setView(nextView);
  }

  return (
    <>
      <Navigation setView={navigate} />
      <button data-add-asset hidden onClick={() => navigate("create")} />
      {view === "dashboard" && <Dashboard key={dashboardResetToken} onOpen={openDetail} refreshToken={refreshToken} />}
      {view === "create" && <AssetForm onCreated={createdAsset} onCancel={() => navigate("dashboard")} />}
      {view === "detail" && <AssetDetail id={detailId} onBack={() => navigate("dashboard")} />}
    </>
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
