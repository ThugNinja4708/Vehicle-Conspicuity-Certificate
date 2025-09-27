import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { useAuth } from '../App';
import { 
  Home, 
  Users, 
  FileText, 
  BarChart3, 
  LogOut, 
  Building2,
  UserCheck,
  PlusCircle,
  Settings
} from 'lucide-react';

const Layout = ({ children, userRole }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getNavigationItems = () => {
    switch (userRole) {
      case 'admin':
        return [
          { path: '/admin', label: 'Dashboard', icon: Home },
          { path: '/admin/users', label: 'Users', icon: Users },
          { path: '/admin/certificates', label: 'Certificates', icon: FileText },
          { path: '/admin/reports', label: 'Reports', icon: BarChart3 },
        ];
      case 'distributor':
        return [
          { path: '/distributor', label: 'Dashboard', icon: Home },
          { path: '/distributor/retailers', label: 'Retailers', icon: UserCheck },
          { path: '/distributor/certificates', label: 'Certificates', icon: FileText },
        ];
      case 'retailer':
        return [
          { path: '/retailer', label: 'Dashboard', icon: Home },
          { path: '/retailer/certificates', label: 'My Certificates', icon: FileText },
          { path: '/certificate/new', label: 'New Certificate', icon: PlusCircle },
        ];
      default:
        return [];
    }
  };

  const navigationItems = getNavigationItems();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl border-r border-gray-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-6 border-b border-gray-200">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">VCS Manager</h1>
              <p className="text-xs text-gray-500 uppercase tracking-wide">{userRole}</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 ${
                    isActive 
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm' 
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                  data-testid={`nav-link-${item.label.toLowerCase().replace(' ', '-')}`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-emerald-600' : 'text-gray-400'}`} />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* User Info & Logout */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full flex items-center justify-center">
                <span className="text-sm font-semibold text-gray-700">
                  {user?.username?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user?.username}</p>
                <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
              </div>
            </div>
            
            <Button
              onClick={handleLogout}
              variant="outline"
              className="w-full justify-start gap-2 text-gray-600 hover:text-red-600 hover:border-red-200 hover:bg-red-50"
              data-testid="logout-button"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;