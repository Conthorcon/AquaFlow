// ───────── Sidebar ─────────
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  const ob = document.getElementById('openSidebar');
  if (sb.classList.contains('w-64')) {
    sb.classList.remove('w-64','p-4'); sb.classList.add('w-0','overflow-hidden','p-0');
    ob.classList.remove('hidden');
  } else {
    sb.classList.remove('w-0','overflow-hidden','p-0'); sb.classList.add('w-64','p-4');
    ob.classList.add('hidden');
  }
}

// ───────── Modal ─────────
function openModal(id, boxId) {
  const el = document.getElementById(id), box = document.getElementById(boxId);
  el.classList.remove('hidden');
  requestAnimationFrame(() => { box.classList.remove('scale-95','opacity-0'); box.classList.add('scale-100','opacity-100'); });
}
function closeModal(id, boxId) {
  const el = document.getElementById(id), box = document.getElementById(boxId);
  box.classList.remove('scale-100','opacity-100'); box.classList.add('scale-95','opacity-0');
  setTimeout(() => el.classList.add('hidden'), 250);
}

// ───────── Toast ─────────
function showToast(msg, type = 'success') {
  const colors = { success:'bg-green-600', error:'bg-red-600', warning:'bg-amber-500', info:'bg-blue-600' };
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `px-4 py-3 rounded-xl text-white text-sm font-medium shadow-xl max-w-xs pointer-events-auto ${colors[type]} transform translate-x-8 opacity-0 transition-all duration-300`;
  t.textContent = msg;
  c.appendChild(t);
  requestAnimationFrame(() => { t.classList.remove('translate-x-8','opacity-0'); t.classList.add('translate-x-0','opacity-100'); });
  setTimeout(() => { t.classList.add('translate-x-8','opacity-0'); setTimeout(() => t.remove(), 300); }, 3000);
}

// ───────── Search and Filter ─────────
let currentFilter = 'all';

function applyFilterAndSearch() {
  const q = document.getElementById('search-input').value.toLowerCase();
  
  document.querySelectorAll('.inventory-row').forEach(r => {
    const nameMatch = r.dataset.name.includes(q);
    const qty = parseInt(r.dataset.qty) || 0;
    
    let filterMatch = true;
    if (currentFilter === 'instock') filterMatch = (qty > 0);
    else if (currentFilter === 'outstock') filterMatch = (qty === 0);
    
    r.style.display = (nameMatch && filterMatch) ? '' : 'none';
  });
}

document.getElementById('search-input').addEventListener('input', applyFilterAndSearch);

document.querySelectorAll('.card-filter').forEach(card => {
  card.addEventListener('click', () => {
    const filter = card.dataset.filter;
    currentFilter = filter;
    
    let targetText = 'Tất cả sản phẩm';
    if (filter === 'instock') targetText = 'Sản phẩm còn hàng';
    else if (filter === 'outstock') targetText = 'Sản phẩm hết hàng';
    
    const textEl = document.getElementById('current-filter-text');
    if (textEl) textEl.textContent = targetText;
    
    document.querySelectorAll('.card-filter').forEach(c => c.classList.remove('ring-2', 'ring-blue-400', 'ring-offset-1'));
    card.classList.add('ring-2', 'ring-blue-400', 'ring-offset-1');
    
    applyFilterAndSearch();
  });
});


// ═══════════════════════════════════════════════════
// ADD PRODUCT MODAL
// ═══════════════════════════════════════════════════
let newProductPrices = {};

function buildGroupSelect(selectEl) {
  selectEl.innerHTML = '<option value="">— Chọn loại khách —</option>';
  // GROUPS is passed from Flask template
  if (typeof GROUPS !== 'undefined') {
    GROUPS.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.id; opt.textContent = g.name;
      selectEl.appendChild(opt);
    });
  }
}

