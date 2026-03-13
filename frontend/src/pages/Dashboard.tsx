import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Music, Mic2, Image as ImageIcon, PenTool } from 'lucide-react';
import './Dashboard.css';

const modules = [
  {
    title: 'Story Weaver',
    description: 'Contextual memory building. Input words and get an engaging story.',
    icon: <BookOpen size={32} />,
    path: '/story-weaver',
    color: 'var(--accent-primary)'
  },
  {
    title: 'Youtube Learner',
    description: 'Rhythmic memory. Learn vocabulary and pacing through audios/videos.',
    icon: <Music size={32} />,
    path: '/melody',
    color: 'var(--accent-secondary)'
  },
  {
    title: 'Podcast Pro',
    description: 'Acoustic practice. Perfect your pronunciation by shadowing natives.',
    icon: <Mic2 size={32} />,
    path: '/podcasts',
    color: 'var(--accent-warning)',
    comingSoon: true,
  },
  {
    title: 'Visual Memory',
    description: 'Spatial and image memory. Connect words to vibrant imagery.',
    icon: <ImageIcon size={32} />,
    path: '/visual-memory',
    color: 'var(--accent-secondary)'
  },
  {
    title: 'Journaling',
    description: 'Expressive writing. Translate constructs and improve syntax.',
    icon: <PenTool size={32} />,
    path: '/writing',
    color: 'var(--accent-tertiary)',
    comingSoon: true,
  },
  {
    title: 'Resource Learner',
    description: 'Local transcription. Upload audio/video and get a timestamped interactive transcript.',
    icon: <Mic2 size={32} />,
    path: '/resource-learner',
    color: 'var(--accent-primary)'
  }
];

const Dashboard = () => {
  return (
    <div className="page-container animate-fade-in dashboard-page">
      <header className="page-header">
        <h2 className="title-gradient">Welcome back, Learner!</h2>
        <p className="subtitle">Choose a cognitive approach to continue your language journey today.</p>
      </header>

      <div className="dashboard-grid">
        {modules.map((mod, idx) => (
          <Link to={mod.path} key={idx} className={`module-card glass-panel${mod.comingSoon ? ' module-card--coming-soon' : ''}`} style={{ '--card-accent': mod.color } as React.CSSProperties}>
            <div className="card-icon-wrapper" style={{ color: mod.color }}>
              {mod.icon}
            </div>
            <div className="card-content">
              <h3>{mod.title}</h3>
              <p>{mod.description}</p>
            </div>
            <div className="card-action">
              <span>{mod.comingSoon ? 'Coming Soon' : 'Start'}</span>
              <span className="arrow">→</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
