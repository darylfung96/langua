import { Link, useLocation, useNavigate } from 'react-router-dom';
// import { BookOpen, Music, Mic2, Image as ImageIcon, PenTool, LayoutDashboard, Volume2 } from 'lucide-react';
import { BookOpen, Music, Mic2, Image as ImageIcon, LayoutDashboard, Volume2, LogOut } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import './Header.css';

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const initial = user?.email ? user.email[0].toUpperCase() : 'U';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { path: '/story-weaver', label: 'Story Weaver', icon: <BookOpen size={20} /> },
    { path: '/melody', label: 'YouTube Learner', icon: <Music size={20} /> },
    { path: '/resource-learner', label: 'Resource Learner', icon: <Volume2 size={20} /> },
    { path: '/podcasts', label: 'Shadowing', icon: <Mic2 size={20} /> },
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
        <button className="profile-btn" title="Logged in">
          <div className="avatar">{initial}</div>
        </button>
        <button className="logout-btn" onClick={handleLogout} title="Sign out">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
};

export default Header;
