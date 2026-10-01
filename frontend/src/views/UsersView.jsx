import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { 
  UserCog, Plus, Shield, Mail, Check, X, Trash2, Edit3, 
  UserCheck, RefreshCw, KeyRound, ShieldAlert, Sparkles, CheckCircle2
} from 'lucide-react';

const ROLE_DEFINITIONS = {
  ADMIN: {
    label: 'System Administrator',
    badgeClass: 'badge-danger',
    color: '#ef4444',
    bg: 'rgba(239, 68, 68, 0.12)',
    access: 'Full System Access: Menu, Tables, Billing, KDS, Inventory, Staff & Reports',
  },
  MANAGER: {
    label: 'Operations Manager',
    badgeClass: 'badge-primary',
    color: '#8b5cf6',
    bg: 'rgba(139, 92, 246, 0.12)',
    access: 'Management: Menu, Tables, Billing, Inventory, Staff, and Reports',
  },
  CHEF: {
    label: 'Head Chef',
    badgeClass: 'badge-warning',
    color: '#f59e0b',
    bg: 'rgba(245, 158, 11, 0.12)',
    access: 'Kitchen KDS, Live Prep Station, Recipe Stock, and Menu Item Creation',
  },
  WAITER: {
    label: 'Dining Floor Waiter',
    badgeClass: 'badge-info',
    color: '#06b6d4',
    bg: 'rgba(6, 182, 212, 0.12)',
    access: 'Floor Operations: Table seating, floor dining & live order status',
  },
  CASHIER: {
    label: 'Billing Cashier',
    badgeClass: 'badge-success',
    color: '#10b981',
    bg: 'rgba(16, 185, 129, 0.12)',
    access: 'Checkout Terminal: Payment collections (UPI/Cash/Card), GST Invoices & Thermal Printing',
  },
};

