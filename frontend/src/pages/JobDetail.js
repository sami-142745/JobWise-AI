import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import Alert from '../components/Alert';
import Spinner from '../components/Spinner';
import { api } from '../api';

export default function JobDetail() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    api
      .getJob(id)
      .then((data) => {
        if (!cancelled) setJob(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) return <Spinner label="Loading job…" />;
  if (error) {
    return (
      <div className="page">
        <Alert kind="error" title="Could not load job">
          {error}
        </Alert>
      </div>
    );
  }

  return (
    <div className="page">
      <article className="job-detail">
        <p className="muted">{job.company}</p>
        <h1>{job.title}</h1>
        <p className="job-meta">
          <span>{job.location}</span>
          {job.salary && <span>· {job.salary}</span>}
          {job.experience_level && <span>· {job.experience_level}</span>}
        </p>

        <h3>About the role</h3>
        <p className="job-desc-full">{job.description}</p>

        <h3>Required skills</h3>
        <div className="chips">
          {job.skills.map((skill) => (
            <span key={skill} className="chip">
              {skill}
            </span>
          ))}
        </div>

        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary"
          >
            Apply Now
          </a>
        )}
      </article>
    </div>
  );
}