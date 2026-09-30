import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { 
  Boxes, Plus, AlertTriangle, RefreshCw, ArrowUp, ArrowDown, 
  Search, Check, X, History, Scale, Package, Trash2, Edit3, 
  TrendingDown, CheckCircle2, XCircle, ArrowUpRight, ArrowDownRight,
  Filter
} from 'lucide-react';

export default function InventoryView() {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState('WAREHOUSE'); // 'WAREHOUSE' | 'MOVEMENTS'
  const [ingredients, setIngredients] = useState([]);
  const [movements, setMovements] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [movementFilter, setMovementFilter] = useState('ALL');

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [selectedIngredient, setSelectedIngredient] = useState(null);
  const [itemToDelete, setItemToDelete] = useState(null);

  // New Ingredient Form
  const [name, setName] = useState('');
  const [unit, setUnit] = useState('KG');
  const [currentStock, setCurrentStock] = useState(10);
  const [threshold, setThreshold] = useState(5);
  const [costPerUnit, setCostPerUnit] = useState(50);

  // Adjustment Form
  const [adjustQty, setAdjustQty] = useState(5);
  const [adjustType, setAdjustType] = useState('PURCHASE'); // PURCHASE, MANUAL_ADD, WASTAGE, ADJUSTMENT, RETURN
  const [adjustReason, setAdjustReason] = useState('Restock shipment delivery');

  const loadData = async () => {
    setLoading(true);
    try {
      const [dashRes, ingRes, movRes] = await Promise.all([
        api.inventory.getDashboard().catch(() => null),
        api.inventory.getIngredients(),
        api.inventory.getMovements(100).catch(() => []),
      ]);
      setDashboard(dashRes);
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
        name: name.trim(),
        unit: unit.toUpperCase(),
        current_stock: parseFloat(currentStock) || 0,
        low_stock_threshold: parseFloat(threshold) || 5,
        cost_per_unit: parseFloat(costPerUnit) || 0,
        is_active: true,
      });
      showToast(`Raw material "${name}" registered successfully!`, 'success');
      setShowAddModal(false);
      setName('');
      setCurrentStock(10);
      setThreshold(5);
      await loadData();
    } catch (err) {
      showToast(err.message || 'Failed to create raw material', 'danger');
    }
  };

  const handleStockAdjustment = async (e) => {
    e.preventDefault();
    if (!selectedIngredient) return;

    try {
      const isPositive = ['PURCHASE', 'MANUAL_ADD', 'RETURN', 'ORDER_RETURN'].includes(adjustType);
      const qty = parseFloat(adjustQty) || 0;
      const current = parseFloat(selectedIngredient.current_stock) || 0;
      const newStock = isPositive ? current + qty : Math.max(0, current - qty);

      // Record movement audit log
      await api.inventory.createMovement({
        ingredient_id: selectedIngredient.id,
        quantity: qty,
        unit: selectedIngredient.unit,
        movement_type: adjustType,
        reference_type: 'MANUAL',
        reason: adjustReason,
      });

      // Update current stock
      await api.inventory.updateStock(selectedIngredient.id, newStock);

      showToast(`Stock updated for ${selectedIngredient.name}: ${newStock} ${selectedIngredient.unit}`, 'success');
      setShowAdjustModal(false);
      setSelectedIngredient(null);
      await loadData();
    } catch (err) {
      showToast(err.message || 'Failed to adjust stock', 'danger');
    }
  };

  const handleDeleteIngredient = async () => {
    if (!itemToDelete) return;
    try {
      await api.inventory.deleteIngredient(itemToDelete.id);
      showToast(`Ingredient "${itemToDelete.name}" removed`, 'success');
      setItemToDelete(null);
      await loadData();
    } catch (err) {
      showToast(err.message || 'Failed to delete ingredient', 'danger');
    }
  };

  // Dashboard calculation helpers
  const totalItems = dashboard?.total_ingredients ?? ingredients.length;
  const lowStockCount = dashboard?.low_stock_items ?? ingredients.filter(i => (i.current_stock || 0) <= (i.low_stock_threshold || 5) && (i.current_stock || 0) > 0).length;
  const outOfStockCount = dashboard?.out_of_stock_items ?? ingredients.filter(i => (i.current_stock || 0) <= 0).length;
  const todayConsumption = dashboard?.today_consumption ?? 0;
  const lowStockItems = ingredients.filter(i => (i.current_stock || 0) <= (i.low_stock_threshold || 5));
  const filteredIngredients = ingredients.filter(i => i.name.toLowerCase().includes(search.toLowerCase()));

  const filteredMovements = movements.filter(m => {
    if (movementFilter === 'ALL') return true;
    return m.movement_type === movementFilter;
  });

  const getMovementBadge = (type) => {
    switch (type) {
      case 'PURCHASE':
      case 'MANUAL_ADD':
        return { label: `+ ${type}`, bg: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: 'rgba(16, 185, 129, 0.3)' };
      case 'ORDER_DEDUCTION':
        return { label: '- RECIPE DEDUCTION', bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', border: 'rgba(239, 68, 68, 0.3)' };
      case 'ORDER_RETURN':
      case 'RETURN':
        return { label: '+ ORDER RETURN', bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', border: 'rgba(59, 130, 246, 0.3)' };
      case 'WASTAGE':
        return { label: '- WASTAGE / LOSS', bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.3)' };
      default:
        return { label: type || 'ADJUSTMENT', bg: 'rgba(168, 85, 247, 0.15)', color: '#a855f7', border: 'rgba(168, 85, 247, 0.3)' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'Outfit' }}>Central Raw Inventory</h1>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '3px 10px',
                borderRadius: 'var(--radius-full)',
                background: 'rgba(16, 185, 129, 0.15)',
                color: '#10b981',
                border: '1px solid rgba(16, 185, 129, 0.3)',
              }}
            >
              Recipe-Synchronized
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            Real-time ingredient stocks, automatic recipe deduction on order completion, and transaction audit trails.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button onClick={loadData} className="btn btn-secondary" title="Refresh Inventory">
            <RefreshCw size={15} />
            <span>Sync</span>
          </button>
          <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
            <Plus size={16} />
            <span>Add Raw Material</span>
          </button>
        </div>
      </div>

      {/* 5 Dashboard KPI Metrics (Requirement 17) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: '14px',
        }}
      >
        {/* Card 1: Total Ingredients */}
        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Boxes size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>TOTAL INGREDIENTS</div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, fontFamily: 'Outfit', color: 'var(--text-primary)', marginTop: '2px' }}>
              {totalItems} <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)' }}>items</span>
            </div>
          </div>
        </div>

        {/* Card 2: Low Stock Items */}
        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', gap: '14px', borderLeft: lowStockCount > 0 ? '3px solid #f59e0b' : 'none' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <AlertTriangle size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>LOW STOCK ALERTS</div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, fontFamily: 'Outfit', color: lowStockCount > 0 ? '#f59e0b' : 'var(--text-primary)', marginTop: '2px' }}>
              {lowStockCount} <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)' }}>critical</span>
            </div>
          </div>
        </div>

        {/* Card 3: Out of Stock Items */}
        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', gap: '14px', borderLeft: outOfStockCount > 0 ? '3px solid #ef4444' : 'none' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <XCircle size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>OUT OF STOCK</div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, fontFamily: 'Outfit', color: outOfStockCount > 0 ? '#ef4444' : 'var(--text-primary)', marginTop: '2px' }}>
              {outOfStockCount} <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)' }}>items</span>
            </div>
          </div>
        </div>

        {/* Card 4: Today's Consumption */}
        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Scale size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>TODAY'S CONSUMPTION</div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, fontFamily: 'Outfit', color: 'var(--text-primary)', marginTop: '2px' }}>
              {todayConsumption} <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)' }}>kg / units</span>
            </div>
          </div>
        </div>

        {/* Card 5: Recent Movements */}
        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <History size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>STOCK MOVEMENTS</div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, fontFamily: 'Outfit', color: 'var(--text-primary)', marginTop: '2px' }}>
              {movements.length} <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)' }}>audited</span>
            </div>
          </div>
        </div>
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
                ⚠ Low Stock Warning: {lowStockItems.length} Ingredients Below Safety Level
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {lowStockItems.map(i => `${i.name} (${i.current_stock} ${i.unit})`).slice(0, 4).join(', ')}
                {lowStockItems.length > 4 ? ` and ${lowStockItems.length - 4} more` : ''}
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

      {/* Tabs: Warehouse Materials vs Stock Movement Audit Trail */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '4px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setActiveTab('WAREHOUSE')}
            className={`btn btn-sm ${activeTab === 'WAREHOUSE' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ gap: '6px' }}
          >
            <Boxes size={15} />
            <span>Warehouse Materials ({ingredients.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('MOVEMENTS')}
            className={`btn btn-sm ${activeTab === 'MOVEMENTS' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ gap: '6px' }}
          >
            <History size={15} />
            <span>Stock Movement Audit Log ({movements.length})</span>
          </button>
        </div>

        {activeTab === 'WAREHOUSE' ? (
          <div style={{ position: 'relative', width: '280px' }}>
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
        ) : (
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Type:</span>
            <select
              value={movementFilter}
              onChange={e => setMovementFilter(e.target.value)}
              className="select"
              style={{ height: '32px', fontSize: '0.78rem', padding: '0 8px' }}
            >
              <option value="ALL">All Movements</option>
              <option value="PURCHASE">Purchase / Restock</option>
              <option value="ORDER_DEDUCTION">Recipe Deduction</option>
              <option value="ORDER_RETURN">Order Return</option>
              <option value="WASTAGE">Wastage / Loss</option>
              <option value="ADJUSTMENT">Adjustment</option>
            </select>
          </div>
        )}
      </div>

      {/* TAB 1: WAREHOUSE MATERIALS */}
      {activeTab === 'WAREHOUSE' && (
        <>
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
                gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))',
                gap: '16px',
              }}
            >
              {filteredIngredients.map(item => {
                const stock = parseFloat(item.current_stock) || 0;
                const thresholdVal = parseFloat(item.low_stock_threshold) || 5;
                const isOut = stock <= 0;
                const isLow = !isOut && stock <= thresholdVal;
                const stockPct = Math.min(100, Math.round((stock / (thresholdVal * 3 || 15)) * 100));

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
                      borderTop: isOut 
                        ? '3px solid var(--danger)' 
                        : isLow 
                        ? '3px solid var(--warning)' 
                        : '3px solid var(--success)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>{item.name}</h3>
                      <span className={`badge ${isOut ? 'badge-danger' : isLow ? 'badge-warning' : 'badge-success'}`}>
                        {isOut ? 'OUT OF STOCK' : isLow ? 'LOW STOCK' : 'IN STOCK'}
                      </span>
                    </div>

                    {/* Stock Level Bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Current Stock:</span>
                        <strong style={{ fontSize: '1.1rem', color: isOut ? 'var(--danger)' : isLow ? 'var(--warning)' : 'var(--text-primary)', fontFamily: 'Outfit' }}>
                          {item.current_stock} {item.unit || 'KG'}
                        </strong>
                      </div>

                      <div style={{ width: '100%', height: '7px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${stockPct}%`,
                            height: '100%',
                            background: isOut ? 'var(--danger)' : isLow ? 'var(--warning)' : 'var(--success)',
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        <span>Alert Threshold: {item.low_stock_threshold || 5} {item.unit}</span>
                        <span>₹{item.cost_per_unit || 0}/{item.unit || 'unit'}</span>
                      </div>
                    </div>

                    {/* Footer Controls */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                      <button
                        onClick={() => setItemToDelete(item)}
                        className="btn btn-secondary btn-sm"
                        title="Delete ingredient"
                        style={{ padding: '6px 8px', color: 'var(--text-muted)' }}
                      >
                        <Trash2 size={13} />
                      </button>

                      <button
                        onClick={() => {
                          setSelectedIngredient(item);
                          setShowAdjustModal(true);
                        }}
                        className="btn btn-secondary btn-sm"
                        style={{ gap: '6px', fontWeight: 600 }}
                      >
                        <Scale size={14} style={{ color: 'var(--primary)' }} />
                        <span>Adjust / Restock</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* TAB 2: STOCK MOVEMENT AUDIT TRAIL (Section 9 Requirement) */}
      {activeTab === 'MOVEMENTS' && (
        <div className="glass-panel" style={{ borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Stock Movement History & Audit Trail</h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Permanent ledger recording automatic recipe deductions, restocks, returns, and adjustments.
              </p>
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Showing {filteredMovements.length} records
            </span>
          </div>

          {filteredMovements.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No stock movements recorded yet.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.83rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-tertiary)', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '12px 18px', fontWeight: 600 }}>Date & Time</th>
                    <th style={{ padding: '12px 18px', fontWeight: 600 }}>Movement Type</th>
                    <th style={{ padding: '12px 18px', fontWeight: 600 }}>Raw Material</th>
                    <th style={{ padding: '12px 18px', fontWeight: 600 }}>Quantity</th>
                    <th style={{ padding: '12px 18px', fontWeight: 600 }}>Reference</th>
                    <th style={{ padding: '12px 18px', fontWeight: 600 }}>Reason / Note</th>
                    <th style={{ padding: '12px 18px', fontWeight: 600 }}>Logged By</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMovements.map((m, idx) => {
                    const badge = getMovementBadge(m.movement_type);
                    const isDeduction = m.movement_type === 'ORDER_DEDUCTION' || m.movement_type === 'WASTAGE';
                    const dateStr = m.created_at ? new Date(m.created_at).toLocaleString('en-IN', {
                      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                    }) : 'Just now';

                    return (
                      <tr 
                        key={m.id || idx}
                        style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background 0.15s ease' }}
                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                      >
                        <td style={{ padding: '12px 18px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                          {dateStr}
                        </td>
                        <td style={{ padding: '12px 18px', whiteSpace: 'nowrap' }}>
                          <span
                            style={{
                              fontSize: '0.68rem',
                              fontWeight: 700,
                              padding: '3px 8px',
                              borderRadius: '4px',
                              background: badge.bg,
                              color: badge.color,
                              border: `1px solid ${badge.border}`,
                              letterSpacing: '0.02em',
                            }}
                          >
                            {badge.label}
                          </span>
                        </td>
                        <td style={{ padding: '12px 18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {m.ingredient_name || 'Ingredient'}
                        </td>
                        <td style={{ padding: '12px 18px', fontWeight: 700, color: isDeduction ? 'var(--danger)' : 'var(--success)' }}>
                          {isDeduction ? '-' : '+'}{m.quantity} {m.unit || 'KG'}
                        </td>
                        <td style={{ padding: '12px 18px', color: 'var(--text-muted)' }}>
                          {m.reference_type ? `${m.reference_type}: ` : ''}
                          <strong>{m.reference_id ? `#${String(m.reference_id).slice(-6)}` : 'System'}</strong>
                        </td>
                        <td style={{ padding: '12px 18px', color: 'var(--text-secondary)', maxWidth: '220px' }}>
                          {m.reason || 'Automated stock management'}
                        </td>
                        <td style={{ padding: '12px 18px', color: 'var(--text-muted)' }}>
                          {m.created_by || 'Auto/System'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Adjust Stock Modal */}
      {showAdjustModal && selectedIngredient && (
        <div className="modal-overlay" onClick={() => setShowAdjustModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '26px', maxWidth: '460px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Stock Adjustment / Restock</h2>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{selectedIngredient.name}</div>
              </div>
              <button onClick={() => setShowAdjustModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleStockAdjustment} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ padding: '12px 16px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Current Warehouse Stock:</span>
                <strong style={{ fontSize: '1.15rem', color: 'var(--text-primary)', fontFamily: 'Outfit' }}>
                  {selectedIngredient.current_stock} {selectedIngredient.unit}
                </strong>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Adjustment Reason & Movement Type</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
                  {[
                    { id: 'PURCHASE', label: '+ Restock / Purchase' },
                    { id: 'MANUAL_ADD', label: '+ Manual Addition' },
                    { id: 'RETURN', label: '+ Return from Order' },
                    { id: 'WASTAGE', label: '- Spoilage / Wastage' },
                    { id: 'ADJUSTMENT', label: '± Inventory Audit' },
                  ].map(t => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setAdjustType(t.id)}
                      className={`btn btn-sm ${adjustType === t.id ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ fontSize: '0.74rem', padding: '8px 6px', justifyContent: 'center' }}
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
                  step="0.01"
                  required
                  min="0.01"
                  value={adjustQty}
                  onChange={e => setAdjustQty(e.target.value)}
                  className="input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Audit Note / Reason</label>
                <input
                  type="text"
                  placeholder="e.g. Shipment received from vendor #204"
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
                  Confirm Movement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add New Raw Material Modal (Supports kg, gram, litre, ml, piece, packet) */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '26px', maxWidth: '480px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'var(--primary-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <Package size={20} />
                </div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Register Raw Material</h2>
              </div>
              <button onClick={() => setShowAddModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateIngredient} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Material / Ingredient Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Basmati Rice, Chicken, Paneer, Oil"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Standard Base Unit *</label>
                  <select value={unit} onChange={e => setUnit(e.target.value)} className="select">
                    <option value="KG">Kilogram (kg)</option>
                    <option value="GRAM">Gram (g)</option>
                    <option value="LITRE">Litre (L)</option>
                    <option value="ML">Millilitre (ml)</option>
                    <option value="PIECE">Piece / Unit</option>
                    <option value="PACKET">Packet (pkt)</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Initial Stock Level</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={currentStock}
                    onChange={e => setCurrentStock(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Low Stock Alert Level</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={threshold}
                    onChange={e => setThreshold(e.target.value)}
                    className="input"
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Cost Per Unit (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={costPerUnit}
                    onChange={e => setCostPerUnit(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
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

      {/* Delete Ingredient Confirmation Modal */}
      {itemToDelete && (
        <div className="modal-overlay" onClick={() => setItemToDelete(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '26px', maxWidth: '420px', textAlign: 'center' }}>
            <div style={{ width: '52px', height: '52px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--danger)', margin: '0 auto 16px' }}>
              <Trash2 size={24} />
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Delete Ingredient?</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px', lineHeight: 1.4 }}>
              Are you sure you want to remove <strong>"{itemToDelete.name}"</strong>? If recipes link to this ingredient, availability calculations may be affected.
            </p>

            <div style={{ display: 'flex', gap: '12px', marginTop: '22px' }}>
              <button onClick={() => setItemToDelete(null)} className="btn btn-secondary" style={{ flex: 1 }}>
                Cancel
              </button>
              <button onClick={handleDeleteIngredient} className="btn btn-danger" style={{ flex: 1 }}>
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
