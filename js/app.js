(function () {
  'use strict';

  // ===== 商品数据 =====
  var PRODUCTS = [
    { id: 1, name: '草莓奶糖', emoji: '🍬', category: '糖果', price: 5.00, stock: 200 },
    { id: 2, name: '橘子软糖', emoji: '🍬', category: '糖果', price: 6.00, stock: 150 },
    { id: 3, name: '黄油曲奇', emoji: '🍪', category: '饼干', price: 12.00, stock: 100,
      modifiers: [
        { group: '口味', type: 'single', options: [
          { label: '原味', priceDelta: 0 },
          { label: '抹茶', priceDelta: 2.00 },
          { label: '巧克力', priceDelta: 3.00 }
        ]}
      ]
    },
    { id: 4, name: '苏打饼干', emoji: '🍪', category: '饼干', price: 8.00, stock: 120 },
    { id: 5, name: '开心果', emoji: '🥜', category: '坚果', price: 25.00, stock: 80 },
    { id: 6, name: '混合坚果', emoji: '🥜', category: '坚果', price: 35.00, stock: 60 },
    { id: 7, name: '牛奶巧克力', emoji: '🍫', category: '巧克力', price: 15.00, stock: 90,
      modifiers: [
        { group: '份量', type: 'single', options: [
          { label: '标准装', priceDelta: 0 },
          { label: '大包装', priceDelta: 5.00 }
        ]},
        { group: '加料', type: 'multiple', max: 2, options: [
          { label: '加坚果', priceDelta: 3.00 },
          { label: '加焦糖', priceDelta: 2.00 }
        ]}
      ]
    },
    { id: 8, name: '黑巧克块', emoji: '🍫', category: '巧克力', price: 18.00, stock: 70 },
    { id: 9, name: '可乐', emoji: '🥤', category: '饮料', price: 4.00, stock: 200,
      modifiers: [
        { group: '杯型', type: 'single', options: [
          { label: '中杯', priceDelta: 0 },
          { label: '大杯', priceDelta: 2.00 }
        ]}
      ]
    },
    { id: 10, name: '柠檬茶', emoji: '🥤', category: '饮料', price: 5.00, stock: 180 },
    { id: 11, name: '芒果果冻', emoji: '🍮', category: '果冻', price: 6.00, stock: 100,
      modifiers: [
        { group: '加料', type: 'multiple', max: 1, options: [
          { label: '加椰奶', priceDelta: 2.00 },
          { label: '加西米露', priceDelta: 1.50 }
        ]}
      ]
    },
    { id: 12, name: '草莓布丁', emoji: '🍮', category: '果冻', price: 7.00, stock: 90 }
  ];

  var LS_STOCK = 'snack_stock';
  var LS_CART = 'snack_cart';
  var LS_USERS = 'snack_users';
  var LS_SESSION = 'snack_session';
  var LS_ORDERS = 'snack_orders';
  var LS_SPECIALS = 'snack_specials';
  var LS_STAFF = 'snack_staff';
  var LS_STOCK_HISTORY = 'snack_stock_history';
  var LS_STOCK_THRESHOLD = 'snack_stock_threshold';
  var LS_PROMO_DISMISSED = 'snack_promo_dismissed';

  var stockData = {};
  var cartData = [];
  var currentCat = '全部';
  var currentSearch = '';
  var currentSort = 'default';
  var lastOrderSnap = [];
  var currentUser = null;
  var staffMode = false;
  var staffOrderFilter = 'all';
  var modifierPendingId = null;
  var modifierSelections = {};
  var bc = null;

  // ===== 初始化 =====
  function init() {
    // Default staff user for demo
    if (!localStorage.getItem(LS_STAFF)) {
      localStorage.setItem(LS_STAFF, 'admin');
    }
    loadStock();
    loadCart();
    authInit();
    renderPromoBanner();
    renderFavorites();
    renderProducts();
    updateBadge();
    updateBottomBar();
    updateStaffToggle();
    initBroadcast();
  }

  // ===== 库存 =====
  function loadStock() {
    var saved = localStorage.getItem(LS_STOCK);
    if (saved) {
      stockData = JSON.parse(saved);
    } else {
      for (var i = 0; i < PRODUCTS.length; i++) {
        stockData[PRODUCTS[i].id] = PRODUCTS[i].stock;
      }
      saveStock();
    }
  }

  function saveStock() { localStorage.setItem(LS_STOCK, JSON.stringify(stockData)); }

  function getStock(id) { return stockData[id] !== undefined ? stockData[id] : 0; }

  // ===== Feature 7: 库存管理辅助 =====
  function getStockThreshold() {
    var t = localStorage.getItem(LS_STOCK_THRESHOLD);
    return t ? parseInt(t) : 20;
  }

  function getStockLabel(stock) {
    if (stock <= 0) return 'out';
    if (stock < getStockThreshold()) return 'low';
    return 'normal';
  }

  function getStockHistory() {
    return JSON.parse(localStorage.getItem(LS_STOCK_HISTORY) || '[]');
  }

  function logStockAction(pid, name, amount) {
    var history = getStockHistory();
    history.unshift({
      productId: pid,
      productName: name,
      amount: amount,
      newStock: getStock(pid),
      timestamp: new Date().toISOString()
    });
    if (history.length > 20) history.length = 20;
    localStorage.setItem(LS_STOCK_HISTORY, JSON.stringify(history));
  }

  function restock(pid, amount) {
    if (amount <= 0) return;
    stockData[pid] = (stockData[pid] || 0) + amount;
    saveStock();
    var p = getProduct(pid);
    logStockAction(pid, p ? p.name : 'Unknown', amount);
    if (staffMode) renderStockPanel();
    renderProducts();
    showToast('已补货 ' + (p ? p.name : '') + ' +' + amount);
  }

  function renderStockPanel() {
    var container = document.getElementById('stockManagement');
    var threshold = getStockThreshold();
    var html = '<div class="stock-table-wrap"><table class="stock-table">';
    html += '<thead><tr><th>商品</th><th>名称</th><th>库存</th><th>状态</th><th>操作</th></tr></thead><tbody>';

    for (var i = 0; i < PRODUCTS.length; i++) {
      var p = PRODUCTS[i];
      var stock = getStock(p.id);
      var label = getStockLabel(stock);
      var statusText = stock <= 0 ? '缺货' : (label === 'low' ? '库存不足' : '正常');
      var statusClass = stock <= 0 ? 'red' : (label === 'low' ? 'yellow' : 'green');

      html += '<tr>';
      html += '<td>' + p.emoji + '</td>';
      html += '<td>' + p.name + '</td>';
      html += '<td><strong>' + stock + '</strong></td>';
      html += '<td><span class="stock-status ' + statusClass + '">' + statusText + '</span></td>';
      html += '<td class="stock-controls">';
      html += '<button class="btn-restock" onclick="window._snack.restock(' + p.id + ',10)">+10</button>';
      html += '<button class="btn-restock" onclick="window._snack.restock(' + p.id + ',50)">+50</button>';
      html += '<button class="btn-restock" onclick="window._snack.restock(' + p.id + ',100)">+100</button>';
      html += '<input type="number" class="restock-input" id="restockInput' + p.id + '" min="1" value="1" placeholder="数量">';
      html += '<button class="btn-restock" onclick="var v=parseInt(document.getElementById(\'restockInput' + p.id + '\').value);if(v>0)window._snack.restock(' + p.id + ',v)">补货</button>';
      html += '</td>';
      html += '</tr>';
    }

    html += '</tbody></table></div>';

    // Threshold config
    html += '<div style="margin:12px 0;display:flex;align-items:center;gap:8px;">';
    html += '<label style="font-size:0.82rem;">低库存阈值：</label>';
    html += '<input type="number" id="thresholdInput" value="' + threshold + '" min="1" max="100" style="width:60px;padding:4px 8px;border:1px solid var(--border);border-radius:6px;font-size:0.82rem;">';
    html += '<button class="btn-restock" onclick="var v=parseInt(document.getElementById(\'thresholdInput\').value);if(v>0){localStorage.setItem(\'' + LS_STOCK_THRESHOLD + '\',v);window._snack.renderStockPanel();showToast(\'阈值已更新\')}">更新</button>';
    html += '</div>';

    // Stock history
    var history = getStockHistory();
    if (history.length > 0) {
      html += '<div class="stock-history">';
      html += '<h4>📋 补货记录 (最近20条)</h4>';
      html += '<div class="stock-history-list">';
      for (var j = 0; j < history.length; j++) {
        var h = history[j];
        var d = new Date(h.timestamp);
        var timeStr = pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
        html += '<div class="stock-history-item">' + timeStr + ' — ' + escapeHtml(h.productName) + ' +' + h.amount + ' (现库存: ' + h.newStock + ')</div>';
      }
      html += '</div></div>';
    }

    container.innerHTML = html;
  }

  // ===== Feature 1: 订单历史 =====
  function getOrders() {
    return JSON.parse(localStorage.getItem(LS_ORDERS) || '[]');
  }

  function saveOrders(orders) {
    localStorage.setItem(LS_ORDERS, JSON.stringify(orders));
  }

  function openOrders() {
    renderOrders();
    document.getElementById('ordersOverlay').classList.add('show');
    document.getElementById('ordersModal').classList.add('show');
  }

  function closeOrders() {
    document.getElementById('ordersOverlay').classList.remove('show');
    document.getElementById('ordersModal').classList.remove('show');
  }

  function renderOrders() {
    var container = document.getElementById('ordersList');
    var orders = getOrders();

    if (!orders || orders.length === 0) {
      container.innerHTML = '<div class="orders-empty">📭 暂无订单记录，快去购物吧！</div>';
      return;
    }

    var sorted = orders.slice().sort(function (a, b) { return new Date(b.date) - new Date(a.date); });
    var html = '';

    for (var i = 0; i < sorted.length; i++) {
      var o = sorted[i];
      var d = new Date(o.date);
      var dateStr = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
      var statusMap = { received: '已接收', preparing: '准备中', ready: '已完成', completed: '已完成' };
      var statusLabel = statusMap[o.status] || o.status;
      var oStatus = o.status || 'completed';

      html += '<div class="order-card">';
      html += '<div class="order-card-header">';
      html += '<div><div class="order-id">' + o.id + '</div><div class="order-date">' + dateStr + '</div></div>';
      html += '<span class="order-status-badge ' + oStatus + '">' + statusLabel + '</span>';
      html += '</div>';
      html += '<div class="order-items-list">';
      for (var j = 0; j < o.items.length; j++) {
        var item = o.items[j];
        html += item.emoji + ' ' + escapeHtml(item.name) + ' × ' + item.qty + ' = ¥' + item.subtotal.toFixed(2) + '<br>';
      }
      html += '</div>';
      html += '<div class="order-total">合计: ¥' + o.total.toFixed(2) + '</div>';
      html += '<div class="order-actions">';
      html += '<button class="btn-reorder" onclick="window._snack.reorder(' + "'" + o.id + "'" + ')">🔄 再来一单</button>';
      html += '</div>';
      html += '</div>';
    }

    container.innerHTML = html;
  }

  function reorder(orderId) {
    if (!isLoggedIn()) {
      showToast('请先登录');
      openLogin();
      return;
    }
    var orders = getOrders();
    var order = null;
    for (var i = 0; i < orders.length; i++) {
      if (orders[i].id === orderId) { order = orders[i]; break; }
    }
    if (!order) { showToast('订单不存在'); return; }

    var added = 0;
    var skipped = 0;
    for (var j = 0; j < order.items.length; j++) {
      var oi = order.items[j];
      if (!oi.productId) { skipped++; continue; }
      var stock = getStock(oi.productId);
      if (stock <= 0) { skipped++; continue; }

      var idx = cartFind(oi.productId, null);
      var currentQty = idx >= 0 ? cartData[idx].quantity : 0;
      var addQty = Math.min(oi.qty, stock - currentQty);
      if (addQty <= 0) { skipped++; continue; }

      if (idx >= 0) {
        cartData[idx].quantity += addQty;
      } else {
        var p = getProduct(oi.productId);
        if (!p) { skipped++; continue; }
        cartData.push({ id: oi.productId, name: p.name, emoji: p.emoji, price: p.price, quantity: addQty });
      }
      added += addQty;
      if (addQty < oi.qty) skipped++;
    }

    saveCart();
    updateBadge();
    updateBottomBar();
    renderProducts();
    renderFavorites();

    var msg = '已重新加入购物车 ✓';
    if (skipped > 0) msg += ' (' + skipped + '件因库存不足未加入)';
    showToast(msg);

    if (document.getElementById('cartDrawer').classList.contains('open')) updateDrawer();
  }

  // ===== 购物车 =====
  function loadCart() {
    var saved = localStorage.getItem(LS_CART);
    if (saved) cartData = JSON.parse(saved);
  }

  function saveCart() { localStorage.setItem(LS_CART, JSON.stringify(cartData)); }

  function getModKey(modifiers) {
    if (!modifiers || modifiers.length === 0) return '';
    var parts = [];
    for (var i = 0; i < modifiers.length; i++) {
      parts.push(modifiers[i].group + ':' + modifiers[i].selection);
    }
    parts.sort();
    return parts.join('|');
  }

  function cartFind(id, modifiers) {
    var key = getModKey(modifiers);
    for (var i = 0; i < cartData.length; i++) {
      var itemKey = getModKey(cartData[i].modifiers);
      if (cartData[i].id === id && itemKey === key) return i;
    }
    return -1;
  }

  function cartCount() {
    var t = 0;
    for (var i = 0; i < cartData.length; i++) t += cartData[i].quantity;
    return t;
  }

  function calcItemTotal(item) {
    var base = item.price * item.quantity;
    var modSum = 0;
    if (item.modifiers) {
      for (var i = 0; i < item.modifiers.length; i++) {
        modSum += item.modifiers[i].delta;
      }
    }
    return base + modSum * item.quantity;
  }

  function cartTotal() {
    var t = 0;
    for (var i = 0; i < cartData.length; i++) t += calcItemTotal(cartData[i]);
    return t;
  }

  // ===== Feature 2: 收藏 =====
  function getFavKey() {
    if (!currentUser) return null;
    return 'snack_favorites_' + currentUser.username;
  }

  function getFavorites() {
    var key = getFavKey();
    if (!key) return [];
    return JSON.parse(localStorage.getItem(key) || '[]');
  }

  function saveFavorites(favs) {
    var key = getFavKey();
    if (!key) return;
    localStorage.setItem(key, JSON.stringify(favs));
  }

  function toggleFavorite(pid) {
    if (!isLoggedIn()) { showToast('请先登录'); return; }
    var favs = getFavorites();
    var idx = -1;
    for (var i = 0; i < favs.length; i++) {
      if (favs[i].id === pid) { idx = i; break; }
    }
    if (idx >= 0) {
      favs.splice(idx, 1);
      showToast('已取消收藏');
    } else {
      var p = getProduct(pid);
      if (!p) return;
      favs.push({ id: p.id, name: p.name, emoji: p.emoji, price: p.price });
      showToast('已收藏 ' + p.name + ' ⭐');
    }
    saveFavorites(favs);
    renderFavorites();
    if (document.getElementById('cartDrawer').classList.contains('open')) updateDrawer();
  }

  function isFavorite(pid) {
    if (!currentUser) return false;
    var favs = getFavorites();
    for (var i = 0; i < favs.length; i++) {
      if (favs[i].id === pid) return true;
    }
    return false;
  }

  function renderFavorites() {
    var section = document.getElementById('favoritesSection');
    var grid = document.getElementById('favGrid');
    if (!section || !grid) return;

    if (!currentUser) { section.style.display = 'none'; return; }

    var favs = getFavorites();
    if (favs.length === 0) { section.style.display = 'none'; return; }

    section.style.display = 'block';
    grid.innerHTML = '';
    for (var i = 0; i < favs.length; i++) {
      var f = favs[i];
      var stock = getStock(f.id);
      var out = stock <= 0;
      var div = document.createElement('div');
      div.className = 'fav-item';
      div.innerHTML =
        '<div class="fav-item-emoji">' + f.emoji + '</div>' +
        '<div class="fav-item-name">' + escapeHtml(f.name) + '</div>' +
        '<div class="fav-item-price">¥' + f.price.toFixed(2) + '</div>' +
        '<button class="fav-add-btn" onclick="window._snack.addToCart(' + f.id + ')"' + (out ? ' disabled' : '') + '>' + (out ? '缺货' : '加入购物车') + '</button>';
      grid.appendChild(div);
    }
  }

  function toggleFavSection() {
    var grid = document.getElementById('favGrid');
    var toggle = document.getElementById('favToggle');
    if (!grid || !toggle) return;
    var collapsed = grid.style.display === 'none';
    grid.style.display = collapsed ? '' : 'none';
    toggle.classList.toggle('collapsed', !collapsed);
  }

  // ===== Feature 6: 特价促销 =====
  function getSpecials() {
    return JSON.parse(localStorage.getItem(LS_SPECIALS) || '[]');
  }

  function saveSpecials(specials) {
    localStorage.setItem(LS_SPECIALS, JSON.stringify(specials));
  }

  function getSpecialForProduct(pid) {
    var specials = getSpecials();
    var now = new Date();
    for (var i = 0; i < specials.length; i++) {
      var s = specials[i];
      if (s.productId !== pid) continue;
      if (s.endDate) {
        var end = new Date(s.endDate);
        if (end <= now) continue;
      }
      return s;
    }
    return null;
  }

  function renderPromoBanner() {
    var banner = document.getElementById('promoBanner');
    var textEl = document.getElementById('promoText');
    if (!banner || !textEl) return;

    var dismissed = localStorage.getItem(LS_PROMO_DISMISSED);
    if (dismissed) {
      var dimTime = parseInt(dismissed);
      if (Date.now() - dimTime < 86400000) {
        banner.style.display = 'none';
        return;
      }
    }

    var specials = getSpecials();
    var now = new Date();
    var active = [];
    for (var i = 0; i < specials.length; i++) {
      var s = specials[i];
      if (s.endDate) { var end = new Date(s.endDate); if (end <= now) continue; }
      active.push(s);
    }

    if (active.length > 0) {
      textEl.textContent = '🔥 ' + active[0].label + ' — 限时优惠，快来抢购！';
      banner.style.display = 'block';
    } else {
      banner.style.display = 'none';
    }
  }

  function closePromo() {
    var banner = document.getElementById('promoBanner');
    if (banner) banner.style.display = 'none';
    localStorage.setItem(LS_PROMO_DISMISSED, Date.now().toString());
  }

  function renderSpecialsPanel() {
    var container = document.getElementById('specialsManagement');
    var specials = getSpecials();

    var html = '<div class="specials-editor">';
    html += '<h4 style="margin-bottom:10px;">🔥 特价管理</h4>';

    html += '<div class="special-form">';
    html += '<select id="spProduct">';
    for (var i = 0; i < PRODUCTS.length; i++) {
      html += '<option value="' + PRODUCTS[i].id + '">' + PRODUCTS[i].emoji + ' ' + PRODUCTS[i].name + '</option>';
    }
    html += '</select>';
    html += '<select id="spType"><option value="percent">折扣(%)</option><option value="fixed">固定价(¥)</option></select>';
    html += '<input type="number" id="spValue" placeholder="值" min="1" style="width:70px;">';
    html += '<input type="text" id="spLabel" placeholder="标签" style="width:110px;">';
    html += '<input type="date" id="spEndDate" style="width:135px;">';
    html += '<button class="btn-add-special" onclick="window._snack.addSpecialItem()">添加</button>';
    html += '</div>';

    if (specials.length === 0) {
      html += '<div class="specials-empty">暂无特价活动</div>';
    } else {
      for (var j = 0; j < specials.length; j++) {
        var s = specials[j];
        var p = getProduct(s.productId);
        var pName = p ? p.emoji + ' ' + p.name : 'ID:' + s.productId;
        var discountInfo = s.type === 'percent' ? s.value + '% OFF' : '¥' + s.value;
        html += '<div class="special-item">';
        html += '<span>' + pName + ' — ' + escapeHtml(s.label) + ' (' + discountInfo + ')' + (s.endDate ? ' 至 ' + s.endDate : '') + '</span>';
        html += '<button class="btn-remove-special" onclick="window._snack.removeSpecial(' + j + ')">删除</button>';
        html += '</div>';
      }
    }

    html += '</div>';
    container.innerHTML = html;
  }

  function addSpecialItem() {
    var pid = parseInt(document.getElementById('spProduct').value);
    var type = document.getElementById('spType').value;
    var value = parseFloat(document.getElementById('spValue').value);
    var label = document.getElementById('spLabel').value.trim();
    var endDate = document.getElementById('spEndDate').value || null;
    if (!value || value <= 0) { showToast('请输入有效值'); return; }
    if (!label) { showToast('请输入标签'); return; }
    var specials = getSpecials();
    specials.push({ productId: pid, type: type, value: value, label: label, endDate: endDate });
    saveSpecials(specials);
    renderSpecialsPanel();
    renderPromoBanner();
    renderProducts();
    showToast('已添加特价商品');
  }

  function removeSpecial(idx) {
    var specials = getSpecials();
    specials.splice(idx, 1);
    saveSpecials(specials);
    renderSpecialsPanel();
    renderPromoBanner();
    renderProducts();
    showToast('已删除特价');
  }

  // ===== 搜索 =====
  function search() {
    currentSearch = document.getElementById('searchInput').value.trim();
    renderProducts();
  }

  // ===== 筛选分类 =====
  function filterCat(cat) {
    currentCat = cat;
    document.querySelectorAll('.tag-btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.cat === cat || (cat === '全部' && btn.dataset.cat === '全部'));
    });
    renderProducts();
  }

  // ===== Feature 5: 排序 =====
  function setSort(sort) {
    currentSort = sort;
    renderProducts();
  }

  // ===== 渲染商品 =====
  function renderProducts() {
    var grid = document.getElementById('productGrid');
    grid.innerHTML = '';

    // Filter
    var filtered = [];
    for (var i = 0; i < PRODUCTS.length; i++) {
      var p = PRODUCTS[i];
      if (currentCat !== '全部' && p.category !== currentCat) continue;
      if (currentSearch && p.name.toLowerCase().indexOf(currentSearch.toLowerCase()) === -1) continue;
      filtered.push(p);
    }

    // Sort (Feature 5)
    filtered.sort(function (a, b) {
      switch (currentSort) {
        case 'price-asc': return a.price - b.price;
        case 'price-desc': return b.price - a.price;
        case 'name': return a.name.localeCompare(b.name, 'zh');
        default: return a.id - b.id;
      }
    });

    for (var i = 0; i < filtered.length; i++) {
      var p = filtered[i];
      var stock = getStock(p.id);
      var outOfStock = stock <= 0;
      var catColor = getCatColor(p.category);
      var special = getSpecialForProduct(p.id);
      var hasModifiers = p.modifiers && p.modifiers.length > 0;

      var card = document.createElement('div');
      card.className = 'product-card' + (outOfStock ? ' out-of-stock' : '');

      var imgHtml = '<div class="card-img-wrap"><div class="card-img">' + p.emoji + '</div>';
      if (special) {
        var badgeLabel = special.type === 'percent' ? special.value + '% OFF' : (special.type === 'fixed' ? '¥' + special.value : 'SALE');
        imgHtml += '<span class="sale-badge">🔥 ' + badgeLabel + '</span>';
      }
      imgHtml += '</div>';

      var priceHtml;
      if (special) {
        var salePrice = special.type === 'percent'
          ? p.price * (1 - special.value / 100)
          : (special.type === 'fixed' ? special.value : p.price);
        priceHtml = '<div class="card-price"><span class="original-price">¥' + p.price.toFixed(2) + '</span><span class="sale-price">¥' + salePrice.toFixed(2) + '</span></div>';
      } else {
        priceHtml = '<div class="card-price">¥' + p.price.toFixed(2) + '</div>';
      }

      var btnHtml;
      if (outOfStock) {
        btnHtml = '<button class="btn-add" disabled>缺货</button>';
      } else if (hasModifiers) {
        btnHtml =
          '<div style="display:flex;gap:4px;">' +
          '<button class="btn-add" style="flex:1;" onclick="window._snack.addToCart(' + p.id + ')">加入</button>' +
          '<button class="btn-add" style="flex:0;padding:9px 10px;" onclick="window._snack.openModifier(' + p.id + ')" title="自定义">🔧</button>' +
          '</div>';
      } else {
        btnHtml = '<button class="btn-add" onclick="window._snack.addToCart(' + p.id + ')">加入购物车</button>';
      }

      card.innerHTML = imgHtml +
        '<div class="card-body">' +
        '<span class="card-cat-tag" style="background:' + catColor.bg + ';color:' + catColor.text + '">' + p.category + '</span>' +
        '<div class="card-name">' + p.name + '</div>' +
        priceHtml +
        '<div class="card-stock' + (outOfStock ? ' zero' : '') + '">' + (outOfStock ? '缺货' : '库存 ' + stock + ' 件') + '</div>' +
        btnHtml +
        '</div>';
      grid.appendChild(card);
    }
  }

  function getCatColor(cat) {
    var map = {
      '糖果': { bg: '#FFF0F5', text: '#FF69B4' },
      '饼干': { bg: '#FFF8DC', text: '#DAA520' },
      '坚果': { bg: '#F0FFF0', text: '#228B22' },
      '巧克力': { bg: '#F5F5DC', text: '#8B4513' },
      '饮料': { bg: '#E0FFFF', text: '#0077B6' },
      '果冻': { bg: '#FFFACD', text: '#FF8C00' }
    };
    return map[cat] || { bg: '#FFF0F5', text: '#FF69B4' };
  }

  // ===== 加入购物车 =====
  function addToCart(id, modifiers) {
    if (!isLoggedIn()) {
      showToast('请先登录后再购物');
      openLogin();
      return;
    }
    var p = getProduct(id);
    if (!p) return;

    // If product has modifiers and none provided, use default
    if (p.modifiers && p.modifiers.length > 0 && (!modifiers || modifiers.length === 0)) {
      // Use first option of each group as default
      var defaults = [];
      for (var mi = 0; mi < p.modifiers.length; mi++) {
        var g = p.modifiers[mi];
        if (g.type === 'single' && g.options.length > 0) {
          defaults.push({ group: g.group, selection: g.options[0].label, delta: g.options[0].priceDelta });
        }
      }
      modifiers = defaults;
    }

    var stock = getStock(id);
    var idx = cartFind(id, modifiers);
    var currentQty = idx >= 0 ? cartData[idx].quantity : 0;

    if (currentQty >= stock) {
      showToast(p.name + ' 已达库存上限 (' + stock + '件)');
      return;
    }

    if (idx >= 0) {
      cartData[idx].quantity++;
    } else {
      var item = { id: id, name: p.name, emoji: p.emoji, price: p.price, quantity: 1 };
      if (modifiers && modifiers.length > 0) {
        item.modifiers = modifiers;
      }
      cartData.push(item);
    }

    saveCart();
    updateBadge();
    updateBottomBar();
    renderProducts();
    renderFavorites();
    showToast('已加入购物车 ✓');
    if (document.getElementById('cartDrawer').classList.contains('open')) updateDrawer();
  }

  // ===== 修改数量 =====
  function updateQuantity(idx, delta) {
    var item = cartData[idx];
    if (!item) return;

    var next = item.quantity + delta;
    if (next <= 0) { removeItem(idx); return; }

    var stock = getStock(item.id);
    if (next > stock) {
      showToast('数量不能超过库存 (' + stock + ')'); return;
    }

    item.quantity = next;
    saveCart();
    updateDrawer();
    updateBadge();
    updateBottomBar();
  }

  // ===== Feature 2 & 4: 收藏 + 自定义用于购物车 =====
  function removeItem(idx) {
    cartData.splice(idx, 1);
    saveCart();
    updateDrawer();
    updateBadge();
    updateBottomBar();
    renderProducts();
  }

  function clearCart() {
    if (cartData.length === 0) return;
    if (!confirm('确定要清空购物车吗？此操作不可撤销。')) return;
    cartData = [];
    saveCart();
    updateDrawer();
    updateBadge();
    updateBottomBar();
    renderProducts();
    showToast('购物车已清空');
  }

  // ===== Feature 4: Modifier Picker =====
  function openModifier(id) {
    var p = getProduct(id);
    if (!p || !p.modifiers) { addToCart(id); return; }
    if (!isLoggedIn()) { showToast('请先登录后再购物'); openLogin(); return; }

    modifierPendingId = id;
    modifierSelections = {};

    // Initialize defaults: first option for single-select, empty for multi
    for (var mi = 0; mi < p.modifiers.length; mi++) {
      var g = p.modifiers[mi];
      if (g.type === 'single') {
        modifierSelections[mi] = [0];
      } else {
        modifierSelections[mi] = [];
      }
    }

    renderModifierPicker(id);
    document.getElementById('modifierOverlay').classList.add('show');
    document.getElementById('modifierModal').classList.add('show');
  }

  function closeModifier() {
    document.getElementById('modifierOverlay').classList.remove('show');
    document.getElementById('modifierModal').classList.remove('show');
    modifierPendingId = null;
    modifierSelections = {};
  }

  function renderModifierPicker(id) {
    var p = getProduct(id);
    if (!p || !p.modifiers) return;

    var html = '<div class="modifier-product-title">' + p.emoji + ' ' + escapeHtml(p.name) + '</div>';
    html += '<div class="modifier-total-line" id="modTotal">合计: ¥' + p.price.toFixed(2) + '</div>';

    for (var mi = 0; mi < p.modifiers.length; mi++) {
      var group = p.modifiers[mi];
      html += '<div class="modifier-group">';
      html += '<div class="modifier-group-title">' + escapeHtml(group.group) + '</div>';
      html += '<div class="modifier-options">';

      for (var oj = 0; oj < group.options.length; oj++) {
        var opt = group.options[oj];
        var isSelected = modifierSelections[mi] && modifierSelections[mi].indexOf(oj) >= 0;
        var deltaText = '';
        if (opt.priceDelta > 0) deltaText = '+¥' + opt.priceDelta.toFixed(2);
        else if (opt.priceDelta < 0) deltaText = '-¥' + Math.abs(opt.priceDelta).toFixed(2);

        html += '<div class="modifier-option' + (isSelected ? ' selected' : '') + '" data-gidx="' + mi + '" data-oidx="' + oj + '" onclick="window._snack.toggleModOption(' + mi + ',' + oj + ')">';
        html += '<span class="modifier-option-label">' + escapeHtml(opt.label) + '</span>';
        if (deltaText) html += '<span class="modifier-option-delta">' + deltaText + '</span>';
        html += '</div>';
      }

      if (group.type === 'multiple' && group.max) {
        html += '<div style="font-size:0.72rem;color:var(--text-light);margin-top:4px;">最多选择 ' + group.max + ' 项</div>';
      }

      html += '</div></div>';
    }

    html += '<div class="modifier-actions">';
    html += '<button class="btn-modifier-confirm" onclick="window._snack.confirmModifier()">确认添加</button>';
    html += '</div>';

    document.getElementById('modifierBody').innerHTML = html;
    updateModTotal();
  }

  function toggleModOption(groupIdx, optIdx) {
    var p = getProduct(modifierPendingId);
    if (!p || !p.modifiers[groupIdx]) return;

    var group = p.modifiers[groupIdx];

    if (group.type === 'single') {
      modifierSelections[groupIdx] = [optIdx];
    } else if (group.type === 'multiple') {
      if (!modifierSelections[groupIdx]) modifierSelections[groupIdx] = [];
      var idx = modifierSelections[groupIdx].indexOf(optIdx);
      if (idx >= 0) {
        modifierSelections[groupIdx].splice(idx, 1);
      } else {
        if (group.max && modifierSelections[groupIdx].length >= group.max) {
          showToast('最多选择 ' + group.max + ' 项');
          return;
        }
        modifierSelections[groupIdx].push(optIdx);
      }
    }

    updateModTotal();
    updateModVisual();
  }

  function updateModTotal() {
    var p = getProduct(modifierPendingId);
    if (!p) return;
    var total = p.price;
    for (var gIdx in modifierSelections) {
      if (!modifierSelections.hasOwnProperty(gIdx)) continue;
      var group = p.modifiers[parseInt(gIdx)];
      var selected = modifierSelections[parseInt(gIdx)];
      if (!selected) continue;
      for (var k = 0; k < selected.length; k++) {
        total += group.options[selected[k]].priceDelta;
      }
    }
    var el = document.getElementById('modTotal');
    if (el) el.textContent = '合计: ¥' + total.toFixed(2);
  }

  function updateModVisual() {
    var els = document.querySelectorAll('.modifier-option[data-gidx]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      var gIdx = parseInt(el.dataset.gidx);
      var oIdx = parseInt(el.dataset.oidx);
      var isSel = modifierSelections[gIdx] && modifierSelections[gIdx].indexOf(oIdx) >= 0;
      el.classList.toggle('selected', isSel);
    }
  }

  function confirmModifier() {
    var p = getProduct(modifierPendingId);
    if (!p) return;

    var modifiers = [];
    for (var gIdx in modifierSelections) {
      if (!modifierSelections.hasOwnProperty(gIdx)) continue;
      var group = p.modifiers[parseInt(gIdx)];
      var selected = modifierSelections[parseInt(gIdx)];
      if (!selected) continue;
      for (var k = 0; k < selected.length; k++) {
        var opt = group.options[selected[k]];
        modifiers.push({
          group: group.group,
          selection: opt.label,
          delta: opt.priceDelta
        });
      }
    }

    addToCart(modifierPendingId, modifiers);
    closeModifier();
  }

  // ===== UI 更新 =====
  function updateBadge() {
    var badge = document.getElementById('cartBadge');
    var n = cartCount();
    badge.textContent = n;
    badge.className = 'cart-badge' + (n > 0 ? ' show' : '');
  }

  function updateBottomBar() {
    var bar = document.getElementById('cartBar');
    var n = cartCount();
    var t = cartTotal();
    var btnBar = document.getElementById('btnSettle');
    var btnDrawer = document.getElementById('btnCheckout');

    bar.classList.toggle('show', n > 0);
    document.getElementById('cartCountBar').textContent = n;
    document.getElementById('cartTotalBar').textContent = '¥' + t.toFixed(2);
    btnBar.disabled = n === 0;
    btnDrawer.disabled = n === 0;
  }

  function updateDrawer() {
    var container = document.getElementById('drawerItems');
    var totalEl = document.getElementById('drawerTotal');

    if (cartData.length === 0) {
      container.innerHTML = '<div class="drawer-empty">购物车是空的，快去挑选零食吧~ 🍭</div>';
      totalEl.textContent = '¥0.00';
      return;
    }

    container.innerHTML = '';
    for (var i = 0; i < cartData.length; i++) {
      var item = cartData[i];
      var isFav = currentUser ? isFavorite(item.id) : false;
      var div = document.createElement('div');
      div.className = 'drawer-item';

      var modHtml = '';
      if (item.modifiers && item.modifiers.length > 0) {
        modHtml = '<div class="cart-item-mods">' + item.modifiers.map(function (m) { return m.selection; }).join(', ') + '</div>';
      }

      div.innerHTML =
        '<span class="drawer-item-emoji">' + item.emoji + '</span>' +
        '<div class="drawer-item-info">' +
        '<div class="drawer-item-name">' + escapeHtml(item.name) + '</div>' +
        '<div class="drawer-item-price">¥' + item.price.toFixed(2) + ' × ' + item.quantity + '</div>' +
        modHtml +
        '<div class="drawer-item-sub">¥' + calcItemTotal(item).toFixed(2) + '</div>' +
        '</div>' +
        '<button class="fav-star ' + (isFav ? 'active' : 'inactive') + '" onclick="window._snack.toggleFavorite(' + item.id + ')" title="' + (isFav ? '取消收藏' : '收藏') + '">' + (isFav ? '★' : '☆') + '</button>' +
        '<div class="drawer-item-controls">' +
        '<button class="qty-btn" onclick="window._snack.updateQuantity(' + i + ',-1)"' + (item.quantity <= 1 ? ' disabled' : '') + '>−</button>' +
        '<span class="qty-num">' + item.quantity + '</span>' +
        '<button class="qty-btn" onclick="window._snack.updateQuantity(' + i + ',1)">+</button>' +
        '</div>' +
        '<button class="btn-remove" onclick="window._snack.removeItem(' + i + ')">🗑</button>';
      container.appendChild(div);
    }
    totalEl.textContent = '¥' + cartTotal().toFixed(2);
  }

  function toggleCart() {
    var open = document.getElementById('cartDrawer').classList.toggle('open');
    document.getElementById('drawerOverlay').classList.toggle('show', open);
    if (open) updateDrawer();
  }

  // ===== 结算 =====
  function openCheckout() {
    if (!isLoggedIn()) {
      showToast('请先登录后再结算');
      openLogin();
      return;
    }
    if (cartData.length === 0) return;

    for (var i = 0; i < cartData.length; i++) {
      var item = cartData[i];
      if (item.quantity > getStock(item.id)) {
        showToast('部分商品库存不足，请调整购物车'); return;
      }
    }

    toggleCart();
    document.getElementById('summaryCount').textContent = cartCount();
    document.getElementById('summaryTotal').textContent = '¥' + cartTotal().toFixed(2);
    document.getElementById('checkoutForm').reset();
    clearErrors();
    if (currentUser) {
      var nameField = document.getElementById('fName');
      if (nameField && !nameField.value) nameField.value = currentUser.username;
    }
    document.getElementById('modalOverlay').classList.add('show');
    document.getElementById('checkoutModal').classList.add('show');
  }

  function closeCheckout() {
    document.getElementById('modalOverlay').classList.remove('show');
    document.getElementById('checkoutModal').classList.remove('show');
  }

  function submitOrder(e) {
    e.preventDefault();
    if (!validateForm()) return;

    for (var i = 0; i < cartData.length; i++) {
      var item = cartData[i];
      if (item.quantity > getStock(item.id)) {
        showToast('库存不足，订单无法提交'); return;
      }
    }

    lastOrderSnap = cartData.map(function (item) {
      return {
        productId: item.id,
        name: item.name,
        emoji: item.emoji,
        qty: item.quantity,
        subtotal: calcItemTotal(item)
      };
    });

    for (var j = 0; j < cartData.length; j++) {
      var cj = cartData[j];
      stockData[cj.id] = (stockData[cj.id] || 0) - cj.quantity;
    }
    saveStock();

    var orderNo = 'SN' + Date.now();

    // Feature 1: Save order to history
    var order = {
      id: orderNo,
      date: new Date().toISOString(),
      items: lastOrderSnap,
      total: cartTotal(),
      customerName: currentUser ? currentUser.username : 'Guest',
      status: 'received',
      statusHistory: [{ status: 'received', timestamp: new Date().toISOString() }]
    };
    var existingOrders = getOrders();
    existingOrders.push(order);
    saveOrders(existingOrders);
    renderFavorites();

    // Broadcast new order
    if (bc) {
      try { bc.postMessage({ type: 'orderNew', orderId: orderNo }); } catch (e) { }
    }

    cartData = [];
    saveCart();

    closeCheckout();
    updateBadge();
    updateBottomBar();
    renderProducts();

    document.getElementById('orderNum').textContent = '订单编号：' + orderNo;
    var html = '';
    for (var k = 0; k < lastOrderSnap.length; k++) {
      var s = lastOrderSnap[k];
      html += s.emoji + ' ' + escapeHtml(s.name) + ' × ' + s.qty + ' = ¥' + s.subtotal.toFixed(2) + '<br>';
    }
    document.getElementById('orderItems').innerHTML = html;
    document.getElementById('successOverlay').classList.add('show');
    document.getElementById('successModal').classList.add('show');
  }

  function closeSuccess() {
    document.getElementById('successOverlay').classList.remove('show');
    document.getElementById('successModal').classList.remove('show');
    lastOrderSnap = [];
  }

  // ===== Feature 3: 员工面板 =====
  function isStaff() {
    if (!currentUser) return false;
    var staffList = localStorage.getItem(LS_STAFF) || '';
    var names = staffList.split(',').map(function (s) { return s.trim(); });
    return names.indexOf(currentUser.username) >= 0;
  }

  function initBroadcast() {
    try {
      bc = new BroadcastChannel('snack_shop');
      bc.onmessage = function (e) {
        if (e.data && e.data.type === 'orderStatusUpdate' && staffMode) {
          renderStaffOrders();
        }
        if (e.data && e.data.type === 'orderNew' && staffMode) {
          renderStaffOrders();
          playNotificationSound();
        }
      };
    } catch (e) {
      bc = null;
    }
  }

  function toggleStaffMode() {
    if (!currentUser || !isStaff()) { showToast('无权限'); return; }

    staffMode = !staffMode;
    var grid = document.getElementById('productGrid');
    var dash = document.getElementById('staffDashboard');
    var searchBar = document.querySelector('.search-filter-bar');
    var favSection = document.getElementById('favoritesSection');
    var staffBtn = document.getElementById('staffToggle');

    if (staffMode) {
      grid.style.display = 'none';
      dash.style.display = 'block';
      if (favSection) favSection.style.display = 'none';
      searchBar.style.display = 'none';
      staffBtn.classList.add('active');
      staffBtn.textContent = '✕ 退出管理';
      renderStaffOrders();
    } else {
      grid.style.display = '';
      dash.style.display = 'none';
      if (favSection) favSection.style.display = currentUser && getFavorites().length > 0 ? '' : 'none';
      searchBar.style.display = '';
      staffBtn.classList.remove('active');
      staffBtn.textContent = '👤 管理';
    }
  }

  function switchStaffTab(tab) {
    document.querySelectorAll('.staff-tab').forEach(function (t) {
      t.classList.toggle('active', t.dataset.tab === tab);
    });
    document.getElementById('staffOrdersPanel').style.display = tab === 'orders' ? '' : 'none';
    document.getElementById('staffStockPanel').style.display = tab === 'stock' ? '' : 'none';
    document.getElementById('staffSpecialsPanel').style.display = tab === 'specials' ? '' : 'none';
    if (tab === 'orders') renderStaffOrders();
    if (tab === 'stock') renderStockPanel();
    if (tab === 'specials') renderSpecialsPanel();
  }

  function renderStaffOrders() {
    var container = document.getElementById('staffOrderList');
    var allOrders = getOrders();

    var filtered = [];
    for (var i = 0; i < allOrders.length; i++) {
      if (staffOrderFilter === 'all' || allOrders[i].status === staffOrderFilter) {
        filtered.push(allOrders[i]);
      }
    }

    filtered.sort(function (a, b) { return new Date(b.date) - new Date(a.date); });

    if (filtered.length === 0) {
      container.innerHTML = '<div class="staff-orders-empty">' +
        (staffOrderFilter !== 'all' ? '没有此状态的订单' : '暂无订单，等待新订单...') + '</div>';
      return;
    }

    var html = '';
    for (var i = 0; i < filtered.length; i++) {
      var o = filtered[i];
      var d = new Date(o.date);
      var timeStr = pad(d.getHours()) + ':' + pad(d.getMinutes());
      var statusMap = { received: '已接收', preparing: '准备中', ready: '已完成' };
      var statusLabel = statusMap[o.status] || o.status;

      var nextStatus = null;
      var nextLabel = null;
      if (o.status === 'received') { nextStatus = 'preparing'; nextLabel = '准备中'; }
      else if (o.status === 'preparing') { nextStatus = 'ready'; nextLabel = '已完成'; }

      var itemNames = [];
      for (var j = 0; j < o.items.length; j++) {
        itemNames.push(o.items[j].emoji + o.items[j].name + '×' + o.items[j].qty);
      }

      html += '<div class="staff-order-card">';
      html += '<div class="staff-order-header">';
      html += '<div><span class="staff-order-number">' + o.id + '</span> <span class="staff-order-customer">' + escapeHtml(o.customerName || 'Guest') + '</span></div>';
      html += '<span class="staff-order-time">' + timeStr + '</span>';
      html += '</div>';
      html += '<div class="staff-order-items">' + itemNames.join(', ') + '</div>';
      html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;">';
      html += '<span class="staff-order-status-btn ' + o.status + '">' + statusLabel + '</span>';
      if (nextStatus) {
        html += '<button class="staff-order-status-btn ' + nextStatus + '" onclick="window._snack.advanceOrderStatus(\'' + o.id + '\')">→ 标记为' + nextLabel + '</button>';
      }
      html += '</div>';
      html += '</div>';
    }

    container.innerHTML = html;
  }

  function filterOrders(status) {
    staffOrderFilter = status;
    document.querySelectorAll('.order-filter-tab').forEach(function (tab) {
      tab.classList.toggle('active', tab.dataset.status === status);
    });
    renderStaffOrders();
  }

  function advanceOrderStatus(orderId) {
    var orders = getOrders();
    for (var i = 0; i < orders.length; i++) {
      if (orders[i].id === orderId) {
        var nextStatus = null;
        if (orders[i].status === 'received') nextStatus = 'preparing';
        else if (orders[i].status === 'preparing') nextStatus = 'ready';

        if (nextStatus) {
          orders[i].status = nextStatus;
          if (!orders[i].statusHistory) orders[i].statusHistory = [];
          orders[i].statusHistory.push({ status: nextStatus, timestamp: new Date().toISOString() });
          saveOrders(orders);

          if (bc) {
            try { bc.postMessage({ type: 'orderStatusUpdate', orderId: orderId, status: nextStatus }); } catch (e) { }
          }

          renderStaffOrders();
          var labelMap = { preparing: '准备中', ready: '已完成' };
          showToast('订单 ' + orderId + ' 已更新为 ' + labelMap[nextStatus]);
        }
        return;
      }
    }
  }

  function updateStaffToggle() {
    var btn = document.getElementById('staffToggle');
    if (btn) {
      btn.style.display = isStaff() ? 'inline-flex' : 'none';
    }
  }

  function playNotificationSound() {
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 800;
      osc.type = 'sine';
      gain.gain.value = 0.12;
      osc.start();
      osc.stop(ctx.currentTime + 0.12);
    } catch (e) { }
  }

  // ===== 表单验证 =====
  function validateForm() {
    var valid = true;
    clearErrors();

    var name = document.getElementById('fName').value.trim();
    var phone = document.getElementById('fPhone').value.trim();
    var address = document.getElementById('fAddress').value.trim();

    if (!name) { showErr('fName', 'errName', '请输入收货人姓名'); valid = false; }
    if (!phone) { showErr('fPhone', 'errPhone', '请输入手机号'); valid = false; } else if (!/^1[3-9]\d{9}$/.test(phone)) { showErr('fPhone', 'errPhone', '手机号格式不正确'); valid = false; }
    if (!address) { showErr('fAddress', 'errAddress', '请输入收货地址'); valid = false; } else if (address.length < 5) { showErr('fAddress', 'errAddress', '地址太短，请填写完整'); valid = false; }

    return valid;
  }

  function showErr(inpId, errId, msg) {
    document.getElementById(inpId).classList.add('error');
    document.getElementById(errId).textContent = msg;
  }

  function clearErrors() {
    ['fName', 'fPhone', 'fAddress'].forEach(function (id) { document.getElementById(id).classList.remove('error'); });
    ['errName', 'errPhone', 'errAddress'].forEach(function (id) { document.getElementById(id).textContent = ''; });
  }

  // ===== Toast =====
  function showToast(msg) {
    var old = document.getElementById('toast');
    if (old) old.remove();
    var t = document.createElement('div');
    t.id = 'toast';
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:rgba(255,105,180,0.92);color:#fff;padding:10px 24px;border-radius:20px;font-size:0.88rem;z-index:9999;white-space:nowrap;box-shadow:0 4px 16px rgba(255,105,180,0.3);';
    document.body.appendChild(t);
    setTimeout(function () {
      t.style.transition = 'opacity 0.3s'; t.style.opacity = '0';
      setTimeout(function () { t.remove(); }, 300);
    }, 1800);
  }

  // ===== 用户认证 =====
  function authInit() {
    loadSession();
    updateAuthUI();
  }

  function loadSession() {
    var saved = localStorage.getItem(LS_SESSION);
    if (!saved) return;
    try {
      var data = JSON.parse(saved);
      if (!data || !data.username) return;
      var users = JSON.parse(localStorage.getItem(LS_USERS) || '[]');
      for (var i = 0; i < users.length; i++) {
        if (users[i].username === data.username) {
          currentUser = users[i];
          return;
        }
      }
    } catch (e) { }
  }

  function register(username, password) {
    if (!username || username.length < 2) { showToast('用户名至少需要 2 个字符'); return false; }
    if (!password || password.length < 6) { showToast('密码至少需要 6 个字符'); return false; }

    var users = JSON.parse(localStorage.getItem(LS_USERS) || '[]');
    for (var i = 0; i < users.length; i++) {
      if (users[i].username === username) { showToast('用户名已存在'); return false; }
    }

    users.push({
      username: username,
      password: btoa(password),
      createdAt: Date.now()
    });
    localStorage.setItem(LS_USERS, JSON.stringify(users));
    return true;
  }

  function login(username, password) {
    if (!username || !password) { showToast('请输入用户名和密码'); return false; }

    var users = JSON.parse(localStorage.getItem(LS_USERS) || '[]');
    var encoded = btoa(password);
    for (var i = 0; i < users.length; i++) {
      if (users[i].username === username && users[i].password === encoded) {
        currentUser = users[i];
        localStorage.setItem(LS_SESSION, JSON.stringify({ username: username }));
        updateAuthUI();
        renderFavorites();
        renderProducts();
        showToast('登录成功，欢迎 ' + username + '！');
        return true;
      }
    }

    showToast('用户名或密码错误');
    return false;
  }

  function logout() {
    if (staffMode) {
      staffMode = false;
      var dash = document.getElementById('staffDashboard');
      var grid = document.getElementById('productGrid');
      if (dash) dash.style.display = 'none';
      if (grid) grid.style.display = '';
      var staffBtn = document.getElementById('staffToggle');
      if (staffBtn) {
        staffBtn.classList.remove('active');
        staffBtn.textContent = '👤 管理';
      }
    }
    currentUser = null;
    localStorage.removeItem(LS_SESSION);
    updateAuthUI();
    renderFavorites();
    renderProducts();
    showToast('已退出登录');
  }

  function isLoggedIn() {
    return currentUser !== null;
  }

  function getCurrentUser() {
    return currentUser;
  }

  function updateAuthUI() {
    var container = document.getElementById('authContainer');
    if (!container) return;

    if (currentUser) {
      container.innerHTML =
        '<span class="user-greeting">你好，' + escapeHtml(currentUser.username) + '</span>' +
        '<button class="auth-btn" onclick="window._snack.logout()">退出</button>';
    } else {
      container.innerHTML =
        '<button class="auth-btn" onclick="window._snack.openLogin()">登录</button>' +
        '<button class="auth-btn auth-btn-register" onclick="window._snack.openRegister()">注册</button>';
    }
    updateStaffToggle();
  }

  // ===== Auth Modals =====
  function openLogin() {
    document.getElementById('loginOverlay').classList.add('show');
    document.getElementById('loginModal').classList.add('show');
    setTimeout(function () { document.getElementById('loginUsername').focus(); }, 100);
  }

  function closeLogin() {
    document.getElementById('loginOverlay').classList.remove('show');
    document.getElementById('loginModal').classList.remove('show');
    var form = document.getElementById('loginForm');
    if (form) form.reset();
  }

  function submitLogin(e) {
    e.preventDefault();
    var username = document.getElementById('loginUsername').value.trim();
    var password = document.getElementById('loginPassword').value;
    if (!username) { showToast('请输入用户名'); return; }
    if (!password) { showToast('请输入密码'); return; }
    if (login(username, password)) closeLogin();
  }

  function openRegister() {
    document.getElementById('registerOverlay').classList.add('show');
    document.getElementById('registerModal').classList.add('show');
    setTimeout(function () { document.getElementById('regUsername').focus(); }, 100);
  }

  function closeRegister() {
    document.getElementById('registerOverlay').classList.remove('show');
    document.getElementById('registerModal').classList.remove('show');
    var form = document.getElementById('registerForm');
    if (form) form.reset();
  }

  function submitRegister(e) {
    e.preventDefault();
    var username = document.getElementById('regUsername').value.trim();
    var password = document.getElementById('regPassword').value;
    var confirmPwd = document.getElementById('regConfirmPassword').value;

    if (!username || username.length < 2) { showToast('用户名至少需要 2 个字符'); return; }
    if (!password || password.length < 6) { showToast('密码至少需要 6 个字符'); return; }
    if (password !== confirmPwd) { showToast('两次密码输入不一致'); return; }

    if (register(username, password)) {
      closeRegister();
      showToast('注册成功，请登录');
    }
  }

  function escapeHtml(str) {
    if (typeof str !== 'string') return String(str || '');
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  // ===== 辅助 =====
  function getProduct(id) {
    for (var i = 0; i < PRODUCTS.length; i++) { if (PRODUCTS[i].id === id) return PRODUCTS[i]; }
    return null;
  }

  function pad(n) { return n < 10 ? '0' + n : String(n); }

  // ===== 暴露到 window =====
  window._snack = {
    // Core
    search: search,
    filterCat: filterCat,
    setSort: setSort,
    addToCart: addToCart,
    updateQuantity: updateQuantity,
    removeItem: removeItem,
    clearCart: clearCart,
    toggleCart: toggleCart,
    openCheckout: openCheckout,
    closeCheckout: closeCheckout,
    submitOrder: submitOrder,
    closeSuccess: closeSuccess,
    // Auth
    openLogin: openLogin,
    closeLogin: closeLogin,
    submitLogin: submitLogin,
    openRegister: openRegister,
    closeRegister: closeRegister,
    submitRegister: submitRegister,
    logout: logout,
    isLoggedIn: isLoggedIn,
    getCurrentUser: getCurrentUser,
    // Feature 1: Orders
    openOrders: openOrders,
    closeOrders: closeOrders,
    reorder: reorder,
    // Feature 2: Favorites
    toggleFavorite: toggleFavorite,
    toggleFavSection: toggleFavSection,
    // Feature 4: Modifiers
    openModifier: openModifier,
    closeModifier: closeModifier,
    toggleModOption: toggleModOption,
    confirmModifier: confirmModifier,
    // Feature 3: Staff
    toggleStaffMode: toggleStaffMode,
    switchStaffTab: switchStaffTab,
    filterOrders: filterOrders,
    advanceOrderStatus: advanceOrderStatus,
    // Feature 7: Stock
    restock: restock,
    renderStockPanel: renderStockPanel,
    // Feature 6: Specials
    closePromo: closePromo,
    addSpecialItem: addSpecialItem,
    removeSpecial: removeSpecial
  };

  init();

})();
