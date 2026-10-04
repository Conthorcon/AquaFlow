
let allPurchases = [];

document.addEventListener('DOMContentLoaded', () => {
    // Mặc định: Hiển thị tháng hiện tại
    const now = new Date();
    const fMonth = document.getElementById('filter-month');
    const fYear = document.getElementById('filter-year');
    if (fMonth) fMonth.value = now.getMonth() + 1;
    if (fYear) fYear.value = now.getFullYear();
    setFilterMode('time');

    // Initial loads
    fetchPurchaseList();
    loadCategoriesToSelects();

    // Event Listeners
    document.getElementById('search-name').onkeyup = (e) => {
        if (e.key === 'Enter') fetchPurchaseList();
    };
    
    document.getElementById('add-purchase-form').onsubmit = handleAddPurchase;

    // Filter focus listeners
    ['filter-day', 'filter-month', 'filter-year'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.onkeyup = (e) => {
                if (e.key === 'Enter') applyFilter();
            };
        }
    });
});

function setFilterMode(mode) {
    const allBtn = document.getElementById('mode-all');
    const timeBtn = document.getElementById('mode-time');
    const timeInputs = document.getElementById('time-filter-inputs');
    const modeInput = document.getElementById('filter-mode-input');

    modeInput.value = mode;

    if (mode === 'all') {
        if (allBtn) allBtn.className = "px-4 py-2 rounded-lg text-sm font-semibold transition-all bg-white shadow-sm text-blue-600";
        if (timeBtn) timeBtn.className = "px-4 py-2 rounded-lg text-sm font-semibold transition-all text-gray-500 hover:text-gray-700";
        timeInputs.classList.add('opacity-40', 'pointer-events-none');
    } else {
        if (timeBtn) timeBtn.className = "px-4 py-2 rounded-lg text-sm font-semibold transition-all bg-white shadow-sm text-blue-600";
        if (allBtn) allBtn.className = "px-4 py-2 rounded-lg text-sm font-semibold transition-all text-gray-500 hover:text-gray-700";
        timeInputs.classList.remove('opacity-40', 'pointer-events-none');
    }
}

function applyFilter() {
    fetchPurchaseList();
}

async function fetchPurchaseList() {
    const q = document.getElementById('search-name').value;
    const mode = document.getElementById('filter-mode-input').value;
    const day = document.getElementById('filter-day').value;
    const month = document.getElementById('filter-month').value;
    const year = document.getElementById('filter-year').value;
    const category = document.getElementById('filter-category').value;
    
    const tableBody = document.getElementById('purchase-table-body');
    tableBody.innerHTML = `
        <tr>
            <td colspan="4" class="px-8 py-10 text-center">
                <div class="flex flex-col items-center space-y-3">
                    <div class="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span class="text-sm font-bold text-gray-400 uppercase tracking-widest">Đang tải dữ liệu...</span>
                </div>
            </td>
        </tr>
    `;

    try {
        const url = `/api/purchaseList?q=${encodeURIComponent(q)}&mode=${mode}&day=${day}&month=${month}&year=${year}&category=${encodeURIComponent(category)}`;
        const response = await fetch(url);
        const data = await response.json();
        allPurchases = data;
        
        renderTable(data);
        updateStats(data);
    } catch (error) {
        console.error('Error:', error);
        showToast('Không thể tải danh sách đơn mua', 'error');
    }
}

