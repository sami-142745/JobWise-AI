import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import Alert from '../components/Alert';
import JobCard from '../components/JobCard';
import Spinner from '../components/Spinner';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';

export default function Dashboard() {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [recs, prof] = await Promise.all([
          api.getRecommendations(6),
          api.getResumeProfile().catch(() => null),
        ]);
        if (cancelled) return;
        setRecommendations(recs);
        setProfile(prof);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <Spinner label="Fetching your recommendations…" />;

  const hasProfile = Boolean(profile);

  return (
    <div className="page">
      <header className="page-header">
        <h1>Welcome back, {user.full_name.split(' ')[0]} 👋</h1>
        <p className="muted">Here’s what the AI agent found for you today.</p>
      </header>

      {error && <Alert kind="error">{error}</Alert>}

      <section className="stats-grid">
        <div className="stat-card">
          <span className="stat-value">{user.skills?.length || 0}</span>
          <span className="stat-label">Identified skills</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{profile?.years_experience ?? 0}y</span>
          <span className="stat-label">Experience</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{recommendations.length}</span>
          <span className="stat-label">Top matches</span>
        </div>
      </section>

      {!hasProfile && (
        <div className="cta-banner">
          <div>
            <h2>Unlock personalized recommendations</h2>
            <p className="muted">
              Upload your resume and let the AI agent analyze your skills to
              recommend the best jobs for you.
            </p>
          </div>
          <Link to="/resume" className="btn btn-primary">
            Upload Resume
          </Link>
        </div>
      )}

      {hasProfile && (
        <section>
          <div className="section-head">
            <h2>Top matches for you</h2>
            <Link to="/jobs" className="btn btn-outline btn-sm">
              Browse all jobs
            </Link>
          </div>
          <div className="job-grid">
            {recommendations.map((job) => (
              <JobCard key={job.id} job={job} showMatch />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}