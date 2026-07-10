import { createBrowserRouter } from "react-router";
import { LoginPage } from "./components/LoginPage";
import { FacultyDashboard } from "./components/FacultyDashboard";
import { StudentDashboard } from "./components/StudentDashboard";
import { AdminDashboard } from "./components/AdminDashboard";
import { AdminLoginPage } from "./components/AdminLoginPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: LoginPage,
  },
  {
    path: "/faculty",
    Component: FacultyDashboard,
  },
  {
    path: "/student",
    Component: StudentDashboard,
  },
  {
    path: "/admin",
    Component: AdminDashboard,
  },
  {
    path: "/admin-login",
    Component: AdminLoginPage,
  },
]);
