// [Sidebar]

function toggleSidebar() {
const sidebar = document.getElementById('sidebar');
const openBtn = document.getElementById('openSidebar');

if (sidebar.classList.contains('w-64')) {
    sidebar.classList.remove('w-64', 'p-4');
    // sidebar.classList.add('w-0', 'hidden', 'p-0');
    sidebar.classList.add('w-0', 'overflow-hidden', 'p-0');
    openBtn.classList.remove('hidden');
} else {
    // sidebar.classList.remove('w-0', 'hidden', 'p-0');
    sidebar.classList.remove('w-0', 'overflow-hidden', 'p-0');
    sidebar.classList.add('w-64', 'p-4');
    openBtn.classList.add('hidden');
}
}

// ===================================================================
// [MODAL UI SYSTEM]
// ===================================================================

const ICONS = {
    error: {
        bg: 'bg-red-100',
        svg: `<svg class="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>`
    },
    warning: {
        bg: 'bg-amber-100',
        svg: `<svg class="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
              </svg>`
    },
    success: {
        bg: 'bg-green-100',
        svg: `<svg class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
              </svg>`
    },
    delete: {
        bg: 'bg-red-100',
        svg: `<svg class="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>`
    },
    info: {
        bg: 'bg-blue-100',
        svg: `<svg class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>`
    }
};

const CONFIRM_BTN_COLORS = {
    error:   'bg-red-600 hover:bg-red-700',
    warning: 'bg-amber-500 hover:bg-amber-600',
    success: 'bg-green-600 hover:bg-green-700',
    delete:  'bg-red-600 hover:bg-red-700',
    info:    'bg-blue-600 hover:bg-blue-700'
};

function _openModal(el, box) {
    el.classList.remove('hidden');
    requestAnimationFrame(() => {
        box.classList.remove('scale-95', 'opacity-0');
        box.classList.add('scale-100', 'opacity-100');
    });
}

function _closeModal(el, box, cb) {
    box.classList.remove('scale-100', 'opacity-100');
    box.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
        el.classList.add('hidden');
        if (cb) cb();
    }, 250);
}

/**
 * showAlert — hiện modal thông báo 1 nút OK
 * @param {string} title
 * @param {string} message
 * @param {'error'|'warning'|'success'|'info'} type
 */
function showAlert(title, message, type = 'warning') {
    const el  = document.getElementById('modal-alert');
    const box = document.getElementById('modal-alert-box');
    const icon = document.getElementById('modal-alert-icon');
    document.getElementById('modal-alert-title').textContent   = title;
    document.getElementById('modal-alert-message').textContent = message;

    icon.className = `flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${ICONS[type].bg}`;
    icon.innerHTML = ICONS[type].svg;

    _openModal(el, box);

    const okBtn = document.getElementById('modal-alert-ok');
    const close = () => _closeModal(el, box);
    // Remove old listeners
    const newOk = okBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newOk, okBtn);
    newOk.addEventListener('click', close);
    document.getElementById('modal-alert-backdrop').onclick = close;
}

/**
 * showConfirm — hiện modal xác nhận 2 nút (Hủy / Xác nhận)
 * @param {object} opts
 *   title, message, type, detailLines (array of strings), confirmText, onConfirm
 */
function showConfirm({ title, message, type = 'info', detailLines = [], confirmText = 'Xác nhận', onConfirm }) {
    const el  = document.getElementById('modal-confirm');
    const box = document.getElementById('modal-confirm-box');
    const icon = document.getElementById('modal-confirm-icon');
    const detailEl = document.getElementById('modal-confirm-detail');
    const confirmOkBtn = document.getElementById('modal-confirm-ok');

    document.getElementById('modal-confirm-title').textContent   = title;
    document.getElementById('modal-confirm-message').textContent = message;

    icon.className = `flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${ICONS[type].bg}`;
    icon.innerHTML = ICONS[type].svg;

    // Nút xác nhận màu theo type
    confirmOkBtn.className = `px-5 py-2 rounded-xl text-sm font-semibold text-white transition-all duration-200 active:scale-95 ${CONFIRM_BTN_COLORS[type] || CONFIRM_BTN_COLORS.info}`;
    confirmOkBtn.textContent = confirmText;

    // Detail box
    if (detailLines.length > 0) {
        detailEl.innerHTML = detailLines.map(l => `<div class="flex gap-2"><span class="text-gray-400">•</span><span>${l}</span></div>`).join('');
        detailEl.classList.remove('hidden');
    } else {
        detailEl.innerHTML = '';
        detailEl.classList.add('hidden');
    }

    _openModal(el, box);

    const close = () => _closeModal(el, box);

    // Clone để xóa listener cũ
    const newOk     = confirmOkBtn.cloneNode(true);
    const cancelBtn = document.getElementById('modal-confirm-cancel');
    const newCancel = cancelBtn.cloneNode(true);
    confirmOkBtn.parentNode.replaceChild(newOk, confirmOkBtn);
    cancelBtn.parentNode.replaceChild(newCancel, cancelBtn);

    newOk.addEventListener('click', () => { close(); if (onConfirm) onConfirm(); });
    newCancel.addEventListener('click', close);
    document.getElementById('modal-confirm-backdrop').onclick = close;
}

