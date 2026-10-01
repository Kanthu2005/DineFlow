/**
 * DineFlow API Client Layer
 * Handles dynamic URL detection, JWT authorization, and complete CRUD actions.
 */

const getInitialBaseUrl = () => {
  // 1. Explicit Vite environment variable (e.g. set in Vercel project environment variables)
  if (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) {
    return import.meta.env.VITE_API_URL.replace(/\/+$/, "");
  }

  // 2. Saved manual override in browser localStorage
  const saved = localStorage.getItem("dineflow_api_url");
  if (saved) return saved.replace(/\/+$/, "");

  const hostname = window.location.hostname;
  const isLocalHost = 
    hostname === "localhost" || 
    hostname === "127.0.0.1";

  // 3. Local development
  if (isLocalHost) {
    if (window.location.port === "5173" || window.location.port === "8000") {
      return "/api";
    }
    return "http://localhost:8000/api";
  }

  // 4. Same-origin deployment (e.g. if served directly from Render backend at /app)
  if (hostname.includes("onrender.com")) {
    return "/api";
  }

  // 5. Deployed on Vercel, Netlify, or any production frontend host -> default to Render backend
  return "https://dineflow-coo6.onrender.com/api";
};

let baseUrl = getInitialBaseUrl();

export const getBaseUrl = () => baseUrl;
export const setBaseUrl = (url) => {
  baseUrl = url.replace(/\/+$/, "");
  localStorage.setItem("dineflow_api_url", baseUrl);
};

export const getToken = () => localStorage.getItem("dineflow_token");
export const setToken = (token) => {
  if (token) localStorage.setItem("dineflow_token", token);
  else localStorage.removeItem("dineflow_token");
};

export const getCurrentUser = () => {
  try {
    const raw = localStorage.getItem("dineflow_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const setCurrentUser = (user) => {
  if (user) localStorage.setItem("dineflow_user", JSON.stringify(user));
  else localStorage.removeItem("dineflow_user");
};

async function request(endpoint, options = {}) {
  const url = `${baseUrl}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
    config.body = JSON.stringify(options.body);
  }

  try {
    const response = await fetch(url, config);
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      let errorMsg = "";
      if (data) {
        if (typeof data.detail === "string") errorMsg = data.detail;
        else if (Array.isArray(data.detail)) errorMsg = data.detail.map(d => d.msg).join("; ");
        else if (data.message) errorMsg = data.message;
        else if (data.error) errorMsg = data.error;
      }
      if (!errorMsg) errorMsg = `Server returned HTTP ${response.status}`;

      // Auto-reauth for demo accounts if 401
      if (response.status === 401 && !options._retried) {
        try {
          const loginRes = await fetch(`${baseUrl}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: "admin@dineflow.com", password: "Password123!" }),
          });
          if (loginRes.ok) {
            const loginData = await loginRes.json();
            if (loginData?.access_token) {
              setToken(loginData.access_token);
              if (loginData.user) setCurrentUser(loginData.user);
              return await request(endpoint, { ...options, _retried: true });
            }
          }
        } catch (e) {
          console.warn("Silent re-auth failed:", e);
        }
      }

      const err = new Error(errorMsg);
      err.status = response.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (err) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      err.message = `Cannot reach backend at ${baseUrl}. Ensure FastAPI is running on port 8000.`;
    }
    throw err;
  }
}

