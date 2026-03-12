import { Link, useLocation } from 'react-router-dom';
// import { BookOpen, Music, Mic2, Image as ImageIcon, PenTool, LayoutDashboard, Volume2 } from 'lucide-react';
import { BookOpen, Music, Image as ImageIcon, LayoutDashboard, Volume2 } from 'lucide-react';
import './Header.css';

const Header = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { path: '/story-weaver', label: 'Story Weaver', icon: <BookOpen size={20} /> },
    { path: '/melody', label: 'Lyric Learner', icon: <Music size={20} /> },
    { path: '/resource-learner', label: 'Resource Learner', icon: <Volume2 size={20} /> },
    // { path: '/podcasts', label: 'Podcast Pro', icon: <Mic2 size={20} /> },
    { path: '/visual-memory', label: 'Visuals', icon: <ImageIcon size={20} /> },
    // { path: '/writing', label: 'Journal', icon: <PenTool size={20} /> },
  ];

  return (
    <header className="header glass-panel">
      <div className="header-brand">
        <div className="logo-glow"></div>
        <h1>Lingua<span>Nova</span></h1>
      </div>

      <nav className="header-nav">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
          >
            {item.icon}
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="header-actions">
        <button className="profile-btn">
          <div className="avatar">U</div>
        </button>
      </div>
    </header>
  );
};

export default Header;
