(function() {
  'use strict';

  // ===== 商品数据 =====
  var PRODUCTS = [
    { id: 1,  name: '草莓奶糖',   emoji: '🍬', category: '糖果',     price: 5.00,  stock: 200 },
    { id: 2,  name: '橘子软糖',   emoji: '🍬', category: '糖果',     price: 6.00,  stock: 150 },
    { id: 3,  name: '黄油曲奇',   emoji: '🍪', category: '饼干',     price: 12.00, stock: 100 },
    { id: 4,  name: '苏打饼干',   emoji: '🍪', category: '饼干',     price: 8.00,  stock: 120 },
    { id: 5,  name: '开心果',     emoji: '🥜', category: '坚果',     price: 25.00, stock: 80  },
    { id: 6,  name: '混合坚果',   emoji: '🥜', category: '坚果',     price: 35.00, stock: 60  },
    { id: 7,  name: '牛奶巧克力', emoji: '🍫', category: '巧克力',  price: 15.00, stock: 90  },
    { id: 8,  name: '黑巧克块',  emoji: '🍫', category: '巧克力',  price: 18.00, stock: 70  },
    { id: 9,  name: '可乐',      emoji: '🥤', category: '饮料',     price: 4.00,  stock: 200 },
    { id: 10, name: '柠檬茶',    emoji: '🥤', category: '饮料',     price: 5.00,  stock: 180 },
    { id: 11, name: '芒果果冻',  emoji: '🍮', category: '果冻',     price: 6.00,  stock: 100 },
    { id: 12, name: '草莓布丁',  emoji: '🍮', category: '果冻',     price: 7.00,  stock: 90  },
  ];

  var LS_STOCK    = 'snack_stock';
  var LS_CART     = 'snack_cart';
  var LS_USERS    = 'snack_users';
  var LS_SESSION  = 'snack_session';

  var stockData      = {};
  var cartData      = [];
  var currentCat     = '全部';
  var currentSearch = '';
  var lastOrderSnap = [];

  var currentUser   = null; // { username, password(base64), phone, address }

  // ===== 初始化 =====
  function init() {
    loadStock();
    loadCart();
    authInit();
    renderProducts();
    updateBadge();
    updateBottomBar();
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

  // ===== 购物车 =====
  function loadCart() {
    var saved = localStorage.getItem(LS_CART);
    if (saved) cartData = JSON.parse(saved);
  }

  function saveCart() { localStorage.setItem(LS_CART, JSON.stringify(cartData)); }

  function cartIndex(id) {
    for (var i = 0; i < cartData.length; i++) { if (cartData[i].id === id) return i; }
    return -1;
  }

  function cartCount() {
    var t = 0;
    for (var i = 0; i < cartData.length; i++) t += cartData[i].quantity;
    return t;
  }

  function cartTotal() {
    var t = 0;
    for (var i = 0; i < cartData.length; i++) t += cartData[i].price * cartData[i].quantity;
    return t;
  }

  // ===== 搜索 =====
  function search() {
    currentSearch = document.getElementById('searchInput').value.trim();
    renderProducts();
  }

  // ===== 筛选分类 =====
  function filterCat(cat) {
    currentCat = cat;
    document.querySelectorAll('.tag-btn').forEach(function(btn) {
      btn.classList.toggle('active', btn.dataset.cat === cat || (cat === '全部' && btn.dataset.cat === '全部'));
    });
    renderProducts();
  }

  // ===== 渲染商品 =====
  function renderProducts() {
    var grid = document.getElementById('productGrid');
    grid.innerHTML = '';

    for (var i = 0; i < PRODUCTS.length; i++) {
      var p = PRODUCTS[i];

      if (currentCat !== '全部' && p.category !== currentCat) continue;

      if (currentSearch) {
        if (p.name.toLowerCase().indexOf(currentSearch.toLowerCase()) === -1) continue;
      }

      var stock = getStock(p.id);
      var outOfStock = stock <= 0;
      var catColor = getCatColor(p.category);

      var card = document.createElement('div');
      card.className = 'product-card' + (outOfStock ? ' out-of-stock' : '');
      card.innerHTML =
        '<div class="card-img">' + p.emoji + '</div>' +
        '<div class="card-body">' +
          '<span class="card-cat-tag" style="background:' + catColor.bg + ';color:' + catColor.text + '">' + p.category + '</span>' +
          '<div class="card-name">' + p.name + '</div>' +
          '<div class="card-price">¥' + p.price.toFixed(2) + '</div>' +
          '<div class="card-stock' + (outOfStock ? ' zero' : '') + '">' + (outOfStock ? '缺货' : '库存 ' + stock + ' 件') + '</div>' +
          '<button class="btn-add" onclick="window._snack.addToCart(' + p.id + ')"' + (outOfStock ? ' disabled' : '') + '>' +
            (outOfStock ? '缺货' : '加入购物车') +
          '</button>' +
        '</div>';
      grid.appendChild(card);
    }
  }

  function getCatColor(cat) {
    var map = {
      '糖果':    { bg: '#FFF0F5', text: '#FF69B4' },
      '饼干':    { bg: '#FFF8DC', text: '#DAA520' },
      '坚果':    { bg: '#F0FFF0', text: '#228B22' },
      '巧克力':  { bg: '#F5F5DC', text: '#8B4513' },
      '饮料':    { bg: '#E0FFFF', text: '#0077B6' },
      '果冻':    { bg: '#FFFACD', text: '#FF8C00' }
    };
    return map[cat] || { bg: '#FFF0F5', text: '#FF69B4' };
  }

  // ===== 加入购物车（第一层校验） =====
  function addToCart(id) {
    if (!isLoggedIn()) {
      showToast('请先登录后再购物');
      openLogin();
      return;
    }
    var p = getProduct(id);
    if (!p) return;

    var stock = getStock(id);
    var idx = cartIndex(id);
    var currentQty = idx >= 0 ? cartData[idx].quantity : 0;

    if (currentQty >= stock) {
      showToast(p.name + ' 已达库存上限 (' + stock + '件)');
      return;
    }

    if (idx >= 0) {
      cartData[idx].quantity++;
    } else {
      cartData.push({ id: id, name: p.name, emoji: p.emoji, price: p.price, quantity: 1 });
    }

    saveCart();
    updateBadge();
    updateBottomBar();
    renderProducts();
    showToast('已加入购物车 ✓');
  }

  // ===== 修改数量（第二层校验） =====
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

  // ===== 删除商品 =====
  function removeItem(idx) {
    cartData.splice(idx, 1);
    saveCart();
    updateDrawer();
    updateBadge();
    updateBottomBar();
    renderProducts();
  }

  // ===== 清空购物车 =====
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
      var div = document.createElement('div');
      div.className = 'drawer-item';
      div.innerHTML =
        '<span class="drawer-item-emoji">' + item.emoji + '</span>' +
        '<div class="drawer-item-info">' +
          '<div class="drawer-item-name">' + item.name + '</div>' +
          '<div class="drawer-item-price">¥' + item.price.toFixed(2) + ' × ' + item.quantity + '</div>' +
          '<div class="drawer-item-sub">¥' + (item.price * item.quantity).toFixed(2) + '</div>' +
        '</div>' +
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

  // ===== 结算（第三层校验） =====
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

    lastOrderSnap = cartData.map(function(item) {
      return {
        name: item.name, emoji: item.emoji,
        qty: item.quantity, subtotal: item.price * item.quantity
      };
    });

    for (var j = 0; j < cartData.length; j++) {
      var cj = cartData[j];
      stockData[cj.id] = (stockData[cj.id] || 0) - cj.quantity;
    }
    saveStock();

    var orderNo = 'SN' + Date.now();
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
      html += s.emoji + ' ' + s.name + ' × ' + s.qty + ' = ¥' + s.subtotal.toFixed(2) + '<br>';
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

  // ===== 表单验证 =====
  function validateForm() {
    var valid = true;
    clearErrors();

    var name = document.getElementById('fName').value.trim();
    var phone = document.getElementById('fPhone').value.trim();
    var address = document.getElementById('fAddress').value.trim();

    if (!name) { showErr('fName', 'errName', '请输入收货人姓名'); valid = false; }
    if (!phone) { showErr('fPhone', 'errPhone', '请输入手机号'); valid = false; }
    else if (!/^1[3-9]\d{9}$/.test(phone)) { showErr('fPhone', 'errPhone', '手机号格式不正确'); valid = false; }
    if (!address) { showErr('fAddress', 'errAddress', '请输入收货地址'); valid = false; }
    else if (address.length < 5) { showErr('fAddress', 'errAddress', '地址太短，请填写完整'); valid = false; }

    return valid;
  }

  function showErr(inpId, errId, msg) {
    document.getElementById(inpId).classList.add('error');
    document.getElementById(errId).textContent = msg;
  }

  function clearErrors() {
    ['fName', 'fPhone', 'fAddress'].forEach(function(id) { document.getElementById(id).classList.remove('error'); });
    ['errName', 'errPhone', 'errAddress'].forEach(function(id) { document.getElementById(id).textContent = ''; });
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
    setTimeout(function() {
      t.style.transition = 'opacity 0.3s'; t.style.opacity = '0';
      setTimeout(function() { t.remove(); }, 300);
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
    } catch(e) {}
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
        showToast('登录成功，欢迎 ' + username + '！');
        return true;
      }
    }

    showToast('用户名或密码错误');
    return false;
  }

  function logout() {
    currentUser = null;
    localStorage.removeItem(LS_SESSION);
    updateAuthUI();
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
  }

  // ===== Auth Modals =====
  function openLogin() {
    document.getElementById('loginOverlay').classList.add('show');
    document.getElementById('loginModal').classList.add('show');
    setTimeout(function() { document.getElementById('loginUsername').focus(); }, 100);
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
    setTimeout(function() { document.getElementById('regUsername').focus(); }, 100);
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
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  // ===== 辅助
  function getProduct(id) {
    for (var i = 0; i < PRODUCTS.length; i++) { if (PRODUCTS[i].id === id) return PRODUCTS[i]; }
    return null;
  }

  // ===== 暴露到 window =====
  window._snack = {
    search: search,
    filterCat: filterCat,
    addToCart: addToCart,
    updateQuantity: updateQuantity,
    removeItem: removeItem,
    clearCart: clearCart,
    toggleCart: toggleCart,
    openCheckout: openCheckout,
    closeCheckout: closeCheckout,
    submitOrder: submitOrder,
    closeSuccess: closeSuccess,
    openLogin: openLogin,
    closeLogin: closeLogin,
    submitLogin: submitLogin,
    openRegister: openRegister,
    closeRegister: closeRegister,
    submitRegister: submitRegister,
    logout: logout,
    isLoggedIn: isLoggedIn,
    getCurrentUser: getCurrentUser
  };

  init();

})();