export const api = {
  // Health
  health: async () => {
    try {
      const rootUrl = baseUrl.replace(/\/api\/?$/, "");
      const res = await fetch(`${rootUrl}/health`);
      if (res.ok) return await res.json();
    } catch {}
    const res = await fetch(`${baseUrl}/health`);
    return await res.json();
  },

  // Auth
  auth: {
    login: (email, password) => request("/auth/login", { method: "POST", body: { email, password } }),
    register: (userData) => request("/auth/register", { method: "POST", body: userData }),
    me: () => request("/auth/me"),
  },

  // Users
  users: {
    getAll: () => request("/users"),
    create: (data) => request("/users", { method: "POST", body: data }),
    getOne: (id) => request(`/users/${id}`),
    update: (id, data) => request(`/users/${id}`, { method: "PUT", body: data }),
    delete: (id) => request(`/users/${id}`, { method: "DELETE" }),
  },

  // Customers
  customers: {
    getAll: () => request("/customers"),
    create: (data) => request("/customers", { method: "POST", body: data }),
    getOne: (id) => request(`/customers/${id}`),
  },

  // Menu
  menu: {
    getCategories: () => request("/menu/categories"),
    createCategory: (data) => request("/menu/categories", { method: "POST", body: data }),
    deleteCategory: (id) => request(`/menu/categories/${id}`, { method: "DELETE" }),
    getItems: () => request("/menu/items"),
    getItem: (id) => request(`/menu/items/${id}`),
    createItem: (data) => request("/menu/items", { method: "POST", body: data }),
    updateItem: (id, data) => request(`/menu/items/${id}`, { method: "PUT", body: data }),
    deleteItem: (id) => request(`/menu/items/${id}`, { method: "DELETE" }),
    getAvailability: () => request("/menu-items/availability"),
    getItemAvailability: (id, quantity = 1) => request(`/menu-items/${id}/availability?quantity=${quantity}`),
  },

  // Recipes
  recipes: {
    getByMenuItem: (menuItemId) => request(`/menu-items/${menuItemId}/recipe`),
    addIngredient: (menuItemId, data) => request(`/menu/${menuItemId}/recipe`, { method: "POST", body: data }),
    create: (data) => request("/recipes", { method: "POST", body: data }),
    update: (id, data) => request(`/recipes/${id}`, { method: "PUT", body: data }),
    delete: (id) => request(`/recipes/${id}`, { method: "DELETE" }),
    deleteIngredient: (menuItemId, ingredientId) => request(`/menu/${menuItemId}/recipe/${ingredientId}`, { method: "DELETE" }),
  },

  // Tables
  tables: {
    getAll: () => request("/tables"),
    getAvailable: () => request("/tables/available"),
    create: (data) => request("/tables", { method: "POST", body: data }),
    updateStatus: (id, status) => request(`/tables/${id}/status`, { method: "PATCH", body: { status } }),
  },

  // Reservations
  reservations: {
    getAll: () => request("/reservations"),
    create: (data) => request("/reservations", { method: "POST", body: data }),
    update: (id, data) => request(`/reservations/${id}`, { method: "PUT", body: data }),
  },

  // Orders
  orders: {
    getAll: () => request("/orders"),
    getOne: (id) => request(`/orders/${id}`),
    create: (data) => request("/orders", { method: "POST", body: data }),
    confirm: (orderId) => request(`/orders/${orderId}/confirm`, { method: "POST" }),
    complete: (orderId) => request(`/orders/${orderId}/complete`, { method: "POST" }),
    validateCart: (items) => request("/orders/validate-cart", { method: "POST", body: { items } }),
    updateStatus: (id, status) => request(`/orders/${id}/status`, { method: "PATCH", body: { status } }),
    updateDiscount: (id, data) => request(`/orders/${id}/discount`, { method: "PATCH", body: typeof data === "number" ? { discount_amount: data } : data }),
    addItem: (orderId, itemData) => request(`/orders/${orderId}/items`, { method: "POST", body: itemData }),
    getItems: (orderId) => request(`/orders/${orderId}/items`),
    recalculate: (orderId) => request(`/orders/${orderId}/recalculate`, { method: "POST" }),
  },

  // Kitchen
  kitchen: {
    getTickets: (status = null) => {
      const q = status ? `?status=${encodeURIComponent(status)}` : "";
      return request(`/kitchen/tickets${q}`);
    },
    createTicket: (orderId, priority = "NORMAL") => request("/kitchen/tickets", { method: "POST", body: { order_id: orderId, priority } }),
    getTicket: (ticketId) => request(`/kitchen/tickets/${ticketId}`),
    updateStatus: (ticketId, status) => request(`/kitchen/tickets/${ticketId}/status?status_value=${encodeURIComponent(status)}`, { method: "PATCH" }),
    assignStaff: (ticketId, userId, role = "CHEF") => request(`/kitchen/tickets/${ticketId}/assign`, { method: "POST", body: { user_id: userId, role } }),
  },

  // Billing
  billing: {
    getInvoices: (status = null) => {
      const q = status ? `?status=${encodeURIComponent(status)}` : "";
      return request(`/invoices${q}`);
    },
    createInvoice: (orderId, discountAmount = null) => 
      request("/invoices", { 
        method: "POST", 
        body: { 
          order_id: orderId, 
          ...(discountAmount !== null && discountAmount !== undefined ? { discount_amount: Number(discountAmount) } : {}) 
        } 
      }),
    getInvoice: (id) => request(`/invoices/${id}`),
    getInvoiceByOrder: (orderId) => request(`/invoices/order/${orderId}`),
    createPayment: (data) => request("/payments", { method: "POST", body: data }),
    getPayments: () => request("/payments"),
    createRefund: (data) => request("/refunds", { method: "POST", body: data }),
  },

  // Inventory
  inventory: {
    getIngredients: () => request("/inventory"),
    getActiveIngredients: () => request("/inventory/active"),
    getDashboard: () => request("/inventory/dashboard"),
    createIngredient: (data) => request("/inventory", { method: "POST", body: data }),
    updateIngredient: (id, data) => request(`/inventory/${id}`, { method: "PUT", body: data }),
    deleteIngredient: (id) => request(`/inventory/${id}`, { method: "DELETE" }),
    updateStock: (id, quantity) => request(`/inventory/${id}/stock`, { method: "POST", body: { quantity: Number(quantity) } }),
    getStockStatus: (id) => request(`/inventory/${id}/stock-status`),
    getMovements: (limit = 100) => request(`/inventory/movements?limit=${limit}`),
    createMovement: (data) => request("/stock-movements", { method: "POST", body: data }),
  },

  // Feedback
  feedback: {
    getAll: () => request("/feedback"),
    getSummary: () => request("/feedback/summary"),
    create: (orderId, data) => request(`/orders/${orderId}/feedback`, { method: "POST", body: data }),
  },

  // Users & Staff
  users: {
    getAll: () => request("/users"),
    getById: (id) => request(`/users/${id}`),
    create: (data) => request("/users", { method: "POST", body: data }),
    update: (id, data) => request(`/users/${id}`, { method: "PUT", body: data }),
    delete: (id) => request(`/users/${id}`, { method: "DELETE" }),
  },

  // Reports
  reports: {
    getDailySales: () => request("/reports/daily-sales"),
    getKitchenWorkload: () => request("/reports/kitchen-workload"),
    getDishCapacity: (menuItemId) => request(`/reports/dish-capacity/${menuItemId}`),
  },
};
