import React, { useState } from 'react';
import { useAuth, PRESET_ACCOUNTS, ROLE_PERMISSIONS } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { 
  Search, Sun, Moon, Database, Shield, ChevronDown, Check, 
  RefreshCw, Radio
} from 'lucide-react';

export default function Header({ currentView, onSearch, theme, onToggleTheme, onNavigate }) {
  const { user, role, switchRole, backendStatus, checkHealth, permissions } = useAuth();
  const { showToast } = useToast();
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);
  const [switching, setSwitching] = useState(false);

  const handleRoleSelect = async (targetRole) => {
    setRoleDropdownOpen(false);
    setSwitching(true);
    try {
      const newUser = await switchRole(targetRole);
      const targetPerms = ROLE_PERMISSIONS[targetRole] || ROLE_PERMISSIONS.ADMIN;
      if (onNavigate) {
        onNavigate(targetPerms.defaultView);
      }
      showToast(`Switched station to ${targetRole}: ${targetPerms.stationName}`, 'success');
    } catch {
      showToast(`Failed to switch to ${targetRole}`, 'error');
    } finally {
      setSwitching(false);
    }
  };

  return (
    <header
      style={{
        height: 'var(--header-height)',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(9, 13, 22, 0.85)',
        backdropFilter: 'blur(16px)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        gap: '20px',
      }}
    >
      {/* Search Bar */}
      <div style={{ position: 'relative', width: '340px' }}>
        <Search
          size={16}
          style={{
            position: 'absolute',
            left: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-muted)',
          }}
        />
        <input
          type="text"
          placeholder="Quick search dishes, orders, tables... ( / )"
          onChange={(e) => onSearch && onSearch(e.target.value)}
          className="input"
          style={{
            paddingLeft: '36px',
            paddingRight: '36px',
            height: '40px',
            fontSize: '0.85rem',
            borderRadius: 'var(--radius-full)',
          }}
        />
        <kbd
          style={{
            position: 'absolute',
            right: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            fontSize: '0.65rem',
            background: 'rgba(255, 255, 255, 0.1)',
            padding: '2px 6px',
            borderRadius: '4px',
            color: 'var(--text-muted)',
          }}
        >
          /
        </kbd>
      </div>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Backend & DB Health Indicator */}
        <div
          onClick={checkHealth}
          title="Click to re-ping MongoDB backend"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.75rem',
            cursor: 'pointer',
            transition: 'border-color 0.2s ease',
          }}
        >
          <span className={`pulse-dot ${backendStatus.online ? 'online' : 'offline'}`} />
          <span style={{ color: backendStatus.online ? 'var(--text-primary)' : 'var(--danger)', fontWeight: 600 }}>
            {backendStatus.online ? `MongoDB Live` : 'DB Offline'}
          </span>
          {backendStatus.latency && (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
              ({backendStatus.latency}ms)
            </span>
          )}
        </div>

        {/* 1-Click Role Switcher */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
            className="btn btn-secondary btn-sm"
            style={{
              padding: '6px 12px',
              borderRadius: 'var(--radius-full)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Shield size={14} style={{ color: 'var(--primary)' }} />
            <span style={{ fontWeight: 600 }}>{role}</span>
            <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
          </button>

          {roleDropdownOpen && (
            <div
              style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                right: 0,
                width: '240px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-lg)',
                padding: '8px',
                zIndex: 200,
                backdropFilter: 'blur(16px)',
              }}
            >
              <div style={{ padding: '6px 10px', fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                1-CLICK STATION SWITCHER
              </div>
              {PRESET_ACCOUNTS.map((acc) => (
                <div
                  key={acc.role}
                  onClick={() => handleRoleSelect(acc.role)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                    background: role === acc.role ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                    color: role === acc.role ? 'var(--primary)' : 'var(--text-primary)',
                    fontSize: '0.825rem',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)')}
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background =
                      role === acc.role ? 'rgba(99, 102, 241, 0.15)' : 'transparent')
                  }
                >
                  <div>
                    <div style={{ fontWeight: 600 }}>{acc.title}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{acc.email}</div>
                  </div>
                  {role === acc.role && <Check size={14} style={{ color: 'var(--primary)' }} />}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          className="btn btn-secondary btn-sm"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          style={{ width: '36px', height: '36px', padding: 0, borderRadius: '50%' }}
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {/* User Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              width: '30px',
              height: '30px',
              borderRadius: '50%',
              background: 'var(--primary-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.8rem',
              color: '#fff',
            }}
          >
            {user?.name ? user.name[0].toUpperCase() : 'A'}
          </div>
          <div style={{ lineHeight: 1.2 }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>{user?.name || 'Administrator'}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{role}</div>
          </div>
        </div>
      </div>
    </header>
  );
}
