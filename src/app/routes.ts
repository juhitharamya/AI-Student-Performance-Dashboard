import { createBrowserRouter } from "react-router";
import { LoginPage } from "./components/LoginPage";
import { FacultyDashboard } from "./components/FacultyDashboard";
import { StudentDashboard } from "./components/StudentDashboard";

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
]);
