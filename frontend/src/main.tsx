import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './state/Auth';
import { ErrorState, Loading, ToastProvider } from './components/UI';
import Shell from './components/Shell';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ResourceList from './pages/ResourceList';
import ResourceForm from './pages/ResourceForm';
import ResourceDetail from './pages/ResourceDetail';
import RelatedList from './pages/RelatedList';
import AcademicRecord from './pages/AcademicRecord';
import MyStudents from './pages/MyStudents';
import Profile from './pages/Profile';
import { resources } from './features/resources';
import type { Resource } from './features/resources';
import { ApiError } from './api/client';
import './styles/global.css';
function Protected() {
  const { user, loading, error, retry } = useAuth();
  const location = useLocation();
  if (loading) return <Loading label="Opening your workspace…" />;
  if (error) return <ErrorState error={error} retry={retry} />;
  return user ? (
    <Outlet />
  ) : (
    <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  );
}
export function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Protected />}>
            <Route element={<Shell />}>
              <Route index element={<Dashboard />} />
              {(Object.keys(resources) as Resource[]).map((resource) => (
                <Route key={resource} path={resource}>
                  <Route index element={<ResourceList resource={resource} />} />
                  <Route path="new" element={<ResourceForm resource={resource} />} />
                  <Route path=":id" element={<ResourceDetail resource={resource} />} />
                  <Route path=":id/edit" element={<ResourceForm resource={resource} />} />
                </Route>
              ))}
              <Route path="students/:id/enrollments" element={<RelatedList kind="enrollments" />} />
              <Route path="students/:id/grades" element={<RelatedList kind="grades" />} />
              <Route path="course-offerings/:id/students" element={<RelatedList kind="roster" />} />
              <Route path="my-students" element={<MyStudents />} />
              <Route path="academic-record" element={<AcademicRecord />} />
              <Route path="profile" element={<Profile />} />
              <Route
                path="*"
                element={
                  <ErrorState
                    error={
                      new ApiError(
                        404,
                        'This page does not exist. Choose a module from the navigation.'
                      )
                    }
                  />
                }
              />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </ToastProvider>
  );
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
