/**
 * Tables & Reservations Module
 * Visual Floor Plan & Booking Manager
 */

const TablesView = (() => {
  let tables = [];
  let reservations = [];
  let activeTab = "floor"; // "floor" or "reservations"

  async function init() {
    await refresh();
  }

  async function refresh() {
    await loadTables();
    await loadReservations();
    render();
  }

  async function loadTables() {
    try {
      tables = await API.tables.getAll();
    } catch (e) {
      console.warn("Could not load tables:", e);
      tables = [];
    }
  }

  async function loadReservations() {
    try {
      reservations = await API.reservations.getAll();
    } catch (e) {
      console.warn("Could not load reservations:", e);
      reservations = [];
    }
  }

  function setSubTab(tab) {
    activeTab = tab;
    document.querySelectorAll(".tables-subtab-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === tab);
    });
    document.getElementById("tables-floor-view").style.display = tab === "floor" ? "block" : "none";
    document.getElementById("tables-reservations-view").style.display = tab === "reservations" ? "block" : "none";
  }

  function render() {
    renderFloorPlan();
    renderReservations();
  }

  let tableFilter = "all";

  function setTableFilter(status) {
    tableFilter = status;
    document.querySelectorAll(".table-filter-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.status === status);
    });
    if (window.Sound) Sound.click();
    renderFloorPlan();
  }

  function renderFloorPlan() {
    const container = document.getElementById("tables-grid-container");
    const countTotal = document.getElementById("tables-count-all");
    const countAvail = document.getElementById("tables-count-avail");
    const countOcc = document.getElementById("tables-count-occ");
    const countRes = document.getElementById("tables-count-res");

    if (countTotal) countTotal.textContent = tables.length;
    if (countAvail) countAvail.textContent = tables.filter(t => t.status === "AVAILABLE").length;
    if (countOcc) countOcc.textContent = tables.filter(t => t.status === "OCCUPIED").length;
    if (countRes) countRes.textContent = tables.filter(t => t.status === "RESERVED").length;

    if (!container) return;

    let filtered = tables;
    if (tableFilter !== "all") {
      filtered = filtered.filter(t => t.status === tableFilter);
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-dim);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🪑</div>
          <p>No tables matching this filter.</p>
          <button class="btn btn-secondary btn-sm" style="margin-top: 1rem;" onclick="TablesView.setTableFilter('all')">Show All Tables</button>
        </div>`;
      return;
    }

    container.innerHTML = filtered.map(t => {
      const id = t.id || t._id;
      const status = t.status || "AVAILABLE";
      const statusClass = `status-${status}`;

      return `
        <div class="table-card ${statusClass}" onclick="TablesView.openTableStatusModal('${id}', '${status}', '${t.table_number}')">
          <div class="table-visual">
            T${t.table_number}
          </div>
          <div>
            <div class="table-num">Table ${t.table_number}</div>
            <div class="table-meta">Capacity: ${t.capacity} guests • ${t.location || 'Indoor'}</div>
          </div>
          <div>
            ${getTableStatusBadge(status)}
          </div>
          <div class="table-card-actions" onclick="event.stopPropagation()">
            ${status === 'AVAILABLE' ? `
              <button class="table-action-btn" onclick="POS.selectTable('${id}')">⚡ Seat & Order</button>
            ` : (status === 'OCCUPIED' ? `
              <button class="table-action-btn" onclick="App.switchView('billing')">🧾 Checkout</button>
            ` : `
              <button class="table-action-btn" onclick="TablesView.updateStatus('${id}', 'AVAILABLE')">🟢 Free Table</button>
            `)}
          </div>
        </div>
      `;
    }).join("");
  }

  function getTableStatusBadge(status) {
    switch (status) {
      case "AVAILABLE": return '<span class="badge badge-green">Available</span>';
      case "OCCUPIED": return '<span class="badge badge-red">Occupied</span>';
      case "RESERVED": return '<span class="badge badge-amber">Reserved</span>';
      case "OUT_OF_SERVICE": return '<span class="badge badge-muted">Out of Service</span>';
      default: return `<span class="badge badge-muted">${status}</span>`;
    }
  }

  function renderReservations() {
    const tableBody = document.getElementById("reservations-table-body");
    if (!tableBody) return;

    if (reservations.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-dim);">
            No upcoming reservations recorded.
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = reservations.map(r => {
      const id = r.id || r._id;
      const dateStr = r.reservation_date || '-';
      const timeStr = `${r.start_time || ''} - ${r.end_time || ''}`;
      const status = r.status || "CONFIRMED";

      return `
        <tr>
          <td style="font-weight: 600;">${dateStr}</td>
          <td>${timeStr}</td>
          <td style="font-weight: 600; color: var(--accent-primary);">Table ID: ${r.table_id ? r.table_id.slice(-4) : '-'}</td>
          <td>${r.guest_count} Guests</td>
          <td>${r.contact_number || '-'}</td>
          <td><span class="badge ${status === 'CONFIRMED' ? 'badge-green' : 'badge-muted'}">${status}</span></td>
          <td>
            <div style="display: flex; gap: 0.35rem;">
              <button class="btn btn-secondary btn-sm" onclick="TablesView.updateReservationStatus('${id}', 'CANCELLED')">Cancel</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  function openAddTableModal() {
    App.openModal("add-table-modal");
  }

  async function submitAddTable() {
    const tableNum = document.getElementById("table-num-input")?.value?.trim();
    const capacity = parseInt(document.getElementById("table-capacity-input")?.value, 10);
    const location = document.getElementById("table-location-input")?.value?.trim() || "Indoor";

    if (!tableNum || !capacity) {
      App.showToast("Table number and capacity are required", "warning");
      return;
    }

    try {
      App.showLoader(true);
      await API.tables.create({
        table_number: tableNum,
        capacity,
        location,
        is_active: true
      });
      App.showToast(`Table ${tableNum} registered!`, "success");
      App.closeModal("add-table-modal");
      await refresh();
      if (window.POS) POS.refresh();
    } catch (e) {
      App.showToast(`Error creating table: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  function openTableStatusModal(tableId, currentStatus, tableNum) {
    const modalContent = document.getElementById("table-status-modal-content");
    if (!modalContent) return;

    modalContent.innerHTML = `
      <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="font-size: 2.5rem; margin-bottom: 0.25rem;">🪑</div>
        <h3 style="font-size: 1.35rem; font-weight: 700; color: #ffffff;">Table ${tableNum}</h3>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem;">Current Status: ${getTableStatusBadge(currentStatus)}</p>
      </div>

      <div style="margin-bottom: 1.25rem;">
        <button class="btn btn-primary" style="width: 100%; justify-content: center; padding: 0.75rem; font-size: 0.95rem; margin-bottom: 0.5rem;" onclick="App.closeModal('table-status-modal'); POS.selectTable('${tableId}');">
          🛒 Start New Order for Table ${tableNum}
        </button>
      </div>

      <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--text-dim); margin-bottom: 0.5rem;">Quick Status Change:</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem;">
        <button class="btn btn-success btn-sm" onclick="TablesView.updateStatus('${tableId}', 'AVAILABLE')">🟢 Mark Available</button>
        <button class="btn btn-danger btn-sm" onclick="TablesView.updateStatus('${tableId}', 'OCCUPIED')">🔴 Mark Occupied</button>
        <button class="btn btn-secondary btn-sm" onclick="TablesView.updateStatus('${tableId}', 'RESERVED')">🟡 Mark Reserved</button>
        <button class="btn btn-secondary btn-sm" onclick="TablesView.updateStatus('${tableId}', 'OUT_OF_SERVICE')">⚪ Out of Service</button>
      </div>
    `;

    App.openModal("table-status-modal");
  }

  async function updateStatus(tableId, status) {
    try {
      App.showLoader(true);
      await API.tables.updateStatus(tableId, status);
      App.showToast(`Table marked as ${status}`, "success");
      App.closeModal("table-status-modal");
      await refresh();
    } catch (e) {
      App.showToast(`Failed to update table: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  function openNewReservationModal() {
    loadReservationTableOptions();
    loadReservationCustomerOptions();
    App.openModal("new-reservation-modal");
  }

  async function loadReservationTableOptions() {
    const select = document.getElementById("res-table-select");
    if (!select) return;
    try {
      const avail = await API.tables.getAll();
      select.innerHTML = avail.map(t => `<option value="${t.id || t._id}">Table ${t.table_number} (${t.capacity} seats)</option>`).join("");
    } catch (e) {
      console.warn("Could not load table options:", e);
    }
  }

  async function loadReservationCustomerOptions() {
    const select = document.getElementById("res-customer-select");
    if (!select) return;
    try {
      const custs = await API.customers.getAll();
      select.innerHTML = custs.map(c => `<option value="${c.id || c._id}">${c.name} (${c.phone})</option>`).join("");
    } catch (e) {
      console.warn("Could not load customer options:", e);
    }
  }

  async function submitReservation() {
    const customerId = document.getElementById("res-customer-select")?.value;
    const tableId = document.getElementById("res-table-select")?.value;
    const resDate = document.getElementById("res-date-input")?.value;
    const startTime = document.getElementById("res-start-time")?.value;
    const endTime = document.getElementById("res-end-time")?.value;
    const guests = parseInt(document.getElementById("res-guests-input")?.value, 10);
    const phone = document.getElementById("res-phone-input")?.value?.trim();

    if (!customerId || !tableId || !resDate || !startTime || !endTime || !guests || !phone) {
      App.showToast("All reservation fields are required", "warning");
      return;
    }

    try {
      App.showLoader(true);
      await API.reservations.create({
        customer_id: customerId,
        table_id: tableId,
        reservation_date: resDate,
        start_time: startTime + ":00",
        end_time: endTime + ":00",
        guest_count: guests,
        contact_number: phone
      });
      App.showToast("Reservation confirmed!", "success");
      App.closeModal("new-reservation-modal");
      await refresh();
    } catch (e) {
      App.showToast(`Reservation error: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  async function updateReservationStatus(resId, status) {
    try {
      App.showLoader(true);
      await API.reservations.update(resId, { status });
      App.showToast(`Reservation ${status}`, "success");
      await refresh();
    } catch (e) {
      App.showToast(`Error: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  return {
    init,
    refresh,
    setSubTab,
    setTableFilter,
    openAddTableModal,
    submitAddTable,
    openTableStatusModal,
    updateStatus,
    openNewReservationModal,
    submitReservation,
    updateReservationStatus
  };
})();
