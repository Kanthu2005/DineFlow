import React from 'react';
import { 
  LayoutDashboard, ShoppingBag, Clock, ChefHat, Grid, 
  Receipt, UtensilsCrossed, Boxes, Users, BarChart3, UserCog,
  Sparkles, LogOut, ShieldCheck, Lock, PlusCircle
} from 'lucide-react';
import { useAuth, ROLE_PERMISSIONS } from '../context/AuthContext';

export const ALL_NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'menu', label: 'Menu', icon: UtensilsCrossed },
  { id: 'add-menu', label: 'Add Menu', icon: PlusCircle },
  { id: 'orders', label: 'Live Orders', icon: Clock },
  { id: 'kitchen', label: 'Kitchen (KDS)', icon: ChefHat },
  { id: 'tables', label: 'Tables & Floor', icon: Grid },
  { id: 'billing', label: 'Billing', icon: Receipt },
  { id: 'inventory', label: 'Inventory', icon: Boxes },
  { id: 'feedback', label: 'Feedback', icon: Users },
  { id: 'reports', label: 'Analytics', icon: BarChart3 },
  { id: 'users', label: 'Staff Directory', icon: UserCog },
];

export default function Sidebar({ currentView, onViewChange }) {
  const { role, permissions, logout } = useAuth();

  // Strict RBAC: only show navigation items permitted for the active role
  const allowedViews = permissions?.allowedViews || [];
  const visibleNavItems = ALL_NAV_ITEMS.filter(item => allowedViews.includes(item.id));

  return (
    <aside
      style={{
        width: 'var(--sidebar-width)',
        height: '100vh',
        position: 'sticky',
        top: 0,
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 110,
        userSelect: 'none',
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          height: 'var(--header-height)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '0 20px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--primary-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: 'var(--shadow-glow)',
            flexShrink: 0,
          }}
        >
          <Sparkles size={20} />
        </div>
        <div style={{ overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '1.2rem', fontWeight: 800, fontFamily: 'Outfit', letterSpacing: '-0.02em' }}>DineFlow</span>
            <span
              style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                background: 'rgba(99, 102, 241, 0.2)',
                color: '#818cf8',
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid rgba(99, 102, 241, 0.4)',
              }}
            >
              OS
            </span>
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
            Restaurant Management
          </div>
        </div>
      </div>

      {/* Role Station Badge Banner */}
      <div
        style={{
          padding: '12px 16px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <div
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: permissions?.badgeColor || 'var(--primary)',
            boxShadow: `0 0 10px ${permissions?.badgeColor || 'var(--primary)'}`,
          }}
        />
        <div style={{ overflow: 'hidden' }}>
          <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 700 }}>
            Active Station
          </div>
          <div
            style={{
              fontSize: '0.8rem',
              fontWeight: 700,
              color: permissions?.badgeColor || 'var(--text-primary)',
              whiteSpace: 'nowrap',
              textOverflow: 'ellipsis',
              overflow: 'hidden',
            }}
          >
            {permissions?.stationName || `${role} Station`}
          </div>
        </div>
      </div>

      {/* Nav List */}
      <nav
        style={{
          flex: 1,
          padding: '16px 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          overflowY: 'auto',
        }}
      >
        <div style={{ padding: '4px 10px', fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Authorized Sections ({visibleNavItems.length})
        </div>

        {visibleNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                background: isActive ? 'var(--primary-gradient)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                border: '1px solid',
                borderColor: isActive ? 'transparent' : 'transparent',
                cursor: 'pointer',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.875rem',
                transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: isActive ? 'var(--shadow-glow)' : 'none',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                  e.currentTarget.style.color = 'var(--text-primary)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Icon size={18} style={{ opacity: isActive ? 1 : 0.8 }} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  style={{
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: 'var(--radius-full)',
                    background: isActive ? 'rgba(255, 255, 255, 0.25)' : 'var(--accent)',
                    color: '#fff',
                  }}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        {/* Informational Role Restrictions note */}
        {role !== 'ADMIN' && (
          <div
            style={{
              marginTop: 'auto',
              padding: '12px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px dashed var(--border-subtle)',
              fontSize: '0.72rem',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '8px',
            }}
          >
            <Lock size={14} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--text-muted)' }} />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Role Enforced</div>
              Other sections are hidden based on your station credentials.
            </div>
          </div>
        )}
      </nav>

      {/* Footer System Info */}
      <div
        style={{
          padding: '14px 16px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
        }}
      >
        <div>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>DineFlow</span> v2.0.0
        </div>
        <button
          onClick={logout}
          title="Sign Out / Reset Session"
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 6px',
            borderRadius: 'var(--radius-sm)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--danger)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
        >
          <LogOut size={14} />
        </button>
      </div>
    </aside>
  );
}
