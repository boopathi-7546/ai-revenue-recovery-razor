import { Link, useNavigate } from 'react-router-dom';
import { LogOut, Zap, BarChart2, Settings } from 'lucide-react';
import { supabase } from '../supabase';
import toast from 'react-hot-toast';

interface NavbarProps {
  businessName?: string;
}

export function Navbar({ businessName }: NavbarProps) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/dashboard" className="navbar-logo">
          <Zap size={20} style={{ color: 'var(--accent)' }} />
          Revenue<span>Recovery</span>
        </Link>

        <div className="navbar-actions">
          {businessName && (
            <span className="navbar-business-name" title={businessName}>
              {businessName}
            </span>
          )}
          <button
            id="navbar-logout-btn"
            className="btn btn-ghost btn-sm"
            onClick={handleLogout}
            title="Logout"
          >
            <LogOut size={15} />
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
