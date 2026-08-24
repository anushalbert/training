import { useState } from "react";
import Stats from "./Stats";
import Approvals from "./Approvals";
import Announcements from "./Announcements";
import CourseAssignment from "./CourseAssignment";

const TABS = [
  { key: "stats", label: "Stats", component: Stats },
  { key: "approvals", label: "Approvals", component: Approvals },
  { key: "announcements", label: "Announcements", component: Announcements },
  { key: "courses", label: "Course Assignment", component: CourseAssignment },
];

export default function AdminDashboard() {
  const [active, setActive] = useState("stats");
  const ActiveComponent = TABS.find((t) => t.key === active).component;

  return (
    <div className="container">
      <h1>Admin Dashboard</h1>
      <div className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={active === tab.key ? "active" : ""}
            onClick={() => setActive(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <ActiveComponent />
    </div>
  );
}
