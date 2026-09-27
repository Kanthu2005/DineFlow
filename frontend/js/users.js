/**
 * Staff & User Management Module
 */

const UsersView = (() => {
  let usersList = [];

  async function init() {
    await refresh();
  }

  async function refresh() {
    try {
      usersList = await API.users.getAll();
      render();
    } catch (e) {
      console.warn("Could not load users:", e);
      usersList = [];
      render();
    }
  }

  function render() {
    const tableBody = document.getElementById("users-table-body");
    const countBadge = document.getElementById("users-total-count");
    if (!tableBody) return;

    if (countBadge) countBadge.textContent = `${usersList.length} Staff`;

    if (usersList.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-dim);">
            No user accounts found.
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = usersList.map(u => {
      const id = u.id || u._id;
      const role = (u.role || "WAITER").toUpperCase();
      const isActive = u.is_active !== false;

      return `
        <tr>
          <td style="font-weight: 700;">${u.name || 'Staff Member'}</td>
          <td>${u.email}</td>
          <td>${getRoleBadge(role)}</td>
          <td>
            <span class="badge ${isActive ? 'badge-green' : 'badge-red'}">
              ${isActive ? 'Active' : 'Inactive'}
            </span>
          </td>
          <td>
            <button class="btn btn-danger btn-sm" onclick="UsersView.deleteUser('${id}')">Remove</button>
          </td>
        </tr>
      `;
    }).join("");
  }

  function getRoleBadge(role) {
    switch (role) {
      case "ADMIN": return '<span class="badge badge-purple">Admin</span>';
      case "MANAGER": return '<span class="badge badge-blue">Manager</span>';
      case "CHEF": return '<span class="badge badge-amber">Chef</span>';
      case "WAITER": return '<span class="badge badge-green">Waiter</span>';
      case "CASHIER": return '<span class="badge badge-muted">Cashier</span>';
      default: return `<span class="badge badge-muted">${role}</span>`;
    }
  }

  function openAddModal() {
    App.openModal("add-user-modal");
  }

  async function submitAddUser() {
    const name = document.getElementById("new-user-name")?.value?.trim();
    const email = document.getElementById("new-user-email")?.value?.trim();
    const password = document.getElementById("new-user-password")?.value;
    const role = document.getElementById("new-user-role")?.value || "WAITER";

    if (!name || !email || !password) {
      App.showToast("All fields are required", "warning");
      return;
    }

    try {
      App.showLoader(true);
      try {
        await API.users.create({
          name,
          email,
          password,
          role,
          is_active: true
        });
      } catch (err) {
        // Fallback to auth.register
        await API.auth.register({ name, email, password, role });
      }

      if (window.Sound) Sound.success();
      App.showToast(`Staff account for ${name} (${role}) created successfully!`, "success");
      App.closeModal("add-user-modal");

      // Reset form
      const nameInput = document.getElementById("new-user-name");
      const emailInput = document.getElementById("new-user-email");
      if (nameInput) nameInput.value = "";
      if (emailInput) emailInput.value = "";

      await refresh();
    } catch (e) {
      if (window.Sound) Sound.error();
      App.showToast(`Failed: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  async function deleteUser(id) {
    if (!confirm("Are you sure you want to remove this staff user?")) return;

    try {
      App.showLoader(true);
      await API.users.delete(id);
      App.showToast("Staff user removed", "success");
      await refresh();
    } catch (e) {
      App.showToast(`Delete failed: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  return {
    init,
    refresh,
    openAddModal,
    submitAddUser,
    deleteUser
  };
})();
