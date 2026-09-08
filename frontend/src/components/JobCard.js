import React from 'react';
import { Link } from 'react-router-dom';

function scoreColor(score) {
  if (score >= 70) return 'high';
  if (score >= 45) return 'mid';
  return 'low';
}

function MatchScore({ score }) {
  const level = scoreColor(score);
  return (
    <div className={`match-score match-score--${level}`}>
      <span className="match-score-value">{score}%</span>
      <span className="match-score-label">match</span>
    </div>
  );
}

function SkillChips({ skills, extra = [] }) {
  return (
    <div className="chips">
      {skills.slice(0, 6).map((skill) => (
        <span key={skill} className="chip">
          {skill}
        </span>
      ))}
      {extra.length > 0 && <span className="chip chip--extra">+{extra.length} more</span>}
    </div>
  );
}

function EngineBadge({ mode }) {
  if (mode === 'ollama') {
    return (
      <span className="engine-badge engine-badge--ollama">Ollama AI</span>
    );
  }
  if (mode === 'offline-rules' || mode === 'offline') {
    return <span className="engine-badge">Offline engine</span>;
  }
  return null;
}

export default function JobCard({ job, showMatch = false, showApply = false }) {
  const matched = job.matched_skills || [];
  const missing = job.missing_skills || [];
  const suggested = job.suggested_skills || [];
  const reasoning = job.ai_reasoning || job.rationale;

  return (
    <article className="job-card">
      <div className="job-card-top">
        <div>
          <h3 className="job-title">
            <Link to={`/jobs/${job.id}`}>{job.title}</Link>
          </h3>
          <p className="job-company">
            {job.company} <EngineBadge mode={job.ai_mode} />
          </p>
        </div>
        {showMatch && <MatchScore score={job.match_score} />}
      </div>

      <p className="job-meta">
        <span>{job.location}</span>
        {job.salary && <span>· {job.salary}</span>}
        {job.experience_level && <span>· {job.experience_level}</span>}
      </p>

      <p className="job-desc">
        {job.description && job.description.length > 180
          ? `${job.description.slice(0, 180)}…`
          : job.description}
      </p>

      <SkillChips skills={job.skills} />

      {showMatch && (matched.length > 0 || missing.length > 0 || suggested.length > 0) && (
        <div className="match-details">
          {matched.length > 0 && (
            <p className="match-good">
              <strong>You match:</strong> {matched.join(', ')}
            </p>
          )}
          {(missing.length > 0 || suggested.length > 0) && (
            <p className="match-gap">
              <strong>Consider learning:</strong>{' '}
              {(suggested.length > 0 ? suggested : missing).join(', ')}
            </p>
          )}
        </div>
      )}

      {reasoning && <p className="job-rationale muted">💡 {reasoning}</p>}

      <div className="job-card-actions">
        <Link to={`/jobs/${job.id}`} className="btn btn-primary btn-sm">
          View Details
        </Link>
        {showApply && job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-outline btn-sm"
          >
            Apply
          </a>
        )}
      </div>
    </article>
  );
}