import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import { Star, MessageSquare, Plus, User, RefreshCw, X, ThumbsUp } from 'lucide-react';

export default function FeedbackView() {
  const { showToast } = useToast();
  const [feedbackList, setFeedbackList] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // Form
  const [orderId, setOrderId] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [fbRes, ordRes] = await Promise.all([
        api.feedback.getAll().catch(() => []),
        api.orders.getAll().catch(() => []),
      ]);
      setFeedbackList(Array.isArray(fbRes) ? fbRes : []);
      setOrders(Array.isArray(ordRes) ? ordRes : []);
      if (Array.isArray(ordRes) && ordRes.length > 0 && !orderId) {
        setOrderId(ordRes[0].id);
      }
    } catch (err) {
      console.error('Feedback load error:', err);
      showToast('Could not load feedback records', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateFeedback = async (e) => {
    e.preventDefault();
    if (!orderId || !comment) {
      showToast('Please select an order and provide review feedback', 'warning');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.feedback.create(orderId, {
        rating: parseInt(rating) || 5,
        comment,
        customer_name: customerName || 'Satisfied Guest',
      });
      showToast('Customer review submitted!', 'success');
      setFeedbackList(prev => [res, ...prev]);
      setShowModal(false);
      setComment('');
      setCustomerName('');
    } catch (err) {
      showToast(err.message || 'Failed to submit feedback', 'danger');
    } finally {
      setSubmitting(false);
    }
  };

  // Average rating
  const avgRating = feedbackList.length > 0
    ? (feedbackList.reduce((acc, f) => acc + (f.rating || 5), 0) / feedbackList.length).toFixed(1)
    : '5.0';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>Customer Reviews & Dining Feedback</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Guest satisfaction scores, food ratings, and experience testimonials.
          </p>
        </div>

        <button onClick={() => setShowModal(true)} className="btn btn-primary">
          <Plus size={16} />
          <span>Record Guest Review</span>
        </button>
      </div>

      {/* Summary Score Bar */}
      <div
        className="glass-panel"
        style={{
          padding: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '32px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ fontSize: '3rem', fontWeight: 800, fontFamily: 'Outfit', color: 'var(--primary)' }}>
            {avgRating}
          </div>
          <div>
            <div style={{ display: 'flex', gap: '4px', color: '#f59e0b' }}>
              {[1, 2, 3, 4, 5].map(s => (
                <Star key={s} size={20} fill={s <= Math.round(parseFloat(avgRating)) ? '#f59e0b' : 'transparent'} />
              ))}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Based on {feedbackList.length} verified customer reviews
            </div>
          </div>
        </div>
      </div>

      {/* Reviews Grid */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading customer reviews...
        </div>
      ) : feedbackList.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No reviews recorded yet. Click "Record Guest Review" to collect feedback.
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '16px',
          }}
        >
          {feedbackList.map(item => (
            <div
              key={item.id}
              className="glass-panel"
              style={{
                padding: '20px',
                borderRadius: 'var(--radius-lg)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '14px',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', gap: '2px', color: '#f59e0b' }}>
                    {[1, 2, 3, 4, 5].map(star => (
                      <Star key={star} size={15} fill={star <= item.rating ? '#f59e0b' : 'transparent'} />
                    ))}
                  </div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent'}
                  </span>
                </div>

                <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontStyle: 'italic', lineHeight: 1.5 }}>
                  "{item.comment || 'Excellent dining experience and courteous service.'}"
                </p>
              </div>

              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {item.customer_name || 'Guest'}
                </span>
                <span>Order #{item.order_id?.slice(-6) || 'Direct'}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Record Review Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '24px', maxWidth: '440px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Record Guest Review</h2>
              <button onClick={() => setShowModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateFeedback} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Related Order</label>
                <select value={orderId} onChange={e => setOrderId(e.target.value)} className="select">
                  {orders.map(o => (
                    <option key={o.id} value={o.id}>
                      Order #{o.order_number || o.id?.slice(-6)} - {o.customer_name || 'Guest'} (₹{parseFloat(o.total_amount || 0).toFixed(2)})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Guest Name</label>
                <input
                  type="text"
                  placeholder="e.g. Ananya Sen"
                  value={customerName}
                  onChange={e => setCustomerName(e.target.value)}
                  className="input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Rating (Stars)</label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {[1, 2, 3, 4, 5].map(s => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setRating(s)}
                      style={{
                        flex: 1,
                        padding: '8px',
                        background: rating >= s ? 'rgba(245, 158, 11, 0.2)' : 'var(--bg-tertiary)',
                        border: '1px solid',
                        borderColor: rating >= s ? '#f59e0b' : 'var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        color: rating >= s ? '#f59e0b' : 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Star size={16} fill={rating >= s ? '#f59e0b' : 'transparent'} />
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Review Comment *</label>
                <textarea
                  rows="3"
                  required
                  placeholder="The Biryani was exceptionally fragrant and the tandoori kebabs were hot and fresh!"
                  value={comment}
                  onChange={e => setComment(e.target.value)}
                  className="textarea"
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="btn btn-primary" style={{ flex: 1 }}>
                  {submitting ? 'Submitting...' : 'Submit Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
