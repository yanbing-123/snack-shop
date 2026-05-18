# Snack Shop — New Feature Requirements

**Date:** 2026-05-18
**Context:** Pure frontend app (HTML/CSS/JS, localStorage). No backend — all features must work client-side only.
**Existing features:** 12-product catalog, 6-category filtering, search, cart drawer, checkout with form validation, user auth (register/login/logout), stock management with oversell protection.

---

## Feature 1: Order History & Reorder — P1

**Impact:** High — solves the "I want to order the same thing again" problem for repeat customers.
**Effort:** Low (~1 day)

### Requirements
- After order submission, persist completed orders to localStorage (`snack_orders` key)
- New "Order History" page/section showing past orders (date, items, total, status)
- Order cards show: date, item count, total price, status badge (Completed)
- "Reorder" button on each order — re-adds all items to current cart (respecting current stock limits)
- Empty state: "No orders yet, start shopping!"

### Data model
```js
{
  id: "SN{timestamp}",
  date: ISO string,
  items: [{ name, emoji, qty, subtotal }],
  total: number,
  status: "completed"
}
```

### UI changes
- Add "📋 Orders" nav button in header (next to cart)
- New orders list view (modal or inline page)
- Reorder confirmation toast

---

## Feature 2: Favorites / Quick Reorder — P1

**Impact:** High — one-tap repeat for regulars, reduces browse friction.
**Effort:** Low (~0.5 day)

### Requirements
- "★ Favorite" toggle button on each cart item
- Favorites stored per user in localStorage (`snack_favorites_{username}`)
- New "⭐ Favorites" quick-access section in header / home screen
- Favorite display: item emoji + name + price + "Add to Cart" button
- Persist across sessions (tied to logged-in user)

### Data model
```js
// Per user:
{ username: "xxx", items: [{ id: 1, name: "可乐", emoji: "🥤" }] }
```

### UI changes
- Star icon toggle on cart drawer items
- Favorites section on home page (above product grid, collapsible)
- Empty state: "Save your favorite items for quick ordering!"

---

## Feature 3: Staff Dashboard — Order Queue — P2

**Impact:** High for operations — turns the customer app into a complete shop system.
**Effort:** Medium (~1.5 days)

### Requirements
- New `/staff` view accessible from a toggle in the header (visible only when logged in as a staff user)
- Staff users: designate accounts via `snack_staff` localStorage key (simple comma-separated usernames or flag in user data)
- Live order queue showing all submitted orders, sorted by time (newest first)
- Order cards display: order number, items, customer name, timestamp, status
- Status transitions: Received → Preparing → Ready (tap to advance)
- Use `BroadcastChannel` API for cross-tab sync — when a staff tab marks an order Ready, the customer tab sees the update
- Filter by status tabs: All / Received / Preparing / Ready

### Data model
```js
// Enhance existing order with:
{
  customerName: string,
  status: "received" | "preparing" | "ready",
  statusHistory: [{ status, timestamp }]
}
```

### UI changes
- Staff toggle in header (small, inconspicuous)
- Full-screen staff dashboard replacing product grid
- Large, high-contrast buttons for status transitions (usable in noisy environment)
- Sound cue on new order (Web Audio API beep)

---

## Feature 4: Item Customization / Modifiers — P2

**Impact:** Medium-high — lets shops differentiate with customizable items.
**Effort:** Medium (~2 days)

### Requirements
- Modifier groups defined per item in product data (e.g., "Size: Small/Medium/Large", "Add-ons: Extra cheese +¥3")
- Each modifier group has options, each option can have a price delta
- Modifier selection appears in a small panel on the product card (expandable) or a quick-select modal
- Selected modifiers display in the cart drawer item line
- Quantity updates retain modifier selections
- Validate modifier limits (e.g., "Max 2 toppings")

### Data model
```js
// Extend product data:
{
  ...existing,
  modifiers: [
    {
      group: "Size",
      type: "single",  // radio
      options: [
        { label: "Small", priceDelta: 0 },
        { label: "Medium", priceDelta: 2.00 },
        { label: "Large", priceDelta: 4.00 }
      ]
    },
    {
      group: "Add-ons",
      type: "multiple", // checkbox
      max: 2,
      options: [
        { label: "Extra chocolate", priceDelta: 3.00 }
      ]
    }
  ]
}

// Extend cart item:
{
  ...existing,
  modifiers: [{ group: "Size", selection: "Large", delta: 4.00 }]
}
```

### UI changes
- "Customize" button on product card (replaces or augments "Add to Cart")
- Modifier picker modal/panel — radios for single-select, checkboxes for multi
- Real-time price update as modifiers change
- Modifiers summary in cart drawer item

---

## Feature 5: Product Sorting — P2

**Impact:** Medium — improves browse UX, low effort to implement.
**Effort:** Low (~0.3 day)

### Requirements
- Sort dropdown/buttons near search bar: Default | Price ↑ | Price ↓ | Name A–Z
- Default sort mirrors original order (by product ID)
- Sorting applies on top of the current category filter and search query
- Active sort indicator visible

### UI changes
- Sort button group or select in the search-filter bar
- Active sort highlighted

---

## Feature 6: Daily Specials & Promotions — P2

**Impact:** Medium — drives sales and discovery without a backend.
**Effort:** Low-medium (~1 day)

### Requirements
- Specials stored in localStorage (`snack_specials` key) — allows manager/staff to set from the staff panel
- Special = list of product IDs + optional discount percentage or fixed price
- Specials banner at top of home screen (auto-dismissible)
- Specials badge on product cards (e.g., "🔥 20% OFF" tag)
- Staff can toggle/manage specials from the staff dashboard
- Auto-expire: specials can have an end date (ISO string or null for permanent)

### Data model
```js
{
  items: [{ productId: 1, type: "percent", value: 20 }],
  label: "Lunch Special",
  endDate: "2026-05-25" // or null
}
```

### UI changes
- Promo banner below header on home page
- "SALE" tag overlay on product cards with special pricing
- Specials editor in staff dashboard (simple form)

---

## Feature 7: Stock Management Panel (Staff/Manager) — P2

**Impact:** Medium — gives staff control over inventory directly in the app.
**Effort:** Medium (~1 day)

### Requirements
- Stock overview table showing all 12 products: name, current stock, status (normal/low/out)
- "Restock" button per item with pre-set amounts (e.g., +10, +50, +100) or custom input
- Low-stock threshold configuration (default: < 20 items = low) stored in localStorage
- Color-coded status indicators: green (normal), yellow (low), red (out of stock)
- Stock adjustment history log (last 20 actions) for audit

### UI changes
- Stock management tab in staff dashboard
- Stock overview table with inline restock controls
- Status badges with color coding

---

## Summary

| # | Feature | Priority | Impact | Effort | Dependencies |
|---|---------|----------|--------|--------|-------------|
| 1 | Order History & Reorder | P1 | High | Low | None |
| 2 | Favorites / Quick Reorder | P1 | High | Low | User auth (exists) |
| 3 | Staff Dashboard — Order Queue | P2 | High | Medium | Order history (#1) |
| 4 | Item Customization | P2 | Medium | Medium | None |
| 5 | Product Sorting | P2 | Medium | Low | None |
| 6 | Daily Specials & Promotions | P2 | Medium | Low-Medium | Stock management (#7) |
| 7 | Stock Management Panel | P2 | Medium | Medium | Staff auth (#3) |

**Recommended order of implementation:** 1 → 2 → 5 → 3 → 7 → 6 → 4
(Fastest wins first, building up to staff tools and customization.)