/**
 * showToast — hiện thông báo thoáng góc trên phải
 * @param {string} message
 * @param {'success'|'error'|'warning'|'info'} type
 * @param {number} duration ms
 */
function showToast(message, type = 'success', duration = 3000) {
    const COLOR_MAP = {
        success: 'bg-green-600',
        error:   'bg-red-600',
        warning: 'bg-amber-500',
        info:    'bg-blue-600'
    };
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl text-white text-sm font-medium shadow-xl
        ${COLOR_MAP[type] || COLOR_MAP.info}
        transform translate-x-8 opacity-0 transition-all duration-300 max-w-xs`;
    toast.innerHTML = `
        <span class="flex-shrink-0">${ICONS[type].svg.replace(/text-\w+-500/, 'text-white')}</span>
        <span>${message}</span>
    `;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-8', 'opacity-0');
        toast.classList.add('translate-x-0', 'opacity-100');
    });

    setTimeout(() => {
        toast.classList.add('translate-x-8', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}


// [UTILS]
function removeVietnameseTones(str) {
    str = str.replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, "a");
    str = str.replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, "e");
    str = str.replace(/ì|í|ị|ỉ|ĩ/g, "i");
    str = str.replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, "o");
    str = str.replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, "u");
    str = str.replace(/ỳ|ý|ỵ|ỷ|ỹ/g, "y");
    str = str.replace(/đ/g, "d");
    str = str.replace(/À|Á|Ạ|Ả|Ã|Â|Ầ|Ấ|Ậ|Ẩ|Ẫ|Ă|Ằ|Ắ|Ặ|Ẳ|Ẵ/g, "A");
    str = str.replace(/È|É|Ẹ|Ẻ|Ẽ|Ê|Ề|Ế|Ệ|Ể|Ễ/g, "E");
    str = str.replace(/Ì|Í|Ị|Ỉ|Ĩ/g, "I");
    str = str.replace(/Ò|Ó|Ọ|Ỏ|Õ|Ô|Ồ|Ố|Ộ|Ổ|Ỗ|Ơ|Ờ|Ớ|Ợ|Ở|Ỡ/g, "O");
    str = str.replace(/Ù|Ú|Ụ|Ủ|Ũ|Ư|Ừ|Ứ|Ự|Ử|Ữ/g, "U");
    str = str.replace(/Ỳ|Ý|Ỵ|Ỷ|Ỹ/g, "Y");
    str = str.replace(/Đ/g, "D");
    // Loại bỏ các dấu phụ khác (dấu hỏi, ngã, nặng...) nếu có lỗi encoding
    str = str.normalize('NFD').replace(/[\u0300-\u036f]/g, "");
    return str;
}


// [Customer Search]

// Lưu trữ dữ liệu từ API
let customerDatabase = [];
let productDatabase = [];
// Lưu trữ nhóm khách hàng hiện tại (mặc định 1 - Khách lẻ)
let currentCustomerGroupId = 1;
// Cờ đánh dấu khách hàng mới
let isNewCustomer = false;

// Giả lập lịch sử tìm kiếm
let recentSearches = JSON.parse(localStorage.getItem('recentCustomerSearches') || '[]'); 


const input = document.getElementById('customer-input');
const inputPhone = document.getElementById('customer-phone');
const inputAddress = document.getElementById('customer-address');

const list = document.getElementById('suggestion-list');
const tagContainer = document.getElementById('selected-tag');
const tagText = document.getElementById('tag-text');
const removeTagBtn = document.getElementById('remove-tag');
const inputContainer = document.getElementById('input-container');


// Hàm khi chọn một khách hàng
function selectCustomer(customer, isNew = false) {
    isNewCustomer = isNew;

    // 1. Hiển thị Tag
    tagText.textContent = customer.name;
    tagContainer.classList.remove('hidden');
    tagContainer.classList.add('flex');

    // 2. Điền thông tin phụ & Xử lý quyền chỉnh sửa
    inputPhone.value = customer.phone || "";
    inputAddress.value = customer.address || "";
    currentCustomerGroupId = customer.group_id || 1;

    if (isNewCustomer) {
        inputPhone.readOnly = false;
        inputAddress.readOnly = false;
        inputPhone.classList.remove('bg-gray-50', 'text-gray-500', 'cursor-not-allowed');
        inputAddress.classList.remove('bg-gray-50', 'text-gray-500', 'cursor-not-allowed');
        inputPhone.placeholder = "Nhập số điện thoại (Bắt buộc)";
        inputAddress.placeholder = "Nhập địa chỉ (Bắt buộc)";
        inputPhone.focus();
    } else {
        inputPhone.readOnly = true;
        inputAddress.readOnly = true;
        inputPhone.classList.add('bg-gray-50', 'text-gray-500', 'cursor-not-allowed');
        inputAddress.classList.add('bg-gray-50', 'text-gray-500', 'cursor-not-allowed');
        inputPhone.placeholder = "Chưa có dữ liệu...";
        inputAddress.placeholder = "Chưa có dữ liệu...";
    }

    // 3. Ẩn/Xóa text trong input và ẩn placeholder
    input.value = customer.name;
    input.placeholder = "";
    input.classList.add('hidden'); 

    // 4. Đóng danh sách
    list.classList.add('hidden');
    
    // Lưu vào lịch sử nếu không phải khách mới hoàn toàn (để tránh rác)
    if (!isNewCustomer) addToHistory(customer.name);

    // 5. Mở khóa phần chọn sản phẩm
    const prodTrigger = document.getElementById('product-trigger');
    prodTrigger.classList.remove('bg-gray-50', 'cursor-not-allowed', 'opacity-50', 'pointer-events-none');
    prodTrigger.classList.add('bg-white', 'cursor-pointer', 'hover:border-blue-400');
    prodTrigger.title = "";
    document.getElementById('product-display-text').textContent = "Bấm để thêm sản phẩm...";
}

// Hàm khi bấm vào dấu X để xóa Tag
removeTagBtn.onclick = function() {
    isNewCustomer = false;
    tagContainer.classList.add('hidden');
    tagContainer.classList.remove('flex');
    input.value = "";
    input.classList.remove('hidden');
    input.placeholder = "Bên mua (Tên khách hàng)";
    input.focus();

    // Reset thông tin phụ & Khóa lại
    inputPhone.value = "";
    inputAddress.value = "";
    inputPhone.readOnly = true;
    inputAddress.readOnly = true;
    inputPhone.classList.add('bg-gray-50', 'text-gray-500', 'cursor-not-allowed');
    inputAddress.classList.add('bg-gray-50', 'text-gray-500', 'cursor-not-allowed');
    currentCustomerGroupId = 1;

    // Khóa lại phần chọn sản phẩm & Xóa sản phẩm cũ (để tránh sai giá nhóm)
    const prodTrigger = document.getElementById('product-trigger');
    prodTrigger.classList.add('bg-gray-50', 'cursor-not-allowed', 'opacity-50', 'pointer-events-none');
    prodTrigger.classList.remove('bg-white', 'cursor-pointer', 'hover:border-blue-400');
    prodTrigger.title = "Vui lòng chọn khách hàng trước";
    document.getElementById('product-display-text').textContent = "Thêm sản phẩm & số lượng...";
    
    // Clear products list and total
    tagsDisplay.innerHTML = "";
    document.getElementById('total-amount-input').value = "";
};

function showList(items, isHistory = false) {
    list.innerHTML = "";
    const currentValue = input.value.trim();

    if (items.length > 0) {
        const header = document.createElement('li');
        header.className = "p-2 text-xs font-bold text-gray-400 bg-gray-50 uppercase";
        header.textContent = isHistory ? "Tìm kiếm gần đây" : "Kết quả tìm thấy";
        list.appendChild(header);
    }

    items.forEach(customer => {
        const li = document.createElement('li');
        li.className = "p-3 hover:bg-blue-50 cursor-pointer text-sm border-b last:border-b-0";
        li.innerHTML = `
            <div class="font-medium">${customer.name}</div>
            <div class="text-xs text-gray-400">${customer.phone || 'Không có SĐT'} - ${customer.address || 'Không có địa chỉ'}</div>
        `;
        li.onclick = () => selectCustomer(customer, false);
        list.appendChild(li);
    });

    // Thêm mới
    if (currentValue !== "" && !customerDatabase.some(c => c.name === currentValue)) {
        const addNewLi = document.createElement('li');
        addNewLi.className = "p-3 text-blue-600 hover:bg-gray-50 cursor-pointer font-medium text-sm border-t";
        addNewLi.innerHTML = `+ Thêm mới: "${currentValue}"`;
        addNewLi.onclick = () => {
            const newCustomer = { name: currentValue, phone: "", address: "", group_id: 1 };
            selectCustomer(newCustomer, true); // Đánh dấu là khách mới
        };
        list.appendChild(addNewLi);
    }

    if (list.children.length > 0) list.classList.remove('hidden');
}

inputContainer.onclick = () => {
    if (!tagContainer.classList.contains('hidden')) return;
    input.focus();
};

function addToHistory(name) {
    recentSearches = [name, ...recentSearches.filter(i => i !== name)].slice(0, 3);
    localStorage.setItem('recentCustomerSearches', JSON.stringify(recentSearches));
}

function renderSearch(val) {
    const currentValue = val.trim();
    
    fetch('/api/customerList')
    .then(response => response.json())
    .then(data => {
        customerDatabase = data;
        
        if (currentValue === "") {
            // Hiển thị lịch sử (cần map ngược từ tên sang object)
            const historyObjs = recentSearches.map(name => 
                customerDatabase.find(c => c.name === name) || {name, phone: "", address: "", group_id: 1}
            );
            showList(historyObjs, true);
            return;
        }

        const normalizedQuery = removeVietnameseTones(currentValue).toLowerCase();
        const filtered = customerDatabase.filter(customer => 
            removeVietnameseTones(customer.name).toLowerCase().includes(normalizedQuery)
        );

        showList(filtered, false);
    });
}

input.addEventListener('focus', () => renderSearch(input.value));
input.addEventListener('input', (e) => renderSearch(e.target.value));

document.addEventListener('click', (e) => {
    // Đóng danh sách gợi ý khách hàng
    if (!document.getElementById('customer-search-container').contains(e.target)) {
        list.classList.add('hidden');
    }
    // Đóng popup thêm sản phẩm
    const productLogicContainer = document.getElementById('product-logic-container');
    if (productLogicContainer && !productLogicContainer.contains(e.target)) {
        const productPopup = document.getElementById('product-popup');
        if (productPopup) productPopup.classList.add('hidden');
    }
});


// [Product Logic]

const productTrigger = document.getElementById('product-trigger');
const productPopup = document.getElementById('product-popup');
const popNameInput = document.getElementById('pop-product-name');
const popQtyInput = document.getElementById('pop-product-qty');
const popAddBtn = document.getElementById('pop-add-btn');
const tagsDisplay = document.getElementById('product-tags-display');

const tagProduct = document.getElementById('tag-product');
const selectedTagProduct = document.getElementById('selected-tag-product');
const removeTagProduct = document.getElementById('remove-tag-product');

const popPriceDisplay = document.getElementById('pop-product-price');
const popSuggestionList = document.getElementById('pop-suggestion-list');

// Lưu giá hiện tại của sản phẩm đang chọn trong popup
let currentPopPrice = 0;

productTrigger.onclick = (e) => {
    productPopup.classList.toggle('hidden');
    if (!productPopup.classList.contains('hidden')) {
        popNameInput.focus();
    }
};

popAddBtn.onclick = () => {
    const name = popNameInput.value.trim();
    const qty = parseInt(popQtyInput.value) || 1;
    const price = parseInt(popPriceDisplay.value) || 0; // Đọc từ input thay vì biến global

    if (name === "") {
        showAlert("Thiếu thông tin", "Vui lòng nhập hoặc chọn tên sản phẩm trước khi thêm.", "warning");
        return;
    }

    createProductTag(name, qty, price);

    // Tự động cập nhật tổng tiền
    updateTotalAmount(qty * price);

    // Reset popup
    selectedTagProduct.classList.add('hidden');
    popNameInput.classList.remove('hidden');
    popNameInput.value = "";
    popQtyInput.value = 1;
    popPriceDisplay.value = 0; // Reset input về 0
    currentPopPrice = 0;
    productPopup.classList.add('hidden');
};

function createProductTag(name, qty, price) {
    const tag = document.createElement('div');
    tag.className = "flex items-center bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full text-sm border border-blue-200 shadow-sm";
    tag.dataset.totalPrice = qty * price;
    tag.innerHTML = `
        <span class="font-bold mr-1">${qty}x</span>
        <span>${name}</span>
        <button class="ml-2 text-blue-400 hover:text-red-500 font-bold" onclick="removeProductTag(this)">&times;</button>
    `;
    tagsDisplay.appendChild(tag);
}

function removeProductTag(btn) {
    const tag = btn.parentElement;
    const priceToRemove = parseInt(tag.dataset.totalPrice) || 0;
    updateTotalAmount(-priceToRemove);
    tag.remove();
}

function updateTotalAmount(delta) {
    const amountInput = document.getElementById('total-amount-input');
    let currentTotal = parseInt(amountInput.value.replace(/,/g, '')) || 0;
    currentTotal += delta;
    if (currentTotal < 0) currentTotal = 0;
    
    if (currentTotal === 0) {
        amountInput.value = ""; // Show placeholder "Thành tiền"
    } else {
        amountInput.value = currentTotal.toLocaleString('en-US');
    }
}

function selectProduct(product, price) {
    tagProduct.textContent = product.name;
    selectedTagProduct.classList.remove('hidden');
    selectedTagProduct.classList.add('flex');
    popQtyInput.focus();

    popPriceDisplay.value = price; 
    // popPriceDisplay.value = 0; 
    currentPopPrice = price;

    popNameInput.value = product.name;
    popNameInput.classList.add('hidden'); 
    popSuggestionList.classList.add('hidden');
}

removeTagProduct.onclick = function() {
    selectedTagProduct.classList.add('hidden');
    selectedTagProduct.classList.remove('flex');
    popNameInput.value = "";
    popNameInput.classList.remove('hidden');
    popNameInput.placeholder = "Nhập hoặc chọn tên...";
    popNameInput.focus();
    popPriceDisplay.value = 0;
    currentPopPrice = 0;
};

function renderPopSuggestions(val) {
    popSuggestionList.innerHTML = "";
    const query = removeVietnameseTones(val.trim().toLowerCase());

    if (query === "") {
        popSuggestionList.classList.add('hidden');
        return;
    }

    const filtered = productDatabase.filter(product => 
        removeVietnameseTones(product.name).toLowerCase().includes(query)
    ).slice(0, 5);

    if (filtered.length > 0) {
        filtered.forEach(product => {
            const li = document.createElement('li');
            li.className = "p-2 hover:bg-blue-50 cursor-pointer text-sm border-b last:border-b-0 flex justify-between";
            const price = (product.prices && product.prices[currentCustomerGroupId]) || 0;
            li.innerHTML = `
                <span>${product.name}</span>
                <span class="text-xs text-blue-500 font-bold">${price > 0 ? price.toLocaleString('en-US') + 'đ' : 'Chưa có giá'}</span>
            `;
            if (price > 0) {
                li.onclick = () => selectProduct(product, price);
            } else {
                li.classList.add('opacity-50', 'cursor-not-allowed');
                li.title = "Sản phẩm này chưa được cấu hình giá cho nhóm khách này";
            }
            popSuggestionList.appendChild(li);
        });
        popSuggestionList.classList.remove('hidden');
    } else {
        const noResult = document.createElement('li');
        noResult.className = "p-2 text-xs text-gray-400 italic";
        noResult.textContent = "Không tìm thấy sản phẩm";
        popSuggestionList.appendChild(noResult);
        popSuggestionList.classList.remove('hidden');
    }
}

popNameInput.addEventListener('input', (e) => {
    if (productDatabase.length === 0) {
        fetch('/api/productList')
        .then(response => response.json())
        .then(data => {
            productDatabase = data;
            renderPopSuggestions(e.target.value);
        });
    } else {
        renderPopSuggestions(e.target.value);
    }
});

popNameInput.addEventListener('keydown', (e) => {
    if (e.key === "Escape") popSuggestionList.classList.add('hidden');
});


// [Total Amount Logic]
const taxInput = document.getElementById('tax-input');
const amountInput = document.getElementById('total-amount-input');
const noteInput = document.getElementById('note-input')
const makeOrderButton = document.getElementById('make-order-button');

const allowOnlyNumbers = (e) => {
    e.target.value = e.target.value.replace(/[^0-9]/g, '');
};

amountInput.addEventListener('input', (e) => {
    allowOnlyNumbers(e);
    let value = e.target.value.replace(/,/g, '');
    if (value !== "") e.target.value = Number(value).toLocaleString('en-US');
});

taxInput.addEventListener('input', allowOnlyNumbers);
taxInput.addEventListener('blur', (e) => {
    let value = e.target.value.replace('%', '');
    if (value !== '') e.target.value = value + '%';
});
taxInput.addEventListener('focus', (e) => {
    e.target.value = e.target.value.replace('%', '');
});

function getSelectedProducts() {
    const products = [];
    const tags = tagsDisplay.querySelectorAll('div');

    tags.forEach(tag => {
        const spans = tag.querySelectorAll('span');
        const qtyText = spans[0].textContent.replace('x', '');
        const productName = spans[1].textContent;
        // Tính giá đơn vị từ dataset (dataset.totalPrice / qty)
        const totalPrice = parseInt(tag.dataset.totalPrice) || 0;
        const qty = parseInt(qtyText) || 1;

        products.push({
            name: productName,
            quantity: qty,
            price: totalPrice / qty 
        });
    });

    return products;
}

makeOrderButton.addEventListener('click', () => {
    const productAmount = tagsDisplay.childElementCount;
    const customerName = tagText.textContent.trim();

    // Kiểm tra bắt buộc: khách hàng và ít nhất 1 sản phẩm
    if (!customerName) {
        showAlert("Thiếu thông tin", "Vui lòng chọn hoặc nhập tên khách hàng trước khi tạo đơn.", "warning");
        return;
    }
    if (productAmount === 0) {
        showAlert("Thiếu sản phẩm", "Vui lòng thêm ít nhất một sản phẩm vào đơn hàng.", "warning");
        return;
    }

    // Kiểm tra thông tin bắt buộc cho khách hàng mới
    if (isNewCustomer) {
        const phone = inputPhone.value.trim();
        const address = inputAddress.value.trim();
        if (!phone || !address) {
            showAlert("Khách hàng mới", "Vì đây là khách hàng mới, vui lòng nhập đầy đủ Số điện thoại và Địa chỉ.", "warning");
            return;
        }
    }

    // Xác nhận trước khi tạo
    const totalText = amountInput.value || "0";
    showConfirm({
        title: "Xác nhận tạo đơn hàng",
        message: "Kiểm tra lại thông tin bên dưới trước khi tạo đơn.",
        type: "info",
        detailLines: [
            `Khách hàng: <strong>${customerName}</strong>`,
            `Số loại sản phẩm: <strong>${productAmount}</strong>`,
            `Thành tiền: <strong>${totalText} VNĐ`
        ],
        confirmText: "Tạo đơn",
        onConfirm: () => submitOrder()
    });
});

function submitOrder() {
    const customerName = tagText.textContent.trim();
    const data = {
        totalAmount: amountInput.value.replace(/,/g, ''),
        tax: taxInput.value.replace('%', ''),
        customerName: customerName,
        customerPhone: inputPhone.value,
        customerAddress: inputAddress.value,
        productList: getSelectedProducts(),
        note: noteInput.value
    };

    fetch('/api/addSales', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === "success") {
            window.location.href = result.redirect_url;
        } else {
            showAlert("Lỗi tạo đơn", result.message, "error");
        }
    })
    .catch(error => console.error('Error:', error));
}


// [Global Tooltip Portal]
document.addEventListener('DOMContentLoaded', () => {
    const portal = document.getElementById('tooltip-portal');
    const tooltipBody = document.getElementById('tooltip-body');
    const portalContent = document.getElementById('tooltip-content');

    if (!portal) return;

    document.addEventListener('mouseover', (e) => {
        const trigger = e.target.closest('.js-tooltip-trigger');
        if (!trigger) return;

        const template = trigger.querySelector('.tooltip-template');
        if (!template) return;

        tooltipBody.innerHTML = template.innerHTML;
        const rect = trigger.getBoundingClientRect();
        
        portal.classList.remove('hidden');
        const portalRect = portalContent.getBoundingClientRect();

        let top = rect.top - portalRect.height - 12;
        let left = rect.left + (rect.width / 2) - (portalRect.width / 2);

        if (top < 10) top = 10;
        if (left < 10) left = 10;
        if (left + portalRect.width > window.innerWidth - 10) {
            left = window.innerWidth - portalRect.width - 10;
        }

        portal.style.top = `${top}px`;
        portal.style.left = `${left}px`;

        requestAnimationFrame(() => {
            portal.style.opacity = '1';
        });
    });

    document.addEventListener('mouseout', (e) => {
        const trigger = e.target.closest('.js-tooltip-trigger');
        if (!trigger) return;

        portal.style.opacity = '0';
        setTimeout(() => {
            if (portal.style.opacity === '0') {
                portal.classList.add('hidden');
            }
        }, 200);
    });
});

// [Quick Actions]
function toggleStatus(id, newStatus) {
    fetch('/api/sale/update_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id, status: newStatus })
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === "success") {
            window.location.reload();
        } else {
            showAlert("Lỗi cập nhật", result.message, "error");
        }
    })
    .catch(error => console.error('Error:', error));
}

function assignDelivery(id, employeeId) {
    fetch('/api/sale/assign_delivery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id, employee_id: employeeId })
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === "success") {
            window.location.reload();
        } else {
            showAlert("Lỗi gán nhân viên", result.message, "error");
        }
    })
    .catch(error => console.error('Error:', error));
}

function deleteSale(id, customerName) {
    showConfirm({
        title: "Xóa đơn hàng",
        message: "Hành động này không thể hoàn tác. Bạn có chắc muốn xóa đơn hàng này?",
        type: "delete",
        detailLines: [`Khách hàng: <strong>${customerName}</strong>`],
        confirmText: "Xóa đơn",
        onConfirm: () => {
            fetch(`/api/sale/${id}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(result => {
                if (result.status === "success") {
                    showToast("Đã xóa đơn hàng thành công", "success");
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showAlert("Lỗi khi xóa", result.message, "error");
                }
            })
            .catch(error => console.error('Error:', error));
        }
    });
}
// [Filter Logic]
function setFilterMode(mode) {
    document.getElementById('filter-mode-input').value = mode;
    
    const modeDefaultBtn = document.getElementById('mode-default');
    const modeTimeBtn = document.getElementById('mode-time');
    const timeInputs = document.getElementById('time-filter-inputs');

    if (mode === 'default') {
        modeDefaultBtn.classList.add('bg-white', 'shadow-sm', 'text-blue-600');
        modeDefaultBtn.classList.remove('text-gray-500', 'hover:text-gray-700');
        
        modeTimeBtn.classList.remove('bg-white', 'shadow-sm', 'text-blue-600');
        modeTimeBtn.classList.add('text-gray-500', 'hover:text-gray-700');
        
        timeInputs.classList.add('opacity-30', 'pointer-events-none');
        timeInputs.classList.remove('opacity-100');
    } else {
        modeTimeBtn.classList.add('bg-white', 'shadow-sm', 'text-blue-600');
        modeTimeBtn.classList.remove('text-gray-500', 'hover:text-gray-700');
        
        modeDefaultBtn.classList.remove('bg-white', 'shadow-sm', 'text-blue-600');
        modeDefaultBtn.classList.add('text-gray-500', 'hover:text-gray-700');
        
        timeInputs.classList.remove('opacity-30', 'pointer-events-none');
        timeInputs.classList.add('opacity-100');
    }
}

