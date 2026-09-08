import React, { useCallback, useEffect, useState } from 'react';

import Alert from '../components/Alert';
import JobCard from '../components/JobCard';
import Spinner from '../components/Spinner';
import { api } from '../api';

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [searching, setSearching] = useState(false);

  const load = useCallback(async (params) => {
    setLoading(true);
    setError('');
    try {
      const results = await api.listJobs(params);
      setJobs(results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load({ limit: 50 });
  }, [load]);

  const onSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      load({ limit: 50 });
      return;
    }
    setSearching(true);
    setError('');
    try {
      const results = await api.searchJobs(query.trim(), location.trim());
      setJobs(results);
    } catch (err) {
      setError(err.message);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <h1>Browse Jobs</h1>
        <p className="muted">Search the roles available and find your next move.</p>
      </header>

      <form className="search-bar" onSubmit={onSearch}>
        <input
          type="text"
          placeholder="Search by title, skill, or company…  e.g. python"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <input
          type="text"
          placeholder="Location (optional)"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <button type="submit" className="btn btn-primary" disabled={searching}>
          {searching ? 'Searching…' : 'Search'}
        </button>
      </form>

      {error && <Alert kind="error">{error}</Alert>}

      {loading ? (
        <Spinner label="Loading jobs…" />
      ) : jobs.length === 0 ? (
        <Alert kind="info" title="No jobs found">
          Try a different keyword or clear your search.
        </Alert>
      ) : (
        <div className="job-list">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} showApply />
          ))}
        </div>
      )}
    </div>
  );
}