import { Link } from 'react-router-dom';

const NotFound = () => (
  <div
    className="page-container animate-fade-in"
    style={{ textAlign: 'center', paddingTop: '4rem' }}
  >
    <h2 style={{ fontSize: '4rem', margin: 0 }}>404</h2>
    <p style={{ fontSize: '1.25rem', margin: '1rem 0 2rem' }}>
      Page not found
    </p>
    <Link to="/" style={{ textDecoration: 'none', color: 'var(--accent-primary)' }}>
      ← Back to Dashboard
    </Link>
  </div>
);

export default NotFound;
