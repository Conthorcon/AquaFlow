// ───────── Common UI ─────────
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

// ───────── Employee Data ─────────
let allEmployees = [];

async function fetchEmployees() {
    try {
        const response = await fetch('/api/employeeList');
        allEmployees = await response.json();
        renderTable(allEmployees);
    } catch (err) {
        console.error('Fetch error:', err);
    }
}

function renderTable(data) {
    const body = document.getElementById('employee-table-body');
    const noData = document.getElementById('no-data-msg');
    body.innerHTML = '';
    
    if (data.length === 0) {
        noData.classList.remove('hidden');
        return;
    }
    noData.classList.add('hidden');

    data.forEach(e => {
        const tr = document.createElement('tr');
        tr.className = 'border-b hover:bg-gray-50/60 transition-colors cursor-default';
        tr.innerHTML = `
            <td class="px-5 py-3 font-semibold text-gray-800">${e.name}</td>
            <td class="px-5 py-3 text-gray-600 text-sm font-medium tabular-nums">${e.phone || '—'}</td>
            <td class="px-5 py-3 text-gray-500 text-sm leading-relaxed truncate max-w-[200px]" title="${e.address || ''}">${e.address || '—'}</td>
            <td class="px-5 py-3">
                <span class="inline-flex px-2 py-0.5 rounded-lg text-xs font-bold bg-purple-50 text-purple-600 border border-purple-100">
                    ${e.role_name}
                </span>
            </td>
            <td class="px-5 py-3 text-center">
                <div class="flex items-center justify-center gap-2">
                    <button onclick="editEmployee(${e.id})" class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition" title="Sửa thông tin">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                    </button>
                    <button onclick="deleteEmployee(${e.id}, '${e.name}')" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition" title="Xóa nhân viên">
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
    const filtered = allEmployees.filter(emp => 
        emp.name.toLowerCase().includes(q) || 
        emp.role_name.toLowerCase().includes(q) ||
        (emp.address && emp.address.toLowerCase().includes(q))
    );
    renderTable(filtered);
};

// ───────── Actions ─────────
document.getElementById('btn-add-employee').onclick = () => {
    document.getElementById('emp-id').value = '';
    document.getElementById('modal-title').textContent = 'Thêm nhân viên mới';
    document.getElementById('btn-submit-employee').textContent = 'Thêm mới';
    
    document.getElementById('emp-name').value = '';
    document.getElementById('emp-phone').value = '';
    document.getElementById('emp-address').value = '';
    
    refreshRoleSelect(null);
    openModal('modal-employee', 'modal-employee-box');
};

function refreshRoleSelect(selectedId = null) {
    const select = document.getElementById('emp-role');
    select.innerHTML = '<option value="">— Chọn chức vụ —</option>';
    ROLES.forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.id; opt.textContent = r.name;
        if (r.id == selectedId) opt.selected = true;
        select.appendChild(opt);
    });
}

function editEmployee(id) {
    const emp = allEmployees.find(x => x.id === id);
    if (!emp) return;

    document.getElementById('emp-id').value = emp.id;
    document.getElementById('modal-title').textContent = 'Chỉnh sửa thông tin';
    document.getElementById('btn-submit-employee').textContent = 'Lưu thay đổi';

    document.getElementById('emp-name').value = emp.name;
    document.getElementById('emp-phone').value = emp.phone || '';
    document.getElementById('emp-address').value = emp.address || '';

    refreshRoleSelect(emp.role_id);
    openModal('modal-employee', 'modal-employee-box');
}

// ───────── Role Actions ─────────
function renderRoleList() {
    const container = document.getElementById('role-list-container');
    container.innerHTML = '';
    
    ROLES.forEach(r => {
        const item = document.createElement('div');
        item.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-2xl group transition hover:bg-white hover:shadow-sm border border-transparent hover:border-gray-100';
        item.innerHTML = `
            <span class="text-sm font-bold text-gray-700">${r.name}</span>
            <button onclick="deleteRole(${r.id}, '${r.name}')" class="p-2 text-gray-300 hover:text-red-600 hover:bg-red-50 rounded-xl transition" title="Xóa chức vụ">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
        `;
        container.appendChild(item);
    });
}

document.getElementById('btn-manage-roles').onclick = () => {
    document.getElementById('new-role-name').value = '';
    renderRoleList();
    openModal('modal-roles', 'modal-roles-box');
};
document.getElementById('btn-close-roles').onclick = () => closeModal('modal-roles', 'modal-roles-box');
document.getElementById('modal-roles-backdrop').onclick = () => closeModal('modal-roles', 'modal-roles-box');

document.getElementById('btn-submit-role').onclick = async () => {
    const name = document.getElementById('new-role-name').value.trim();
    if (!name) { showToast('Vui lòng nhập tên chức vụ', 'warning'); return; }

    try {
        const response = await fetch('/api/employeeRole/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const result = await response.json();
        if (response.ok) {
            showToast('Thêm chức vụ thành công!', 'success');
            ROLES.push({ id: result.id, name: name });
            refreshRoleSelect(result.id);
            renderRoleList();
            document.getElementById('new-role-name').value = '';
        } else {
            showToast(result.message || 'Lỗi khi thêm chức vụ', 'error');
        }
    } catch (err) {
        showToast('Lỗi kết nối server', 'error');
    }
};

async function deleteRole(id, name) {
    showConfirm('Xác nhận xóa', `Bạn có chắc chắn muốn xóa chức vụ "${name}"?`, async () => {
        try {
            const response = await fetch(`/api/employeeRole/delete/${id}`, { method: 'DELETE' });
            const result = await response.json();
            if (response.ok) {
                showToast('Đã xóa chức vụ', 'success');
                const idx = ROLES.findIndex(r => r.id === id);
                if (idx > -1) ROLES.splice(idx, 1);
                renderRoleList();
                refreshRoleSelect();
            } else {
                showToast(result.message || 'Lỗi khi xóa', 'error');
            }
        } catch (err) {
            showToast('Lỗi kết nối server', 'error');
        }
    });
}

document.getElementById('modal-employee-backdrop').onclick = () => closeModal('modal-employee', 'modal-employee-box');

document.getElementById('btn-submit-employee').onclick = async () => {
    const id = document.getElementById('emp-id').value;
    const name = document.getElementById('emp-name').value.trim();
    const phone = document.getElementById('emp-phone').value.trim();
    const address = document.getElementById('emp-address').value.trim();
    const role_id = document.getElementById('emp-role').value;

    if (!name || !role_id) {
        showToast('Vui lòng điền đầy đủ Tên và Chức vụ', 'warning');
        return;
    }

    const payload = { id, name, phone, address, role_id };
    const endpoint = id ? '/api/employee/update' : '/api/employee/add';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (response.ok) {
            showToast(id ? 'Đã cập nhật thông tin!' : 'Thêm nhân viên thành công!', 'success');
            closeModal('modal-employee', 'modal-employee-box');
            fetchEmployees();
        } else {
            showToast(result.message || 'Có lỗi xảy ra', 'error');
        }
    } catch (err) {
        showToast('Lỗi kết nối server', 'error');
    }
};

async function deleteEmployee(id, name) {
    showConfirm('Xác nhận xóa', `Bạn có chắc chắn muốn xóa nhân viên "${name}" không?`, async () => {
        try {
            const response = await fetch(`/api/employee/delete/${id}`, { method: 'DELETE' });
            if (response.ok) {
                showToast('Đã xóa nhân viên', 'success');
                fetchEmployees();
            } else {
                const result = await response.json();
                showToast(result.message || 'Lỗi khi xóa', 'error');
            }
        } catch (err) {
            showToast('Lỗi kết nối server', 'error');
        }
    });
}

// Init
window.onload = () => {
    fetchEmployees();
    refreshRoleSelect();
};
