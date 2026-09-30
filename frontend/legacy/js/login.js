/**
 * DineFlow Login & Registration Page Controller
 * Handles 1-click station logins, credentials authentication, staff registration,
 * real-time password evaluation, and seamless workspace transitions.
 */

const LoginController = (() => {
  const PRESET_ACCOUNTS = {
    ADMIN: { email: "admin@dineflow.com", password: "Password123!", role: "ADMIN", title: "System Admin" },
    MANAGER: { email: "manager@dineflow.com", password: "Password123!", role: "MANAGER", title: "General Manager" },
    CHEF: { email: "chef@dineflow.com", password: "Password123!", role: "CHEF", title: "Head Chef" },
    WAITER: { email: "waiter@dineflow.com", password: "Password123!", role: "WAITER", title: "Floor Waiter" },
    CASHIER: { email: "cashier@dineflow.com", password: "Password123!", role: "CASHIER", title: "Billing Cashier" },
  };

  async function init() {
    // If opened directly without ?force=true, redirect immediately to dashboard
    const params = new URLSearchParams(window.location.search);
    if (!params.get("force")) {
      window.location.href = "index.html";
      return;
    }
    checkExistingAuth();
    checkHealth();
    setupEvents();
  }

  function checkExistingAuth() {
    const token = API.getToken();
    const user = API.getCurrentUser();
    if (token && user) {
      const banner = document.getElementById("existing-session-banner");
      if (banner) {
        banner.style.display = "flex";
        const nameEl = document.getElementById("existing-user-name");
        if (nameEl) {
          nameEl.textContent = `${user.name || user.email} (${user.role || 'STAFF'})`;
        }
      }
    }
  }

  async function checkHealth() {
    const statusText = document.getElementById("login-db-status");
    if (!statusText) return;

    try {
      const start = performance.now();
      const res = await API.health();
      const latency = Math.round(performance.now() - start);

      if (res && res.status === "healthy") {
        statusText.innerHTML = `
          <span class="pulse-dot" style="background:#10b981;"></span>
          MongoDB Live &bull; ${res.database_name || "restaurant_management"} (${latency}ms)
        `;
      } else {
        statusText.innerHTML = `
          <span class="pulse-dot" style="background:#f59e0b;"></span>
          Backend Connected (${latency}ms)
        `;
      }
    } catch {
      statusText.innerHTML = `
        <span class="pulse-dot" style="background:#ef4444;"></span>
        Backend Offline (Check server on port 8000)
      `;
    }
  }

  function setupEvents() {
    const loginForm = document.getElementById("manual-login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", handleManualLogin);
    }

    const registerForm = document.getElementById("register-form");
    if (registerForm) {
      registerForm.addEventListener("submit", handleRegister);
    }
  }

  function switchTab(tab) {
    const signinTab = document.getElementById("tab-btn-signin");
    const registerTab = document.getElementById("tab-btn-register");
    const signinForm = document.getElementById("manual-login-form");
    const registerForm = document.getElementById("register-form");
    const alertBox = document.getElementById("login-alert");

    if (alertBox) alertBox.style.display = "none";
    if (window.Sound) Sound.click();

    if (tab === "signin") {
      signinTab.classList.add("active");
      registerTab.classList.remove("active");
      signinForm.style.display = "block";
      registerForm.style.display = "none";
      const emailInput = document.getElementById("login-email");
      if (emailInput) emailInput.focus();
    } else {
      signinTab.classList.remove("active");
      registerTab.classList.add("active");
      signinForm.style.display = "none";
      registerForm.style.display = "block";
      const nameInput = document.getElementById("reg-name");
      if (nameInput) nameInput.focus();
    }
  }

  function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (window.Sound) Sound.click();

    if (input.type === "password") {
      input.type = "text";
      btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;
    } else {
      input.type = "password";
      btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
    }
  }

  function checkPasswordStrength(password) {
    const box = document.getElementById("reg-password-strength-box");
    const fill = document.getElementById("reg-password-strength-fill");
    const text = document.getElementById("reg-password-strength-text");
    if (!box || !fill || !text) return;

    if (!password) {
      box.style.display = "none";
      return;
    }

    box.style.display = "flex";
    const len = password.length;
    let score = 0;

    if (len >= 6) score += 1;
    if (len >= 8) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;

    if (len < 6) {
      fill.style.width = "25%";
      fill.style.background = "#ef4444";
      text.textContent = "Too short (min 6 chars)";
      text.style.color = "#ef4444";
    } else if (score <= 2) {
      fill.style.width = "45%";
      fill.style.background = "#f59e0b";
      text.textContent = "Fair";
      text.style.color = "#f59e0b";
    } else if (score <= 4) {
      fill.style.width = "75%";
      fill.style.background = "#3b82f6";
      text.textContent = "Strong";
      text.style.color = "#60a5fa";
    } else {
      fill.style.width = "100%";
      fill.style.background = "#10b981";
      text.textContent = "Very Strong";
      text.style.color = "#34d399";
    }
  }

  function showAlert(msg, type = "danger") {
    const alertBox = document.getElementById("login-alert");
    if (!alertBox) return;

    alertBox.textContent = msg;
    alertBox.className = `login-alert ${type}`;
    alertBox.style.display = "flex";
  }

  async function quickRoleLogin(role, cardElement = null) {
    const account = PRESET_ACCOUNTS[role];
    if (!account) return;

    if (window.Sound) Sound.click();
    showAlert(`Authenticating as ${account.title}...`, "warning");

    const btn = cardElement ? cardElement.querySelector(".role-card-btn") : null;
    const originalBtnText = btn ? btn.innerHTML : "Login";
    if (btn) {
      btn.innerHTML = `<span style="display:inline-block; width:12px; height:12px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite; margin-right:4px; vertical-align:middle;"></span> Loading...`;
      btn.disabled = true;
    }

    try {
      const res = await API.auth.login(account.email, account.password);
      if (res && res.access_token) {
        API.setToken(res.access_token);
        API.setCurrentUser(res.user);
        if (window.Sound) Sound.success();
        showAlert(`Welcome back, ${res.user.name || account.title}! Launching workspace...`, "success");
        setTimeout(() => {
          window.location.href = "index.html";
        }, 300);
      } else {
        throw new Error("Invalid response received from authentication server.");
      }
    } catch (err) {
      if (btn) {
        btn.innerHTML = originalBtnText;
        btn.disabled = false;
      }
      if (window.Sound) Sound.error();
      showAlert(`Quick Login failed: ${err.message || "Please ensure the backend is active."}`, "danger");
    }
  }

  async function handleManualLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    if (!email || !password) {
      showAlert("Please enter both work email and password.", "danger");
      return;
    }

    if (window.Sound) Sound.click();
    setSubmitLoading("login-submit-btn", true, "Signing in...");
    showAlert("Verifying credentials...", "warning");

    try {
      const res = await API.auth.login(email, password);
      if (res && res.access_token) {
        API.setToken(res.access_token);
        API.setCurrentUser(res.user);
        if (window.Sound) Sound.success();
        showAlert(`Welcome back, ${res.user.name || res.user.email}! Redirecting...`, "success");
        setTimeout(() => {
          window.location.href = "index.html";
        }, 400);
      } else {
        throw new Error("No authorization token received.");
      }
    } catch (err) {
      setSubmitLoading("login-submit-btn", false, "Sign In to Workspace &rarr;");
      if (window.Sound) Sound.error();
      showAlert(err.message || "Invalid email or password. Please verify your credentials.", "danger");
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById("reg-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    const role = document.getElementById("reg-role").value || "WAITER";

    if (!name || !email || !password) {
      showAlert("Please fill in all registration fields.", "danger");
      return;
    }

    if (password.length < 6) {
      showAlert("Password must be at least 6 characters long.", "danger");
      return;
    }

    if (window.Sound) Sound.click();
    setSubmitLoading("register-submit-btn", true, "Creating Account...");
    showAlert("Provisioning new staff account...", "warning");

    try {
      const regRes = await API.auth.register({ name, email, password, role });
      
      // Auto-login with returned credentials or direct token
      if (regRes && regRes.access_token) {
        API.setToken(regRes.access_token);
        API.setCurrentUser(regRes.user || { name, email, role });
      } else {
        // Fallback login
        const loginRes = await API.auth.login(email, password);
        API.setToken(loginRes.access_token);
        API.setCurrentUser(loginRes.user);
      }

      if (window.Sound) Sound.success();
      showAlert("Account created successfully! Launching your workspace...", "success");
      setTimeout(() => {
        window.location.href = "index.html";
      }, 450);
    } catch (err) {
      setSubmitLoading("register-submit-btn", false, "Create Staff Account &rarr;");
      if (window.Sound) Sound.error();
      showAlert(`Registration failed: ${err.message}`, "danger");
    }
  }

  function setSubmitLoading(btnId, isLoading, defaultHtml) {
    const btn = document.getElementById(btnId);
    if (!btn) return;

    btn.disabled = isLoading;
    btn.innerHTML = isLoading
      ? `<span style="display:inline-block; width:16px; height:16px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite; margin-right:8px; vertical-align:middle;"></span> Processing...`
      : defaultHtml;
  }

  function fillDemo(role) {
    const acc = PRESET_ACCOUNTS[role];
    if (!acc) return;
    if (window.Sound) Sound.click();

    switchTab("signin");
    document.getElementById("login-email").value = acc.email;
    document.getElementById("login-password").value = acc.password;
    showAlert(`Loaded credentials for ${acc.title}. Click 'Sign In' to proceed.`, "warning");
  }

  function continueSession() {
    if (window.Sound) Sound.click();
    window.location.href = "index.html";
  }

  function clearSession() {
    API.setToken(null);
    API.setCurrentUser(null);
    const banner = document.getElementById("existing-session-banner");
    if (banner) banner.style.display = "none";
    if (window.Sound) Sound.pop();
    showAlert("Previous session cleared. Sign in or choose a demo station.", "success");
  }

  return {
    init,
    quickRoleLogin,
    switchTab,
    togglePasswordVisibility,
    checkPasswordStrength,
    fillDemo,
    continueSession,
    clearSession,
  };
})();

document.addEventListener("DOMContentLoaded", LoginController.init);
