/**
 * DineFlow Main Application Controller
 * Handles Navigation, Authentication, Role Switcher, Notifications, and Dashboard Stats
 */

const App = (() => {
  let currentView = "dashboard";
  let isBackendOnline = false;

  const PRESET_ACCOUNTS = [
    { role: "ADMIN", email: "admin@dineflow.com", name: "System Admin" },
    { role: "MANAGER", email: "manager@dineflow.com", name: "General Manager" },
    { role: "CHEF", email: "chef@dineflow.com", name: "Head Chef" },
    { role: "WAITER", email: "waiter@dineflow.com", name: "Floor Waiter" },
    { role: "CASHIER", email: "cashier@dineflow.com", name: "Billing Cashier" },
  ];

  // Auto-authenticate default session so Dashboard is the first page directly
  async function ensureAuthenticated() {
    let user = API.getCurrentUser();
    let token = API.getToken();

    if (token && user) {
      return;
    }

    // Default to System Admin as primary station account
    const defaultAccount = PRESET_ACCOUNTS[0]; // Admin
    const defaultUser = {
      name: defaultAccount.name,
      email: defaultAccount.email,
      role: defaultAccount.role,
    };
    API.setCurrentUser(defaultUser);

    // Silently obtain valid JWT from backend if online
    try {
      const res = await API.auth.login(defaultAccount.email, "Password123!");
      if (res && res.access_token) {
        API.setToken(res.access_token);
        if (res.user) {
          API.setCurrentUser(res.user);
        }
        return;
      }
    } catch (e) {
      console.warn("Silent admin login failed, fallback token active:", e);
    }

    // Fallback token for offline / local mode
    API.setToken("demo-admin-session-token");
  }

  async function start() {
    initTheme();
    setupEventListeners();
    await checkBackendConnection();

    // Ensure session exists so the main dashboard is loaded directly as the first page
    await ensureAuthenticated();

    updateUserUI();

    // Initialize all modules
    await refreshAll();

    // Open initial view from hash or default to dashboard
    const hash = window.location.hash.replace("#", "") || "dashboard";
    switchView(hash);

    // Periodic health check
    setInterval(checkBackendConnection, 20000);
  }

  function initTheme() {
    const saved = localStorage.getItem("dineflow_theme") || "dark";
    applyTheme(saved);
  }

  function toggleTheme() {
    const isLight = document.documentElement.classList.contains("light-theme");
    const newTheme = isLight ? "dark" : "light";
    applyTheme(newTheme);
    localStorage.setItem("dineflow_theme", newTheme);
    showToast(`Switched to ${newTheme === 'light' ? 'Day Light Mode' : 'Night Dark Mode'}`, "info");
  }

  function applyTheme(theme) {
    const icon = document.getElementById("theme-toggle-icon");
    const label = document.getElementById("theme-toggle-label");
    if (theme === "light") {
      document.documentElement.classList.add("light-theme");
      if (icon) icon.textContent = "🌙";
      if (label) label.textContent = "Night Mode";
    } else {
      document.documentElement.classList.remove("light-theme");
      if (icon) icon.textContent = "☀️";
      if (label) label.textContent = "Day Mode";
    }
  }

  function setupEventListeners() {
    // Nav Items
    document.querySelectorAll(".nav-item").forEach(item => {
      item.addEventListener("click", e => {
        e.preventDefault();
        const view = item.dataset.view;
        if (view) switchView(view);
      });
    });

    // Close modals on escape key or clicking backdrop, and global keyboard shortcuts
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") closeAllModals();

      // Quick focus search on '/' or Ctrl+K / Cmd+K
      if ((e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k")) {
        e.preventDefault();
        const globalSearch = document.getElementById("global-header-search");
        if (globalSearch) {
          globalSearch.focus();
          globalSearch.select();
        } else {
          if (currentView !== "pos") switchView("pos");
          const searchInput = document.getElementById("pos-search-input");
          if (searchInput) {
            searchInput.focus();
            searchInput.select();
          }
        }
      }
    });

    document.querySelectorAll(".modal-overlay").forEach(overlay => {
      overlay.addEventListener("click", e => {
        if (e.target === overlay) closeModal(overlay.id);
      });
    });
  }

  async function checkBackendConnection() {
    const dot = document.getElementById("backend-status-dot");
    const text = document.getElementById("backend-status-text");

    try {
      const start = performance.now();
      await API.health();
      const latency = Math.round(performance.now() - start);

      isBackendOnline = true;
      if (dot) {
        dot.className = "status-dot online";
      }
      if (text) {
        text.textContent = `Online (${latency}ms)`;
      }
    } catch {
      isBackendOnline = false;
      if (dot) {
        dot.className = "status-dot";
      }
      if (text) {
        text.textContent = "Offline (Click to edit)";
      }
    }
  }

  function openConfigModal() {
    const input = document.getElementById("api-base-url-input");
    if (input) input.value = API.getBaseUrl();
    openModal("api-config-modal");
  }

  function saveApiConfig() {
    const input = document.getElementById("api-base-url-input");
    if (input && input.value) {
      API.setBaseUrl(input.value.trim());
      showToast("API Base URL updated!", "success");
      closeModal("api-config-modal");
      checkBackendConnection();
      refreshAll();
    }
  }

  // 1-Click Role Switcher
  async function quickRoleLogin(role, silent = false) {
    const account = PRESET_ACCOUNTS.find(a => a.role === role);
    if (!account) return;

    try {
      showLoader(true);
      const res = await API.auth.login(account.email, "Password123!");
      API.setToken(res.access_token);

      // Save user
      const userData = res.user || {
        name: account.name,
        email: account.email,
        role: role
      };
      API.setCurrentUser(userData);

      updateUserUI();
      if (!silent) {
        showToast(`Switched profile to ${role} (${account.email})`, "success");
      }

      closeRoleDropdown();
      applyRolePermissions(role);
      await refreshAll();
    } catch (e) {
      console.warn("Auto-login failed:", e);
      if (!silent) {
        showToast(`Login failed: ${e.message}`, "error");
      }
    } finally {
      showLoader(false);
    }
  }

  function toggleRoleDropdown() {
    const menu = document.getElementById("role-dropdown-menu");
    if (menu) menu.classList.toggle("show");
  }

  function closeRoleDropdown() {
    const menu = document.getElementById("role-dropdown-menu");
    if (menu) menu.classList.remove("show");
  }

  function updateUserUI() {
    const user = API.getCurrentUser();
    if (!user) return;

    const avatar = document.getElementById("user-avatar-text");
    const nameEl = document.getElementById("user-display-name");
    const roleEl = document.getElementById("user-display-role");
    const headerPillRole = document.getElementById("header-role-pill-text");
    const topAvatar = document.getElementById("top-user-avatar");
    const topName = document.getElementById("top-user-name");
    const dashWelcome = document.getElementById("dashboard-welcome-name");

    const roleIcons = {
      ADMIN: "👑",
      MANAGER: "📊",
      CHEF: "👨‍🍳",
      WAITER: "🤵",
      CASHIER: "💳",
    };
    const roleIcon = roleIcons[user.role] || "👤";

    const initials = (user.name || user.email || "DF").slice(0, 2).toUpperCase();
    if (avatar) avatar.textContent = initials;
    if (nameEl) nameEl.textContent = user.name || user.email;
    if (roleEl) roleEl.textContent = `${roleIcon} ${user.role || "STAFF"}`;
    if (headerPillRole) headerPillRole.textContent = user.role || "STAFF";
    if (topAvatar) topAvatar.textContent = roleIcon;
    if (topName) topName.textContent = user.name || user.email;
    if (dashWelcome) dashWelcome.textContent = user.name || user.email;

    applyRolePermissions(user.role);
  }

  async function logout() {
    API.setToken(null);
    API.setCurrentUser(null);
    showToast("Session reset. Restoring System Administrator...", "info");
    await ensureAuthenticated();
    updateUserUI();
    applyRolePermissions("ADMIN");
    await refreshAll();
    switchView("dashboard");
    showToast("Active station reset to System Admin", "success");
  }

  function applyRolePermissions(role) {
    const roleUpper = (role || "").toUpperCase();
    
    // Hide or show nav items based on role
    document.querySelectorAll(".nav-item").forEach(item => {
      const allowedRoles = item.dataset.roles ? item.dataset.roles.split(",") : null;
      if (allowedRoles) {
        if (allowedRoles.includes(roleUpper) || roleUpper === "ADMIN") {
          item.style.display = "flex";
        } else {
          item.style.display = "none";
        }
      }
    });

    // Check if currently active view is allowed for this role
    const activeNav = document.querySelector(`.nav-item[data-view="${currentView}"]`);
    if (activeNav && activeNav.dataset.roles) {
      const allowedRoles = activeNav.dataset.roles.split(",");
      if (!allowedRoles.includes(roleUpper) && roleUpper !== "ADMIN") {
        const defaultViews = {
          CHEF: "kitchen",
          WAITER: "pos",
          CASHIER: "billing",
          MANAGER: "dashboard",
          ADMIN: "dashboard"
        };
        const nextView = defaultViews[roleUpper] || "dashboard";
        switchView(nextView);
      }
    }
  }

  function switchView(viewName) {
    const user = API.getCurrentUser();
    const roleUpper = (user?.role || "ADMIN").toUpperCase();
    const targetNav = document.querySelector(`.nav-item[data-view="${viewName}"]`);

    // Verify role permissions
    if (targetNav && targetNav.dataset.roles) {
      const allowedRoles = targetNav.dataset.roles.split(",");
      if (!allowedRoles.includes(roleUpper) && roleUpper !== "ADMIN") {
        showToast(`Access Restricted: "${getViewMeta(viewName).title}" requires ${allowedRoles.join('/')} privileges.`, "warning");
        return;
      }
    }

    const views = document.querySelectorAll(".view-section");
    const navItems = document.querySelectorAll(".nav-item");

    views.forEach(v => v.classList.remove("active"));
    navItems.forEach(n => n.classList.remove("active"));

    const targetView = document.getElementById(`view-${viewName}`);

    if (targetView) {
      targetView.classList.add("active");
      currentView = viewName;
      window.location.hash = viewName;

      // Update page title
      const titleBox = document.getElementById("current-page-title");
      const descBox = document.getElementById("current-page-desc");
      const viewMeta = getViewMeta(viewName);

      if (titleBox) titleBox.textContent = viewMeta.title;
      if (descBox) descBox.textContent = viewMeta.desc;
    }

    if (targetNav) {
      targetNav.classList.add("active");
    }

    // Refresh view specific data
    triggerViewRefresh(viewName);
  }

  function getViewMeta(view) {
    const meta = {
      dashboard: { title: "Executive Dashboard", desc: "Live restaurant metrics and operational overview" },
      pos: { title: "Point of Sale (POS)", desc: "Select dishes, configure guest tickets, and dispatch orders to kitchen" },
      orders: { title: "Order Pipeline", desc: "Track, modify, and monitor active and past guest orders" },
      kitchen: { title: "Kitchen Display (KDS)", desc: "Real-time chef board, prep queue, and ticket advances" },
      tables: { title: "Tables & Reservations", desc: "Interactive floor plan and guest table booking system" },
      billing: { title: "Billing & Cashier", desc: "Issue customer invoices, receive payments, and print receipts" },
      inventory: { title: "Inventory & Ingredients", desc: "Stock levels, replenishment alerts, and cost tracking" },
      "menu-mgmt": { title: "Menu Management", desc: "Manage culinary catalog, categories, dishes, prices, and availability" },
      feedback: { title: "Guest Reviews & Ratings", desc: "Customer satisfaction scores and dining feedback" },
      users: { title: "Staff Directory & Roles", desc: "Employee access control and restaurant credentials" },
    };
    return meta[view] || { title: "Restaurant Operations", desc: "DineFlow Management Suite" };
  }

  function triggerViewRefresh(view) {
    switch (view) {
      case "dashboard": Dashboard.refresh(); break;
      case "pos": POS.refresh(); break;
      case "orders": OrdersList.refresh(); break;
      case "kitchen": KitchenDisplay.refresh(); break;
      case "tables": TablesView.refresh(); break;
      case "billing": BillingView.refresh(); break;
      case "inventory": InventoryView.refresh(); break;
      case "menu-mgmt": MenuMgmt.refresh(); break;
      case "feedback": FeedbackView.refresh(); break;
      case "users": UsersView.refresh(); break;
    }
  }

  async function refreshAll() {
    await Dashboard.refresh().catch(() => {});
    if (window.POS) POS.init().catch(() => {});
    if (window.OrdersList) OrdersList.init().catch(() => {});
    if (window.KitchenDisplay) KitchenDisplay.init().catch(() => {});
    if (window.TablesView) TablesView.init().catch(() => {});
    if (window.BillingView) BillingView.init().catch(() => {});
    if (window.InventoryView) InventoryView.init().catch(() => {});
    if (window.MenuMgmt) MenuMgmt.init().catch(() => {});
    if (window.FeedbackView) FeedbackView.init().catch(() => {});
    if (window.UsersView) UsersView.init().catch(() => {});
  }

  // Modals
  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("show");
  }

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("show");
  }

  function closeAllModals() {
    document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("show"));
  }

  // Dismiss modal when clicking backdrop or pressing Escape
  document.addEventListener("click", (e) => {
    if (e.target && e.target.classList && e.target.classList.contains("modal-overlay")) {
      e.target.classList.remove("show");
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const openModals = Array.from(document.querySelectorAll(".modal-overlay.show"));
      if (openModals.length > 0) {
        openModals[openModals.length - 1].classList.remove("show");
      }
    }
  });

  // Loader
  function showLoader(show) {
    const loader = document.getElementById("global-loader");
    if (loader) loader.style.display = show ? "flex" : "none";
  }

  // Toast Notifications
  function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let icon = "ℹ️";
    if (type === "success") icon = "✅";
    if (type === "error") icon = "❌";
    if (type === "warning") icon = "⚠️";

    toast.innerHTML = `
      <span style="font-size: 1.1rem;">${icon}</span>
      <div class="toast-message">${escapeHtml(message)}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function onGlobalSearch(query) {
    const val = (query || "").trim();
    if (currentView === "pos") {
      const posInput = document.getElementById("pos-search-input");
      if (posInput && posInput.value !== val) posInput.value = val;
      if (window.POS && typeof POS.search === "function") POS.search(val);
    } else if (currentView === "menu-mgmt") {
      const menuInput = document.getElementById("menu-mgmt-search-input");
      if (menuInput && menuInput.value !== val) menuInput.value = val;
      if (window.MenuMgmt && typeof MenuMgmt.searchDishes === "function") MenuMgmt.searchDishes(val);
    } else {
      switchView("pos");
      const posInput = document.getElementById("pos-search-input");
      if (posInput) posInput.value = val;
      if (window.POS && typeof POS.search === "function") POS.search(val);
    }
  }

  return {
    start,
    switchView,
    toggleTheme,
    quickRoleLogin,
    toggleRoleDropdown,
    openConfigModal,
    saveApiConfig,
    checkBackendConnection,
    openModal,
    closeModal,
    closeAllModals,
    showLoader,
    showToast,
    logout,
    refreshAll,
    onGlobalSearch
  };
})();

// Dashboard Sub-module
const Dashboard = (() => {
  async function refresh() {
    try {
      const [orders, tables, invoices, tickets, ingredients] = await Promise.all([
        API.orders.getAll().catch(() => []),
        API.tables.getAll().catch(() => []),
        API.billing.getInvoices().catch(() => []),
        API.kitchen.getTickets().catch(() => []),
        API.inventory.getIngredients().catch(() => []),
      ]);

      // Active Orders (confirmed / in kitchen / preparing)
      const activeOrders = orders.filter(o => ["CONFIRMED", "SENT_TO_KITCHEN", "PREPARING", "READY"].includes(o.status));
      const activeCountEl = document.getElementById("dash-active-orders");
      if (activeCountEl) activeCountEl.textContent = activeOrders.length;

      // Tables Occupied vs Total
      const occupiedTables = tables.filter(t => t.status === "OCCUPIED");
      const tablesCountEl = document.getElementById("dash-tables-occupied");
      if (tablesCountEl) tablesCountEl.textContent = `${occupiedTables.length} / ${tables.length}`;

      // Revenue Today from Invoices
      const totalRev = invoices
        .filter(i => i.status === "PAID")
        .reduce((sum, inv) => sum + Number(inv.total_amount?.$numberDecimal || inv.total_amount || 0), 0);
      const revEl = document.getElementById("dash-revenue-today");
      if (revEl) revEl.innerHTML = `<span style="font-weight: 800; margin-right: 2px;">₹</span>${totalRev.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

      // Kitchen Pending Queue
      const pendingTickets = tickets.filter(t => t.status === "QUEUED" || t.status === "PREPARING");
      const ticketsEl = document.getElementById("dash-kitchen-tickets");
      if (ticketsEl) ticketsEl.textContent = pendingTickets.length;

      // Low Stock Count
      const lowStockCount = ingredients.filter(i => {
        const cur = Number(i.available_quantity?.$numberDecimal || i.available_quantity || 0);
        const min = Number(i.minimum_stock_level?.$numberDecimal || i.minimum_stock_level || 0);
        return cur <= min;
      }).length;
      const stockEl = document.getElementById("dash-low-stock");
      if (stockEl) stockEl.textContent = lowStockCount;

      // Render Recent Orders table on dashboard
      renderRecentOrders(orders.slice(0, 5));

    } catch (e) {
      console.warn("Dashboard refresh error:", e);
    }
  }

  function renderRecentOrders(recent) {
    const tableBody = document.getElementById("dash-recent-orders-body");
    if (!tableBody) return;

    if (recent.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 1.5rem;">No recent orders</td></tr>`;
      return;
    }

    tableBody.innerHTML = recent.map(o => {
      const orderId = o.id || o._id;
      const total = Number(o.total_amount?.$numberDecimal || o.total_amount || 0).toFixed(2);
      return `
        <tr>
          <td style="font-weight: 700; color: var(--accent-primary);">${o.order_number || `#${orderId.slice(-6)}`}</td>
          <td>${o.order_type}</td>
          <td style="font-weight: 700;">₹${total}</td>
          <td><span class="badge ${o.status === 'COMPLETED' ? 'badge-green' : 'badge-amber'}">${o.status}</span></td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="App.switchView('orders'); OrdersList.viewDetails('${orderId}')">View</button>
          </td>
        </tr>
      `;
    }).join("");
  }

  return { refresh };
})();

// Document Ready Bootstrap
document.addEventListener("DOMContentLoaded", () => {
  App.start();
});
