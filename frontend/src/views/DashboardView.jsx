import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { 
  TrendingUp, ShoppingBag, Grid, ChefHat, AlertTriangle, 
  ArrowUpRight, Clock, Plus, RefreshCw, CheckCircle2, ChevronRight, UtensilsCrossed
} from 'lucide-react';

export default function DashboardView({ onNavigate }) {
  const { showToast } = useToast();
  const [stats, setStats] = useState({
    todayRevenue: 0,
    activeOrders: 0,
    occupiedTables: 0,
    totalTables: 0,
    kitchenPending: 0,
    lowStockCount: 0,
  });
  const [recentOrders, setRecentOrders] = useState([]);
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [ordersRes, tablesRes, ticketsRes, ingredientsRes] = await Promise.allSettled([
        api.orders.getAll(),
        api.tables.getAll(),
        api.kitchen.getTickets(),
        api.inventory.getIngredients(),
      ]);

      const orders = ordersRes.status === 'fulfilled' && Array.isArray(ordersRes.value) ? ordersRes.value : [];
      const tablesList = tablesRes.status === 'fulfilled' && Array.isArray(tablesRes.value) ? tablesRes.value : [];
      const tickets = ticketsRes.status === 'fulfilled' && Array.isArray(ticketsRes.value) ? ticketsRes.value : [];
      const ingredients = ingredientsRes.status === 'fulfilled' && Array.isArray(ingredientsRes.value) ? ingredientsRes.value : [];

      // Calculate Revenue from Confirmed/Completed/Served orders
      const revenue = orders.reduce((acc, o) => {
        const amt = parseFloat(o.total_amount || 0);
        return acc + (isNaN(amt) ? 0 : amt);
      }, 0);

      const activeOrdersCount = orders.filter(o => !['COMPLETED', 'CANCELLED'].includes(o.status)).length;
      const occupiedTablesCount = tablesList.filter(t => t.status === 'OCCUPIED').length;
      const pendingTicketsCount = tickets.filter(t => ['PENDING', 'PREPARING'].includes(t.status)).length;
      const lowStock = ingredients.filter(i => (i.current_stock || 0) <= (i.low_stock_threshold || 10)).length;

      setStats({
        todayRevenue: revenue,
        activeOrders: activeOrdersCount,
        occupiedTables: occupiedTablesCount,
        totalTables: tablesList.length || 1,
        kitchenPending: pendingTicketsCount,
        lowStockCount: lowStock,
      });

      setRecentOrders(orders.slice(0, 6));
      setTables(tablesList.slice(0, 8));
    } catch (err) {
      console.error('Dashboard load error:', err);
      showToast('Could not refresh all dashboard statistics', 'warning');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const occupancyRate = Math.round((stats.occupiedTables / (stats.totalTables || 1)) * 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Restaurant Executive Cockpit</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Real-time multi-station dining operations, live kitchen dispatch, and revenue metrics.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={loadDashboardData} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
          <button onClick={() => onNavigate('menu')} className="btn btn-primary">
            <UtensilsCrossed size={16} />
            <span>Manage Menu</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
          gap: '18px',
        }}
      >
        {/* Revenue */}
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>TODAY'S REVENUE</span>
            <div style={{ padding: '6px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--primary)' }}>
              <TrendingUp size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit' }}>
            ₹{stats.todayRevenue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '0.75rem', color: 'var(--success)' }}>
            <ArrowUpRight size={14} />
            <span>Real-time aggregate total</span>
          </div>
        </div>

        {/* Active Orders */}
        <div className="stat-card" onClick={() => onNavigate('orders')} style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>ACTIVE DINING ORDERS</span>
            <div style={{ padding: '6px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent)' }}>
              <ShoppingBag size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit' }}>
            {stats.activeOrders}
          </div>
          <div style={{ marginTop: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Live customer orders in progress &rarr;
          </div>
        </div>

        {/* Table Occupancy */}
        <div className="stat-card" onClick={() => onNavigate('tables')} style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>TABLE OCCUPANCY</span>
            <div style={{ padding: '6px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--success)' }}>
              <Grid size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit' }}>
            {occupancyRate}%
          </div>
          <div style={{ marginTop: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {stats.occupiedTables} of {stats.totalTables} tables occupied
          </div>
        </div>

        {/* Kitchen Tickets Queue */}
        <div className="stat-card" onClick={() => onNavigate('kitchen')} style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>KITCHEN DISPATCH (KDS)</span>
            <div style={{ padding: '6px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--danger)' }}>
              <ChefHat size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit' }}>
            {stats.kitchenPending}
          </div>
          <div style={{ marginTop: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Pending cook preparation tickets &rarr;
          </div>
        </div>

        {/* Low Stock Alerts */}
        <div className="stat-card" onClick={() => onNavigate('inventory')} style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>LOW STOCK ALERTS</span>
            <div style={{ padding: '6px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--warning)' }}>
              <AlertTriangle size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit', color: stats.lowStockCount > 0 ? 'var(--warning)' : 'inherit' }}>
            {stats.lowStockCount}
          </div>
          <div style={{ marginTop: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Raw ingredients below safety margin
          </div>
        </div>
      </div>

      {/* Main Sections Split */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '24px' }}>
        {/* Recent Orders Stream */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={18} style={{ color: 'var(--primary)' }} />
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Live Orders Stream</h2>
            </div>
            <button onClick={() => onNavigate('orders')} className="btn btn-secondary btn-sm">
              View All ({stats.activeOrders})
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {recentOrders.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No active orders recorded today.
              </div>
            ) : (
              recentOrders.map((ord) => (
                <div
                  key={ord.id}
                  onClick={() => onNavigate('orders')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--border-active)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                        #{ord.order_number || ord.id?.slice(-6)}
                      </span>
                      <span className={`badge ${
                        ord.status === 'CONFIRMED' || ord.status === 'READY' ? 'badge-success' :
                        ord.status === 'PREPARING' ? 'badge-warning' :
                        ord.status === 'CANCELLED' ? 'badge-danger' : 'badge-primary'
                      }`}>
                        {ord.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                      Customer: {ord.customer_name || 'Walk-in Guest'} &bull; {ord.order_type || 'DINE_IN'}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                      ₹{parseFloat(ord.total_amount || 0).toFixed(2)}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {ord.items?.length || 0} items
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Floor Plan Snapshot */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Grid size={18} style={{ color: 'var(--success)' }} />
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Floor Seating Snapshot</h2>
            </div>
            <button onClick={() => onNavigate('tables')} className="btn btn-secondary btn-sm">
              Manage Floor
            </button>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(95px, 1fr))',
              gap: '12px',
            }}
          >
            {tables.map((t) => {
              const isOccupied = t.status === 'OCCUPIED';
              const isReserved = t.status === 'RESERVED';
              return (
                <div
                  key={t.id}
                  onClick={() => onNavigate('tables')}
                  style={{
                    padding: '12px 8px',
                    borderRadius: 'var(--radius-md)',
                    background: isOccupied 
                      ? 'rgba(239, 68, 68, 0.12)' 
                      : isReserved 
                      ? 'rgba(245, 158, 11, 0.12)' 
                      : 'rgba(16, 185, 129, 0.12)',
                    border: '1px solid',
                    borderColor: isOccupied 
                      ? 'rgba(239, 68, 68, 0.3)' 
                      : isReserved 
                      ? 'rgba(245, 158, 11, 0.3)' 
                      : 'rgba(16, 185, 129, 0.3)',
                    textAlign: 'center',
                    cursor: 'pointer',
                    transition: 'transform 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.05)')}
                  onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
                >
                  <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'Outfit' }}>
                    {t.table_number?.toString().toUpperCase().startsWith('T') ? t.table_number : `T${t.table_number}`}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {t.capacity} Seats
                  </div>
                  <div
                    style={{
                      fontSize: '0.65rem',
                      fontWeight: 700,
                      marginTop: '6px',
                      color: isOccupied ? 'var(--danger)' : isReserved ? 'var(--warning)' : 'var(--success)',
                    }}
                  >
                    {t.status}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
