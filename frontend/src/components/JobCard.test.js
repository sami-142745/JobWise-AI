import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import JobCard from './JobCard';

const baseJob = {
  id: 'j1',
  title: 'Backend Engineer',
  company: 'ACME Corp',
  location: 'Remote',
  skills: ['python', 'fastapi'],
};

test('renders Ollama badge, reasoning and suggested skills when enriched', () => {
  const job = {
    ...baseJob,
    match_score: 93,
    matched_skills: ['python', 'fastapi'],
    suggested_skills: ['kafka', 'terraform'],
    ai_reasoning: 'Strong overlap with backend stacks.',
    ai_mode: 'ollama',
  };
  render(
    <MemoryRouter>
      <JobCard job={job} showMatch />
    </MemoryRouter>
  );

  expect(screen.getByText('Ollama AI')).toBeInTheDocument();
  expect(screen.getByText(/Strong overlap with backend stacks/)).toBeInTheDocument();
  expect(screen.getByText('kafka, terraform')).toBeInTheDocument();
  expect(screen.getByText('93%')).toBeInTheDocument();
});

test('falls back to offline engine label and rationale', () => {
  const job = {
    ...baseJob,
    match_score: 55,
    matched_skills: ['python'],
    missing_skills: ['fastapi'],
    rationale: 'Recommended: decent skills overlap.',
    ai_mode: 'offline-rules',
  };
  render(
    <MemoryRouter>
      <JobCard job={job} showMatch />
    </MemoryRouter>
  );

  expect(screen.getByText('Offline engine')).toBeInTheDocument();
  expect(screen.getByText(/Recommended: decent skills overlap/)).toBeInTheDocument();
  const gap = screen.getByText((content, element) =>
    element?.classList.contains('match-gap') && content.includes('fastapi')
  );
  expect(gap).toHaveTextContent('Consider learning:');
  expect(gap).toHaveTextContent('fastapi');
});