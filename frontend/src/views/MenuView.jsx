import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { 
  UtensilsCrossed, Plus, Search, Edit2, Trash2, Check, 
  X, RefreshCw, Clock, Leaf, AlertCircle, Eye, EyeOff,
  ChefHat, Sparkles, Filter, Lock, CheckCircle2, Flame
} from 'lucide-react';

const PRESET_DISH_IMAGES = [
  { label: 'Biryani Special', url: 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600' },
  { label: 'Butter Chicken', url: 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600' },
  { label: 'Paneer Tikka', url: 'https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600' },
  { label: 'Garlic Naan', url: 'https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600' },
  { label: 'South Indian Dosa', url: 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600' },
  { label: 'Gulab Jamun', url: 'https://images.unsplash.com/photo-1605197586548-932f146a782b?w=600' },
];

export default function MenuView() {
  const { role, permissions } = useAuth();
  const { showToast } = useToast();

  const canManageMenu = permissions?.canEditMenu ?? (role === 'ADMIN' || role === 'MANAGER' || role === 'CHEF');

  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState('ALL');
  const [dietFilter, setDietFilter] = useState('ALL'); // ALL, VEG, NON_VEG, IN_STOCK, OUT_OF_STOCK

  // Add/Edit Dish Modal
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [price, setPrice] = useState('');
  const [prepTime, setPrepTime] = useState(15);
  const [isVeg, setIsVeg] = useState(true);
  const [imageUrl, setImageUrl] = useState('');
  const [saving, setSaving] = useState(false);

  // New Category Modal
  const [showCatModal, setShowCatModal] = useState(false);
  const [newCatName, setNewCatName] = useState('');
  const [newCatDesc, setNewCatDesc] = useState('');

  // Delete Confirm Modal
  const [itemToDelete, setItemToDelete] = useState(null);

  // Recipe View Modal
  const [recipeItem, setRecipeItem] = useState(null);
  const [recipeLoading, setRecipeLoading] = useState(false);
  const [recipeIngredients, setRecipeIngredients] = useState([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [itRes, catRes] = await Promise.all([
        api.menu.getItems(),
        api.menu.getCategories(),
      ]);
      setItems(Array.isArray(itRes) ? itRes : []);
      setCategories(Array.isArray(catRes) ? catRes : []);
    } catch (err) {
      console.error('Menu load error:', err);
      showToast('Could not load menu catalog', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openAddModal = () => {
    if (!canManageMenu) {
      showToast('Only Chef, Manager, or Admin can add dishes', 'warning');
      return;
    }
    setEditingItem(null);
    setName('');
    setDescription('');
    setCategoryId(categories[0]?.id || '');
    setPrice('');
    setPrepTime(15);
    setIsVeg(true);
    setImageUrl(PRESET_DISH_IMAGES[0].url);
    setShowModal(true);
  };

  const openEditModal = (item) => {
    if (!canManageMenu) {
      showToast('Only Chef, Manager, or Admin can edit dishes', 'warning');
      return;
    }
    setEditingItem(item);
    setName(item.name || '');
    setDescription(item.description || '');
    setCategoryId(item.category_id || categories[0]?.id || '');
    setPrice(item.price || '');
    setPrepTime(item.preparation_time || 15);
    setIsVeg(!!item.is_vegetarian);
    setImageUrl(item.image_url || PRESET_DISH_IMAGES[0].url);
    setShowModal(true);
  };

  const handleSaveItem = async (e) => {
    e.preventDefault();
    if (!name || !price || !categoryId) {
      showToast('Please fill all required dish fields', 'warning');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name: name.trim(),
        description: description.trim(),
        category_id: categoryId,
        price: parseFloat(price) || 0,
        preparation_time: parseInt(prepTime) || 15,
        is_vegetarian: isVeg,
        image_url: imageUrl.trim() || 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600',
        is_available: true,
      };

      if (editingItem) {
        await api.menu.updateItem(editingItem.id, payload);
        setItems(prev => prev.map(it => it.id === editingItem.id ? { ...it, ...payload } : it));
        showToast(`Dish "${name}" updated successfully!`, 'success');
      } else {
        const created = await api.menu.createItem(payload);
        setItems(prev => [created, ...prev]);
        showToast(`Dish "${name}" added to menu!`, 'success');
      }
      setShowModal(false);
    } catch (err) {
      showToast(err.message || 'Failed to save menu item', 'danger');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleAvailability = async (item) => {
    const nextVal = !item.is_available;
    try {
      await api.menu.updateItem(item.id, { is_available: nextVal });
      setItems(prev => prev.map(it => it.id === item.id ? { ...it, is_available: nextVal } : it));
      showToast(`${item.name} marked as ${nextVal ? 'Available in Kitchen' : 'Sold Out'}`, 'info');
    } catch (err) {
      showToast('Failed to update kitchen stock availability', 'danger');
    }
  };

  const confirmDeleteItem = async () => {
    if (!itemToDelete) return;
    try {
      await api.menu.deleteItem(itemToDelete.id);
      setItems(prev => prev.filter(it => it.id !== itemToDelete.id));
      showToast(`Removed "${itemToDelete.name}" from catalog`, 'success');
      setItemToDelete(null);
    } catch (err) {
      showToast(err.message || 'Failed to delete dish', 'danger');
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    if (!newCatName) return;
    try {
      const res = await api.menu.createCategory({ 
        name: newCatName.trim(), 
        description: newCatDesc.trim() || undefined 
      });
      setCategories(prev => [...prev, res]);
      showToast(`Category "${newCatName}" created!`, 'success');
      setShowCatModal(false);
      setNewCatName('');
      setNewCatDesc('');
    } catch (err) {
      showToast(err.message || 'Failed to create category', 'danger');
    }
  };

  const openRecipeModal = async (item) => {
    setRecipeItem(item);
    setRecipeLoading(true);
    setRecipeIngredients([]);
    try {
      const res = await api.recipes.getByMenuItem(item.id);
      setRecipeIngredients(Array.isArray(res) ? res : []);
    } catch {
      // Fallback display if no backend recipe is linked yet
      setRecipeIngredients([]);
    } finally {
      setRecipeLoading(false);
    }
  };

  // Filter items
  const filteredItems = items.filter(it => {
    const matchesCat = selectedCat === 'ALL' || it.category_id === selectedCat;
    const matchesSearch = 
      it.name.toLowerCase().includes(search.toLowerCase()) ||
      (it.description && it.description.toLowerCase().includes(search.toLowerCase()));
    
    let matchesDiet = true;
    if (dietFilter === 'VEG') matchesDiet = !!it.is_vegetarian;
    else if (dietFilter === 'NON_VEG') matchesDiet = !it.is_vegetarian;
    else if (dietFilter === 'IN_STOCK') matchesDiet = !!it.is_available;
    else if (dietFilter === 'OUT_OF_STOCK') matchesDiet = !it.is_available;

    return matchesCat && matchesSearch && matchesDiet;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'Outfit' }}>Menu & Culinary Catalog</h1>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: 'var(--radius-full)',
                background: 'rgba(99, 102, 241, 0.15)',
                color: '#818cf8',
                border: '1px solid rgba(99, 102, 241, 0.3)',
              }}
            >
              {items.length} Dishes
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            Authentic Indian dietary categorization, live kitchen availability status, recipes, and price control.
          </p>
        </div>

        {/* Actions based on role */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {canManageMenu ? (
            <>
              <button onClick={() => setShowCatModal(true)} className="btn btn-secondary">
                <Plus size={15} />
                <span>Add Category</span>
              </button>
              <button onClick={openAddModal} className="btn btn-primary">
                <Plus size={16} />
                <span>Add New Dish</span>
              </button>
            </>
          ) : (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.78rem',
                color: 'var(--text-muted)',
              }}
            >
              <Lock size={14} style={{ color: 'var(--warning)' }} />
              <span>{role} Station (View & Stock Toggle Only)</span>
            </div>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Categories Bar */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
          <button
            onClick={() => setSelectedCat('ALL')}
            className={`btn btn-sm ${selectedCat === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap' }}
          >
            All Categories ({items.length})
          </button>
          {categories.map(c => {
            const count = items.filter(it => it.category_id === c.id).length;
            return (
              <button
                key={c.id}
                onClick={() => setSelectedCat(c.id)}
                className={`btn btn-sm ${selectedCat === c.id ? 'btn-primary' : 'btn-secondary'}`}
                style={{ borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap' }}
              >
                {c.name} ({count})
              </button>
            );
          })}
        </div>

        {/* Second Row: Dietary Filter Pills + Search Input */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', justifyContent: 'space-between' }}>
          {/* Dietary Filter Buttons */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setDietFilter('ALL')}
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'ALL' ? 'var(--primary)' : 'var(--border-subtle)',
                background: dietFilter === 'ALL' ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                color: dietFilter === 'ALL' ? '#818cf8' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              All Types
            </button>
            <button
              onClick={() => setDietFilter('VEG')}
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'VEG' ? '#10b981' : 'var(--border-subtle)',
                background: dietFilter === 'VEG' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
                color: dietFilter === 'VEG' ? '#10b981' : 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span className="food-symbol veg" style={{ width: '12px', height: '12px', padding: '1px' }}>
                <span style={{ width: '6px', height: '6px' }} />
              </span>
              Pure Veg
            </button>
            <button
              onClick={() => setDietFilter('NON_VEG')}
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'NON_VEG' ? '#ef4444' : 'var(--border-subtle)',
                background: dietFilter === 'NON_VEG' ? 'rgba(239, 68, 68, 0.2)' : 'transparent',
                color: dietFilter === 'NON_VEG' ? '#ef4444' : 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span className="food-symbol nonveg" style={{ width: '12px', height: '12px', padding: '1px' }}>
                <span style={{ borderLeftWidth: '3px', borderRightWidth: '3px', borderBottomWidth: '6px' }} />
              </span>
              Non-Veg
            </button>
            <button
              onClick={() => setDietFilter('IN_STOCK')}
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'IN_STOCK' ? 'var(--success)' : 'var(--border-subtle)',
                background: dietFilter === 'IN_STOCK' ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
                color: dietFilter === 'IN_STOCK' ? 'var(--success)' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              Available In Stock
            </button>
            <button
              onClick={() => setDietFilter('OUT_OF_STOCK')}
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'OUT_OF_STOCK' ? 'var(--danger)' : 'var(--border-subtle)',
                background: dietFilter === 'OUT_OF_STOCK' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
                color: dietFilter === 'OUT_OF_STOCK' ? 'var(--danger)' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              Sold Out
            </button>
          </div>

          {/* Search Box */}
          <div style={{ position: 'relative', width: '280px' }}>
            <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search cuisine, ingredients..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input"
              style={{ paddingLeft: '34px', height: '36px', fontSize: '0.825rem', borderRadius: 'var(--radius-full)' }}
            />
          </div>
        </div>
      </div>

      {/* Dishes Cards Grid */}
      {loading ? (
        <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 12px' }} />
          Loading restaurant menu catalog...
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <UtensilsCrossed size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>No dishes found</h3>
          <p style={{ fontSize: '0.85rem', marginTop: '6px' }}>
            Try adjusting your search query, category, or dietary filter.
          </p>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '20px',
          }}
        >
          {filteredItems.map(item => {
            const isAvailable = item.is_available !== false;
            const categoryObj = categories.find(c => c.id === item.category_id);

            return (
              <div
                key={item.id}
                className="glass-panel"
                style={{
                  borderRadius: 'var(--radius-lg)',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                  opacity: isAvailable ? 1 : 0.65,
                  transition: 'all 0.25s ease',
                  border: isAvailable ? '1px solid var(--border-subtle)' : '1px dashed rgba(239, 68, 68, 0.4)',
                }}
              >
                {/* Dish Image Banner */}
                <div style={{ height: '160px', background: '#0f172a', position: 'relative', overflow: 'hidden' }}>
                  <img
                    src={item.image_url || 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600'}
                    alt={item.name}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', transition: 'transform 0.3s ease' }}
                    onError={e => {
                      e.target.onerror = null;
                      e.target.src = 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600';
                    }}
                  />

                  {/* Gradient shadow overlay */}
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background: 'linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.1) 40%, rgba(15,23,42,0.95) 100%)',
                    }}
                  />

                  {/* Top Left: Authentic Indian Veg / Non-Veg Indicator Badge */}
                  <div style={{ position: 'absolute', top: '10px', left: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div
                      className={`food-symbol ${item.is_vegetarian ? 'veg' : 'nonveg'}`}
                      style={{ background: 'rgba(0, 0, 0, 0.75)', boxShadow: '0 2px 6px rgba(0,0,0,0.5)' }}
                    >
                      {item.is_vegetarian ? <span /> : <span />}
                    </div>
                    <span
                      style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-full)',
                        background: 'rgba(0, 0, 0, 0.75)',
                        backdropFilter: 'blur(8px)',
                        color: item.is_vegetarian ? '#10b981' : '#ef4444',
                        border: `1px solid ${item.is_vegetarian ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                      }}
                    >
                      {item.is_vegetarian ? 'VEGETARIAN' : 'NON-VEGETARIAN'}
                    </span>
                  </div>

                  {/* Top Right: Stock Status Toggle Button */}
                  <button
                    onClick={() => handleToggleAvailability(item)}
                    title={isAvailable ? 'Mark as Sold Out' : 'Mark as In Stock'}
                    style={{
                      position: 'absolute',
                      top: '10px',
                      right: '10px',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      background: isAvailable ? 'rgba(16, 185, 129, 0.9)' : 'rgba(239, 68, 68, 0.9)',
                      color: '#ffffff',
                      border: 'none',
                      cursor: 'pointer',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    {isAvailable ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                    <span>{isAvailable ? 'AVAILABLE' : 'SOLD OUT'}</span>
                  </button>

                  {/* Bottom Over Image: Prep Time */}
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '8px',
                      left: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '0.72rem',
                      color: '#e2e8f0',
                      background: 'rgba(0,0,0,0.6)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    <Clock size={12} style={{ color: 'var(--accent)' }} />
                    <span>{item.preparation_time || 15} mins prep</span>
                  </div>
                </div>

                {/* Dish Information */}
                <div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 700, lineHeight: 1.3 }}>{item.name}</h3>
                      {categoryObj && (
                        <span
                          style={{
                            fontSize: '0.65rem',
                            fontWeight: 600,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: 'var(--bg-tertiary)',
                            color: 'var(--text-muted)',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {categoryObj.name}
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '6px', lineHeight: 1.4 }}>
                      {item.description || 'Crafted with premium aromatic spices and authentic recipe.'}
                    </p>
                  </div>

                  {/* Bottom Row: Price & Actions */}
                  <div style={{ marginTop: '16px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>PRICE</span>
                        <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit', letterSpacing: '-0.02em' }}>
                          ₹{parseFloat(item.price || 0).toFixed(2)}
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '6px' }}>
                        {/* Recipe Ingredients Button */}
                        <button
                          onClick={() => openRecipeModal(item)}
                          className="btn btn-secondary btn-sm"
                          title="View Recipe Ingredients"
                          style={{ padding: '7px 10px', fontSize: '0.75rem', gap: '4px' }}
                        >
                          <ChefHat size={14} style={{ color: '#f59e0b' }} />
                          <span>Recipe</span>
                        </button>

                        {/* Edit & Delete (Admin/Manager/Chef) */}
                        {canManageMenu && (
                          <>
                            <button
                              onClick={() => openEditModal(item)}
                              className="btn btn-secondary btn-sm"
                              title="Edit Dish"
                              style={{ padding: '7px' }}
                            >
                              <Edit2 size={13} />
                            </button>
                            <button
                              onClick={() => setItemToDelete(item)}
                              className="btn btn-danger btn-sm"
                              title="Delete Dish"
                              style={{ padding: '7px' }}
                            >
                              <Trash2 size={13} />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Recipe / Ingredients Modal */}
      {recipeItem && (
        <div className="modal-overlay" onClick={() => setRecipeItem(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '28px', maxWidth: '520px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
                  <ChefHat size={20} />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Recipe & Ingredients</h2>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{recipeItem.name}</div>
                </div>
              </div>
              <button onClick={() => setRecipeItem(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            {recipeLoading ? (
              <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Loading recipe mapping...
              </div>
            ) : recipeIngredients.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '18px' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  MAPPED INVENTORY INGREDIENTS
                </div>
                {recipeIngredients.map((r, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.85rem',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>{r.ingredient_name || r.name || `Ingredient #${i+1}`}</span>
                    <span style={{ color: 'var(--accent)', fontWeight: 700 }}>
                      {r.quantity_required || r.quantity || 1} {r.unit || 'units'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', marginBottom: '18px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>Standard Culinary Preparation</div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Kitchen prep time: <strong>{recipeItem.preparation_time || 15} minutes</strong>. Requires standard restaurant inventory provisions.
                </p>
              </div>
            )}

            <button onClick={() => setRecipeItem(null)} className="btn btn-secondary" style={{ width: '100%' }}>
              Close Recipe View
            </button>
          </div>
        </div>
      )}

      {/* Add / Edit Dish Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '28px', maxWidth: '580px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', background: 'var(--primary-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <UtensilsCrossed size={18} />
                </div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                  {editingItem ? 'Edit Dish Details' : 'Add Dish to Menu Catalog'}
                </h2>
              </div>
              <button onClick={() => setShowModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveItem} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Dish Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Royal Shahi Paneer"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Category *</label>
                  <select required value={categoryId} onChange={e => setCategoryId(e.target.value)} className="select">
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="280.00"
                    value={price}
                    onChange={e => setPrice(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Kitchen Prep Time (mins)</label>
                  <input
                    type="number"
                    value={prepTime}
                    onChange={e => setPrepTime(e.target.value)}
                    className="input"
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Dietary Classification</label>
                  <div
                    onClick={() => setIsVeg(!isVeg)}
                    style={{
                      height: '42px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '0 12px',
                      borderRadius: 'var(--radius-md)',
                      background: isVeg ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      border: `1px solid ${isVeg ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                      cursor: 'pointer',
                    }}
                  >
                    <div className={`food-symbol ${isVeg ? 'veg' : 'nonveg'}`} style={{ width: '14px', height: '14px', padding: '1px' }}>
                      {isVeg ? <span style={{ width: '7px', height: '7px' }} /> : <span style={{ borderLeftWidth: '3.5px', borderRightWidth: '3.5px', borderBottomWidth: '7px' }} />}
                    </div>
                    <span style={{ fontSize: '0.825rem', fontWeight: 700, color: isVeg ? 'var(--success)' : 'var(--danger)' }}>
                      {isVeg ? 'Pure Vegetarian' : 'Non-Vegetarian'}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Dish Image URL</label>
                <input
                  type="url"
                  placeholder="https://images.unsplash.com/..."
                  value={imageUrl}
                  onChange={e => setImageUrl(e.target.value)}
                  className="input"
                />
                <div style={{ display: 'flex', gap: '6px', marginTop: '6px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Quick Presets:</span>
                  {PRESET_DISH_IMAGES.slice(0, 4).map(p => (
                    <button
                      key={p.label}
                      type="button"
                      onClick={() => setImageUrl(p.url)}
                      style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        padding: '2px 6px',
                        fontSize: '0.65rem',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                      }}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Description / Recipe Highlights</label>
                <textarea
                  rows="2"
                  placeholder="Fresh cottage cheese simmered in a rich tomato, butter, and cashew gravy..."
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  className="textarea"
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" disabled={saving} className="btn btn-primary" style={{ flex: 1 }}>
                  {saving ? 'Saving...' : editingItem ? 'Save Changes' : 'Add Dish'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Category Modal */}
      {showCatModal && (
        <div className="modal-overlay" onClick={() => setShowCatModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '24px', maxWidth: '420px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Add Menu Category</h2>
              <button onClick={() => setShowCatModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateCategory} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Category Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Clay Oven Tandoori"
                  value={newCatName}
                  onChange={e => setNewCatName(e.target.value)}
                  className="input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Description</label>
                <textarea
                  rows="2"
                  placeholder="Charcoal grilled delicacies with authentic marinades..."
                  value={newCatDesc}
                  onChange={e => setNewCatDesc(e.target.value)}
                  className="textarea"
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowCatModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Create Category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Custom Delete Confirmation Modal */}
      {itemToDelete && (
        <div className="modal-overlay" onClick={() => setItemToDelete(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '28px', maxWidth: '420px', textAlign: 'center' }}>
            <div style={{ width: '54px', height: '54px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--danger)', margin: '0 auto 16px' }}>
              <Trash2 size={24} />
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Remove from Menu?</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px', lineHeight: 1.4 }}>
              Are you sure you want to delete <strong>"{itemToDelete.name}"</strong>? This will permanently remove it from customer ordering and KDS.
            </p>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button onClick={() => setItemToDelete(null)} className="btn btn-secondary" style={{ flex: 1 }}>
                Cancel
              </button>
              <button onClick={confirmDeleteItem} className="btn btn-danger" style={{ flex: 1 }}>
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
