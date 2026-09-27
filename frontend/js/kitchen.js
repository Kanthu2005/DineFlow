/**
 * Kitchen Display System (KDS) Module
 * Real-time chef and kitchen operations board.
 */

const KitchenDisplay = (() => {
  let tickets = [];
  let pollInterval = null;

  async function init() {
    await refresh();
    // Auto-refresh KDS tickets every 15 seconds
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(refresh, 15000);
  }

  async function refresh() {
    try {
      tickets = await API.kitchen.getTickets();
      renderBoard();
    } catch (e) {
      console.warn("Could not load kitchen tickets:", e);
      tickets = [];
      renderBoard();
    }
  }

  function renderBoard() {
    const queuedCol = document.getElementById("kds-col-queued");
    const preparingCol = document.getElementById("kds-col-preparing");
    const readyCol = document.getElementById("kds-col-ready");
    const completedCol = document.getElementById("kds-col-completed");

    if (!queuedCol || !preparingCol || !readyCol || !completedCol) return;

    const queuedTickets = tickets.filter(t => t.status === "QUEUED");
    const preparingTickets = tickets.filter(t => t.status === "PREPARING");
    const readyTickets = tickets.filter(t => t.status === "READY");
    const handedOverTickets = tickets.filter(t => t.status === "HANDED_OVER");

    // Update counts
    document.getElementById("kds-count-queued").textContent = queuedTickets.length;
    document.getElementById("kds-count-preparing").textContent = preparingTickets.length;
    document.getElementById("kds-count-ready").textContent = readyTickets.length;
    document.getElementById("kds-count-completed").textContent = handedOverTickets.length;

    queuedCol.innerHTML = renderTicketCards(queuedTickets, "QUEUED");
    preparingCol.innerHTML = renderTicketCards(preparingTickets, "PREPARING");
    readyCol.innerHTML = renderTicketCards(readyTickets, "READY");
    completedCol.innerHTML = renderTicketCards(handedOverTickets, "HANDED_OVER");
  }

  function getElapsedTimeBadge(createdAt) {
    if (!createdAt) return `<span class="ticket-timer">⏱️ Just now</span>`;
    const diffSec = Math.max(0, Math.floor((Date.now() - new Date(createdAt).getTime()) / 1000));
    const minutes = Math.floor(diffSec / 60);
    const seconds = diffSec % 60;
    const timeStr = `${minutes}m ${seconds < 10 ? '0' : ''}${seconds}s`;

    if (minutes >= 20) {
      return `<span class="ticket-timer urgent" title="Urgent ticket delay!">🚨 ${timeStr}</span>`;
    }
    if (minutes >= 10) {
      return `<span class="ticket-timer warning" title="Cooking in progress">⚠️ ${timeStr}</span>`;
    }
    return `<span class="ticket-timer" title="Normal queue time">⏱️ ${timeStr}</span>`;
  }

  function renderTicketCards(colTickets, columnStatus) {
    if (colTickets.length === 0) {
      return `<div style="text-align: center; color: var(--text-dim); padding: 2rem 0; font-size: 0.85rem;">No orders</div>`;
    }

    return colTickets.map(t => {
      const ticketId = t.id || t._id;
      const orderNum = t.order_number || (t.order_id ? `#${t.order_id.slice(-6)}` : 'Order');
      const priority = t.priority || "NORMAL";
      const items = t.order_items || [];
      const priorityClass = `priority-${priority}`;
      const timerBadge = getElapsedTimeBadge(t.created_at);

      let itemsHtml = items.map(i => `
        <div class="ticket-item-row" onclick="KitchenDisplay.toggleItemCheck(this)" title="Click to strike-through prepared item">
          <span><span class="ticket-item-qty">${i.quantity}×</span> ${escapeHtml(i.item_name_snapshot || 'Item')}</span>
          ${i.special_instructions ? `<span style="font-size: 0.7rem; color: var(--color-warning);">⚠️ ${escapeHtml(i.special_instructions)}</span>` : ''}
        </div>
      `).join("");

      if (items.length === 0) {
        itemsHtml = `<div style="color: var(--text-dim); font-size: 0.75rem;">Standard preparation</div>`;
      }

      let actionBtn = "";
      if (columnStatus === "QUEUED") {
        actionBtn = `<button class="btn btn-primary btn-sm" style="width: 100%;" onclick="KitchenDisplay.advanceStatus('${ticketId}', 'PREPARING')">🔥 Start Cooking</button>`;
      } else if (columnStatus === "PREPARING") {
        actionBtn = `<button class="btn btn-success btn-sm" style="width: 100%;" onclick="KitchenDisplay.advanceStatus('${ticketId}', 'READY')">✨ Mark Ready</button>`;
      } else if (columnStatus === "READY") {
        actionBtn = `<button class="btn btn-secondary btn-sm" style="width: 100%;" onclick="KitchenDisplay.advanceStatus('${ticketId}', 'HANDED_OVER')">🍽️ Hand Over</button>`;
      } else {
        actionBtn = `<span style="font-size: 0.72rem; color: var(--color-success); font-weight: 600;">✓ Completed</span>`;
      }

      return `
        <div class="ticket-card ${priorityClass}">
          <div class="ticket-header">
            <div>
              <div class="ticket-id">${orderNum}</div>
              <div style="display: flex; gap: 0.35rem; align-items: center; margin-top: 0.25rem;">
                <span class="badge ${getPriorityBadgeClass(priority)}">${priority}</span>
                ${timerBadge}
              </div>
            </div>
            <span class="ticket-time">${t.order_type || 'DINE_IN'}</span>
          </div>

          <div class="ticket-items-list">
            ${itemsHtml}
          </div>

          <div class="ticket-actions">
            ${actionBtn}
          </div>
        </div>
      `;
    }).join("");
  }

  function toggleItemCheck(el) {
    el.classList.toggle("is-done");
    if (window.Sound) Sound.click();
  }

  function getPriorityBadgeClass(priority) {
    if (priority === "URGENT") return "badge-red";
    if (priority === "HIGH") return "badge-amber";
    return "badge-blue";
  }

  async function advanceStatus(ticketId, newStatus) {
    try {
      App.showLoader(true);
      await API.kitchen.updateStatus(ticketId, newStatus);
      if (window.Sound) Sound.success();
      App.showToast(`Ticket moved to ${newStatus}`, "success");
      await refresh();
      if (window.OrdersList) OrdersList.refresh();
      if (window.Dashboard) Dashboard.refresh();
    } catch (e) {
      App.showToast(`Failed to update ticket: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  function openCreateTicketModal() {
    App.openModal("create-ticket-modal");
    // Load confirmed orders that don't have tickets yet
    loadEligibleOrders();
  }

  async function loadEligibleOrders() {
    const select = document.getElementById("ticket-order-select");
    if (!select) return;

    try {
      const orders = await API.orders.getAll();
      const eligible = orders.filter(o => o.status === "CONFIRMED");
      if (eligible.length === 0) {
        select.innerHTML = `<option value="">No confirmed orders waiting for kitchen</option>`;
      } else {
        select.innerHTML = eligible.map(o => `
          <option value="${o.id || o._id}">${o.order_number || o.id} (${o.order_type} - ₹${Number(o.total_amount?.$numberDecimal || o.total_amount || 0).toFixed(2)})</option>
        `).join("");
      }
    } catch (e) {
      console.warn("Could not load eligible orders:", e);
    }
  }

  async function submitNewTicket() {
    const orderId = document.getElementById("ticket-order-select")?.value;
    const priority = document.getElementById("ticket-priority-select")?.value || "NORMAL";

    if (!orderId) {
      App.showToast("Please choose an order", "warning");
      return;
    }

    try {
      App.showLoader(true);
      await API.kitchen.createTicket(orderId, priority);
      App.showToast("Kitchen Ticket created!", "success");
      App.closeModal("create-ticket-modal");
      await refresh();
    } catch (e) {
      App.showToast(`Failed: ${e.message}`, "error");
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
    advanceStatus,
    toggleItemCheck,
    openCreateTicketModal,
    submitNewTicket
  };
})();
