// ───────── Common UI ─────────
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const openBtn = document.getElementById('openSidebar');
    if (sidebar.classList.contains('w-64')) {
        sidebar.classList.replace('w-64', 'w-0');
        sidebar.classList.add('overflow-hidden', 'p-0');
        openBtn.classList.remove('hidden');
    } else {
        sidebar.classList.replace('w-0', 'w-64');
        sidebar.classList.remove('overflow-hidden', 'p-0');
        openBtn.classList.add('hidden');
    }
}

function openModal(id, boxId) {
    const el = document.getElementById(id), box = document.getElementById(boxId);
    el.classList.remove('hidden');
    requestAnimationFrame(() => { 
        box.classList.remove('scale-95','opacity-0'); 
        box.classList.add('scale-100','opacity-100'); 
    });
}

function closeModal(id, boxId) {
    const el = document.getElementById(id), box = document.getElementById(boxId);
    box.classList.remove('scale-100','opacity-100'); 
    box.classList.add('scale-95','opacity-0');
    setTimeout(() => el.classList.add('hidden'), 250);
}

function showToast(msg, type = 'success') {
    const colors = { success:'bg-green-600', error:'bg-red-600', warning:'bg-amber-500', info:'bg-blue-600' };
    const container = document.getElementById('toast-container');
    const t = document.createElement('div');
    t.className = `px-4 py-3 rounded-xl text-white text-sm font-medium shadow-xl max-w-xs pointer-events-auto ${colors[type]} transform translate-x-8 opacity-0 transition-all duration-300`;
    t.textContent = msg;
    container.appendChild(t);
    requestAnimationFrame(() => { t.classList.remove('translate-x-8','opacity-0'); t.classList.add('translate-x-0','opacity-100'); });
    setTimeout(() => { t.classList.add('translate-x-8','opacity-0'); setTimeout(() => t.remove(), 300); }, 3000);
}

