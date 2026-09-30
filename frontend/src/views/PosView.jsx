import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { 
  Search, ShoppingCart, Plus, Minus, Trash2, Clock, Check, 
  Send, Sparkles, Filter, Leaf, Utensils
} from 'lucide-react';

export default function PosView({ onOrderPlaced }) {
  const { showToast } = useToast();
  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [tables, setTables] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [vegOnly, setVegOnly] = useState(false);
  const [loading, setLoading] = useState(true);

  // Cart State
  const [cart, setCart] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [orderType, setOrderType] = useState('DINE_IN');
  const [discountAmount, setDiscountAmount] = useState(0);
  const [placingOrder, setPlacingOrder] = useState(false);
  const [confirmedOrder, setConfirmedOrder] = useState(null);

  useEffect(() => {
    loadPosData();
  }, []);

  const loadPosData = async () => {
    setLoading(true);
    try {
      const [catsRes, itemsRes, tablesRes] = await Promise.all([
        api.menu.getCategories(),
        api.menu.getItems(),
        api.tables.getAll(),
      ]);
      setCategories(Array.isArray(catsRes) ? catsRes : []);
      setItems(Array.isArray(itemsRes) ? itemsRes : []);
      setTables(Array.isArray(tablesRes) ? tablesRes : []);
    } catch (err) {
      console.error('POS data error:', err);
      showToast('Could not load menu catalog or tables', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Add Item to Cart
  const addToCart = (item) => {
    setCart((prev) => {
      const existing = prev.find((c) => c.item.id === item.id);
      if (existing) {
        return prev.map((c) =>
          c.item.id === item.id ? { ...c, quantity: c.quantity + 1 } : c
        );
      }
      return [...prev, { item, quantity: 1, specialInstructions: '' }];
    });
    showToast(`Added ${item.name} to cart`, 'success', 1500);
  };

  // Update Quantity
  const updateQuantity = (itemId, delta) => {
    setCart((prev) =>
      prev
        .map((c) => {
          if (c.item.id === itemId) {
            const newQty = c.quantity + delta;
            return newQty > 0 ? { ...c, quantity: newQty } : null;
          }
          return c;
        })
        .filter(Boolean)
    );
  };

  // Update Item Instructions
  const updateInstructions = (itemId, text) => {
    setCart((prev) =>
      prev.map((c) => (c.item.id === itemId ? { ...c, specialInstructions: text } : c))
    );
  };

  // Filter items
  const filteredItems = items.filter((item) => {
    const matchesCategory =
      selectedCategory === 'ALL' || item.category_id === selectedCategory;
    const matchesSearch =
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesVeg = !vegOnly || item.is_vegetarian;
    return matchesCategory && matchesSearch && matchesVeg;
  });

  // Financial calculations
  const subtotal = cart.reduce((sum, c) => {
    const p = parseFloat(c.item.price || 0);
    return sum + p * c.quantity;
  }, 0);

  const tax = subtotal * 0.05; // 5% GST
  const discount = Math.min(subtotal, Math.max(0, parseFloat(discountAmount) || 0));
  const total = Math.max(0, subtotal + tax - discount);

  // Place Order
  const handlePlaceOrder = async () => {
    if (cart.length === 0) {
      showToast('Your cart is empty. Add dishes first.', 'warning');
      return;
    }

    if (orderType === 'DINE_IN' && !selectedTable) {
      showToast('Please select a dining table for Dine-In orders.', 'warning');
      return;
    }

    setPlacingOrder(true);
    try {
      const orderPayload = {
        customer_name: customerName || 'Walk-in Guest',
        customer_phone: customerPhone || '9876543210',
        table_id: orderType === 'DINE_IN' ? selectedTable : null,
        order_type: orderType,
        items: cart.map((c) => ({
          menu_item_id: c.item.id,
          quantity: c.quantity,
          special_instructions: c.specialInstructions || '',
        })),
      };

      const newOrder = await api.orders.create(orderPayload);

      // Auto-create Kitchen Ticket for live preparation
      try {
        await api.kitchen.createTicket(newOrder.id, 'NORMAL');
      } catch (ktErr) {
        console.warn('Kitchen ticket auto-dispatch notice:', ktErr);
      }

      setConfirmedOrder(newOrder);
      setCart([]);
      setCustomerName('');
      setCustomerPhone('');
      setSelectedTable('');
      setDiscountAmount(0);
      showToast(`Order #${newOrder.order_number || newOrder.id} dispatched to kitchen!`, 'success');
      if (onOrderPlaced) onOrderPlaced(newOrder);
    } catch (err) {
      console.error('Order creation failed:', err);
      showToast(err.message || 'Failed to place order', 'danger');
    } finally {
      setPlacingOrder(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px', height: 'calc(100vh - 120px)' }}>
      {/* Left: Menu Catalog */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', overflowY: 'auto', paddingRight: '6px' }}>
        {/* Top Controls Bar */}
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', justifyContent: 'space-between' }}>
          {/* Search Input */}
          <div style={{ position: 'relative', flex: '1 1 240px' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search dishes by name or ingredients..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input"
              style={{ paddingLeft: '36px', height: '40px', fontSize: '0.85rem' }}
            />
          </div>

          {/* Veg Only Toggle */}
          <button
            onClick={() => setVegOnly(!vegOnly)}
            className={`btn btn-sm ${vegOnly ? 'btn-success' : 'btn-secondary'}`}
            style={{ borderRadius: 'var(--radius-full)' }}
          >
            <Leaf size={14} style={{ color: vegOnly ? '#fff' : '#10b981' }} />
            <span>Pure Veg Only</span>
          </button>
        </div>

        {/* Categories Bar */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
          <button
            onClick={() => setSelectedCategory('ALL')}
            className={`btn btn-sm ${selectedCategory === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ borderRadius: 'var(--radius-full)' }}
          >
            All Dishes ({items.length})
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`btn btn-sm ${selectedCategory === cat.id ? 'btn-primary' : 'btn-secondary'}`}
              style={{ borderRadius: 'var(--radius-full)' }}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Dishes Grid */}
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading menu catalog...
          </div>
        ) : filteredItems.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No dishes found matching criteria.
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))',
              gap: '16px',
            }}
          >
            {filteredItems.map((dish) => (
              <div
                key={dish.id}
                className="glass-panel"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 'var(--radius-md)',
                  overflow: 'hidden',
                  transition: 'all 0.2s ease',
                  cursor: 'pointer',
                }}
                onClick={() => addToCart(dish)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-3px)';
                  e.currentTarget.style.borderColor = 'var(--border-active)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                }}
              >
                {/* Image */}
                <div style={{ height: '120px', background: '#1e293b', position: 'relative', overflow: 'hidden' }}>
                  {dish.image_url ? (
                    <img
                      src={dish.image_url}
                      alt={dish.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => (e.target.style.display = 'none')}
                    />
                  ) : (
                    <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                      <Utensils size={32} />
                    </div>
                  )}

                  {/* Veg / Non-Veg Indicator */}
                  <div style={{ position: 'absolute', top: '8px', left: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <div className={`food-symbol ${dish.is_vegetarian ? 'veg' : 'nonveg'}`} style={{ width: '14px', height: '14px', padding: '1px', background: 'rgba(0,0,0,0.8)' }}>
                      {dish.is_vegetarian ? <span style={{ width: '7px', height: '7px' }} /> : <span style={{ borderLeftWidth: '3.5px', borderRightWidth: '3.5px', borderBottomWidth: '7px' }} />}
                    </div>
                  </div>

                  {dish.preparation_time && (
                    <span
                      style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '0.65rem',
                        fontWeight: 600,
                        background: 'rgba(0, 0, 0, 0.7)',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '3px',
                      }}
                    >
                      <Clock size={10} />
                      {dish.preparation_time}m
                    </span>
                  )}
                </div>

                {/* Content */}
                <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', flex: 1, justifyContent: 'space-between' }}>
                  <div>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 700, lineHeight: 1.2 }}>{dish.name}</h3>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {dish.description}
                    </p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '12px' }}>
                    <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit' }}>
                      ₹{parseFloat(dish.price || 0).toFixed(2)}
                    </div>
                    <button
                      className="btn btn-primary btn-sm"
                      style={{ borderRadius: 'var(--radius-full)', width: '28px', height: '28px', padding: 0 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        addToCart(dish);
                      }}
                    >
                      <Plus size={14} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right: Cart & Order Drawer */}
      <div
        className="glass-panel"
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
        }}
      >
        {/* Cart Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShoppingCart size={18} style={{ color: 'var(--primary)' }} />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Order Cart</h2>
          </div>
          <span className="badge badge-primary">{cart.length} items</span>
        </div>

        {/* Order Details (Type, Table, Customer) */}
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Order Type Selector */}
          <div style={{ display: 'flex', gap: '6px' }}>
            {['DINE_IN', 'TAKEAWAY', 'DELIVERY'].map((type) => (
              <button
                key={type}
                onClick={() => setOrderType(type)}
                className={`btn btn-sm ${orderType === type ? 'btn-primary' : 'btn-secondary'}`}
                style={{ flex: 1, fontSize: '0.75rem', padding: '6px' }}
              >
                {type.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Table Selector for Dine-In */}
          {orderType === 'DINE_IN' && (
            <select
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              className="select"
              style={{ height: '36px', fontSize: '0.8rem' }}
            >
              <option value="">-- Choose Dining Table --</option>
              {tables.map((t) => (
                <option key={t.id} value={t.id}>
                  Table {t.table_number} ({t.capacity} Seats) - {t.status}
                </option>
              ))}
            </select>
          )}

          {/* Customer Inputs */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <input
              type="text"
              placeholder="Guest Name"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              className="input"
              style={{ height: '34px', fontSize: '0.8rem', padding: '6px 10px' }}
            />
            <input
              type="text"
              placeholder="Phone (optional)"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              className="input"
              style={{ height: '34px', fontSize: '0.8rem', padding: '6px 10px' }}
            />
          </div>
        </div>

        {/* Cart Item List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '14px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {cart.length === 0 ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '10px' }}>
              <ShoppingCart size={36} style={{ opacity: 0.3 }} />
              <p style={{ fontSize: '0.85rem' }}>No dishes selected yet.</p>
              <span style={{ fontSize: '0.75rem' }}>Click any dish from the catalog to add.</span>
            </div>
          ) : (
            cart.map((c) => (
              <div
                key={c.item.id}
                style={{
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{c.item.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      ₹{parseFloat(c.item.price).toFixed(2)} &times; {c.quantity}
                    </div>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                    ₹{(parseFloat(c.item.price) * c.quantity).toFixed(2)}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px' }}>
                  {/* Quantity Stepper */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <button
                      onClick={() => updateQuantity(c.item.id, -1)}
                      className="btn btn-secondary btn-sm"
                      style={{ width: '24px', height: '24px', padding: 0 }}
                    >
                      <Minus size={12} />
                    </button>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, width: '20px', textAlign: 'center' }}>
                      {c.quantity}
                    </span>
                    <button
                      onClick={() => updateQuantity(c.item.id, 1)}
                      className="btn btn-secondary btn-sm"
                      style={{ width: '24px', height: '24px', padding: 0 }}
                    >
                      <Plus size={12} />
                    </button>
                  </div>

                  <input
                    type="text"
                    placeholder="Instructions (e.g. less oil)"
                    value={c.specialInstructions}
                    onChange={(e) => updateInstructions(c.item.id, e.target.value)}
                    className="input"
                    style={{ height: '26px', fontSize: '0.7rem', padding: '2px 8px', width: '150px' }}
                  />
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer Summary & Checkout */}
        {cart.length > 0 && (
          <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-subtle)', background: 'rgba(0, 0, 0, 0.2)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.825rem', marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                <span>Subtotal</span>
                <span>₹{subtotal.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                <span>GST (5%)</span>
                <span>₹{tax.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--warning)' }}>
                <span>Discount (₹)</span>
                <input
                  type="number"
                  min="0"
                  value={discountAmount}
                  onChange={(e) => setDiscountAmount(e.target.value)}
                  className="input"
                  style={{ width: '80px', height: '24px', fontSize: '0.75rem', padding: '2px 6px', textAlign: 'right' }}
                />
              </div>
              <div style={{ height: '1px', background: 'var(--border-subtle)', margin: '4px 0' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                <span>Grand Total</span>
                <span style={{ color: 'var(--primary)' }}>₹{total.toFixed(2)}</span>
              </div>
            </div>

            <button
              onClick={handlePlaceOrder}
              disabled={placingOrder}
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px', fontSize: '0.95rem' }}
            >
              <Send size={16} />
              <span>{placingOrder ? 'Sending to Kitchen...' : 'Confirm & Send to Kitchen'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Order Confirmed Modal */}
      {confirmedOrder && (
        <div className="modal-overlay" onClick={() => setConfirmedOrder(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '420px', padding: '28px', textAlign: 'center' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--success)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <Check size={32} />
            </div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800 }}>Order Confirmed!</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '6px' }}>
              Order #{confirmedOrder.order_number || confirmedOrder.id?.slice(-6)} has been dispatched directly to the Kitchen KDS terminal.
            </p>

            <div style={{ margin: '20px 0', padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', textAlign: 'left', fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Order ID:</span>
                <span style={{ fontWeight: 600 }}>{confirmedOrder.id?.slice(-8)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Customer:</span>
                <span>{confirmedOrder.customer_name || 'Guest'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Total Amount:</span>
                <span style={{ fontWeight: 700, color: 'var(--primary)' }}>₹{parseFloat(confirmedOrder.total_amount || 0).toFixed(2)}</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => setConfirmedOrder(null)} className="btn btn-primary" style={{ flex: 1 }}>
                New Order
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
