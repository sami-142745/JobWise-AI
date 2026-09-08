import React from 'react';
import { Link } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';

export default function Welcome() {
  const { user } = useAuth();

  return (
    <div className="landing">
      <section className="hero">
        <div className="hero-badge">AI-Powered Job Matching</div>
        <h1>Find the job your skills were made for.</h1>
        <p className="hero-sub">
          Upload your resume. Our AI agent analyzes your skills, experience, and
          preferences — then matches you with roles that actually fit.
        </p>
        <div className="hero-actions">
          {user ? (
            <Link to="/dashboard" className="btn btn-primary btn-lg">
              Go to Dashboard
            </Link>
          ) : (
            <>
              <Link to="/register" className="btn btn-primary btn-lg">
                Get Started — It’s Free
              </Link>
              <Link to="/login" className="btn btn-outline btn-lg">
                Log In
              </Link>
            </>
          )}
        </div>
      </section>

      <section className="features">
        <div className="feature-card">
          <div className="feature-icon">🧠</div>
          <h3>Resume Analysis</h3>
          <p>
            The AI agent reads your resume (PDF, DOCX, or TXT) and extracts your
            skills and experience automatically.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🎯</div>
          <h3>Smart Matching</h3>
          <p>
            Jobs are scored against your profile so you can see exactly how well
            you match — and what skills to build.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🔍</div>
          <h3>Powerful Search</h3>
          <p>
            Search live job listings by title, company, skill, or location and
            apply in a couple of clicks.
          </p>
        </div>
      </section>
    </div>
  );
}