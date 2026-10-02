import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { 
  Search, ShoppingCart, Plus, Minus, Trash2, Clock, Check, 
  Send, Sparkles, Filter, Leaf, Utensils, AlertTriangle, XCircle, Info,
  Edit3, X
} from 'lucide-react';

const PRESET_DISH_IMAGES = [
  { label: 'Biryani Special', url: 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600' },
  { label: 'Butter Chicken', url: 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600' },
  { label: 'Paneer Tikka', url: 'https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600' },
  { label: 'Crispy Starter', url: 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600' },
  { label: 'Indian Curry', url: 'https://images.unsplash.com/photo-1545247181-516773cae754?w=600' },
];

export default function PosView({ onOrderPlaced, onNavigate, initialTableId }) {
  const { role, permissions } = useAuth();
  const canManageMenu = permissions?.canEditMenu ?? (role === 'ADMIN' || role === 'MANAGER' || role === 'CHEF');
  const { showToast } = useToast();
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [items, setItems] = useState([]);
  const [tables, setTables] = useState([]);
  const [availabilityMap, setAvailabilityMap] = useState({});
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedSubcat, setSelectedSubcat] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [dietFilter, setDietFilter] = useState('ALL'); // 'ALL' | 'VEG' | 'NON_VEG'
  const [loading, setLoading] = useState(true);

  // Quick Dish Add/Edit in POS
  const [showDishModal, setShowDishModal] = useState(false);
  const [editingDish, setEditingDish] = useState(null);
  const [dishName, setDishName] = useState('');
  const [dishPrice, setDishPrice] = useState('');
  const [dishCategory, setDishCategory] = useState('');
  const [dishIsVeg, setDishIsVeg] = useState(true);
  const [dishDesc, setDishDesc] = useState('');
  const [dishPrepTime, setDishPrepTime] = useState(15);
  const [dishImageUrl, setDishImageUrl] = useState('');
  const [savingDish, setSavingDish] = useState(false);
  const [dishToDelete, setDishToDelete] = useState(null);

  // Cart State
  const [cart, setCart] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [orderType, setOrderType] = useState('DINE_IN');
  const [discountAmount, setDiscountAmount] = useState(0);
  const [placingOrder, setPlacingOrder] = useState(false);
  const [confirmedOrder, setConfirmedOrder] = useState(null);

  // Shortages Modal State
  const [cartShortages, setCartShortages] = useState(null);

  useEffect(() => {
    loadPosData();
  }, []);

  useEffect(() => {
    if (initialTableId) {
      setSelectedTable(initialTableId);
    } else {
      const savedTable = localStorage.getItem('dineflow_pos_selected_table');
      if (savedTable) {
        setSelectedTable(savedTable);
        localStorage.removeItem('dineflow_pos_selected_table');
      }
    }
  }, [initialTableId]);

  useEffect(() => {
    const rawDish = localStorage.getItem('dineflow_pos_add_dish');
    if (rawDish && items.length > 0) {
      try {
        const dish = JSON.parse(rawDish);
        const target = items.find((it) => it.id === dish.id) || dish;
        addToCart(target);
        showToast(`Added "${target.name}" from Menu to cart!`, 'success');
      } catch (e) {
        console.error('Failed to parse dish from menu:', e);
      } finally {
        localStorage.removeItem('dineflow_pos_add_dish');
      }
    }
  }, [items]);

  const loadPosData = async () => {
    setLoading(true);
    try {
      const [catsRes, subcatsRes, itemsRes, tablesRes, availRes] = await Promise.all([
        api.menu.getCategories(),
        api.menu.getSubcategories().catch(() => []),
        api.menu.getItems(),
        api.tables.getAll(),
        api.menu.getAvailability().catch(() => ({})),
      ]);
      setCategories(Array.isArray(catsRes) ? catsRes : []);
      setSubcategories(Array.isArray(subcatsRes) ? subcatsRes : []);
      setItems(Array.isArray(itemsRes) ? itemsRes : []);
      setTables(Array.isArray(tablesRes) ? tablesRes : []);
      setAvailabilityMap(availRes || {});
    } catch (err) {
      console.error('POS data error:', err);
      showToast('Could not load menu or tables', 'error');
    } finally {
      setLoading(false);
    }
  };

  const openAddDishModal = () => {
    if (!canManageMenu) {
      showToast('Only Chef, Manager, or Admin can add dishes', 'warning');
      return;
    }
    setEditingDish(null);
    setDishName('');
    setDishPrice('');
    setDishCategory(categories[0]?.id || '');
    setDishIsVeg(true);
    setDishDesc('');
    setDishPrepTime(15);
    setDishImageUrl(PRESET_DISH_IMAGES[0].url);
    setShowDishModal(true);
  };

  const openEditDishModal = (dish, e) => {
    if (e) e.stopPropagation();
    if (!canManageMenu) {
      showToast('Only Chef, Manager, or Admin can edit dishes', 'warning');
      return;
    }
    setEditingDish(dish);
    setDishName(dish.name || '');
    setDishPrice(dish.price || '');
    setDishCategory(dish.category_id || categories[0]?.id || '');
    setDishIsVeg(!!dish.is_vegetarian);
    setDishDesc(dish.description || '');
    setDishPrepTime(dish.preparation_time || 15);
    setDishImageUrl(dish.image_url || PRESET_DISH_IMAGES[0].url);
    setShowDishModal(true);
  };

  const handleSaveDish = async (e) => {
    e.preventDefault();
    if (!dishName || !dishPrice || !dishCategory) {
      showToast('Please fill all required dish fields (Name, Price, Category)', 'warning');
      return;
    }
    setSavingDish(true);
    try {
      const payload = {
        name: dishName.trim(),
        description: dishDesc.trim(),
        category_id: dishCategory,
        price: parseFloat(dishPrice) || 0,
        preparation_time: parseInt(dishPrepTime) || 15,
        is_vegetarian: dishIsVeg,
        image_url: dishImageUrl.trim() || PRESET_DISH_IMAGES[0].url,
        is_available: true,
      };

      if (editingDish) {
        await api.menu.updateItem(editingDish.id, payload);
        showToast(`Dish "${dishName}" updated successfully!`, 'success');
      } else {
        await api.menu.createItem(payload);
        showToast(`Dish "${dishName}" added to menu!`, 'success');
      }
      setShowDishModal(false);
      await loadPosData();
    } catch (err) {
      showToast(err.message || 'Failed to save dish', 'danger');
    } finally {
      setSavingDish(false);
    }
  };

  const handleDeleteDish = (dish, e) => {
    if (e) e.stopPropagation();
    setDishToDelete(dish);
  };

  const confirmDeleteDish = async () => {
    if (!dishToDelete) return;
    try {
      await api.menu.deleteItem(dishToDelete.id);
      showToast(`Dish "${dishToDelete.name}" removed from menu`, 'success');
      setDishToDelete(null);
      await loadPosData();
    } catch (err) {
      showToast(err.message || 'Failed to delete dish', 'danger');
    }
  };

  // Add Item to Cart with Real-time Recipe Stock Validation
  const addToCart = (item) => {
    const avail = availabilityMap[item.id] || { status: 'AVAILABLE', max_portions: 9999 };

    if (avail.status === 'OUT_OF_STOCK') {
      showToast(`❌ ${item.name} is unavailable: ${avail.message || 'Required ingredients are out of stock'}`, 'danger', 4000);
      return;
    }

    const existing = cart.find((c) => c.item.id === item.id);
    const currentQty = existing ? existing.quantity : 0;
    const nextQty = currentQty + 1;

    if (avail.has_recipe && nextQty > avail.max_portions) {
      showToast(
        `❌ Cannot add ${nextQty} ${item.name}s. Stock supports only ${avail.max_portions} plates.`,
        'warning',
        4000
      );
      return;
    }

    setCart((prev) => {
      if (existing) {
        return prev.map((c) =>
          c.item.id === item.id ? { ...c, quantity: c.quantity + 1 } : c
        );
      }
      return [...prev, { item, quantity: 1, specialInstructions: '' }];
    });
    showToast(`Added ${item.name} to cart`, 'success', 1500);
  };

  // Update Quantity with Stock Limit Check
  const updateQuantity = (itemId, delta) => {
    if (delta > 0) {
      const avail = availabilityMap[itemId] || { status: 'AVAILABLE', max_portions: 9999 };
      const existing = cart.find((c) => c.item.id === itemId);
      const currentQty = existing ? existing.quantity : 0;
      if (avail.has_recipe && currentQty + delta > avail.max_portions) {
        showToast(
          `❌ Cannot increase quantity. Only ${avail.max_portions} plates available for this dish.`,
          'warning',
          3500
        );
        return;
      }
    }

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
    const matchesSubcat =
      selectedSubcat === 'ALL' || 
      String(item.subcategory_id) === String(selectedSubcat) || 
      (item.subcategory_name && item.subcategory_name.toLowerCase() === selectedSubcat.toLowerCase());
    const matchesSearch =
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(searchQuery.toLowerCase()));
    let matchesDiet = true;
    if (dietFilter === 'VEG') matchesDiet = !!item.is_vegetarian;
    else if (dietFilter === 'NON_VEG') matchesDiet = !item.is_vegetarian;
    return matchesCategory && matchesSubcat && matchesSearch && matchesDiet;
  });

  // Financial calculations
  const subtotal = cart.reduce((sum, c) => {
    const p = parseFloat(c.item.price || 0);
    return sum + p * c.quantity;
  }, 0);

  const discount = Math.min(subtotal, Math.max(0, parseFloat(discountAmount) || 0));
  const taxableAmount = Math.max(0, subtotal - discount);
  const tax = taxableAmount * 0.05; // 5% GST on taxable base
  const total = taxableAmount + tax;

  // Place Order with Backend Cart-Level Stock Validation
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
      // 1. Transactional Cart Validation on Backend
      const cartItemsPayload = cart.map((c) => ({
        menu_item_id: c.item.id,
        quantity: c.quantity,
      }));

      const valRes = await api.orders.validateCart(cartItemsPayload);
      if (!valRes.is_valid) {
        setCartShortages(valRes.shortages || []);
        showToast('❌ Order cannot be placed: Insufficient raw material inventory.', 'danger', 5000);
        setPlacingOrder(false);
        return;
      }

      // 2. Create Order
      const orderPayload = {
        customer_name: customerName || 'Walk-in Guest',
        customer_phone: customerPhone || '9876543210',
        table_id: orderType === 'DINE_IN' ? selectedTable : null,
        order_type: orderType,
        discount_amount: discount,
        items: cart.map((c) => ({
          menu_item_id: c.item.id,
          quantity: c.quantity,
          special_instructions: c.specialInstructions || '',
        })),
      };

      const newOrder = await api.orders.create(orderPayload);

      // 3. Confirm Order (Validates stock & queues kitchen ticket, stock deduction happens at SERVED)
      try {
        await api.orders.confirm(newOrder.id);
      } catch (confirmErr) {
        console.warn('Order confirmation warning:', confirmErr);
      }

      // Refresh live stock availability
      api.menu.getAvailability().then((res) => setAvailabilityMap(res || {})).catch(() => {});

      setConfirmedOrder(newOrder);
      setCart([]);
      setCustomerName('');
      setCustomerPhone('');
      setSelectedTable('');
      setDiscountAmount(0);
      showToast(`Order #${newOrder.order_number || newOrder.id} confirmed and dispatched to kitchen!`, 'success');
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

          {/* Dietary Filter Segmented Control: All, Veg, Non-Veg */}
          <div style={{ display: 'flex', gap: '4px', background: 'rgba(255, 255, 255, 0.05)', padding: '3px', borderRadius: 'var(--radius-full)', border: '1px solid var(--border-subtle)' }}>
            <button
              type="button"
              onClick={() => setDietFilter('ALL')}
              className="btn btn-xs"
              style={{
                borderRadius: 'var(--radius-full)',
                padding: '6px 14px',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: dietFilter === 'ALL' ? 'var(--primary)' : 'transparent',
                color: dietFilter === 'ALL' ? '#fff' : 'var(--text-muted)',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              All Types
            </button>
            <button
              type="button"
              onClick={() => setDietFilter('VEG')}
              className="btn btn-xs"
              style={{
                borderRadius: 'var(--radius-full)',
                padding: '6px 14px',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: dietFilter === 'VEG' ? '#10b981' : 'transparent',
                color: dietFilter === 'VEG' ? '#fff' : '#10b981',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
              }}
            >
              <Leaf size={13} />
              <span>Veg</span>
            </button>
            <button
              type="button"
              onClick={() => setDietFilter('NON_VEG')}
              className="btn btn-xs"
              style={{
                borderRadius: 'var(--radius-full)',
                padding: '6px 14px',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: dietFilter === 'NON_VEG' ? '#ef4444' : 'transparent',
                color: dietFilter === 'NON_VEG' ? '#fff' : '#ef4444',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: dietFilter === 'NON_VEG' ? '#fff' : '#ef4444', display: 'inline-block' }} />
              <span>Non-Veg</span>
            </button>
          </div>
        </div>

        {/* Categories Bar & Quick Add */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto' }}>
            <button
              onClick={() => { setSelectedCategory('ALL'); setSelectedSubcat('ALL'); }}
              className={`btn btn-sm ${selectedCategory === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ borderRadius: 'var(--radius-full)' }}
            >
              All Dishes ({items.length})
            </button>
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => { setSelectedCategory(cat.id); setSelectedSubcat('ALL'); }}
                className={`btn btn-sm ${selectedCategory === cat.id ? 'btn-primary' : 'btn-secondary'}`}
                style={{ borderRadius: 'var(--radius-full)' }}
              >
                {cat.name}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {onNavigate && (
              <button
                type="button"
                onClick={() => onNavigate('menu')}
                className="btn btn-sm btn-secondary"
                style={{ borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px' }}
                title="Manage Restaurant Menu"
              >
                <Utensils size={14} />
                <span>Menu</span>
              </button>
            )}
            {canManageMenu && (
              <button
                type="button"
                onClick={openAddDishModal}
                className="btn btn-sm btn-primary"
                style={{ borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px' }}
              >
                <Plus size={14} />
                <span>Add Dish</span>
              </button>
            )}
        </div>

        {/* Subcategories Filter Chips */}
        {subcategories.length > 0 && (
          <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', padding: '2px 0 6px 0', alignItems: 'center' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, marginRight: '4px' }}>
              Subcategory:
            </span>
            <button
              type="button"
              onClick={() => setSelectedSubcat('ALL')}
              style={{
                padding: '3px 10px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.72rem',
                fontWeight: 700,
                border: '1px solid',
                borderColor: selectedSubcat === 'ALL' ? 'var(--primary)' : 'var(--border-subtle)',
                background: selectedSubcat === 'ALL' ? 'rgba(99, 102, 241, 0.25)' : 'var(--bg-tertiary)',
                color: selectedSubcat === 'ALL' ? '#818cf8' : 'var(--text-secondary)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              All
            </button>
            {subcategories
              .filter(s => selectedCategory === 'ALL' || String(s.category_id) === String(selectedCategory))
              .map(sub => {
                const isSelected = selectedSubcat === sub.id || selectedSubcat === sub.name;
                return (
                  <button
                    key={sub.id}
                    type="button"
                    onClick={() => setSelectedSubcat(sub.id)}
                    style={{
                      padding: '3px 10px',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      border: '1px solid',
                      borderColor: isSelected ? 'var(--primary)' : 'var(--border-subtle)',
                      background: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'var(--bg-tertiary)',
                      color: isSelected ? '#818cf8' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {sub.name}
                  </button>
                );
              })}
          </div>
        )}

        {/* Dishes Grid */}
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading menu and stock availability...
          </div>
        ) : filteredItems.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No dishes found matching criteria.
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
              gap: '16px',
            }}
          >
            {filteredItems.map((dish) => {
              const avail = availabilityMap[dish.id] || { status: 'AVAILABLE', max_portions: 9999 };
              const isOutOfStock = avail.status === 'OUT_OF_STOCK';
              const isLowStock = avail.status === 'LOW_STOCK';

              return (
                <div
                  key={dish.id}
                  className="glass-panel"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                    transition: 'all 0.2s ease',
                    cursor: isOutOfStock ? 'not-allowed' : 'pointer',
                    opacity: isOutOfStock ? 0.75 : 1,
                    border: isOutOfStock
                      ? '1px solid rgba(239, 68, 68, 0.4)'
                      : isLowStock
                      ? '1px solid rgba(245, 158, 11, 0.4)'
                      : '1px solid var(--border-subtle)',
                  }}
                  onClick={() => addToCart(dish)}
                  onMouseEnter={(e) => {
                    if (!isOutOfStock) {
                      e.currentTarget.style.transform = 'translateY(-3px)';
                      e.currentTarget.style.borderColor = 'var(--border-active)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isOutOfStock) {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.borderColor = isLowStock ? 'rgba(245, 158, 11, 0.4)' : 'var(--border-subtle)';
                    }
                  }}
                >
                  {/* Image */}
                  <div style={{ height: '120px', background: '#1e293b', position: 'relative', overflow: 'hidden' }}>
                    {dish.image_url ? (
                      <img
                        src={dish.image_url}
                        alt={dish.name}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                          filter: isOutOfStock ? 'grayscale(80%)' : 'none',
                        }}
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

                    {/* Stock Availability Badge (Section 26 & 27) */}
                    <div style={{ position: 'absolute', top: '8px', right: '8px' }}>
                      {isOutOfStock ? (
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            background: 'rgba(239, 68, 68, 0.9)',
                            color: '#fff',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '3px',
                            boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
                          }}
                        >
                          🔴 Out of Stock
                        </span>
                      ) : isLowStock ? (
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            background: 'rgba(245, 158, 11, 0.95)',
                            color: '#000',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '3px',
                            boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
                          }}
                        >
                          🟡 Only {avail.max_portions} left
                        </span>
                      ) : (
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            background: 'rgba(16, 185, 129, 0.85)',
                            color: '#fff',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '3px',
                          }}
                        >
                          🟢 Available
                        </span>
                      )}
                    </div>

                    {/* Prep Time */}
                    {dish.preparation_time && (
                      <span
                        style={{
                          position: 'absolute',
                          bottom: '6px',
                          left: '8px',
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

                      {/* Out of Stock Reason Display (Section 22 & 23) */}
                      {isOutOfStock && (
                        <div style={{ marginTop: '6px', fontSize: '0.7rem', color: '#f87171', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <AlertTriangle size={12} />
                          <span>{avail.limiting_ingredient ? `${avail.limiting_ingredient} is unavailable` : 'Ingredients unavailable'}</span>
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '12px' }}>
                      <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit' }}>
                        ₹{parseFloat(dish.price || 0).toFixed(2)}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {canManageMenu && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <button
                              type="button"
                              title="Edit Dish & Price"
                              onClick={(e) => openEditDishModal(dish, e)}
                              style={{
                                width: '28px',
                                height: '28px',
                                borderRadius: 'var(--radius-full)',
                                background: 'rgba(255, 255, 255, 0.08)',
                                border: '1px solid var(--border-subtle)',
                                color: 'var(--text-secondary)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                              }}
                            >
                              <Edit3 size={13} />
                            </button>
                            <button
                              type="button"
                              title="Delete Dish"
                              onClick={(e) => handleDeleteDish(dish, e)}
                              style={{
                                width: '28px',
                                height: '28px',
                                borderRadius: 'var(--radius-full)',
                                background: 'rgba(239, 68, 68, 0.12)',
                                border: '1px solid rgba(239, 68, 68, 0.25)',
                                color: '#ef4444',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                              }}
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        )}

                        <button
                          className={`btn btn-sm ${isOutOfStock ? 'btn-secondary' : 'btn-primary'}`}
                          style={{
                            borderRadius: isOutOfStock ? '4px' : 'var(--radius-full)',
                            padding: isOutOfStock ? '4px 8px' : '0',
                            width: isOutOfStock ? 'auto' : '28px',
                            height: '28px',
                            fontSize: '0.75rem',
                          }}
                          disabled={isOutOfStock}
                          onClick={(e) => {
                            e.stopPropagation();
                            addToCart(dish);
                          }}
                        >
                          {isOutOfStock ? 'Unavailable' : <Plus size={14} />}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
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
          {cart.length > 0 && (
            <button
              onClick={() => setCart([])}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '0.8rem', cursor: 'pointer' }}
            >
              Clear
            </button>
          )}
        </div>

        {/* Customer & Order Type Settings */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255, 255, 255, 0.02)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', gap: '6px' }}>
            {['DINE_IN', 'TAKEAWAY', 'DELIVERY'].map((t) => (
              <button
                key={t}
                onClick={() => setOrderType(t)}
                className={`btn btn-sm ${orderType === t ? 'btn-primary' : 'btn-secondary'}`}
                style={{ flex: 1, fontSize: '0.75rem', padding: '4px 6px' }}
              >
                {t.replace('_', ' ')}
              </button>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <input
              type="text"
              placeholder="Guest Name"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              className="input"
              style={{ height: '32px', fontSize: '0.8rem' }}
            />
            {orderType === 'DINE_IN' ? (
              <select
                value={selectedTable}
                onChange={(e) => setSelectedTable(e.target.value)}
                className="select"
                style={{ height: '32px', fontSize: '0.8rem' }}
              >
                <option value="">Select Table *</option>
                {tables.map((tbl) => (
                  <option key={tbl.id} value={tbl.id}>
                    {tbl.table_number?.toString().toUpperCase().startsWith('T') ? tbl.table_number : `T${tbl.table_number}`} ({tbl.capacity} Seats)
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="Phone (optional)"
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                className="input"
                style={{ height: '32px', fontSize: '0.8rem' }}
              />
            )}
          </div>
        </div>

        {/* Cart Items List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {cart.length === 0 ? (
            <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
              <ShoppingCart size={32} style={{ margin: '0 auto 8px', opacity: 0.3 }} />
              <p style={{ fontSize: '0.85rem' }}>No items in cart.</p>
              <span style={{ fontSize: '0.75rem' }}>Click on menu dishes to add.</span>
            </div>
          ) : (
            cart.map(({ item, quantity, specialInstructions }) => (
              <div
                key={item.id}
                style={{
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h4 style={{ fontSize: '0.85rem', fontWeight: 600 }}>{item.name}</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      ₹{parseFloat(item.price || 0).toFixed(2)} × {quantity}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    ₹{(parseFloat(item.price || 0) * quantity).toFixed(2)}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px' }}>
                  <input
                    type="text"
                    placeholder="Instructions (less spicy, no onions...)"
                    value={specialInstructions}
                    onChange={(e) => updateInstructions(item.id, e.target.value)}
                    style={{
                      background: 'rgba(0,0,0,0.2)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      padding: '2px 8px',
                      fontSize: '0.7rem',
                      color: 'var(--text-primary)',
                      flex: 1,
                      marginRight: '8px',
                    }}
                  />
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <button
                      onClick={() => updateQuantity(item.id, -1)}
                      style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: '4px',
                        border: '1px solid var(--border-subtle)',
                        background: 'var(--bg-secondary)',
                        color: 'var(--text-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                      }}
                    >
                      <Minus size={12} />
                    </button>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, minWidth: '16px', textAlign: 'center' }}>
                      {quantity}
                    </span>
                    <button
                      onClick={() => updateQuantity(item.id, 1)}
                      style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: '4px',
                        border: '1px solid var(--border-subtle)',
                        background: 'var(--bg-secondary)',
                        color: 'var(--text-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                      }}
                    >
                      <Plus size={12} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Financial Summary & Order Action */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.1)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Food Items Subtotal</span>
              <span>₹{subtotal.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Govt GST (5%)</span>
              <span>₹{tax.toFixed(2)}</span>
            </div>
            {discount > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#10b981' }}>
                <span>Promotional Discount</span>
                <span>-₹{discount.toFixed(2)}</span>
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px', borderTop: '1px dashed var(--border-subtle)', paddingTop: '6px' }}>
              <span>Net Amount Payable</span>
              <span style={{ color: 'var(--primary)', fontFamily: 'Outfit' }}>₹{total.toFixed(2)}</span>
            </div>
          </div>

          <button
            onClick={handlePlaceOrder}
            disabled={placingOrder || cart.length === 0}
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '14px', height: '42px', fontWeight: 700, fontSize: '0.9rem', gap: '8px' }}
          >
            <Send size={16} />
            <span>{placingOrder ? 'Validating Stock...' : 'Confirm & Send to Kitchen'}</span>
          </button>
        </div>
      </div>

      {/* Insufficient Stock Shortage Alert Modal (Section 23, 24, 29, 32) */}
      {cartShortages && (
        <div className="modal-overlay" onClick={() => setCartShortages(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px', padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--danger)', marginBottom: '12px' }}>
              <XCircle size={26} />
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Insufficient Inventory Stock</h2>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: 1.4 }}>
              This order cannot be prepared because one or more recipe raw materials are insufficient in the main inventory:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>
              {cartShortages.map((s, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'rgba(239, 68, 68, 0.08)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    borderRadius: 'var(--radius-md)',
                    padding: '10px 14px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: '#f87171', fontSize: '0.9rem' }}>{s.ingredient_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Required: {s.required} {s.unit} | Available: {s.available} {s.unit}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>SHORTAGE</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#ef4444' }}>
                      {s.shortage} {s.unit}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <button onClick={() => setCartShortages(null)} className="btn btn-secondary" style={{ width: '100%' }}>
              Adjust Cart Quantities
            </button>
          </div>
        </div>
      )}

      {/* Quick Add / Edit Dish Modal in POS (for Manager / Admin / Chef) */}
      {showDishModal && (
        <div className="modal-overlay" onClick={() => setShowDishModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '520px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
                  <Utensils size={18} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                    {editingDish ? 'Edit Dish & Price' : 'Add New Culinary Dish'}
                  </h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Updates live in POS and Menu immediately
                  </span>
                </div>
              </div>
              <button onClick={() => setShowDishModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveDish} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Dish Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chicken Dum Biryani"
                  value={dishName}
                  onChange={(e) => setDishName(e.target.value)}
                  className="input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Category *</label>
                  <select
                    value={dishCategory}
                    onChange={(e) => setDishCategory(e.target.value)}
                    className="select"
                    required
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Price (INR ₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    placeholder="220.00"
                    value={dishPrice}
                    onChange={(e) => setDishPrice(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Dietary Classification</label>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      type="button"
                      onClick={() => setDishIsVeg(true)}
                      className={`btn btn-sm ${dishIsVeg ? 'btn-success' : 'btn-secondary'}`}
                      style={{ flex: 1, fontSize: '0.75rem' }}
                    >
                      <Leaf size={12} />
                      <span>Veg</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setDishIsVeg(false)}
                      className={`btn btn-sm ${!dishIsVeg ? 'btn-danger' : 'btn-secondary'}`}
                      style={{ flex: 1, fontSize: '0.75rem' }}
                    >
                      <span>Non-Veg</span>
                    </button>
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Prep Time (Minutes)</label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={dishPrepTime}
                    onChange={(e) => setDishPrepTime(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Description</label>
                <textarea
                  rows="2"
                  placeholder="Ingredients, preparation style, and flavor profile..."
                  value={dishDesc}
                  onChange={(e) => setDishDesc(e.target.value)}
                  className="input"
                  style={{ resize: 'none' }}
                />
              </div>

              {/* Quick Image Selector */}
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Quick Food Image</label>
                <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
                  {PRESET_DISH_IMAGES.map((img, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setDishImageUrl(img.url)}
                      style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        border: '1px solid',
                        borderColor: dishImageUrl === img.url ? 'var(--primary)' : 'var(--border-subtle)',
                        background: dishImageUrl === img.url ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                        color: dishImageUrl === img.url ? 'var(--primary)' : 'var(--text-muted)',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {img.label}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowDishModal(false)}
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingDish}
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                >
                  {savingDish ? 'Saving Dish...' : editingDish ? 'Update Dish' : 'Create Dish'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Dish Confirmation Modal */}
      {dishToDelete && (
        <div className="modal-overlay" onClick={() => setDishToDelete(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '420px', padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#ef4444', marginBottom: '12px' }}>
              <Trash2 size={24} />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Remove Dish from Menu?</h3>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.4, marginBottom: '20px' }}>
              Are you sure you want to remove <strong>"{dishToDelete.name}"</strong>? It will no longer appear in the POS or Menu.
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => setDishToDelete(null)} className="btn btn-secondary" style={{ flex: 1 }}>
                Cancel
              </button>
              <button onClick={confirmDeleteDish} className="btn btn-danger" style={{ flex: 1 }}>
                Yes, Delete Dish
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