function applyFilter() {
    const mode = document.getElementById('filter-mode-input').value;
    const day = document.getElementById('filter-day').value;
    const month = document.getElementById('filter-month').value;
    const year = document.getElementById('filter-year').value;

    let url = `/sale?mode=${mode}`;
    if (day) url += `&day=${day}`;
    if (month) url += `&month=${month}`;
    if (year) url += `&year=${year}`;

    window.location.href = url;
}

function showHelp() {
    showAlert("Thông tin hỗ trợ", "Vui lòng liên hệ:\nKỹ thuật viên: Trương Trần Phương Khanh\nSố điện thoại: 0912 345 678", "info");
}

// ===================================================================
// [IMPORT SYSTEM: OCR & CSV]
// ===================================================================

let IMPORT_CACHE = {
    customers: [],
    products: []
};

function openImportModal() {
    const el = document.getElementById('modal-import-review');
    const box = document.getElementById('modal-import-box');
    _openModal(el, box);
}

function closeImportModal() {
    const el = document.getElementById('modal-import-review');
    const box = document.getElementById('modal-import-box');
    _closeModal(el, box);
}

document.getElementById('btn-import-file').addEventListener('click', () => {
    document.getElementById('import-file-input').click();
});

document.getElementById('import-file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Hiển thị loading (nếu có) - ở đây dùng Toast tạm
    showToast("Đang xử lý dữ liệu, vui lòng đợi...", "info");

    const formData = new FormData();
    formData.append('file', file);

    try {
        // Fetch data cho dropdowns trước khi hiện modal (nếu chưa có)
        if (IMPORT_CACHE.customers.length === 0) {
            const [cRes, pRes] = await Promise.all([
                fetch('/api/customerList').then(r => r.json()),
                fetch('/api/productList').then(r => r.json())
            ]);
            IMPORT_CACHE.customers = cRes;
            IMPORT_CACHE.products = pRes;
        }

        const res = await fetch('/api/sale/extract', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.status === 'error') {
            showAlert("Lỗi xử lý", data.message, "error");
            return;
        }

        renderImportReview(data);
        openImportModal();
    } catch (err) {
        showAlert("Lỗi hệ thống", "Không thể trích xuất dữ liệu: " + err.message, "error");
    } finally {
        e.target.value = ''; // Reset input
    }
});

