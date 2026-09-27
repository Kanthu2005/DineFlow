/**
 * Billing, Invoicing & Payments Module
 * Complete support for GST Tax Invoices, Real-time Line Item Breakdown,
 * Quick Cash Tendered Calculation, and Direct Order Invoicing.
 */

const BillingView = (() => {
  let invoices = [];
  let filterStatus = "all";
  let cachedOrders = [];

  async function init() {
    await refresh();
  }

  async function refresh() {
    try {
      invoices = await API.billing.getInvoices();
      renderInvoices();
    } catch (e) {
      console.warn("Could not load invoices:", e);
      invoices = [];
      renderInvoices();
    }
  }

  function setFilter(status) {
    filterStatus = status;
    renderInvoices();
  }

  function renderInvoices() {
    const tableBody = document.getElementById("invoices-table-body");
    const countBadge = document.getElementById("invoices-total-count");

    // Update Billing Stats Cards
    const statTotal = document.getElementById("billing-stat-total-invoices");
    const statRevenue = document.getElementById("billing-stat-revenue");
    const statPending = document.getElementById("billing-stat-pending");
    const statUnpaidCount = document.getElementById("billing-stat-unpaid-count");

    const totalCount = invoices.length;
    let totalRevenue = 0;
    let totalPending = 0;
    let unpaidCount = 0;

    invoices.forEach(inv => {
      const amt = Number(inv.total_amount?.$numberDecimal || inv.total_amount || 0);
      if (inv.status === "PAID") {
        totalRevenue += amt;
      } else {
        totalPending += amt;
        unpaidCount += 1;
      }
    });

    if (statTotal) statTotal.textContent = totalCount;
    if (statRevenue) statRevenue.textContent = `₹${totalRevenue.toFixed(2)}`;
    if (statPending) statPending.textContent = `₹${totalPending.toFixed(2)}`;
    if (statUnpaidCount) statUnpaidCount.textContent = `${unpaidCount} unpaid invoices`;

    if (!tableBody) return;

    let filtered = invoices;
    if (filterStatus !== "all") {
      filtered = filtered.filter(i => i.status === filterStatus);
    }

    if (countBadge) countBadge.textContent = `${filtered.length} Invoices`;

    if (filtered.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-dim);">
            <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🧾</div>
            <div style="font-size: 1rem; font-weight: 600; color: #fff; margin-bottom: 0.25rem;">No invoices found</div>
            <span style="font-size: 0.82rem; color: var(--text-dim);">Click "+ Generate Invoice" to create a bill from an active order.</span>
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = filtered.map(inv => {
      const invId = inv.id || inv._id;
      const invNum = inv.invoice_number || `INV-${invId.slice(-6)}`;
      const orderNum = inv.order_number || (inv.order_id ? `#${inv.order_id.slice(-6)}` : '-');
      const total = Number(inv.total_amount?.$numberDecimal || inv.total_amount || 0).toFixed(2);
      const subtotal = Number(inv.subtotal?.$numberDecimal || inv.subtotal || 0).toFixed(2);
      const dateStr = inv.generated_at ? new Date(inv.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-';
      const statusBadge = getInvoiceBadge(inv.status);

      return `
        <tr>
          <td style="font-weight: 700; color: var(--accent-primary);">${invNum}</td>
          <td style="font-weight: 600;">${orderNum}</td>
          <td>₹${subtotal}</td>
          <td style="font-weight: 700; font-size: 0.95rem; color: #10b981;">₹${total}</td>
          <td>${statusBadge}</td>
          <td style="font-size: 0.78rem; color: var(--text-dim);">${dateStr}</td>
          <td>
            <div style="display: flex; gap: 0.4rem; align-items: center;">
              <button class="btn btn-secondary btn-sm" onclick="BillingView.viewReceipt('${invId}')" title="Print/View Tax Invoice" style="font-size: 0.78rem; padding: 0.35rem 0.65rem;">
                🧾 Tax Invoice
              </button>
              ${inv.status !== 'PAID' ? `
                <button class="btn btn-primary btn-sm" onclick="BillingView.openPaymentModal('${invId}', ${total})" title="Collect & Settle Payment" style="font-size: 0.78rem; padding: 0.35rem 0.7rem; background: linear-gradient(135deg, #10b981, #059669); font-weight: 700;">
                  💳 Pay
                </button>
              ` : `
                <span class="badge badge-green" style="align-self: center; font-weight: 700;">✓ Settled</span>
              `}
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  function getInvoiceBadge(status) {
    switch (status) {
      case "PAID": return '<span class="badge badge-green">Paid</span>';
      case "PARTIALLY_PAID": return '<span class="badge badge-amber">Partially Paid</span>';
      case "UNPAID": return '<span class="badge badge-red">Unpaid</span>';
      default: return `<span class="badge badge-muted">${status || 'Unknown'}</span>`;
    }
  }

  let currentTotalDue = 0;

  async function openPaymentModal(invoiceId, totalAmount) {
    currentTotalDue = Number(totalAmount || 0);
    const invInput = document.getElementById("pay-invoice-id");
    const amountInput = document.getElementById("pay-amount-input");
    const changeBox = document.getElementById("pay-change-box");

    // Live Breakdown Elements
    const invNumEl = document.getElementById("pay-invoice-num");
    const tableTextEl = document.getElementById("pay-invoice-table-text");
    const statusBadgeEl = document.getElementById("pay-invoice-status-badge");
    const itemsListEl = document.getElementById("pay-invoice-items-list");
    const subtotalEl = document.getElementById("pay-invoice-subtotal");
    const taxEl = document.getElementById("pay-invoice-tax");
    const discountRow = document.getElementById("pay-invoice-discount-row");
    const discountEl = document.getElementById("pay-invoice-discount");
    const grandtotalEl = document.getElementById("pay-invoice-grandtotal");

    if (invInput) invInput.value = invoiceId;
    if (amountInput) {
      amountInput.value = currentTotalDue.toFixed(2);
      amountInput.oninput = calculateChange;
    }
    if (changeBox) changeBox.style.display = "none";

    // Set initial loading state for invoice breakdown
    if (invNumEl) invNumEl.textContent = "Loading Invoice...";
    if (tableTextEl) tableTextEl.textContent = "";
    if (itemsListEl) itemsListEl.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 0.5rem;">Fetching invoice items...</div>`;
    if (subtotalEl) subtotalEl.textContent = `₹${currentTotalDue.toFixed(2)}`;
    if (taxEl) taxEl.textContent = "₹0.00";
    if (grandtotalEl) grandtotalEl.textContent = `₹${currentTotalDue.toFixed(2)}`;

    if (window.Sound) Sound.pop();
    App.openModal("payment-modal");

    // Fetch full invoice & order item details
    try {
      const inv = await API.billing.getInvoice(invoiceId);
      const subtotal = Number(inv.subtotal?.$numberDecimal || inv.subtotal || 0).toFixed(2);
      const tax = Number(inv.tax_amount?.$numberDecimal || inv.tax_amount || 0).toFixed(2);
      const discount = Number(inv.discount_amount?.$numberDecimal || inv.discount_amount || 0).toFixed(2);
      const total = Number(inv.total_amount?.$numberDecimal || inv.total_amount || 0).toFixed(2);
      currentTotalDue = parseFloat(total);

      if (amountInput) {
        amountInput.value = currentTotalDue.toFixed(2);
        calculateChange();
      }

      if (invNumEl) invNumEl.textContent = inv.invoice_number || `INV-${invoiceId.slice(-6)}`;
      if (statusBadgeEl) {
        statusBadgeEl.className = inv.status === 'PAID' ? 'badge badge-green' : 'badge badge-amber';
        statusBadgeEl.textContent = inv.status || 'UNPAID';
      }
      if (subtotalEl) subtotalEl.textContent = `₹${subtotal}`;
      if (taxEl) taxEl.textContent = `₹${tax}`;
      if (grandtotalEl) grandtotalEl.textContent = `₹${total}`;

      if (Number(discount) > 0 && discountRow && discountEl) {
        discountRow.style.display = "flex";
        discountEl.textContent = `-₹${discount}`;
      } else if (discountRow) {
        discountRow.style.display = "none";
      }

      // Fetch items and table
      if (inv.order_id) {
        const [items, order] = await Promise.all([
          API.orders.getItems(inv.order_id).catch(() => []),
          API.orders.getOne(inv.order_id).catch(() => null)
        ]);

        if (tableTextEl && order) {
          const tNum = order.table_id?.table_number || order.table_id || "Takeaway";
          tableTextEl.textContent = `(Table #${tNum} • Order #${order.order_number || order.id?.slice(-6)})`;
        }

        if (itemsListEl) {
          if (items.length > 0) {
            itemsListEl.innerHTML = items.map(item => {
              const iTotal = Number(item.item_total?.$numberDecimal || item.item_total || 0).toFixed(2);
              return `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.2rem 0; border-bottom: 1px dotted rgba(255,255,255,0.06);">
                  <span style="color: var(--text-main); font-weight: 500;">
                    ${item.quantity}× ${item.item_name_snapshot || 'Item'}
                  </span>
                  <span style="font-weight: 600; color: #fff;">₹${iTotal}</span>
                </div>
              `;
            }).join("");
          } else {
            itemsListEl.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 0.35rem;">Dining order item(s)</div>`;
          }
        }
      }
    } catch (err) {
      console.warn("Could not fetch full invoice details for modal:", err);
    }
  }

  function calculateChange() {
    const amountInput = document.getElementById("pay-amount-input");
    const changeBox = document.getElementById("pay-change-box");
    const changeVal = document.getElementById("pay-change-value");
    if (!amountInput || !changeBox || !changeVal) return;

    const tendered = Number(amountInput.value || 0);
    if (tendered > currentTotalDue) {
      const change = tendered - currentTotalDue;
      changeVal.textContent = `₹${change.toFixed(2)}`;
      changeBox.style.display = "flex";
    } else {
      changeBox.style.display = "none";
    }
  }

  function setQuickCash(amount) {
    const amountInput = document.getElementById("pay-amount-input");
    if (amountInput) {
      amountInput.value = amount.toFixed(2);
      calculateChange();
    }
    if (window.Sound) Sound.click();
  }

  function setExactCash() {
    const amountInput = document.getElementById("pay-amount-input");
    if (amountInput) {
      amountInput.value = Number(currentTotalDue || 0).toFixed(2);
      calculateChange();
    }
    if (window.Sound) Sound.click();
  }

  async function submitPayment() {
    const invoiceId = document.getElementById("pay-invoice-id")?.value;
    const amount = Number(document.getElementById("pay-amount-input")?.value || 0);
    const method = document.getElementById("pay-method-select")?.value || "CASH";
    const ref = document.getElementById("pay-ref-input")?.value?.trim() || null;
    const user = API.getCurrentUser();

    if (!invoiceId || amount <= 0) {
      App.showToast("Enter a valid payment amount", "warning");
      return;
    }

    try {
      App.showLoader(true);
      await API.billing.createPayment({
        invoice_id: invoiceId,
        amount: amount,
        payment_method: method,
        transaction_reference: ref || `TXN-${Date.now().toString().slice(-6)}`,
        recorded_by: user?.email || user?.name || "cashier_staff"
      });

      if (window.Sound) Sound.cash();
      App.showToast("Payment recorded successfully!", "success");
      App.closeModal("payment-modal");
      await refresh();
      if (window.OrdersList) OrdersList.refresh();
      if (window.Dashboard) Dashboard.refresh();
      if (window.TablesView) TablesView.refresh();

      // Show receipt right after payment
      setTimeout(() => {
        viewReceipt(invoiceId);
      }, 350);
    } catch (e) {
      App.showToast(`Payment failed: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  // ================= GENERATE INVOICE WORKFLOW =================
  async function openCreateInvoiceModal() {
    const select = document.getElementById("invoice-order-select");
    const previewContainer = document.getElementById("invoice-order-preview-container");
    const noOrderAlert = document.getElementById("invoice-no-order-alert");
    const submitBtn = document.getElementById("btn-submit-generate-invoice");

    if (previewContainer) previewContainer.style.display = "none";
    if (noOrderAlert) noOrderAlert.style.display = "none";

    try {
      App.showLoader(true);
      const [allOrders, allInvoices] = await Promise.all([
        API.orders.getAll().catch(() => []),
        API.billing.getInvoices().catch(() => [])
      ]);

      cachedOrders = allOrders || [];
      const invoicedOrderIds = new Set(allInvoices.map(i => i.order_id).filter(Boolean));

      // Eligible orders: active/completed orders that don't have an invoice yet (or unbilled)
      const eligible = cachedOrders.filter(o => o.status !== "CANCELLED" && !invoicedOrderIds.has(o.id || o._id));

      if (select) {
        if (eligible.length === 0) {
          select.innerHTML = `<option value="">-- No pending orders to bill --</option>`;
          if (noOrderAlert) noOrderAlert.style.display = "block";
          if (submitBtn) submitBtn.disabled = true;
        } else {
          if (submitBtn) submitBtn.disabled = false;
          select.innerHTML = `
            <option value="">-- Choose active or unbilled order --</option>
            ${eligible.map(o => {
              const oId = o.id || o._id;
              const oNum = o.order_number || `#${oId.slice(-6)}`;
              const tNum = o.table_id?.table_number || o.table_id || "Takeaway";
              const total = Number(o.total_amount?.$numberDecimal || o.total_amount || 0).toFixed(2);
              return `<option value="${oId}">Order ${oNum} — Table #${tNum} (₹${total}) [${o.status}]</option>`;
            }).join("")}
          `;
          // Select first by default if exists
          if (eligible.length > 0) {
            select.value = eligible[0].id || eligible[0]._id;
            onSelectOrderForInvoice(select.value);
          }
        }
      }

      App.openModal("create-invoice-modal");
    } catch (e) {
      App.showToast(`Error preparing invoice options: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  async function onSelectOrderForInvoice(orderId) {
    const previewContainer = document.getElementById("invoice-order-preview-container");
    if (!orderId) {
      if (previewContainer) previewContainer.style.display = "none";
      return;
    }

    try {
      const [order, items] = await Promise.all([
        API.orders.getOne(orderId).catch(() => null),
        API.orders.getItems(orderId).catch(() => [])
      ]);

      if (!order) return;

      const orderNumEl = document.getElementById("inv-preview-order-num");
      const tableTextEl = document.getElementById("inv-preview-table-text");
      const typeEl = document.getElementById("inv-preview-type");
      const itemsListEl = document.getElementById("inv-preview-items-list");
      const subtotalEl = document.getElementById("inv-preview-subtotal");
      const taxEl = document.getElementById("inv-preview-tax");
      const discountRow = document.getElementById("inv-preview-discount-row");
      const discountEl = document.getElementById("inv-preview-discount");
      const grandtotalEl = document.getElementById("inv-preview-grandtotal");

      const subtotal = Number(order.subtotal?.$numberDecimal || order.subtotal || 0).toFixed(2);
      const tax = Number(order.tax_amount?.$numberDecimal || order.tax_amount || 0).toFixed(2);
      const discount = Number(order.discount_amount?.$numberDecimal || order.discount_amount || 0).toFixed(2);
      const total = Number(order.total_amount?.$numberDecimal || order.total_amount || 0).toFixed(2);

      if (orderNumEl) orderNumEl.textContent = `Order ${order.order_number || '#' + orderId.slice(-6)}`;
      if (tableTextEl) {
        const tNum = order.table_id?.table_number || order.table_id || "Counter";
        tableTextEl.textContent = `Table #${tNum}`;
      }
      if (typeEl) typeEl.textContent = order.order_type || "DINE_IN";
      if (subtotalEl) subtotalEl.textContent = `₹${subtotal}`;
      if (taxEl) taxEl.textContent = `₹${tax}`;
      if (grandtotalEl) grandtotalEl.textContent = `₹${total}`;

      if (Number(discount) > 0 && discountRow && discountEl) {
        discountRow.style.display = "flex";
        discountEl.textContent = `-₹${discount}`;
      } else if (discountRow) {
        discountRow.style.display = "none";
      }

      if (itemsListEl) {
        if (items.length > 0) {
          itemsListEl.innerHTML = items.map(i => {
            const lineTotal = Number(i.item_total?.$numberDecimal || i.item_total || 0).toFixed(2);
            return `
              <div style="display: flex; justify-content: space-between; padding: 0.25rem 0; border-bottom: 1px dotted rgba(255,255,255,0.07);">
                <span>${i.quantity}× ${i.item_name_snapshot}</span>
                <span style="font-weight: 600; color: #fff;">₹${lineTotal}</span>
              </div>
            `;
          }).join("");
        } else {
          itemsListEl.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 0.5rem;">Standard Dining Order</div>`;
        }
      }

      if (previewContainer) previewContainer.style.display = "block";
    } catch (e) {
      console.warn("Could not load preview for order:", e);
    }
  }

  async function submitGenerateInvoice() {
    const select = document.getElementById("invoice-order-select");
    const orderId = select?.value;

    if (!orderId) {
      App.showToast("Please choose an order to generate invoice", "warning");
      return;
    }

    try {
      App.showLoader(true);
      const inv = await API.billing.createInvoice(orderId);
      App.showToast(`🧾 Invoice ${inv.invoice_number || 'created'} generated successfully!`, "success");
      App.closeModal("create-invoice-modal");
      await refresh();

      const invId = inv.id || inv._id;
      const total = Number(inv.total_amount?.$numberDecimal || inv.total_amount || 0);

      // Offer to settle payment or view invoice
      setTimeout(() => {
        openPaymentModal(invId, total);
      }, 350);
    } catch (e) {
      App.showToast(`Error creating invoice: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  // ================= REAL-WORLD GST TAX INVOICE & RECEIPT =================
  async function viewReceipt(invoiceId) {
    try {
      App.showLoader(true);
      const inv = await API.billing.getInvoice(invoiceId);
      const order = inv.order_id ? await API.orders.getOne(inv.order_id).catch(() => null) : null;
      const items = inv.order_id ? await API.orders.getItems(inv.order_id).catch(() => []) : [];

      const receiptContent = document.getElementById("receipt-modal-content");
      if (!receiptContent) return;

      const subtotal = Number(inv.subtotal?.$numberDecimal || inv.subtotal || 0).toFixed(2);
      const tax = Number(inv.tax_amount?.$numberDecimal || inv.tax_amount || 0).toFixed(2);
      const cgst = (parseFloat(tax) / 2).toFixed(2);
      const sgst = (parseFloat(tax) / 2).toFixed(2);
      const discount = Number(inv.discount_amount?.$numberDecimal || inv.discount_amount || 0).toFixed(2);
      const total = Number(inv.total_amount?.$numberDecimal || inv.total_amount || 0).toFixed(2);

      const tableNum = order?.table_id?.table_number || order?.table_id || "Counter";
      const orderNumber = order?.order_number || (order?.id ? `#${order.id.slice(-6)}` : "WALK-IN");
      const invNumber = inv.invoice_number || `INV-${invoiceId.slice(-6)}`;
      const dateFormatted = new Date(inv.generated_at || Date.now()).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
      });
      const timeFormatted = new Date(inv.generated_at || Date.now()).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true
      });

      let itemsHtml = items.map((item, idx) => {
        const itemTotal = Number(item.item_total?.$numberDecimal || item.item_total || 0).toFixed(2);
        const unitPrice = Number(item.unit_price?.$numberDecimal || item.unit_price || 0).toFixed(2);
        return `
          <tr style="border-bottom: 1px dashed #e5e7eb;">
            <td style="padding: 4px 2px; text-align: left;">${item.item_name_snapshot}</td>
            <td style="padding: 4px 2px; text-align: center; color: #6b7280; font-size: 0.7rem;">996331</td>
            <td style="padding: 4px 2px; text-align: center;">${item.quantity}</td>
            <td style="padding: 4px 2px; text-align: right;">₹${unitPrice}</td>
            <td style="padding: 4px 2px; text-align: right; font-weight: 700;">₹${itemTotal}</td>
          </tr>
        `;
      }).join("");

      if (items.length === 0) {
        itemsHtml = `
          <tr>
            <td colspan="5" style="text-align: center; color: #6b7280; padding: 10px;">General Dining Service</td>
          </tr>
        `;
      }

      receiptContent.innerHTML = `
        <div class="thermal-receipt" style="background: #ffffff; color: #111827; padding: 1.5rem; border-radius: 8px; font-family: 'Courier New', Courier, monospace; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
          <!-- Header -->
          <div class="receipt-header" style="text-align: center; margin-bottom: 0.75rem;">
            <div style="font-size: 1.35rem; font-weight: 900; letter-spacing: 1px; color: #000;">DINEFLOW RESTAURANT</div>
            <div style="font-size: 0.8rem; font-weight: 600; color: #374151;">AUTHENTIC CUISINE & HOSPITALITY</div>
            <div style="font-size: 0.72rem; color: #6b7280; margin-top: 3px;">12th Main, 100ft Road, Indiranagar, Bengaluru - 560038</div>
            <div style="font-size: 0.72rem; color: #4b5563; margin-top: 2px;">
              <strong>GSTIN:</strong> 29AAAAA0000A1Z5 | <strong>FSSAI:</strong> 11223344556677
            </div>
            <div style="margin-top: 6px; display: inline-block; padding: 2px 10px; background: #000; color: #fff; font-size: 0.75rem; font-weight: 800; border-radius: 3px;">
              TAX INVOICE
            </div>
          </div>

          <div style="border-top: 1px dashed #374151; margin: 8px 0;"></div>

          <!-- Invoice Details Meta -->
          <div style="font-size: 0.75rem; line-height: 1.4; color: #1f2937;">
            <div style="display: flex; justify-content: space-between;">
              <span><strong>Invoice No:</strong> ${invNumber}</span>
              <span><strong>Date:</strong> ${dateFormatted}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span><strong>Order Ref:</strong> ${orderNumber}</span>
              <span><strong>Time:</strong> ${timeFormatted}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span><strong>Table:</strong> #${tableNum}</span>
              <span><strong>Type:</strong> ${order?.order_type || 'DINE_IN'}</span>
            </div>
          </div>

          <div style="border-top: 1px solid #111827; border-bottom: 1px solid #111827; margin: 8px 0; padding: 4px 0;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.72rem;">
              <thead>
                <tr style="font-weight: 800; color: #000;">
                  <th style="text-align: left; padding: 2px;">ITEM</th>
                  <th style="text-align: center; padding: 2px;">HSN</th>
                  <th style="text-align: center; padding: 2px;">QTY</th>
                  <th style="text-align: right; padding: 2px;">RATE</th>
                  <th style="text-align: right; padding: 2px;">AMT</th>
                </tr>
              </thead>
              <tbody>
                ${itemsHtml}
              </tbody>
            </table>
          </div>

          <!-- Total Calculation -->
          <div style="font-size: 0.76rem; line-height: 1.5; color: #1f2937;">
            <div style="display: flex; justify-content: space-between;">
              <span>Items Subtotal:</span>
              <span style="font-weight: 600;">₹${subtotal}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span>CGST @ 2.5%:</span>
              <span>₹${cgst}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span>SGST @ 2.5%:</span>
              <span>₹${sgst}</span>
            </div>
            ${Number(discount) > 0 ? `
              <div style="display: flex; justify-content: space-between; color: #059669; font-weight: 700;">
                <span>Discount Applied:</span>
                <span>-₹${discount}</span>
              </div>
            ` : ''}
            
            <div style="border-top: 2px solid #000; margin: 6px 0 4px 0;"></div>
            
            <div style="display: flex; justify-content: space-between; font-size: 1.15rem; font-weight: 900; color: #000;">
              <span>NET PAYABLE:</span>
              <span>₹${total}</span>
            </div>
          </div>

          <div style="border-top: 1px dashed #374151; margin: 10px 0;"></div>

          <!-- Footer & Payment Status -->
          <div style="text-align: center; font-size: 0.72rem; color: #4b5563;">
            <div style="font-size: 0.82rem; font-weight: 800; margin-bottom: 4px; color: ${inv.status === 'PAID' ? '#059669' : '#d97706'};">
              PAYMENT STATUS: ${inv.status}
            </div>
            <p style="margin-bottom: 4px;">GST Included. Thank you for dining with DineFlow!</p>
            <p style="font-size: 0.68rem; color: #6b7280;">Visit Again • Have a Wonderful Day</p>
            
            <div class="receipt-barcode" style="margin: 8px auto 4px auto; display: flex; justify-content: center; height: 32px; gap: 2px;">
              ${Array.from({ length: 42 }).map((_, i) => `<span style="background: #000; width: ${i % 4 === 0 ? 3 : (i % 2 === 0 ? 2 : 1)}px; height: 100%;"></span>`).join("")}
            </div>
            <span style="font-size: 0.65rem; letter-spacing: 2px; color: #9ca3af;">*${invNumber}*</span>
          </div>
        </div>
      `;

      if (window.Sound) Sound.pop();
      App.openModal("receipt-modal");
    } catch (e) {
      App.showToast(`Error rendering tax invoice: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  function printReceipt() {
    window.print();
  }

  return {
    init,
    refresh,
    setFilter,
    openPaymentModal,
    setQuickCash,
    setExactCash,
    submitPayment,
    viewReceipt,
    printReceipt,
    openCreateInvoiceModal,
    onSelectOrderForInvoice,
    submitGenerateInvoice
  };
})();
