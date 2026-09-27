/**
 * Inventory, Ingredients & Stock Tracking Module
 */

const InventoryView = (() => {
  let ingredients = [];
  let movements = [];

  async function init() {
    await refresh();
  }

  async function refresh() {
    await loadIngredients();
    await loadMovements();
    render();
  }

  async function loadIngredients() {
    try {
      ingredients = await API.inventory.getIngredients();
    } catch (e) {
      console.warn("Could not load ingredients:", e);
      ingredients = [];
    }
  }

  async function loadMovements() {
    try {
      movements = await API.inventory.getMovements();
    } catch (e) {
      console.warn("Could not load movements:", e);
      movements = [];
    }
  }

  function render() {
    renderIngredientsTable();
    renderMovementsTable();
  }

  function renderIngredientsTable() {
    const tableBody = document.getElementById("inventory-table-body");
    const countBadge = document.getElementById("inventory-total-count");
    if (!tableBody) return;

    if (countBadge) countBadge.textContent = `${ingredients.length} Items`;

    if (ingredients.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-dim);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📦</div>
            No ingredients in inventory.
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = ingredients.map(ing => {
      const id = ing.id || ing._id;
      const current = Number(ing.available_quantity?.$numberDecimal || ing.available_quantity || 0);
      const minLevel = Number(ing.minimum_stock_level?.$numberDecimal || ing.minimum_stock_level || 0);
      const cost = Number(ing.cost_per_unit?.$numberDecimal || ing.cost_per_unit || 0).toFixed(2);
      const unit = ing.unit || "unit";

      const ratio = minLevel > 0 ? (current / (minLevel * 2)) * 100 : 100;
      const barPercent = Math.min(100, Math.max(8, ratio));

      let barClass = "healthy";
      let statusBadge = '<span class="badge badge-green">In Stock</span>';

      if (current <= minLevel) {
        barClass = "danger";
        statusBadge = '<span class="badge badge-red">Low Stock</span>';
      } else if (current <= minLevel * 1.5) {
        barClass = "warning";
        statusBadge = '<span class="badge badge-amber">Restock Soon</span>';
      }

      return `
        <tr>
          <td style="font-weight: 700;">${ing.name}</td>
          <td>
            <div style="font-weight: 700; font-size: 0.95rem;">${current.toFixed(1)} ${unit}</div>
            <div class="stock-bar-wrapper">
              <div class="stock-bar ${barClass}" style="width: ${barPercent}%;"></div>
            </div>
          </td>
          <td>${minLevel} ${unit}</td>
          <td>₹${cost} / ${unit}</td>
          <td>${ing.supplier_name || 'Local Farm'}</td>
          <td>${statusBadge}</td>
          <td>
            <button class="btn btn-primary btn-sm" onclick="InventoryView.openRestockModal('${id}', '${ing.name}', '${unit}')">+ Restock</button>
          </td>
        </tr>
      `;
    }).join("");
  }

  function renderMovementsTable() {
    const tableBody = document.getElementById("movements-table-body");
    if (!tableBody) return;

    if (movements.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-dim);">
            No stock movements logged.
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = movements.slice(0, 15).map(m => {
      const type = m.movement_type || "RESTOCK";
      const qty = Number(m.quantity?.$numberDecimal || m.quantity || 0);
      const isPositive = type === "RESTOCK" || type === "PURCHASE";
      const dateStr = m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-';

      return `
        <tr>
          <td style="font-weight: 600;">${m.ingredient_id ? m.ingredient_id.slice(-6) : '-'}</td>
          <td><span class="badge ${isPositive ? 'badge-green' : 'badge-amber'}">${type}</span></td>
          <td style="font-weight: 700; color: ${isPositive ? 'var(--color-success)' : 'var(--color-danger)'};">
            ${isPositive ? '+' : '-'}${qty}
          </td>
          <td>${m.reason || 'Inventory operation'}</td>
          <td style="font-size: 0.78rem; color: var(--text-dim);">${dateStr}</td>
        </tr>
      `;
    }).join("");
  }

  function openAddModal() {
    App.openModal("add-ingredient-modal");
  }

  async function submitAddIngredient() {
    const name = document.getElementById("ing-name-input")?.value?.trim();
    const unit = document.getElementById("ing-unit-input")?.value?.trim();
    const available = Number(document.getElementById("ing-qty-input")?.value || 0);
    const minLevel = Number(document.getElementById("ing-min-input")?.value || 0);
    const cost = Number(document.getElementById("ing-cost-input")?.value || 0);
    const supplier = document.getElementById("ing-supplier-input")?.value?.trim() || null;

    if (!name || !unit) {
      App.showToast("Name and unit are required", "warning");
      return;
    }

    try {
      App.showLoader(true);
      await API.inventory.createIngredient({
        name,
        unit,
        available_quantity: available,
        minimum_stock_level: minLevel,
        cost_per_unit: cost,
        supplier_name: supplier,
        is_active: true
      });
      App.showToast(`Ingredient "${name}" added to inventory!`, "success");
      App.closeModal("add-ingredient-modal");
      await refresh();
    } catch (e) {
      App.showToast(`Error: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  function openRestockModal(ingredientId, name, unit) {
    const idInput = document.getElementById("restock-ing-id");
    const nameLabel = document.getElementById("restock-ing-name");
    const unitLabel = document.getElementById("restock-ing-unit");

    if (idInput) idInput.value = ingredientId;
    if (nameLabel) nameLabel.textContent = name;
    if (unitLabel) unitLabel.textContent = unit;

    App.openModal("restock-modal");
  }

  async function submitRestock() {
    const ingredientId = document.getElementById("restock-ing-id")?.value;
    const qty = Number(document.getElementById("restock-qty-input")?.value || 0);

    if (!ingredientId || qty <= 0) {
      App.showToast("Enter a valid quantity", "warning");
      return;
    }

    try {
      App.showLoader(true);
      await API.inventory.updateStock(ingredientId, qty);
      App.showToast(`Restocked ${qty} units successfully!`, "success");
      App.closeModal("restock-modal");
      await refresh();
    } catch (e) {
      App.showToast(`Restock failed: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  return {
    init,
    refresh,
    openAddModal,
    submitAddIngredient,
    openRestockModal,
    submitRestock
  };
})();
