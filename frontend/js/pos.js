/**
 * POS (Point of Sale) & Order Management Module
 */

const POS = (() => {
  let categories = [];
  let menuItems = [];
  let cart = [];
  let activeCategoryId = "all";
  let dietFilter = "all"; // "all", "veg", "nonveg", "fast"
  let discountPercent = 0;
  let searchQuery = "";

  async function init() {
    await loadCategories();
    await loadMenuItems();
    await loadTableOptions();
    await loadCustomerOptions();
    renderCategories();
    renderMenuItems();
    renderCart();
  }

  async function loadCategories() {
    try {
      categories = await API.menu.getCategories();
    } catch (e) {
      console.warn("Could not load categories:", e);
      categories = [];
    }
  }

  async function loadMenuItems() {
    try {
      menuItems = await API.menu.getItems();
    } catch (e) {
      console.warn("Could not load menu items:", e);
      menuItems = [];
    }
  }

  async function loadTableOptions() {
    const tableSelect = document.getElementById("pos-table-select");
    if (!tableSelect) return;
    try {
      const tables = await API.tables.getAll();
      tableSelect.innerHTML = `<option value="">-- Select Table --</option>` +
        tables.map(t => {
          const statusIcon = t.status === "AVAILABLE" ? "🟢" : (t.status === "OCCUPIED" ? "🔴" : "🟡");
          return `<option value="${t.id || t._id}">${statusIcon} Table ${t.table_number} (${t.location || 'Main'} - ${t.capacity} seats)</option>`;
        }).join("");
    } catch (e) {
      console.warn("Could not load tables:", e);
    }
  }

  async function loadCustomerOptions() {
    const customerSelect = document.getElementById("pos-customer-select");
    if (!customerSelect) return;
    try {
      const customers = await API.customers.getAll();
      customerSelect.innerHTML = `<option value="">Walk-in Guest</option>` +
        customers.map(c => `<option value="${c.id || c._id}">${c.name} (${c.phone})</option>`).join("");
    } catch (e) {
      console.warn("Could not load customers:", e);
    }
  }

  function getCategoryIcon(name) {
    const n = (name || "").toLowerCase();
    if (n.includes("curry") || n.includes("main") || n.includes("entree")) return "🍛";
    if (n.includes("starter") || n.includes("appetizer") || n.includes("snack")) return "🥗";
    if (n.includes("bread") || n.includes("roti") || n.includes("naan")) return "🫓";
    if (n.includes("rice") || n.includes("biryani")) return "🍚";
    if (n.includes("drink") || n.includes("beverage")) return "🥤";
    if (n.includes("dessert") || n.includes("sweet")) return "🍰";
    if (n.includes("pizza") || n.includes("burger")) return "🍔";
    return "🍽️";
  }

  function renderCategories() {
    const container = document.getElementById("pos-category-tabs");
    if (!container) return;

    let html = `<button class="category-tab-btn ${activeCategoryId === 'all' ? 'active' : ''}" onclick="POS.filterCategory('all')">🍽️ All Items (${menuItems.length})</button>`;
    
    categories.forEach(cat => {
      const catId = cat.id || cat._id;
      const count = menuItems.filter(i => (i.category_id === catId || (i.category_id && i.category_id.$oid === catId))).length;
      const icon = getCategoryIcon(cat.name);
      html += `<button class="category-tab-btn ${activeCategoryId === catId ? 'active' : ''}" onclick="POS.filterCategory('${catId}')">${icon} ${cat.name} (${count})</button>`;
    });

    container.innerHTML = html;
  }

  function filterCategory(catId) {
    activeCategoryId = catId;
    renderCategories();
    renderMenuItems();
  }

  function setDietFilter(type) {
    dietFilter = type;
    document.querySelectorAll(".diet-chip-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.diet === type);
    });
    renderMenuItems();
  }

  function setDiscount(percent) {
    discountPercent = percent;
    document.querySelectorAll(".discount-pill").forEach(pill => {
      pill.classList.toggle("active", parseInt(pill.dataset.discount, 10) === percent);
    });
    renderCart();
  }

  function search(query) {
    searchQuery = query.toLowerCase().trim();
    renderMenuItems();
  }

  function renderMenuItems() {
    const container = document.getElementById("pos-items-grid");
    if (!container) return;

    let filtered = menuItems;

    // Category filter
    if (activeCategoryId !== "all") {
      filtered = filtered.filter(item => {
        const cId = item.category_id?.id || item.category_id?._id || item.category_id;
        return cId === activeCategoryId;
      });
    }

    // Dietary filter
    if (dietFilter === "veg") {
      filtered = filtered.filter(item => item.is_vegetarian === true);
    } else if (dietFilter === "nonveg") {
      filtered = filtered.filter(item => item.is_vegetarian === false);
    } else if (dietFilter === "fast") {
      filtered = filtered.filter(item => (item.preparation_time || 0) <= 15);
    }

    // Search query filter
    if (searchQuery) {
      filtered = filtered.filter(item =>
        item.name.toLowerCase().includes(searchQuery) ||
        (item.description && item.description.toLowerCase().includes(searchQuery))
      );
    }

    const countLabel = document.getElementById("pos-dishes-count-label");
    if (countLabel) {
      countLabel.textContent = `Showing ${filtered.length} of ${menuItems.length} dishes`;
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3.5rem 1.5rem; color: var(--text-dim);">
          <div style="font-size: 3rem; margin-bottom: 0.75rem;">🍽️</div>
          <p style="font-size: 1.05rem; font-weight: 600; color: var(--text-main);">No dishes match your filter</p>
          <span style="font-size: 0.85rem; display: block; margin-bottom: 1.25rem;">Try choosing a different category or clearing search</span>
          <button type="button" class="btn btn-primary btn-sm" onclick="MenuMgmt.openAddItemModal()">+ Add New Dish</button>
        </div>`;
      return;
    }

    const user = API.getCurrentUser();
    const canManageMenu = user && ["ADMIN", "MANAGER", "CHEF"].includes((user.role || "").toUpperCase());

    const cardsHtml = filtered.map(item => {
      const id = item.id || item._id;
      const price = Number(item.price?.$numberDecimal || item.price || 0).toFixed(2);
      const isVeg = item.is_vegetarian;
      const icon = getCategoryIcon(item.name);
      const imageUrl = item.image_url;
      const cartItem = cart.find(c => c.itemId === id);
      const inCartQty = cartItem ? cartItem.quantity : 0;

      return `
        <div class="menu-card ${inCartQty > 0 ? 'in-cart' : ''}" data-dish-id="${id}" onclick="POS.addToCart('${id}')">
          <div class="menu-card-image-wrap">
            ${imageUrl ? `
              <img src="${imageUrl}" alt="${escapeHtml(item.name)}" class="menu-card-img" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
              <div class="menu-card-img-placeholder" style="display: none;">${icon}</div>
            ` : `
              <div class="menu-card-img-placeholder">${icon}</div>
            `}
            <div class="menu-card-image-overlay">
              <div style="display: flex; gap: 0.35rem; align-items: center;">
                <span class="diet-icon-mark ${isVeg ? 'veg' : 'nonveg'}" title="${isVeg ? 'Pure Vegetarian' : 'Non-Vegetarian'}"></span>
                ${item.preparation_time ? `<span class="menu-card-time" style="background: rgba(15,23,42,0.88); backdrop-filter: blur(4px);">⏱️ ${item.preparation_time}m</span>` : ''}
              </div>
              <div style="display: flex; gap: 0.35rem; align-items: center;">
                ${inCartQty > 0 ? `<span class="cart-qty-pill">🛒 ${inCartQty}</span>` : ''}
                ${canManageMenu ? `
                  <button type="button" class="menu-card-delete-btn" onclick="event.stopPropagation(); MenuMgmt.openEditItemModal('${id}')" title="Edit '${escapeHtml(item.name)}' recipe & pricing" style="background: rgba(37,99,235,0.85); border-color: rgba(96,165,250,0.5);">
                    ✏️
                  </button>
                  <button type="button" class="menu-card-delete-btn" onclick="event.stopPropagation(); MenuMgmt.promptDeleteDish('${id}')" title="Delete '${escapeHtml(item.name)}' from menu">
                    🗑️
                  </button>
                ` : ''}
              </div>
            </div>
          </div>
          <div class="menu-card-center">
            <div class="menu-card-name">${escapeHtml(item.name)}</div>
            <div class="menu-card-desc">${escapeHtml(item.description || 'Authentic chef recipe cooked fresh with finest aromatic spices.')}</div>
          </div>
          <div class="menu-card-bottom">
            <span class="menu-card-price">₹${price}</span>
            <div style="display: flex; gap: 0.4rem; align-items: center;">
              ${inCartQty > 0 ? `
                <div class="menu-card-qty-stepper" onclick="event.stopPropagation();">
                  <button type="button" class="stepper-btn" onclick="event.stopPropagation(); POS.updateQty('${id}', -1)" title="Reduce quantity">−</button>
                  <span class="stepper-qty">${inCartQty}</span>
                  <button type="button" class="stepper-btn" onclick="event.stopPropagation(); POS.updateQty('${id}', 1)" title="Increase quantity">+</button>
                </div>
              ` : `
                <button type="button" class="menu-card-add-btn" onclick="event.stopPropagation(); POS.addToCart('${id}')" title="Add to Ticket">
                  <span>+ Add</span>
                </button>
              `}
            </div>
          </div>
        </div>
      `;
    }).join("");

    const addCardHtml = `
      <div class="menu-card add-new-dish-card" onclick="MenuMgmt.openAddItemModal(POS.getActiveCategoryId())" title="Add a new dish to the restaurant menu">
        <div class="add-new-dish-inner">
          <div class="add-new-dish-icon">+</div>
          <div style="font-weight: 700; color: var(--accent-primary); margin-top: 0.65rem; font-size: 1rem;">Add New Dish</div>
          <div style="font-size: 0.78rem; color: var(--text-dim); margin-top: 0.25rem;">Create recipe, photo & price</div>
        </div>
      </div>
    `;

    container.innerHTML = cardsHtml + (canManageMenu ? addCardHtml : '');
  }

  function addToCart(itemId) {
    const item = menuItems.find(i => (i.id || i._id) === itemId);
    if (!item) return;

    const existing = cart.find(c => c.itemId === itemId);
    const price = Number(item.price?.$numberDecimal || item.price || 0);

    if (existing) {
      existing.quantity += 1;
    } else {
      cart.push({
        itemId,
        name: item.name,
        price,
        quantity: 1,
        instructions: ""
      });
    }

    renderCart();
    renderMenuItems();
    App.showToast(`Added "${item.name}" to cart`, "info");
  }

  function updateQty(itemId, delta) {
    const item = cart.find(c => c.itemId === itemId);
    if (!item) return;

    item.quantity += delta;
    if (item.quantity <= 0) {
      cart = cart.filter(c => c.itemId !== itemId);
    }
    renderCart();
    renderMenuItems();
  }

  function clearCart() {
    cart = [];
    renderCart();
    renderMenuItems();
  }

  function renderCart() {
    const container = document.getElementById("pos-cart-items");
    const countBadge = document.getElementById("pos-cart-count");
    const subtotalEl = document.getElementById("pos-cart-subtotal");
    const discountEl = document.getElementById("pos-cart-discount-line");
    const discountValEl = document.getElementById("pos-cart-discount-value");
    const taxEl = document.getElementById("pos-cart-tax");
    const totalEl = document.getElementById("pos-cart-total");

    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    if (countBadge) countBadge.textContent = totalItems;

    if (!container) return;

    if (cart.length === 0) {
      container.innerHTML = `
        <div class="cart-empty">
          <div style="font-size: 2.5rem; opacity: 0.4;">🛒</div>
          <p style="font-weight: 500;">Your ticket is currently empty.</p>
          <span style="font-size: 0.75rem;">Click menu items to add them here</span>
        </div>`;
      if (subtotalEl) subtotalEl.textContent = "₹0.00";
      if (discountEl) discountEl.style.display = "none";
      if (taxEl) taxEl.textContent = "₹0.00";
      if (totalEl) totalEl.textContent = "₹0.00";
      return;
    }

    let subtotal = 0;

    container.innerHTML = cart.map(item => {
      const lineTotal = item.price * item.quantity;
      subtotal += lineTotal;

      return `
        <div class="cart-item-row">
          <div class="cart-item-details">
            <div class="cart-item-name">${escapeHtml(item.name)}</div>
            <div class="cart-item-unit-price">₹${item.price.toFixed(2)} ea</div>
          </div>
          <div class="cart-item-qty-controls">
            <button class="qty-btn minus" onclick="POS.updateQty('${item.itemId}', -1)" title="Decrease quantity">-</button>
            <span class="qty-display">${item.quantity}</span>
            <button class="qty-btn plus" onclick="POS.updateQty('${item.itemId}', 1)" title="Increase quantity">+</button>
          </div>
          <div class="cart-item-total">₹${lineTotal.toFixed(2)}</div>
          <button class="cart-item-del-btn" onclick="POS.removeItem('${item.itemId}')" title="Remove item">✕</button>
        </div>
      `;
    }).join("");

    const discountAmount = subtotal * (discountPercent / 100);
    const taxable = Math.max(0, subtotal - discountAmount);
    const tax = taxable * 0.05; // 5% standard tax
    const grandTotal = taxable + tax;

    if (subtotalEl) subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
    if (discountEl) {
      if (discountPercent > 0) {
        discountEl.style.display = "flex";
        if (discountValEl) discountValEl.textContent = `-₹${discountAmount.toFixed(2)} (${discountPercent}%)`;
      } else {
        discountEl.style.display = "none";
      }
    }
    if (taxEl) taxEl.textContent = `₹${tax.toFixed(2)}`;
    if (totalEl) totalEl.textContent = `₹${grandTotal.toFixed(2)}`;
  }

  function removeItem(itemId) {
    const item = cart.find(c => c.itemId === itemId);
    cart = cart.filter(c => c.itemId !== itemId);
    renderCart();
    if (item) App.showToast(`Removed "${item.name}" from cart`, "info");
  }

  function selectTable(tableId) {
    const tableSelect = document.getElementById("pos-table-select");
    if (tableSelect) {
      tableSelect.value = tableId;
      App.switchView("pos");
      App.showToast(`Table selected for new order!`, "success");
    }
  }

  async function placeOrder(sendToKitchen = false) {
    if (cart.length === 0) {
      App.showToast("Your order is empty. Please add items first.", "warning");
      return;
    }

    const tableId = document.getElementById("pos-table-select")?.value || null;
    const customerId = document.getElementById("pos-customer-select")?.value || null;
    const orderType = document.getElementById("pos-type-select")?.value || "DINE_IN";
    const notes = document.getElementById("pos-order-notes")?.value?.trim() || "";
    const user = API.getCurrentUser();

    try {
      App.showLoader(true);

      // 1. Create Order
      const orderPayload = {
        customer_id: customerId || undefined,
        table_id: tableId || undefined,
        order_type: orderType,
        created_by: user?.email || user?.name || "pos_staff"
      };

      const newOrder = await API.orders.create(orderPayload);
      const orderId = newOrder.id || newOrder._id;

      // 2. Add Each Cart Item to the Order
      for (const item of cart) {
        await API.orders.addItem(orderId, {
          menu_item_id: item.itemId,
          quantity: item.quantity,
          special_instructions: notes || item.instructions || undefined
        });
      }

      // 3. Recalculate Order Subtotal & Total
      await API.orders.recalculate(orderId);

      // 4. Update status to CONFIRMED
      await API.orders.updateStatus(orderId, "CONFIRMED");

      // 5. If Send to Kitchen is requested:
      if (sendToKitchen) {
        await API.kitchen.createTicket(orderId, "NORMAL");
        App.showToast(`Order #${newOrder.order_number || orderId.slice(-6)} placed & sent to Kitchen KDS!`, "success");
      } else {
        App.showToast(`Order #${newOrder.order_number || orderId.slice(-6)} placed successfully!`, "success");
      }

      // If a table was occupied, mark table as OCCUPIED
      if (tableId) {
        await API.tables.updateStatus(tableId, "OCCUPIED").catch(() => {});
      }

      const notesInput = document.getElementById("pos-order-notes");
      if (notesInput) notesInput.value = "";

      clearCart();
      await loadTableOptions();
      await OrdersList.refresh();
      if (window.KitchenDisplay) KitchenDisplay.refresh();
      if (window.TablesView) TablesView.refresh();

    } catch (err) {
      App.showToast(`Order placement failed: ${err.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function getItem(id) {
    return menuItems.find(i => (i.id || i._id) === id);
  }

  async function onNewItemAdded(targetId) {
    activeCategoryId = "all";
    dietFilter = "all";
    searchQuery = "";
    const searchInput = document.getElementById("pos-search-input");
    if (searchInput) searchInput.value = "";
    document.querySelectorAll(".diet-chip-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.diet === "all");
    });
    await init();
    // Smooth scroll and pulse highlight on new card
    setTimeout(() => {
      if (targetId) {
        const card = document.querySelector(`[data-dish-id="${targetId}"]`);
        if (card) {
          card.scrollIntoView({ behavior: 'smooth', block: 'center' });
          card.classList.add('dish-card-highlight');
          setTimeout(() => card.classList.remove('dish-card-highlight'), 3500);
        }
      }
    }, 150);
  }

  return {
    init,
    filterCategory,
    setDietFilter,
    setDiscount,
    search,
    addToCart,
    updateQty,
    removeItem,
    clearCart,
    placeOrder,
    selectTable,
    getActiveCategoryId: () => (activeCategoryId === "all" ? null : activeCategoryId),
    getItem,
    onNewItemAdded,
    refresh: init
  };
})();
