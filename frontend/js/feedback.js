/**
 * Customer Feedback & Ratings Module
 */

const FeedbackView = (() => {
  let reviews = [];
  let summary = null;

  async function init() {
    await refresh();
  }

  async function refresh() {
    await loadFeedback();
    await loadSummary();
    render();
  }

  async function loadFeedback() {
    try {
      reviews = await API.feedback.getAll();
    } catch (e) {
      console.warn("Could not load feedback:", e);
      reviews = [];
    }
  }

  async function loadSummary() {
    try {
      summary = await API.feedback.getSummary();
    } catch (e) {
      console.warn("Could not load feedback summary:", e);
      summary = null;
    }
  }

  function render() {
    renderSummary();
    renderReviews();
  }

  function renderSummary() {
    const avgEl = document.getElementById("feedback-avg-rating");
    const totalEl = document.getElementById("feedback-total-count");
    const foodEl = document.getElementById("feedback-food-rating");
    const serviceEl = document.getElementById("feedback-service-rating");

    if (summary) {
      if (avgEl) avgEl.textContent = Number(summary.average_rating || 5.0).toFixed(1);
      if (totalEl) totalEl.textContent = `${summary.total_feedback || reviews.length} reviews`;
      if (foodEl) foodEl.textContent = `Food: ${Number(summary.average_food_rating || 5.0).toFixed(1)}/5`;
      if (serviceEl) serviceEl.textContent = `Service: ${Number(summary.average_service_rating || 5.0).toFixed(1)}/5`;
    } else {
      if (avgEl) avgEl.textContent = "5.0";
      if (totalEl) totalEl.textContent = `${reviews.length} reviews`;
    }
  }

  function renderReviews() {
    const container = document.getElementById("feedback-cards-grid");
    if (!container) return;

    if (reviews.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-dim);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⭐</div>
          No customer reviews recorded yet.
        </div>`;
      return;
    }

    container.innerHTML = reviews.map(r => {
      const rating = r.rating || 5;
      const stars = "★".repeat(rating) + "☆".repeat(5 - rating);
      const dateStr = r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recent';

      return `
        <div class="glass-card" style="display: flex; flex-direction: column; gap: 0.5rem;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="star-rating">${stars}</span>
            <span style="font-size: 0.75rem; color: var(--text-dim);">${dateStr}</span>
          </div>
          <p style="font-size: 0.88rem; color: var(--text-main); font-style: italic;">
            "${escapeHtml(r.comments || 'Great experience, wonderful ambience and delicious food!')}"
          </p>
          <div style="font-size: 0.75rem; color: var(--text-dim); border-top: 1px solid var(--glass-border); padding-top: 0.5rem; margin-top: auto; display: flex; justify-content: space-between;">
            <span>Food: ${r.food_rating || 5}/5</span>
            <span>Service: ${r.service_rating || 5}/5</span>
          </div>
        </div>
      `;
    }).join("");
  }

  function openSubmitModal() {
    loadFeedbackOrderOptions();
    loadFeedbackCustomerOptions();
    App.openModal("submit-feedback-modal");
  }

  async function loadFeedbackOrderOptions() {
    const select = document.getElementById("fb-order-select");
    if (!select) return;
    try {
      const orders = await API.orders.getAll();
      select.innerHTML = orders.map(o => `
        <option value="${o.id || o._id}">${o.order_number || o.id} (${o.order_type})</option>
      `).join("");
    } catch (e) {
      console.warn("Could not load orders:", e);
    }
  }

  async function loadFeedbackCustomerOptions() {
    const select = document.getElementById("fb-customer-select");
    if (!select) return;
    try {
      const custs = await API.customers.getAll();
      select.innerHTML = custs.map(c => `
        <option value="${c.id || c._id}">${c.name}</option>
      `).join("");
    } catch (e) {
      console.warn("Could not load customers:", e);
    }
  }

  async function submitFeedback() {
    const orderId = document.getElementById("fb-order-select")?.value;
    const customerId = document.getElementById("fb-customer-select")?.value;
    const overall = parseInt(document.getElementById("fb-rating-overall")?.value || 5, 10);
    const food = parseInt(document.getElementById("fb-rating-food")?.value || 5, 10);
    const service = parseInt(document.getElementById("fb-rating-service")?.value || 5, 10);
    const comments = document.getElementById("fb-comments-input")?.value?.trim() || "";

    if (!orderId || !customerId) {
      App.showToast("Order and customer selection are required", "warning");
      return;
    }

    try {
      App.showLoader(true);
      await API.feedback.create(orderId, {
        customer_id: customerId,
        rating: overall,
        food_rating: food,
        service_rating: service,
        comments: comments || undefined
      });

      App.showToast("Thank you for your feedback!", "success");
      App.closeModal("submit-feedback-modal");
      await refresh();
    } catch (e) {
      App.showToast(`Feedback error: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  return {
    init,
    refresh,
    openSubmitModal,
    submitFeedback
  };
})();
