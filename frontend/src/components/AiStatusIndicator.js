import { useEffect, useState } from 'react';

import { api } from '../api';

const DEFAULT = { status: 'unknown', engine: 'offline-rules', model: null };

export default function AiStatusIndicator() {
  const [ai, setAi] = useState(DEFAULT);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api
        .aiStatus()
        .then((data) => {
          if (!cancelled) {
            setAi(data);
            setError(false);
          }
        })
        .catch(() => {
          if (!cancelled) setError(true);
        });
    };
    load();
    const timer = setInterval(load, 30000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const ready = ai.status === 'available' && !error;
  const state = error ? 'offline' : ai.status;
  const label = ready
    ? ai.model || 'Ollama'
    : state === 'checking' ? 'Checking AI...' : 'Offline engine';

  return (
    <span className={`ai-pill ai-pill--${state}`} title={ai.message || ''}>
      <span className="ai-pill-dot" aria-hidden="true" />
      {label}
    </span>
  );
}