import { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertCircle, ArrowDownRight, ArrowUpRight, Bell, Boxes,
  CheckCircle2, ChevronDown, CircleHelp, Clock3, Cpu, Database,
  Gauge, HardDrive, LayoutDashboard, Map, Network, Search, Server,
  Settings2, ShieldCheck, Signal, SlidersHorizontal, Wifi, Zap,
} from "lucide-react";

type Device = { id: string; name: string; type: string; site: string; status: string; cpu: number; memory: number; ip: string };
type Incident = { id: string; severity: string; title: string; device: string; age: string };
type Overview = { demo: boolean; kpis: { availability: number; devices_total: number; devices_online: number; active_incidents: number; sites: number }; devices: Device[]; incidents: Incident[] };
type ProviderStatus = { configured: boolean; reachable: boolean; message: string };
type IntegrationStatus = { netbox: ProviderStatus; zabbix: ProviderStatus; demo_mode: boolean };
type InventoryItem = { external_id: string; name: string; status: string | null; device_type: string | null; device_height?: number | null; role: string | null; site: string | null; tenant: string | null; rack: string | null; position: number | null; face: string | null; primary_ip: string | null; source: string; monitoring_status?: string; match_method?: string | null; zabbix_hosts?: { external_id: string; technical_name: string; name: string; status: string }[] };
type NetBoxRack = { external_id: string; name: string; site: string | null; u_height: number | null; facility: string | null; status: string | null };
type TriggerItem = { external_id: string; title: string; priority: string; last_change: string; hosts: { hostid: string; host: string; name: string }[]; source: string };

const fallback: Overview = {
  demo: true,
  kpis: { availability: 99.94, devices_total: 128, devices_online: 124, active_incidents: 3, sites: 4 },
  devices: [
    { id: "srv-core-01", name: "core-srv-01", type: "Server", site: "São Paulo DC", status: "online", cpu: 24, memory: 68, ip: "10.10.1.11" },
    { id: "sw-dist-02", name: "dist-sw-02", type: "Switch", site: "São Paulo DC", status: "warning", cpu: 71, memory: 54, ip: "10.10.1.22" },
    { id: "fw-edge-01", name: "edge-fw-01", type: "Firewall", site: "Curitiba POP", status: "online", cpu: 18, memory: 42, ip: "10.20.0.1" },
    { id: "nas-backup-01", name: "backup-nas-01", type: "Storage", site: "São Paulo DC", status: "critical", cpu: 12, memory: 81, ip: "10.10.2.30" },
  ],
  incidents: [
    { id: "INC-2048", severity: "critical", title: "Storage pool capacity above 90%", device: "backup-nas-01", age: "8 min" },
    { id: "INC-2047", severity: "warning", title: "High CPU utilization", device: "dist-sw-02", age: "21 min" },
    { id: "INC-2045", severity: "warning", title: "Interface errors detected", device: "core-srv-01", age: "46 min" },
  ],
};

const nav = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Inventory", icon: Boxes },
  { label: "Datacenter", icon: Server },
  { label: "Topology", icon: Network },
  { label: "Incidents", icon: Bell },
];

