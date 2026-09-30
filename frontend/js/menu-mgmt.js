/**
 * Menu Administration Module (Categories & Dishes)
 * Full CRUD support: Add, Edit, Live Preview, Toggle Availability, and Delete dishes & categories.
 * Robust optimistic updates and seamless POS synchronisation.
 */

const MenuMgmt = (() => {
  let categories = [];
  let items = [];
  let pendingDeleteDishId = null;
  let pendingDeleteDishName = null;
  let pendingDeleteCatId = null;
  let pendingDeleteCatName = null;

  // Filter state for Menu Catalog table
  let searchQuery = "";
  let filterCatId = "all";
  let activeDietFilter = "all"; // "all" | "veg" | "nonveg"

  const CANONICAL_CATEGORIES = [
    "Veg Starters",
    "Non-Veg Starters",
    "Veg Main Course",
    "Non-Veg Main Course",
    "Biryani",
    "Rice & Noodles",
    "Breads",
    "Desserts",
    "Beverages"
  ];

  // Curated food images for fallback and presets
  const DEFAULT_FOOD_IMAGES = {
    veg: "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
    nonveg: "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
    biryani: "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
    bread: "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
    sweet: "https://images.unsplash.com/photo-1553787499-6f9133860278?w=600&auto=format&fit=crop&q=80",
    curry: "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
    starter: "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
    beverage: "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80"
  };

  async function init() {
    await refresh();
  }

  async function refresh() {
    await loadCategories();
    await loadItems();
    render();
  }

  async function loadCategories() {
    try {
      const res = await API.menu.getCategories();
      const rawCats = Array.isArray(res) ? res : [];
      categories = rawCats.sort((a, b) => {
        const idxA = CANONICAL_CATEGORIES.indexOf(a.name);
        const idxB = CANONICAL_CATEGORIES.indexOf(b.name);
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        if (idxA !== -1) return -1;
        if (idxB !== -1) return 1;
        return a.name.localeCompare(b.name);
      });
    } catch (e) {
      console.warn("Could not load categories:", e);
      categories = [];
    }
  }

  async function loadItems() {
    try {
      const res = await API.menu.getItems();
      items = Array.isArray(res) ? res : [];
    } catch (e) {
      console.warn("Could not load items:", e);
      items = [];
    }
  }

  function getCategories() {
    return categories;
  }

  function getItems() {
    return items;
  }

  function getItem(id) {
    return items.find(i => (i.id || i._id) === id);
  }

  function render() {
    renderStats();
    populateCategoryFilter();
    renderItemsTable();
    renderCategoriesTable();
  }

  function renderStats() {
    const totalCountBadge = document.getElementById("menu-items-count-badge");
    if (totalCountBadge) {
      totalCountBadge.textContent = `${items.length} Dishes`;
    }

    const statTotal = document.getElementById("menu-stat-total-dishes");
    const statCats = document.getElementById("menu-stat-total-cats");
    const statVeg = document.getElementById("menu-stat-veg-dishes");
    const statNonveg = document.getElementById("menu-stat-nonveg-dishes");

    if (statTotal) statTotal.textContent = items.length;
    if (statCats) statCats.textContent = categories.length;
    if (statVeg) statVeg.textContent = items.filter(i => i.is_vegetarian).length;
    if (statNonveg) statNonveg.textContent = items.filter(i => !i.is_vegetarian).length;
  }

  function populateCategoryFilter() {
    const filterSelect = document.getElementById("menu-mgmt-category-filter");
    if (!filterSelect) return;

    const currentVal = filterSelect.value || filterCatId;
    let html = `<option value="all">📁 All Categories (${items.length})</option>`;
    categories.forEach(cat => {
      const cid = cat.id || cat._id;
      const count = items.filter(i => {
        const iCat = typeof i.category_id === "object" ? (i.category_id?.$oid || i.category_id?.id) : i.category_id;
        return iCat === cid || iCat === cat.name;
      }).length;
      html += `<option value="${cid}">${cat.name} (${count})</option>`;
    });

    filterSelect.innerHTML = html;
    filterSelect.value = currentVal;
  }

  function getCategoryName(catId) {
    if (!catId) return "General";
    const rawId = typeof catId === "object" ? (catId.$oid || catId.id || String(catId)) : String(catId);
    const found = categories.find(c => (c.id === rawId || c._id === rawId || c.name === rawId));
    return found ? found.name : rawId;
  }

  function escapeAttr(text) {
    if (!text) return "";
    return String(text).replace(/'/g, "\\'").replace(/"/g, "&quot;");
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Search & Filter handlers
  function searchDishes(val) {
    searchQuery = (val || "").toLowerCase().trim();
    renderItemsTable();
  }

  function filterCategory(catId) {
    filterCatId = catId || "all";
    renderItemsTable();
  }

  function filterDiet(diet) {
    activeDietFilter = diet || "all";
    document.querySelectorAll(".menu-mgmt-diet-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.diet === diet);
    });
    renderItemsTable();
  }

  function renderItemsTable() {
    const tableBody = document.getElementById("menu-items-table-body");
    if (!tableBody) return;

    if (items.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 3rem; color: var(--text-dim);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🍽️</div>
            <p style="font-size: 1rem; font-weight: 600; color: var(--text-main);">No dishes found in menu catalog</p>
            <span style="font-size: 0.85rem; display: block; margin-bottom: 1rem;">Click "+ Add Dish" above to create your first offering</span>
            <button class="btn btn-primary btn-sm" onclick="MenuMgmt.openAddItemModal()">+ Add Dish</button>
          </td>
        </tr>`;
      return;
    }

    let filtered = items;

    // Filter by Category
    if (filterCatId && filterCatId !== "all") {
      const activeCat = categories.find(c => (c.id === filterCatId || c._id === filterCatId));
      filtered = filtered.filter(i => {
        const raw = typeof i.category_id === "object"
          ? (i.category_id?.$oid || i.category_id?.id || i.category_id?._id || String(i.category_id))
          : String(i.category_id || "");
        return raw === filterCatId || (activeCat && raw === activeCat.name);
      });
    }

    // Filter by Diet
    if (activeDietFilter === "veg") {
      filtered = filtered.filter(i => i.is_vegetarian === true);
    } else if (activeDietFilter === "nonveg") {
      filtered = filtered.filter(i => i.is_vegetarian === false);
    }

    // Filter by Search Query (searches across name, description, category, and diet)
    if (searchQuery) {
      filtered = filtered.filter(i => {
        const nameMatch = (i.name || "").toLowerCase().includes(searchQuery);
        const descMatch = (i.description || "").toLowerCase().includes(searchQuery);
        const catMatch = getCategoryName(i.category_id).toLowerCase().includes(searchQuery);
        const dietMatch = (searchQuery === "veg" && i.is_vegetarian) ||
                          ((searchQuery === "nonveg" || searchQuery === "non-veg" || searchQuery === "non veg") && !i.is_vegetarian);
        return nameMatch || descMatch || catMatch || dietMatch;
      });
    }

    if (filtered.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 2.5rem; color: var(--text-dim);">
            <div style="font-size: 2rem; margin-bottom: 0.35rem;">🔍</div>
            <p style="font-weight: 600; color: var(--text-main);">No dishes match your filter criteria</p>
            <span style="font-size: 0.85rem;">Try adjusting search terms or clearing the filters</span>
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = filtered.map(item => {
      const id = item.id || item._id;
      const price = Number(item.price?.$numberDecimal || item.price || 0).toFixed(2);
      const isAvailable = item.is_available !== false;
      const isVeg = item.is_vegetarian;
      const catName = getCategoryName(item.category_id);
      const imgHtml = item.image_url 
        ? `<img src="${item.image_url}" class="dish-table-thumb" alt="${escapeHtml(item.name)}" onerror="this.onerror=null; this.src='${DEFAULT_FOOD_IMAGES.veg}';">`
        : `<div class="dish-table-thumb" style="display:flex; align-items:center; justify-content:center; font-size:1.3rem; background:rgba(245,158,11,0.12);">🍛</div>`;

      return `
        <tr data-table-dish-id="${id}">
          <td>
            <div class="dish-table-row-img">
              ${imgHtml}
              <div>
                <span style="font-weight: 700; color: #fff; font-size: 0.95rem;">${escapeHtml(item.name)}</span>
                <div style="font-size: 0.78rem; color: var(--accent-primary); font-weight: 600;">${escapeHtml(catName)}</div>
              </div>
            </div>
          </td>
          <td>
            <span class="badge ${isVeg ? 'badge-green' : 'badge-red'}">
              ${isVeg ? '🟢 Pure Veg' : '🔴 Non-Veg'}
            </span>
          </td>
          <td style="font-weight: 800; color: #10b981; font-size: 1.05rem;">₹${price}</td>
          <td style="color: var(--text-muted); font-size: 0.88rem;">⏱️ ${item.preparation_time || 15} mins</td>
          <td>
            <span class="badge ${isAvailable ? 'badge-green' : 'badge-amber'}">
              ${isAvailable ? 'Available' : 'Sold Out'}
            </span>
          </td>
          <td>
            <div style="display: flex; gap: 0.45rem; align-items: center;">
              <button class="btn btn-secondary btn-sm" onclick="MenuMgmt.openEditItemModal('${id}')" title="Edit dish details" style="padding: 0.35rem 0.65rem; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 0.25rem;">
                <span>✏️</span> Edit
              </button>
              <button class="btn btn-secondary btn-sm" onclick="MenuMgmt.toggleAvailability('${id}', ${isAvailable})" title="Toggle dish availability" style="font-size: 0.78rem; padding: 0.35rem 0.65rem;">
                ${isAvailable ? 'Mark Sold Out' : 'Mark Available'}
              </button>
              <button class="btn btn-danger btn-sm" onclick="MenuMgmt.promptDeleteDish('${id}')" title="Permanently delete dish from menu" style="padding: 0.35rem 0.7rem; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 0.25rem;">
                <span>🗑️</span> Delete
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  function renderCategoriesTable() {
    const tableBody = document.getElementById("menu-cat-table-body");
    if (!tableBody) return;

    if (categories.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="4" style="text-align: center; padding: 2.5rem; color: var(--text-dim);">
            No categories available. Click "+ Add Category" to create one.
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = categories.map(cat => {
      const catId = cat.id || cat._id;
      const count = items.filter(i => {
        const iCat = typeof i.category_id === "object" ? (i.category_id?.$oid || i.category_id?.id) : i.category_id;
        return iCat === catId || iCat === cat.name;
      }).length;

      return `
        <tr>
          <td style="font-weight: 700; color: #fff; font-size: 0.95rem;">${escapeHtml(cat.name)}</td>
          <td style="color: var(--text-muted); font-size: 0.85rem;">${escapeHtml(cat.description || 'Delicious culinary assortment.')}</td>
          <td><span class="badge badge-purple" style="font-weight: 700;">${count} Dishes</span></td>
          <td>
            <button class="btn btn-danger btn-sm" onclick="MenuMgmt.promptDeleteCategory('${catId}', '${escapeAttr(cat.name)}')" title="Delete '${escapeAttr(cat.name)}' category" style="padding: 0.35rem 0.65rem; font-size: 0.75rem;">
              🗑️ Delete
            </button>
          </td>
        </tr>
      `;
    }).join("");
  }

  // Synchronise Diet radio buttons cleanly
  function setDishDiet(isVeg, isEdit = false) {
    const prefix = isEdit ? "edit-" : "";
    const vegRadio = document.getElementById(`${prefix}dish-diet-radio-veg`);
    const nonvegRadio = document.getElementById(`${prefix}dish-diet-radio-nonveg`);
    const vegCheckbox = document.getElementById(`${prefix}dish-veg-input`);

    if (vegRadio) vegRadio.checked = isVeg;
    if (nonvegRadio) nonvegRadio.checked = !isVeg;
    if (vegCheckbox) vegCheckbox.checked = isVeg;

    if (isEdit) {
      updateEditLivePreview();
    } else {
      updateLivePreview();
    }
  }

  // Auto-detect dietary type based on category name
  function autoSyncDietFromCategory(catIdOrName, isEdit = false) {
    if (!catIdOrName) return;
    const cat = categories.find(c => (c.id === catIdOrName || c._id === catIdOrName || c.name === catIdOrName));
    const name = (cat ? cat.name : catIdOrName).toLowerCase();
    
    if (name.includes("non-veg") || name.includes("non veg")) {
      setDishDiet(false, isEdit);
    } else if (name.includes("veg")) {
      setDishDiet(true, isEdit);
    }
  }

  async function openAddItemModal(preferredCatId = null) {
    await loadCategories();
    
    const select = document.getElementById("dish-category-select");
    const newCatGroup = document.getElementById("dish-new-cat-inline-group");
    if (newCatGroup) newCatGroup.style.display = "none";

    if (select) {
      let optionsHtml = "";
      if (categories.length === 0) {
        optionsHtml = `<option value="">-- No existing categories --</option>`;
      } else {
        optionsHtml = categories.map(c => {
          const cid = c.id || c._id;
          const isSelected = (preferredCatId && (preferredCatId === cid || preferredCatId === c.name)) ? "selected" : "";
          return `<option value="${cid}" ${isSelected}>${c.name}</option>`;
        }).join("");
      }
      optionsHtml += `<option value="__NEW__">➕ Create New Category...</option>`;
      select.innerHTML = optionsHtml;

      select.onchange = () => {
        if (newCatGroup) {
          const isNew = select.value === "__NEW__";
          newCatGroup.style.display = isNew ? "block" : "none";
          if (isNew) {
            const newCatInput = document.getElementById("dish-new-cat-inline-input");
            if (newCatInput) {
              newCatInput.value = "";
              newCatInput.focus();
            }
          }
        }
        autoSyncDietFromCategory(select.value, false);
        updateLivePreview();
      };
    }

    // Reset input fields
    const nameInput = document.getElementById("dish-name-input");
    if (nameInput) nameInput.value = "";
    const priceInput = document.getElementById("dish-price-input");
    if (priceInput) priceInput.value = "250.00";
    const prepInput = document.getElementById("dish-prep-input");
    if (prepInput) prepInput.value = "15";
    const imgInput = document.getElementById("dish-image-input");
    if (imgInput) imgInput.value = "";
    const descInput = document.getElementById("dish-desc-input");
    if (descInput) descInput.value = "";

    // Reset diet to Veg by default or synced with preferred category
    setDishDiet(true, false);
    if (preferredCatId) {
      autoSyncDietFromCategory(preferredCatId, false);
    }

    // Attach live preview listeners
    [nameInput, priceInput, prepInput, imgInput, descInput].forEach(el => {
      if (el) el.oninput = updateLivePreview;
    });

    updateLivePreview();
    App.openModal("add-dish-modal");

    setTimeout(() => {
      if (nameInput) nameInput.focus();
    }, 120);
  }

  function updateLivePreview() {
    const previewName = document.getElementById("modal-dish-preview-name");
    const previewPrice = document.getElementById("modal-dish-preview-price");
    const previewDesc = document.getElementById("modal-dish-preview-desc");
    const previewTime = document.getElementById("modal-dish-preview-time");
    const previewImg = document.getElementById("modal-dish-preview-img");
    const previewDiet = document.getElementById("modal-dish-preview-diet");

    const name = document.getElementById("dish-name-input")?.value?.trim() || "Royal Paneer Tikka";
    const priceVal = document.getElementById("dish-price-input")?.value?.replace(/[^0-9.]/g, "") || "250.00";
    const prep = document.getElementById("dish-prep-input")?.value || "15";
    const vegRadio = document.getElementById("dish-diet-radio-veg");
    const isVeg = vegRadio ? vegRadio.checked : (document.getElementById("dish-veg-input")?.checked ?? true);
    const desc = document.getElementById("dish-desc-input")?.value?.trim() || "Authentic chef recipe cooked fresh with finest aromatic spices.";
    let img = document.getElementById("dish-image-input")?.value?.trim();

    if (!img) {
      img = isVeg ? DEFAULT_FOOD_IMAGES.veg : DEFAULT_FOOD_IMAGES.nonveg;
    }

    if (previewName) previewName.textContent = name;
    if (previewPrice) previewPrice.textContent = `₹${parseFloat(priceVal || 0).toFixed(2)}`;
    if (previewDesc) previewDesc.textContent = desc;
    if (previewTime) previewTime.textContent = `⏱️ ${prep}m`;
    if (previewImg) previewImg.src = img;
    if (previewDiet) {
      previewDiet.className = `diet-icon-mark ${isVeg ? 'veg' : 'nonveg'}`;
      previewDiet.title = isVeg ? "Pure Vegetarian" : "Non-Vegetarian";
    }
  }

  function selectPresetImage(url, forceVeg = null, catName = null) {
    const imgInput = document.getElementById("dish-image-input");
    if (imgInput) {
      imgInput.value = url;
    }
    if (catName) {
      const select = document.getElementById("dish-category-select");
      if (select) {
        const found = Array.from(select.options).find(opt => opt.text.trim().toLowerCase() === catName.toLowerCase());
        if (found) {
          select.value = found.value;
        }
      }
    }
    if (forceVeg !== null) {
      setDishDiet(forceVeg, false);
    } else {
      updateLivePreview();
    }
    App.showToast("Sample photo selected!", "info");
  }

  async function submitAddItem() {
    const name = document.getElementById("dish-name-input")?.value?.trim();
    let categoryId = document.getElementById("dish-category-select")?.value;
    const priceRaw = String(document.getElementById("dish-price-input")?.value || "");
    const cleanPrice = parseFloat(priceRaw.replace(/[^0-9.]/g, ""));
    const prepTime = parseInt(document.getElementById("dish-prep-input")?.value || "15", 10) || 15;
    const vegRadio = document.getElementById("dish-diet-radio-veg");
    const isVeg = vegRadio ? vegRadio.checked : (document.getElementById("dish-veg-input")?.checked ?? true);
    const desc = document.getElementById("dish-desc-input")?.value?.trim() || "";
    let imageUrl = document.getElementById("dish-image-input")?.value?.trim() || null;

    if (!name || name.length < 2) {
      App.showToast("Dish name is required (minimum 2 characters)", "warning");
      document.getElementById("dish-name-input")?.focus();
      return;
    }

    // Handle new category creation inline
    if (!categoryId || categoryId === "__NEW__") {
      const newCatInput = document.getElementById("dish-new-cat-inline-input");
      const newCatName = newCatInput?.value?.trim();
      if (!newCatName) {
        const newCatGroup = document.getElementById("dish-new-cat-inline-group");
        if (newCatGroup) newCatGroup.style.display = "block";
        App.showToast("Please enter a name for the new category", "warning");
        if (newCatInput) newCatInput.focus();
        return;
      }
      try {
        App.showLoader(true);
        const createdCat = await API.menu.createCategory({ name: newCatName });
        categoryId = createdCat.id || createdCat._id || createdCat.name;
        await loadCategories();
      } catch (e) {
        App.showToast(`Category setup error: ${e.message}`, "error");
        App.showLoader(false);
        return;
      }
    }

    if (!categoryId) {
      App.showToast("Please select or create a category", "warning");
      return;
    }

    if (isNaN(cleanPrice) || cleanPrice <= 0) {
      App.showToast("Please enter a valid price in ₹ greater than 0", "warning");
      document.getElementById("dish-price-input")?.focus();
      return;
    }

    // Smart default image fallback if empty
    if (!imageUrl) {
      const lower = name.toLowerCase();
      if (lower.includes("biryani") || lower.includes("pulao")) {
        imageUrl = DEFAULT_FOOD_IMAGES.biryani;
      } else if (lower.includes("naan") || lower.includes("roti") || lower.includes("paratha") || lower.includes("bread")) {
        imageUrl = DEFAULT_FOOD_IMAGES.bread;
      } else if (lower.includes("jamun") || lower.includes("sweet") || lower.includes("dessert") || lower.includes("halwa")) {
        imageUrl = DEFAULT_FOOD_IMAGES.sweet;
      } else if (lower.includes("curry") || lower.includes("masala") || lower.includes("korma") || lower.includes("dal")) {
        imageUrl = DEFAULT_FOOD_IMAGES.curry;
      } else if (lower.includes("tikka") || lower.includes("kebab") || lower.includes("starter")) {
        imageUrl = DEFAULT_FOOD_IMAGES.starter;
      } else if (lower.includes("lassi") || lower.includes("chai") || lower.includes("drink") || lower.includes("beverage") || lower.includes("juice")) {
        imageUrl = DEFAULT_FOOD_IMAGES.beverage;
      } else {
        imageUrl = isVeg ? DEFAULT_FOOD_IMAGES.veg : DEFAULT_FOOD_IMAGES.nonveg;
      }
    }

    try {
      App.showLoader(true);
      const createdItem = await API.menu.createItem({
        name,
        category_id: categoryId,
        price: cleanPrice,
        preparation_time: prepTime > 0 ? prepTime : 15,
        is_vegetarian: isVeg,
        is_available: true,
        description: desc || "Authentic chef recipe cooked fresh with finest aromatic spices.",
        image_url: imageUrl,
      });

      App.showToast(`✅ Dish "${name}" added to menu successfully!`, "success");
      App.closeModal("add-dish-modal");
      
      // Refresh both Menu Administration & POS Restaurant Menu
      await refresh();
      if (window.POS && typeof POS.onNewItemAdded === "function") {
        await POS.onNewItemAdded(createdItem?.id || createdItem?._id || categoryId);
      } else if (window.POS && typeof POS.refresh === "function") {
        await POS.refresh();
      }

      // Highlight the newly created dish row
      const newId = createdItem?.id || createdItem?._id;
      if (newId) {
        setTimeout(() => {
          const row = document.querySelector(`tr[data-table-dish-id="${newId}"]`);
          if (row) {
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            row.style.transition = "background-color 0.5s ease";
            row.style.backgroundColor = "rgba(16, 185, 129, 0.25)";
            setTimeout(() => { row.style.backgroundColor = ""; }, 2500);
          }
        }, 150);
      }
    } catch (e) {
      App.showToast(`Error adding dish: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  // ================= DELETE DISH FLOW =================
  function promptDeleteDish(itemId) {
    const item = items.find(i => (i.id || i._id) === itemId) || (window.POS && POS.getItem(itemId));
    if (!item) {
      // Direct delete fallback
      deleteItem(itemId, "this dish");
      return;
    }

    pendingDeleteDishId = itemId;
    pendingDeleteDishName = item.name;

    const confirmBtn = document.getElementById("confirm-delete-dish-btn");
    if (confirmBtn) {
      confirmBtn.dataset.itemId = itemId;
      confirmBtn.dataset.itemName = item.name;
    }

    const imgEl = document.getElementById("delete-dish-img");
    const nameEl = document.getElementById("delete-dish-name");
    const dietEl = document.getElementById("delete-dish-diet-badge");
    const priceEl = document.getElementById("delete-dish-price");

    if (imgEl) {
      imgEl.src = item.image_url || (item.is_vegetarian ? DEFAULT_FOOD_IMAGES.veg : DEFAULT_FOOD_IMAGES.nonveg);
    }
    if (nameEl) nameEl.textContent = item.name;
    if (dietEl) {
      dietEl.className = `badge ${item.is_vegetarian ? 'badge-green' : 'badge-red'}`;
      dietEl.textContent = item.is_vegetarian ? '🟢 Pure Veg' : '🔴 Non-Veg';
    }
    if (priceEl) {
      const p = Number(item.price?.$numberDecimal || item.price || 0).toFixed(2);
      priceEl.textContent = `₹${p}`;
    }

    App.openModal("delete-dish-modal");
  }

  async function confirmDeleteDish(fallbackId = null, fallbackName = null) {
    const confirmBtn = document.getElementById("confirm-delete-dish-btn");
    const itemId = pendingDeleteDishId || confirmBtn?.dataset?.itemId || fallbackId;
    const itemName = pendingDeleteDishName || confirmBtn?.dataset?.itemName || fallbackName;
    pendingDeleteDishId = null;
    pendingDeleteDishName = null;
    if (confirmBtn) {
      delete confirmBtn.dataset.itemId;
      delete confirmBtn.dataset.itemName;
    }

    App.closeModal("delete-dish-modal");
    if (itemId) {
      await deleteItem(itemId, itemName);
    }
  }

  async function deleteItem(itemId, itemName) {
    const label = itemName || "this dish";
    
    // Optimistic UI Removal: remove immediately from local items array and re-render
    const previousItems = [...items];
    items = items.filter(i => (i.id || i._id) !== itemId);
    renderStats();
    renderItemsTable();

    // If POS has this item in cart or view, remove it immediately
    if (window.POS && typeof POS.removeDishFromDisplay === "function") {
      POS.removeDishFromDisplay(itemId);
    } else if (window.POS && typeof POS.removeItem === "function") {
      POS.removeItem(itemId);
    }

    try {
      App.showLoader(true);
      await API.menu.deleteItem(itemId);
      App.showToast(`🗑️ "${label}" permanently removed from menu!`, "success");
      
      // Resync data in background
      await refresh();
      if (window.POS && typeof POS.refresh === "function") {
        await POS.refresh();
      }
    } catch (e) {
      // Rollback on error
      items = previousItems;
      renderStats();
      renderItemsTable();
      if (window.POS && typeof POS.refresh === "function") {
        await POS.refresh();
      }
      App.showToast(`Error deleting dish: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  // ================= DELETE CATEGORY FLOW =================
  function promptDeleteCategory(catId, catName) {
    pendingDeleteCatId = catId;
    pendingDeleteCatName = catName;

    const confirmBtn = document.getElementById("confirm-delete-cat-btn");
    if (confirmBtn) {
      confirmBtn.dataset.catId = catId;
      confirmBtn.dataset.catName = catName;
    }

    const nameEl = document.getElementById("delete-cat-name");
    if (nameEl) nameEl.textContent = catName;

    App.openModal("delete-category-modal");
  }

  async function confirmDeleteCategory(fallbackId = null, fallbackName = null) {
    const confirmBtn = document.getElementById("confirm-delete-cat-btn");
    const catId = pendingDeleteCatId || confirmBtn?.dataset?.catId || fallbackId;
    const catName = pendingDeleteCatName || confirmBtn?.dataset?.catName || fallbackName || "Category";
    pendingDeleteCatId = null;
    pendingDeleteCatName = null;
    if (confirmBtn) {
      delete confirmBtn.dataset.catId;
      delete confirmBtn.dataset.catName;
    }

    App.closeModal("delete-category-modal");

    if (!catId) return;

    // Optimistic removal from categories array
    const prevCats = [...categories];
    categories = categories.filter(c => (c.id || c._id) !== catId);
    renderStats();
    populateCategoryFilter();
    renderCategoriesTable();

    try {
      App.showLoader(true);
      await API.menu.deleteCategory(catId);
      App.showToast(`🗑️ Category "${catName}" deleted!`, "success");
      await refresh();
      if (window.POS && typeof POS.refresh === "function") {
        await POS.refresh();
      }
    } catch (e) {
      categories = prevCats;
      renderStats();
      populateCategoryFilter();
      renderCategoriesTable();
      App.showToast(`Error deleting category: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  function openAddCategoryModal() {
    const nameInput = document.getElementById("cat-name-input");
    if (nameInput) nameInput.value = "";
    const descInput = document.getElementById("cat-desc-input");
    if (descInput) descInput.value = "";
    App.openModal("add-category-modal");
    setTimeout(() => {
      if (nameInput) nameInput.focus();
    }, 120);
  }

  async function submitAddCategory() {
    const name = document.getElementById("cat-name-input")?.value?.trim();
    const desc = document.getElementById("cat-desc-input")?.value?.trim() || "";

    if (!name || name.length < 2) {
      App.showToast("Category name is required (min 2 characters)", "warning");
      document.getElementById("cat-name-input")?.focus();
      return;
    }

    try {
      App.showLoader(true);
      const newCat = await API.menu.createCategory({ name, description: desc });
      App.showToast(`Category "${name}" created!`, "success");
      App.closeModal("add-category-modal");
      await loadCategories();

      // If add-dish-modal is currently open, refresh its select and auto-select this new category!
      const addDishModal = document.getElementById("add-dish-modal");
      if (addDishModal && addDishModal.classList.contains("show")) {
        const select = document.getElementById("dish-category-select");
        if (select) {
          const newCatId = newCat?.id || newCat?._id || newCat?.name || name;
          let optionsHtml = categories.map(c => {
            const cid = c.id || c._id;
            const isSelected = (cid === newCatId || c.name === name) ? "selected" : "";
            return `<option value="${cid}" ${isSelected}>${c.name}</option>`;
          }).join("");
          optionsHtml += `<option value="__NEW__">➕ Create New Category...</option>`;
          select.innerHTML = optionsHtml;
          select.value = newCatId;
          const inlineGroup = document.getElementById("dish-new-cat-inline-group");
          if (inlineGroup) inlineGroup.style.display = "none";
        }
      }

      await refresh();
      if (window.POS && typeof POS.refresh === "function") await POS.refresh();
    } catch (e) {
      App.showToast(`Error creating category: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  async function toggleAvailability(itemId, current) {
    try {
      App.showLoader(true);
      await API.menu.updateItem(itemId, { is_available: !current });
      App.showToast(`Dish marked ${!current ? 'Available' : 'Sold Out'}`, "success");
      await refresh();
      if (window.POS && typeof POS.refresh === "function") await POS.refresh();
    } catch (e) {
      App.showToast(`Error: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  // ================= EDIT DISH WORKFLOW =================
  async function openEditItemModal(itemId) {
    await loadCategories();
    const item = items.find(i => (i.id || i._id) === itemId);
    if (!item) {
      App.showToast("Dish details not found", "error");
      return;
    }

    const idInput = document.getElementById("edit-dish-id");
    const nameInput = document.getElementById("edit-dish-name-input");
    const categorySelect = document.getElementById("edit-dish-category-select");
    const priceInput = document.getElementById("edit-dish-price-input");
    const prepInput = document.getElementById("edit-dish-prep-input");
    const imgInput = document.getElementById("edit-dish-image-input");
    const descInput = document.getElementById("edit-dish-desc-input");

    if (idInput) idInput.value = itemId;
    if (nameInput) nameInput.value = item.name || "";

    const rawCatId = typeof item.category_id === "object" ? (item.category_id?.$oid || item.category_id?.id || String(item.category_id)) : String(item.category_id || "");
    if (categorySelect) {
      categorySelect.innerHTML = categories.map(c => {
        const cid = c.id || c._id;
        const isSelected = (cid === rawCatId || c.name === rawCatId) ? "selected" : "";
        return `<option value="${cid}" ${isSelected}>${c.name}</option>`;
      }).join("");
      categorySelect.onchange = () => {
        autoSyncDietFromCategory(categorySelect.value, true);
        updateEditLivePreview();
      };
    }

    const price = Number(item.price?.$numberDecimal || item.price || 0).toFixed(2);
    if (priceInput) priceInput.value = price;
    if (prepInput) prepInput.value = item.preparation_time || 15;

    const isVeg = item.is_vegetarian !== false;
    setDishDiet(isVeg, true);

    if (imgInput) imgInput.value = item.image_url || "";
    if (descInput) descInput.value = item.description || "";

    [nameInput, priceInput, prepInput, imgInput, descInput].forEach(el => {
      if (el) el.oninput = updateEditLivePreview;
    });

    updateEditLivePreview();
    App.openModal("edit-dish-modal");
  }

  function updateEditLivePreview() {
    const previewName = document.getElementById("modal-edit-dish-preview-name");
    const previewPrice = document.getElementById("modal-edit-dish-preview-price");
    const previewDesc = document.getElementById("modal-edit-dish-preview-desc");
    const previewTime = document.getElementById("modal-edit-dish-preview-time");
    const previewImg = document.getElementById("modal-edit-dish-preview-img");
    const previewDiet = document.getElementById("modal-edit-dish-preview-diet");

    const name = document.getElementById("edit-dish-name-input")?.value?.trim() || "Paneer Dish";
    const priceVal = document.getElementById("edit-dish-price-input")?.value?.replace(/[^0-9.]/g, "") || "0.00";
    const prep = document.getElementById("edit-dish-prep-input")?.value || "15";
    const vegRadio = document.getElementById("edit-dish-diet-radio-veg");
    const isVeg = vegRadio ? vegRadio.checked : (document.getElementById("edit-dish-veg-input")?.checked ?? true);
    const desc = document.getElementById("edit-dish-desc-input")?.value?.trim() || "Authentic culinary preparation.";
    let img = document.getElementById("edit-dish-image-input")?.value?.trim();

    if (!img) {
      img = isVeg ? DEFAULT_FOOD_IMAGES.veg : DEFAULT_FOOD_IMAGES.nonveg;
    }

    if (previewName) previewName.textContent = name;
    if (previewPrice) previewPrice.textContent = `₹${parseFloat(priceVal || 0).toFixed(2)}`;
    if (previewDesc) previewDesc.textContent = desc;
    if (previewTime) previewTime.textContent = `⏱️ ${prep}m`;
    if (previewImg) previewImg.src = img;
    if (previewDiet) {
      previewDiet.className = `diet-icon-mark ${isVeg ? 'veg' : 'nonveg'}`;
      previewDiet.title = isVeg ? "Pure Vegetarian" : "Non-Vegetarian";
    }
  }

  function selectEditPresetImage(url, forceVeg = null, catName = null) {
    const imgInput = document.getElementById("edit-dish-image-input");
    if (imgInput) {
      imgInput.value = url;
    }
    if (catName) {
      const select = document.getElementById("edit-dish-category-select");
      if (select) {
        const found = Array.from(select.options).find(opt => opt.text.trim().toLowerCase() === catName.toLowerCase());
        if (found) {
          select.value = found.value;
        }
      }
    }
    if (forceVeg !== null) {
      setDishDiet(forceVeg, true);
    } else {
      updateEditLivePreview();
    }
    App.showToast("Sample photo applied!", "info");
  }

  async function submitEditItem() {
    const itemId = document.getElementById("edit-dish-id")?.value;
    const name = document.getElementById("edit-dish-name-input")?.value?.trim();
    const categoryId = document.getElementById("edit-dish-category-select")?.value;
    const priceRaw = String(document.getElementById("edit-dish-price-input")?.value || "");
    const cleanPrice = parseFloat(priceRaw.replace(/[^0-9.]/g, ""));
    const prepTime = parseInt(document.getElementById("edit-dish-prep-input")?.value || "15", 10) || 15;
    const vegRadio = document.getElementById("edit-dish-diet-radio-veg");
    const isVeg = vegRadio ? vegRadio.checked : (document.getElementById("edit-dish-veg-input")?.checked ?? true);
    const desc = document.getElementById("edit-dish-desc-input")?.value?.trim() || "";
    const imageUrl = document.getElementById("edit-dish-image-input")?.value?.trim() || null;

    if (!itemId) {
      App.showToast("No dish selected for editing", "error");
      return;
    }

    if (!name || name.length < 2) {
      App.showToast("Dish name is required (minimum 2 characters)", "warning");
      document.getElementById("edit-dish-name-input")?.focus();
      return;
    }

    if (isNaN(cleanPrice) || cleanPrice <= 0) {
      App.showToast("Please enter a valid price in ₹ greater than 0", "warning");
      document.getElementById("edit-dish-price-input")?.focus();
      return;
    }

    try {
      App.showLoader(true);
      await API.menu.updateItem(itemId, {
        name,
        category_id: categoryId,
        price: cleanPrice,
        preparation_time: prepTime > 0 ? prepTime : 15,
        is_vegetarian: isVeg,
        description: desc,
        image_url: imageUrl
      });

      App.showToast(`✅ Dish "${name}" updated successfully!`, "success");
      App.closeModal("edit-dish-modal");

      await refresh();
      if (window.POS && typeof POS.refresh === "function") await POS.refresh();
    } catch (e) {
      App.showToast(`Error updating dish: ${e.message}`, "error");
    } finally {
      App.showLoader(false);
    }
  }

  return {
    init,
    refresh,
    getCategories,
    getItems,
    getItem,
    searchDishes,
    filterCategory,
    filterDiet,
    setDishDiet,
    openAddItemModal,
    submitAddItem,
    selectPresetImage,
    updateLivePreview,
    openEditItemModal,
    updateEditLivePreview,
    selectEditPresetImage,
    submitEditItem,
    promptDeleteDish,
    confirmDeleteDish,
    deleteItem,
    promptDeleteCategory,
    confirmDeleteCategory,
    openAddCategoryModal,
    submitAddCategory,
    toggleAvailability
  };
})();
