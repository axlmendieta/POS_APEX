import { products, quickItems } from './items.js';

// --- State ---
let cart = [];
let selectedIndex = -1;
let total = 0;
let isPaymentModalOpen = false;
let isWeightModalOpen = false;
let pendingWeightItem = null;

// --- DOM Elements ---
const omniSearch = document.getElementById('omni-search');
const ticketItemsContainer = document.getElementById('ticket-items');
const totalAmountEl = document.getElementById('total-amount');
const quickGrid = document.getElementById('quick-grid');
const payButton = document.getElementById('pay-btn');
const paymentModal = document.getElementById('payment-modal');
const weightModal = document.getElementById('weight-modal');
const weightInput = document.getElementById('weight-input');
const receivedInput = document.getElementById('received-input');
const changeDisplay = document.getElementById('change-display');
const denomGrid = document.getElementById('denom-grid');
const toastEl = document.getElementById('toast');

// --- Initialization ---
function init() {
    renderQuickGrid();
    omniSearch.focus();
    setupEventListeners();
}

function setupEventListeners() {
    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        if (isPaymentModalOpen || isWeightModalOpen) return; // Modal logic handles its own keys

        switch (e.key) {
            case 'F1':
                e.preventDefault();
                omniSearch.focus();
                break;
            case 'F5':
                e.preventDefault();
                if (cart.length > 0) openPaymentModal();
                break;
            case 'F10':
                e.preventDefault();
                showToast('Price Check Mode Active (Mock)');
                break;
            case 'Delete':
                if (selectedIndex >= 0 && selectedIndex < cart.length) {
                    removeFromCart(selectedIndex);
                }
                break;
            case '+':
            case '=': // Often shared key
                if (document.activeElement !== omniSearch && selectedIndex >= 0) {
                    updateQuantity(selectedIndex, 1);
                    e.preventDefault(); // Prevent typing +
                }
                break;
            case '-':
                if (document.activeElement !== omniSearch && selectedIndex >= 0) {
                    updateQuantity(selectedIndex, -1);
                    e.preventDefault();
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                selectRow(Math.max(0, selectedIndex - 1));
                break;
            case 'ArrowDown':
                e.preventDefault();
                selectRow(Math.min(cart.length - 1, selectedIndex + 1));
                break;
        }
    });

    // Validating input only numbers on weight
    weightInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') confirmWeight();
        if (e.key === 'Escape') closeWeightModal();
    });

    // Search Input
    omniSearch.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            handleSearch(omniSearch.value);
            omniSearch.value = '';
        }
    });

    // Payment Input
    receivedInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') calculateChange();
        if (e.key === 'Escape') closePaymentModal();
    });

    // Numpad clicks (Delegation)
    document.querySelector('.numpad').addEventListener('click', (e) => {
        if (e.target.classList.contains('num-key')) {
            handleNumpad(e.target.dataset.key);
        }
    });
}

// --- Core Logic ---

function handleSearch(query) {
    if (!query) return;

    // precise match for barcode usually
    const product = products.find(p => p.barcode === query || p.name.toLowerCase() === query.toLowerCase());

    if (product) {
        if (product.weighted) {
            openWeightModal(product);
        } else {
            addToCart(product, 1);
        }
    } else {
        showToast(`Item "${query}" not found`);
        playErrorSound();
    }
}

function addToCart(product, qty) {
    const existingIndex = cart.findIndex(item => item.barcode === product.barcode);

    if (existingIndex > -1 && !product.weighted) {
        // If not weighted, just stack
        cart[existingIndex].qty += qty;
        cart[existingIndex].total = cart[existingIndex].qty * cart[existingIndex].price;
        selectRow(existingIndex);
    } else {
        // Add new (Weighted items always new row usually, but here we simplify)
        cart.push({
            ...product,
            qty: qty,
            total: qty * product.price
        });
        selectRow(cart.length - 1);
    }
    renderTicket();
}

function updateQuantity(index, change) {
    const item = cart[index];
    if (!item) return;

    if (item.weighted) {
        showToast("Cannot auto-adjust weighted items. Delete and re-weigh.");
        return;
    }

    item.qty += change;
    if (item.qty <= 0) {
        cart.splice(index, 1);
        selectedIndex = Math.min(index, cart.length - 1);
    } else {
        item.total = item.qty * item.price;
    }
    renderTicket();
}

function removeFromCart(index) {
    cart.splice(index, 1);
    selectedIndex = Math.min(index, cart.length - 1);
    renderTicket();
}

// --- Rendering ---