function renderConfirmedPrices() {
  const list = document.getElementById('confirmed-prices-list');
  const noMsg = document.getElementById('no-prices-msg');
  [...list.children].forEach(c => { if (c !== noMsg) c.remove(); });

  const entries = Object.entries(newProductPrices);
  noMsg.style.display = entries.length === 0 ? '' : 'none';

  entries.forEach(([gid, price]) => {
    const g = GROUPS.find(x => x.id == gid);
    if (!g) return;
    const row = document.createElement('div');
    row.className = 'confirmed-row flex items-center justify-between bg-purple-50 border border-purple-100 rounded-xl px-3 py-2';
    row.innerHTML = `
      <div class="flex items-center gap-2">
        <svg class="w-4 h-4 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
        </svg>
        <span class="text-sm font-medium text-gray-700">${g.name}</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm font-bold text-purple-700">${Number(price).toLocaleString('en-US')}đ</span>
        <button onclick="removeNewPrice(${gid})" class="text-gray-300 hover:text-red-400 transition text-xs leading-none" title="Xóa">✕</button>
      </div>
    `;
    list.appendChild(row);
  });
}

function removeNewPrice(gid) {
  delete newProductPrices[gid];
  renderConfirmedPrices();
}

document.getElementById('btn-add-product').onclick = () => {
  newProductPrices = {};
  ['new-product-name','new-cap-type','new-bottle-type','new-capacity'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('new-init-qty').value = '0';
  document.getElementById('new-group-select').value = '';
  document.getElementById('new-price-input').value = '';
  buildGroupSelect(document.getElementById('new-group-select'));
  renderConfirmedPrices();
  openModal('modal-add-product','modal-add-product-box');
};
document.getElementById('modal-add-product-backdrop').onclick = () => closeModal('modal-add-product','modal-add-product-box');

document.getElementById('new-group-select').addEventListener('change', e => {
  const gid = e.target.value;
  const priceInput = document.getElementById('new-price-input');
  priceInput.value = gid && newProductPrices[gid] != null ? newProductPrices[gid] : '';
});

document.getElementById('new-price-confirm-btn').onclick = () => {
  const select = document.getElementById('new-group-select');
  const priceInput = document.getElementById('new-price-input');
  const gid = select.value;
  const price = parseFloat(priceInput.value);

  if (!gid) { showToast('Vui lòng chọn loại khách hàng', 'warning'); return; }
  if (isNaN(price) || price < 0) { showToast('Giá không hợp lệ', 'warning'); return; }

  const gName = GROUPS.find(g => g.id == gid)?.name || '';

  showInlineConfirm(
    `Xác nhận giá <strong>${price.toLocaleString('en-US')}đ</strong> cho <strong>${gName}</strong>?`,
    () => {
      newProductPrices[gid] = price;
      select.value = '';
      priceInput.value = '';
      renderConfirmedPrices();
    }
  );
};

document.getElementById('btn-submit-add-product').onclick = () => {
  const name = document.getElementById('new-product-name').value.trim();
  if (!name) { showToast('Vui lòng nhập tên sản phẩm', 'warning'); return; }

  fetch('/api/inventory/add_product', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
      name,
      cap_type:    document.getElementById('new-cap-type').value.trim(),
      bottle_type: document.getElementById('new-bottle-type').value.trim(),
      capacity:    document.getElementById('new-capacity').value.trim(),
      initial_qty: parseInt(document.getElementById('new-init-qty').value) || 0,
      group_prices: newProductPrices
    })
  }).then(r => r.json()).then(result => {
    if (result.status === 'success') {
      closeModal('modal-add-product','modal-add-product-box');
      showToast('Đã thêm sản phẩm thành công!', 'success');
      setTimeout(() => window.location.reload(), 800);
    } else { showToast(result.message, 'error'); }
  });
};


// ═══════════════════════════════════════════════════
// EDIT PRICE MODAL
// ═══════════════════════════════════════════════════
let editCurrentPrices = {};  

function openPriceModal(productId, productName, pricesByGroup) {
  editCurrentPrices = { ...pricesByGroup };
  document.getElementById('price-product-id').value = productId;
  document.getElementById('modal-price-subtitle').textContent = productName;
  document.getElementById('edit-group-select').value = '';
  document.getElementById('edit-price-input').value = '';
  buildGroupSelect(document.getElementById('edit-group-select'));
  renderEditSavedPrices();
  openModal('modal-price','modal-price-box');
}
document.getElementById('modal-price-backdrop').onclick = () => closeModal('modal-price','modal-price-box');

