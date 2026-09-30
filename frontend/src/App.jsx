import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth, ROLE_PERMISSIONS } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import { ShieldAlert, ArrowRight, Lock, CheckCircle2 } from 'lucide-react';

import DashboardView from './views/DashboardView';
import PosView from './views/PosView';
import OrdersView from './views/OrdersView';
import KitchenView from './views/KitchenView';
import TablesView from './views/TablesView';
import BillingView from './views/BillingView';
import MenuView from './views/MenuView';
import InventoryView from './views/InventoryView';
import FeedbackView from './views/FeedbackView';
import ReportsView from './views/ReportsView';
import UsersView from './views/UsersView';

function AccessRestrictedScreen({ currentView, onGoDefault }) {
  const { role, user, permissions, switchRole } = useAuth();
  const stationName = permissions?.stationName || `${role} Station`;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        padding: '32px',
        textAlign: 'center',
      }}
    >
      <div
        className="glass-panel"
        style={{
          maxWidth: '540px',
          width: '100%',
          padding: '36px 32px',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          background: 'linear-gradient(180deg, rgba(239, 68, 68, 0.08) 0%, rgba(15, 23, 42, 0.95) 100%)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px',
        }}
      >
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '2px solid rgba(239, 68, 68, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--danger)',
          }}
        >
          <Lock size={32} />
        </div>

        <div>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--danger)',
              background: 'rgba(239, 68, 68, 0.1)',
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
            }}
          >
            Access Clearance Restricted
          </span>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginTop: '10px' }}>
            Section Not Available For Your Role
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '6px', lineHeight: 1.5 }}>
            You are logged in as <strong>{user?.name || role}</strong> with the <strong style={{ color: permissions?.badgeColor || 'var(--primary)' }}>{role}</strong> profile ({stationName}).
            This section is locked to prevent unauthorized operational actions.
          </p>
        </div>

        {/* Permitted Views Pills */}
        <div style={{ width: '100%', background: 'rgba(255, 255, 255, 0.03)', padding: '14px', borderRadius: 'var(--radius-md)', textAlign: 'left' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Your Authorized Workstations:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {permissions?.allowedViews?.map((v) => (
              <span
                key={v}
                onClick={() => onGoDefault(v)}
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  background: 'rgba(99, 102, 241, 0.15)',
                  color: '#818cf8',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  cursor: 'pointer',
                }}
              >
                &rarr; {v.toUpperCase()}
              </span>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', width: '100%', marginTop: '8px' }}>
          <button
            onClick={() => onGoDefault(permissions?.defaultView || 'dashboard')}
            className="btn btn-primary"
            style={{ flex: 1, padding: '10px 16px' }}
          >
            <span>Go to My Station ({permissions?.defaultView?.toUpperCase()})</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

function AppContent() {
  const { role, isAllowed, defaultView } = useAuth();

  const [currentView, setCurrentView] = useState(() => {
    const hash = window.location.hash.replace('#', '');
    return hash || 'dashboard';
  });

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('dineflow_theme') || 'dark';
  });
  const [targetInvoiceForBilling, setTargetInvoiceForBilling] = useState(null);

  // Sync role changes: if active view is not permitted for the new role, automatically navigate to defaultView
  useEffect(() => {
    if (!isAllowed(currentView)) {
      handleNavigate(defaultView);
    }
  }, [role, defaultView]);

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light-theme');
    } else {
      document.documentElement.classList.remove('light-theme');
    }
    localStorage.setItem('dineflow_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const handleNavigate = (viewId) => {
    setCurrentView(viewId);
    window.location.hash = viewId;
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (
        (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) ||
        ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k')
      ) {
        e.preventDefault();
        if (isAllowed('pos')) {
          handleNavigate('pos');
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [role]);

  const handleNavigateToBilling = (inv) => {
    if (isAllowed('billing')) {
      setTargetInvoiceForBilling(inv);
      handleNavigate('billing');
    }
  };

  const isCurrentViewAllowed = isAllowed(currentView);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Sidebar Navigation */}
      <Sidebar currentView={currentView} onViewChange={handleNavigate} />

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Sticky Header */}
        <Header
          currentView={currentView}
          theme={theme}
          onToggleTheme={toggleTheme}
          onNavigate={handleNavigate}
        />

        {/* Dynamic View Body */}
        <main style={{ flex: 1, padding: '24px 28px', overflowY: 'auto' }}>
          {!isCurrentViewAllowed ? (
            <AccessRestrictedScreen
              currentView={currentView}
              onGoDefault={handleNavigate}
            />
          ) : (
            <>
              {currentView === 'dashboard' && <DashboardView onNavigate={handleNavigate} />}
              {currentView === 'pos' && <PosView onOrderPlaced={() => handleNavigate('orders')} />}
              {currentView === 'orders' && <OrdersView onNavigateToBilling={handleNavigateToBilling} />}
              {currentView === 'kitchen' && <KitchenView />}
              {currentView === 'tables' && <TablesView onNavigateToPOS={(tblId) => handleNavigate('pos')} onNavigateToBilling={() => handleNavigate('billing')} />}
              {currentView === 'billing' && <BillingView targetInvoice={targetInvoiceForBilling} />}
              {currentView === 'menu' && <MenuView />}
              {currentView === 'inventory' && <InventoryView />}
              {currentView === 'feedback' && <FeedbackView />}
              {currentView === 'reports' && <ReportsView />}
              {currentView === 'users' && <UsersView />}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </AuthProvider>
  );
}