export default function UsersView() {
  const { user: currentAuthUser, switchPerson, refreshStaff } = useAuth();
  const { showToast } = useToast();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // Role edit modal
  const [editingUser, setEditingUser] = useState(null);
  const [selectedRole, setSelectedRole] = useState('WAITER');
  const [savingRole, setSavingRole] = useState(false);

  // Form for adding new staff
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('Password123!');
  const [role, setRole] = useState('WAITER');
  const [submitting, setSubmitting] = useState(false);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await api.users.getAll();
      setUsers(Array.isArray(res) ? res : []);
      if (refreshStaff) refreshStaff();
    } catch (err) {
      console.error('Users load error:', err);
      showToast('Could not load staff directory', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (!name || !email || !password) return;
    setSubmitting(true);
    try {
      const res = await api.users.create({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
        role,
        is_active: true,
      });
      showToast(`Staff member "${name}" registered with role ${role}!`, 'success');
      setUsers(prev => [res, ...prev]);
      setShowAddModal(false);
      setName('');
      setEmail('');
      if (refreshStaff) refreshStaff();
    } catch (err) {
      showToast(err.message || 'Failed to register user', 'danger');
    } finally {
      setSubmitting(false);
    }
  };

  const openRoleEditModal = (u) => {
    setEditingUser(u);
    setSelectedRole(u.role || 'WAITER');
  };

  const handleUpdateRole = async (e) => {
    e.preventDefault();
    if (!editingUser) return;
    setSavingRole(true);
    try {
      const updated = await api.users.update(editingUser.id, { role: selectedRole });
      setUsers(prev => prev.map(u => (u.id === editingUser.id ? { ...u, role: selectedRole } : u)));
      showToast(`Role for ${editingUser.name} updated to ${selectedRole}!`, 'success');
      setEditingUser(null);
      if (refreshStaff) refreshStaff();
    } catch (err) {
      showToast(err.message || 'Failed to update user role', 'danger');
    } finally {
      setSavingRole(false);
    }
  };

  const handleDeleteUser = async (userId, userName) => {
    if (!window.confirm(`Are you sure you want to deactivate staff account "${userName}"?`)) return;
    try {
      await api.users.delete(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
      showToast(`Account "${userName}" removed`, 'success');
      if (refreshStaff) refreshStaff();
    } catch (err) {
      showToast(err.message || 'Failed to remove account', 'danger');
    }
  };

  const handleSwitchToPerson = (u) => {
    if (switchPerson) {
      switchPerson(u);
      showToast(`Logged in as ${u.name} (${u.role})`, 'success');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>Staff Directory & Roles</h1>
            <span className="badge badge-primary">
              Role-Based Access Control
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            Assign access roles per person across Administrator, Manager, Chef, Waiter, and Cashier stations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={loadUsers} className="btn btn-secondary">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Staff</span>
          </button>
          <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
            <Plus size={16} />
            <span>Add Staff Member</span>
          </button>
        </div>
      </div>

      {/* Role Clearance Cards Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        {Object.entries(ROLE_DEFINITIONS).map(([rKey, rDef]) => {
          const count = users.filter(u => u.role === rKey).length;
          return (
            <div
              key={rKey}
              className="glass-panel"
              style={{
                padding: '14px 16px',
                borderLeft: `4px solid ${rDef.color}`,
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: rDef.color }}>
                  {rDef.label}
                </span>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    background: rDef.bg,
                    color: rDef.color,
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                  }}
                >
                  {count} Staff
                </span>
              </div>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.3, marginTop: '2px' }}>
                {rDef.access}
              </p>
            </div>
          );
        })}
      </div>

      {/* Users Grid */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 10px' }} />
          Loading staff directory and assigned roles...
        </div>
      ) : users.length === 0 ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <UserCog size={36} style={{ margin: '0 auto 10px', opacity: 0.4 }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>No Staff Accounts Found</h3>
          <p style={{ fontSize: '0.85rem', marginTop: '6px' }}>
            Click "Add Staff Member" to provision accounts with appropriate role clearances.
          </p>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '16px',
          }}
        >
          {users.map(u => {
            const roleInfo = ROLE_DEFINITIONS[u.role] || {
              label: u.role,
              badgeClass: 'badge-primary',
              color: 'var(--primary)',
              access: 'Custom Access',
            };
            const isCurrent = currentAuthUser?.email === u.email || currentAuthUser?.name === u.name;

            return (
              <div
                key={u.id}
                className="glass-panel"
                style={{
                  padding: '18px',
                  borderRadius: 'var(--radius-lg)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  border: isCurrent ? '1.5px solid var(--primary)' : '1px solid var(--border-subtle)',
                  background: isCurrent ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-card)',
                  position: 'relative',
                }}
              >
                {isCurrent && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '12px',
                      right: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: 'var(--primary)',
                      background: 'rgba(99, 102, 241, 0.15)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)',
                    }}
                  >
                    <CheckCircle2 size={12} />
                    <span>Active Session</span>
                  </div>
                )}

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', paddingRight: isCurrent ? '80px' : '0' }}>
                  <div
                    style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: '50%',
                      background: `linear-gradient(135deg, ${roleInfo.color} 0%, rgba(15, 23, 42, 0.8) 100%)`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#fff',
                      fontWeight: 800,
                      fontSize: '1.15rem',
                      border: `2px solid ${roleInfo.color}`,
                      flexShrink: 0,
                    }}
                  >
                    {u.name ? u.name[0].toUpperCase() : 'U'}
                  </div>
                  <div style={{ overflow: 'hidden' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {u.name}
                    </h3>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {u.email}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className={`badge ${roleInfo.badgeClass}`} style={{ fontSize: '0.72rem' }}>
                      {roleInfo.label}
                    </span>
                    <button
                      onClick={() => openRoleEditModal(u)}
                      className="btn btn-secondary btn-xs"
                      style={{ padding: '3px 8px', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                      title="Change user's access role"
                    >
                      <Edit3 size={11} />
                      <span>Change Role</span>
                    </button>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', lineHeight: 1.3 }}>
                    {roleInfo.access}
                  </div>
                </div>

                {/* Card Action Controls: Login as Person & Remove */}
                <div style={{ display: 'flex', gap: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', marginTop: 'auto' }}>
                  <button
                    onClick={() => handleSwitchToPerson(u)}
                    disabled={isCurrent}
                    className={`btn btn-sm ${isCurrent ? 'btn-secondary' : 'btn-primary'}`}
                    style={{
                      flex: 1,
                      fontSize: '0.75rem',
                      padding: '6px 10px',
                      opacity: isCurrent ? 0.6 : 1,
                    }}
                  >
                    <UserCheck size={13} />
                    <span>{isCurrent ? 'Current Session' : `Login as ${u.name.split(' ')[0]}`}</span>
                  </button>

                  <button
                    onClick={() => handleDeleteUser(u.id, u.name)}
                    className="btn btn-secondary btn-sm"
                    style={{ padding: '6px 10px', color: '#ef4444' }}
                    title="Remove staff account"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Role Modal */}
      {editingUser && (
        <div className="modal-overlay" onClick={() => setEditingUser(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '24px', maxWidth: '480px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', background: 'var(--primary-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <Shield size={18} />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Assign Access Role</h2>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Person: <strong style={{ color: 'var(--text-primary)' }}>{editingUser.name}</strong> ({editingUser.email})
                  </div>
                </div>
              </div>
              <button onClick={() => setEditingUser(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleUpdateRole} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '8px' }}>
                  Select Role According to Person
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(ROLE_DEFINITIONS).map(([rKey, rDef]) => (
                    <label
                      key={rKey}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '10px',
                        padding: '10px 12px',
                        borderRadius: 'var(--radius-md)',
                        background: selectedRole === rKey ? 'rgba(99, 102, 241, 0.12)' : 'var(--bg-tertiary)',
                        border: '1px solid',
                        borderColor: selectedRole === rKey ? 'var(--primary)' : 'var(--border-subtle)',
                        cursor: 'pointer',
                      }}
                    >
                      <input
                        type="radio"
                        name="access_role"
                        value={rKey}
                        checked={selectedRole === rKey}
                        onChange={() => setSelectedRole(rKey)}
                        style={{ marginTop: '3px' }}
                      />
                      <div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 700, color: rDef.color }}>
                          {rDef.label} ({rKey})
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          {rDef.access}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setEditingUser(null)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" disabled={savingRole} className="btn btn-primary" style={{ flex: 1 }}>
                  {savingRole ? 'Saving Role...' : 'Save Role Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Staff Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '24px', maxWidth: '460px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', background: 'var(--primary-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <UserCog size={18} />
                </div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Provision Staff Person</h2>
              </div>
              <button onClick={() => setShowAddModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateUser} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Staff Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kumar"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Work Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="ramesh@dineflow.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Assigned Access Role</label>
                <select value={role} onChange={e => setRole(e.target.value)} className="select">
                  <option value="ADMIN">System Administrator (Full Privileges)</option>
                  <option value="MANAGER">Operations Manager</option>
                  <option value="CHEF">Head Chef (Kitchen KDS & Recipes)</option>
                  <option value="WAITER">Floor Waiter (Tables & Orders)</option>
                  <option value="CASHIER">Billing Cashier (Invoices & Payments)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Temporary Password</label>
                <input
                  type="text"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="input"
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="btn btn-primary" style={{ flex: 1 }}>
                  {submitting ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