document.getElementById('edit-group-select').addEventListener('change', e => {
  const gid = e.target.value;
  const priceInput = document.getElementById('edit-price-input');
  priceInput.value = gid && editCurrentPrices[gid] != null ? editCurrentPrices[gid] : '';
});

function renderEditSavedPrices() {
  const container = document.getElementById('edit-saved-prices');
  container.innerHTML = '';
  const entries = Object.entries(editCurrentPrices).filter(([,p]) => p > 0);

  if (entries.length === 0) {
    container.innerHTML = '<p class="text-xs text-gray-400 italic">Chưa có giá nào được thiết lập</p>';
    return;
  }
  entries.forEach(([gid, price]) => {
    const g = GROUPS.find(x => x.id == gid);
    if (!g) return;
    const row = document.createElement('div');
    row.className = 'confirmed-row flex items-center justify-between bg-purple-50 border border-purple-100 rounded-xl px-3 py-2';
    row.innerHTML = `
      <span class="text-sm font-medium text-gray-700">${g.name}</span>
      <span class="text-sm font-bold text-purple-700">${Number(price).toLocaleString('en-US')}đ</span>
    `;
    container.appendChild(row);
  });
}

document.getElementById('edit-price-confirm-btn').onclick = () => {
  const productId = document.getElementById('price-product-id').value;
  const select = document.getElementById('edit-group-select');
  const priceInput = document.getElementById('edit-price-input');
  const gid = select.value;
  const price = parseFloat(priceInput.value);

  if (!gid) { showToast('Vui lòng chọn loại khách hàng', 'warning'); return; }
  if (isNaN(price) || price < 0) { showToast('Giá không hợp lệ', 'warning'); return; }

  const gName = GROUPS.find(g => g.id == gid)?.name || '';

  showInlineConfirm(
    `Lưu giá <strong>${price.toLocaleString('en-US')}đ</strong> cho <strong>${gName}</strong>?`,
    () => {
      fetch('/api/inventory/update_price_single', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ product_id: productId, group_id: parseInt(gid), price })
      }).then(r => r.json()).then(result => {
        if (result.status === 'success') {
          editCurrentPrices[gid] = price;
          select.value = '';
          priceInput.value = '';
          renderEditSavedPrices();
          showToast(`Đã lưu giá ${gName}`, 'success');
          // Update attribute in DOM so it presists until page reload
          const btn = document.querySelector(`.btn-edit-price[data-id="${productId}"]`);
          if(btn) {
              btn.dataset.prices = JSON.stringify(editCurrentPrices);
          }
        } else { showToast(result.message, 'error'); }
      });
    }
  );
};


// ═══════════════════════════════════════════════════
// INVENTORY QTY MODAL
// ═══════════════════════════════════════════════════
function openUpdateModal(productId, productName, currentQty) {
  document.getElementById('update-product-id').value = productId;
  document.getElementById('update-mode').value = 'set';
  document.getElementById('modal-update-title').textContent = 'Đặt lại tồn kho';
  document.getElementById('modal-update-subtitle').textContent = productName;
  document.getElementById('update-qty-label').textContent = 'Số lượng mới';
  document.getElementById('update-qty-value').value = currentQty;
  document.getElementById('update-note').value = '';
  const btn = document.getElementById('btn-submit-update-qty');
  btn.className = 'px-5 py-2 rounded-xl text-sm font-semibold text-white transition active:scale-95 bg-blue-600 hover:bg-blue-700';
  btn.textContent = 'Lưu';
  openModal('modal-update-qty','modal-update-qty-box');
}

