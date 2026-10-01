import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { 
  BarChart3, TrendingUp, DollarSign, ChefHat, Boxes, 
  ArrowUpRight, RefreshCw, Award
} from 'lucide-react';

export default function ReportsView() {
  const { showToast } = useToast();
  const [dailySales, setDailySales] = useState(null);
  const [workload, setWorkload] = useState(null);
  const [orders, setOrders] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadReports = async () => {
    setLoading(true);
    try {
      const [salesRes, ordersRes, itemsRes] = await Promise.all([
        api.reports.getDailySales().catch(() => null),
        api.orders.getAll().catch(() => []),
        api.menu.getItems().catch(() => []),
      ]);
      setDailySales(salesRes);
      setOrders(Array.isArray(ordersRes) ? ordersRes : []);
      setItems(Array.isArray(itemsRes) ? itemsRes : []);
    } catch (err) {
      console.error('Reports load error:', err);
      showToast('Could not load analytics metrics', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  // Compute top selling dishes
  const itemCounts = {};
  orders.forEach(o => {
    if (o.items && Array.isArray(o.items)) {
      o.items.forEach(it => {
        const name = it.menu_item_name || it.name || 'Dish';
        itemCounts[name] = (itemCounts[name] || 0) + (it.quantity || 1);
      });
    }
  });

  const topDishes = Object.entries(itemCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6);

  const totalRevenue = orders.reduce((sum, o) => sum + (parseFloat(o.total_amount) || 0), 0);
  const avgOrderValue = orders.length > 0 ? (totalRevenue / orders.length).toFixed(2) : '0.00';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>Restaurant Analytics & Reports</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Daily revenue performance, popular dishes, and kitchen efficiency indicators.
          </p>
        </div>

        <button onClick={loadReports} className="btn btn-secondary btn-sm">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Analytics</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '18px' }}>
        <div className="stat-card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>CUMULATIVE REVENUE</div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit', marginTop: '6px' }}>
            ₹{totalRevenue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--success)', marginTop: '4px' }}>
            Across {orders.length} total customer orders
          </div>
        </div>

        <div className="stat-card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>AVERAGE TICKET SIZE</div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit', marginTop: '6px', color: 'var(--primary)' }}>
            ₹{avgOrderValue}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Spend per customer visit
          </div>
        </div>

        <div className="stat-card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>MENU DISHES</div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit', marginTop: '6px' }}>
            {items.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Active menu dishes
          </div>
        </div>
      </div>

      {/* Top Dishes Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Award size={18} style={{ color: 'var(--accent)' }} />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Top Selling Dishes</h2>
          </div>

          {topDishes.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No order data yet to calculate top dishes.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {topDishes.map(([name, count], idx) => {
                const maxCount = topDishes[0][1] || 1;
                const pct = Math.round((count / maxCount) * 100);

                return (
                  <div key={idx} style={{ padding: '10px 14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600 }}>
                        #{idx + 1} {name}
                      </span>
                      <strong style={{ color: 'var(--primary)' }}>{count} ordered</strong>
                    </div>

                    <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', background: 'var(--primary-gradient)' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Operating Performance Summary */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <BarChart3 size={18} style={{ color: 'var(--primary)' }} />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Order Fulfillment Breakdown</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {['CONFIRMED', 'PREPARING', 'READY', 'SERVED', 'COMPLETED', 'CANCELLED'].map(st => {
              const count = orders.filter(o => o.status === st).length;
              return (
                <div key={st} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{st}</span>
                  <span className={`badge ${
                    st === 'COMPLETED' || st === 'READY' ? 'badge-success' :
                    st === 'PREPARING' ? 'badge-warning' :
                    st === 'CANCELLED' ? 'badge-danger' : 'badge-primary'
                  }`}>
                    {count} orders
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
