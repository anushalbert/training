import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./routes/ProtectedRoute";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Unauthorized from "./pages/Unauthorized";

import AdminDashboard from "./pages/admin/AdminDashboard";

import TrainerDashboard from "./pages/trainer/TrainerDashboard";
import UploadMaterial from "./pages/trainer/UploadMaterial";
import CreateQuestionnaire from "./pages/trainer/CreateQuestionnaire";

import TraineeDashboard from "./pages/trainee/TraineeDashboard";
import Profile from "./pages/trainee/Profile";
import Enrollments from "./pages/trainee/Enrollments";
import TakeAssessment from "./pages/trainee/TakeAssessment";

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/unauthorized" element={<Unauthorized />} />

        <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
          <Route path="/admin" element={<AdminDashboard />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={["trainer"]} />}>
          <Route path="/trainer" element={<TrainerDashboard />} />
          <Route path="/trainer/courses/:courseId/materials" element={<UploadMaterial />} />
          <Route path="/trainer/courses/:courseId/questionnaire" element={<CreateQuestionnaire />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={["trainee"]} />}>
          <Route path="/trainee" element={<TraineeDashboard />} />
          <Route path="/trainee/profile" element={<Profile />} />
          <Route path="/trainee/enrollments" element={<Enrollments />} />
          <Route path="/trainee/assessments/:assessmentId" element={<TakeAssessment />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  );
}