function openAddModal(productId, productName, currentQty) {
  document.getElementById('update-product-id').value = productId;
  document.getElementById('update-mode').value = 'add';
  document.getElementById('modal-update-title').textContent = 'Nhập thêm hàng';
  document.getElementById('modal-update-subtitle').textContent = `${productName} — Hiện tại: ${currentQty}`;
  document.getElementById('update-qty-label').textContent = 'Số lượng nhập thêm';
  document.getElementById('update-qty-value').value = 0;
  document.getElementById('update-note').value = '';
  const btn = document.getElementById('btn-submit-update-qty');
  btn.className = 'px-5 py-2 rounded-xl text-sm font-semibold text-white transition active:scale-95 bg-green-600 hover:bg-green-700';
  btn.textContent = 'Nhập thêm';
  openModal('modal-update-qty','modal-update-qty-box');
}
document.getElementById('modal-update-qty-backdrop').onclick = () => closeModal('modal-update-qty','modal-update-qty-box');

document.getElementById('btn-submit-update-qty').onclick = () => {
  const productId = document.getElementById('update-product-id').value;
  const mode = document.getElementById('update-mode').value;
  const quantity = parseInt(document.getElementById('update-qty-value').value) || 0;
  const note = document.getElementById('update-note').value.trim();

  fetch('/api/inventory/update', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ product_id: productId, quantity, mode, note })
  }).then(r => r.json()).then(result => {
    if (result.status === 'success') {
      closeModal('modal-update-qty','modal-update-qty-box');
      showToast('Cập nhật tồn kho thành công!', 'success');
      setTimeout(() => window.location.reload(), 800);
    } else { showToast(result.message, 'error'); }
  });
};


// ═══════════════════════════════════════════════════
// INLINE CONFIRM
// ═══════════════════════════════════════════════════
function showInlineConfirm(htmlMsg, onConfirm) {
  const old = document.getElementById('inline-confirm-popup');
  if (old) old.remove();

  const popup = document.createElement('div');
  popup.id = 'inline-confirm-popup';
  popup.className = 'fixed inset-0 z-[10001] flex items-center justify-center';
  popup.innerHTML = `
    <div class="absolute inset-0 bg-black/20" onclick="this.parentElement.remove()"></div>
    <div class="relative bg-white rounded-2xl shadow-2xl px-6 py-5 max-w-xs w-full mx-4 transform transition-all duration-200 scale-95 opacity-0" id="inline-confirm-box">
      <p class="text-sm text-gray-700 leading-relaxed mb-4">${htmlMsg}</p>
      <div class="flex gap-2 justify-end">
        <button onclick="document.getElementById('inline-confirm-popup').remove()"
          class="px-4 py-2 rounded-xl text-sm font-semibold bg-gray-100 text-gray-600 hover:bg-gray-200 transition active:scale-95">Hủy</button>
        <button id="inline-confirm-ok"
          class="px-4 py-2 rounded-xl text-sm font-semibold bg-purple-600 text-white hover:bg-purple-700 transition active:scale-95">Xác nhận</button>
      </div>
    </div>
  `;
  document.body.appendChild(popup);

  requestAnimationFrame(() => {
    const box = document.getElementById('inline-confirm-box');
    if(box) {
        box.classList.remove('scale-95','opacity-0');
        box.classList.add('scale-100','opacity-100');
    }
  });

  document.getElementById('inline-confirm-ok').onclick = () => {
    popup.remove();
    onConfirm();
  };
}


// Event Delegation for action buttons
document.addEventListener('click', e => {
  // Edit Price button
  const btnEditPrice = e.target.closest('.btn-edit-price');
  if (btnEditPrice) {
    const productId = btnEditPrice.dataset.id;
    const productName = btnEditPrice.dataset.name;
    const pricesByGroup = JSON.parse(btnEditPrice.dataset.prices || '{}');
    openPriceModal(productId, productName, pricesByGroup);
    return;
  }
  
  // Add stock button
  const btnAddStock = e.target.closest('.btn-add-stock');
  if (btnAddStock) {
    const productId = btnAddStock.dataset.id;
    const productName = btnAddStock.dataset.name;
    const qty = btnAddStock.dataset.qty;
    openAddModal(productId, productName, qty);
    return;
  }
});
