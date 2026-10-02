import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { 
  UtensilsCrossed, Plus, Search, Edit2, Trash2, Check, 
  X, RefreshCw, Clock, Leaf, AlertCircle, Eye, EyeOff,
  ChefHat, Sparkles, Filter, Lock, CheckCircle2, Flame,
  ShoppingCart, Minus, ArrowRight, Layers, Tag, Percent,
  TrendingUp, Award, DollarSign, FolderPlus, ArrowUpDown
} from 'lucide-react';

const PRESET_DISH_IMAGES = [
  { label: 'Biryani Special', url: 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600' },
  { label: 'Butter Chicken', url: 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600' },
  { label: 'Paneer Tikka', url: 'https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600' },
  { label: 'Garlic Naan', url: 'https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600' },
  { label: 'South Indian Dosa', url: 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600' },
  { label: 'Gulab Jamun', url: 'https://images.unsplash.com/photo-1605197586548-932f146a782b?w=600' },
  { label: 'Crispy Starter', url: 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600' },
  { label: 'Ice Cream Sundae', url: 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600' },
];

export default function MenuView({ onNavigate, initialTab = 'browse' }) {
  const { role, permissions } = useAuth();
  const { showToast } = useToast();
  const canManageMenu = true; // Admin, Manager, Chef have management rights

  const [subTab, setSubTab] = useState(initialTab || 'browse');

  // Core Data States
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [stats, setStats] = useState(null);
  const [availabilityMap, setAvailabilityMap] = useState({});
  const [loading, setLoading] = useState(true);

  // Filters & Search
  const [search, setSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState('ALL'); // 'ALL', 'VEG', 'NON_VEG', 'STARTERS', 'DESSERTS', or catId
  const [selectedSubcat, setSelectedSubcat] = useState('ALL'); // 'ALL' or subcatId
  const [dietFilter, setDietFilter] = useState('ALL'); // 'ALL', 'VEG', 'NON_VEG', 'EGG', 'BEVERAGE', 'IN_STOCK', 'OUT_OF_STOCK'
  const [priceFilter, setPriceFilter] = useState('ALL'); // 'ALL', 'UNDER_100', '100_250', 'ABOVE_250'
  const [sortBy, setSortBy] = useState('display_order'); // 'display_order', 'price_asc', 'price_desc', 'name_asc', 'name_desc'

  // Add / Edit Item Modal
  const [showItemModal, setShowItemModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [itemName, setItemName] = useState('');
  const [itemCatId, setItemCatId] = useState('');
  const [itemSubcatId, setItemSubcatId] = useState('');
  const [itemDesc, setItemDesc] = useState('');
  const [basePrice, setBasePrice] = useState('');
  const [discount, setDiscount] = useState('0');
  const [tax, setTax] = useState('0');
  const [foodType, setFoodType] = useState('Veg');
  const [prepTime, setPrepTime] = useState(15);
  const [itemImageUrl, setItemImageUrl] = useState('');
  const [isAvailable, setIsAvailable] = useState(true);
  const [isFeatured, setIsFeatured] = useState(false);
  const [displayOrder, setDisplayOrder] = useState(0);
  const [spicyLevel, setSpicyLevel] = useState('Medium');
  const [servingSize, setServingSize] = useState('Serves 2');
  const [tagsInput, setTagsInput] = useState('');
  const [savingItem, setSavingItem] = useState(false);

  // Category Management Modal
  const [showCatModal, setShowCatModal] = useState(false);
  const [editingCat, setEditingCat] = useState(null);
  const [catName, setCatName] = useState('');
  const [catDesc, setCatDesc] = useState('');
  const [catFoodType, setCatFoodType] = useState('Veg');
  const [catImageUrl, setCatImageUrl] = useState('');
  const [catOrder, setCatOrder] = useState(1);
  const [catActive, setCatActive] = useState(true);
  const [savingCat, setSavingCat] = useState(false);

  // Subcategory Management Modal
  const [showSubcatModal, setShowSubcatModal] = useState(false);
  const [editingSubcat, setEditingSubcat] = useState(null);
  const [subcatParentCatId, setSubcatParentCatId] = useState('');
  const [subcatName, setSubcatName] = useState('');
  const [subcatDesc, setSubcatDesc] = useState('');
  const [subcatOrder, setSubcatOrder] = useState(1);
  const [subcatActive, setSubcatActive] = useState(true);
  const [savingSubcat, setSavingSubcat] = useState(false);

  // Safe Delete Modal
  const [itemToDelete, setItemToDelete] = useState(null);
  const [deletingItem, setDeletingItem] = useState(false);

  // Recipe Configuration & BOM Modal
  const [recipeItem, setRecipeItem] = useState(null);
  const [recipeLoading, setRecipeLoading] = useState(false);
  const [recipeIngredients, setRecipeIngredients] = useState([]);
  const [recipeAvailability, setRecipeAvailability] = useState(null);
  const [inventoryList, setInventoryList] = useState([]);
  const [selectedIngId, setSelectedIngId] = useState('');
  const [ingQty, setIngQty] = useState('');
  const [ingUnit, setIngUnit] = useState('GRAM');
  const [savingRecipe, setSavingRecipe] = useState(false);

  // Cart & Ordering State (Cart addition does NOT deduct inventory)
  const [cart, setCart] = useState(() => {
    try {
      const s = localStorage.getItem('dineflow_menu_cart');
      return s ? JSON.parse(s) : [];
    } catch {
      return [];
    }
  });
  const [tablesList, setTablesList] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [orderType, setOrderType] = useState('DINE_IN');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [showCartDrawer, setShowCartDrawer] = useState(false);
  const [placingOrder, setPlacingOrder] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem('dineflow_menu_cart', JSON.stringify(cart));
    } catch (e) {
      console.warn('Could not persist cart:', e);
    }
  }, [cart]);

  // Load All Menu Data, Hierarchy & Stats
  const loadData = async () => {
    setLoading(true);
    try {
      const [itRes, catRes, subcatRes, statsRes, availRes, tblRes] = await Promise.all([
        api.menu.getItems(),
        api.menu.getCategories(),
        api.menu.getSubcategories().catch(() => []),
        api.menu.getStats().catch(() => null),
        api.menu.getAvailability().catch(() => ({})),
        api.tables.getAll().catch(() => []),
      ]);

      const itemsList = Array.isArray(itRes) ? itRes : [];
      setItems(itemsList);
      const catList = Array.isArray(catRes) ? catRes : [];
      setCategories(catList);
      const subcatList = Array.isArray(subcatRes) ? subcatRes : [];
      setSubcategories(subcatList);
      setStats(statsRes);
      const availObj = availRes?.items || availRes || {};
      setAvailabilityMap(typeof availObj === 'object' ? availObj : {});
      if (Array.isArray(tblRes) && tblRes.length > 0) {
        setTablesList(tblRes);
        setSelectedTable(prev => prev || tblRes[0].id);
      }
    } catch (err) {
      console.error('Menu load error:', err);
      showToast('Could not load menu hierarchy', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Recalculate Final Price on the fly
  const calculatedFinalPrice = Math.max(
    0,
    (parseFloat(basePrice) || 0) - (parseFloat(discount) || 0) + (parseFloat(tax) || 0)
  );

  // Subcategories available for chosen Category in modal
  const modalAvailableSubcategories = subcategories.filter(s => {
    if (!itemCatId) return true;
    return String(s.category_id) === String(itemCatId);
  });

  // Open Add Item Modal
  const openAddItemModal = () => {
    setEditingItem(null);
    setItemName('');
    setItemCatId(categories[0]?.id || '');
    setItemSubcatId('');
    setItemDesc('');
    setBasePrice('');
    setDiscount('0');
    setTax('0');
    setFoodType('Veg');
    setPrepTime(15);
    setItemImageUrl(PRESET_DISH_IMAGES[0].url);
    setIsAvailable(true);
    setIsFeatured(false);
    setDisplayOrder(items.length + 1);
    setSpicyLevel('Medium');
    setServingSize('Serves 2');
    setTagsInput('');
    setShowItemModal(true);
  };

  // Open Edit Item Modal
  const openEditItemModal = (item) => {
    if (!canManageMenu) {
      showToast('Only Chef, Manager, or Admin can edit dishes', 'warning');
      return;
    }
    setEditingItem(item);
    setItemName(item.name || '');
    setItemCatId(item.category_id || categories[0]?.id || '');
    setItemSubcatId(item.subcategory_id || '');
    setItemDesc(item.description || '');
    const bp = item.base_price != null ? item.base_price : item.price;
    setBasePrice(bp != null ? String(bp) : '');
    setDiscount(item.discount != null ? String(item.discount) : '0');
    setTax(item.tax != null ? String(item.tax) : '0');
    setFoodType(item.food_type || item.type || (item.is_vegetarian ? 'Veg' : 'Non-Veg'));
    setPrepTime(item.preparation_time || 15);
    setItemImageUrl(item.image_url || PRESET_DISH_IMAGES[0].url);
    setIsAvailable(item.is_available !== false);
    setIsFeatured(!!item.is_featured);
    setDisplayOrder(item.display_order || 0);
    setSpicyLevel(item.spicy_level || 'Medium');
    setServingSize(item.serving_size || 'Serves 2');
    setTagsInput(Array.isArray(item.tags) ? item.tags.join(', ') : '');
    setShowItemModal(true);
  };

  // Save Item (Create or Update)
  const handleSaveItem = async (e) => {
    e.preventDefault();
    if (!itemName || !basePrice || !itemCatId) {
      showToast('Please fill all required dish fields (Name, Category, Price)', 'warning');
      return;
    }

    setSavingItem(true);
    try {
      const isVegBool = foodType === 'Veg' || foodType === 'Beverage';
      const parsedBp = parseFloat(basePrice) || 0;
      const parsedDisc = Math.max(0, parseFloat(discount) || 0);
      const parsedTax = Math.max(0, parseFloat(tax) || 0);
      const computedFp = Math.max(0, parsedBp - parsedDisc + parsedTax);

      const tagsArray = tagsInput
        .split(',')
        .map(t => t.trim())
        .filter(Boolean);

      const payload = {
        name: itemName.trim(),
        description: itemDesc.trim(),
        category_id: itemCatId,
        subcategory_id: itemSubcatId || null,
        price: parsedBp,
        base_price: parsedBp,
        discount: parsedDisc,
        tax: parsedTax,
        final_price: computedFp,
        preparation_time: Math.max(1, parseInt(prepTime) || 15),
        food_type: foodType,
        type: foodType,
        is_vegetarian: isVegBool,
        image_url: itemImageUrl.trim() || 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600',
        is_available: isAvailable,
        is_featured: isFeatured,
        display_order: parseInt(displayOrder) || 0,
        spicy_level: spicyLevel,
        serving_size: servingSize,
        tags: tagsArray,
      };

      if (editingItem) {
        const updated = await api.menu.updateItem(editingItem.id, payload);
        setItems(prev => prev.map(it => it.id === editingItem.id ? { ...it, ...updated } : it));
        showToast(`Menu item "${itemName}" updated successfully!`, 'success');
      } else {
        const created = await api.menu.createItem(payload);
        setItems(prev => [created, ...prev]);
        showToast(`Menu item "${itemName}" added successfully!`, 'success');
      }

      setShowItemModal(false);
      // Reload stats & availability
      api.menu.getStats().then(setStats).catch(() => {});
      api.menu.getAvailability().then(setAvailabilityMap).catch(() => {});
    } catch (err) {
      showToast(err.message || 'Failed to save menu item', 'danger');
    } finally {
      setSavingItem(false);
    }
  };

  // Safe Delete Item Handler
  const confirmSafeDeleteItem = async () => {
    if (!itemToDelete) return;
    setDeletingItem(true);
    try {
      const res = await api.menu.deleteItem(itemToDelete.id);
      if (res?.soft_deleted) {
        showToast(`Item safely deactivated: preserved in historical orders.`, 'info', 4000);
        setItems(prev => prev.map(it => it.id === itemToDelete.id ? { ...it, is_active: false, is_available: false } : it));
      } else {
        setItems(prev => prev.filter(it => it.id !== itemToDelete.id));
        showToast(`Menu item deleted successfully.`, 'success');
      }
      setItemToDelete(null);
      api.menu.getStats().then(setStats).catch(() => {});
    } catch (err) {
      showToast(err.message || 'Failed to delete dish', 'danger');
    } finally {
      setDeletingItem(false);
    }
  };

  // Toggle Availability
  const handleToggleAvailability = async (item) => {
    const nextVal = !item.is_available;
    try {
      await api.menu.updateItem(item.id, { is_available: nextVal });
      setItems(prev => prev.map(it => it.id === item.id ? { ...it, is_available: nextVal } : it));
      showToast(`${item.name} marked as ${nextVal ? 'Available' : 'Currently Unavailable'}`, 'info');
      api.menu.getStats().then(setStats).catch(() => {});
    } catch (err) {
      showToast('Failed to toggle availability', 'danger');
    }
  };

  // Category Management Handlers
  const openNewCategoryModal = () => {
    setEditingCat(null);
    setCatName('');
    setCatDesc('');
    setCatFoodType('Veg');
    setCatImageUrl('');
    setCatOrder(categories.length + 1);
    setCatActive(true);
    setShowCatModal(true);
  };

  const openEditCategoryModal = (cat) => {
    setEditingCat(cat);
    setCatName(cat.name || '');
    setCatDesc(cat.description || '');
    setCatFoodType(cat.food_type || 'Veg');
    setCatImageUrl(cat.image_url || '');
    setCatOrder(cat.display_order || 1);
    setCatActive(cat.is_active !== false);
    setShowCatModal(true);
  };

  const handleSaveCategory = async (e) => {
    e.preventDefault();
    if (!catName.trim()) {
      showToast('Category name is required', 'warning');
      return;
    }
    setSavingCat(true);
    try {
      const payload = {
        name: catName.trim(),
        description: catDesc.trim(),
        food_type: catFoodType,
        image_url: catImageUrl.trim() || undefined,
        display_order: parseInt(catOrder) || 1,
        is_active: catActive,
      };

      if (editingCat) {
        const updated = await api.menu.updateCategory(editingCat.id, payload);
        setCategories(prev => prev.map(c => c.id === editingCat.id ? { ...c, ...updated } : c));
        showToast(`Category "${catName}" updated!`, 'success');
      } else {
        const created = await api.menu.createCategory(payload);
        setCategories(prev => [...prev, created]);
        showToast(`Category "${catName}" created!`, 'success');
      }
      setShowCatModal(false);
    } catch (err) {
      showToast(err.message || 'Failed to save category', 'danger');
    } finally {
      setSavingCat(false);
    }
  };

  const handleDeleteCategory = async (catId) => {
    if (!window.confirm('Are you sure you want to delete this category? Associated dishes will need reassignment.')) return;
    try {
      await api.menu.deleteCategory(catId);
      setCategories(prev => prev.filter(c => c.id !== catId));
      showToast('Category deleted successfully', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to delete category', 'danger');
    }
  };

  // Subcategory Management Handlers
  const openNewSubcategoryModal = (parentCatId = null) => {
    setEditingSubcat(null);
    setSubcatParentCatId(parentCatId || categories[0]?.id || '');
    setSubcatName('');
    setSubcatDesc('');
    setSubcatOrder(subcategories.length + 1);
    setSubcatActive(true);
    setShowSubcatModal(true);
  };

  const openEditSubcategoryModal = (subcat) => {
    setEditingSubcat(subcat);
    setSubcatParentCatId(subcat.category_id || categories[0]?.id || '');
    setSubcatName(subcat.name || '');
    setSubcatDesc(subcat.description || '');
    setSubcatOrder(subcat.display_order || 1);
    setSubcatActive(subcat.is_active !== false);
    setShowSubcatModal(true);
  };

  const handleSaveSubcategory = async (e) => {
    e.preventDefault();
    if (!subcatName.trim() || !subcatParentCatId) {
      showToast('Subcategory name and parent Category are required', 'warning');
      return;
    }
    setSavingSubcat(true);
    try {
      const payload = {
        category_id: subcatParentCatId,
        name: subcatName.trim(),
        description: subcatDesc.trim(),
        display_order: parseInt(subcatOrder) || 1,
        is_active: subcatActive,
      };

      if (editingSubcat) {
        const updated = await api.menu.updateSubcategory(editingSubcat.id, payload);
        setSubcategories(prev => prev.map(s => s.id === editingSubcat.id ? { ...s, ...updated } : s));
        showToast(`Subcategory "${subcatName}" updated!`, 'success');
      } else {
        const created = await api.menu.createSubcategory(payload);
        setSubcategories(prev => [...prev, created]);
        showToast(`Subcategory "${subcatName}" created!`, 'success');
      }
      setShowSubcatModal(false);
    } catch (err) {
      showToast(err.message || 'Failed to save subcategory', 'danger');
    } finally {
      setSavingSubcat(false);
    }
  };

  const handleDeleteSubcategory = async (subcatId) => {
    if (!window.confirm('Are you sure you want to delete this subcategory?')) return;
    try {
      await api.menu.deleteSubcategory(subcatId);
      setSubcategories(prev => prev.filter(s => s.id !== subcatId));
      showToast('Subcategory deleted successfully', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to delete subcategory', 'danger');
    }
  };

  // Recipe Modal Handlers
  const openRecipeModal = async (item) => {
    setRecipeItem(item);
    setRecipeLoading(true);
    setRecipeIngredients([]);
    setRecipeAvailability(null);
    try {
      const [res, avail, inv] = await Promise.all([
        api.recipes.getByMenuItem(item.id).catch(() => []),
        api.menu.getItemAvailability(item.id).catch(() => null),
        api.inventory.getIngredients().catch(() => []),
      ]);
      setRecipeIngredients(Array.isArray(res) ? res : []);
      setRecipeAvailability(avail);
      const invItems = Array.isArray(inv) ? inv : [];
      setInventoryList(invItems);
      if (invItems.length > 0) {
        setSelectedIngId(invItems[0].id);
        const firstUnit = invItems[0].unit;
        setIngUnit(firstUnit === 'KG' ? 'GRAM' : (firstUnit === 'LITRE' ? 'ML' : firstUnit));
      }
      setIngQty('');
    } catch (err) {
      console.error('Recipe load error:', err);
      setRecipeIngredients([]);
    } finally {
      setRecipeLoading(false);
    }
  };

  const handleAddIngredient = async (e) => {
    e.preventDefault();
    if (!selectedIngId || !ingQty || !recipeItem) return;
    setSavingRecipe(true);
    try {
      await api.recipes.addIngredient(recipeItem.id, {
        ingredient_id: selectedIngId,
        quantity_required: parseFloat(ingQty),
        unit: ingUnit,
      });
      showToast('Ingredient added to recipe!', 'success');
      const [res, avail] = await Promise.all([
        api.recipes.getByMenuItem(recipeItem.id),
        api.menu.getItemAvailability(recipeItem.id),
      ]);
      setRecipeIngredients(Array.isArray(res) ? res : []);
      setRecipeAvailability(avail);
      setIngQty('');
    } catch (err) {
      showToast(err.message || 'Failed to update recipe', 'danger');
    } finally {
      setSavingRecipe(false);
    }
  };

  const handleDeleteIngredient = async (ingredientId) => {
    if (!recipeItem) return;
    try {
      await api.recipes.deleteIngredient(recipeItem.id, ingredientId);
      showToast('Ingredient removed from recipe', 'success');
      const [res, avail] = await Promise.all([
        api.recipes.getByMenuItem(recipeItem.id),
        api.menu.getItemAvailability(recipeItem.id),
      ]);
      setRecipeIngredients(Array.isArray(res) ? res : []);
      setRecipeAvailability(avail);
    } catch (err) {
      showToast(err.message || 'Failed to remove ingredient', 'danger');
    }
  };

  // Cart & Ordering Handlers (Stock shortages checked; NO deduction on cart addition)
  const handleAddToCart = (item) => {
    const avail = availabilityMap[item.id] || {};
    if (avail.status === 'OUT_OF_STOCK' || item.is_available === false) {
      showToast(`Currently Unavailable: ${avail.message || 'Sold out in kitchen'}`, 'warning', 3500);
      return;
    }
    const existing = cart.find(c => c.item.id === item.id);
    const nextQty = (existing?.quantity || 0) + 1;
    if (avail.has_recipe && avail.max_portions != null && nextQty > avail.max_portions) {
      showToast(`Cannot add more. Inventory supports max ${avail.max_portions} plates for ${item.name}`, 'warning', 4000);
      return;
    }

    setCart(prev => {
      const exists = prev.find(c => c.item.id === item.id);
      if (exists) {
        return prev.map(c => c.item.id === item.id ? { ...c, quantity: c.quantity + 1 } : c);
      }
      return [...prev, { item, quantity: 1, instructions: '' }];
    });
    showToast(`Added ${item.name} to Cart`, 'success', 1500);
  };

  const handleUpdateCartQty = (itemId, delta) => {
    setCart(prev =>
      prev
        .map(c => {
          if (c.item.id === itemId) {
            const newQty = c.quantity + delta;
            return newQty > 0 ? { ...c, quantity: newQty } : null;
          }
          return c;
        })
        .filter(Boolean)
    );
  };

  const handleUpdateCartInstructions = (itemId, instructions) => {
    setCart(prev => prev.map(c => c.item.id === itemId ? { ...c, instructions } : c));
  };

  const handleClearCart = () => {
    setCart([]);
    showToast('Cart cleared', 'info');
  };

  const cartCount = cart.reduce((sum, c) => sum + c.quantity, 0);
  const cartSubtotal = cart.reduce((sum, c) => sum + (parseFloat(c.item.price || 0) * c.quantity), 0);
  const cartTax = cartSubtotal * 0.05;
  const cartTotal = cartSubtotal + cartTax;

  const handlePlaceOrder = async () => {
    if (cart.length === 0) {
      showToast('Your cart is empty. Add dishes first.', 'warning');
      return;
    }
    if (orderType === 'DINE_IN' && !selectedTable && tablesList.length > 0) {
      showToast('Please select a dining table for Dine-In orders.', 'warning');
      return;
    }

    setPlacingOrder(true);
    try {
      const orderPayload = {
        customer_name: customerName.trim() || 'Walk-in Guest',
        customer_phone: customerPhone.trim() || '9876543210',
        table_id: orderType === 'DINE_IN' ? selectedTable : null,
        order_type: orderType,
        items: cart.map(c => ({
          menu_item_id: c.item.id,
          quantity: c.quantity,
          special_instructions: c.instructions || '',
        })),
      };

      const newOrder = await api.orders.create(orderPayload);
      try {
        await api.orders.confirm(newOrder.id);
      } catch (confirmErr) {
        console.warn('Order confirmation warning:', confirmErr);
      }

      setCart([]);
      localStorage.removeItem('dineflow_menu_cart');
      setShowCartDrawer(false);
      showToast(`Order #${newOrder.order_number || newOrder.id} placed & sent to kitchen!`, 'success', 4500);

      api.menu.getAvailability().then(res => setAvailabilityMap(res?.items || res || {})).catch(() => {});
    } catch (err) {
      console.error('Order creation error:', err);
      showToast(err.message || 'Failed to place order', 'danger');
    } finally {
      setPlacingOrder(false);
    }
  };

  // Identify starter items
  const isItemStarter = (it) => {
    const cat = categories.find(c => String(c.id) === String(it.category_id));
    const catName = (cat?.name || '').toLowerCase();
    const itSubcat = (it.subcategory_name || '').toLowerCase();
    const itName = (it.name || '').toLowerCase();
    return (
      catName.includes('starter') ||
      itSubcat.includes('starter') ||
      itName.includes('tikka') ||
      itName.includes('manchurian') ||
      itName.includes('lollipop') ||
      itName.includes('crispy')
    );
  };

  // Identify dessert items
  const isItemDessert = (it) => {
    const cat = categories.find(c => String(c.id) === String(it.category_id));
    const catName = (cat?.name || '').toLowerCase();
    const itSubcat = (it.subcategory_name || '').toLowerCase();
    const itName = (it.name || '').toLowerCase();
    return (
      catName.includes('dessert') ||
      itSubcat.includes('dessert') ||
      itName.includes('jamun') ||
      itName.includes('rasmalai') ||
      itName.includes('ice cream') ||
      itName.includes('brownie')
    );
  };

  // Get active subcategories for selected category in main menu view
  const currentCategoryObj = categories.find(c => {
    if (selectedCat === 'VEG') return c.name.toUpperCase() === 'VEG';
    if (selectedCat === 'NON_VEG') return c.name.toUpperCase() === 'NON-VEG';
    if (selectedCat === 'STARTERS') return c.name.toUpperCase().includes('STARTER');
    if (selectedCat === 'DESSERTS') return c.name.toUpperCase().includes('DESSERT');
    return String(c.id) === String(selectedCat);
  });

  const activeSubcategoryChips = subcategories.filter(s => {
    if (!currentCategoryObj) return true;
    return String(s.category_id) === String(currentCategoryObj.id);
  });

  // Filter Items
  const filteredItems = items.filter(it => {
    // Category Filter
    let matchesCat = true;
    if (selectedCat === 'ALL') {
      matchesCat = true;
    } else if (selectedCat === 'VEG') {
      matchesCat = !!it.is_vegetarian;
    } else if (selectedCat === 'NON_VEG') {
      matchesCat = !it.is_vegetarian;
    } else if (selectedCat === 'STARTERS') {
      matchesCat = isItemStarter(it);
    } else if (selectedCat === 'DESSERTS') {
      matchesCat = isItemDessert(it);
    } else {
      matchesCat = String(it.category_id) === String(selectedCat);
    }

    // Subcategory Filter
    let matchesSubcat = true;
    if (selectedSubcat !== 'ALL') {
      matchesSubcat = String(it.subcategory_id) === String(selectedSubcat) || 
                      (it.subcategory_name && it.subcategory_name.toLowerCase() === selectedSubcat.toLowerCase());
    }

    // Search Query
    const searchLow = search.toLowerCase();
    const matchesSearch = 
      it.name.toLowerCase().includes(searchLow) ||
      (it.description && it.description.toLowerCase().includes(searchLow)) ||
      (it.subcategory_name && it.subcategory_name.toLowerCase().includes(searchLow)) ||
      (Array.isArray(it.tags) && it.tags.some(t => t.toLowerCase().includes(searchLow)));

    // Dietary Filter
    let matchesDiet = true;
    const itType = (it.food_type || it.type || (it.is_vegetarian ? 'Veg' : 'Non-Veg')).toLowerCase();
    if (dietFilter === 'VEG') matchesDiet = itType === 'veg' || (it.is_vegetarian && itType !== 'beverage');
    else if (dietFilter === 'NON_VEG') matchesDiet = itType === 'non-veg' || (!it.is_vegetarian && itType !== 'egg');
    else if (dietFilter === 'EGG') matchesDiet = itType === 'egg';
    else if (dietFilter === 'BEVERAGE') matchesDiet = itType === 'beverage';
    else if (dietFilter === 'IN_STOCK') matchesDiet = it.is_available !== false;
    else if (dietFilter === 'OUT_OF_STOCK') matchesDiet = it.is_available === false;

    // Price Filter
    let matchesPrice = true;
    const p = parseFloat(it.final_price != null ? it.final_price : it.price || 0);
    if (priceFilter === 'UNDER_100') matchesPrice = p < 100;
    else if (priceFilter === '100_250') matchesPrice = p >= 100 && p <= 250;
    else if (priceFilter === 'ABOVE_250') matchesPrice = p > 250;

    return matchesCat && matchesSubcat && matchesSearch && matchesDiet && matchesPrice;
  });

  // Sort Items
  const sortedItems = [...filteredItems].sort((a, b) => {
    if (sortBy === 'price_asc') {
      return (parseFloat(a.price || 0)) - (parseFloat(b.price || 0));
    }
    if (sortBy === 'price_desc') {
      return (parseFloat(b.price || 0)) - (parseFloat(a.price || 0));
    }
    if (sortBy === 'name_asc') {
      return (a.name || '').localeCompare(b.name || '');
    }
    if (sortBy === 'name_desc') {
      return (b.name || '').localeCompare(a.name || '');
    }
    // Default: display_order
    return (a.display_order || 0) - (b.display_order || 0);
  });

  // Group items by Subcategory for hierarchical display (Section 5)
  const itemsBySubcategory = sortedItems.reduce((acc, it) => {
    const subName = it.subcategory_name || 'General';
    if (!acc[subName]) acc[subName] = [];
    acc[subName].push(it);
    return acc;
  }, {});

  // Compute live statistics
  const liveStats = stats || {
    total_items: items.length,
    available_items: items.filter(i => i.is_available !== false).length,
    unavailable_items: items.filter(i => i.is_available === false).length,
    veg_items: items.filter(i => i.is_vegetarian).length,
    non_veg_items: items.filter(i => !i.is_vegetarian).length,
    starters: items.filter(isItemStarter).length,
    desserts: items.filter(isItemDessert).length,
    featured_items: items.filter(i => i.is_featured).length,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Header & Action Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit' }}>Menu Management</h1>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '3px 10px',
                borderRadius: 'var(--radius-full)',
                background: 'rgba(99, 102, 241, 0.15)',
                color: '#818cf8',
                border: '1px solid rgba(99, 102, 241, 0.3)',
              }}
            >
              {items.length} Dishes &bull; {categories.length} Categories
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            Category &rarr; Subcategory &rarr; Menu Item hierarchy with live recipe BOM and inventory linkage.
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => setSubTab('browse')}
            className={`btn ${subTab === 'browse' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ borderRadius: 'var(--radius-full)', padding: '8px 16px', fontWeight: 600 }}
          >
            <UtensilsCrossed size={15} />
            <span>Menu Items</span>
          </button>
          <button
            onClick={openAddItemModal}
            className="btn btn-primary"
            style={{ borderRadius: 'var(--radius-full)', padding: '8px 18px', fontWeight: 700, boxShadow: 'var(--shadow-glow)' }}
          >
            <Plus size={16} />
            <span>+ Add Menu Item</span>
          </button>
          <button
            onClick={() => openNewSubcategoryModal()}
            className="btn btn-secondary"
            style={{ borderRadius: 'var(--radius-full)', padding: '8px 16px', fontWeight: 600 }}
          >
            <Layers size={15} style={{ color: '#818cf8' }} />
            <span>Subcategories</span>
          </button>
          <button
            onClick={openNewCategoryModal}
            className="btn btn-secondary"
            style={{ borderRadius: 'var(--radius-full)', padding: '8px 16px', fontWeight: 600 }}
          >
            <FolderPlus size={15} style={{ color: '#f59e0b' }} />
            <span>Categories</span>
          </button>
          <button
            onClick={() => setShowCartDrawer(true)}
            className="btn btn-primary"
            style={{
              borderRadius: 'var(--radius-full)',
              padding: '8px 18px',
              fontWeight: 700,
              gap: '8px',
              background: cart.length > 0 ? 'var(--primary-gradient)' : 'rgba(255, 255, 255, 0.08)',
              border: cart.length > 0 ? 'none' : '1px solid var(--border-subtle)',
              color: cart.length > 0 ? '#fff' : 'var(--text-primary)',
              boxShadow: cart.length > 0 ? 'var(--shadow-glow)' : 'none',
            }}
          >
            <ShoppingCart size={16} />
            <span>Cart ({cartCount})</span>
            {cartCount > 0 && (
              <span style={{ fontSize: '0.72rem', background: 'rgba(255, 255, 255, 0.25)', padding: '2px 8px', borderRadius: 'var(--radius-full)' }}>
                ₹{cartTotal.toFixed(2)}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* 21. Dashboard Statistics Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '12px',
        }}
      >
        <div className="glass-panel" style={{ padding: '14px 16px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Items</span>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'Outfit', color: 'var(--text-primary)', marginTop: '2px' }}>
            {liveStats.total_items}
          </span>
        </div>
        <div className="glass-panel" style={{ padding: '14px 16px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', borderLeft: '3px solid #10b981' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#10b981', textTransform: 'uppercase' }}>Available</span>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'Outfit', color: '#10b981', marginTop: '2px' }}>
            {liveStats.available_items}
          </span>
        </div>
        <div className="glass-panel" style={{ padding: '14px 16px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', borderLeft: '3px solid #ef4444' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase' }}>Unavailable</span>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'Outfit', color: '#ef4444', marginTop: '2px' }}>
            {liveStats.unavailable_items}
          </span>
        </div>
        <div className="glass-panel" style={{ padding: '14px 16px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>🌱 Veg</span>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'Outfit', color: '#10b981', marginTop: '2px' }}>
            {liveStats.veg_items}
          </span>
        </div>
        <div className="glass-panel" style={{ padding: '14px 16px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>🍗 Non-Veg</span>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'Outfit', color: '#ef4444', marginTop: '2px' }}>
            {liveStats.non_veg_items}
          </span>
        </div>
        <div className="glass-panel" style={{ padding: '14px 16px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>🍢 Starters</span>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'Outfit', color: '#f59e0b', marginTop: '2px' }}>
            {liveStats.starters}
          </span>
        </div>
        <div className="glass-panel" style={{ padding: '14px 16px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>🍨 Desserts</span>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'Outfit', color: '#ec4899', marginTop: '2px' }}>
            {liveStats.desserts}
          </span>
        </div>
        <div className="glass-panel" style={{ padding: '14px 16px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>⭐ Featured</span>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'Outfit', color: '#eab308', marginTop: '2px' }}>
            {liveStats.featured_items}
          </span>
        </div>
      </div>

      {/* Filter and Hierarchy Panel */}
      <div className="glass-panel" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Tier 1: Main Category Tabs */}
        <div>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.04em' }}>
            1. CATEGORY
          </div>
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px', alignItems: 'center' }}>
            <button
              onClick={() => { setSelectedCat('ALL'); setSelectedSubcat('ALL'); }}
              className={`btn btn-sm ${selectedCat === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap', fontWeight: 700 }}
            >
              🍽️ All Menu ({items.length})
            </button>
            <button
              onClick={() => { setSelectedCat('VEG'); setSelectedSubcat('ALL'); }}
              className={`btn btn-sm ${selectedCat === 'VEG' ? 'btn-primary' : 'btn-secondary'}`}
              style={{
                borderRadius: 'var(--radius-full)',
                whiteSpace: 'nowrap',
                fontWeight: 700,
                background: selectedCat === 'VEG' ? 'var(--primary-gradient)' : 'rgba(16, 185, 129, 0.15)',
                borderColor: selectedCat === 'VEG' ? 'transparent' : 'rgba(16, 185, 129, 0.4)',
                color: selectedCat === 'VEG' ? '#fff' : '#10b981',
              }}
            >
              🥦 VEG ({items.filter(i => i.is_vegetarian).length})
            </button>
            <button
              onClick={() => { setSelectedCat('NON_VEG'); setSelectedSubcat('ALL'); }}
              className={`btn btn-sm ${selectedCat === 'NON_VEG' ? 'btn-primary' : 'btn-secondary'}`}
              style={{
                borderRadius: 'var(--radius-full)',
                whiteSpace: 'nowrap',
                fontWeight: 700,
                background: selectedCat === 'NON_VEG' ? 'var(--primary-gradient)' : 'rgba(239, 68, 68, 0.15)',
                borderColor: selectedCat === 'NON_VEG' ? 'transparent' : 'rgba(239, 68, 68, 0.4)',
                color: selectedCat === 'NON_VEG' ? '#fff' : '#ef4444',
              }}
            >
              🍗 NON-VEG ({items.filter(i => !i.is_vegetarian).length})
            </button>
            <button
              onClick={() => { setSelectedCat('STARTERS'); setSelectedSubcat('ALL'); }}
              className={`btn btn-sm ${selectedCat === 'STARTERS' ? 'btn-primary' : 'btn-secondary'}`}
              style={{
                borderRadius: 'var(--radius-full)',
                whiteSpace: 'nowrap',
                fontWeight: 700,
                background: selectedCat === 'STARTERS' ? 'var(--primary-gradient)' : 'rgba(245, 158, 11, 0.15)',
                borderColor: selectedCat === 'STARTERS' ? 'transparent' : 'rgba(245, 158, 11, 0.4)',
                color: selectedCat === 'STARTERS' ? '#fff' : '#f59e0b',
              }}
            >
              🍢 STARTERS ({items.filter(isItemStarter).length})
            </button>
            <button
              onClick={() => { setSelectedCat('DESSERTS'); setSelectedSubcat('ALL'); }}
              className={`btn btn-sm ${selectedCat === 'DESSERTS' ? 'btn-primary' : 'btn-secondary'}`}
              style={{
                borderRadius: 'var(--radius-full)',
                whiteSpace: 'nowrap',
                fontWeight: 700,
                background: selectedCat === 'DESSERTS' ? 'var(--primary-gradient)' : 'rgba(236, 72, 153, 0.15)',
                borderColor: selectedCat === 'DESSERTS' ? 'transparent' : 'rgba(236, 72, 153, 0.4)',
                color: selectedCat === 'DESSERTS' ? '#fff' : '#ec4899',
              }}
            >
              🍨 DESSERTS ({items.filter(isItemDessert).length})
            </button>

            {/* Custom Categories */}
            {categories
              .filter(c => !['veg', 'non-veg', 'starters', 'starter', 'desserts', 'dessert'].includes(c.name.toLowerCase().trim()))
              .map(c => {
                const count = items.filter(it => String(it.category_id) === String(c.id)).length;
                const isSelected = selectedCat === c.id;
                return (
                  <button
                    key={c.id}
                    onClick={() => { setSelectedCat(c.id); setSelectedSubcat('ALL'); }}
                    className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap' }}
                  >
                    {c.name} ({count})
                  </button>
                );
              })}
          </div>
        </div>

        {/* Tier 2: Subcategory Filters (Pill Chips) */}
        {activeSubcategoryChips.length > 0 && (
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.04em', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>2. SUBCATEGORY FILTER</span>
              <button
                type="button"
                onClick={() => openNewSubcategoryModal(currentCategoryObj?.id)}
                style={{ background: 'transparent', border: 'none', color: 'var(--primary)', fontSize: '0.72rem', cursor: 'pointer', fontWeight: 600 }}
              >
                + Add Subcategory
              </button>
            </div>
            <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px', alignItems: 'center' }}>
              <button
                onClick={() => setSelectedSubcat('ALL')}
                style={{
                  padding: '5px 14px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  border: '1px solid',
                  borderColor: selectedSubcat === 'ALL' ? 'var(--primary)' : 'var(--border-subtle)',
                  background: selectedSubcat === 'ALL' ? 'rgba(99, 102, 241, 0.25)' : 'var(--bg-tertiary)',
                  color: selectedSubcat === 'ALL' ? '#818cf8' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }}
              >
                All Subcategories
              </button>
              {activeSubcategoryChips.map(sub => {
                const isSubSelected = selectedSubcat === sub.id || selectedSubcat === sub.name;
                const count = items.filter(i => String(i.subcategory_id) === String(sub.id) || (i.subcategory_name && i.subcategory_name.toLowerCase() === sub.name.toLowerCase())).length;
                return (
                  <button
                    key={sub.id}
                    onClick={() => setSelectedSubcat(sub.id)}
                    style={{
                      padding: '5px 14px',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      border: '1px solid',
                      borderColor: isSubSelected ? 'var(--primary)' : 'var(--border-subtle)',
                      background: isSubSelected ? 'rgba(99, 102, 241, 0.25)' : 'var(--bg-tertiary)',
                      color: isSubSelected ? '#818cf8' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px',
                    }}
                  >
                    <span>{sub.name}</span>
                    <span style={{ fontSize: '0.65rem', opacity: 0.75 }}>({count})</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Tier 3: Search, Dietary Filters, Price Range, and Sorting */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
          {/* Dietary Filter Pills */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setDietFilter('ALL')}
              style={{
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.72rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'ALL' ? 'var(--primary)' : 'var(--border-subtle)',
                background: dietFilter === 'ALL' ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                color: dietFilter === 'ALL' ? '#818cf8' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              All Types
            </button>
            <button
              onClick={() => setDietFilter('VEG')}
              style={{
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.72rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'VEG' ? '#10b981' : 'var(--border-subtle)',
                background: dietFilter === 'VEG' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
                color: dietFilter === 'VEG' ? '#10b981' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              Pure Veg
            </button>
            <button
              onClick={() => setDietFilter('NON_VEG')}
              style={{
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.72rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'NON_VEG' ? '#ef4444' : 'var(--border-subtle)',
                background: dietFilter === 'NON_VEG' ? 'rgba(239, 68, 68, 0.2)' : 'transparent',
                color: dietFilter === 'NON_VEG' ? '#ef4444' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              Non-Veg
            </button>
            <button
              onClick={() => setDietFilter('IN_STOCK')}
              style={{
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.72rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'IN_STOCK' ? '#10b981' : 'var(--border-subtle)',
                background: dietFilter === 'IN_STOCK' ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
                color: dietFilter === 'IN_STOCK' ? '#10b981' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              Available
            </button>
            <button
              onClick={() => setDietFilter('OUT_OF_STOCK')}
              style={{
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.72rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: dietFilter === 'OUT_OF_STOCK' ? '#ef4444' : 'var(--border-subtle)',
                background: dietFilter === 'OUT_OF_STOCK' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
                color: dietFilter === 'OUT_OF_STOCK' ? '#ef4444' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              Unavailable
            </button>
          </div>

          {/* Price Range & Sorting */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <select
              value={priceFilter}
              onChange={e => setPriceFilter(e.target.value)}
              className="select"
              style={{ height: '34px', fontSize: '0.75rem', padding: '0 8px', borderRadius: 'var(--radius-full)' }}
            >
              <option value="ALL">All Prices</option>
              <option value="UNDER_100">Under ₹100</option>
              <option value="100_250">₹100 - ₹250</option>
              <option value="ABOVE_250">Above ₹250</option>
            </select>

            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
              className="select"
              style={{ height: '34px', fontSize: '0.75rem', padding: '0 8px', borderRadius: 'var(--radius-full)' }}
            >
              <option value="display_order">Sort: Menu Order</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="name_asc">Name: A to Z</option>
              <option value="name_desc">Name: Z to A</option>
            </select>

            {/* Search Box */}
            <div style={{ position: 'relative', width: '220px' }}>
              <Search size={13} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search dish or tags..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="input"
                style={{ paddingLeft: '30px', height: '34px', fontSize: '0.78rem', borderRadius: 'var(--radius-full)' }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Dishes Cards Display */}
      {loading ? (
        <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 12px' }} />
          Loading menu hierarchy and recipes...
        </div>
      ) : sortedItems.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <UtensilsCrossed size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>No dishes found</h3>
          <p style={{ fontSize: '0.85rem', marginTop: '6px', marginBottom: '16px' }}>
            No menu items matched your active category, subcategory, or search filters.
          </p>
          <button onClick={openAddItemModal} className="btn btn-primary" style={{ margin: '0 auto', display: 'inline-flex' }}>
            <Plus size={16} />
            <span>+ Add Menu Item</span>
          </button>
        </div>
      ) : (
        /* Hierarchical Grouping by Subcategory (Section 5) */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {Object.entries(itemsBySubcategory).map(([subcatTitle, subItems]) => (
            <div key={subcatTitle} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', fontFamily: 'Outfit', color: 'var(--text-primary)' }}>
                    {subcatTitle}
                  </h2>
                  <span style={{ fontSize: '0.72rem', background: 'rgba(255, 255, 255, 0.08)', padding: '2px 8px', borderRadius: 'var(--radius-full)', color: 'var(--text-secondary)' }}>
                    {subItems.length} dishes
                  </span>
                </div>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                  gap: '20px',
                }}
              >
                {subItems.map(item => {
                  const isItemActive = item.is_active !== false;
                  const isItemAvail = item.is_available !== false;
                  const availInfo = availabilityMap[item.id];
                  const isOutOfStock = availInfo?.status === 'OUT_OF_STOCK';
                  const isLowStock = availInfo?.status === 'LOW_STOCK';
                  const maxPortions = availInfo?.max_portions;
                  const finalP = item.final_price != null ? item.final_price : item.price;
                  const hasDiscount = item.discount != null && parseFloat(item.discount) > 0;

                  return (
                    <div
                      key={item.id}
                      className="glass-panel"
                      style={{
                        borderRadius: 'var(--radius-lg)',
                        overflow: 'hidden',
                        display: 'flex',
                        flexDirection: 'column',
                        opacity: isItemActive && isItemAvail && !isOutOfStock ? 1 : 0.75,
                        transition: 'all 0.25s ease',
                        border: isOutOfStock 
                          ? '1px dashed rgba(239, 68, 68, 0.5)' 
                          : isItemAvail 
                          ? '1px solid var(--border-subtle)' 
                          : '1px dashed rgba(239, 68, 68, 0.4)',
                      }}
                    >
                      {/* Dish Image Banner */}
                      <div style={{ height: '160px', background: '#0f172a', position: 'relative', overflow: 'hidden' }}>
                        <img
                          src={item.image_url || 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600'}
                          alt={item.name}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={e => {
                            e.currentTarget.onerror = null;
                            e.currentTarget.src = 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600';
                          }}
                        />

                        {/* Gradient shadow overlay */}
                        <div
                          style={{
                            position: 'absolute',
                            inset: 0,
                            background: 'linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.1) 40%, rgba(15,23,42,0.95) 100%)',
                          }}
                        />

                        {/* Top Left: Food Type Indicator Badge */}
                        <div style={{ position: 'absolute', top: '10px', left: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <div
                            className={`food-symbol ${item.is_vegetarian ? 'veg' : 'nonveg'}`}
                            style={{
                              background: 'rgba(0, 0, 0, 0.75)',
                              boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
                              borderColor: item.is_vegetarian ? '#10b981' : '#ef4444',
                            }}
                          >
                            {item.is_vegetarian ? <span /> : <span />}
                          </div>
                          <span
                            style={{
                              fontSize: '0.65rem',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-full)',
                              background: 'rgba(0, 0, 0, 0.75)',
                              backdropFilter: 'blur(8px)',
                              color: item.is_vegetarian ? '#10b981' : '#ef4444',
                              border: `1px solid ${item.is_vegetarian ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                            }}
                          >
                            {item.is_vegetarian ? 'VEG' : 'NON-VEG'}
                          </span>
                          {item.is_featured && (
                            <span
                              style={{
                                fontSize: '0.62rem',
                                fontWeight: 800,
                                padding: '2px 6px',
                                borderRadius: 'var(--radius-full)',
                                background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                                color: '#fff',
                                boxShadow: '0 2px 6px rgba(245, 158, 11, 0.4)',
                              }}
                            >
                              ★ FEATURED
                            </span>
                          )}
                        </div>

                        {/* Top Right: Status Badge & Toggle Button */}
                        <div style={{ position: 'absolute', top: '10px', right: '10px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                          <button
                            onClick={() => handleToggleAvailability(item)}
                            title={isItemAvail ? 'Mark as Unavailable' : 'Mark as Available'}
                            style={{
                              padding: '3px 8px',
                              borderRadius: 'var(--radius-full)',
                              fontSize: '0.65rem',
                              fontWeight: 700,
                              background: isItemAvail ? 'rgba(16, 185, 129, 0.9)' : 'rgba(239, 68, 68, 0.9)',
                              color: '#ffffff',
                              border: 'none',
                              cursor: 'pointer',
                              boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                          >
                            {isItemAvail ? <CheckCircle2 size={11} /> : <AlertCircle size={11} />}
                            <span>{isItemAvail ? 'AVAILABLE' : 'UNAVAILABLE'}</span>
                          </button>

                          {availInfo && (
                            <span
                              style={{
                                fontSize: '0.62rem',
                                fontWeight: 800,
                                padding: '2px 7px',
                                borderRadius: '4px',
                                background: isOutOfStock
                                  ? 'rgba(239, 68, 68, 0.95)'
                                  : isLowStock
                                  ? 'rgba(245, 158, 11, 0.95)'
                                  : 'rgba(16, 185, 129, 0.9)',
                                color: '#ffffff',
                                boxShadow: '0 2px 6px rgba(0,0,0,0.4)',
                              }}
                            >
                              {isOutOfStock
                                ? '🔴 OUT OF STOCK'
                                : isLowStock
                                ? `🟡 LIMITED (${maxPortions} left)`
                                : `🟢 IN STOCK (${maxPortions != null ? maxPortions + ' left' : 'READY'})`}
                            </span>
                          )}
                        </div>

                        {/* Bottom Over Image: Prep Time */}
                        <div
                          style={{
                            position: 'absolute',
                            bottom: '8px',
                            left: '12px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '0.72rem',
                            color: '#e2e8f0',
                            background: 'rgba(0,0,0,0.6)',
                            padding: '2px 8px',
                            borderRadius: '4px',
                          }}
                        >
                          <Clock size={12} style={{ color: 'var(--accent)' }} />
                          <span>{item.preparation_time || 15} mins prep</span>
                        </div>
                      </div>

                      {/* Dish Details */}
                      <div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, lineHeight: 1.3 }}>{item.name}</h3>
                            <div style={{ display: 'flex', gap: '4px' }}>
                              {item.category_name && (
                                <span
                                  style={{
                                    fontSize: '0.65rem',
                                    fontWeight: 600,
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    background: 'var(--bg-tertiary)',
                                    color: 'var(--text-muted)',
                                    whiteSpace: 'nowrap',
                                  }}
                                >
                                  {item.category_name}
                                </span>
                              )}
                            </div>
                          </div>

                          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '6px', lineHeight: 1.4 }}>
                            {item.description || 'Crafted with premium aromatic spices and authentic recipe.'}
                          </p>

                          {/* Spicy Level & Serving Size Badges */}
                          <div style={{ display: 'flex', gap: '6px', marginTop: '8px', flexWrap: 'wrap' }}>
                            {item.spicy_level && (
                              <span style={{ fontSize: '0.68rem', padding: '1px 6px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
                                🌶️ {item.spicy_level}
                              </span>
                            )}
                            {item.serving_size && (
                              <span style={{ fontSize: '0.68rem', padding: '1px 6px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-secondary)' }}>
                                🍽️ {item.serving_size}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Bottom Row: Price & Actions */}
                        <div style={{ marginTop: '16px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <div>
                              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>PRICE</span>
                              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                                <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit', letterSpacing: '-0.02em' }}>
                                  ₹{parseFloat(finalP || 0).toFixed(2)}
                                </div>
                                {hasDiscount && (
                                  <span style={{ fontSize: '0.75rem', textDecoration: 'line-through', color: 'var(--text-muted)' }}>
                                    ₹{parseFloat(item.base_price || item.price).toFixed(2)}
                                  </span>
                                )}
                              </div>
                            </div>

                            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', justifyContent: 'flex-end', alignItems: 'center' }}>
                              {/* Add to Cart button */}
                              {(() => {
                                const inCart = cart.find(c => c.item.id === item.id);
                                const cartQty = inCart ? inCart.quantity : 0;
                                if (cartQty > 0) {
                                  return (
                                    <div
                                      style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '4px',
                                        background: 'var(--primary-gradient)',
                                        borderRadius: 'var(--radius-md)',
                                        padding: '2px 4px',
                                        boxShadow: 'var(--shadow-glow)',
                                      }}
                                    >
                                      <button
                                        type="button"
                                        onClick={() => handleUpdateCartQty(item.id, -1)}
                                        title="Decrease quantity"
                                        style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', padding: '4px 6px', display: 'flex', alignItems: 'center' }}
                                      >
                                        <Minus size={13} />
                                      </button>
                                      <span style={{ color: '#fff', fontWeight: 800, fontSize: '0.8rem', minWidth: '18px', textAlign: 'center' }}>
                                        {cartQty}
                                      </span>
                                      <button
                                        type="button"
                                        onClick={() => handleAddToCart(item)}
                                        title="Add more"
                                        style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', padding: '4px 6px', display: 'flex', alignItems: 'center' }}
                                      >
                                        <Plus size={13} />
                                      </button>
                                    </div>
                                  );
                                }
                                return (
                                  <button
                                    type="button"
                                    onClick={() => handleAddToCart(item)}
                                    disabled={!isItemAvail || isOutOfStock}
                                    className="btn btn-primary btn-sm"
                                    title={!isItemAvail || isOutOfStock ? 'Dish is currently unavailable' : 'Add to cart'}
                                    style={{
                                      padding: '7px 12px',
                                      fontSize: '0.78rem',
                                      fontWeight: 700,
                                      gap: '5px',
                                      opacity: !isItemAvail || isOutOfStock ? 0.6 : 1,
                                      cursor: !isItemAvail || isOutOfStock ? 'not-allowed' : 'pointer',
                                    }}
                                  >
                                    <ShoppingCart size={13} />
                                    <span>Add</span>
                                  </button>
                                );
                              })()}

                              {/* Recipe Ingredients Button */}
                              <button
                                onClick={() => openRecipeModal(item)}
                                className="btn btn-secondary btn-sm"
                                title="Manage Recipe Ingredients"
                                style={{ padding: '7px 9px', fontSize: '0.75rem', gap: '4px' }}
                              >
                                <ChefHat size={13} style={{ color: '#f59e0b' }} />
                                <span>Recipe</span>
                              </button>

                              {/* Edit & Delete (Admin/Manager/Chef) */}
                              {canManageMenu && (
                                <>
                                  <button
                                    onClick={() => openEditItemModal(item)}
                                    className="btn btn-secondary btn-sm"
                                    title="Edit Item"
                                    style={{ padding: '7px 9px', fontSize: '0.75rem', gap: '4px' }}
                                  >
                                    <Edit2 size={13} />
                                  </button>
                                  <button
                                    onClick={() => setItemToDelete(item)}
                                    className="btn btn-danger btn-sm"
                                    title="Delete Item"
                                    style={{ padding: '7px 9px', fontSize: '0.75rem', gap: '4px' }}
                                  >
                                    <Trash2 size={13} />
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 2. Add / Edit Menu Item Modal */}
      {showItemModal && (
        <div className="modal-overlay" onClick={() => setShowItemModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '28px', maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'var(--primary-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <UtensilsCrossed size={18} />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                    {editingItem ? 'Edit Menu Item' : 'Add New Menu Item'}
                  </h2>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Category &rarr; Subcategory &rarr; Item configuration
                  </div>
                </div>
              </div>
              <button onClick={() => setShowItemModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveItem} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Item Name */}
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Item Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chicken Dum Biryani, Paneer Butter Masala..."
                  value={itemName}
                  onChange={e => setItemName(e.target.value)}
                  className="input"
                />
              </div>

              {/* Category & Subcategory Selectors */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Category *</label>
                  <select
                    required
                    value={itemCatId}
                    onChange={e => {
                      setItemCatId(e.target.value);
                      setItemSubcatId(''); // reset subcategory on category change
                    }}
                    className="select"
                  >
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Subcategory</label>
                  <select
                    value={itemSubcatId}
                    onChange={e => setItemSubcatId(e.target.value)}
                    className="select"
                  >
                    <option value="">-- No Subcategory / General --</option>
                    {modalAvailableSubcategories.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Price Management: Base Price, Discount, Tax, and Final Price preview */}
              <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <DollarSign size={14} style={{ color: 'var(--primary)' }} />
                  <span>14. Price Management & Tax Calculation</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Base Price (₹) *</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      min="0"
                      placeholder="250.00"
                      value={basePrice}
                      onChange={e => setBasePrice(e.target.value)}
                      className="input"
                      style={{ height: '36px', fontSize: '0.85rem' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Discount (₹)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={discount}
                      onChange={e => setDiscount(e.target.value)}
                      className="input"
                      style={{ height: '36px', fontSize: '0.85rem' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>GST / Tax (₹)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={tax}
                      onChange={e => setTax(e.target.value)}
                      className="input"
                      style={{ height: '36px', fontSize: '0.85rem' }}
                    />
                  </div>
                </div>

                {/* Final Price Preview */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px dashed var(--border-subtle)', paddingTop: '8px', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Calculated Final Price:</span>
                  <span style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit' }}>
                    ₹{calculatedFinalPrice.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Food Type & Preparation Time */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Food Type *</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
                    <div
                      onClick={() => setFoodType('Veg')}
                      style={{
                        height: '38px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                        borderRadius: 'var(--radius-md)',
                        background: foodType === 'Veg' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                        border: `2px solid ${foodType === 'Veg' ? '#10b981' : 'var(--border-subtle)'}`,
                        cursor: 'pointer',
                        fontWeight: 700,
                        fontSize: '0.78rem',
                        color: foodType === 'Veg' ? '#10b981' : 'var(--text-muted)',
                      }}
                    >
                      <span className="food-symbol veg" style={{ width: '10px', height: '10px', padding: '1px' }}>
                        <span style={{ width: '5px', height: '5px' }} />
                      </span>
                      <span>Veg</span>
                    </div>

                    <div
                      onClick={() => setFoodType('Non-Veg')}
                      style={{
                        height: '38px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                        borderRadius: 'var(--radius-md)',
                        background: foodType === 'Non-Veg' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                        border: `2px solid ${foodType === 'Non-Veg' ? '#ef4444' : 'var(--border-subtle)'}`,
                        cursor: 'pointer',
                        fontWeight: 700,
                        fontSize: '0.78rem',
                        color: foodType === 'Non-Veg' ? '#ef4444' : 'var(--text-muted)',
                      }}
                    >
                      <span className="food-symbol nonveg" style={{ width: '10px', height: '10px', padding: '1px' }}>
                        <span style={{ borderLeftWidth: '2.5px', borderRightWidth: '2.5px', borderBottomWidth: '5px' }} />
                      </span>
                      <span>Non-Veg</span>
                    </div>
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Prep Time (mins) *</label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={prepTime}
                    onChange={e => setPrepTime(e.target.value)}
                    className="input"
                    style={{ height: '38px' }}
                  />
                </div>
              </div>

              {/* Image URL & Presets */}
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Image URL</label>
                <input
                  type="url"
                  placeholder="https://images.unsplash.com/..."
                  value={itemImageUrl}
                  onChange={e => setItemImageUrl(e.target.value)}
                  className="input"
                />
                <div style={{ display: 'flex', gap: '6px', marginTop: '6px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Quick Presets:</span>
                  {PRESET_DISH_IMAGES.slice(0, 5).map(p => (
                    <button
                      key={p.label}
                      type="button"
                      onClick={() => setItemImageUrl(p.url)}
                      style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        padding: '2px 6px',
                        fontSize: '0.65rem',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                      }}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Spicy Level, Serving Size, Display Order */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Spicy Level</label>
                  <select
                    value={spicyLevel}
                    onChange={e => setSpicyLevel(e.target.value)}
                    className="select"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  >
                    <option value="None">None</option>
                    <option value="Mild">Mild</option>
                    <option value="Medium">Medium</option>
                    <option value="Spicy">Spicy</option>
                    <option value="Extra Spicy">Extra Spicy</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Serving Size</label>
                  <input
                    type="text"
                    placeholder="e.g. Serves 2"
                    value={servingSize}
                    onChange={e => setServingSize(e.target.value)}
                    className="input"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Display Order</label>
                  <input
                    type="number"
                    value={displayOrder}
                    onChange={e => setDisplayOrder(e.target.value)}
                    className="input"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  />
                </div>
              </div>

              {/* Tags & Flags */}
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Tags (comma-separated)</label>
                  <input
                    type="text"
                    placeholder="Chef Special, Bestseller, Mughlai"
                    value={tagsInput}
                    onChange={e => setTagsInput(e.target.value)}
                    className="input"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', justifyContent: 'center' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={isAvailable}
                      onChange={e => setIsAvailable(e.target.checked)}
                    />
                    <span>Available</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={isFeatured}
                      onChange={e => setIsFeatured(e.target.checked)}
                    />
                    <span>Featured Item</span>
                  </label>
                </div>
              </div>

              {/* Description */}
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Description</label>
                <textarea
                  rows="2"
                  placeholder="Authentic aromatic preparation with traditional spices and fresh ingredients..."
                  value={itemDesc}
                  onChange={e => setItemDesc(e.target.value)}
                  className="textarea"
                />
              </div>

              {/* Submit Buttons */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowItemModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" disabled={savingItem} className="btn btn-primary" style={{ flex: 1 }}>
                  {savingItem ? 'Saving...' : editingItem ? 'Save Changes' : 'Create Menu Item'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 3. Category Management Modal */}
      {showCatModal && (
        <div className="modal-overlay" onClick={() => setShowCatModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '24px', maxWidth: '560px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FolderPlus size={18} style={{ color: '#f59e0b' }} />
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                  {editingCat ? 'Edit Category' : 'Manage Categories'}
                </h2>
              </div>
              <button onClick={() => setShowCatModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            {/* Existing Categories List */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Current Categories ({categories.length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto' }}>
                {categories.map(cat => (
                  <div
                    key={cat.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.85rem',
                    }}
                  >
                    <div>
                      <strong style={{ marginRight: '8px' }}>{cat.name}</strong>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Order #{cat.display_order || 0}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        type="button"
                        onClick={() => openEditCategoryModal(cat)}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '3px 7px' }}
                      >
                        <Edit2 size={12} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteCategory(cat.id)}
                        className="btn btn-danger btn-sm"
                        style={{ padding: '3px 7px' }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Category Form */}
            <form onSubmit={handleSaveCategory} style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
              <div style={{ fontSize: '0.825rem', fontWeight: 700 }}>
                {editingCat ? `Edit "${editingCat.name}"` : '+ Add New Category'}
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Category Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. VEG, NON-VEG, STARTERS, DESSERTS..."
                  value={catName}
                  onChange={e => setCatName(e.target.value)}
                  className="input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Food Type</label>
                  <select
                    value={catFoodType}
                    onChange={e => setCatFoodType(e.target.value)}
                    className="select"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  >
                    <option value="Veg">Veg</option>
                    <option value="Non-Veg">Non-Veg</option>
                    <option value="Both">Both / Universal</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Display Order</label>
                  <input
                    type="number"
                    value={catOrder}
                    onChange={e => setCatOrder(e.target.value)}
                    className="input"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Description</label>
                <textarea
                  rows="2"
                  placeholder="Category highlights and offerings..."
                  value={catDesc}
                  onChange={e => setCatDesc(e.target.value)}
                  className="textarea"
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
                <button type="button" onClick={() => setShowCatModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Close
                </button>
                <button type="submit" disabled={savingCat} className="btn btn-primary" style={{ flex: 1 }}>
                  {savingCat ? 'Saving...' : editingCat ? 'Update Category' : 'Create Category'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 4. Subcategory Management Modal */}
      {showSubcatModal && (
        <div className="modal-overlay" onClick={() => setShowSubcatModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '24px', maxWidth: '580px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} style={{ color: '#818cf8' }} />
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                  {editingSubcat ? 'Edit Subcategory' : 'Manage Subcategories'}
                </h2>
              </div>
              <button onClick={() => setShowSubcatModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            {/* Existing Subcategories List */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Current Subcategories ({subcategories.length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto' }}>
                {subcategories.map(sub => {
                  const parent = categories.find(c => String(c.id) === String(sub.category_id));
                  return (
                    <div
                      key={sub.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--bg-tertiary)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '0.85rem',
                      }}
                    >
                      <div>
                        <strong style={{ marginRight: '6px' }}>{sub.name}</strong>
                        <span style={{ fontSize: '0.7rem', color: '#818cf8', background: 'rgba(99, 102, 241, 0.12)', padding: '1px 6px', borderRadius: '4px', marginRight: '6px' }}>
                          {parent?.name || 'Category'}
                        </span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Order #{sub.display_order || 0}</span>
                      </div>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          type="button"
                          onClick={() => openEditSubcategoryModal(sub)}
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '3px 7px' }}
                        >
                          <Edit2 size={12} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteSubcategory(sub.id)}
                          className="btn btn-danger btn-sm"
                          style={{ padding: '3px 7px' }}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Subcategory Form */}
            <form onSubmit={handleSaveSubcategory} style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
              <div style={{ fontSize: '0.825rem', fontWeight: 700 }}>
                {editingSubcat ? `Edit "${editingSubcat.name}"` : '+ Add New Subcategory'}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Parent Category *</label>
                  <select
                    required
                    value={subcatParentCatId}
                    onChange={e => setSubcatParentCatId(e.target.value)}
                    className="select"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  >
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Subcategory Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Main Course, Biryani, Indian Breads..."
                    value={subcatName}
                    onChange={e => setSubcatName(e.target.value)}
                    className="input"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Display Order</label>
                  <input
                    type="number"
                    value={subcatOrder}
                    onChange={e => setSubcatOrder(e.target.value)}
                    className="input"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Active Status</label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', height: '36px', fontSize: '0.8rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={subcatActive}
                      onChange={e => setSubcatActive(e.target.checked)}
                    />
                    <span>Active Subcategory</span>
                  </label>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Description</label>
                <textarea
                  rows="2"
                  placeholder="Specialty subcategory descriptions..."
                  value={subcatDesc}
                  onChange={e => setSubcatDesc(e.target.value)}
                  className="textarea"
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
                <button type="button" onClick={() => setShowSubcatModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Close
                </button>
                <button type="submit" disabled={savingSubcat} className="btn btn-primary" style={{ flex: 1 }}>
                  {savingSubcat ? 'Saving...' : editingSubcat ? 'Update Subcategory' : 'Create Subcategory'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 8. Safe Delete Confirmation Modal */}
      {itemToDelete && (
        <div className="modal-overlay" onClick={() => setItemToDelete(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '28px', maxWidth: '440px', textAlign: 'center' }}>
            <div style={{ width: '54px', height: '54px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--danger)', margin: '0 auto 16px' }}>
              <Trash2 size={24} />
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Delete Menu Item?</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px', lineHeight: 1.5 }}>
              Are you sure you want to delete <strong>"{itemToDelete.name}"</strong>?
            </p>
            <div style={{ margin: '14px 0', padding: '12px', borderRadius: 'var(--radius-sm)', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.25)', fontSize: '0.78rem', color: '#93c5fd', textAlign: 'left' }}>
              <strong>Safe Deletion Guarantee:</strong> If this item has previous orders, bills, or kitchen tickets, historical accounting and reporting records will remain intact. The dish will be safely deactivated (<code style={{ color: '#fff' }}>is_active = false</code>) rather than breaking historical invoices.
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
              <button onClick={() => setItemToDelete(null)} className="btn btn-secondary" style={{ flex: 1 }}>
                Cancel
              </button>
              <button onClick={confirmSafeDeleteItem} disabled={deletingItem} className="btn btn-danger" style={{ flex: 1 }}>
                {deletingItem ? 'Deleting...' : 'Confirm Safe Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 9 & 10. Recipe / Ingredients BOM Configuration Modal */}
      {recipeItem && (
        <div className="modal-overlay" onClick={() => setRecipeItem(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ padding: '28px', maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
                  <ChefHat size={22} />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.3rem', fontWeight: 800 }}>Recipe & Bill of Materials</h2>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {recipeItem.name} &bull; 1 Plate Portion
                  </div>
                </div>
              </div>
              <button onClick={() => setRecipeItem(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            {/* Availability / Capacity Banner */}
            {recipeLoading ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Loading recipe mapping and live warehouse stock...
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {/* Starter Exemption / Recipe Explanation Info */}
                {recipeIngredients.length === 0 && (
                  <div style={{ padding: '14px 18px', borderRadius: 'var(--radius-md)', background: 'rgba(59, 130, 246, 0.12)', border: '1px solid rgba(59, 130, 246, 0.3)', fontSize: '0.825rem', color: '#60a5fa', lineHeight: 1.4 }}>
                    <strong>ℹ No Recipe Mapped Yet:</strong> Starters and dishes without a mapped recipe do not deduct warehouse stock. To connect this dish to inventory, add raw ingredients below.
                  </div>
                )}

                {/* Live Stock Capacity Indicator */}
                {recipeIngredients.length > 0 && recipeAvailability && (
                  <div
                    style={{
                      padding: '14px 18px',
                      borderRadius: 'var(--radius-md)',
                      background: recipeAvailability.status === 'AVAILABLE'
                        ? 'rgba(16, 185, 129, 0.12)'
                        : recipeAvailability.status === 'LOW_STOCK'
                        ? 'rgba(245, 158, 11, 0.12)'
                        : 'rgba(239, 68, 68, 0.12)',
                      border: `1px solid ${
                        recipeAvailability.status === 'AVAILABLE'
                          ? 'rgba(16, 185, 129, 0.3)'
                          : recipeAvailability.status === 'LOW_STOCK'
                          ? 'rgba(245, 158, 11, 0.3)'
                          : 'rgba(239, 68, 68, 0.3)'
                      }`,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: '0.9rem',
                          color: recipeAvailability.status === 'AVAILABLE'
                            ? 'var(--success)'
                            : recipeAvailability.status === 'LOW_STOCK'
                            ? 'var(--warning)'
                            : 'var(--danger)',
                        }}
                      >
                        {recipeAvailability.status === 'AVAILABLE' && '🟢 IN STOCK & READY TO COOK'}
                        {recipeAvailability.status === 'LOW_STOCK' && '🟡 LIMITED CAPACITY'}
                        {recipeAvailability.status === 'OUT_OF_STOCK' && '🔴 INSUFFICIENT WAREHOUSE STOCK'}
                      </span>
                      <strong style={{ fontSize: '1rem', fontFamily: 'Outfit' }}>
                        {recipeAvailability.max_portions} portions available
                      </strong>
                    </div>

                    {recipeAvailability.shortages && recipeAvailability.shortages.length > 0 && (
                      <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.78rem', color: '#f87171' }}>
                        <div style={{ fontWeight: 600, marginBottom: '4px' }}>Insufficient Stock Breakdown:</div>
                        {recipeAvailability.shortages.map((s, idx) => (
                          <div key={idx}>
                            &bull; <strong>{s.ingredient_name}</strong>: Requires {s.required} {s.unit}, only {s.available} {s.unit} in stock (Shortage: {s.shortage} {s.unit})
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Mapped Recipe Ingredients List */}
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px', letterSpacing: '0.04em' }}>
                    RECIPE BILL OF MATERIALS (PER 1 PORTION)
                  </div>

                  {recipeIngredients.length === 0 ? (
                    <div style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      No raw ingredients configured yet for this recipe.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {recipeIngredients.map((ing, idx) => (
                        <div
                          key={ing.id || idx}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '10px 14px',
                            borderRadius: 'var(--radius-md)',
                            background: 'var(--bg-tertiary)',
                            border: '1px solid var(--border-subtle)',
                            fontSize: '0.85rem',
                          }}
                        >
                          <div>
                            <div style={{ fontWeight: 700 }}>{ing.ingredient_name || ing.name}</div>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                              Warehouse Stock: {ing.available_stock != null ? `${ing.available_stock} ${ing.ingredient_unit || ing.unit}` : 'Available'}
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{ fontWeight: 800, color: 'var(--accent)', fontFamily: 'Outfit' }}>
                              {ing.quantity_required} {ing.unit}
                            </span>
                            {canManageMenu && (
                              <button
                                type="button"
                                onClick={() => handleDeleteIngredient(ing.ingredient_id)}
                                className="btn btn-danger btn-sm"
                                title="Remove from Recipe"
                                style={{ padding: '5px 8px' }}
                              >
                                <Trash2 size={13} />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Add Raw Material to Recipe Form */}
                {canManageMenu && (
                  <form onSubmit={handleAddIngredient} style={{ marginTop: '8px', padding: '16px', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700 }}>
                      + Add / Update Raw Material in Recipe
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '10px' }}>
                      <div>
                        <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Ingredient</label>
                        <select
                          value={selectedIngId}
                          onChange={e => {
                            setSelectedIngId(e.target.value);
                            const found = inventoryList.find(i => i.id === e.target.value);
                            if (found) {
                              const u = found.unit;
                              setIngUnit(u === 'KG' ? 'GRAM' : (u === 'LITRE' ? 'ML' : u));
                            }
                          }}
                          className="select"
                          style={{ height: '36px', fontSize: '0.8rem' }}
                        >
                          {inventoryList.map(inv => (
                            <option key={inv.id} value={inv.id}>
                              {inv.name} ({inv.current_stock} {inv.unit} in stock)
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Qty / Plate</label>
                        <input
                          type="number"
                          step="0.01"
                          required
                          min="0.01"
                          placeholder="e.g. 250"
                          value={ingQty}
                          onChange={e => setIngQty(e.target.value)}
                          className="input"
                          style={{ height: '36px', fontSize: '0.8rem' }}
                        />
                      </div>

                      <div>
                        <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Unit</label>
                        <select
                          value={ingUnit}
                          onChange={e => setIngUnit(e.target.value)}
                          className="select"
                          style={{ height: '36px', fontSize: '0.8rem' }}
                        >
                          <option value="GRAM">g (grams)</option>
                          <option value="KG">kg (kilograms)</option>
                          <option value="ML">ml (millilitres)</option>
                          <option value="LITRE">L (litres)</option>
                          <option value="PIECE">piece</option>
                          <option value="PACKET">packet</option>
                        </select>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={savingRecipe || !selectedIngId || !ingQty}
                      className="btn btn-primary btn-sm"
                      style={{ alignSelf: 'flex-start', marginTop: '4px' }}
                    >
                      {savingRecipe ? 'Saving...' : 'Save Ingredient to Recipe'}
                    </button>
                  </form>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                  <button onClick={() => setRecipeItem(null)} className="btn btn-secondary">
                    Close Recipe Builder
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Floating Bottom Cart Bar (when cart has items and drawer is closed) */}
      {cartCount > 0 && !showCartDrawer && (
        <div
          onClick={() => setShowCartDrawer(true)}
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '28px',
            zIndex: 120,
            background: 'var(--primary-gradient)',
            color: '#fff',
            padding: '12px 22px',
            borderRadius: 'var(--radius-full)',
            boxShadow: '0 8px 30px rgba(99, 102, 241, 0.5)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            cursor: 'pointer',
            transition: 'transform 0.2s ease',
          }}
          onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-2px) scale(1.02)')}
          onMouseLeave={e => (e.currentTarget.style.transform = 'none')}
        >
          <div style={{ position: 'relative' }}>
            <ShoppingCart size={20} />
            <span
              style={{
                position: 'absolute',
                top: '-8px',
                right: '-8px',
                background: '#fff',
                color: 'var(--primary)',
                fontSize: '0.7rem',
                fontWeight: 800,
                width: '18px',
                height: '18px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {cartCount}
            </span>
          </div>
          <div style={{ fontWeight: 800, fontSize: '0.9rem' }}>
            {cartCount} {cartCount === 1 ? 'item' : 'items'} in Cart &bull; ₹{cartTotal.toFixed(2)}
          </div>
          <span style={{ background: 'rgba(255,255,255,0.25)', padding: '4px 10px', borderRadius: 'var(--radius-full)', fontSize: '0.75rem', fontWeight: 700 }}>
            View Cart &rarr;
          </span>
        </div>
      )}

      {/* Slide-out Order Cart Drawer */}
      {showCartDrawer && (
        <div className="modal-overlay" onClick={() => setShowCartDrawer(false)} style={{ zIndex: 140 }}>
          <div
            onClick={e => e.stopPropagation()}
            style={{
              position: 'fixed',
              top: 0,
              right: 0,
              bottom: 0,
              width: '100%',
              maxWidth: '460px',
              background: 'var(--bg-secondary)',
              borderLeft: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: 'var(--shadow-xl)',
              zIndex: 150,
            }}
          >
            {/* Drawer Header */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', background: 'var(--primary-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <ShoppingCart size={18} />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Order Cart</h2>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{cartCount} items selected</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {cart.length > 0 && (
                  <button onClick={handleClearCart} className="btn btn-secondary btn-sm" style={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                    Clear
                  </button>
                )}
                <button onClick={() => setShowCartDrawer(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}>
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Drawer Body */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Order Type Toggle */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', background: 'var(--bg-tertiary)', padding: '4px', borderRadius: 'var(--radius-md)' }}>
                <button
                  type="button"
                  onClick={() => setOrderType('DINE_IN')}
                  className={`btn btn-sm ${orderType === 'DINE_IN' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ border: 'none', borderRadius: 'var(--radius-sm)', justifyContent: 'center' }}
                >
                  🍽️ Dine-In
                </button>
                <button
                  type="button"
                  onClick={() => setOrderType('TAKEAWAY')}
                  className={`btn btn-sm ${orderType === 'TAKEAWAY' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ border: 'none', borderRadius: 'var(--radius-sm)', justifyContent: 'center' }}
                >
                  🥡 Takeaway
                </button>
              </div>

              {/* Table Selection for Dine-in */}
              {orderType === 'DINE_IN' && (
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                    Select Table *
                  </label>
                  <select
                    value={selectedTable}
                    onChange={e => setSelectedTable(e.target.value)}
                    className="select"
                    style={{ width: '100%' }}
                  >
                    {tablesList.map(t => (
                      <option key={t.id} value={t.id}>
                        {t.table_number || `Table #${t.id.slice(-4)}`} &bull; Capacity: {t.capacity} ({t.status})
                      </option>
                    ))}
                    {tablesList.length === 0 && <option value="">No tables found</option>}
                  </select>
                </div>
              )}

              {/* Guest Details */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Guest Name</label>
                  <input
                    type="text"
                    placeholder="Guest Name"
                    value={customerName}
                    onChange={e => setCustomerName(e.target.value)}
                    className="input"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Phone</label>
                  <input
                    type="tel"
                    placeholder="Phone number"
                    value={customerPhone}
                    onChange={e => setCustomerPhone(e.target.value)}
                    className="input"
                    style={{ height: '36px', fontSize: '0.8rem' }}
                  />
                </div>
              </div>

              {/* Items List */}
              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px', letterSpacing: '0.04em' }}>
                  Selected Items ({cart.length})
                </div>

                {cart.length === 0 ? (
                  <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <ShoppingCart size={36} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
                    <div style={{ fontWeight: 600 }}>Your cart is empty</div>
                    <p style={{ fontSize: '0.8rem', marginTop: '4px' }}>Click "+ Add" on any dish to add it here.</p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {cart.map((c) => {
                      const itemTotal = parseFloat(c.item.final_price || c.item.price || 0) * c.quantity;
                      return (
                        <div
                          key={c.item.id}
                          style={{
                            background: 'var(--bg-tertiary)',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-md)',
                            padding: '12px 14px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div className={`food-symbol ${c.item.is_vegetarian ? 'veg' : 'nonveg'}`} style={{ width: '12px', height: '12px', padding: '1px' }}>
                                {c.item.is_vegetarian ? <span style={{ width: '6px', height: '6px' }} /> : <span style={{ borderLeftWidth: '3px', borderRightWidth: '3px', borderBottomWidth: '6px' }} />}
                              </div>
                              <div>
                                <div style={{ fontWeight: 700, fontSize: '0.875rem' }}>{c.item.name}</div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>₹{parseFloat(c.item.final_price || c.item.price || 0).toFixed(2)} / plate</div>
                              </div>
                            </div>
                            <div style={{ fontWeight: 800, color: 'var(--primary)', fontFamily: 'Outfit', fontSize: '0.95rem' }}>
                              ₹{itemTotal.toFixed(2)}
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2px' }}>
                            <input
                              type="text"
                              placeholder="Notes (e.g. less spicy)..."
                              value={c.instructions}
                              onChange={e => handleUpdateCartInstructions(c.item.id, e.target.value)}
                              className="input"
                              style={{ height: '30px', fontSize: '0.72rem', flex: 1, marginRight: '10px' }}
                            />
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: 'var(--radius-sm)', padding: '2px 4px' }}>
                              <button
                                type="button"
                                onClick={() => handleUpdateCartQty(c.item.id, -1)}
                                style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', padding: '3px 6px', display: 'flex' }}
                              >
                                <Minus size={13} />
                              </button>
                              <span style={{ fontWeight: 800, fontSize: '0.825rem', minWidth: '16px', textAlign: 'center' }}>{c.quantity}</span>
                              <button
                                type="button"
                                onClick={() => handleAddToCart(c.item)}
                                style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', padding: '3px 6px', display: 'flex' }}
                              >
                                <Plus size={13} />
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Drawer Footer / Checkout */}
            {cart.length > 0 && (
              <div style={{ padding: '18px 24px', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-tertiary)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                  <span>Subtotal</span>
                  <span>₹{cartSubtotal.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                  <span>GST (5%)</span>
                  <span>₹{cartTax.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', borderTop: '1px dashed var(--border-subtle)', paddingTop: '8px' }}>
                  <span>Total Payable</span>
                  <span style={{ color: 'var(--primary)', fontFamily: 'Outfit' }}>₹{cartTotal.toFixed(2)}</span>
                </div>

                <button
                  type="button"
                  onClick={handlePlaceOrder}
                  disabled={placingOrder}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '12px', justifyContent: 'center', fontSize: '0.925rem', fontWeight: 800, boxShadow: 'var(--shadow-glow)' }}
                >
                  {placingOrder ? 'Sending to Kitchen...' : `Place Order & Send to Kitchen (₹${cartTotal.toFixed(2)})`}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
