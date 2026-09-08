import React from 'react';
import { Route, Routes } from 'react-router-dom';

import NavBar from './components/NavBar';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import Dashboard from './pages/Dashboard';
import JobDetail from './pages/JobDetail';
import Jobs from './pages/Jobs';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import Register from './pages/Register';
import Resume from './pages/Resume';
import Welcome from './pages/Welcome';

export default function App() {
  return (
    <AuthProvider>
      <div className="app-shell">
        <NavBar />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Welcome />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/jobs"
              element={
                <ProtectedRoute>
                  <Jobs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/jobs/:id"
              element={
                <ProtectedRoute>
                  <JobDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/resume"
              element={
                <ProtectedRoute>
                  <Resume />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <footer className="app-footer muted">
          JobWise AI · Built with FastAPI, MongoDB, and React
        </footer>
      </div>
    </AuthProvider>
  );
}