import { NavLink, Outlet } from "react-router-dom";
import ThemeToggle from "./ThemeToggle";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: "⊞" },
  { to: "/ask", label: "Ask Agent", icon: "▷" },
  { to: "/documents", label: "Documents", icon: "◈" },
  { to: "/approvals", label: "Approvals", icon: "◎" },
  { to: "/risk", label: "Risk Scoring", icon: "△" },
  { to: "/tools", label: "MCP Tools", icon: "⚙" },
  { to: "/evaluate", label: "Evaluation", icon: "✓" },
];

export default function Layout() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title-row">
            <h1>AgentOS</h1>
            <ThemeToggle />
          </div>
          <span className="sidebar-subtitle">Enterprise AI Platform</span>
        </div>
        <nav>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `nav-link ${isActive ? "active" : ""}`
              }
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
