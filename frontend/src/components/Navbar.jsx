import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const dashboardPath = user?.role === "admin" ? "/admin" : user?.role === "trainer" ? "/trainer" : "/trainee";

  return (
    <nav className="navbar">
      <Link className="brand" to="/">
        Training Platform
      </Link>
      <div className="nav-links">
        {user ? (
          <>
            <Link to={dashboardPath}>Dashboard</Link>
            <span className="badge">{user.role}</span>
            <span className="muted">{user.full_name}</span>
            <button className="secondary" onClick={handleLogout}>
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/signup">Sign up</Link>
          </>
        )}
      </div>
    </nav>
  );
}
