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

  useEffect(() => {
    const api = import.meta.env.VITE_API_URL || "http://localhost:8000";
    fetch(`${api}/api/overview`)
      .then((response) => { if (!response.ok) throw new Error("API unavailable"); return response.json(); })
      .then((payload: Overview) => { setData(payload); setApiState("connected"); })
      .catch(() => setApiState("demo"));
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
          <div className="panel integrations-panel"><div className="panel-header"><div><h2>Platform integrations</h2><p>Connected infrastructure services</p></div><button className="more-button">•••</button></div><Integration icon={<Boxes size={18}/>} name="NetBox" desc="Inventory & IPAM" state="Pending setup"/><Integration icon={<Activity size={18}/>} name="Zabbix" desc="Monitoring & alerting" state="Pending setup"/><Integration icon={<Gauge size={18}/>} name="Grafana" desc="Metrics visualization" state="Local service"/></div></section>

          <footer><span>InfraVision NOC <b>v0.1.0</b></span><span><span className="pulse"/> All systems nominal <span className="footer-sep">•</span> Built for modern NOC teams</span></footer>
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
function Integration({ icon, name, desc, state }: { icon: React.ReactNode; name: string; desc: string; state: string }) { return <div className="integration-row"><div className="integration-icon">{icon}</div><div className="integration-info"><b>{name}</b><small>{desc}</small></div><span className="integration-state"><i/>{state}</span></div>; }

export default App;