function renderImportReview(data) {
    const custInput = document.getElementById('reviewed-customer-name');
    const custSelect = document.getElementById('reviewed-customer-match');
    const tableBody = document.getElementById('import-review-body');
    const msg = document.getElementById('extraction-msg');

    // 1. Render Customer
    custInput.value = data.customer ? data.customer.name : "Không tìm thấy";
    
    // Tạo danh sách dropdown khách hàng
    custSelect.innerHTML = '<option value="">-- Chọn khách hàng --</option>';
    IMPORT_CACHE.customers.forEach(c => {
        const selected = (data.customer && data.customer.id === c.id) ? 'selected' : '';
        custSelect.innerHTML += `<option value="${c.id}" ${selected}>${c.name}</option>`;
    });

    // 2. Render Items
    tableBody.innerHTML = '';
    data.items.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.className = "border-b hover:bg-gray-50/50 transition";
        
        let productOptions = '<option value="">-- Chọn sản phẩm --</option>';
        IMPORT_CACHE.products.forEach(p => {
            const pName = `${p.name} ${p.cap_type} ${p.bottle_type} ${p.capacity}`.trim();
            const selected = (item.id === p.id) ? 'selected' : '';
            productOptions += `<option value="${p.id}" ${selected}>${pName}</option>`;
        });

        tr.innerHTML = `
            <td class="px-6 py-4 font-medium text-gray-500">${item.name}</td>
            <td class="px-6 py-4">
                <select class="w-full border border-gray-200 p-2 rounded-lg text-xs outline-none focus:border-indigo-400 row-product-select">
                    ${productOptions}
                </select>
            </td>
            <td class="px-6 py-4 text-center">
                <input type="number" class="w-16 border border-gray-200 p-2 rounded-lg text-center text-xs outline-none row-qty-input" value="${item.qty}" min="1" />
            </td>
            <td class="px-6 py-4 text-center">
                <button onclick="this.closest('tr').remove()" class="p-2 text-red-300 hover:text-red-500 transition">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
            </td>
        `;
        tableBody.appendChild(tr);
    });

    msg.textContent = `Đã tìm thấy ${data.items.length} mặt hàng. Vui lòng khớp với hệ thống trước khi xác nhận.`;
}

