import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { 
  Clock, Search, Filter, RefreshCw, CheckCircle, ChefHat, 
  Receipt, XCircle, ChevronDown, ChevronUp, User, Table, Utensils,
  PlusCircle, Sparkles, CheckCircle2, ArrowRight
} from 'lucide-react';
import AddMoreItemsModal from '../components/AddMoreItemsModal';

const STATUS_TABS = [
  'ALL', 'PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'SERVED', 'DELIVERED', 'COMPLETED', 'CANCELLED'
];

export default function OrdersView({ onNavigateToBilling }) {
  const { showToast } = useToast();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ALL');
  const [search, setSearch] = useState('');
  const [expandedOrders, setExpandedOrders] = useState({});
  const [updatingId, setUpdatingId] = useState(null);
  const [addMoreOrder, setAddMoreOrder] = useState(null);
  const [updatingItemId, setUpdatingItemId] = useState(null);

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
      loadOrders();

      if (newStatus === 'SERVED' || newStatus === 'DELIVERED') {
        showToast('Food delivered! You can add more items anytime or generate the bill.', 'info');
      }
    } catch (err) {
      showToast(err.message || 'Failed to update order status', 'danger');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleUpdateItemStatus = async (orderId, itemId, newStatus) => {
    setUpdatingItemId(itemId);
    try {
      await api.orders.updateItemStatus(orderId, itemId, newStatus);
      showToast(`Item updated to ${newStatus}`, 'success');
      loadOrders();
    } catch (err) {
      showToast(err.message || 'Failed to update item status', 'danger');
    } finally {
      setUpdatingItemId(null);
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

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {['PLACED', 'CONFIRMED', 'SENT_TO_KITCHEN', 'PREPARING', 'READY', 'SERVED', 'DELIVERED', 'PARTIALLY_DELIVERED'].includes(order.status) && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setAddMoreOrder(order);
                        }}
                        className="btn btn-primary btn-sm"
                        style={{
                          background: 'linear-gradient(135deg, var(--primary) 0%, #a855f7 100%)',
                          border: 'none',
                          boxShadow: '0 2px 8px rgba(99, 102, 241, 0.35)',
                          gap: '5px',
                          fontSize: '0.74rem',
                          fontWeight: 700,
                          padding: '4px 10px',
                        }}
                      >
                        <PlusCircle size={13} />
                        <span>+ Add Items</span>
                      </button>
                    )}

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
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Dishes Ordered & Fulfillment Flow
                      </h4>
                      {['PLACED', 'CONFIRMED', 'SENT_TO_KITCHEN', 'PREPARING', 'READY', 'SERVED', 'DELIVERED', 'PARTIALLY_DELIVERED'].includes(order.status) && (
                        <button
                          onClick={() => setAddMoreOrder(order)}
                          className="btn btn-sm btn-secondary"
                          style={{
                            borderColor: 'var(--primary)',
                            color: 'var(--primary)',
                            fontSize: '0.72rem',
                            gap: '5px',
                            padding: '3px 9px',
                          }}
                        >
                          <PlusCircle size={13} />
                          <span>Add More Items to this Order</span>
                        </button>
                      )}
                    </div>

                    {/* Items table with clear distinction between previously delivered vs newly added */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
                      {order.items?.map((it, idx) => {
                        const name = it.name || it.item_name_snapshot || it.menu_item_name || `Item ${idx + 1}`;
                        const qty = it.quantity || 1;
                        const rate = parseFloat(it.price_at_addition || it.price || it.unit_price_snapshot || it.unit_price || (it.item_total ? it.item_total / qty : 0));
                        const total = parseFloat(it.item_total || rate * qty);
                        const isDelivered = it.status === 'DELIVERED' || it.status === 'SERVED';
                        const isAdditional = it.is_additional || (it.batch_number && it.batch_number > 1);

                        return (
                          <div
                            key={it.id || idx}
                            style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              flexWrap: 'wrap',
                              gap: '8px',
                              padding: '10px 14px',
                              borderRadius: 'var(--radius-sm)',
                              background: isAdditional ? 'rgba(99, 102, 241, 0.06)' : 'var(--bg-tertiary)',
                              borderLeft: isDelivered 
                                ? '3px solid var(--success)' 
                                : isAdditional 
                                ? '3px solid #a855f7' 
                                : '3px solid var(--warning)',
                              fontSize: '0.85rem',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                              {/* Round badge */}
                              {isAdditional ? (
                                <span style={{ fontSize: '0.68rem', background: 'rgba(168, 85, 247, 0.2)', color: '#c084fc', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                                  Round {it.batch_number || 2} (Additional)
                                </span>
                              ) : (
                                <span style={{ fontSize: '0.68rem', background: 'rgba(255, 255, 255, 0.08)', color: 'var(--text-muted)', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                                  Round 1 (Original)
                                </span>
                              )}

                              {/* Item status badge */}
                              <span className={`badge ${
                                isDelivered ? 'badge-success' :
                                it.status === 'READY' ? 'badge-primary' :
                                it.status === 'PREPARING' ? 'badge-warning' : 'badge-secondary'
                              }`} style={{ fontSize: '0.65rem' }}>
                                {it.status || (isDelivered ? 'DELIVERED' : 'PENDING')}
                              </span>

                              <div>
                                <span style={{ fontWeight: 600 }}>{name}</span>
                                <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>
                                  &times; {qty} {rate > 0 ? `(@ ₹${rate.toFixed(2)})` : ''}
                                </span>
                                {it.added_at && isAdditional && (
                                  <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                                    (Added {new Date(it.added_at).toLocaleTimeString()})
                                  </span>
                                )}
                                {it.special_instructions && (
                                  <div style={{ fontSize: '0.72rem', color: 'var(--warning)', marginTop: '2px' }}>
                                    Note: {it.special_instructions}
                                  </div>
                                )}
                              </div>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                              <span style={{ fontWeight: 700, fontFamily: 'Outfit' }}>
                                ₹{total.toFixed(2)}
                              </span>

                              {/* Quick item status advance buttons */}
                              {it.id && (
                                <div style={{ display: 'flex', gap: '4px' }}>
                                  {it.status === 'PENDING' && (
                                    <button
                                      onClick={() => handleUpdateItemStatus(order.id, it.id, 'PREPARING')}
                                      disabled={updatingItemId === it.id}
                                      className="btn btn-secondary btn-sm"
                                      style={{ fontSize: '0.68rem', padding: '2px 6px' }}
                                      title="Mark item cooking"
                                    >
                                      Cook
                                    </button>
                                  )}
                                  {it.status === 'PREPARING' && (
                                    <button
                                      onClick={() => handleUpdateItemStatus(order.id, it.id, 'READY')}
                                      disabled={updatingItemId === it.id}
                                      className="btn btn-primary btn-sm"
                                      style={{ fontSize: '0.68rem', padding: '2px 6px' }}
                                      title="Mark item ready"
                                    >
                                      Ready
                                    </button>
                                  )}
                                  {it.status === 'READY' && (
                                    <button
                                      onClick={() => handleUpdateItemStatus(order.id, it.id, 'DELIVERED')}
                                      disabled={updatingItemId === it.id}
                                      className="btn btn-success btn-sm"
                                      style={{ fontSize: '0.68rem', padding: '2px 6px' }}
                                      title="Mark item delivered"
                                    >
                                      Deliver
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Financial Summary breakdown */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '14px' }}>
                      <div style={{ minWidth: '260px', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.78rem', background: 'rgba(0,0,0,0.2)', padding: '12px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                        {order.previous_item_total !== undefined && parseFloat(order.previous_item_total) > 0 && (
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                            <span>Previous Items Total:</span>
                            <span>₹{parseFloat(order.previous_item_total).toFixed(2)}</span>
                          </div>
                        )}
                        {order.new_item_total !== undefined && parseFloat(order.new_item_total) > 0 && (
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#c084fc', fontWeight: 600 }}>
                            <span>Newly Added Items Total:</span>
                            <span>+₹{parseFloat(order.new_item_total).toFixed(2)}</span>
                          </div>
                        )}
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontWeight: 600 }}>
                          <span>Subtotal:</span>
                          <span>₹{parseFloat(order.subtotal || 0).toFixed(2)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                          <span>GST (5%):</span>
                          <span>₹{parseFloat(order.tax_amount || 0).toFixed(2)}</span>
                        </div>
                        {parseFloat(order.discount_amount || 0) > 0 && (
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#10b981' }}>
                            <span>Discount:</span>
                            <span>-₹{parseFloat(order.discount_amount || 0).toFixed(2)}</span>
                          </div>
                        )}
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 800, fontSize: '0.95rem', color: 'var(--primary)', borderTop: '1px dashed var(--border-subtle)', paddingTop: '6px', marginTop: '3px', fontFamily: 'Outfit' }}>
                          <span>Total Payable:</span>
                          <span>₹{parseFloat(order.total_amount || 0).toFixed(2)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Status Advance Action Buttons */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center', justifyContent: 'flex-end', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                      {/* Add More Items button */}
                      {['PLACED', 'CONFIRMED', 'SENT_TO_KITCHEN', 'PREPARING', 'READY', 'SERVED', 'DELIVERED', 'PARTIALLY_DELIVERED'].includes(order.status) && (
                        <button
                          onClick={() => setAddMoreOrder(order)}
                          className="btn btn-primary btn-sm"
                          style={{
                            background: 'linear-gradient(135deg, var(--primary) 0%, #a855f7 100%)',
                            border: 'none',
                            gap: '6px',
                          }}
                        >
                          <PlusCircle size={14} />
                          <span>Add More Items</span>
                        </button>
                      )}

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

                      {(order.status === 'READY' || order.status === 'PARTIALLY_DELIVERED') && (
                        <button
                          onClick={() => handleUpdateStatus(order.id, 'DELIVERED')}
                          disabled={updatingId === order.id}
                          className="btn btn-primary btn-sm"
                        >
                          <Utensils size={14} />
                          <span>Mark Delivered to Table</span>
                        </button>
                      )}

                      {/* Invoice Generation Trigger */}
                      {['SERVED', 'DELIVERED', 'READY', 'CONFIRMED'].includes(order.status) && (
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

      {/* Add More Items Modal */}
      <AddMoreItemsModal
        order={addMoreOrder}
        isOpen={!!addMoreOrder}
        onClose={() => setAddMoreOrder(null)}
        onSuccess={() => {
          setAddMoreOrder(null);
          loadOrders();
        }}
        onNavigateToBilling={onNavigateToBilling}
      />
    </div>
  );
}
