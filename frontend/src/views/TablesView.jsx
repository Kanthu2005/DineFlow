import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { 
  Grid, Plus, Calendar, User, Clock, Check, RefreshCw,
  Users, CheckCircle2, AlertCircle, X, ShoppingBag, Receipt,
  Sparkles, Coffee, Phone, ChevronRight, Layers, Eye
} from 'lucide-react';

const ZONES = [
  { id: 'ALL', label: 'All Floor Zones' },
  { id: 'MAIN_HALL', label: 'Main Dining Hall' },
  { id: 'TERRACE', label: 'Open Terrace Garden' },
  { id: 'VIP_LOUNGE', label: 'VIP Executive Lounge' },
  { id: 'FAMILY_SECTION', label: 'Family Dining Section' },
];

export default function TablesView({ onNavigateToBilling }) {
  const { role, permissions } = useAuth();
  const { showToast } = useToast();

  const canManageTables = role === 'ADMIN' || role === 'MANAGER';

  const [tables, setTables] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('FLOOR'); // 'FLOOR' or 'RESERVATIONS'
  const [selectedZone, setSelectedZone] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL', 'AVAILABLE', 'OCCUPIED', 'RESERVED'

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showReserveModal, setShowReserveModal] = useState(false);
  const [selectedTableForReserve, setSelectedTableForReserve] = useState(null);

  // New Table Form
  const [tableNumber, setTableNumber] = useState('');
  const [capacity, setCapacity] = useState(4);
  const [zone, setZone] = useState('MAIN_HALL');

  // Reservation Form
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [reserveTableId, setReserveTableId] = useState('');
  const [reserveDate, setReserveDate] = useState(new Date().toISOString().split('T')[0]);
  const [reserveTime, setReserveTime] = useState('19:30');
  const [guestCount, setGuestCount] = useState(2);
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tRes, rRes] = await Promise.all([
        api.tables.getAll(),
        api.reservations.getAll().catch(() => []),
      ]);
      setTables(Array.isArray(tRes) ? tRes : []);
      setReservations(Array.isArray(rRes) ? rRes : []);
    } catch (err) {
      console.error('Tables load error:', err);
      showToast('Could not load tables or reservations', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdateStatus = async (tableId, nextStatus) => {
    try {
      await api.tables.updateStatus(tableId, nextStatus);
      showToast(`Table status set to ${nextStatus}`, 'success');
      setTables(prev => prev.map(t => t.id === tableId ? { ...t, status: nextStatus } : t));
    } catch (err) {
      showToast(err.message || 'Failed to update table status', 'danger');
    }
  };

  const handleCreateTable = async (e) => {
    e.preventDefault();
    if (!canManageTables) {
      showToast('Only Admin or Manager can add new tables', 'warning');
      return;
    }
    if (!tableNumber) {
      showToast('Please enter a table number', 'warning');
      return;
    }
    const numStr = tableNumber.toString().trim();
    const formattedNum = numStr.toUpperCase().startsWith('T')
      ? numStr.toUpperCase()
      : `T${numStr}`;
    setSubmitting(true);
    try {
      await api.tables.create({
        table_number: formattedNum,
        capacity: parseInt(capacity) || 4,
        location: zone,
      });
      showToast(`Table ${formattedNum} configured successfully!`, 'success');
      setShowAddModal(false);
      setTableNumber('');
      await loadData();
    } catch (err) {
      showToast(err.message || 'Failed to create table', 'danger');
    } finally {
      setSubmitting(false);
    }
  };

  const openReserveForTable = (table) => {
    setSelectedTableForReserve(table);
    setReserveTableId(table.id);
    setShowReserveModal(true);
  };

  const handleCreateReservation = async (e) => {
    e.preventDefault();
    if (!customerName || !reserveTableId) {
      showToast('Please fill all required reservation details', 'warning');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.reservations.create({
        customer_name: customerName.trim(),
        customer_phone: customerPhone.trim() || '9876543210',
        table_id: reserveTableId,
        reservation_date: reserveDate,
        start_time: reserveTime,
        party_size: parseInt(guestCount) || 2,
      });
      showToast(`Reservation confirmed for ${customerName}!`, 'success');
      setReservations(prev => [res, ...prev]);
      // Update table status to RESERVED
      setTables(prev => prev.map(t => t.id === reserveTableId ? { ...t, status: 'RESERVED' } : t));
      setShowReserveModal(false);
      setCustomerName('');
      setCustomerPhone('');
      setSelectedTableForReserve(null);
    } catch (err) {
      showToast(err.message || 'Failed to book reservation', 'danger');
    } finally {
      setSubmitting(false);
    }
  };

  // Metrics
  const totalTables = tables.length;
  const availableCount = tables.filter(t => t.status === 'AVAILABLE').length;
  const occupiedCount = tables.filter(t => t.status === 'OCCUPIED').length;
  const reservedCount = tables.filter(t => t.status === 'RESERVED').length;
  const occupancyRate = totalTables > 0 ? Math.round((occupiedCount / totalTables) * 100) : 0;

  // Filtered tables
  const filteredTables = tables.filter(t => {
    const matchesZone = selectedZone === 'ALL' || t.location === selectedZone;
    const matchesStatus = statusFilter === 'ALL' || t.status === statusFilter;
    return matchesZone && matchesStatus;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'Outfit' }}>Tables & Dining Floor Plan</h1>
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
              {totalTables} Tables
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            Live floor layout, seat capacity, dining occupancy, and reservation schedule.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => setShowReserveModal(true)} className="btn btn-secondary">
            <Calendar size={16} />
            <span>Book Reservation</span>
          </button>
          {canManageTables && (
            <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
              <Plus size={16} />
              <span>Add New Table</span>
            </button>
          )}
        </div>
      </div>

      {/* Floor Statistics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: 'var(--radius-md)', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#818cf8' }}>
            <Grid size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>TOTAL CAPACITY</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'Outfit' }}>{totalTables} Tables</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#10b981' }}>
            <CheckCircle2 size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>AVAILABLE SEATS</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#10b981', fontFamily: 'Outfit' }}>{availableCount} Tables</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: 'var(--radius-md)', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
            <Users size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>CURRENTLY DINING</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ef4444', fontFamily: 'Outfit' }}>{occupiedCount} Tables</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: 'var(--radius-md)', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
            <Calendar size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>RESERVED TABLES</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f59e0b', fontFamily: 'Outfit' }}>{reservedCount} Tables</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: 'var(--radius-md)', background: 'rgba(168, 85, 247, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#c084fc' }}>
            <Sparkles size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>OCCUPANCY RATE</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#c084fc', fontFamily: 'Outfit' }}>{occupancyRate}%</div>
          </div>
        </div>
      </div>

      {/* Main Tabs (Floor View vs Reservations List) */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => setActiveTab('FLOOR')}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              background: activeTab === 'FLOOR' ? 'var(--primary-gradient)' : 'transparent',
              color: activeTab === 'FLOOR' ? '#fff' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Grid size={16} />
            <span>Interactive Floor Layout</span>
          </button>

          <button
            onClick={() => setActiveTab('RESERVATIONS')}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              background: activeTab === 'RESERVATIONS' ? 'var(--primary-gradient)' : 'transparent',
              color: activeTab === 'RESERVATIONS' ? '#fff' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Calendar size={16} />
            <span>Booked Reservations ({reservations.length})</span>
          </button>
        </div>

        <button onClick={loadData} className="btn btn-secondary btn-sm" title="Refresh Floor Data">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Sync</span>
        </button>
      </div>

      {activeTab === 'FLOOR' && (
        <>
          {/* Zone and Status Filters */}
          <div className="glass-panel" style={{ padding: '14px 20px', display: 'flex', flexWrap: 'wrap', gap: '14px', justifyContent: 'space-between', alignItems: 'center' }}>
            {/* Zones */}
            <div style={{ display: 'flex', gap: '8px', overflowX: 'auto' }}>
              {ZONES.map(z => (
                <button
                  key={z.id}
                  onClick={() => setSelectedZone(z.id)}
                  className={`btn btn-sm ${selectedZone === z.id ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap', fontSize: '0.78rem' }}
                >
                  {z.label}
                </button>
              ))}
            </div>

            {/* Status Pills */}
            <div style={{ display: 'flex', gap: '6px' }}>
              {['ALL', 'AVAILABLE', 'OCCUPIED', 'RESERVED'].map(st => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    border: '1px solid',
                    borderColor: statusFilter === st ? 'var(--primary)' : 'var(--border-subtle)',
                    background: statusFilter === st ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                    color: statusFilter === st ? '#818cf8' : 'var(--text-muted)',
                    cursor: 'pointer',
                  }}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Tables Floor Plan Grid */}
          {loading ? (
            <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 12px' }} />
              Loading floor plan...
            </div>
          ) : filteredTables.length === 0 ? (
            <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <Coffee size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>No tables in this floor zone</h3>
              <p style={{ fontSize: '0.85rem', marginTop: '6px' }}>
                Add new dining tables or switch the filter above.
              </p>
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                gap: '18px',
              }}
            >
              {filteredTables.map(table => {
                const isAvailable = table.status === 'AVAILABLE';
                const isOccupied = table.status === 'OCCUPIED';
                const isReserved = table.status === 'RESERVED';

                // Look for active reservation
                const activeRes = reservations.find(r => r.table_id === table.id && r.status !== 'CANCELLED');

                return (
                  <div
                    key={table.id}
                    className="glass-panel"
                    style={{
                      borderRadius: 'var(--radius-lg)',
                      padding: '20px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '14px',
                      transition: 'all 0.25s ease',
                      border: '1px solid',
                      borderColor: isAvailable 
                        ? 'rgba(16, 185, 129, 0.4)' 
                        : isOccupied 
                        ? 'rgba(239, 68, 68, 0.4)' 
                        : 'rgba(245, 158, 11, 0.4)',
                      background: isAvailable
                        ? 'linear-gradient(180deg, rgba(16, 185, 129, 0.05) 0%, rgba(15, 23, 42, 0.8) 100%)'
                        : isOccupied
                        ? 'linear-gradient(180deg, rgba(239, 68, 68, 0.05) 0%, rgba(15, 23, 42, 0.8) 100%)'
                        : 'linear-gradient(180deg, rgba(245, 158, 11, 0.05) 0%, rgba(15, 23, 42, 0.8) 100%)',
                      boxShadow: isOccupied ? '0 0 20px rgba(239, 68, 68, 0.1)' : 'none',
                    }}
                  >
                    {/* Header: Table Number & Status Badge */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div
                          style={{
                            padding: '4px 12px',
                            borderRadius: 'var(--radius-md)',
                            background: isAvailable 
                              ? 'rgba(16, 185, 129, 0.15)' 
                              : isOccupied 
                              ? 'rgba(239, 68, 68, 0.15)' 
                              : 'rgba(245, 158, 11, 0.15)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 800,
                            fontFamily: 'Outfit',
                            fontSize: '1.35rem',
                            letterSpacing: '0.02em',
                            color: isAvailable ? '#10b981' : isOccupied ? '#ef4444' : '#f59e0b',
                            border: `1px solid ${isAvailable ? 'rgba(16, 185, 129, 0.3)' : isOccupied ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                            minWidth: '52px',
                          }}
                        >
                          {table.table_number?.toString().toUpperCase().startsWith('T') ? table.table_number : `T${table.table_number}`}
                        </div>
                        <div>
                          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                            {table.location ? table.location.replace(/_/g, ' ') : 'MAIN DINING'}
                          </div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {table.capacity} Seats &bull; {table.status}
                          </div>
                        </div>
                      </div>

                      <span className={`badge ${isAvailable ? 'badge-success' : isOccupied ? 'badge-danger' : 'badge-warning'}`}>
                        {table.status}
                      </span>
                    </div>

                    {/* Table Geometry / Seating Capacity Visualization */}
                    <div
                      style={{
                        padding: '12px',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(0, 0, 0, 0.3)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Users size={16} style={{ color: 'var(--text-secondary)' }} />
                        <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{table.capacity} Guests Capacity</span>
                      </div>

                      {/* Visual Seat Dots */}
                      <div style={{ display: 'flex', gap: '4px' }}>
                        {Array.from({ length: Math.min(table.capacity || 4, 8) }).map((_, i) => (
                          <div
                            key={i}
                            style={{
                              width: '8px',
                              height: '8px',
                              borderRadius: '50%',
                              background: isOccupied ? '#ef4444' : isReserved ? '#f59e0b' : '#10b981',
                              opacity: 0.8,
                            }}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Occupied or Reserved details note */}
                    {isReserved && activeRes && (
                      <div style={{ fontSize: '0.75rem', background: 'rgba(245, 158, 11, 0.1)', padding: '8px 10px', borderRadius: '4px', border: '1px dashed rgba(245, 158, 11, 0.3)', color: '#fcd34d' }}>
                        <div>Reserved: <strong>{activeRes.customer_name}</strong></div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Time: {activeRes.start_time || '19:30'} ({activeRes.party_size || 2} pax)</div>
                      </div>
                    )}

                    {isOccupied && (
                      <div style={{ fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', padding: '8px 10px', borderRadius: '4px', border: '1px dashed rgba(239, 68, 68, 0.3)', color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Clock size={13} />
                        <span>Dining in Progress &bull; Kitchen Order Active</span>
                      </div>
                    )}

                    {/* Operational Action Buttons */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: 'auto' }}>
                      {/* Primary Workflow Button */}
                      {isAvailable && (
                        <button
                          onClick={() => handleUpdateStatus(table.id, 'OCCUPIED')}
                          className="btn btn-primary btn-sm"
                          style={{ width: '100%', justifyContent: 'center', padding: '8px' }}
                        >
                          <CheckCircle2 size={14} />
                          <span>Seat Guests</span>
                        </button>
                      )}

                      {isOccupied && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                          <button
                            onClick={() => onNavigateToBilling ? onNavigateToBilling() : null}
                            className="btn btn-primary btn-sm"
                            style={{ padding: '6px', fontSize: '0.75rem', background: 'var(--accent)' }}
                          >
                            <Receipt size={13} />
                            <span>Collect Bill</span>
                          </button>
                          <button
                            onClick={() => handleUpdateStatus(table.id, 'AVAILABLE')}
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '6px', fontSize: '0.75rem' }}
                          >
                            <Check size={13} />
                            <span>Clear Table</span>
                          </button>
                        </div>
                      )}

                      {isReserved && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                          <button
                            onClick={() => handleUpdateStatus(table.id, 'OCCUPIED')}
                            className="btn btn-primary btn-sm"
                            style={{ padding: '6px', fontSize: '0.75rem' }}
                          >
                            <span>Seat Guests</span>
                          </button>
                          <button
                            onClick={() => handleUpdateStatus(table.id, 'AVAILABLE')}
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '6px', fontSize: '0.75rem' }}
                          >
                            <span>Release</span>
                          </button>
                        </div>
                      )}

                      {/* Manual Quick Status Bar */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px', marginTop: '4px' }}>
                        <button
                          onClick={() => handleUpdateStatus(table.id, 'AVAILABLE')}
                          style={{
                            fontSize: '0.68rem',
                            padding: '4px',
                            borderRadius: '4px',
                            border: '1px solid',
                            borderColor: isAvailable ? 'var(--success)' : 'transparent',
                            background: isAvailable ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                            color: isAvailable ? '#10b981' : 'var(--text-muted)',
                            cursor: 'pointer',
                          }}
                        >
                          Available
                        </button>
                        <button
                          onClick={() => handleUpdateStatus(table.id, 'OCCUPIED')}
                          style={{
                            fontSize: '0.68rem',
                            padding: '4px',
                            borderRadius: '4px',
                            border: '1px solid',
                            borderColor: isOccupied ? 'var(--danger)' : 'transparent',
                            background: isOccupied ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                            color: isOccupied ? '#ef4444' : 'var(--text-muted)',
                            cursor: 'pointer',
                          }}
                        >
                          Occupied
                        </button>
                        <button
                          onClick={() => openReserveForTable(table)}
                          style={{
                            fontSize: '0.68rem',
                            padding: '4px',
                            borderRadius: '4px',
                            border: '1px solid',
                            borderColor: isReserved ? 'var(--warning)' : 'transparent',
                            background: isReserved ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                            color: isReserved ? '#f59e0b' : 'var(--text-muted)',
                            cursor: 'pointer',
                          }}
                        >
                          Reserve
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Tab: Booked Reservations Schedule */}
      {activeTab === 'RESERVATIONS' && (
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Upcoming Dining Reservations</h2>
            <button onClick={() => setShowReserveModal(true)} className="btn btn-primary btn-sm">
              <Plus size={14} />
              <span>Book New Table</span>
            </button>
          </div>

          {reservations.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No active reservations booked. Click "Book New Table" to register guest reservations.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {reservations.map(res => (
                <div
                  key={res.id}
                  style={{
                    padding: '14px 18px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '12px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
                      <Calendar size={18} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{res.customer_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '10px', marginTop: '2px' }}>
                        <span>Party: {res.party_size || 2} Guests</span>
                        <span>&bull;</span>
                        <span>Phone: {res.customer_phone || 'N/A'}</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent)' }}>
                        {res.reservation_date || 'Today'} &bull; {res.start_time || '19:30'}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        Table ID: {res.table_id?.slice(-6) || 'Auto'}
                      </div>
                    </div>

                    <span className="badge badge-warning">
                      {res.status || 'CONFIRMED'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add Table Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '28px', maxWidth: '480px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', background: 'var(--primary-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <Grid size={18} />
                </div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Add Dining Table</h2>
              </div>
              <button onClick={() => setShowAddModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateTable} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Table Number / Identifier *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 13 or T13"
                  value={tableNumber}
                  onChange={e => setTableNumber(e.target.value)}
                  className="input"
                />
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Will be formatted automatically as simple ID like <strong>T13</strong>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Seating Capacity</label>
                <select value={capacity} onChange={e => setCapacity(e.target.value)} className="select">
                  <option value={2}>2 Seater &mdash; Romantic Couple Table</option>
                  <option value={4}>4 Seater &mdash; Standard Dining</option>
                  <option value={6}>6 Seater &mdash; Family Booth</option>
                  <option value={8}>8 Seater &mdash; Executive Dining</option>
                  <option value={12}>12 Seater &mdash; Grand Banquet</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Floor Zone Location</label>
                <select value={zone} onChange={e => setZone(e.target.value)} className="select">
                  <option value="MAIN_DINING">Main Dining</option>
                  <option value="FAMILY_SECTION">Family Section</option>
                  <option value="WINDOW_BAY">Window Bay</option>
                  <option value="OUTDOOR_PATIO">Outdoor Patio</option>
                  <option value="TERRACE">Open Terrace Garden</option>
                  <option value="VIP_LOUNGE">VIP Executive Lounge</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="btn btn-primary" style={{ flex: 1 }}>
                  {submitting ? 'Configuring...' : 'Add Table'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Book Reservation Modal */}
      {showReserveModal && (
        <div className="modal-overlay" onClick={() => setShowReserveModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '28px', maxWidth: '500px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', background: 'rgba(245, 158, 11, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
                  <Calendar size={18} />
                </div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Book Table Reservation</h2>
              </div>
              <button onClick={() => setShowReserveModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateReservation} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Guest Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Patel"
                  value={customerName}
                  onChange={e => setCustomerName(e.target.value)}
                  className="input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Mobile Phone</label>
                <input
                  type="tel"
                  placeholder="e.g. +91 98765 43210"
                  value={customerPhone}
                  onChange={e => setCustomerPhone(e.target.value)}
                  className="input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Select Table *</label>
                  <select required value={reserveTableId} onChange={e => setReserveTableId(e.target.value)} className="select">
                    <option value="">-- Choose Table --</option>
                    {tables.map(t => (
                      <option key={t.id} value={t.id}>
                        {t.table_number?.toString().toUpperCase().startsWith('T') ? t.table_number : `T${t.table_number}`} ({t.capacity} Seats) &mdash; {t.status}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Party Size (Pax)</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={guestCount}
                    onChange={e => setGuestCount(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Reservation Date</label>
                  <input
                    type="date"
                    required
                    value={reserveDate}
                    onChange={e => setReserveDate(e.target.value)}
                    className="input"
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Arrival Time</label>
                  <input
                    type="time"
                    required
                    value={reserveTime}
                    onChange={e => setReserveTime(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setShowReserveModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="btn btn-primary" style={{ flex: 1 }}>
                  {submitting ? 'Confirming...' : 'Confirm Reservation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
