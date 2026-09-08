import React from 'react';
import { NavLink } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import AiStatusIndicator from './AiStatusIndicator';

function Brand() {
  return (
    <span className="navbar-brand">
      <span role="img" aria-hidden="true">&#129302;</span> JobWise AI
    </span>
  );
}

export default function NavBar() {
  const { user, logout } = useAuth();

  if (!user) {
    return (
      <nav className="navbar">
        <Brand />
        <div className="navbar-links">
          <NavLink to="/" className="nav-link" end>
            Home
          </NavLink>
          <NavLink to="/login" className="nav-link">
            Login
          </NavLink>
          <NavLink to="/register" className="nav-link btn btn-outline nav-cta">
            Get Started
          </NavLink>
        </div>
      </nav>
    );
  }

  return (
    <nav className="navbar">
      <Brand />
      <div className="navbar-links">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/jobs"
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          Browse Jobs
        </NavLink>
        <NavLink
          to="/resume"
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          My Resume
        </NavLink>
        <span className="navbar-user">{user.full_name}</span>
        <AiStatusIndicator />
        <button type="button" className="btn btn-outline" onClick={logout}>
          Logout
        </button>
      </div>
    </nav>
  );
}