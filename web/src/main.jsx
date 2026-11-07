import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

async function getApi(path, token) {
  const response = await fetch(path, {
    method: "GET",
    cache: "no-store",
    credentials: "omit",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const message = response.status === 401
      ? "Session token not accepted."
      : `Request failed (HTTP ${response.status}).`;
    throw new Error(message);
  }
  return response.json();
}

function displayBytes(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric < 0) return "—";
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  let number = numeric;
  let unit = 0;
  while (number >= 1024 && unit < units.length - 1) {
    number /= 1024;
    unit += 1;
  }
  return `${number.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function formatNamespace(value) {
  return value || "(root)";
}

function App() {
  const [inputToken, setInputToken] = useState("");
  const [token, setToken] = useState("");
  const [instances, setInstances] = useState([]);
  const [instanceId, setInstanceId] = useState("");
  const [datastore, setDatastore] = useState("");
  const [namespace, setNamespace] = useState("");
  const [namespaces, setNamespaces] = useState([""]);
  const [groups, setGroups] = useState([]);
  const [storeStatus, setStoreStatus] = useState(null);
  const [serverVersion, setServerVersion] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    if (!token) return;
    let active = true;
    setLoading(true);
    getApi("/api/v1/instances", token).then((data) => {
      if (!active) return;
      const items = Array.isArray(data.items) ? data.items : [];
      setInstances(items);
      setInstanceId((old) => items.some((x) => x.id === old) ? old : (items[0]?.id || ""));
      setError("");
    }).catch((err) => {
      if (active) setError(err.message);
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [token, refresh]);

  const selected = instances.find((item) => item.id === instanceId);
  useEffect(() => {
    const stores = selected?.datastores || [];
    setDatastore((old) => stores.includes(old) ? old : (stores[0] || ""));
  }, [selected]);

  useEffect(() => {
    if (!token || !instanceId || !datastore) return;
    let active = true;
    setLoading(true);
    const prefix = `/api/v1/instances/${encodeURIComponent(instanceId)}/datastores/${encodeURIComponent(datastore)}`;
    Promise.all([
      getApi(`${prefix}/namespaces`, token),
      getApi(`${prefix}/status`, token),
      getApi(`/api/v1/instances/${encodeURIComponent(instanceId)}/version`, token),
    ]).then(([ns, status, version]) => {
      if (!active) return;
      const names = Array.isArray(ns.data)
        ? ns.data.map((entry) => typeof entry === "string"
          ? entry : (entry.ns ?? entry.namespace ?? ""))
        : [];
      const unique = ["", ...new Set(names.filter(Boolean))];
      setNamespaces(unique);
      setNamespace((old) => unique.includes(old) ? old : "");
      setStoreStatus(status.data || null);
      setServerVersion(version.data || null);
      setError("");
    }).catch((err) => {
      if (active) setError(err.message);
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [token, instanceId, datastore, refresh]);

  useEffect(() => {
    if (!token || !instanceId || !datastore) return;
    let active = true;
    setLoading(true);
    const path = `/api/v1/instances/${encodeURIComponent(instanceId)}/datastores/${encodeURIComponent(datastore)}/groups?ns=${encodeURIComponent(namespace)}`;
    getApi(path, token).then((data) => {
      if (!active) return;
      setGroups(Array.isArray(data.data) ? data.data : []);
      setError("");
    }).catch((err) => {
      if (active) setError(err.message);
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [token, instanceId, datastore, namespace, refresh]);

  if (!token) return (
    <main className="login">
      <div className="brand">PBS <span>Sentinel</span></div>
      <section className="login-card">
        <div className="eyebrow">Protected operations console</div>
        <h1>Backup visibility, without the guesswork.</h1>
        <p>Read-only monitoring across independent Proxmox Backup Server instances.</p>
        <form onSubmit={(event) => {
          event.preventDefault();
          if (inputToken.trim()) setToken(inputToken.trim());
          setInputToken("");
        }}>
          <label htmlFor="token">Sentinel access token</label>
          <input id="token" type="password" autoComplete="off" value={inputToken}
            onChange={(event) => setInputToken(event.target.value)}
            placeholder="Enter your access token" />
          <button type="submit">Open dashboard</button>
        </form>
        <small>Token is held in browser memory only. PBS credentials never reach your browser. Use HTTPS and SSO for production.</small>
      </section>
    </main>
  );

  const type = serverVersion?.version || serverVersion?.release || "Connected";
  const total = storeStatus?.total ?? storeStatus?.store?.total;
  const used = storeStatus?.used ?? storeStatus?.store?.used;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">PBS <span>Sentinel</span></div>
        <div className="nav-title">WORKSPACE</div>
        <div className="nav-item active">Backup overview</div>
        <div className="nav-item muted">Integrity & incidents <span>Planned</span></div>
        <div className="nav-item muted">Recovery plans <span>Planned</span></div>
        <div className="sidebar-foot">Early preview · Read-only</div>
      </aside>
      <main className="content">
        <header className="topbar">
          <div>
            <div className="eyebrow">Infrastructure / Overview</div>
            <h1>Backup overview</h1>
            <p>Inspect PBS instances, datastores and backup groups from one place.</p>
          </div>
          <div className="toolbar">
            <button className="secondary" type="button" onClick={() => setRefresh((x) => x + 1)}>Refresh</button>
            <button className="secondary" type="button" onClick={() => {
              setToken(""); setInstances([]); setGroups([]); setStoreStatus(null);
            }}>Lock</button>
          </div>
        </header>

        {error && <div className="error" role="alert">{error}</div>}
        <div className="filters">
          <label>Instance
            <select value={instanceId} onChange={(e) => setInstanceId(e.target.value)}>
              {instances.map((x) => <option value={x.id} key={x.id}>{x.label}</option>)}
            </select>
          </label>
          <label>Datastore
            <select value={datastore} onChange={(e) => setDatastore(e.target.value)}>
              {(selected?.datastores || []).map((x) => <option value={x} key={x}>{x}</option>)}
            </select>
          </label>
          <label>Namespace
            <select value={namespace} onChange={(e) => setNamespace(e.target.value)}>
              {namespaces.map((x) => <option value={x} key={x}>{formatNamespace(x)}</option>)}
            </select>
          </label>
        </div>
        <div className="metrics">
          <article className="metric"><span>Connection</span><strong>{error ? "Needs attention" : type}</strong><small>{selected?.label || "No instance configured"}</small></article>
          <article className="metric"><span>Groups</span><strong>{groups.length}</strong><small>Selected namespace</small></article>
          <article className="metric"><span>Stored data</span><strong>{displayBytes(used)}</strong><small>{total == null ? "Reported by PBS" : `of ${displayBytes(total)} total`}</small></article>
        </div>
        <section className="table-card">
          <div className="section-head">
            <div>
              <h2>Backup groups</h2>
              <p>Datastore <b>{datastore || "—"}</b> · Namespace <b>{formatNamespace(namespace)}</b></p>
            </div>
            <div className="read-only">READ ONLY</div>
          </div>
          <div className="table-scroll"><table>
            <thead><tr><th>Type</th><th>Backup ID</th><th>Snapshots</th><th>Last backup</th></tr></thead>
            <tbody>
              {groups.map((row, index) => {
                const backupType = row["backup-type"] ?? row.backup_type ?? "—";
                const backupId = row["backup-id"] ?? row.backup_id ?? "—";
                const count = row["backup-count"] ?? row.backup_count ?? "—";
                const timestamp = row["last-backup"] ?? row.last_backup;
                const last = typeof timestamp === "number"
                  ? new Date(timestamp * 1000).toLocaleString() : "—";
                return <tr key={`${backupType}-${backupId}-${index}`}>
                  <td><span className="tag">{backupType}</span></td>
                  <td><b>{backupId}</b></td>
                  <td>{count}</td>
                  <td>{last}</td>
                </tr>;
              })}
              {!groups.length && <tr><td colSpan="4" className="empty">
                {loading ? "Loading..." : "No backup groups in this namespace."}
              </td></tr>}
            </tbody>
          </table></div>
        </section>
        <footer>Metadata inventory is not an integrity verification. Use native PBS Verify and restore drills.</footer>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
