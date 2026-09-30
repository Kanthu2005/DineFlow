import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { UserCog, Plus, Shield, Mail, Check, X, Trash2 } from 'lucide-react';

export default function UsersView() {
  const { showToast } = useToast();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // Form
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
        name,
        email: email.toLowerCase(),
        password,
        role,
        is_active: true,
      });
      showToast(`Staff member "${name}" registered with role ${role}!`, 'success');
      setUsers(prev => [res, ...prev]);
      setShowAddModal(false);
      setName('');
      setEmail('');
    } catch (err) {
      showToast(err.message || 'Failed to register user', 'danger');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteUser = async (userId, userName) => {
    if (!window.confirm(`Are you sure you want to deactivate staff account "${userName}"?`)) return;
    try {
      await api.users.delete(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
      showToast(`Account "${userName}" removed`, 'success');
    } catch (err) {
      showToast(err.message || 'Failed to remove account', 'danger');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>Staff Directory & Permissions</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Manage staff accounts across Administrator, Manager, Chef, Waiter, and Cashier roles.
          </p>
        </div>

        <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
          <Plus size={16} />
          <span>Add Staff Member</span>
        </button>
      </div>

      {/* Users Grid */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading staff directory...
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '16px',
          }}
        >
          {users.map(u => (
            <div
              key={u.id}
              className="glass-panel"
              style={{
                padding: '20px',
                borderRadius: 'var(--radius-lg)',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '50%',
                      background: 'var(--primary-gradient)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#fff',
                      fontWeight: 700,
                      fontSize: '1.1rem',
                    }}
                  >
                    {u.name ? u.name[0].toUpperCase() : 'U'}
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>{u.name}</h3>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{u.email}</div>
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteUser(u.id, u.name)}
                  className="btn btn-secondary btn-sm"
                  style={{ padding: '6px', color: 'var(--text-muted)' }}
                  title="Remove account"
                >
                  <Trash2 size={13} />
                </button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                <span className="badge badge-primary">{u.role}</span>
                <span style={{ fontSize: '0.75rem', color: u.is_active ? 'var(--success)' : 'var(--danger)' }}>
                  &bull; {u.is_active ? 'Active Account' : 'Inactive'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Staff Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '24px', maxWidth: '440px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Provision Staff Account</h2>
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
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Assigned Station Role</label>
                <select value={role} onChange={e => setRole(e.target.value)} className="select">
                  <option value="ADMIN">System Administrator (Full Privileges)</option>
                  <option value="MANAGER">General Manager</option>
                  <option value="CHEF">Head Chef (Kitchen KDS)</option>
                  <option value="WAITER">Floor Waiter (POS & Tables)</option>
                  <option value="CASHIER">Billing Cashier (Invoices & Payments)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Initial Temporary Password</label>
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