const ICONS = {
    error: { bg: 'bg-red-100 text-red-600', svg: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>' },
    success: { bg: 'bg-green-100 text-green-600', svg: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>' },
    info: { bg: 'bg-blue-100 text-blue-600', svg: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>' },
    warning: { bg: 'bg-amber-100 text-amber-600', svg: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>' }
};

// function showAlert(title, message, type = 'info') {
//     const el = document.getElementById('modal-alert');
//     const box = document.getElementById('modal-alert-box');
//     const icon = document.getElementById('modal-alert-icon');
//     document.getElementById('modal-alert-title').textContent = title;
//     document.getElementById('modal-alert-message').innerHTML = message;
//     icon.className = `mx-auto mb-4 w-12 h-12 rounded-full flex items-center justify-center ${ICONS[type].bg}`;
//     icon.innerHTML = ICONS[type].svg;
//     openModal('modal-alert', 'modal-alert-box');
// }

document.getElementById('modal-alert-ok').onclick = () => closeModal('modal-alert', 'modal-alert-box');
document.getElementById('modal-alert-backdrop').onclick = () => closeModal('modal-alert', 'modal-alert-box');

function showConfirm(title, message, onConfirm) {
    const el = document.getElementById('modal-confirm');
    const box = document.getElementById('modal-confirm-box');
    document.getElementById('modal-confirm-title').textContent = title;
    document.getElementById('modal-confirm-message').textContent = message;
    
    document.getElementById('modal-confirm-ok').onclick = () => {
        closeModal('modal-confirm', 'modal-confirm-box');
        onConfirm();
    };
    document.getElementById('modal-confirm-cancel').onclick = () => closeModal('modal-confirm', 'modal-confirm-box');
    document.getElementById('modal-confirm-backdrop').onclick = () => closeModal('modal-confirm', 'modal-confirm-box');
    
    openModal('modal-confirm', 'modal-confirm-box');
}

// ───────── Customer Data ─────────
let allCustomers = [];

async function fetchCustomers() {
    try {
        const response = await fetch('/api/customers');
        allCustomers = await response.json();
        renderTable(allCustomers);
    } catch (err) {
        console.error('Fetch error:', err);
    }
}

function renderTable(data) {
    const body = document.getElementById('customer-table-body');
    const noData = document.getElementById('no-data-msg');
    body.innerHTML = '';
    
    if (data.length === 0) {
        noData.classList.remove('hidden');
        return;
    }
    noData.classList.add('hidden');

    data.forEach(c => {
        const tr = document.createElement('tr');
        tr.className = 'border-b hover:bg-gray-50/60 transition-colors cursor-default';
        tr.innerHTML = `
            <td class="px-5 py-3 font-semibold text-gray-800">${c.name}</td>
            <td class="px-5 py-3 text-gray-600 text-sm font-medium tabular-nums">${c.phone || '—'}</td>
            <td class="px-5 py-3 text-gray-500 text-sm leading-relaxed">${c.address || '—'}</td>
            <td class="px-5 py-3">
                <span class="inline-flex px-2 py-0.5 rounded-lg text-xs font-bold bg-blue-50 text-blue-600 border border-blue-100">
                    ${c.group_name}
                </span>
            </td>
            <td class="px-5 py-3 text-center">
                <div class="flex items-center justify-center gap-2">
                    <button onclick="editCustomer(${c.id})" class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition" title="Sửa thông tin">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                    </button>
                    <button onclick="deleteCustomer(${c.id}, '${c.name}')" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition" title="Xóa khách hàng">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                </div>
            </td>
        `;
        body.appendChild(tr);
    });
}

// ───────── Search ─────────
document.getElementById('search-input').oninput = (e) => {
    const q = e.target.value.toLowerCase();
    const filtered = allCustomers.filter(c => 
        c.name.toLowerCase().includes(q) || 
        (c.address && c.address.toLowerCase().includes(q))
    );
    renderTable(filtered);
};

// ───────── Actions ─────────
document.getElementById('btn-add-customer').onclick = () => {
    // Reset form
    document.getElementById('edit-cust-id').value = '';
    document.getElementById('modal-add-customer').querySelector('h3').textContent = 'Thêm khách hàng mới';
    document.getElementById('btn-submit-customer').textContent = 'Thêm mới';
    
    document.getElementById('new-cust-name').value = '';
    document.getElementById('new-cust-phone').value = '';
    document.getElementById('addr-street').value = '';
    document.getElementById('addr-ward').value = '';
    document.getElementById('addr-city').value = '';
    
    const select = document.getElementById('new-cust-group');
    refreshGroupSelects(select);
    
    openModal('modal-add-customer', 'modal-add-customer-box');
};

function refreshGroupSelects(selectEl, selectedId = null) {
    selectEl.innerHTML = '<option value="">— Chọn nhóm —</option>';
    GROUPS.forEach(g => {
        const opt = document.createElement('option');
        opt.value = g.id; opt.textContent = g.name;
        if (g.id == selectedId) opt.selected = true;
        selectEl.appendChild(opt);
    });
}

function editCustomer(id) {
    const c = allCustomers.find(x => x.id === id);
    if (!c) return;

    document.getElementById('edit-cust-id').value = c.id;
    document.getElementById('modal-add-customer').querySelector('h3').textContent = 'Chỉnh sửa thông tin';
    document.getElementById('btn-submit-customer').textContent = 'Lưu thay đổi';

    document.getElementById('new-cust-name').value = c.name;
    document.getElementById('new-cust-phone').value = c.phone || '';
    
    // Split address: "Street, Ward, City"
    const parts = c.address ? c.address.split(', ') : [];
    document.getElementById('addr-street').value = parts[0] || '';
    document.getElementById('addr-ward').value = parts[1] || '';
    document.getElementById('addr-city').value = parts[2] || '';

    // Build groups and select
    const select = document.getElementById('new-cust-group');
    refreshGroupSelects(select, c.group_id);

    openModal('modal-add-customer', 'modal-add-customer-box');
}

// ───────── Group Actions ─────────
function renderGroupList() {
    const container = document.getElementById('group-list-container');
    container.innerHTML = '';
    
    GROUPS.forEach(g => {
        const item = document.createElement('div');
        item.className = 'flex items-center justify-between p-2 hover:bg-gray-50 rounded-xl group transition';
        item.innerHTML = `
            <span class="text-sm font-medium text-gray-700">${g.name}</span>
            <button onclick="deleteGroup(${g.id}, '${g.name}')" class="p-1.5 text-gray-300 hover:text-red-600 hover:bg-red-50 rounded-lg transition opacity-0 group-hover:opacity-100" title="Xóa nhóm">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
        `;
        container.appendChild(item);
    });
}

document.getElementById('btn-quick-add-group').onclick = () => {
    document.getElementById('new-group-name').value = '';
    renderGroupList();
    openModal('modal-add-group', 'modal-add-group-box');
};
document.getElementById('modal-add-group-cancel').onclick = () => closeModal('modal-add-group', 'modal-add-group-box');
document.getElementById('modal-add-group-backdrop').onclick = () => closeModal('modal-add-group', 'modal-add-group-box');

document.getElementById('btn-submit-group').onclick = async () => {
    const name = document.getElementById('new-group-name').value.trim();
    if (!name) { showToast('Vui lòng nhập tên nhóm', 'warning'); return; }

    try {
        const response = await fetch('/api/addGroup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const result = await response.json();
        if (response.ok) {
            showToast('Thêm nhóm thành công!', 'success');
            // Update local GROUPS list
            GROUPS.push({ id: result.id, name: result.name });
            // Update the select in the parent modal
            refreshGroupSelects(document.getElementById('new-cust-group'), result.id);
            renderGroupList();
            document.getElementById('new-group-name').value = '';
        } else {
            showToast(result.message || 'Lỗi khi thêm nhóm', 'error');
        }
    } catch (err) {
        showToast('Lỗi kết nối server', 'error');
    }
};

async function deleteGroup(id, name) {
    showConfirm('Xác nhận xóa nhóm', `Bạn có chắc chắn muốn xóa nhóm "${name}"?`, async () => {
        try {
            const response = await fetch(`/api/deleteGroup/${id}`, { method: 'DELETE' });
            const result = await response.json();
            if (response.ok) {
                showToast('Đã xóa nhóm khách hàng', 'success');
                // Update local list
                const idx = GROUPS.findIndex(g => g.id === id);
                if (idx > -1) GROUPS.splice(idx, 1);
                // Refresh UI
                renderGroupList();
                refreshGroupSelects(document.getElementById('new-cust-group'));
            } else {
                showToast(result.message || 'Lỗi khi xóa', 'error');
            }
        } catch (err) {
            showToast('Lỗi kết nối server', 'error');
        }
    });
}
document.getElementById('modal-add-customer-backdrop').onclick = () => closeModal('modal-add-customer', 'modal-add-customer-box');

document.getElementById('btn-submit-customer').onclick = async () => {
    const id = document.getElementById('edit-cust-id').value;
    const name = document.getElementById('new-cust-name').value.trim();
    const phone = document.getElementById('new-cust-phone').value.trim();
    const street = document.getElementById('addr-street').value.trim();
    const ward = document.getElementById('addr-ward').value.trim();
    const city = document.getElementById('addr-city').value.trim();
    const group_id = document.getElementById('new-cust-group').value;

    if (!name || !group_id) {
        showToast('Vui lòng điền đầy đủ Tên và Nhóm khách', 'warning');
        return;
    }

    const payload = { id, name, phone, street, ward, city, group_id };
    const endpoint = id ? '/api/updateCustomer' : '/api/addCustomer';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (response.ok) {
            showToast(id ? 'Đã cập nhật thông tin!' : 'Thêm khách hàng thành công!', 'success');
            closeModal('modal-add-customer', 'modal-add-customer-box');
            fetchCustomers();
        } else {
            showToast(result.message || 'Có lỗi xảy ra', 'error');
        }
    } catch (err) {
        showToast('Lỗi kết nối server', 'error');
    }
};

async function deleteCustomer(id, name) {
    showConfirm('Xác nhận xóa', `Bạn có chắc chắn muốn xóa khách hàng "${name}" không? Thao tác này không thể hoàn tác.`, async () => {
        try {
            const response = await fetch(`/api/deleteCustomer/${id}`, { method: 'DELETE' });
            const result = await response.json();
            if (response.ok) {
                showToast('Đã xóa khách hàng', 'success');
                fetchCustomers();
            } else {
                showToast(result.message || 'Lỗi khi xóa', 'error');
            }
        } catch (err) {
            showToast('Lỗi kết nối server', 'error');
        }
    });
}


// function showHelp() {
//     showAlert("Thông tin hỗ trợ", "Vui lòng liên hệ:<br>Kỹ thuật viên: Trương Trần Phương Khanh<br>Số điện thoại: 0912 345 678", "info");
// }

// Init
window.onload = fetchCustomers;