function renderTable(items) {
    const tableBody = document.getElementById('purchase-table-body');
    // const resultCount = document.getElementById('result-count');
    
    tableBody.innerHTML = '';
    // resultCount.textContent = `${items.length} kết quả`;

    if (items.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="px-8 py-10 text-center text-gray-400 font-medium italic">
                    Không tìm thấy đơn hàng nào phù hợp
                </td>
            </tr>
        `;
        return;
    }

    items.forEach((item, index) => {
        const row = document.createElement('tr');
        row.className = "border-b hover:bg-gray-50/60 transition-colors purchase-row";
        
        row.innerHTML = `
            <td class="px-5 py-3 font-semibold text-gray-800 whitespace-nowrap">
                ${item.description}
            </td>
            <td class="px-5 py-3 text-gray-500 text-sm">
                ${item.date}
            </td>
            <td class="px-5 py-3">
                <span class="inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold ${getCategoryClass(item.category)}">
                    ${item.category}
                </span>
            </td>
            <td class="px-5 py-3 text-right font-bold text-blue-700">
                ${item.total_amount.toLocaleString('vi-VN')}đ
            </td>
            <td class="px-5 py-3 text-center">
                <div class="flex items-center justify-center gap-2">
                    <button onclick="editPurchase(${item.id})" class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition" title="Sửa thông tin">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                    </button>
                    <button onclick="deletePurchase(${item.id}, '${item.description}')" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition" title="Xóa đơn hàng">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

function getCategoryClass(cat) {
    switch (cat) {
        case 'Nguyên liệu': return 'bg-amber-100 text-amber-700';
        case 'Văn phòng': return 'bg-purple-100 text-purple-700';
        case 'Vận hành': return 'bg-blue-100 text-blue-700';
        default: return 'bg-gray-100 text-gray-600';
    }
}

function updateStats(items) {
    const totalCount = items.length;
    const totalAmount = items.reduce((sum, item) => sum + item.total_amount, 0);
    const latestDate = items.length > 0 ? items[0].date.split(' ')[0] : '--/--/----';

    document.getElementById('stat-total-count').textContent = totalCount;
    document.getElementById('stat-total-amount').textContent = totalAmount.toLocaleString('vi-VN') + 'đ';
    document.getElementById('stat-latest-date').textContent = latestDate;
}

async function handleAddPurchase(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // UI Loading state
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Đang lưu...';

    const id = document.getElementById('purchase-id').value;
    const endpoint = id ? '/api/purchase/update' : '/api/purchase/add';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast(result.message, 'success');
            closeModal();
            e.target.reset();
            fetchPurchaseList();
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        showToast('Có lỗi xảy ra', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

function editPurchase(id) {
    const item = allPurchases.find(p => p.id === id);
    if (!item) return;

    const m = document.getElementById('modal');
    const mc = document.getElementById('modal-content');
    const form = document.getElementById('add-purchase-form');
    
    // Set Header/Button text
    m.querySelector('h3').textContent = 'Chỉnh sửa đơn mua';
    form.querySelector('button[type="submit"]').textContent = 'Lưu thay đổi';
    
    // Fill data
    document.getElementById('purchase-id').value = item.id;
    form.description.value = item.description;
    form.total_amount.value = item.total_amount;
    form.category.value = item.category;
    
    openModal();
}

function deletePurchase(id, description) {
    showConfirm('Xác nhận xóa', `Bạn có chắc chắn muốn xóa đơn nhập hàng "${description}"?`, async () => {
        try {
            const response = await fetch(`/api/purchase/delete/${id}`, { method: 'DELETE' });
            const result = await response.json();
            if (result.status === 'success') {
                showToast('Đã xóa đơn mua hàng', 'success');
                fetchPurchaseList();
            } else {
                showToast(result.message, 'error');
            }
        } catch (error) {
            showToast('Lỗi kết nối server', 'error');
        }
    });
}

function showConfirm(title, message, onConfirm) {
    const el = document.getElementById('modal-confirm');
    const box = document.getElementById('modal-confirm-box');
    document.getElementById('modal-confirm-title').textContent = title;
    document.getElementById('modal-confirm-message').textContent = message;
    
    document.getElementById('modal-confirm-ok').onclick = () => {
        closeConfirmModal();
        onConfirm();
    };
    document.getElementById('modal-confirm-cancel').onclick = closeConfirmModal;
    document.getElementById('modal-confirm-backdrop').onclick = closeConfirmModal;
    
    el.classList.remove('hidden');
    setTimeout(() => {
        box.classList.remove('scale-95', 'opacity-0');
        box.classList.add('scale-100', 'opacity-100');
    }, 10);
}

function closeConfirmModal() {
    const el = document.getElementById('modal-confirm');
    const box = document.getElementById('modal-confirm-box');
    box.classList.remove('scale-100', 'opacity-100');
    box.classList.add('scale-95', 'opacity-0');
    setTimeout(() => el.classList.add('hidden'), 250);
}

function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-msg');
    const toastIcon = document.getElementById('toast-icon');
    
    toastMsg.textContent = msg;
    if (type === 'success') {
        toastIcon.textContent = '✓';
        toastIcon.className = 'w-8 h-8 rounded-lg flex items-center justify-center font-bold bg-green-500 text-white';
        toast.className = toast.className.replace('bg-red-500', 'bg-gray-900');
    } else {
        toastIcon.textContent = '!';
        toastIcon.className = 'w-8 h-8 rounded-lg flex items-center justify-center font-bold bg-white text-red-600';
        toast.className = toast.className.replace('bg-gray-900', 'bg-red-500');
    }

    toast.classList.remove('hidden', 'translate-y-20');
    toast.classList.add('translate-y-0');
    
    setTimeout(() => {
        toast.classList.add('translate-y-20');
        setTimeout(() => toast.classList.add('hidden'), 500);
    }, 3000);
}

// Category Management Functions
async function loadCategoriesToSelects() {
    try {
        const response = await fetch('/api/purchaseCategories');
        const categories = await response.json();
        
        const filterSelect = document.getElementById('filter-category');
        const formSelect = document.getElementById('form-category');
        
        const optionsHtml = categories.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
        
        filterSelect.innerHTML = '<option value="">Tất cả phân loại</option>' + optionsHtml;
        formSelect.innerHTML = optionsHtml;
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadCategoriesForManagement() {
    try {
        const response = await fetch('/api/purchaseCategories');
        const categories = await response.json();
        const listEl = document.getElementById('category-list');
        
        listEl.innerHTML = categories.map(c => `
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-2xl group transition-all hover:bg-white hover:shadow-md border border-transparent hover:border-gray-100">
                <span class="font-bold text-gray-700">${c.name}</span>
                <button onclick="deleteCategory(${c.id}, '${c.name}')" class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
            </div>
        `).join('') || '<p class="text-center py-4 text-gray-400 italic">Chưa có phân loại nào</p>';
    } catch (error) {
        console.error('Error loading management categories:', error);
    }
}

async function addCategory() {
    const nameInput = document.getElementById('new-category-name');
    const name = nameInput.value.trim();
    if (!name) return;

    try {
        const response = await fetch('/api/purchaseCategory/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast('Đã thêm phân loại mới');
            nameInput.value = '';
            loadCategoriesForManagement();
            loadCategoriesToSelects();
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        showToast('Không thể kết nối máy chủ', 'error');
    }
}

async function deleteCategory(id, name) {
    showConfirm('Xác nhận xóa', `Bạn có chắc chắn muốn xóa phân loại "${name}"?`, async () => {
        try {
            const response = await fetch(`/api/purchaseCategory/delete/${id}`, { method: 'DELETE' });
            const result = await response.json();
            
            if (result.status === 'success') {
                showToast('Đã xóa phân loại');
                loadCategoriesForManagement();
                loadCategoriesToSelects();
            } else {
                showToast(result.message, 'error');
            }
        } catch (error) {
            showToast('Lỗi kết nối máy chủ', 'error');
        }
    });
}
