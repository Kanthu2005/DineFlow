import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { 
  X, Plus, Minus, Search, CheckCircle2, AlertCircle, 
  ChefHat, Receipt, ArrowRight, ArrowLeft, Clock, ShoppingBag, 
  Sparkles, Utensils, Flame
} from 'lucide-react';

export default function AddMoreItemsModal({ order, isOpen, onClose, onSuccess, onNavigateToBilling }) {
  const { showToast } = useToast();

  // Step state: 'SELECT' | 'CONFIRM' | 'SUCCESS'
  const [step, setStep] = useState('SELECT');

  // Menu data
  const [menuItems, setMenuItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loadingMenu, setLoadingMenu] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState('ALL');
  const [dietFilter, setDietFilter] = useState('ALL'); // 'ALL', 'VEG', 'NON_VEG'

  // Additional items cart: { [menu_item_id]: { item, quantity, special_instructions } }
  const [cart, setCart] = useState({});

  // Submitting
  const [submitting, setSubmitting] = useState(false);
  const [updatedOrderResult, setUpdatedOrderResult] = useState(null);

  // Reset modal state when opening
  useEffect(() => {
    if (isOpen) {
      setStep('SELECT');
      setCart({});
      setUpdatedOrderResult(null);
      loadMenu();
    }
  }, [isOpen, order?.id]);

  const loadMenu = async () => {
    setLoadingMenu(true);
    try {
      const [itemsRes, catsRes] = await Promise.all([
        api.menu.getItems(),
        api.menu.getCategories().catch(() => []),
      ]);
      setMenuItems(Array.isArray(itemsRes) ? itemsRes.filter(i => i.is_available !== false) : []);
      setCategories(Array.isArray(catsRes) ? catsRes : []);
    } catch (err) {
      console.error('Failed to load menu items:', err);
      showToast('Could not load menu items', 'error');
    } finally {
      setLoadingMenu(false);
    }
  };

  if (!isOpen || !order) return null;

  // Existing order items
  const existingItems = order.items || [];
  const currentSubtotal = parseFloat(order.subtotal || 0);

  // Cart operations
  const updateCartQty = (item, delta) => {
    setCart(prev => {
      const cur = prev[item.id] || { item, quantity: 0, special_instructions: '' };
      const newQty = cur.quantity + delta;
      if (newQty <= 0) {
        const next = { ...prev };
        delete next[item.id];
        return next;
      }
      return {
        ...prev,
        [item.id]: { ...cur, quantity: newQty },
      };
    });
  };

  const updateCartInstructions = (itemId, instructions) => {
    setCart(prev => {
      if (!prev[itemId]) return prev;
      return {
        ...prev,
        [itemId]: { ...prev[itemId], special_instructions: instructions },
      };
    });
  };

  // Cart calculations
  const cartEntries = Object.values(cart);
  const totalCartCount = cartEntries.reduce((sum, c) => sum + c.quantity, 0);
  const additionalSubtotal = cartEntries.reduce((sum, c) => {
    const price = parseFloat(c.item.price || 0);
    return sum + (price * c.quantity);
  }, 0);

  // Recalculated financial breakdown
  const newSubtotal = currentSubtotal + additionalSubtotal;
  const currentDiscount = parseFloat(order.discount_amount || 0);
  const effectiveDiscount = Math.min(newSubtotal, currentDiscount);
  const taxable = Math.max(0, newSubtotal - effectiveDiscount);
  const estimatedTax = parseFloat((taxable * 0.05).toFixed(2));
  const newTotalPayable = parseFloat((taxable + estimatedTax).toFixed(2));

  // Filtered menu list
  const filteredMenuItems = menuItems.filter(item => {
    const matchesCat = selectedCat === 'ALL' || item.category_id === selectedCat || item.category === selectedCat;
    const matchesSearch = !search || item.name.toLowerCase().includes(search.toLowerCase()) || 
                          (item.description && item.description.toLowerCase().includes(search.toLowerCase()));
    const isVeg = item.is_veg === true || item.dietary_tag === 'VEG';
    const matchesDiet = dietFilter === 'ALL' || 
                        (dietFilter === 'VEG' && isVeg) || 
                        (dietFilter === 'NON_VEG' && !isVeg);
    return matchesCat && matchesSearch && matchesDiet;
  });

  // Handle final submission to backend
  const handleConfirmAddition = async () => {
    if (cartEntries.length === 0) {
      showToast('Please select at least one item to add', 'warning');
      return;
    }

    setSubmitting(true);
    try {
      const itemsPayload = cartEntries.map(c => ({
        menu_item_id: c.item.id || c.item._id,
        quantity: c.quantity,
        special_instructions: c.special_instructions || '',
      }));

      const res = await api.orders.addAdditionalItems(order.id, itemsPayload);
      setUpdatedOrderResult(res);
      setStep('SUCCESS');
      showToast(`Added ${totalCartCount} items to Order #${order.order_number}!`, 'success');
      if (onSuccess) onSuccess(res);
    } catch (err) {
      console.error('Error adding additional items:', err);
      showToast(err.message || 'Failed to add items to order', 'danger');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: step === 'SELECT' ? '920px' : '760px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          background: 'var(--bg-card)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          border: '1px solid var(--border-subtle)',
          animation: 'fadeIn 0.2s ease',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-secondary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, var(--primary) 0%, #a855f7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
              }}
            >
              <ShoppingBag size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, fontFamily: 'Outfit' }}>
                  Add More Items to Order #{order.order_number || order.id?.slice(-6)}
                </h3>
                <span className={`badge ${order.status === 'DELIVERED' || order.status === 'SERVED' ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.7rem' }}>
                  {order.status}
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                {order.table_number ? `Table ${order.table_number.toString().toUpperCase().startsWith('T') ? order.table_number : `T${order.table_number}`}` : 'Direct Order'}
                {' • '}Guest: <strong>{order.customer_name || 'Walk-in Diner'}</strong>
                {' • '}Items append to the <strong>same order ID</strong> without separate billing.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: '6px', borderRadius: 'var(--radius-full)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* ================= STEP 1: SELECT ITEMS ================= */}
        {step === 'SELECT' && (
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, overflow: 'hidden' }}>
            {/* Filter & Search Bar */}
            <div
              style={{
                padding: '14px 24px',
                background: 'rgba(0, 0, 0, 0.1)',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                flexWrap: 'wrap',
                gap: '12px',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ position: 'relative', width: '280px' }}>
                <Search size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Search dishes to add..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="input"
                  style={{ paddingLeft: '34px', height: '34px', fontSize: '0.8rem' }}
                />
              </div>

              {/* Diet filter */}
              <div style={{ display: 'flex', gap: '6px' }}>
                {['ALL', 'VEG', 'NON_VEG'].map(diet => (
                  <button
                    key={diet}
                    onClick={() => setDietFilter(diet)}
                    className={`btn btn-sm ${dietFilter === diet ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.72rem', padding: '4px 10px' }}
                  >
                    {diet === 'ALL' ? 'All Dishes' : diet === 'VEG' ? '🟢 Veg Only' : '🔴 Non-Veg'}
                  </button>
                ))}
              </div>
            </div>

            {/* Category Pills */}
            {categories.length > 0 && (
              <div
                style={{
                  padding: '10px 24px',
                  display: 'flex',
                  gap: '6px',
                  overflowX: 'auto',
                  borderBottom: '1px solid var(--border-subtle)',
                  background: 'var(--bg-tertiary)',
                }}
              >
                <button
                  onClick={() => setSelectedCat('ALL')}
                  className={`btn btn-sm ${selectedCat === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ borderRadius: 'var(--radius-full)', fontSize: '0.72rem', padding: '3px 10px' }}
                >
                  All Categories
                </button>
                {categories.map(cat => (
                  <button
                    key={cat.id || cat._id}
                    onClick={() => setSelectedCat(cat.id || cat._id)}
                    className={`btn btn-sm ${selectedCat === (cat.id || cat._id) ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ borderRadius: 'var(--radius-full)', fontSize: '0.72rem', padding: '3px 10px' }}
                  >
                    {cat.name}
                  </button>
                ))}
              </div>
            )}

            {/* Menu Grid */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '18px 24px',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                gap: '14px',
              }}
            >
              {loadingMenu ? (
                <div style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Loading delicious menu items...
                </div>
              ) : filteredMenuItems.length === 0 ? (
                <div style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No matching dishes found in the menu.
                </div>
              ) : (
                filteredMenuItems.map(item => {
                  const cartItem = cart[item.id] || { quantity: 0, special_instructions: '' };
                  const isSelected = cartItem.quantity > 0;
                  const itemPrice = parseFloat(item.price || 0);

                  return (
                    <div
                      key={item.id}
                      className="glass-panel"
                      style={{
                        padding: '14px',
                        borderRadius: 'var(--radius-md)',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-subtle)',
                        background: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-secondary)',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{item.name}</span>
                          <span style={{ fontSize: '0.7rem' }}>
                            {item.is_veg !== false ? '🟢' : '🔴'}
                          </span>
                        </div>
                        {item.description && (
                          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', lineClamp: 2, overflow: 'hidden' }}>
                            {item.description}
                          </p>
                        )}
                      </div>

                      <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--primary)', fontFamily: 'Outfit' }}>
                          ₹{itemPrice.toFixed(2)}
                        </span>

                        {isSelected ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <button
                              onClick={() => updateCartQty(item, -1)}
                              className="btn btn-secondary"
                              style={{ width: '28px', height: '28px', padding: 0, borderRadius: '6px' }}
                            >
                              <Minus size={12} />
                            </button>
                            <span style={{ fontWeight: 800, fontSize: '0.9rem', minWidth: '20px', textAlign: 'center' }}>
                              {cartItem.quantity}
                            </span>
                            <button
                              onClick={() => updateCartQty(item, 1)}
                              className="btn btn-primary"
                              style={{ width: '28px', height: '28px', padding: 0, borderRadius: '6px' }}
                            >
                              <Plus size={12} />
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => updateCartQty(item, 1)}
                            className="btn btn-primary btn-sm"
                            style={{ fontSize: '0.75rem', padding: '4px 12px' }}
                          >
                            <Plus size={13} />
                            <span>Add</span>
                          </button>
                        )}
                      </div>

                      {/* Special instructions field if selected */}
                      {isSelected && (
                        <div style={{ marginTop: '8px' }}>
                          <input
                            type="text"
                            placeholder="Special notes (e.g. less spicy)..."
                            value={cartItem.special_instructions}
                            onChange={e => updateCartInstructions(item.id, e.target.value)}
                            className="input"
                            style={{ height: '26px', fontSize: '0.72rem', padding: '2px 8px' }}
                          />
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>

            {/* Bottom Tray with Live Cart Preview */}
            <div
              style={{
                padding: '16px 24px',
                background: 'var(--bg-secondary)',
                borderTop: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '14px',
              }}
            >
              <div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Existing Delivered Bill: <strong>₹{currentSubtotal.toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit' }}>
                    +₹{additionalSubtotal.toFixed(2)}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    ({totalCartCount} new {totalCartCount === 1 ? 'item' : 'items'} selected)
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={onClose} className="btn btn-secondary">
                  Cancel
                </button>
                <button
                  onClick={() => setStep('CONFIRM')}
                  disabled={totalCartCount === 0}
                  className="btn btn-primary"
                  style={{ gap: '8px' }}
                >
                  <span>Review & Confirm Addition</span>
                  <ArrowRight size={15} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ================= STEP 2: CONFIRMATION SCREEN ================= */}
        {step === 'CONFIRM' && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Notice Banner */}
            <div
              style={{
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                fontSize: '0.85rem',
              }}
            >
              <ChefHat size={22} style={{ color: 'var(--primary)', flexShrink: 0 }} />
              <div>
                <strong>Important Business Rule Adhered:</strong> These additional items will be added to existing{' '}
                <strong>Order #{order.order_number}</strong>. Existing delivered items will remain untouched, and the kitchen will receive a new Round #{order.batch_number ? order.batch_number + 1 : 2} ticket.
              </div>
            </div>

            {/* Side-by-side or stacked item breakdown */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
              {/* Box 1: Previously Delivered Items */}
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={16} style={{ color: 'var(--success)' }} />
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase' }}>
                      Delivered / Completed Items
                    </span>
                  </div>
                  <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                    ROUND 1 &bull; UNMODIFIED
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {existingItems.map((it, idx) => {
                    const name = it.name || it.item_name_snapshot || `Item ${idx + 1}`;
                    const qty = it.quantity || 1;
                    const price = parseFloat(it.price || it.unit_price_snapshot || (it.item_total ? it.item_total / qty : 0));
                    const total = parseFloat(it.item_total || price * qty);
                    return (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '6px 10px',
                          borderRadius: 'var(--radius-sm)',
                          background: 'rgba(0, 0, 0, 0.15)',
                          fontSize: '0.8rem',
                        }}
                      >
                        <div>
                          <span style={{ fontWeight: 600 }}>{name}</span>
                          <span style={{ color: 'var(--text-muted)', marginLeft: '6px' }}>&times; {qty}</span>
                        </div>
                        <span style={{ fontFamily: 'Outfit', fontWeight: 700 }}>₹{total.toFixed(2)}</span>
                      </div>
                    );
                  })}
                </div>

                <div style={{ marginTop: '12px', paddingTop: '8px', borderTop: '1px dashed var(--border-subtle)', display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Previous Subtotal:</span>
                  <span style={{ fontWeight: 800 }}>₹{currentSubtotal.toFixed(2)}</span>
                </div>
              </div>

              {/* Box 2: Newly Adding Items */}
              <div
                style={{
                  background: 'rgba(99, 102, 241, 0.05)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sparkles size={16} style={{ color: 'var(--primary)' }} />
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--primary)' }}>
                      Newly Adding Items
                    </span>
                  </div>
                  <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>
                    PENDING PREP
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {cartEntries.map((c, idx) => {
                    const price = parseFloat(c.item.price || 0);
                    const total = price * c.quantity;
                    return (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '6px 10px',
                          borderRadius: 'var(--radius-sm)',
                          background: 'rgba(99, 102, 241, 0.1)',
                          fontSize: '0.8rem',
                        }}
                      >
                        <div>
                          <span style={{ fontWeight: 600 }}>{c.item.name}</span>
                          <span style={{ color: 'var(--primary)', marginLeft: '6px' }}>&times; {c.quantity}</span>
                          {c.special_instructions && (
                            <div style={{ fontSize: '0.7rem', color: 'var(--warning)' }}>
                              Note: {c.special_instructions}
                            </div>
                          )}
                        </div>
                        <span style={{ fontFamily: 'Outfit', fontWeight: 700, color: 'var(--primary)' }}>
                          +₹{total.toFixed(2)}
                        </span>
                      </div>
                    );
                  })}
                </div>

                <div style={{ marginTop: '12px', paddingTop: '8px', borderTop: '1px dashed rgba(99, 102, 241, 0.3)', display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Additional Subtotal:</span>
                  <span style={{ fontWeight: 800, color: 'var(--primary)' }}>+₹{additionalSubtotal.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Recalculated Bill Table */}
            <div
              style={{
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <h4 style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '12px', color: 'var(--text-muted)' }}>
                Updated Bill Summary Recalculation
              </h4>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                  <span>Previous Items Subtotal:</span>
                  <span>₹{currentSubtotal.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--primary)', fontWeight: 600 }}>
                  <span>Newly Added Items Subtotal:</span>
                  <span>+₹{additionalSubtotal.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, borderTop: '1px solid var(--border-subtle)', paddingTop: '6px', marginTop: '4px' }}>
                  <span>New Order Subtotal:</span>
                  <span>₹{newSubtotal.toFixed(2)}</span>
                </div>
                {effectiveDiscount > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--success)' }}>
                    <span>Discounts Applied:</span>
                    <span>-₹{effectiveDiscount.toFixed(2)}</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                  <span>GST (5%):</span>
                  <span>₹{estimatedTax.toFixed(2)}</span>
                </div>

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '8px',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(99, 102, 241, 0.1)',
                    border: '1px solid rgba(99, 102, 241, 0.25)',
                  }}
                >
                  <span style={{ fontSize: '0.95rem', fontWeight: 800 }}>UPDATED FINAL PAYABLE AMOUNT:</span>
                  <span style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit' }}>
                    ₹{newTotalPayable.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px' }}>
              <button
                onClick={() => setStep('SELECT')}
                disabled={submitting}
                className="btn btn-secondary"
                style={{ gap: '6px' }}
              >
                <ArrowLeft size={15} />
                <span>Back to Menu</span>
              </button>

              <button
                onClick={handleConfirmAddition}
                disabled={submitting}
                className="btn btn-primary"
                style={{ padding: '10px 24px', fontSize: '0.95rem', gap: '8px' }}
              >
                {submitting ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    <span>Dispatching to Kitchen & Updating Order...</span>
                  </>
                ) : (
                  <>
                    <ChefHat size={16} />
                    <span>Confirm & Send to Kitchen</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 3: SUCCESS & UPDATED SUMMARY ================= */}
        {step === 'SUCCESS' && updatedOrderResult && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', textAlign: 'center' }}>
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                background: 'rgba(16, 185, 129, 0.15)',
                color: 'var(--success)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto',
              }}
            >
              <CheckCircle2 size={32} />
            </div>

            <div>
              <h3 style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'Outfit' }}>
                Order #{updatedOrderResult.order_number || order.order_number} Updated!
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px', maxWidth: '480px', margin: '4px auto 0' }}>
                New items were appended to the existing order ID and dispatched to the Kitchen Display System (KDS).
              </p>
            </div>

            {/* Updated Order Items Display */}
            <div
              style={{
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                border: '1px solid var(--border-subtle)',
                textAlign: 'left',
              }}
            >
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '10px', textTransform: 'uppercase' }}>
                All Dishes in Order #{updatedOrderResult.order_number}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {updatedOrderResult.items?.map((it, idx) => {
                  const isDelivered = it.status === 'DELIVERED' || it.status === 'SERVED';
                  const isNew = it.is_additional || it.batch_number > 1;
                  const name = it.name || it.item_name_snapshot || `Item ${idx + 1}`;
                  const qty = it.quantity || 1;
                  const price = parseFloat(it.price_at_addition || it.unit_price_snapshot || it.price || (it.item_total ? it.item_total / qty : 0));
                  const tot = parseFloat(it.item_total || price * qty);

                  return (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        background: isNew ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-tertiary)',
                        borderLeft: isNew ? '3px solid var(--primary)' : '3px solid var(--success)',
                        fontSize: '0.85rem',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className={`badge ${isDelivered ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.65rem' }}>
                          {it.status || 'PENDING'}
                        </span>
                        {isNew && (
                          <span style={{ fontSize: '0.65rem', background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                            Round {it.batch_number || 2} (Additional)
                          </span>
                        )}
                        <span style={{ fontWeight: 600 }}>{name}</span>
                        <span style={{ color: 'var(--text-muted)' }}>&times; {qty}</span>
                      </div>

                      <span style={{ fontWeight: 700, fontFamily: 'Outfit' }}>
                        ₹{tot.toFixed(2)}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Recalculated Total Pill */}
              <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Previous Total: ₹{parseFloat(updatedOrderResult.previous_item_total || currentSubtotal).toFixed(2)} &bull; Additional: ₹{parseFloat(updatedOrderResult.new_item_total || additionalSubtotal).toFixed(2)}
                </div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit' }}>
                  Total Payable: ₹{parseFloat(updatedOrderResult.total_amount || newTotalPayable).toFixed(2)}
                </div>
              </div>
            </div>

            {/* Closing Buttons */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', marginTop: '10px' }}>
              <button onClick={onClose} className="btn btn-secondary">
                Close & Return
              </button>
              {onNavigateToBilling && (
                <button
                  onClick={() => {
                    onClose();
                    onNavigateToBilling(updatedOrderResult);
                  }}
                  className="btn btn-primary"
                  style={{ gap: '6px' }}
                >
                  <Receipt size={15} />
                  <span>Go to Billing Terminal</span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
