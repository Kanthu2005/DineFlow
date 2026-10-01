import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, getCurrentUser, setCurrentUser, getToken, setToken } from '../services/api';

const AuthContext = createContext();

export const ROLE_PERMISSIONS = {
  ADMIN: {
    title: 'System Administrator',
    stationName: 'Executive Admin Terminal',
    badgeColor: '#818cf8',
    defaultView: 'dashboard',
    allowedViews: ['dashboard', 'menu', 'add-menu', 'orders', 'kitchen', 'tables', 'billing', 'inventory', 'feedback', 'reports', 'users'],
    canEditMenu: true,
    canSettleBills: true,
    canManageTables: true,
    canManageUsers: true,
  },
  MANAGER: {
    title: 'General Manager',
    stationName: 'Operations Manager Desk',
    badgeColor: '#38bdf8',
    defaultView: 'dashboard',
    allowedViews: ['dashboard', 'menu', 'add-menu', 'orders', 'kitchen', 'tables', 'billing', 'inventory', 'feedback', 'reports'],
    canEditMenu: true,
    canSettleBills: true,
    canManageTables: true,
    canManageUsers: false,
  },
  CHEF: {
    title: 'Head Chef',
    stationName: 'Kitchen Display Line (KDS)',
    badgeColor: '#f97316',
    defaultView: 'kitchen',
    allowedViews: ['kitchen', 'menu', 'add-menu', 'orders', 'inventory'],
    canEditMenu: true,
    canSettleBills: false,
    canManageTables: false,
    canManageUsers: false,
  },
  WAITER: {
    title: 'Floor Waiter',
    stationName: 'Server & Dining Floor Station',
    badgeColor: '#10b981',
    defaultView: 'tables',
    allowedViews: ['tables', 'menu', 'add-menu', 'orders', 'feedback'],
    canEditMenu: true,
    canSettleBills: false,
    canManageTables: true,
    canManageUsers: false,
  },
  CASHIER: {
    title: 'Billing Cashier',
    stationName: 'Cashier & Settlement Counter',
    badgeColor: '#eab308',
    defaultView: 'billing',
    allowedViews: ['billing', 'orders', 'reports'],
    canEditMenu: false,
    canSettleBills: true,
    canManageTables: false,
    canManageUsers: false,
  },
};

export const PRESET_ACCOUNTS = [
  { role: 'ADMIN', email: 'admin@dineflow.com', name: 'System Administrator', title: 'System Admin' },
  { role: 'MANAGER', email: 'manager@dineflow.com', name: 'General Manager', title: 'General Manager' },
  { role: 'CHEF', email: 'chef@dineflow.com', name: 'Head Chef', title: 'Head Chef' },
  { role: 'WAITER', email: 'waiter@dineflow.com', name: 'Floor Waiter', title: 'Floor Waiter' },
  { role: 'CASHIER', email: 'cashier@dineflow.com', name: 'Billing Cashier', title: 'Billing Cashier' },
];

export function isViewAllowedForRole(role, viewId) {
  const normalizedRole = (role || 'ADMIN').toUpperCase();
  const perms = ROLE_PERMISSIONS[normalizedRole] || ROLE_PERMISSIONS.ADMIN;
  return perms.allowedViews.includes(viewId);
}

