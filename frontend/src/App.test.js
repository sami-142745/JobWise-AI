import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import App from './App';

test('renders the welcome page on the home route', () => {
  render(
    <MemoryRouter initialEntries={['/']}>
      <App />
    </MemoryRouter>
  );
  expect(
    screen.getByRole('heading', { name: /find the job your skills were made for/i })
  ).toBeInTheDocument();
  expect(screen.getByText('JobWise AI')).toBeInTheDocument(); // navbar brand
});

test('renders a login route', () => {
  render(
    <MemoryRouter initialEntries={['/login']}>
      <App />
    </MemoryRouter>
  );
  expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
});