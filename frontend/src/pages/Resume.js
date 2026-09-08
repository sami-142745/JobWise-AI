import React, { useCallback, useEffect, useRef, useState } from 'react';

import Alert from '../components/Alert';
import Spinner from '../components/Spinner';
import { api } from '../api';

export default function Resume() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [textMode, setTextMode] = useState(false);
  const [resumeText, setResumeText] = useState('');
  const [dragging, setDragging] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const fileInputRef = useRef(null);

  const loadProfile = useCallback(() => {
    api
      .getResumeProfile()
      .then(setProfile)
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const handleFile = async (file) => {
    setError('');
    setSuccess('');
    setAnalyzing(true);
    try {
      const result = await api.uploadResume(file);
      setSuccess('Resume uploaded and analyzed successfully!');
      setProfile(result);
      loadProfile();
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const onFileChange = (e) => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const analyzeText = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setAnalyzing(true);
    try {
      const result = await api.analyzeResumeText(resumeText);
      setSuccess('Resume text analyzed successfully!');
      setProfile(result);
      loadProfile();
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <Spinner label="Loading your resume profile…" />;

  return (
    <div className="page">
      <header className="page-header">
        <h1>My Resume</h1>
        <p className="muted">
          Upload your resume (PDF, DOCX, TXT) or paste it as text. The AI agent
          extracts your skills and experience for matching.
        </p>
      </header>

      {error && <Alert kind="error">{error}</Alert>}
      {success && <Alert kind="success">{success}</Alert>}

      <div className="resume-layout">
        <div className="resume-upload">
          {!textMode ? (
            <div
              className={`dropzone${dragging ? ' dropzone--active' : ''}`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md,.csv"
                onChange={onFileChange}
                hidden
              />
              <div className="dropzone-icon">⬆️</div>
              <p>
                <strong>Drop your resume here</strong> or click to browse
              </p>
              <p className="muted">PDF, DOCX or TXT · up to 10 MB</p>
              {analyzing && <Spinner label="Analyzing resume…" />}
            </div>
          ) : (
            <form onSubmit={analyzeText} className="text-form">
              <label htmlFor="resumeText">Paste your resume text</label>
              <textarea
                id="resumeText"
                rows={12}
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste the plain text of your resume here…"
                required
              />
              <div className="btn-row">
                <button type="submit" className="btn btn-primary" disabled={analyzing}>
                  {analyzing ? 'Analyzing…' : 'Analyze Text'}
                </button>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setTextMode(false)}
                >
                  Back to file upload
                </button>
              </div>
            </form>
          )}

          <p className="muted">
            Prefer to paste it?{' '}
            <button
              type="button"
              className="link-button"
              onClick={() => setTextMode((v) => !v)}
            >
              {textMode ? 'Upload a file instead' : 'Paste resume text instead'}
            </button>
          </p>
        </div>

        <div className="resume-profile">
          {profile ? (
            <>
              <h2>Your analyzed profile</h2>
              <p className="muted">
                {profile.filename} · analyzed just now
              </p>
              <div className="profile-stats">
                <div>
                  <span className="stat-value">{profile.skills.length}</span>
                  <span className="stat-label">skills found</span>
                </div>
                <div>
                  <span className="stat-value">{profile.years_experience}y</span>
                  <span className="stat-label">experience</span>
                </div>
              </div>
              <h3>Detected skills</h3>
              <div className="chips">
                {profile.skills.map((skill) => (
                  <span key={skill} className="chip chip--match">
                    {skill}
                  </span>
                ))}
              </div>
              {profile.summary && (
                <>
                  <h3>Extracted summary</h3>
                  <p className="muted">{profile.summary}</p>
                </>
              )}
              <p>
                <a href="/dashboard" className="btn btn-primary btn-sm">
                  View my recommendations
                </a>
              </p>
            </>
          ) : (
            <Alert kind="info" title="No resume on file">
              Once you upload a resume, your extracted profile will appear here
              and your dashboard will show personalized matches.
            </Alert>
          )}
        </div>
      </div>
    </div>
  );
}