function App() {
  const [data, setData] = useState<Overview>(fallback);
  const [active, setActive] = useState("Overview");
  const [query, setQuery] = useState("");
  const [apiState, setApiState] = useState("connecting");
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [inventoryDemo, setInventoryDemo] = useState(true);
  const [triggers, setTriggers] = useState<TriggerItem[]>([]);
  const [triggersDemo, setTriggersDemo] = useState(true);

  useEffect(() => {
    const api = import.meta.env.VITE_API_URL || "http://localhost:8000";
    fetch(`${api}/api/overview`)
      .then((response) => { if (!response.ok) throw new Error("API unavailable"); return response.json(); })
      .then((payload: Overview) => { setData(payload); setApiState("connected"); })
      .catch(() => setApiState("demo"));
    fetch(`${api}/api/integrations/status`)
      .then((response) => { if (!response.ok) throw new Error("Integration status unavailable"); return response.json(); })
      .then((payload: IntegrationStatus) => setIntegrations(payload))
      .catch(() => setIntegrations(null));
    fetch(`${api}/api/correlation/inventory`)
      .then((response) => { if (!response.ok) throw new Error("Inventory unavailable"); return response.json(); })
      .then((payload) => { setInventory(payload.results || []); setInventoryDemo(Boolean(payload.demo)); })
      .catch(() => { setInventory([]); setInventoryDemo(true); });
    fetch(`${api}/api/monitoring/triggers`)
      .then((response) => { if (!response.ok) throw new Error("Triggers unavailable"); return response.json(); })
      .then((payload) => { setTriggers(payload.results || []); setTriggersDemo(Boolean(payload.demo)); })
      .catch(() => { setTriggers([]); setTriggersDemo(true); });
  }, []);

  const filteredDevices = useMemo(
    () => data.devices.filter((device) => `${device.name} ${device.type} ${device.ip}`.toLowerCase().includes(query.toLowerCase())),
    [data.devices, query],
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><Activity size={20} /></div><div><strong>INFRA<span>VISION</span></strong><small>NETWORK OPERATIONS</small></div></div>
        <div className="workspace"><span className="workspace-dot" /> Production environment <ChevronDown size={14} /></div>
        <div className="nav-label">WORKSPACE</div>
        <nav>{nav.map(({ label, icon: Icon }) => <button key={label} className={active === label ? "nav-item active" : "nav-item"} onClick={() => setActive(label)}><Icon size={17} /><span>{label}</span>{label === "Incidents" && <em>3</em>}</button>)}</nav>
        <div className="nav-label tools-label">MANAGEMENT</div>
        <button className="nav-item" onClick={() => setActive("Integrations")}><Zap size={17} /><span>Integrations</span></button>
        <button className="nav-item" onClick={() => setActive("Settings")}><Settings2 size={17} /><span>Settings</span></button>
        <div className="sidebar-bottom"><div className="help-card"><CircleHelp size={17}/><div><b>Need help?</b><small>View documentation</small></div></div><div className="profile"><div className="avatar">CS</div><div><b>Cledson Santos</b><small>Administrator</small></div><Settings2 size={16}/></div></div>
      </aside>

      <main className="main-area">
        <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> <b>{active}</b></div><div className="top-actions"><div className={apiState === "connected" ? "connection connected" : "connection"}><span />{apiState === "connected" ? "API connected" : apiState === "demo" ? "Demo mode" : "Connecting"}</div><button className="icon-button"><Bell size={18}/><i /></button><div className="top-avatar">CS</div></div></header>

        <div className="content">
          {active === "Overview" && <>
          <div className="page-heading"><div><div className="eyebrow">MONITORING CENTER <span>•</span> LIVE OVERVIEW</div><h1>Infrastructure overview</h1><p>Real-time visibility across your infrastructure environment.</p></div><div className="heading-actions"><button className="outline-button"><Clock3 size={15}/> Last 24 hours <ChevronDown size={14}/></button><button className="primary-button"><SlidersHorizontal size={15}/> Customize view</button></div></div>
          {data.demo && <div className="demo-banner"><span><ShieldCheck size={15}/> DEMONSTRATION ENVIRONMENT</span><p>Sample telemetry is fictional. Connect NetBox and Zabbix to display live infrastructure data.</p></div>}

          <section className="kpi-grid">
            <Kpi title="Service availability" value={`${data.kpis.availability.toFixed(2)}%`} delta="+0.08%" positive icon={<Gauge size={17}/>} foot="vs. previous 24 hours" />
            <Kpi title="Monitored devices" value={String(data.kpis.devices_total)} delta={`${data.kpis.devices_online} online`} positive icon={<Server size={17}/>} foot="Across all registered sites" />
            <Kpi title="Active incidents" value={String(data.kpis.active_incidents)} delta="2 require attention" icon={<AlertCircle size={17}/>} foot="1 critical · 2 warnings" />
            <Kpi title="Infrastructure sites" value={String(data.kpis.sites)} delta="All locations" positive icon={<Map size={17}/>} foot="Geographically distributed" />
          </section>

          <section className="middle-grid">
            <div className="panel health-panel"><div className="panel-header"><div><h2>Infrastructure health</h2><p>Device status distribution</p></div><button className="more-button">•••</button></div><div className="health-content"><div className="donut-wrap"><div className="donut"><div><strong>{Math.round(data.kpis.devices_online / data.kpis.devices_total * 100)}%</strong><small>ONLINE</small></div></div></div><div className="health-legend"><Legend color="green" label="Online" value={String(data.kpis.devices_online)}/><Legend color="yellow" label="Warning" value="3"/><Legend color="red" label="Critical" value="1"/><Legend color="muted" label="Offline" value="0"/></div></div><div className="panel-foot"><span><span className="pulse" /> Monitoring operational</span><span>Updated just now</span></div></div>
            <div className="panel sites-panel"><div className="panel-header"><div><h2>Sites & locations</h2><p>Infrastructure distribution</p></div><button className="text-button">View all <ArrowUpRight size={14}/></button></div><div className="site-list"><Site name="São Paulo Data Center" city="São Paulo, BR" count="64 devices" percent={78}/><Site name="Curitiba POP" city="Curitiba, BR" count="28 devices" percent={55}/><Site name="Rio de Janeiro Office" city="Rio de Janeiro, BR" count="22 devices" percent={42}/><Site name="Porto Alegre Branch" city="Porto Alegre, BR" count="14 devices" percent={28}/></div></div>
          </section>

          <section className="panel devices-panel"><div className="panel-header"><div><h2>Monitored devices</h2><p>Latest device status from your infrastructure</p></div><div className="table-actions"><label className="search-box"><Search size={15}/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search devices..." /></label><button className="outline-button compact"><SlidersHorizontal size={14}/> Filter</button><button className="text-button">View inventory <ArrowUpRight size={14}/></button></div></div><div className="table-scroll"><table><thead><tr><th>DEVICE</th><th>TYPE</th><th>LOCATION</th><th>IP ADDRESS</th><th>CPU</th><th>MEMORY</th><th>STATUS</th></tr></thead><tbody>{filteredDevices.map((device) => <tr key={device.id}><td><div className="device-name"><div className="device-icon"><Server size={16}/></div><b>{device.name}</b></div></td><td>{device.type}</td><td>{device.site}</td><td className="mono">{device.ip}</td><td><Metric value={device.cpu}/></td><td><Metric value={device.memory}/></td><td><Status status={device.status}/></td></tr>)}</tbody></table>{filteredDevices.length === 0 && <div className="empty-state">No devices match your search.</div>}</div><div className="table-footer">Showing {filteredDevices.length} of {data.kpis.devices_total} devices <button>Open inventory <ArrowUpRight size={13}/></button></div></section>

          <section className="bottom-grid"><div className="panel incidents-panel"><div className="panel-header"><div><h2>Recent incidents</h2><p>Events requiring operator attention</p></div><button className="text-button">Incident center <ArrowUpRight size={14}/></button></div><div className="incident-list">{data.incidents.map((incident) => <div className="incident-row" key={incident.id}><div className={`severity-icon ${incident.severity}`}><AlertCircle size={16}/></div><div className="incident-main"><b>{incident.title}</b><small>{incident.id} <span>•</span> {incident.device}</small></div><span className={`severity-pill ${incident.severity}`}>{incident.severity}</span><small className="incident-age">{incident.age} ago</small></div>)}</div></div>
          <div className="panel integrations-panel"><div className="panel-header"><div><h2>Platform integrations</h2><p>Connected infrastructure services</p></div><button className="more-button">•••</button></div><Integration icon={<Boxes size={18}/>} name="NetBox" desc="Inventory & IPAM" state={providerLabel(integrations?.netbox)}/><Integration icon={<Activity size={18}/>} name="Zabbix" desc="Monitoring & alerting" state={providerLabel(integrations?.zabbix)}/><Integration icon={<Gauge size={18}/>} name="Grafana" desc="Metrics visualization" state="Local service"/></div></section>

          <footer><span>InfraVision NOC <b>v0.5.0</b></span><span><span className="pulse"/> All systems nominal <span className="footer-sep">•</span> Built for modern NOC teams</span></footer>
          </>}
          {active === "Inventory" && <InventoryPage devices={inventory} demo={inventoryDemo} fallback={data.devices} />}
          {active === "Datacenter" && <DatacenterPage />}
          {active === "Topology" && <TopologyPage />}
          {active === "Incidents" && <IncidentsPage triggers={triggers} demo={triggersDemo} fallback={data.incidents} />}
          {active === "Integrations" && <IntegrationsPage integrations={integrations} />}
          {active === "Settings" && <SettingsPage />}
        </div>
      </main>
    </div>
  );
}

