import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { 
  Boxes, Plus, AlertTriangle, RefreshCw, ArrowUp, ArrowDown, 
  Search, Check, X, History, Scale
} from 'lucide-react';

export default function InventoryView() {
  const { showToast } = useToast();
  const [ingredients, setIngredients] = useState([]);
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [selectedIngredient, setSelectedIngredient] = useState(null);

  // New Ingredient Form
  const [name, setName] = useState('');
  const [unit, setUnit] = useState('KG');
  const [currentStock, setCurrentStock] = useState(10);
  const [threshold, setThreshold] = useState(5);
  const [costPerUnit, setCostPerUnit] = useState(50);

  // Adjustment Form
  const [adjustQty, setAdjustQty] = useState(5);
  const [adjustType, setAdjustType] = useState('IN'); // IN, OUT, LOSS, AUDIT
  const [adjustReason, setAdjustReason] = useState('Weekly shipment delivery');

  const loadData = async () => {
    setLoading(true);
    try {
      const [ingRes, movRes] = await Promise.all([
        api.inventory.getIngredients(),
        api.inventory.getMovements().catch(() => []),
      ]);
      setIngredients(Array.isArray(ingRes) ? ingRes : []);
      setMovements(Array.isArray(movRes) ? movRes : []);
    } catch (err) {
      console.error('Inventory error:', err);
      showToast('Could not load inventory stock', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateIngredient = async (e) => {
    e.preventDefault();
    if (!name) return;
    try {
      const res = await api.inventory.createIngredient({
        name,
        unit,
        current_stock: parseFloat(currentStock) || 0,
        low_stock_threshold: parseFloat(threshold) || 5,
        cost_per_unit: parseFloat(costPerUnit) || 0,
        is_active: true,
      });
      showToast(`Ingredient "${name}" registered!`, 'success');
      setIngredients(prev => [...prev, res]);
      setShowAddModal(false);
      setName('');
    } catch (err) {
      showToast(err.message || 'Failed to create ingredient', 'danger');
    }
  };

  const handleStockAdjustment = async (e) => {
    e.preventDefault();
    if (!selectedIngredient) return;

    try {
      const qtyDelta = adjustType === 'IN' ? Math.abs(adjustQty) : -Math.abs(adjustQty);
      const newStock = Math.max(0, (selectedIngredient.current_stock || 0) + qtyDelta);

      // Record movement
      await api.inventory.createMovement({
        ingredient_id: selectedIngredient.id,
        quantity: Math.abs(adjustQty),
        movement_type: adjustType,
        reason: adjustReason,
      });

      // Update current stock
      await api.inventory.updateStock(selectedIngredient.id, newStock);

      setIngredients(prev => prev.map(i => i.id === selectedIngredient.id ? { ...i, current_stock: newStock } : i));
      showToast(`Stock updated for ${selectedIngredient.name}!`, 'success');
      setShowAdjustModal(false);
    } catch (err) {
      showToast(err.message || 'Failed to adjust stock', 'danger');
    }
  };

  const lowStockItems = ingredients.filter(i => (i.current_stock || 0) <= (i.low_stock_threshold || 5));
  const filteredIngredients = ingredients.filter(i => i.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>Raw Inventory & Stock Warehouse</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Track ingredient weights, units, automated menu deduction, and restock shipments.
          </p>
        </div>

        <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
          <Plus size={16} />
          <span>Add Raw Material</span>
        </button>
      </div>

      {/* Low Stock Warning Banner */}
      {lowStockItems.length > 0 && (
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius-lg)',
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <AlertTriangle size={24} style={{ color: 'var(--warning)' }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--warning)' }}>
                {lowStockItems.length} Ingredients Below Safety Stock Level
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {lowStockItems.map(i => i.name).slice(0, 5).join(', ')}
                {lowStockItems.length > 5 ? ` and ${lowStockItems.length - 5} more` : ''}
              </div>
            </div>
          </div>
          <button
            onClick={() => {
              if (lowStockItems[0]) {
                setSelectedIngredient(lowStockItems[0]);
                setShowAdjustModal(true);
              }
            }}
            className="btn btn-sm btn-primary"
          >
            Quick Restock
          </button>
        </div>
      )}

      {/* Search Bar */}
      <div className="glass-panel" style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ position: 'relative', width: '320px' }}>
          <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search raw ingredients..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input"
            style={{ paddingLeft: '32px', height: '34px', fontSize: '0.825rem' }}
          />
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Total Materials: {ingredients.length}
        </span>
      </div>

      {/* Grid of Ingredients */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading warehouse stock...
        </div>
      ) : filteredIngredients.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No ingredients found matching criteria.
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '16px',
          }}
        >
          {filteredIngredients.map(item => {
            const isLow = (item.current_stock || 0) <= (item.low_stock_threshold || 5);
            const stockPct = Math.min(100, Math.round(((item.current_stock || 0) / ((item.low_stock_threshold || 5) * 3)) * 100));

            return (
              <div
                key={item.id}
                className="glass-panel"
                style={{
                  padding: '18px',
                  borderRadius: 'var(--radius-lg)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  borderTop: isLow ? '3px solid var(--warning)' : '3px solid var(--success)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>{item.name}</h3>
                  <span className={`badge ${isLow ? 'badge-warning' : 'badge-success'}`}>
                    {isLow ? 'LOW STOCK' : 'IN STOCK'}
                  </span>
                </div>

                {/* Stock Level Bar */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Current Level:</span>
                    <strong style={{ fontSize: '1rem', color: isLow ? 'var(--warning)' : 'var(--text-primary)' }}>
                      {item.current_stock} {item.unit || 'KG'}
                    </strong>
                  </div>

                  <div style={{ width: '100%', height: '6px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${stockPct}%`,
                        height: '100%',
                        background: isLow ? 'var(--warning)' : 'var(--success)',
                        transition: 'width 0.3s ease',
                      }}
                    />
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Alert Threshold: {item.low_stock_threshold || 5} {item.unit || 'KG'}
                  </div>
                </div>

                {/* Footer Controls */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    ₹{item.cost_per_unit || 0}/{item.unit || 'unit'}
                  </span>

                  <button
                    onClick={() => {
                      setSelectedIngredient(item);
                      setShowAdjustModal(true);
                    }}
                    className="btn btn-secondary btn-sm"
                  >
                    Adjust Stock
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Adjust Stock Modal */}
      {showAdjustModal && selectedIngredient && (
        <div className="modal-overlay" onClick={() => setShowAdjustModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '24px', maxWidth: '440px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Adjust Stock: {selectedIngredient.name}</h2>
              <button onClick={() => setShowAdjustModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleStockAdjustment} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ padding: '10px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', fontSize: '0.85rem' }}>
                Current Quantity: <strong>{selectedIngredient.current_stock} {selectedIngredient.unit}</strong>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Adjustment Type</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
                  {[
                    { id: 'IN', label: '+ Restock (In)' },
                    { id: 'OUT', label: '- Used (Out)' },
                    { id: 'LOSS', label: '- Spoilage/Loss' },
                  ].map(t => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setAdjustType(t.id)}
                      className={`btn btn-sm ${adjustType === t.id ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ fontSize: '0.75rem', padding: '6px 4px' }}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                  Quantity ({selectedIngredient.unit}) *
                </label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={adjustQty}
                  onChange={e => setAdjustQty(e.target.value)}
                  className="input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Reason / Note</label>
                <input
                  type="text"
                  value={adjustReason}
                  onChange={e => setAdjustReason(e.target.value)}
                  className="input"
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowAdjustModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Confirm Adjustment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add New Material Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '24px', maxWidth: '440px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Register Raw Material</h2>
              <button onClick={() => setShowAddModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateIngredient} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Material Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Basmati Rice"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Unit</label>
                  <select value={unit} onChange={e => setUnit(e.target.value)} className="select">
                    <option value="KG">Kilogram (kg)</option>
                    <option value="G">Gram (g)</option>
                    <option value="L">Liter (L)</option>
                    <option value="ML">Milliliter (mL)</option>
                    <option value="PIECES">Pieces / Units</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Initial Stock</label>
                  <input
                    type="number"
                    step="0.1"
                    value={currentStock}
                    onChange={e => setCurrentStock(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Low Stock Alert</label>
                  <input
                    type="number"
                    step="0.1"
                    value={threshold}
                    onChange={e => setThreshold(e.target.value)}
                    className="input"
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Cost / Unit (₹)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={costPerUnit}
                    onChange={e => setCostPerUnit(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Register Material
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