document.getElementById('btn-confirm-import').onclick = async () => {
    const customerId = document.getElementById('reviewed-customer-match').value;
    if (!customerId) {
        showToast("Vui lòng chọn khách hàng", "warning");
        return;
    }

    const rows = document.querySelectorAll('#import-review-body tr');
    const items = [];
    rows.forEach(row => {
        const prodId = row.querySelector('.row-product-select').value;
        const qty = row.querySelector('.row-qty-input').value;
        if (prodId) {
            items.push({ product_id: parseInt(prodId), qty: parseInt(qty) });
        }
    });

    if (items.length === 0) {
        showToast("Vui lòng chọn ít nhất một sản phẩm hợp lệ", "warning");
        return;
    }

    try {
        const res = await fetch('/api/sale/bulk-create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_id: parseInt(customerId),
                items: items
            })
        });
        const result = await res.json();

        if (result.status === 'success') {
            showToast("Đã tạo hóa đơn thành công!", "success");
            closeImportModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert("Lỗi", result.message, "error");
        }
    } catch (err) {
        showAlert("Lỗi hệ thống", "Không thể tạo hóa đơn: " + err.message, "error");
    }
};


function approveZaloOrder(id) {
    const res = fetch('/api/zalo_order/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
    });
    const result = res.json();
    if (result.status === 'success') {
        showToast("Đã duyệt đơn hàng thành công!", "success");
        closeImportModal();
        setTimeout(() => location.reload(), 1000);
    } else {
        showAlert("Lỗi", result.message, "error");
    }
};