function Kpi({ title, value, delta, positive, icon, foot }: { title: string; value: string; delta: string; positive?: boolean; icon: React.ReactNode; foot: string }) {
  return <div className="panel kpi-card"><div className="kpi-top"><span>{title}</span><div className="kpi-icon">{icon}</div></div><div className="kpi-value">{value}</div><div className="kpi-delta">{positive ? <ArrowUpRight size={14}/> : <ArrowDownRight size={14}/>}<b className={positive ? "positive" : ""}>{delta}</b></div><small>{foot}</small></div>;
}
function Legend({ color, label, value }: { color: string; label: string; value: string }) { return <div className="legend-row"><span className={`legend-dot ${color}`}/><span>{label}</span><b>{value}</b></div>; }
function Site({ name, city, count, percent }: { name: string; city: string; count: string; percent: number }) { return <div className="site-row"><div className="site-pin"><Map size={15}/></div><div className="site-info"><b>{name}</b><small>{city}</small></div><div className="site-devices"><b>{count}</b><div className="site-bar"><i style={{width:`${percent}%`}}/></div></div></div>; }
function Metric({ value }: { value: number }) { return <div className="metric"><span>{value}%</span><div><i style={{width:`${value}%`}}/></div></div>; }
function Status({ status }: { status: string }) { return <span className={`status-badge ${status}`}><i/>{status}</span>; }
function providerLabel(provider?: ProviderStatus) { if (!provider) return "API unavailable"; if (!provider.configured) return "Not configured"; return provider.reachable ? "Connected" : "Unreachable"; }
function Integration({ icon, name, desc, state }: { icon: React.ReactNode; name: string; desc: string; state: string }) { const connected = state === "Connected" || state === "Local service"; return <div className="integration-row"><div className="integration-icon">{icon}</div><div className="integration-info"><b>{name}</b><small>{desc}</small></div><span className={connected ? "integration-state connected" : "integration-state"}><i/>{state}</span></div>; }

