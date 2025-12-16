const API_URL = "http://localhost:8000";

const app = {
    state: {
        token: null,
        user: null,
        cart: [],
        products: [],
        currentUpsell: null
    },

    // --- Views Configuration ---
    views: {
        '#sale': {
            title: 'New Sale',
            render: () => {
                // Return generic POS HTML
                return `
                <div class="pos-layout">
                    <!-- Left: Main Content (Search + Grid) -->
                    <div class="flex-col h-full" style="padding-bottom: 20px;">
                        <!-- Top Bar / Filter -->
                        <div class="card" style="margin-bottom: 20px; padding: 15px;">
                            <div class="flex" style="gap: 15px;">
                                <input type="text" id="search" class="flex-1" style="margin-bottom: 0;" placeholder="Search products..." onkeyup="app.filterProducts()">
                                <button onclick="app.loadProducts()" style="width: auto;">↻</button>
                            </div>
                            <!-- Quick Access / Categories (New Requirement) -->
                            <div class="flex" style="margin-top: 10px; overflow-x: auto; padding-bottom: 5px;">
                                <button class="secondary" style="width: auto; white-space: nowrap;" onclick="app.filterCategory('all')">All</button>
                                <button class="secondary" style="width: auto; white-space: nowrap;" onclick="app.filterCategory('Beverage')">Beverages</button>
                                <button class="secondary" style="width: auto; white-space: nowrap;" onclick="app.filterCategory('Snack')">Snacks</button>
                                <button class="secondary" style="width: auto; white-space: nowrap;" onclick="app.filterCategory('Produce')">Produce</button>
                                <button class="secondary" style="width: auto; white-space: nowrap;" onclick="app.filterCategory('Bakery')">Bakery</button>
                            </div>
                        </div>

                        <!-- Product Grid (Scrollable Area) -->
                        <div class="flex-1 scroll-y">
                            <div id="product-list" class="product-grid"></div>
                        </div>
                    </div>

                    <!--Right: Transaction Cart(Full Height)-- >
                    <div class="flex-col h-full">
                        <div class="card flex-col h-full" style="padding: 0; overflow: hidden;">
                            <!-- Customer Header -->
                            <div style="padding: 15px; border-bottom: 1px solid #eee; background: #f9f9fa;">
                                <select id="customer-select" onchange="app.updateCustomerMetrics()" style="margin-bottom: 5px;">
                                    <option value="">Guest Customer</option>
                                    <option value="1">John Doe (VIP)</option>
                                    <option value="2">Jane Smith</option>
                                </select>
                                <div id="customer-stats" class="customer-metrics" style="display: none; margin-top: 0;">
                                    <span>Points: <b id="cust-points">0</b></span>
                                    <span>Visit: <b id="last-visit">N/A</b></span>
                                </div>
                            </div>

                            <!-- Cart Items (Scrollable middle) -->
                            <div id="cart-items" class="flex-1 scroll-y" style="padding: 10px;">
                                <p class="text-sm" style="text-align: center; margin-top: 50px;">Cart is empty</p>
                            </div>

                            <!-- Cart Footer (Totals & Action) -->
                            <div style="padding: 20px; background: #fff; border-top: 1px solid #eee; box-shadow: 0 -4px 12px rgba(0,0,0,0.05);">
                                <div class="flex" style="justify-content: space-between; font-weight: bold; font-size: 24px; margin-bottom: 15px;">
                                    <span>Total</span>
                                    <span id="cart-total">$0.00</span>
                                </div>
                                <div class="grid col-2" style="grid-template-columns: 1fr 2fr; gap: 10px;">
                                    <button class="secondary" onclick="app.checkUpsell()">Offers</button>
                                    <button class="success" onclick="app.openPaymentModal()" style="font-size: 18px;">PAY</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>`;
            },
            postRender: () => {
                // Re-bind events or load specific data
                app.loadProducts();
                app.renderCart();
            }
        },
        '#reports': {
            title: 'Analytics Dashboard',
            render: () => `
                <div class="dashboard-grid">
                    <!-- Row 1: KPIs -->
                    <div class="kpi-row">
                        <div class="kpi-card">
                            <div class="kpi-title">Total Revenue</div>
                            <div class="kpi-value" id="kpi-revenue">--</div>
                            <div class="kpi-trend">Today</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-title">Transactions</div>
                            <div class="kpi-value" id="kpi-tx">--</div>
                            <div class="kpi-trend">Today</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-title">Avg. Ticket</div>
                            <div class="kpi-value" id="kpi-avg">--</div>
                            <div class="kpi-trend">Today</div>
                        </div>
                    </div>

                    <!-- Row 2: Main Chart -->
                    <div class="chart-container-main">
                        <div class="flex" style="justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <div class="section-title">Sales Trend</div>
                            <select id="trend-range" onchange="app.loadDashboard()" style="padding: 5px; border-radius: 6px; border: 1px solid #ddd;">
                                <option value="7">Last 7 Days</option>
                                <option value="30" selected>Last 30 Days</option>
                            </select>
                        </div>
                        <div style="flex: 1; position: relative; min-height: 0;">
                            <canvas id="chart-trend"></canvas>
                        </div>
                    </div>

                    <!-- Row 3: Sub Charts Grid (Products, Categories, Locations, Recent) -->
                    <div class="sub-charts-row" style="grid-template-columns: 1fr 1fr 1fr 1fr;"> 
                        <!-- Top Products -->
                        <div class="chart-container-sub">
                            <div class="section-title">Top Products</div>
                            <div style="height: 200px; position: relative;">
                                <canvas id="chart-products"></canvas>
                            </div>
                        </div>
                        
                        <!-- Categories -->
                         <div class="chart-container-sub">
                            <div class="section-title">By Category</div>
                            <div style="height: 200px; position: relative;">
                                <canvas id="chart-cats"></canvas>
                            </div>
                        </div>

                        <!-- Locations -->
                         <div class="chart-container-sub">
                            <div class="section-title">Revenue by Shop</div>
                            <div style="height: 200px; position: relative;">
                                <canvas id="chart-locs"></canvas>
                            </div>
                        </div>

                        <!-- Recent -->
                        <div class="chart-container-sub">
                            <div class="section-title">Recent Activity</div>
                             <div style="overflow-y: auto; max-height: 200px;">
                                 <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                                    <tbody id="dashboard-recent-tx">
                                        <tr><td>Loading...</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            postRender: () => {
                app.loadDashboard();
            }
        },
        '#stock': {
            title: 'Stock Management',
            render: () => `
                <div class="card">
                    <h2>Inventory Levels</h2>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <tr style="text-align: left; border-bottom: 1px solid #ddd;">
                            <th>Product</th><th>Category</th><th style="text-align: right;">Stock</th>
                        </tr>
                        <tr><td>Water</td><td>Beverage</td><td style="text-align: right;">150</td></tr>
                        <tr><td>Soda</td><td>Beverage</td><td style="text-align: right;">45</td></tr>
                        <tr><td>Premium Soda</td><td>Beverage</td><td style="text-align: right;">12</td></tr>
                    </table>
                </div>
    `
        },
        '#admin': {
            title: 'Admin Panel',
            render: () => `
                <div class="grid col-2">
                    <div class="card">
                        <h3>User Management</h3>
                        <button class="secondary mt-2">Create User</button>
                    </div>
                    <div class="card">
                        <h3>Store Setup</h3>
                        <button class="secondary mt-2">Provision Store</button>
                    </div>
                </div>
    `
        }
    },

    init: () => {
        const token = localStorage.getItem('pos_token');
        const user = JSON.parse(localStorage.getItem('pos_user'));

        if (token && user) {
            app.state.token = token;
            app.state.user = user;
            app.showScreen('pos-screen');
            app.setupUI();

            // Router Init
            window.addEventListener('hashchange', app.handleRoute);

            // Initial Route
            if (!window.location.hash) window.location.hash = '#sale';
            else app.handleRoute();

        }
    },

    handleRoute: async () => {
        const hash = window.location.hash || '#sale';
        const view = app.views[hash];
        const container = document.getElementById('view-container');

        if (!view) {
            window.location.hash = '#sale';
            return;
        }

        // 1. Show Loader / Fade Out
        container.classList.remove('active');
        container.innerHTML = '<div class="loader-container"><div class="loader"></div></div>'; // Spinner

        // 2. Simulate Latency (UX Requirement) + Fade In
        setTimeout(() => {
            container.innerHTML = view.render();
            if (view.postRender) view.postRender();

            // Update Active Link
            document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
            const activeLink = document.querySelector(`a[href = "${hash}"]`);
            if (activeLink) activeLink.classList.add('active');

            // Fade In
            requestAnimationFrame(() => {
                container.classList.add('active');
            });

        }, 300);
    },

    login: async () => {
        const u = document.getElementById('username').value.trim();
        const p = document.getElementById('password').value.trim();
        if (!u || !p) { alert("Please enter username and password"); return; }

        try {
            const formData = new FormData();
            formData.append('username', u);
            formData.append('password', p);
            const res = await fetch(`${API_URL}/token`, { method: 'POST', body: formData });
            if (res.ok) {
                const data = await res.json();
                let role = 'internal_cashier';
                if (u === 'super_admin_user' || u === 'api_admin') role = 'super_admin';
                app.state.user = { username: u, role: role };
                app.state.token = data.access_token;
                localStorage.setItem('pos_token', data.access_token);
                localStorage.setItem('pos_user', JSON.stringify(app.state.user));
                app.showScreen('pos-screen');
                app.setupUI();
                window.location.hash = '#sale';
                app.handleRoute();
            } else { alert('Login failed'); }
        } catch (e) { console.error(e); alert('Error connecting to Server'); }
    },

    logout: () => {
        app.state.token = null;
        app.state.user = null;
        localStorage.removeItem('pos_token');
        localStorage.removeItem('pos_user');
        window.location.hash = ''; // Clear hash
        document.getElementById('pos-screen').style.display = 'none';
        document.getElementById('login-screen').classList.add('visible');
    },

    showScreen: (id) => {
        document.querySelectorAll('.container').forEach(el => el.classList.remove('visible'));
        if (id === 'pos-screen') document.getElementById(id).style.display = 'flex';
        else document.getElementById(id).classList.add('visible');
    },

    setupUI: () => {
        const u = app.state.user;
        document.getElementById('user-display').innerText = u.username;
        document.getElementById('user-role').innerText = u.role.replace('_', ' ').toUpperCase();
        app.renderSidebar(u.role);
    },

    renderSidebar: (role) => {
        const menu = document.getElementById('rbac-menu');
        let links = [{ name: 'POS / New Sale', hash: '#sale' }];

        if (['branch_manager', 'super_admin', 'partner_owner'].includes(role)) {
            links.push({ name: 'Sales Reports', hash: '#reports' });
            links.push({ name: 'Stock Levels', hash: '#stock' });
        }

        if (role === 'super_admin') {
            links.push({ name: '---' });
            links.push({ name: 'Admin Panel', hash: '#admin' });
        }

        links.push({ name: '---' });
        links.push({ name: 'System v4.0 (Fixes Active)', hash: '#', style: 'color: #999; font-size: 11px; pointer-events: none;' });

        menu.innerHTML = links.map(l => {
            if (l.name === '---') return '<hr style="margin: 10px 0; border: 0; border-top: 1px solid #ddd;">';
            if (l.style) return `<a href="${l.hash}" class="nav-link" style="${l.style}">${l.name}</a>`;
            return `<a href="${l.hash}" class="nav-link">${l.name}</a>`;
        }).join('');
    },

    toggleSidebar: () => {
        document.getElementById('sidebar-nav').classList.toggle('collapsed');
        document.querySelector('.main-content').classList.toggle('expanded');
    },

    // --- POS Logic ---
    loadProducts: () => {
        // Mock
        app.state.products = [
            { id: 1, name: "Water", price: 1.00, category: "Beverage", stock: 150 },
            { id: 2, name: "Soda", price: 2.00, category: "Beverage", stock: 45 },
            { id: 3, name: "Premium Soda", price: 5.00, category: "Beverage", stock: 12 },
            { id: 4, name: "Chips", price: 1.50, category: "Snack", stock: 88 }
        ];
        app.renderProducts();
        document.getElementById('store-name').innerText = "Proprietary Store #1";
    },

    renderProducts: () => {
        const grid = document.getElementById('product-list');
        if (!grid) return; // Guard for view switching
        grid.innerHTML = app.state.products.map(p => `
            <div class="card product-item" onclick="app.addToCart(${p.id})">
                <div class="stock-tooltip">${p.stock} in stock</div>
                <h3>${p.name}</h3>
                <div class="text-sm">${p.category}</div>
                <div style="font-weight: bold; margin-top: 5px;">$${p.price.toFixed(2)}</div>
            </div>
        `).join('');
    },

    filterProducts: () => {
        const term = document.getElementById('search').value.toLowerCase();
        const filtered = app.state.products.filter(p => p.name.toLowerCase().includes(term));
        const grid = document.getElementById('product-list');
        grid.innerHTML = filtered.map(p => `
            <div class="card product-item" onclick="app.addToCart(${p.id})">
                <div class="stock-tooltip">${p.stock} in stock</div>
                <h3>${p.name}</h3>
                <div class="text-sm">${p.category}</div>
                <div style="font-weight: bold; margin-top: 5px;">$${p.price.toFixed(2)}</div>
            </div>
        `).join('');
    },

    addToCart: (id) => {
        const prod = app.state.products.find(p => p.id === id);
        const existing = app.state.cart.find(i => i.product_id === id);
        if (existing) { existing.quantity++; }
        else { app.state.cart.push({ ...prod, product_id: id, quantity: 1 }); }
        app.renderCart();
    },

    renderCart: () => {
        const container = document.getElementById('cart-items');
        if (!container) return;

        let total = 0;
        if (app.state.cart.length === 0) {
            container.innerHTML = '<p class="text-sm" style="text-align: center; margin-top: 50px;">Cart is empty</p>';
        } else {
            container.innerHTML = app.state.cart.map((item, index) => {
                const sub = item.price * item.quantity;
                total += sub;
                const isSelected = index === app.state.cart.length - 1; // Auto-highlight last item
                const highlightStyle = isSelected ? 'border-left: 4px solid var(--accent); background: #f0f8ff;' : '';

                return `
                    <div class="cart-item" style="align-items: center; padding: 12px 10px; border-bottom: 1px solid #f0f0f0; ${highlightStyle}">
                        <div style="flex: 1;">
                            <div style="font-weight: 500;">${item.name}</div>
                            <div class="text-sm" style="color: #666;">$${item.price.toFixed(2)} / unit</div>
                        </div>
                        
                        <div class="flex" style="align-items: center; gap: 8px;">
                            <!-- Qty Controls -->
                            <button class="secondary" style="width: 30px; height: 30px; padding: 0; border-radius: 50%;" onclick="app.updateCartQty(${item.product_id}, -1)">-</button>
                            <span style="font-weight: bold; min-width: 20px; text-align: center;">${item.quantity}</span>
                            <button class="secondary" style="width: 30px; height: 30px; padding: 0; border-radius: 50%;" onclick="app.updateCartQty(${item.product_id}, 1)">+</button>
                        </div>

                        <div style="font-weight: bold; min-width: 70px; text-align: right;">$${sub.toFixed(2)}</div>
                        
                         <button class="danger" style="width: 30px; height: 30px; padding: 0; margin-left: 10px; display: flex; align-items: center; justify-content: center;" onclick="app.updateCartQty(${item.product_id}, -9999)">×</button>
                    </div>`;
            }).join('');

            // Auto scroll to bottom
            setTimeout(() => container.scrollTop = container.scrollHeight, 10);
        }

        const totalEl = document.getElementById('cart-total');
        if (totalEl) totalEl.innerText = `$${total.toFixed(2)}`;
        app.state.cartTotal = total; // Store for Payment Modal
    },

    updateCartQty: (id, delta) => {
        const item = app.state.cart.find(i => i.product_id === id);
        if (!item) return;

        const newQty = item.quantity + delta;
        if (newQty <= 0) {
            app.state.cart = app.state.cart.filter(i => i.product_id !== id);
        } else {
            item.quantity = newQty;
        }
        app.renderCart();
    },

    filterCategory: (cat) => {
        const grid = document.getElementById('product-list');
        if (cat === 'all') {
            app.renderProducts();
            return;
        }
        const filtered = app.state.products.filter(p => p.category === cat);
        grid.innerHTML = filtered.map(p => `
            <div class="card product-item" onclick="app.addToCart(${p.id})">
                <div class="stock-tooltip">${p.stock} in stock</div>
                <h3>${p.name}</h3>
                <div class="text-sm">${p.category}</div>
                <div style="font-weight: bold; margin-top: 5px;">$${p.price.toFixed(2)}</div>
            </div>
        `).join('');
    },

    updateCustomerMetrics: () => {
        const val = document.getElementById('customer-select').value;
        const stats = document.getElementById('customer-stats');
        if (val) {
            stats.style.display = 'flex';
            document.getElementById('last-visit').innerText = "2 Days Ago";
            document.getElementById('cust-points').innerText = "1,250";
        } else { stats.style.display = 'none'; }
    },

    checkUpsell: async () => {
        if (app.state.cart.length === 0) return;
        const payload = {
            location_id: 1,
            customer_id: document.getElementById('customer-select').value || 1,
            cart_items: app.state.cart.map(i => ({
                product_id: i.product_id, quantity: i.quantity, unit_price: i.price
            }))
        };
        try {
            const res = await fetch(`${API_URL}/loyalty/upsell`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.status === 200) {
                const offer = await res.json();
                app.showModal(offer);
            } else { alert("No offers available right now."); }
        } catch (e) { console.error(e); }
    },

    showModal: (offer) => {
        app.state.currentUpsell = offer;
        const content = document.getElementById('upsell-content');
        content.innerHTML = `<h3>${offer.suggested_product_name}</h3><p>${offer.reason}</p>
            <div class="card offer-card"><div class="text-sm">${offer.promo_tag}</div>
            <div class="flex" style="justify-content: space-between; font-size: 20px;">
                <span style="text-decoration: line-through; color: #999;">$${offer.original_price}</span>
                <span style="color: var(--danger); font-weight: bold;">$${offer.special_offer_price}</span>
            </div></div>`;
        document.getElementById('upsell-modal').classList.add('open');
    },

    closeModal: () => {
        document.getElementById('upsell-modal').classList.remove('open');
        app.state.currentUpsell = null;
    },

    acceptUpsell: () => {
        const offer = app.state.currentUpsell;
        if (!offer) return;
        const prod = { id: offer.suggested_product_id, name: offer.suggested_product_name, price: offer.special_offer_price };
        app.addToCart(prod.id);
        app.closeModal();
    },

    loadDashboard: async () => {
        try {
            const days = document.getElementById('trend-range')?.value || 30;
            const headers = { 'Authorization': `Bearer ${app.state.token}` };

            // Concurrent Fetch
            const [kpiRes, trendRes, prodRes, catRes, locRes, recentRes] = await Promise.all([
                fetch(`${API_URL}/analytics/kpis`, { headers }),
                fetch(`${API_URL}/analytics/sales-over-time?days=${days}`, { headers }),
                fetch(`${API_URL}/analytics/top-products?limit=5`, { headers }),
                fetch(`${API_URL}/analytics/categories`, { headers }),
                fetch(`${API_URL}/analytics/locations`, { headers }),
                fetch(`${API_URL}/reports/daily`, { headers })
            ]);

            if (kpiRes.ok && trendRes.ok && prodRes.ok && catRes.ok && locRes.ok) {
                const kpis = await kpiRes.json();
                const trends = await trendRes.json();
                const topProds = await prodRes.json();
                const cats = await catRes.json();
                const locs = await locRes.json();
                const recentData = await recentRes.json();

                // Render KPIs
                document.getElementById('kpi-revenue').innerText = `$${kpis.revenue_today.toFixed(2)}`;
                document.getElementById('kpi-tx').innerText = kpis.count_today;
                document.getElementById('kpi-avg').innerText = `$${kpis.avg_ticket.toFixed(2)}`;

                // Render Charts
                app.renderCharts(trends, topProds, cats, locs);

                // Render Recent
                const tbody = document.getElementById('dashboard-recent-tx');
                if (recentData.recent_transactions.length === 0) {
                    tbody.innerHTML = '<tr><td style="padding:10px; color:#999;">No active sales.</td></tr>';
                } else {
                    tbody.innerHTML = recentData.recent_transactions.map(t => `
                        <tr style="border-bottom: 1px solid #f0f0f0;">
                            <td style="padding: 8px 0;">
                                <div style="font-weight: 500;">Order #${t.id}</div>
                                <div style="font-size: 11px; color: #999;">${new Date(t.created_at).toLocaleTimeString()} • ${t.item_count} items</div>
                            </td>
                            <td style="text-align: right; font-weight: bold;">$${t.total_amount.toFixed(2)}</td>
                        </tr>
                     `).join('');
                }
            }
        } catch (e) { console.error("Dashboard Load Error", e); }
    },

    renderCharts: (trends, topProds, cats, locs) => {
        // Destroy old charts to prevent overlay
        if (window.trendChart) window.trendChart.destroy();
        if (window.prodChart) window.prodChart.destroy();
        if (window.catChart) window.catChart.destroy();
        if (window.locChart) window.locChart.destroy();

        // Trend Chart
        const ctxTrend = document.getElementById('chart-trend');
        if (ctxTrend) {
            window.trendChart = new Chart(ctxTrend, {
                type: 'line',
                data: {
                    labels: trends.map(t => new Date(t.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })),
                    datasets: [{
                        label: 'Revenue',
                        data: trends.map(t => t.revenue),
                        borderColor: '#007aff',
                        backgroundColor: 'rgba(0,122,255,0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, grid: { borderDash: [5, 5] } }, x: { grid: { display: false } } }
                }
            });
        }

        // Top Products Chart
        const ctxProd = document.getElementById('chart-products');
        if (ctxProd) {
            window.prodChart = new Chart(ctxProd, {
                type: 'bar',
                data: {
                    labels: topProds.map(p => p.name),
                    datasets: [{
                        label: 'Units Sold',
                        data: topProds.map(p => p.quantity),
                        backgroundColor: ['#34c759', '#32ade6', '#5856d6', '#ff9500', '#ff2d55'],
                        borderRadius: 4,
                        barThickness: 20
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { x: { display: false }, y: { grid: { display: false } } }
                }
            });
        }

        // Category Chart
        const ctxCat = document.getElementById('chart-cats');
        if (ctxCat) {
            window.catChart = new Chart(ctxCat, {
                type: 'doughnut',
                data: {
                    labels: cats.map(c => c.name),
                    datasets: [{
                        data: cats.map(c => c.value),
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'right', labels: { boxWidth: 10, padding: 10, usePointStyle: true } } }
                }
            });
        }

        // Location Chart
        const ctxLoc = document.getElementById('chart-locs');
        if (ctxLoc) {
            window.locChart = new Chart(ctxLoc, {
                type: 'bar',
                data: {
                    labels: locs.map(l => l.location),
                    datasets: [{
                        label: 'Revenue by Shop',
                        data: locs.map(l => l.revenue),
                        backgroundColor: '#5856d6',
                        borderRadius: 4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, grid: { display: false } }, x: { grid: { display: false } } }
                }
            });
        }
    },
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { x: { display: false }, y: { grid: { display: false } } }
}
            });
        }
    },

// --- Payment Logic ---
openPaymentModal: () => {
    if (app.state.cart.length === 0) return;
    const total = app.state.cartTotal || 0;
    document.getElementById('payment-total-due').innerText = `$${total.toFixed(2)}`;
    app.state.paymentInput = "0";
    app.updatePaymentDisplay();
    document.getElementById('payment-modal').classList.add('open');
},

    closePaymentModal: () => {
        document.getElementById('payment-modal').classList.remove('open');
    },

        loadStock: async () => {
            try {
                const res = await fetch(`${API_URL}/inventory`, {
                    headers: { 'Authorization': `Bearer ${app.state.token}` }
                });
                if (res.ok) {
                    const stock = await res.json();
                    const tbody = document.getElementById('stock-table-body');
                    if (!tbody) return;

                    if (stock.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px; color:#666;">No inventory records found.</td></tr>';
                        return;
                    }

                    tbody.innerHTML = stock.map(item => {
                        const isLow = item.stock < 10;
                        const statusHtml = isLow
                            ? `<span style="color: #d32f2f; background: #ffebee; padding: 2px 8px; border-radius: 4px; font-weight: 500;">LOW</span>`
                            : `<span style="color: #388e3c; background: #e8f5e9; padding: 2px 8px; border-radius: 4px; font-weight: 500;">OK</span>`;

                        return `
                        <tr style="border-bottom: 1px solid #f0f0f0;">
                            <td style="padding: 12px 10px; color: #666; font-size: 13px;">#${item.id}</td>
                            <td style="padding: 12px 10px; font-weight: 500;">${item.name}</td>
                            <td style="padding: 12px 10px; color: #666;">${item.category || '-'}</td>
                            <td style="padding: 12px 10px; text-align: center; font-weight: bold;">${item.stock}</td>
                            <td style="padding: 12px 10px; text-align: center;">${statusHtml}</td>
                        </tr>
                    `;
                    }).join('');
                } else {
                    console.error("Failed to load stock");
                }
            } catch (e) { console.error("Stock load error", e); }
        },

            numpadPress: (val) => {
                if (app.state.paymentInput === "0" && val !== '.') {
                    app.state.paymentInput = val;
                } else {
                    if (val === '.' && app.state.paymentInput.includes('.')) return;
                    app.state.paymentInput += val;
                }
                app.updatePaymentDisplay();
            },

                numpadClear: () => {
                    app.state.paymentInput = "0";
                    app.updatePaymentDisplay();
                },

                    quickPay: (amount) => {
                        app.state.paymentInput = amount.toString();
                        app.updatePaymentDisplay();
                    },

                        quickPayExact: () => {
                            app.state.paymentInput = (app.state.cartTotal || 0).toString();
                            app.updatePaymentDisplay();
                        },

                            updatePaymentDisplay: () => {
                                const val = parseFloat(app.state.paymentInput);
                                const total = app.state.cartTotal || 0;
                                document.getElementById('payment-input-display').innerText = `$${val.toFixed(2)}`;

                                // Calculate Change/Balance
                                const change = val - total;
                                const changeDisplay = document.getElementById('payment-change-display');

                                if (change >= 0) {
                                    changeDisplay.innerHTML = `<span style="color: var(--success);">Change Due: $${change.toFixed(2)}</span>`;
                                } else {
                                    const remaining = Math.abs(change);
                                    changeDisplay.innerHTML = `<span style="color: var(--danger);">Remaining Due: $${remaining.toFixed(2)}</span>`;
                                }
                            },

                                resetTransactionState: () => {
                                    console.log("DEBUG: Resetting Transaction State...");
                                    app.state.cart = [];
                                    app.state.cartTotal = 0;
                                    app.state.paymentInput = "0";
                                    app.state.currentDiscount = null;
                                    console.log("DEBUG: State cleared. Cart length:", app.state.cart.length);

                                    // Reset Inputs
                                    const customerSelect = document.getElementById('customer-select');
                                    if (customerSelect) customerSelect.value = "";

                                    // Update UI
                                    app.renderCart();
                                    app.updatePaymentDisplay();
                                    console.log("DEBUG: UI Updated (renderCart called).");
                                },

                                    finalizePayment: async () => {
                                        const tendered = parseFloat(app.state.paymentInput);
                                        const total = app.state.cartTotal || 0;

                                        if (tendered < total) {
                                            alert('Insufficient payment!');
                                            return;
                                        }

                                        // Proceed
                                        await app.processSale();
                                        app.closePaymentModal();
                                    },

                                        // Existing processSale (modified to be called by finalize)
                                        processSale: async () => {
                                            if (app.state.cart.length === 0) return;
                                            const payload = {
                                                selling_location_id: 1,
                                                customer_id: document.getElementById('customer-select').value || null,
                                                items: app.state.cart.map(i => ({
                                                    product_id: i.product_id, quantity: i.quantity, unit_price: i.price
                                                }))
                                            };
                                            try {
                                                const res = await fetch(`${API_URL}/sales`, {
                                                    method: 'POST',
                                                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${app.state.token}` },
                                                    body: JSON.stringify(payload)
                                                });
                                                // Relaxed check to ensure compatibility if server returns 200 or 201
                                                if (res.ok) {
                                                    // Pre-calculate change message before resetting
                                                    const change = parseFloat(app.state.paymentInput) - (app.state.cartTotal || 0);
                                                    const msg = change > 0
                                                        ? `Sale Completed! Change Due: $${change.toFixed(2)}`
                                                        : 'Sale Completed Successfully! 🎉';

                                                    // Critical: Reset state FIRST to ensure UI clears immediately
                                                    try {
                                                        app.resetTransactionState();
                                                    } catch (err) {
                                                        console.error("Critical: Reset failed", err);
                                                        alert("System Error: Cart failed to reset. Please refresh.");
                                                    }

                                                    // THEN show alert (which might block UI)
                                                    // Use setTimeout to allow UI render cycle to complete if alert is blocking
                                                    setTimeout(() => alert(msg), 10);

                                                } else {
                                                    const err = await res.json();
                                                    alert('Sale Failed: ' + err.detail);
                                                }
                                            } catch (e) { console.error(e); alert('Network Error'); }
                                        }
};

app.init();
