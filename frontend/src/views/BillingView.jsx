import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { 
  Receipt, CreditCard, DollarSign, CheckCircle2, RefreshCw, 
  Search, Printer, QrCode, X, ArrowDownLeft, ShieldCheck,
  AlertCircle, Split, Smartphone, Wallet, Banknote, Sparkles,
  ShoppingBag, Check, Volume2, User, Clock, ArrowRight, Share2
} from 'lucide-react';

export default function BillingView({ targetInvoice, onNavigate }) {
  const { role, permissions } = useAuth();
  const { showToast } = useToast();

  const canSettleBills = permissions?.canSettleBills ?? (role === 'CASHIER' || role === 'MANAGER' || role === 'ADMIN');

  // Main navigation tab
  const [activeTab, setActiveTab] = useState('ACTIVE_ORDERS'); // 'ACTIVE_ORDERS' or 'PAID_INVOICES'

  // Data states
  const [orders, setOrders] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);

  // Active billing selection
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [selectedInvoice, setSelectedInvoice] = useState(targetInvoice || null);
  const [searchOrders, setSearchOrders] = useState('');
  const [searchInvoices, setSearchInvoices] = useState('');

  // Payment channel and tender
  const [payMethod, setPayMethod] = useState('UPI'); // 'UPI', 'CASH', 'CARD'
  const [payRef, setPayRef] = useState(`UPI-${Date.now().toString().slice(-6)}`);
  const [cashTendered, setCashTendered] = useState('');
  const [discountPercent, setDiscountPercent] = useState(0);
  const [customDiscount, setCustomDiscount] = useState(0);

  // Settlement processing state
  const [processing, setProcessing] = useState(false);

  // Newly generated invoice modal state (AFTER payment success!)
  const [generatedInvoice, setGeneratedInvoice] = useState(null);
  const [soundboxPlayed, setSoundboxPlayed] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ordersRes, invsRes, tablesRes] = await Promise.all([
        api.orders.getAll().catch(() => []),
        api.billing.getInvoices().catch(() => []),
        api.tables.getAll().catch(() => []),
      ]);

      const allOrders = Array.isArray(ordersRes) ? ordersRes : [];
      const allInvoices = Array.isArray(invsRes) ? invsRes : [];
      const allTables = Array.isArray(tablesRes) ? tablesRes : [];

      setOrders(allOrders);
      setInvoices(allInvoices);
      setTables(allTables);

      // If target invoice passed, select it
      if (targetInvoice) {
        setSelectedInvoice(targetInvoice);
        setActiveTab('PAID_INVOICES');
      } else {
        // Find first unbilled order to preselect
        const unbilled = allOrders.filter(o => o.status !== 'CANCELLED' && o.status !== 'COMPLETED');
        if (unbilled.length > 0 && !selectedOrder) {
          handleSelectOrder(unbilled[0]);
        }
      }
    } catch (err) {
      console.error('Billing load error:', err);
      showToast('Could not load billing orders or invoices', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (targetInvoice) {
      setSelectedInvoice(targetInvoice);
      setActiveTab('PAID_INVOICES');
    }
  }, [targetInvoice]);

  // Select order to bill
  const handleSelectOrder = (order) => {
    setSelectedOrder(order);
    const existingDiscount = parseFloat(order.discount_amount || 0);
    setCustomDiscount(existingDiscount);
    setDiscountPercent(0);
    const sub = parseFloat(order.subtotal || 0);
    const disc = Math.min(sub, existingDiscount);
    const taxable = Math.max(0, sub - disc);
    const total = taxable + taxable * 0.05;
    setCashTendered(total.toFixed(2));
    setPayRef(`${payMethod}-${Date.now().toString().slice(-6)}`);
  };

  // Soundbox sound effect simulation
  const playSoundboxAlert = (amount) => {
    setSoundboxPlayed(true);
    showToast(`🔔 UPI Soundbox: "Payment of ₹${amount} received on PhonePe / GPay"`, 'success');
    setTimeout(() => setSoundboxPlayed(false), 4000);
  };

  // REALISTIC PAYMENT & INVOICE GENERATION SEQUENCE
  const handleSettleAndGenerateInvoice = async () => {
    if (!selectedOrder) return;
    if (!canSettleBills) {
      showToast('Only Cashier, Manager, or Admin can collect payments', 'warning');
      return;
    }

    setProcessing(true);
    try {
      const orderId = selectedOrder.id;

      // 1. Create or update the Tax Invoice for this order with calculated discount
      const invoiceDoc = await api.billing.createInvoice(orderId, discountVal);
      const invoiceId = invoiceDoc.id || invoiceDoc._id;
      const totalAmt = parseFloat(invoiceDoc.total_amount || netPayable || 0);

      // 2. Process and record the payment immediately
      await api.billing.createPayment({
        invoice_id: invoiceId,
        amount: totalAmt,
        payment_method: payMethod,
        transaction_reference: payRef || `TXN-${Date.now()}`,
        recorded_by: `${role} Cashier`,
      });

      // 3. Mark the generated invoice as PAID and include order items for the receipt
      const settledInvoice = {
        ...invoiceDoc,
        status: 'PAID',
        payment_method: payMethod,
        transaction_reference: payRef,
        items: (invoiceDoc.items && invoiceDoc.items.length > 0) ? invoiceDoc.items : (selectedOrder.items || []),
        order_number: selectedOrder.order_number,
        table_number: selectedOrder.table_number,
        customer_name: selectedOrder.customer_name || 'Guest Diner',
      };

      // 4. Update local state
      setInvoices(prev => [settledInvoice, ...prev.filter(i => i.id !== invoiceId)]);
      setOrders(prev => prev.filter(o => o.id !== orderId));
      setSelectedOrder(null);

      // 5. Open the celebration and official tax invoice modal!
      setGeneratedInvoice(settledInvoice);
      showToast(`Payment of ₹${totalAmt.toFixed(2)} confirmed! Tax Invoice ${settledInvoice.invoice_number} generated.`, 'success');
      
      if (payMethod === 'UPI') {
        playSoundboxAlert(totalAmt.toFixed(2));
      }
    } catch (err) {
      console.error('Billing error:', err);
      showToast(err.message || 'Payment settlement failed', 'danger');
    } finally {
      setProcessing(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  // Metrics
  const activeUnbilledOrders = orders.filter(o => o.status !== 'CANCELLED' && o.status !== 'COMPLETED');
  const paidInvoicesList = invoices.filter(i => i.status === 'PAID');
  const totalRevenueCollected = paidInvoicesList.reduce((sum, i) => sum + parseFloat(i.total_amount || 0), 0);
  const pendingCollectionAmount = activeUnbilledOrders.reduce((sum, o) => sum + parseFloat(o.total_amount || 0), 0);

  // Active bill calculations
  const orderSubtotal = selectedOrder ? parseFloat(selectedOrder.subtotal || 0) : 0;
  const discountVal = selectedOrder ? Math.min(orderSubtotal, (orderSubtotal * (discountPercent / 100)) + (parseFloat(customDiscount) || 0)) : 0;
  const taxableAmount = Math.max(0, orderSubtotal - discountVal);
  const cgst = taxableAmount * 0.025;
  const sgst = taxableAmount * 0.025;
  const netPayable = selectedOrder ? Math.max(0, taxableAmount + cgst + sgst) : 0;

  const cashGiven = parseFloat(cashTendered || 0);
  const changeToReturn = cashGiven >= netPayable ? (cashGiven - netPayable).toFixed(2) : '0.00';

  // Filtered lists
  const filteredActiveOrders = activeUnbilledOrders.filter(o => {
    const q = searchOrders.toLowerCase();
    return (
      (o.order_number && o.order_number.toLowerCase().includes(q)) ||
      (o.customer_name && o.customer_name.toLowerCase().includes(q)) ||
      (o.table_number && o.table_number.toString().includes(q))
    );
  });

  const filteredPaidInvoices = paidInvoicesList.filter(inv => {
    const q = searchInvoices.toLowerCase();
    return (
      (inv.invoice_number && inv.invoice_number.toLowerCase().includes(q)) ||
      (inv.id && inv.id.toLowerCase().includes(q)) ||
      (inv.order_number && inv.order_number.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'Outfit' }}>Billing</h1>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: 'var(--radius-full)',
                background: 'rgba(234, 179, 8, 0.15)',
                color: '#eab308',
                border: '1px solid rgba(234, 179, 8, 0.3)',
              }}
            >
              Cashier Terminal
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            Collect guest payments, calculate change, and generate GST tax invoices upon payment confirmation.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {onNavigate && (
            <button onClick={() => onNavigate('orders')} className="btn btn-primary">
              <Clock size={14} />
              <span>Live Orders</span>
            </button>
          )}
          <button onClick={loadData} className="btn btn-secondary">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Sync Registers</span>
          </button>
        </div>
      </div>

      {/* Metrics Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#10b981' }}>
            <Banknote size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>TOTAL CASH & UPI REVENUE</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#10b981', fontFamily: 'Outfit' }}>
              ₹{totalRevenueCollected.toFixed(2)}
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: 'var(--radius-md)', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
            <AlertCircle size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>UNBILLED ORDERS AWAITING PAYMENT</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ef4444', fontFamily: 'Outfit' }}>
              ₹{pendingCollectionAmount.toFixed(2)} ({activeUnbilledOrders.length})
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: 'var(--radius-md)', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#818cf8' }}>
            <Receipt size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>TAX INVOICES GENERATED</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#818cf8', fontFamily: 'Outfit' }}>
              {paidInvoicesList.length} Settled
            </div>
          </div>
        </div>
      </div>

      {/* Main Workflow Tabs */}
      <div style={{ display: 'flex', gap: '12px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        <button
          onClick={() => setActiveTab('ACTIVE_ORDERS')}
          style={{
            padding: '10px 18px',
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: activeTab === 'ACTIVE_ORDERS' ? 'var(--primary-gradient)' : 'transparent',
            color: activeTab === 'ACTIVE_ORDERS' ? '#fff' : 'var(--text-secondary)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <CreditCard size={16} />
          <span>Checkout Active Table / Order</span>
          {activeUnbilledOrders.length > 0 && (
            <span style={{ background: '#ef4444', color: '#fff', padding: '1px 7px', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 700 }}>
              {activeUnbilledOrders.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('PAID_INVOICES')}
          style={{
            padding: '10px 18px',
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: activeTab === 'PAID_INVOICES' ? 'var(--primary-gradient)' : 'transparent',
            color: activeTab === 'PAID_INVOICES' ? '#fff' : 'var(--text-secondary)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Receipt size={16} />
          <span>Settled Tax Invoices Archive ({paidInvoicesList.length})</span>
        </button>
      </div>

      {/* TAB 1: REALISTIC BILLING CHECKOUT & SETTLEMENT */}
      {activeTab === 'ACTIVE_ORDERS' && (
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '24px', minHeight: '620px' }}>
          {/* Left Column: List of Active Tables & Orders */}
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                  SELECT TABLE TO BILL
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {filteredActiveOrders.length} waiting
                </span>
              </div>

              {/* Search Orders */}
              <div style={{ position: 'relative' }}>
                <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Search table # or order #..."
                  value={searchOrders}
                  onChange={e => setSearchOrders(e.target.value)}
                  className="input"
                  style={{ paddingLeft: '32px', height: '34px', fontSize: '0.8rem', borderRadius: 'var(--radius-full)' }}
                />
              </div>
            </div>

            {/* List of Orders */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {loading ? (
                <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Loading active orders...
                </div>
              ) : filteredActiveOrders.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <CheckCircle2 size={32} style={{ margin: '0 auto 10px', color: '#10b981', opacity: 0.8 }} />
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>All Orders Settled!</div>
                  <p style={{ fontSize: '0.78rem', marginTop: '4px', marginBottom: '14px' }}>
                    No unbilled orders waiting. All customer orders are settled.
                  </p>
                  {onNavigate && (
                    <button
                      onClick={() => onNavigate('orders')}
                      className="btn btn-primary btn-sm"
                      style={{ margin: '0 auto', display: 'inline-flex' }}
                    >
                      <Clock size={14} />
                      <span>View Live Orders</span>
                    </button>
                  )}
                </div>
              ) : (
                filteredActiveOrders.map(ord => {
                  const isSelected = selectedOrder?.id === ord.id;
                  const itemsCount = ord.items?.length || 0;

                  return (
                    <div
                      key={ord.id}
                      onClick={() => handleSelectOrder(ord)}
                      style={{
                        padding: '14px',
                        borderRadius: 'var(--radius-md)',
                        background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-tertiary)',
                        border: '1px solid',
                        borderColor: isSelected ? 'var(--primary)' : 'var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        borderLeft: isSelected ? '4px solid var(--primary)' : '4px solid rgba(239, 68, 68, 0.6)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontSize: '1.05rem', fontWeight: 800, fontFamily: 'Outfit', color: 'var(--text-primary)' }}>
                            {ord.table_number ? (ord.table_number.toString().toUpperCase().startsWith('T') ? ord.table_number : `T${ord.table_number}`) : 'Takeaway Counter'}
                          </span>
                        </div>
                        <span style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit' }}>
                          ₹{parseFloat(ord.total_amount || 0).toFixed(2)}
                        </span>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span>Order #{ord.order_number || ord.id?.slice(-6)}</span>
                        <span>{itemsCount} items</span>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        <span>Guest: {ord.customer_name || 'Walk-in Diner'}</span>
                        <span className="badge badge-warning" style={{ fontSize: '0.62rem', padding: '1px 6px' }}>
                          READY TO BILL
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Column: Pre-Bill & Settlement Terminal */}
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
            {selectedOrder ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', maxWidth: '640px', margin: '0 auto', width: '100%' }}>
                {/* Order Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase' }}>
                      CASHIER CHECKOUT STATION
                    </span>
                    <h2 style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'Outfit', marginTop: '2px' }}>
                      {selectedOrder.table_number ? `Billing ${selectedOrder.table_number.toString().toUpperCase().startsWith('T') ? selectedOrder.table_number : `T${selectedOrder.table_number}`}` : 'Takeaway Order Billing'}
                    </h2>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Order #{selectedOrder.order_number || selectedOrder.id?.slice(-8)} &bull; Guest: {selectedOrder.customer_name || 'Dine-in Customer'}
                    </div>
                  </div>

                  <span className="badge badge-warning" style={{ fontSize: '0.8rem', padding: '4px 12px' }}>
                    UNPAID PRE-BILL
                  </span>
                </div>

                {/* Ordered Items Breakdown */}
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-md)', padding: '14px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>
                    ORDERED DISHES & KITCHEN ITEMS
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 50px 80px 90px', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                      <span>FOOD ITEM</span>
                      <span style={{ textAlign: 'center' }}>QTY</span>
                      <span style={{ textAlign: 'right' }}>RATE</span>
                      <span style={{ textAlign: 'right' }}>AMOUNT</span>
                    </div>
                    {selectedOrder.items?.map((it, idx) => {
                      const name = it.name || it.item_name_snapshot || it.menu_item_name || 'Dish Item';
                      const qty = it.quantity || 1;
                      const rate = parseFloat(it.price || it.unit_price_snapshot || (it.item_total ? it.item_total / qty : 0));
                      const total = parseFloat(it.item_total || rate * qty);
                      return (
                        <div key={idx} style={{ display: 'grid', gridTemplateColumns: '1fr 50px 80px 90px', fontSize: '0.85rem', alignItems: 'center' }}>
                          <span style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</span>
                          <span style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>{qty}</span>
                          <span style={{ textAlign: 'right', color: 'var(--text-muted)' }}>₹{rate.toFixed(2)}</span>
                          <span style={{ textAlign: 'right', fontWeight: 700, color: 'var(--text-primary)' }}>₹{total.toFixed(2)}</span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Calculations */}
                  <div style={{ marginTop: '12px', borderTop: '1px dashed var(--border-subtle)', paddingTop: '10px', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                      <span>Subtotal:</span>
                      <span>₹{orderSubtotal.toFixed(2)}</span>
                    </div>

                    {/* Quick Discount Selector & Custom Discount */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '4px 0', flexWrap: 'wrap', gap: '6px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Discount Voucher:</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {[0, 5, 10, 15].map(pct => (
                            <button
                              key={pct}
                              type="button"
                              onClick={() => {
                                setDiscountPercent(pct);
                                if (pct > 0) setCustomDiscount(0);
                              }}
                              style={{
                                padding: '2px 8px',
                                borderRadius: '4px',
                                fontSize: '0.7rem',
                                fontWeight: 600,
                                border: '1px solid',
                                borderColor: discountPercent === pct ? 'var(--primary)' : 'var(--border-subtle)',
                                background: discountPercent === pct ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                                color: discountPercent === pct ? '#818cf8' : 'var(--text-muted)',
                                cursor: 'pointer',
                              }}
                            >
                              {pct === 0 ? 'None' : `${pct}%`}
                            </button>
                          ))}
                        </div>
                        <input
                          type="number"
                          placeholder="₹ Flat"
                          value={customDiscount || ''}
                          onChange={e => {
                            const val = parseFloat(e.target.value) || 0;
                            setCustomDiscount(val);
                            if (val > 0) setDiscountPercent(0);
                          }}
                          style={{
                            width: '68px',
                            height: '24px',
                            fontSize: '0.72rem',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: 'var(--bg-secondary)',
                            border: '1px solid var(--border-subtle)',
                            color: 'var(--text-primary)',
                          }}
                        />
                      </div>
                    </div>

                    {discountVal > 0 && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--success)' }}>
                        <span>Promotional Discount:</span>
                        <span>-₹{discountVal.toFixed(2)}</span>
                      </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                      <span>CGST (2.5%):</span>
                      <span>₹{cgst.toFixed(2)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                      <span>SGST (2.5%):</span>
                      <span>₹{sgst.toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Net Payable Highlight */}
                  <div style={{ marginTop: '12px', padding: '12px 14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 700 }}>NET PAYABLE AMOUNT:</span>
                    <span style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit' }}>
                      ₹{netPayable.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Payment Channel Selection */}
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 700, display: 'block', marginBottom: '8px' }}>
                    SELECT PAYMENT METHOD
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                    {[
                      { id: 'UPI', label: 'UPI / Dynamic QR', icon: QrCode },
                      { id: 'CASH', label: 'Cash Tender', icon: Banknote },
                      { id: 'CARD', label: 'Debit / Credit Card', icon: CreditCard },
                    ].map(m => {
                      const Icon = m.icon;
                      const isSelected = payMethod === m.id;
                      return (
                        <button
                          key={m.id}
                          type="button"
                          onClick={() => {
                            setPayMethod(m.id);
                            setPayRef(`${m.id}-${Date.now().toString().slice(-6)}`);
                          }}
                          className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                          style={{ padding: '12px 8px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}
                        >
                          <Icon size={18} />
                          <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{m.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Method Specific Controls */}
                {payMethod === 'UPI' && (
                  <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                      SCAN TO PAY: ₹{netPayable.toFixed(2)}
                    </div>

                    {/* QR Code Matrix Display */}
                    <div
                      style={{
                        width: '140px',
                        height: '140px',
                        margin: '0 auto 10px',
                        background: '#ffffff',
                        padding: '10px',
                        borderRadius: '8px',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <div style={{ width: '34px', height: '34px', border: '5px solid #000', borderRadius: '4px', background: '#000' }} />
                        <div style={{ width: '34px', height: '34px', border: '5px solid #000', borderRadius: '4px', background: '#000' }} />
                      </div>
                      <div style={{ textAlign: 'center', fontWeight: 800, fontSize: '0.75rem', color: '#000' }}>
                        ₹{netPayable.toFixed(2)}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <div style={{ width: '34px', height: '34px', border: '5px solid #000', borderRadius: '4px', background: '#000' }} />
                        <div style={{ width: '22px', height: '22px', background: '#6366f1', borderRadius: '3px' }} />
                      </div>
                    </div>

                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      UPI ID: <strong>dineflow@icici</strong> &bull; Apps: GPay, PhonePe, Paytm, BHIM
                    </div>

                    <div style={{ display: 'flex', gap: '8px', marginTop: '12px', alignItems: 'center' }}>
                      <input
                        type="text"
                        placeholder="UPI Ref / UTR #"
                        value={payRef}
                        onChange={e => setPayRef(e.target.value)}
                        className="input"
                        style={{ height: '36px', fontSize: '0.8rem' }}
                      />
                      <button
                        type="button"
                        onClick={() => playSoundboxAlert(netPayable.toFixed(2))}
                        className="btn btn-secondary btn-sm"
                        style={{ whiteSpace: 'nowrap', height: '36px' }}
                        title="Simulate UPI Soundbox Chime"
                      >
                        <Volume2 size={14} style={{ color: '#10b981' }} />
                        <span>Soundbox</span>
                      </button>
                    </div>
                  </div>
                )}

                {payMethod === 'CASH' && (
                  <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <label style={{ fontSize: '0.8rem', fontWeight: 700 }}>Cash Received from Customer (₹)</label>
                      <button
                        type="button"
                        onClick={() => setCashTendered(netPayable.toString())}
                        style={{ background: 'none', border: 'none', color: 'var(--primary)', fontSize: '0.75rem', cursor: 'pointer', fontWeight: 600 }}
                      >
                        Exact Amount
                      </button>
                    </div>

                    <input
                      type="number"
                      step="1"
                      value={cashTendered}
                      onChange={e => setCashTendered(e.target.value)}
                      className="input"
                      style={{ fontSize: '1.25rem', fontWeight: 800 }}
                    />

                    {/* Quick Indian Currency Denominations */}
                    <div style={{ display: 'flex', gap: '6px', marginTop: '8px', flexWrap: 'wrap' }}>
                      {[100, 200, 500, 2000].map(den => (
                        <button
                          key={den}
                          type="button"
                          onClick={() => setCashTendered((cashGiven + den).toString())}
                          style={{
                            background: 'rgba(255, 255, 255, 0.05)',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: '4px',
                            padding: '4px 8px',
                            fontSize: '0.72rem',
                            color: 'var(--text-secondary)',
                            cursor: 'pointer',
                          }}
                        >
                          +₹{den}
                        </button>
                      ))}
                    </div>

                    {/* Change Due Box */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', padding: '10px 14px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#10b981' }}>CHANGE TO RETURN:</span>
                      <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#10b981', fontFamily: 'Outfit' }}>
                        ₹{changeToReturn}
                      </span>
                    </div>
                  </div>
                )}

                {payMethod === 'CARD' && (
                  <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)' }}>
                    <label style={{ fontSize: '0.8rem', fontWeight: 700, display: 'block', marginBottom: '6px' }}>
                      Card Terminal Approval Code / Auth Slip #
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. AUTH-482910"
                      value={payRef}
                      onChange={e => setPayRef(e.target.value)}
                      className="input"
                    />
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                      Swipe or tap card on PineLabs / HDFC terminal, then input approval code.
                    </div>
                  </div>
                )}

                {/* THE FINAL SETTLEMENT BUTTON THAT GENERATES INVOICE AFTER PAYMENT */}
                <button
                  onClick={handleSettleAndGenerateInvoice}
                  disabled={processing}
                  className="btn btn-primary"
                  style={{
                    padding: '16px',
                    fontSize: '1rem',
                    fontWeight: 700,
                    borderRadius: 'var(--radius-md)',
                    boxShadow: 'var(--shadow-glow)',
                    background: 'var(--primary-gradient)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                    marginTop: '8px',
                  }}
                >
                  <CheckCircle2 size={20} />
                  <span>
                    {processing ? 'Settling Payment & Generating Tax Invoice...' : `Confirm Payment & Generate Tax Invoice (₹${netPayable.toFixed(2)})`}
                  </span>
                </button>
              </div>
            ) : (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', padding: '40px' }}>
                <Receipt size={48} style={{ opacity: 0.3, marginBottom: '12px' }} />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Select an Active Table Order</h3>
                <p style={{ fontSize: '0.85rem', marginTop: '6px', textAlign: 'center', maxWidth: '360px' }}>
                  Click on an unbilled table order from the left panel to review items, apply discounts, collect payment, and generate the official tax invoice.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: SETTLED TAX INVOICES ARCHIVE */}
      {activeTab === 'PAID_INVOICES' && (
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '24px', minHeight: '620px' }}>
          {/* Left: Settled Invoices List */}
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                  TAX INVOICES ARCHIVE
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {filteredPaidInvoices.length} paid bills
                </span>
              </div>

              {/* Search Invoices */}
              <div style={{ position: 'relative' }}>
                <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Search invoice # or order #..."
                  value={searchInvoices}
                  onChange={e => setSearchInvoices(e.target.value)}
                  className="input"
                  style={{ paddingLeft: '32px', height: '34px', fontSize: '0.8rem', borderRadius: 'var(--radius-full)' }}
                />
              </div>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {filteredPaidInvoices.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No settled invoices found.
                </div>
              ) : (
                filteredPaidInvoices.map(inv => {
                  const isSelected = selectedInvoice?.id === inv.id;

                  return (
                    <div
                      key={inv.id}
                      onClick={() => setSelectedInvoice(inv)}
                      style={{
                        padding: '12px 14px',
                        borderRadius: 'var(--radius-md)',
                        background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-tertiary)',
                        border: '1px solid',
                        borderColor: isSelected ? 'var(--primary)' : 'var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        borderLeft: '4px solid #10b981',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>
                          #{inv.invoice_number || inv.id?.slice(-8)}
                        </span>
                        <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                          PAID
                        </span>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span>Order #{inv.order_number || inv.order_id?.slice(-6) || 'Direct'}</span>
                        <strong style={{ color: 'var(--text-primary)', fontSize: '0.9rem', fontFamily: 'Outfit' }}>
                          ₹{parseFloat(inv.total_amount || 0).toFixed(2)}
                        </strong>
                      </div>

                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        {new Date(inv.generated_at || inv.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} &bull; {new Date(inv.generated_at || inv.created_at || Date.now()).toLocaleDateString()}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Right: Thermal Tax Invoice Receipt Preview */}
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
            {selectedInvoice ? (
              <div style={{ display: 'flex', flexDirection: 'column', maxWidth: '520px', margin: '0 auto', width: '100%' }}>
                {/* Print Action Bar */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                  <span className="badge badge-success" style={{ fontSize: '0.8rem', padding: '4px 12px' }}>
                    GST TAX INVOICE
                  </span>

                  <button onClick={handlePrint} className="btn btn-secondary btn-sm">
                    <Printer size={15} />
                    <span>Reprint Tax Invoice</span>
                  </button>
                </div>

                {/* Thermal Tax Receipt */}
                <div
                  className="printable-receipt"
                  style={{
                    background: '#ffffff',
                    color: '#0f172a',
                    padding: '28px',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
                    fontFamily: 'Courier New, monospace',
                    fontSize: '0.85rem',
                    lineHeight: 1.5,
                  }}
                >
                  <div style={{ textAlign: 'center', borderBottom: '1px dashed #94a3b8', paddingBottom: '12px', marginBottom: '12px' }}>
                    <h2 style={{ fontSize: '1.35rem', fontWeight: 800, fontFamily: 'Outfit, sans-serif', color: '#0f172a', letterSpacing: '-0.02em' }}>
                      DINEFLOW RESTAURANT
                    </h2>
                    <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                      GSTIN: 36ABCDE1234F1Z5 &bull; FSSAI Lic: 13622011000452
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                      Hitech City, Hyderabad &bull; +91 98765 43210
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#475569', marginBottom: '10px' }}>
                    <div>
                      <div><strong>TAX INVOICE:</strong> #{selectedInvoice.invoice_number || selectedInvoice.id?.slice(-8)}</div>
                      <div><strong>ORDER:</strong> #{selectedInvoice.order_number || selectedInvoice.order_id?.slice(-8)}</div>
                      <div><strong>TABLE:</strong> {selectedInvoice.table_number ? (selectedInvoice.table_number.toString().toUpperCase().startsWith('T') ? selectedInvoice.table_number : `T${selectedInvoice.table_number}`) : 'TAKEAWAY'}</div>
                      <div><strong>PAYMENT:</strong> {selectedInvoice.payment_method || 'CASH / UPI'}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div><strong>DATE:</strong> {new Date(selectedInvoice.generated_at || selectedInvoice.created_at || Date.now()).toLocaleDateString()}</div>
                      <div><strong>TIME:</strong> {new Date(selectedInvoice.generated_at || selectedInvoice.created_at || Date.now()).toLocaleTimeString()}</div>
                      <div><strong>STATUS:</strong> PAID</div>
                    </div>
                  </div>

                  {/* Items */}
                  <div style={{ borderTop: '1px dashed #94a3b8', borderBottom: '1px dashed #94a3b8', padding: '10px 0', margin: '10px 0' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 40px 65px 75px', fontWeight: 700, marginBottom: '6px', fontSize: '0.75rem', borderBottom: '1px solid #cbd5e1', paddingBottom: '4px' }}>
                      <span>FOOD ITEM</span>
                      <span style={{ textAlign: 'center' }}>QTY</span>
                      <span style={{ textAlign: 'right' }}>RATE</span>
                      <span style={{ textAlign: 'right' }}>AMOUNT</span>
                    </div>
                    {selectedInvoice.items?.map((it, i) => {
                      const name = it.name || it.item_name_snapshot || it.menu_item_name || 'Dish Item';
                      const qty = it.quantity || 1;
                      const rate = parseFloat(it.price || it.unit_price_snapshot || (it.item_total ? it.item_total / qty : 0));
                      const total = parseFloat(it.item_total || rate * qty);
                      return (
                        <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 40px 65px 75px', marginBottom: '4px', fontSize: '0.78rem' }}>
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</span>
                          <span style={{ textAlign: 'center' }}>{qty}</span>
                          <span style={{ textAlign: 'right' }}>₹{rate.toFixed(2)}</span>
                          <span style={{ textAlign: 'right', fontWeight: 700 }}>₹{total.toFixed(2)}</span>
                        </div>
                      );
                    })}
                    {(!selectedInvoice.items || selectedInvoice.items.length === 0) && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                        <span>Culinary Dining Experience</span>
                        <span>₹{parseFloat(selectedInvoice.subtotal || selectedInvoice.total_amount || 0).toFixed(2)}</span>
                      </div>
                    )}
                  </div>

                  {/* Totals */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Subtotal:</span>
                      <span>₹{parseFloat(selectedInvoice.subtotal || 0).toFixed(2)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569' }}>
                      <span>CGST (2.5%):</span>
                      <span>₹{(parseFloat(selectedInvoice.tax_amount || 0) / 2 || 0).toFixed(2)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569' }}>
                      <span>SGST (2.5%):</span>
                      <span>₹{(parseFloat(selectedInvoice.tax_amount || 0) / 2 || 0).toFixed(2)}</span>
                    </div>
                    {parseFloat(selectedInvoice.discount_amount || 0) > 0 && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#10b981' }}>
                        <span>Promotional Discount:</span>
                        <span>-₹{parseFloat(selectedInvoice.discount_amount || 0).toFixed(2)}</span>
                      </div>
                    )}
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        fontSize: '1.25rem',
                        fontWeight: 800,
                        borderTop: '2px solid #0f172a',
                        paddingTop: '8px',
                        marginTop: '6px',
                        color: '#0f172a',
                      }}
                    >
                      <span>NET AMOUNT PAID:</span>
                      <span>₹{parseFloat(selectedInvoice.total_amount || 0).toFixed(2)}</span>
                    </div>
                  </div>

                  <div style={{ textAlign: 'center', marginTop: '20px', borderTop: '1px dashed #94a3b8', paddingTop: '12px', fontSize: '0.75rem', color: '#64748b' }}>
                    *** TAX PAID INVOICE &bull; THANK YOU ***<br />
                    Visit again at DineFlow!
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                Select an invoice from the archive to inspect and reprint.
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL: INSTANT TAX INVOICE GENERATION AFTER PAYMENT SUCCESS */}
      {generatedInvoice && (
        <div className="modal-overlay" onClick={() => setGeneratedInvoice(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '28px', maxWidth: '540px' }}>
            {/* Header Success Celebration */}
            <div style={{ textAlign: 'center', marginBottom: '16px' }}>
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '2px solid #10b981',
                  color: '#10b981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 12px',
                }}
              >
                <CheckCircle2 size={32} />
              </div>
              <span
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: '#10b981',
                  background: 'rgba(16, 185, 129, 0.1)',
                  padding: '3px 10px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                }}
              >
                Payment Confirmed & Verified
              </span>
              <h2 style={{ fontSize: '1.45rem', fontWeight: 800, marginTop: '8px' }}>
                Tax Invoice Generated!
              </h2>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Invoice <strong style={{ color: 'var(--text-primary)' }}>#{generatedInvoice.invoice_number}</strong> &bull; Total Settled: <strong style={{ color: '#10b981' }}>₹{parseFloat(generatedInvoice.total_amount || 0).toFixed(2)}</strong>
              </div>
            </div>

            {/* Thermal Tax Receipt View */}
            <div
              className="printable-receipt"
              style={{
                background: '#ffffff',
                color: '#0f172a',
                padding: '20px',
                borderRadius: 'var(--radius-md)',
                fontFamily: 'Courier New, monospace',
                fontSize: '0.8rem',
                lineHeight: 1.4,
                maxHeight: '300px',
                overflowY: 'auto',
                marginBottom: '18px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
              }}
            >
              <div style={{ textAlign: 'center', borderBottom: '1px dashed #94a3b8', paddingBottom: '8px', marginBottom: '8px' }}>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, fontFamily: 'Outfit, sans-serif' }}>DINEFLOW RESTAURANT</div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>GSTIN: 36ABCDE1234F1Z5 &bull; Hitech City</div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#475569', marginBottom: '8px' }}>
                <div>INV: #{generatedInvoice.invoice_number}</div>
                <div>{new Date().toLocaleTimeString()}</div>
              </div>

              {/* Items List */}
              <div style={{ borderTop: '1px dashed #94a3b8', borderBottom: '1px dashed #94a3b8', padding: '8px 0', margin: '8px 0' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 40px 65px 75px', fontWeight: 700, marginBottom: '6px', fontSize: '0.75rem', borderBottom: '1px solid #cbd5e1', paddingBottom: '4px' }}>
                  <span>FOOD ITEM</span>
                  <span style={{ textAlign: 'center' }}>QTY</span>
                  <span style={{ textAlign: 'right' }}>RATE</span>
                  <span style={{ textAlign: 'right' }}>AMOUNT</span>
                </div>
                {generatedInvoice.items?.map((it, i) => {
                  const name = it.name || it.item_name_snapshot || it.menu_item_name || 'Dish';
                  const qty = it.quantity || 1;
                  const rate = parseFloat(it.price || it.unit_price_snapshot || (it.item_total ? it.item_total / qty : 0));
                  const total = parseFloat(it.item_total || rate * qty);
                  return (
                    <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 40px 65px 75px', fontSize: '0.78rem', marginBottom: '3px' }}>
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</span>
                      <span style={{ textAlign: 'center' }}>{qty}</span>
                      <span style={{ textAlign: 'right' }}>₹{rate.toFixed(2)}</span>
                      <span style={{ textAlign: 'right', fontWeight: 700 }}>₹{total.toFixed(2)}</span>
                    </div>
                  );
                })}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 800, fontSize: '1rem', borderTop: '1px solid #000', paddingTop: '6px' }}>
                <span>TOTAL PAID:</span>
                <span>₹{parseFloat(generatedInvoice.total_amount || 0).toFixed(2)}</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', textAlign: 'right', marginTop: '2px' }}>
                Via: {generatedInvoice.payment_method || payMethod} ({generatedInvoice.transaction_reference || payRef})
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <button
                onClick={handlePrint}
                className="btn btn-secondary"
                style={{ padding: '12px', justifyContent: 'center' }}
              >
                <Printer size={16} />
                <span>Print Tax Invoice</span>
              </button>

              <button
                onClick={() => setGeneratedInvoice(null)}
                className="btn btn-primary"
                style={{ padding: '12px', justifyContent: 'center' }}
              >
                <span>Bill Next Table</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
