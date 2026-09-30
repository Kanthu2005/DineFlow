/**
 * Orders Management Module (All Active & Historical Orders)
 */

const OrdersList = (() => {
  let orders = [];
  let filterStatus = "all";
  let searchQuery = "";

  async function init() {
    await refresh();
  }

  async function refresh() {
    try {
      orders = await API.orders.getAll();
      renderOrders();
    } catch (e) {
      console.warn("Could not load orders:", e);
      orders = [];
      renderOrders();
    }
  }

  function setFilter(status) {
    filterStatus = status;
    if (window.Sound) Sound.click();
    renderOrders();
  }

  function searchOrders(q) {
    searchQuery = q.toLowerCase().trim();
    renderOrders();
  }

  function renderOrders() {
    const tableBody = document.getElementById("orders-table-body");
    const countBadge = document.getElementById("orders-total-count");
    if (!tableBody) return;

    let filtered = orders;
    if (filterStatus !== "all") {
      filtered = filtered.filter(o => o.status === filterStatus);
    }

    if (searchQuery) {
      filtered = filtered.filter(o => {
        const num = (o.order_number || o.id || o._id || "").toLowerCase();
        const type = (o.order_type || "").toLowerCase();
        const status = (o.status || "").toLowerCase();
        return num.includes(searchQuery) || type.includes(searchQuery) || status.includes(searchQuery);
      });
    }

    if (countBadge) countBadge.textContent = `${filtered.length} Orders`;

    if (filtered.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-dim);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📋</div>
            No orders found matching this filter.
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = filtered.map(order => {
      const orderId = order.id || order._id;
      const orderNum = order.order_number || `#${orderId.slice(-6)}`;
      const total = Number(order.total_amount?.$numberDecimal || order.total_amount || 0).toFixed(2);
      const statusBadge = getStatusBadge(order.status);
      const orderType = order.order_type || "DINE_IN";
      const createdDate = order.created_at ? new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-';

      return `
        <tr>
          <td style="font-weight: 700; color: var(--accent-primary);">${orderNum}</td>
          <td><span class="badge badge-muted">${orderType}</span></td>
          <td>${order.table_id ? `Table ID: ${order.table_id.slice(-4)}` : 'Takeaway/Bar'}</td>
          <td style="font-weight: 700;">₹${total}</td>
          <td>${statusBadge}</td>
          <td style="font-size: 0.78rem; color: var(--text-dim);">${createdDate}</td>
          <td>
            <div style="display: flex; gap: 0.4rem;">
              <button class="btn btn-secondary btn-sm" onclick="OrdersList.viewDetails('${orderId}')">Details</button>
              ${order.status === 'CONFIRMED' ? `
                <button class="btn btn-primary btn-sm" onclick="OrdersList.sendToKitchen('${orderId}')">Send to Kitchen</button>
              ` : ''}
              ${order.status === 'READY' || order.status === 'SERVED' ? `
                <button class="btn btn-success btn-sm" onclick="OrdersList.quickInvoice('${orderId}')">Bill / Invoice</button>
              ` : ''}
              <button class="btn btn-secondary btn-sm" onclick="OrdersList.openDiscountModal('${orderId}')">Discount</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  function getStatusBadge(status) {
    switch (status) {
      case "DRAFT": return '<span class="badge badge-muted">Draft</span>';
      case "CONFIRMED": return '<span class="badge badge-blue">Confirmed</span>';
      case "SENT_TO_KITCHEN": return '<span class="badge badge-amber">In Kitchen</span>';
      case "PREPARING": return '<span class="badge badge-purple">Preparing</span>';
      case "READY": return '<span class="badge badge-green">Ready</span>';
      case "SERVED": return '<span class="badge badge-green">Served</span>';
      case "COMPLETED": return '<span class="badge badge-green">Completed</span>';
      case "CANCELLED": return '<span class="badge badge-red">Cancelled</span>';
      default: return `<span class="badge badge-muted">${status || 'Unknown'}</span>`;
    }
  }

  async function viewDetails(orderId) {
    try {
      App.showLoader(true);
      const order = await API.orders.getOne(orderId);
      const items = await API.orders.getItems(orderId);

      const modalContent = document.getElementById("order-details-modal-content");
      if (!modalContent) return;

      const subtotal = Number(order.subtotal?.$numberDecimal || order.subtotal || 0).toFixed(2);
      const tax = Number(order.tax_amount?.$numberDecimal || order.tax_amount || 0).toFixed(2);
      const discount = Number(order.discount_amount?.$numberDecimal || order.discount_amount || 0).toFixed(2);
      const total = Number(order.total_amount?.$numberDecimal || order.total_amount || 0).toFixed(2);

      let itemsHtml = items.map(item => {
        const itemTotal = Number(item.item_total?.$numberDecimal || item.item_total || 0).toFixed(2);
        const unitPrice = Number(item.unit_price_snapshot?.$numberDecimal || item.unit_price_snapshot || 0).toFixed(2);
        return `
          <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--glass-border);">
            <div>
              <div style="font-weight: 600;">${item.item_name_snapshot}</div>
              <div style="font-size: 0.75rem; color: var(--text-dim);">${item.quantity} × ₹${unitPrice}</div>
            </div>
            <div style="font-weight: 700; color: var(--accent-primary);">₹${itemTotal}</div>
          </div>
        `;
      }).join("");

      if (items.length === 0) {
        itemsHtml = `<div style="text-align: center; color: var(--text-dim); padding: 1rem;">No items attached to this order.</div>`;
      }

      modalContent.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--glass-border);">
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--accent-primary);">${order.order_number || orderId}</h3>
            <span style="font-size: 0.8rem; color: var(--text-dim);">Type: ${order.order_type}</span>
          </div>
          <div>${getStatusBadge(order.status)}</div>
        </div>

        <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;">Ordered Dishes</h4>
        <div style="margin-bottom: 1.25rem;">
          ${itemsHtml}
        </div>

        <div style="background: rgba(0,0,0,0.3); border-radius: var(--radius-md); padding: 0.85rem; font-size: 0.85rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
            <span>Subtotal:</span>
            <span>₹${subtotal}</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
            <span>Tax (5%):</span>
            <span>₹${tax}</span>
          </div>
          ${discount > 0 ? `
            <div style="display: flex; justify-content: space-between; color: var(--color-success); margin-bottom: 0.3rem;">
              <span>Discount:</span>
              <span>-₹${discount}</span>
            </div>
          ` : ''}
          <div style="display: flex; justify-content: space-between; font-weight: 800; font-size: 1rem; border-top: 1px dashed var(--glass-border); padding-top: 0.5rem; margin-top: 0.5rem;">
            <span>Grand Total:</span>
            <span style="color: var(--accent-primary);">₹${total}</span>
          </div>
        </div>

        <div style="margin-top: 1.25rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
          <button class="btn btn-secondary btn-sm" onclick="OrdersList.updateStatus('${orderId}', 'CONFIRMED')">Set Confirmed</button>
          <button class="btn btn-secondary btn-sm" onclick="OrdersList.updateStatus('${orderId}', 'SERVED')">Set Served</button>
          <button class="btn btn-secondary btn-sm" onclick="OrdersList.updateStatus('${orderId}', 'COMPLETED')">Set Completed</button>
          <button class="btn btn-danger btn-sm" onclick="OrdersList.updateStatus('${orderId}', 'CANCELLED')">Cancel Order</button>
        </div>
      `;

      App.openModal("order-details-modal");
    } catch (err) {
      App.showToast(`Failed to load order: ${err.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  async function updateStatus(orderId, status) {
    try {
      App.showLoader(true);
      await API.orders.updateStatus(orderId, status);
      App.showToast(`Order status updated to ${status}`, "success");
      App.closeModal("order-details-modal");
      await refresh();
      if (window.KitchenDisplay) KitchenDisplay.refresh();
      if (window.Dashboard) Dashboard.refresh();
    } catch (e) {
      App.showToast(`Error updating status: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  async function sendToKitchen(orderId) {
    try {
      App.showLoader(true);
      await API.kitchen.createTicket(orderId, "NORMAL");
      if (window.Sound) Sound.success();
      App.showToast("Order ticket pushed to Kitchen KDS!", "success");
      await refresh();
      if (window.KitchenDisplay) KitchenDisplay.refresh();
    } catch (e) {
      if (e.message && e.message.includes("already exists")) {
        App.showToast("Kitchen ticket is already active on KDS board", "info");
      } else {
        if (window.Sound) Sound.error();
        App.showToast(`Failed to dispatch to kitchen: ${e.message}`, "error");
      }
    } finally {
      App.showLoader(false);
    }
  }

  async function quickInvoice(orderId) {
    try {
      App.showLoader(true);
      const inv = await API.billing.createInvoice(orderId);
      App.showToast(`Invoice ${inv.invoice_number} created!`, "success");
      App.switchView("billing");
      if (window.BillingView) BillingView.refresh();
    } catch (e) {
      if (e.message.includes("already exists")) {
        App.showToast("Invoice already generated for this order.", "info");
        App.switchView("billing");
      } else {
        App.showToast(`Invoice error: ${e.message}`, "error");
      }
    } finally {
      App.showLoader(false);
    }
  }

  function openDiscountModal(orderId) {
    const hiddenInput = document.getElementById("discount-order-id");
    if (hiddenInput) hiddenInput.value = orderId;
    App.openModal("discount-modal");
  }

  async function applyDiscount() {
    const orderId = document.getElementById("discount-order-id")?.value;
    const amount = Number(document.getElementById("discount-amount-input")?.value || 0);

    if (!orderId || amount < 0) {
      App.showToast("Enter a valid discount amount", "warning");
      return;
    }

    try {
      App.showLoader(true);
      await API.orders.updateDiscount(orderId, { discount_amount: amount });
      await API.orders.recalculate(orderId);
      App.showToast(`Discount of ₹${amount.toFixed(2)} applied!`, "success");
      App.closeModal("discount-modal");
      await refresh();
    } catch (e) {
      App.showToast(`Failed to apply discount: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  return {
    init,
    refresh,
    setFilter,
    searchOrders,
    viewDetails,
    updateStatus,
    sendToKitchen,
    quickInvoice,
    openDiscountModal,
    applyDiscount
  };
})();