export default App;


function PageTitle({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div></div>;
}

function InventoryPage({ devices, demo, fallback }: { devices: InventoryItem[]; demo: boolean; fallback: Device[] }) {
  const rows: InventoryItem[] = demo ? fallback.map((item) => ({
    external_id: item.id, name: item.name, status: item.status, device_type: item.type,
    role: null, site: item.site, tenant: "Demo tenant", rack: null, position: null,
    face: null, primary_ip: item.ip, source: "demo", monitoring_status: "demo",
  })) : devices;

  return <div className="page-stack">
    <PageTitle eyebrow="ASSET MANAGEMENT • INVENTORY" title="Infrastructure inventory" description="NetBox assets correlated with their Zabbix monitoring hosts."/>
    {demo && <div className="demo-banner"><span><ShieldCheck size={15}/> DEMONSTRATION INVENTORY</span><p>These example assets are fictional. Configure read-only NetBox and Zabbix API credentials to load and correlate your real inventory.</p></div>}
    <div className="kpi-grid inventory-summary">
      <Kpi title="Registered devices" value={String(rows.length)} delta={demo ? "Sample assets" : "From NetBox"} positive icon={<Server size={17}/>} foot="Current inventory result"/>
      <Kpi title="Zabbix matched" value={String(demo ? 0 : rows.filter((item) => item.monitoring_status === "matched").length)} delta="Exact hostname or IP" positive icon={<Activity size={17}/>} foot="Correlated monitoring hosts"/>
      <Kpi title="Ambiguous matches" value={String(demo ? 0 : rows.filter((item) => item.monitoring_status === "ambiguous").length)} delta="Operator review" icon={<AlertCircle size={17}/>} foot="Never merged automatically"/>
      <Kpi title="Unmonitored" value={String(demo ? 0 : rows.filter((item) => item.monitoring_status === "unmonitored").length)} delta="No Zabbix match" icon={<Network size={17}/>} foot="Inventory devices not monitored"/>
    </div>
    <div className="panel inventory-panel">
      <div className="panel-header"><div><h2>Device registry</h2><p>{demo ? "Illustrative data set" : "Live NetBox inventory"}</p></div><span className={demo ? "source-pill demo" : "source-pill live"}>{demo ? "DEMO SOURCE" : "NETBOX + ZABBIX"}</span></div>
      <div className="table-scroll"><table><thead><tr><th>DEVICE</th><th>DEVICE TYPE</th><th>SITE</th><th>RACK</th><th>POSITION</th><th>TENANT</th><th>PRIMARY IP</th><th>STATUS</th><th>MONITORING</th></tr></thead><tbody>
        {rows.map((item) => <tr key={item.external_id}><td><div className="device-name"><div className="device-icon"><Server size={16}/></div><b>{item.name}</b></div></td><td>{item.device_type || item.role || "—"}</td><td>{item.site || "—"}</td><td>{item.rack || "Unassigned"}</td><td>{item.position ? `U${item.position} · ${item.face || "—"}` : "—"}</td><td>{item.tenant || "—"}</td><td className="mono">{item.primary_ip || "—"}</td><td><Status status={item.status === "active" || item.status === "online" ? "online" : item.status === "offline" ? "critical" : "warning"}/></td><td><MonitoringBadge status={item.monitoring_status || (demo ? "demo" : "unmonitored")} method={item.match_method}/></td></tr>)}
      </tbody></table>{rows.length === 0 && <div className="empty-state">No devices returned by NetBox. Check the token permissions and inventory filters.</div>}</div>
      <div className="table-footer">Showing {rows.length} inventory records <span>Read-only synchronization</span></div>
    </div>
  </div>;
}

type RackDevice = {
  id: string; name: string; model: string; startU: number; heightU: number;
  gridRow?: number; side: "front" | "rear";
  status: "online" | "warning" | "critical" | "registered";
  assetStatus?: string; role: string; ip: string; cpu: number | null; memory: number | null;
};
const rackDevices: RackDevice[] = [
  { id: "rtr-core-01", name: "CORE-RTR-01", model: "Cisco Catalyst 8500 · 2U", startU: 42, heightU: 2, side: "front", status: "online", role: "Core router", ip: "10.10.0.1", cpu: 24, memory: 42 },
  { id: "sw-spine-01", name: "SPINE-SW-01", model: "Arista 7050X · 1U", startU: 39, heightU: 1, side: "front", status: "online", role: "Spine switch", ip: "10.10.0.11", cpu: 33, memory: 49 },
  { id: "sw-spine-02", name: "SPINE-SW-02", model: "Arista 7050X · 1U", startU: 37, heightU: 1, side: "front", status: "warning", role: "Spine switch", ip: "10.10.0.12", cpu: 78, memory: 62 },
  { id: "fw-edge-01", name: "EDGE-FW-01", model: "FortiGate 200F · 2U", startU: 34, heightU: 2, side: "front", status: "online", role: "Perimeter firewall", ip: "10.10.0.254", cpu: 19, memory: 51 },
  { id: "srv-esx-01", name: "VM-HOST-01", model: "Dell PowerEdge R750 · 2U", startU: 29, heightU: 2, side: "front", status: "online", role: "Virtualization host", ip: "10.10.1.21", cpu: 54, memory: 73 },
  { id: "srv-esx-02", name: "VM-HOST-02", model: "Dell PowerEdge R750 · 2U", startU: 26, heightU: 2, side: "front", status: "online", role: "Virtualization host", ip: "10.10.1.22", cpu: 41, memory: 66 },
  { id: "nas-san-01", name: "SAN-STORAGE-01", model: "Dell PowerStore · 3U", startU: 21, heightU: 3, side: "front", status: "critical", role: "Primary storage", ip: "10.10.2.30", cpu: 12, memory: 91 },
  { id: "patch-01", name: "PATCH-PANEL-01", model: "48-port Cat6 · 1U", startU: 15, heightU: 1, side: "front", status: "online", role: "Copper patch panel", ip: "—", cpu: null, memory: null },
  { id: "pdu-a", name: "PDU-A", model: "Metered PDU · 0U", startU: 42, heightU: 1, side: "rear", status: "online", role: "Power distribution", ip: "10.10.9.11", cpu: null, memory: null },
  { id: "pdu-b", name: "PDU-B", model: "Metered PDU · 0U", startU: 42, heightU: 1, side: "rear", status: "online", role: "Redundant power", ip: "10.10.9.12", cpu: null, memory: null },
  { id: "cable-manager", name: "CABLE-MGMT", model: "Vertical cable manager · 0U", startU: 35, heightU: 1, side: "rear", status: "online", role: "Cable management", ip: "—", cpu: null, memory: null },
];

function DatacenterPage() {
  const api = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const [side, setSide] = useState<"front" | "rear">("front");
  const [selected, setSelected] = useState("nas-san-01");
  const [netboxRacks, setNetboxRacks] = useState<NetBoxRack[]>([]);
  const [netboxDevices, setNetboxDevices] = useState<InventoryItem[]>([]);
  const [activeRackId, setActiveRackId] = useState("");
  const [usingNetBox, setUsingNetBox] = useState(false);
  const [rackLoading, setRackLoading] = useState(false);
  const [rackError, setRackError] = useState("");

  useEffect(() => {
    let active = true;
    fetch(`${api}/api/inventory/racks`)
      .then((response) => { if (!response.ok) throw new Error("NetBox rack query failed"); return response.json(); })
      .then((payload) => {
        if (!active || payload.demo) return;
        setUsingNetBox(true);
        setNetboxRacks(payload.results || []);
        if (payload.results?.length) { setActiveRackId(String(payload.results[0].external_id)); setSelected(""); }
      })
      .catch(() => { if (active) setRackError("Unable to load NetBox racks. Showing the sample rack."); });
    return () => { active = false; };
  }, [api]);

  useEffect(() => {
    if (!usingNetBox || !activeRackId) return;
    let active = true;
    setRackLoading(true);
    fetch(`${api}/api/inventory/racks/${activeRackId}/devices`)
      .then((response) => { if (!response.ok) throw new Error("Rack device query failed"); return response.json(); })
      .then((payload) => {
        if (!active) return;
        const devices = payload.results || [];
        setNetboxDevices(devices);
        const first = devices.find((item: InventoryItem) => item.position && item.face !== "rear") || devices.find((item: InventoryItem) => item.position);
        setSelected(first ? String(first.external_id) : "");
        setRackError("");
      })
      .catch(() => { if (active) setRackError("Could not retrieve devices for this rack."); })
      .finally(() => { if (active) setRackLoading(false); });
    return () => { active = false; };
  }, [api, activeRackId, usingNetBox]);

  const activeRack = netboxRacks.find((rack) => String(rack.external_id) === activeRackId);
  const rackHeight = usingNetBox ? (activeRack?.u_height || 42) : 42;
  const liveRackDevices: RackDevice[] = netboxDevices.filter((item) => item.position !== null && item.position !== undefined).map((item) => {
    const position = Number(item.position);
    return {
      id: String(item.external_id), name: item.name, model: item.device_type || item.role || "Installed device",
      startU: position, heightU: Math.max(1, Number(item.device_height || 1)), gridRow: Math.max(1, rackHeight - position + 2 - Math.max(1, Number(item.device_height || 1))),
      side: item.face === "rear" ? "rear" : "front", status: "registered",
      assetStatus: String(item.status || "unknown"), role: item.role || item.device_type || "Infrastructure device",
      ip: item.primary_ip || "—", cpu: null, memory: null,
    };
  });
  const currentDevices = usingNetBox ? liveRackDevices : rackDevices;
  const visibleDevices = currentDevices.filter((device) => device.side === side);
  const selectedDevice = currentDevices.find((device) => device.id === selected) || visibleDevices[0] || null;

  return <div className="page-stack">
    <PageTitle eyebrow="PHYSICAL INFRASTRUCTURE • RACK VIEW" title="Datacenter visualization" description="Explore rack elevations, inspect equipment placement and review device health."/>
    {!usingNetBox && <div className="demo-banner"><span><ShieldCheck size={15}/> SIMULATED RACK</span><p>{rackError || "Rack R01 is a fictional 42U demonstration layout. Configure NetBox to load real rack positions."}</p></div>}
    {usingNetBox && <div className="demo-banner live-rack-banner"><span><CheckCircle2 size={15}/> LIVE NETBOX INVENTORY</span><p>Rack layout and equipment positions are loaded from NetBox. Health metrics require Zabbix correlation.</p></div>}
    <div className="rack-toolbar panel">
      <div><span className="rack-kicker">SITE</span><b>{activeRack?.site || (usingNetBox ? "NetBox site" : "São Paulo Data Center")}</b></div>
      <div><span className="rack-kicker">FACILITY</span><b>{activeRack?.facility || (usingNetBox ? "Not specified" : "DC-01 · Row A")}</b></div>
      <div><span className="rack-kicker">RACK</span>{usingNetBox ? <select className="rack-select" value={activeRackId} onChange={(event) => setActiveRackId(event.target.value)}>{netboxRacks.map((rack) => <option key={rack.external_id} value={rack.external_id}>{rack.name} · {rack.u_height || 42}U</option>)}</select> : <b>R01 · 42U</b>}</div>
      <div className="rack-side-switch"><button className={side === "front" ? "selected" : ""} onClick={() => setSide("front")}>Front view</button><button className={side === "rear" ? "selected" : ""} onClick={() => setSide("rear")}>Rear view</button></div>
    </div>
    <div className="rack-layout">
      <div className="panel rack-panel"><div className="panel-header"><div><h2>{activeRack?.name || (usingNetBox ? "Select a rack" : "Rack R01")} elevation</h2><p>{side === "front" ? "Front equipment access" : "Rear cabling and power access"}</p></div><span className={usingNetBox ? "source-pill live" : "source-pill demo"}>{rackHeight}U RACK</span></div>
        {rackLoading ? <div className="empty-state">Loading rack devices from NetBox…</div> : <div className="rack-stage"><div className="rack-numbers" style={{gridTemplateRows:`repeat(${rackHeight},12px)`}}>{Array.from({length:rackHeight}, (_,i) => <span key={i}>U{rackHeight-i}</span>)}</div><div className="rack-frame"><div className="rack-grid" style={{gridTemplateRows:`repeat(${rackHeight},12px)`}}>{visibleDevices.map((device) => <button key={device.id} className={`rack-device ${device.status} ${selected === device.id ? "chosen" : ""}`} style={{gridRow:`${usingNetBox ? device.gridRow : 43-device.startU} / span ${device.heightU}`}} onClick={() => setSelected(device.id)} title={device.model}><span className="rack-device-lights"><i/><i/><i/></span><b>{device.name}</b><small>{device.model}</small></button>)}</div></div></div>}
        {usingNetBox && !rackLoading && visibleDevices.length === 0 && <div className="empty-state">No devices with rack positions on this side.</div>}
        <div className="rack-legend"><span><i className="green-dot"/> Online</span><span><i className="yellow-dot"/> Warning</span><span><i className="red-dot"/> Critical</span>{usingNetBox && <span><i className="registered-dot"/> Registered asset</span>}<span><i className="empty-dot"/> Empty U space</span></div>
      </div>
      <div className="panel rack-detail"><div className="panel-header"><div><h2>Equipment details</h2><p>Selected rack component</p></div><Server size={17} color="#42cba6"/></div>
        {selectedDevice ? <>
          <div className="rack-detail-visual"><div className="rack-detail-illustration"><div className="rack-leds"><i/><i/><i/><i/></div><div className="rack-detail-face"><span/><span/><span/><span/><span/><span/></div></div></div><span className="rack-kicker">DEVICE NAME</span><h3>{selectedDevice.name}</h3><p className="rack-model">{selectedDevice.model}</p><Status status={selectedDevice.status}/>
          <div className="detail-list"><div><span>Role</span><b>{selectedDevice.role}</b></div><div><span>Management IP</span><b className="mono">{selectedDevice.ip}</b></div><div><span>Rack position</span><b>U{selectedDevice.startU}</b></div>{usingNetBox && <div><span>NetBox lifecycle</span><b>{selectedDevice.assetStatus}</b></div>}<div><span>CPU utilization</span><b>{selectedDevice.cpu === null ? "Not available" : `${selectedDevice.cpu}%`}</b></div><div><span>Memory utilization</span><b>{selectedDevice.memory === null ? "Not available" : `${selectedDevice.memory}%`}</b></div></div>
          <small className="demo-note">{usingNetBox ? "Physical placement from NetBox. Live health telemetry requires Zabbix correlation." : "Illustrative rack placement and telemetry. Sample values are fictional."}</small>
        </> : <div className="empty-state">Select a device in the rack to inspect its inventory details.</div>}
      </div>
    </div>
  </div>;
}

function TopologyPage() {
  return <div className="page-stack">
    <PageTitle eyebrow="NETWORK OPERATIONS • TOPOLOGY" title="Network topology" description="A logical map of the simulated core, security, switching and compute layers."/>
    <div className="demo-banner"><span><ShieldCheck size={15}/> DEMONSTRATION TOPOLOGY</span><p>Connections are illustrative. Interface-level links will be populated from NetBox cable and interface relationships.</p></div>
    <div className="panel topology-panel"><div className="panel-header"><div><h2>São Paulo Data Center · Network fabric</h2><p>Logical connectivity overview</p></div><span className="source-pill demo">SAMPLE NETWORK</span></div>
      <div className="topology-map">
        <div className="topology-tier"><div className="topology-node core"><Network size={20}/><div><b>CORE-RTR-01</b><small>Core router · 10.10.0.1</small></div><Status status="online"/></div></div>
        <div className="topology-connectors"><span/><span/></div>
        <div className="topology-tier two"><div className="topology-node"><ShieldCheck size={20}/><div><b>EDGE-FW-01</b><small>Firewall · 10.10.0.254</small></div><Status status="online"/></div><div className="topology-node"><Network size={20}/><div><b>SPINE-SW-01</b><small>Spine switch · 10.10.0.11</small></div><Status status="online"/></div></div>
        <div className="topology-connectors"><span/><span/><span/></div>
        <div className="topology-tier three"><div className="topology-node"><Network size={20}/><div><b>DIST-SW-01</b><small>Distribution · VLAN trunk</small></div><Status status="online"/></div><div className="topology-node"><Network size={20}/><div><b>SPINE-SW-02</b><small>Spine switch · 10.10.0.12</small></div><Status status="warning"/></div><div className="topology-node"><Database size={20}/><div><b>SAN-STORAGE-01</b><small>Storage · 10.10.2.30</small></div><Status status="critical"/></div></div>
        <div className="topology-connectors"><span/><span/><span/></div>
        <div className="topology-tier three"><div className="topology-node endpoint"><Server size={19}/><div><b>VM-HOST-01</b><small>Hypervisor · 10.10.1.21</small></div><Status status="online"/></div><div className="topology-node endpoint"><Server size={19}/><div><b>VM-HOST-02</b><small>Hypervisor · 10.10.1.22</small></div><Status status="online"/></div><div className="topology-node endpoint"><Activity size={19}/><div><b>NOC-MON-01</b><small>Zabbix / Grafana</small></div><Status status="online"/></div></div>
      </div>
      <div className="topology-foot"><span><i className="green-dot"/> Healthy link</span><span><i className="yellow-dot"/> Degraded node</span><span><i className="red-dot"/> Critical node</span></div>
    </div>
  </div>;
}

function IncidentsPage({ triggers, demo, fallback }: { triggers: TriggerItem[]; demo: boolean; fallback: Incident[] }) {
  const items = demo ? fallback.map((item) => ({ id: item.id, title: item.title, device: item.device, severity: item.severity, age: item.age })) : triggers.map((item) => ({
    id: item.external_id,
    title: item.title || "Zabbix trigger",
    device: item.hosts?.map((host) => host.name || host.host).join(", ") || "Unassigned host",
    severity: Number(item.priority) >= 4 ? "critical" : Number(item.priority) >= 2 ? "warning" : "info",
    age: item.last_change ? new Date(Number(item.last_change) * 1000).toLocaleString() : "Unknown",
  }));
  return <div className="page-stack">
    <PageTitle eyebrow="OPERATIONS • EVENT MANAGEMENT" title="Incident center" description="Review active alerts, prioritize affected assets and identify the source system."/>
    {demo && <div className="demo-banner"><span><ShieldCheck size={15}/> DEMONSTRATION INCIDENTS</span><p>These sample incidents are fictional. Configure Zabbix to retrieve active triggers from your monitoring environment.</p></div>}
    <div className="incident-summary"><div className="panel"><span>Active incidents</span><b>{items.length}</b></div><div className="panel"><span>Critical</span><b className="critical-text">{items.filter((item) => item.severity === "critical").length}</b></div><div className="panel"><span>Warnings</span><b className="warning-text">{items.filter((item) => item.severity === "warning").length}</b></div><div className="panel"><span>Source</span><b className="source-text">{demo ? "Demo" : "Zabbix"}</b></div></div>
    <div className="panel inventory-panel"><div className="panel-header"><div><h2>Open event queue</h2><p>Sorted by severity from highest to lowest</p></div><span className={demo ? "source-pill demo" : "source-pill live"}>{demo ? "DEMO SOURCE" : "ZABBIX SOURCE"}</span></div>
      <div className="incident-list">{items.map((item) => <div className="incident-row" key={item.id}><div className={`severity-icon ${item.severity}`}><AlertCircle size={16}/></div><div className="incident-main"><b>{item.title}</b><small>{item.id} <span>•</span> {item.device}</small></div><span className={`severity-pill ${item.severity}`}>{item.severity}</span><small className="incident-age">{item.age}</small></div>)}
      {items.length === 0 && <div className="empty-state">No active Zabbix triggers were returned.</div>}</div>
    </div>
  </div>;
}

function IntegrationsPage({ integrations }: { integrations: IntegrationStatus | null }) {
  const providers = [
    { name: "NetBox", description: "Inventory, sites, racks, devices, interfaces and IPAM.", state: integrations?.netbox, icon: <Boxes size={22}/> },
    { name: "Zabbix", description: "Monitored hosts, trigger state and telemetry collection.", state: integrations?.zabbix, icon: <Activity size={22}/> },
  ];
  return <div className="page-stack">
    <PageTitle eyebrow="PLATFORM MANAGEMENT • CONNECTORS" title="Integrations" description="Manage the upstream systems that provide the platform's source-of-truth data."/>
    <div className="integration-cards">{providers.map((provider) => <div className="panel integration-card" key={provider.name}><div className="integration-card-top"><div className="integration-big-icon">{provider.icon}</div><span className={provider.state?.reachable ? "source-pill live" : "source-pill demo"}>{providerLabel(provider.state).toUpperCase()}</span></div><h2>{provider.name}</h2><p>{provider.description}</p><div className="integration-message">{provider.state?.message || "API status has not been retrieved."}</div><div className="integration-meta"><span>Configured</span><b>{provider.state?.configured ? "Yes" : "No"}</b></div><div className="integration-meta"><span>Reachable</span><b>{provider.state?.reachable ? "Yes" : "No"}</b></div></div>)}</div>
    <div className="panel integration-guide"><h2>Configure credentials</h2><p>Set these environment variables in the project root <code>.env</code> file. Do not paste tokens into source code or commit them to GitHub.</p><pre>{`NETBOX_URL=https://netbox.your-domain.com\nNETBOX_TOKEN=nbt_your_read_only_token\nZABBIX_URL=https://zabbix.your-domain.com\nZABBIX_TOKEN=your_read_only_api_token`}</pre><p className="guide-note">After updating the values, restart the backend service. See <b>docs/INTEGRATIONS.md</b> for token and permission guidance.</p></div>
  </div>;
}

function SettingsPage() {
  return <div className="page-stack">
    <PageTitle eyebrow="PLATFORM MANAGEMENT • CONFIGURATION" title="Settings" description="Local environment information and operational safety controls."/>
    <div className="panel settings-panel"><h2>Environment</h2><div className="settings-row"><span>Application version</span><b>0.5.0</b></div><div className="settings-row"><span>Runtime mode</span><b>Development</b></div><div className="settings-row"><span>API base URL</span><b>http://localhost:8000</b></div><div className="settings-row"><span>Frontend</span><b>React + Vite</b></div><div className="settings-row"><span>Backend</span><b>FastAPI + Python</b></div></div>
    <div className="panel settings-panel"><h2>Security baseline</h2><div className="security-check"><ShieldCheck size={17}/><div><b>Secrets are environment-based</b><small>Keep API tokens in .env. The file is excluded from Git.</small></div></div><div className="security-check"><ShieldCheck size={17}/><div><b>Read-only integrations</b><small>NetBox and Zabbix adapters only issue retrieval requests.</small></div></div><div className="security-check"><AlertCircle size={17}/><div><b>Not production-hardened</b><small>Authentication, RBAC, tenant isolation and audit controls remain on the roadmap.</small></div></div></div>
  </div>;
}

function MonitoringBadge({ status, method }: { status: string; method?: string | null }) {
  const normalized = status === "matched" ? "matched" : status === "ambiguous" ? "ambiguous" : status === "unmonitored" ? "unmonitored" : "demo";
  const label = normalized === "matched"
    ? `Matched · ${method === "hostname" ? "hostname" : method === "management_ip" ? "management IP" : "source"}`
    : normalized === "ambiguous" ? "Ambiguous"
    : normalized === "unmonitored" ? "Unmonitored"
    : "Demo data";
  return <span className={`monitoring-badge ${normalized}`}>{label}</span>;
}