function renderTicket() {
    ticketItemsContainer.innerHTML = '';
    let rollingTotal = 0;

    cart.forEach((item, index) => {
        rollingTotal += item.total;

        const row = document.createElement('div');
        row.className = `ticket-row ${index === selectedIndex ? 'selected' : ''}`;
        row.innerHTML = `
            <div>${item.qty}</div>
            <div>${item.name}</div>
            <div>$${item.price.toFixed(2)}</div>
            <div>$${item.total.toFixed(2)}</div>
            <div><button class="btn-danger" style="padding:2px 8px; font-size: 0.8rem">X</button></div>
        `;

        row.addEventListener('click', () => selectRow(index));
        row.querySelector('button').addEventListener('click', (e) => {
            e.stopPropagation();
            removeFromCart(index);
        });

        ticketItemsContainer.appendChild(row);
    });

    total = rollingTotal;
    totalAmountEl.textContent = `$${total.toFixed(2)}`;

    // Auto scroll to bottom
    const last = ticketItemsContainer.lastElementChild;
    if (last) last.scrollIntoView({ behavior: 'smooth' });
}

function selectRow(index) {
    selectedIndex = index;
    // visual update without full re-render for performance? 
    // keeping simple with full re-render for now as list is small
    // Optimization: Just toggle classes
    Array.from(ticketItemsContainer.children).forEach((el, i) => {
        if (i === index) el.classList.add('selected');
        else el.classList.remove('selected');
    });
}

function renderQuickGrid() {
    quickGrid.innerHTML = '';
    quickItems.forEach(item => {
        const btn = document.createElement('button');
        btn.className = 'quick-btn';
        btn.innerHTML = `
            <span class="icon">${item.image}</span>
            <span>${item.name}</span>
        `;
        btn.addEventListener('click', () => {
            // Simulate looking up by barcode
            handleSearch(item.barcode);
            omniSearch.focus();
        });
        quickGrid.appendChild(btn);
    });
}

// --- Modals ---

function openWeightModal(product) {
    isWeightModalOpen = true;
    pendingWeightItem = product;
    weightModal.classList.add('active');
    document.getElementById('weight-product-name').textContent = product.name;
    weightInput.value = '';
    weightInput.focus();
}

function confirmWeight() {
    const w = parseFloat(weightInput.value);
    if (w > 0) {
        addToCart(pendingWeightItem, w);
        closeWeightModal();
    } else {
        showToast("Invalid Weight");
    }
}

function closeWeightModal() {
    isWeightModalOpen = false;
    pendingWeightItem = null;
    weightModal.classList.remove('active');
    omniSearch.focus();
}

function openPaymentModal() {
    if (total === 0) return;

    isPaymentModalOpen = true;
    paymentModal.classList.add('active');
    document.getElementById('pay-total-display').textContent = `$${total.toFixed(2)}`;
    receivedInput.value = '';
    receivedInput.focus();
    changeDisplay.style.display = 'none';

    // Generate smart denominations
    const denoms = [
        Math.ceil(total),      // Exact / Closest int
        Math.ceil(total / 10) * 10,
        Math.ceil(total / 20) * 20,
        50, 100, 200, 500
    ].filter((v, i, a) => v >= total && a.indexOf(v) === i).sort((a, b) => a - b).slice(0, 6);

    denomGrid.innerHTML = '';
    denoms.forEach(d => {
        const btn = document.createElement('button');
        btn.className = 'denom-btn';
        btn.textContent = `$${d}`;
        btn.onclick = () => {
            receivedInput.value = d;
            calculateChange();
        };
        denomGrid.appendChild(btn);
    });
}

function calculateChange() {
    const received = parseFloat(receivedInput.value);
    if (received >= total) {
        const change = received - total;
        changeDisplay.textContent = `Change: $${change.toFixed(2)}`;
        changeDisplay.style.display = 'block';
        showToast("Transaction Complete!");

        // Optional: Auto close after few seconds and reset
        setTimeout(() => {
            closePaymentModal();
            cart = [];
            total = 0;
            renderTicket();
        }, 2000);

    } else {
        showToast("Insufficient Amount");
    }
}

function closePaymentModal() {
    isPaymentModalOpen = false;
    paymentModal.classList.remove('active');
    omniSearch.focus();
}

// --- Utils ---

function handleNumpad(key) {
    // Determine target input based on context
    let target = omniSearch;
    if (isPaymentModalOpen) target = receivedInput;
    if (isWeightModalOpen) target = weightInput;

    if (key === 'backspace') {
        target.value = target.value.slice(0, -1);
    } else if (key === 'enter') {
        // Dispatch enter event to target
        target.dispatchEvent(new KeyboardEvent('keydown', { 'key': 'Enter' }));
    } else {
        target.value += key;
    }
    target.focus();
}

function showToast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add('active');
    setTimeout(() => toastEl.classList.remove('active'), 2000);
}

function playErrorSound() {
    // Implementation for beep
    console.log("Beep!");
}

// Start
init();