export function getDefaultViewForRole(role) {
  const normalizedRole = (role || 'ADMIN').toUpperCase();
  const perms = ROLE_PERMISSIONS[normalizedRole] || ROLE_PERMISSIONS.ADMIN;
  return perms.defaultView || 'dashboard';
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getCurrentUser());
  const [tokenState, setTokenState] = useState(getToken());
  const [backendStatus, setBackendStatus] = useState({ online: false, latency: null, dbName: '' });

  const checkHealth = async () => {
    try {
      const start = performance.now();
      const res = await api.health();
      const latency = Math.round(performance.now() - start);
      if (res && (res.status === 'healthy' || res.database)) {
        setBackendStatus({ online: true, latency, dbName: res.database_name || 'restaurant_management' });
      } else {
        setBackendStatus({ online: true, latency, dbName: '' });
      }
    } catch {
      setBackendStatus({ online: false, latency: null, dbName: '' });
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 25000);
    return () => clearInterval(interval);
  }, []);

  // Ensure initial admin session so the dashboard is immediately accessible
  useEffect(() => {
    const initSession = async () => {
      if (!user || !tokenState) {
        const defaultAcc = PRESET_ACCOUNTS[0]; // Admin
        try {
          const res = await api.auth.login(defaultAcc.email, 'Password123!');
          if (res?.access_token) {
            setToken(res.access_token);
            setTokenState(res.access_token);
            const usr = res.user || { name: defaultAcc.name, email: defaultAcc.email, role: defaultAcc.role };
            setCurrentUser(usr);
            setUser(usr);
            return;
          }
        } catch {
          // Fallback local session
          const fallbackUser = { name: defaultAcc.name, email: defaultAcc.email, role: defaultAcc.role };
          setCurrentUser(fallbackUser);
          setUser(fallbackUser);
          setToken('demo-session-token');
          setTokenState('demo-session-token');
        }
      }
    };
    initSession();
  }, []);

  const switchRole = async (targetRole) => {
    const acc = PRESET_ACCOUNTS.find(a => a.role === targetRole);
    if (!acc) return;

    try {
      const res = await api.auth.login(acc.email, 'Password123!');
      if (res?.access_token) {
        setToken(res.access_token);
        setTokenState(res.access_token);
        const usr = res.user || { name: acc.name, email: acc.email, role: acc.role };
        setCurrentUser(usr);
        setUser(usr);
        return usr;
      }
    } catch (err) {
      console.warn('Switch role login error, using local switch:', err);
      const fallbackUser = { name: acc.name, email: acc.email, role: acc.role };
      setCurrentUser(fallbackUser);
      setUser(fallbackUser);
      return fallbackUser;
    }
  };

  const [staffList, setStaffList] = useState([]);

  const refreshStaff = async () => {
    try {
      const res = await api.users.getAll();
      if (Array.isArray(res)) {
        setStaffList(res);
      }
    } catch (e) {
      console.warn('Could not load staff list:', e);
    }
  };

  useEffect(() => {
    refreshStaff();
  }, [user]);

  const switchPerson = async (person) => {
    if (!person) return;
    if (typeof person === 'string') {
      return await switchRole(person);
    }
    const preset = PRESET_ACCOUNTS.find(
      a => a.email.toLowerCase() === (person.email || '').toLowerCase() || a.role === person.role
    );
    if (preset) {
      try {
        const res = await api.auth.login(preset.email, 'Password123!');
        if (res?.access_token) {
          setToken(res.access_token);
          setTokenState(res.access_token);
          const usr = { ...res.user, name: person.name || res.user?.name, role: (person.role || res.user?.role || preset.role).toUpperCase() };
          setCurrentUser(usr);
          setUser(usr);
          return usr;
        }
      } catch (err) {
        console.warn('Preset login failed, using local session:', err);
      }
    }
    const usr = {
      id: person.id || person._id,
      name: person.name,
      email: person.email,
      role: (person.role || 'STAFF').toUpperCase(),
    };
    setCurrentUser(usr);
    setUser(usr);
    return usr;
  };

  const login = async (email, password) => {
    const res = await api.auth.login(email, password);
    if (res?.access_token) {
      setToken(res.access_token);
      setTokenState(res.access_token);
      const usr = res.user || { email, role: 'STAFF' };
      setCurrentUser(usr);
      setUser(usr);
      return usr;
    }
    throw new Error('No token returned');
  };

  const logout = () => {
    setToken(null);
    setTokenState(null);
    setCurrentUser(null);
    setUser(null);
  };

  const normalizedRole = (user?.role || 'ADMIN').toUpperCase();
  const permissions = ROLE_PERMISSIONS[normalizedRole] || ROLE_PERMISSIONS.ADMIN;

  return (
    <AuthContext.Provider
      value={{
        user,
        role: normalizedRole,
        permissions,
        token: tokenState,
        backendStatus,
        staffList,
        refreshStaff,
        checkHealth,
        switchRole,
        switchPerson,
        isAllowed: (viewId) => isViewAllowedForRole(normalizedRole, viewId),
        defaultView: permissions.defaultView || 'dashboard',
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
