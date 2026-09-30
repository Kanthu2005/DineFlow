import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { 
  Clock, Search, Filter, RefreshCw, CheckCircle, ChefHat, 
  Receipt, XCircle, ChevronDown, ChevronUp, User, Table, Utensils
} from 'lucide-react';

const STATUS_TABS = [
  'ALL', 'PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'SERVED', 'COMPLETED', 'CANCELLED'
];

export default function OrdersView({ onNavigateToBilling }) {
  const { showToast } = useToast();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ALL');
  const [search, setSearch] = useState('');
  const [expandedOrders, setExpandedOrders] = useState({});
  const [updatingId, setUpdatingId] = useState(null);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const res = await api.orders.getAll();
      setOrders(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error('Error fetching orders:', err);
      showToast('Could not load orders', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const toggleExpand = (id) => {
    setExpandedOrders(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleUpdateStatus = async (orderId, newStatus) => {
    setUpdatingId(orderId);
    try {
      await api.orders.updateStatus(orderId, newStatus);
      showToast(`Order status updated to ${newStatus}`, 'success');
      setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o));

      // If marked SERVED or COMPLETED, we can prompt for billing
      if (newStatus === 'SERVED') {
        showToast('Food served! You can now generate the bill under Billing tab.', 'info');
      }
    } catch (err) {
      showToast(err.message || 'Failed to update order status', 'danger');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleGenerateInvoice = async (orderId) => {
    try {
      const inv = await api.billing.createInvoice(orderId);
      showToast(`Invoice #${inv.invoice_number || inv.id} generated!`, 'success');
      if (onNavigateToBilling) onNavigateToBilling(inv);
    } catch (err) {
      showToast(err.message || 'Failed to generate invoice', 'danger');
    }
  };

  const filteredOrders = orders.filter(o => {
    const matchesTab = activeTab === 'ALL' || o.status === activeTab;
    const matchesSearch = 
      (o.order_number && o.order_number.toLowerCase().includes(search.toLowerCase())) ||
      (o.customer_name && o.customer_name.toLowerCase().includes(search.toLowerCase())) ||
      (o.id && o.id.toLowerCase().includes(search.toLowerCase()));
    return matchesTab && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>Live Orders Directory</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Track order lifecycle from creation, cooking preparation, serving to final invoice settlement.
          </p>
        </div>
        <button onClick={loadOrders} className="btn btn-secondary btn-sm">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh List</span>
        </button>
      </div>

      {/* Tabs & Search */}
      <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Status Filter Tabs */}
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
          {STATUS_TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`btn btn-sm ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
              style={{ borderRadius: 'var(--radius-full)', fontSize: '0.75rem', padding: '5px 12px' }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Search */}
        <div style={{ position: 'relative', maxWidth: '380px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Filter by Order # or Customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input"
            style={{ paddingLeft: '36px', height: '36px', fontSize: '0.825rem' }}
          />
        </div>
      </div>

      {/* Orders List */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading active orders...
        </div>
      ) : filteredOrders.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No orders found matching criteria.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {filteredOrders.map(order => {
            const isExpanded = !!expandedOrders[order.id];
            return (
              <div
                key={order.id}
                className="glass-panel"
                style={{
                  borderRadius: 'var(--radius-md)',
                  overflow: 'hidden',
                  transition: 'border-color 0.2s ease',
                }}
              >
                {/* Main Card Header */}
                <div
                  style={{
                    padding: '16px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '12px',
                    cursor: 'pointer',
                    background: 'var(--bg-card)',
                  }}
                  onClick={() => toggleExpand(order.id)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <span style={{ fontWeight: 800, fontSize: '1.05rem', fontFamily: 'Outfit' }}>
                      #{order.order_number || order.id?.slice(-6)}
                    </span>
                    <span className={`badge ${
                      order.status === 'CONFIRMED' || order.status === 'READY' || order.status === 'COMPLETED' ? 'badge-success' :
                      order.status === 'PREPARING' ? 'badge-warning' :
                      order.status === 'CANCELLED' ? 'badge-danger' : 'badge-primary'
                    }`}>
                      {order.status}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {order.order_type || 'DINE_IN'}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--primary)', fontFamily: 'Outfit' }}>
                        ₹{parseFloat(order.total_amount || 0).toFixed(2)}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {order.items?.length || 0} items
                      </div>
                    </div>
                    {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  </div>
                </div>

                {/* Sub-Header info bar */}
                <div
                  style={{
                    padding: '8px 20px',
                    background: 'rgba(0, 0, 0, 0.15)',
                    borderTop: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.775rem',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span>Customer: <strong style={{ color: 'var(--text-primary)' }}>{order.customer_name || 'Walk-in'}</strong></span>
                    {order.customer_phone && <span>Phone: {order.customer_phone}</span>}
                  </div>
                  <span>Placed: {order.created_at ? new Date(order.created_at).toLocaleTimeString() : 'Just now'}</span>
                </div>

                {/* Expanded Details & Actions */}
                {isExpanded && (
                  <div style={{ padding: '18px 20px', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)' }}>
                    <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '10px', textTransform: 'uppercase' }}>
                      Dishes Ordered
                    </h4>

                    {/* Items table */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '18px' }}>
                      {order.items?.map((it, idx) => (
                        <div
                          key={idx}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            padding: '8px 12px',
                            borderRadius: 'var(--radius-sm)',
                            background: 'var(--bg-tertiary)',
                            fontSize: '0.85rem',
                          }}
                        >
                          <div>
                            <span style={{ fontWeight: 600 }}>{it.menu_item_name || it.name || `Item ${idx + 1}`}</span>
                            <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>&times; {it.quantity}</span>
                            {it.special_instructions && (
                              <div style={{ fontSize: '0.75rem', color: 'var(--warning)', marginTop: '2px' }}>
                                Note: {it.special_instructions}
                              </div>
                            )}
                          </div>
                          <span style={{ fontWeight: 700 }}>
                            ₹{(parseFloat(it.price || it.unit_price || 0) * (it.quantity || 1)).toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Status Advance Action Buttons */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center', justifyContent: 'flex-end', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                      {order.status === 'PENDING' && (
                        <button
                          onClick={() => handleUpdateStatus(order.id, 'CONFIRMED')}
                          disabled={updatingId === order.id}
                          className="btn btn-success btn-sm"
                        >
                          <CheckCircle size={14} />
                          <span>Confirm Order</span>
                        </button>
                      )}

                      {order.status === 'CONFIRMED' && (
                        <button
                          onClick={() => handleUpdateStatus(order.id, 'PREPARING')}
                          disabled={updatingId === order.id}
                          className="btn btn-primary btn-sm"
                        >
                          <ChefHat size={14} />
                          <span>Start Cooking</span>
                        </button>
                      )}

                      {order.status === 'PREPARING' && (
                        <button
                          onClick={() => handleUpdateStatus(order.id, 'READY')}
                          disabled={updatingId === order.id}
                          className="btn btn-success btn-sm"
                        >
                          <CheckCircle size={14} />
                          <span>Mark Food Ready</span>
                        </button>
                      )}

                      {order.status === 'READY' && (
                        <button
                          onClick={() => handleUpdateStatus(order.id, 'SERVED')}
                          disabled={updatingId === order.id}
                          className="btn btn-primary btn-sm"
                        >
                          <Utensils size={14} />
                          <span>Mark Served to Table</span>
                        </button>
                      )}

                      {/* Invoice Generation Trigger */}
                      {['SERVED', 'READY', 'CONFIRMED'].includes(order.status) && (
                        <button
                          onClick={() => handleGenerateInvoice(order.id)}
                          className="btn btn-secondary btn-sm"
                          style={{ borderColor: 'var(--primary)', color: 'var(--primary)' }}
                        >
                          <Receipt size={14} />
                          <span>Generate Bill / Invoice</span>
                        </button>
                      )}

                      {order.status !== 'CANCELLED' && order.status !== 'COMPLETED' && (
                        <button
                          onClick={() => handleUpdateStatus(order.id, 'CANCELLED')}
                          disabled={updatingId === order.id}
                          className="btn btn-danger btn-sm"
                        >
                          <XCircle size={14} />
                          <span>Cancel Order</span>
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
