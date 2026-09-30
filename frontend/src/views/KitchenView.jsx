import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { 
  ChefHat, Clock, AlertTriangle, CheckCircle2, Play, 
  RefreshCw, User, Flame, ArrowRight
} from 'lucide-react';

export default function KitchenView() {
  const { showToast } = useToast();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ACTIVE'); // ACTIVE, ALL, COMPLETED
  const [updatingId, setUpdatingId] = useState(null);

  const loadTickets = async () => {
    setLoading(true);
    try {
      const res = await api.kitchen.getTickets();
      setTickets(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error('Kitchen tickets load error:', err);
      showToast('Could not load kitchen tickets', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
    const interval = setInterval(loadTickets, 15000); // 15s auto-poll for kitchen display
    return () => clearInterval(interval);
  }, []);

  const handleUpdateStatus = async (ticketId, nextStatus) => {
    setUpdatingId(ticketId);
    try {
      await api.kitchen.updateStatus(ticketId, nextStatus);
      showToast(`Ticket moved to ${nextStatus}`, 'success');
      setTickets(prev => prev.map(t => t.id === ticketId ? { ...t, status: nextStatus } : t));
    } catch (err) {
      showToast(err.message || 'Status update failed', 'danger');
    } finally {
      setUpdatingId(null);
    }
  };

  const filteredTickets = tickets.filter(t => {
    if (filter === 'ACTIVE') return t.status === 'PENDING' || t.status === 'PREPARING';
    if (filter === 'COMPLETED') return t.status === 'READY' || t.status === 'SERVED';
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ padding: '8px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--danger)' }}>
            <Flame size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>Kitchen Display System (KDS)</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Real-time cook queue, urgency prioritization, and line prep tickets.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-tertiary)', padding: '4px', borderRadius: 'var(--radius-md)' }}>
            {['ACTIVE', 'COMPLETED', 'ALL'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.75rem', padding: '4px 10px' }}
              >
                {f}
              </button>
            ))}
          </div>
          <button onClick={loadTickets} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Poll</span>
          </button>
        </div>
      </div>

      {/* Tickets Grid */}
      {loading && tickets.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading kitchen preparation tickets...
        </div>
      ) : filteredTickets.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <ChefHat size={40} style={{ opacity: 0.3, margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Kitchen Queue Clear!</h3>
          <p style={{ fontSize: '0.85rem', marginTop: '4px' }}>No orders currently awaiting cook prep in this view.</p>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '18px',
          }}
        >
          {filteredTickets.map(ticket => {
            const isUrgent = ticket.priority === 'URGENT' || ticket.priority === 'HIGH';
            const isCooking = ticket.status === 'PREPARING';
            const isReady = ticket.status === 'READY';

            return (
              <div
                key={ticket.id}
                className="glass-panel"
                style={{
                  borderRadius: 'var(--radius-lg)',
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  borderTop: isUrgent ? '3px solid var(--danger)' : isCooking ? '3px solid var(--warning)' : '3px solid var(--primary)',
                }}
              >
                {/* Ticket Header */}
                <div style={{ padding: '14px 18px', background: 'rgba(0, 0, 0, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 800, fontSize: '1.1rem', fontFamily: 'Outfit' }}>
                        Ticket #{ticket.id?.slice(-6).toUpperCase()}
                      </span>
                      <span className={`badge ${isUrgent ? 'badge-danger' : 'badge-primary'}`}>
                        {ticket.priority || 'NORMAL'}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span>Order #{ticket.order_number || ticket.order_id?.slice(-6) || 'Direct'}</span>
                      {ticket.table_number && (
                        <span style={{ fontWeight: 800, color: 'var(--primary)', background: 'rgba(99, 102, 241, 0.15)', padding: '1px 6px', borderRadius: '4px' }}>
                          {ticket.table_number.toString().toUpperCase().startsWith('T') ? ticket.table_number : `T${ticket.table_number}`}
                        </span>
                      )}
                    </div>
                  </div>

                  <span className={`badge ${isReady ? 'badge-success' : isCooking ? 'badge-warning' : 'badge-primary'}`}>
                    {ticket.status}
                  </span>
                </div>

                {/* Items List */}
                <div style={{ padding: '16px 18px', flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {ticket.items && ticket.items.length > 0 ? (
                    ticket.items.map((it, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                          background: 'var(--bg-tertiary)',
                          fontSize: '0.85rem',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ width: '22px', height: '22px', borderRadius: '4px', background: 'var(--primary-gradient)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.75rem' }}>
                            {it.quantity}
                          </span>
                          <span style={{ fontWeight: 600 }}>{it.menu_item_name || it.name || `Dish #${idx + 1}`}</span>
                        </div>
                        {it.special_instructions && (
                          <span style={{ fontSize: '0.7rem', color: 'var(--warning)', fontStyle: 'italic' }}>
                            {it.special_instructions}
                          </span>
                        )}
                      </div>
                    ))
                  ) : (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Items mapped from order queue.
                    </div>
                  )}
                </div>

                {/* Status Advancement Buttons */}
                <div style={{ padding: '14px 18px', borderTop: '1px solid var(--border-subtle)', background: 'rgba(0, 0, 0, 0.15)', display: 'flex', gap: '10px' }}>
                  {ticket.status === 'PENDING' && (
                    <button
                      onClick={() => handleUpdateStatus(ticket.id, 'PREPARING')}
                      disabled={updatingId === ticket.id}
                      className="btn btn-primary"
                      style={{ flex: 1, padding: '9px' }}
                    >
                      <Play size={14} />
                      <span>Start Cooking</span>
                    </button>
                  )}

                  {ticket.status === 'PREPARING' && (
                    <button
                      onClick={() => handleUpdateStatus(ticket.id, 'READY')}
                      disabled={updatingId === ticket.id}
                      className="btn btn-success"
                      style={{ flex: 1, padding: '9px' }}
                    >
                      <CheckCircle2 size={14} />
                      <span>Mark Food Ready</span>
                    </button>
                  )}

                  {ticket.status === 'READY' && (
                    <button
                      onClick={() => handleUpdateStatus(ticket.id, 'SERVED')}
                      disabled={updatingId === ticket.id}
                      className="btn btn-secondary"
                      style={{ flex: 1, padding: '9px', borderColor: 'var(--success)', color: 'var(--success)' }}
                    >
                      <ArrowRight size={14} />
                      <span>Dispatched to Waiter</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
