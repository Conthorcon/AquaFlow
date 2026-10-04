// [Initialization]
let productDatabase = [];
let saleData = null;

document.addEventListener('DOMContentLoaded', async () => {
    await fetchProductDatabase();
    await fetchSaleDetails();
    
    // Show content with fade-in effect
    const mainContent = document.getElementById('main-content');
    mainContent.classList.remove('opacity-0');
    mainContent.classList.add('opacity-100');

    // Attach Event Listeners for Edit Mode
    if (MODE === 'edit') {
        setupEventListeners();
    }
});

async function fetchProductDatabase() {
    try {
        const response = await fetch('/api/productList');
        productDatabase = await response.json();
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

async function fetchSaleDetails() {
    try {
        const response = await fetch(`/api/sale/${SALE_ID}`);
        saleData = await response.json();
        populateUI(saleData);
    } catch (error) {
        console.error('Error fetching sale details:', error);
        alert('Không thể tải thông tin đơn hàng');
    }
}

function populateUI(data) {
    // Customer Info
    document.getElementById('display-customer-name').textContent = data.customer_name;
    document.getElementById('display-customer-phone').textContent = data.customer_phone || 'Chưa có SĐT';
    document.getElementById('display-customer-address').textContent = data.customer_address || 'Chưa có địa chỉ';
    
    // Order Info
    document.getElementById('display-date-created').textContent = data.date_created;
    document.getElementById('display-date-delivery').textContent = data.date_delivery;
    document.getElementById('display-date-completed').textContent = data.date_completed;

    // Conditional visibility
    if (data.status === 'delivering') {
        document.getElementById('row-date-delivery').classList.remove('hidden');
    } else if (data.status === 'completed') {
        document.getElementById('row-date-delivery').classList.remove('hidden');
        document.getElementById('row-date-completed').classList.remove('hidden');
    }
    
    if (MODE === 'view') {
        const statusEl = document.getElementById('display-status');
        statusEl.textContent = getStatusLabel(data.status);
        statusEl.className += ` ${getStatusClass(data.status)}`;
        
        document.getElementById('display-tax').textContent = `${data.tax}%`;
        document.getElementById('display-note').textContent = data.note || '-';
        
        // Delivery Employee
        const empName = getDeliveryEmployeeName(data.delivery_employee_id);
        document.getElementById('display-delivery-employee').textContent = empName;
    } else {
        document.getElementById('edit-status').value = data.status;
        document.getElementById('edit-tax').value = data.tax;
        document.getElementById('edit-note').value = data.note || '';
        document.getElementById('edit-delivery-employee').value = data.delivery_employee_id || '';
    }

    // Populate Items
    renderItems(data.items);
    updateTotals();
}

function renderItems(items) {
    const tbody = document.getElementById('items-body');
    tbody.innerHTML = '';
    
    items.forEach((item, index) => {
        addItemRow(item);
    });
}

function addItemRow(item) {
    const tbody = document.getElementById('items-body');
    const row = document.createElement('tr');
    row.className = 'group transition-colors hover:bg-gray-50';
    
    const subtotal = item.quantity * item.price_at_sale;
    
    row.innerHTML = `
        <td class="py-4">
            <div class="font-semibold text-gray-800">${item.product_name}</div>
        </td>
        <td class="py-4 text-center">
            ${MODE === 'edit' ? 
              `<input type="number" min="1" value="${item.quantity}" class="qty-input w-16 text-center border border-gray-200 rounded-lg p-1 text-sm focus:ring-1 focus:ring-blue-400 outline-none" onchange="updateRowTotal(this)">` : 
              `<span class="text-gray-600 font-medium">${item.quantity}</span>`
            }
        </td>
        <td class="py-4 text-right">
            <span class="text-gray-500 text-sm">${item.price_at_sale.toLocaleString()}đ</span>
        </td>
        <td class="py-4 text-right font-bold text-gray-700">
            <span class="row-total">${subtotal.toLocaleString()}</span>đ
        </td>
        ${MODE === 'edit' ? 
            `<td class="py-4 text-center">
                <button class="text-gray-300 hover:text-red-500 transition-colors" onclick="removeRow(this)">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            </td>` : ''
        }
    `;
    
    // Store price in data attribute for easy access
    row.dataset.price = item.price_at_sale;
    row.dataset.productName = item.product_name;
    
    tbody.appendChild(row);
}

// [Status Utils]
function getStatusLabel(status) {
    const labels = {
        'pending': 'Chờ xử lý',
        'delivering': 'Đang giao',
        'completed': 'Hoàn thành'
    };
    return labels[status] || status;
}

function getStatusClass(status) {
    const classes = {
        'pending': 'bg-yellow-100 text-yellow-700 border border-yellow-200',
        'delivering': 'bg-blue-100 text-blue-700 border border-blue-200',
        'completed': 'bg-green-100 text-green-700 border border-green-200'
    };
    return classes[status] || '';
}

function getDeliveryEmployeeName(id) {
    if (!id) return 'Chưa gán';
    // The list of employees is available in the dropdown hidden in view mode but exists in DOM structure if rendered
    const select = document.getElementById('edit-delivery-employee');
    if (select) {
        const option = select.querySelector(`option[value="${id}"]`);
        return option ? option.textContent : 'Không rõ';
    }
    return 'Chưa gán';
}

// [Edit Logic]
function setupEventListeners() {
    // Add product logic
    const trigger = document.getElementById('add-product-trigger');
    const dropdown = document.getElementById('product-dropdown');
    const searchInput = document.getElementById('product-search');

    if (trigger) {
        trigger.onclick = (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('hidden');
            if (!dropdown.classList.contains('hidden')) searchInput.focus();
        };
    }

    if (searchInput) {
        searchInput.oninput = (e) => renderProductResults(e.target.value);
    }

    document.addEventListener('click', (e) => {
        if (dropdown && !dropdown.contains(e.target) && e.target !== trigger) {
            dropdown.classList.add('hidden');
        }
    });

    // Tax change logic
    const taxInput = document.getElementById('edit-tax');
    if (taxInput) {
        taxInput.oninput = updateTotals;
    }

    // Save button
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.onclick = submitChanges;
    }
}

function renderProductResults(query) {
    const list = document.getElementById('product-results');
    list.innerHTML = '';
    
    const filtered = productDatabase.filter(p => 
        p.name.toLowerCase().includes(query.toLowerCase())
    ).slice(0, 5);

    filtered.forEach(p => {
        const li = document.createElement('li');
        li.className = 'p-2 hover:bg-blue-50 cursor-pointer rounded-lg text-sm transition-colors flex justify-between items-center';
        
        // Determine price for current customer group
        const groupId = saleData ? saleData.customer_group_id : 1;
        const price = (p.prices && p.prices[groupId]) || 0;
        
        li.innerHTML = `
            <span class="font-medium text-gray-700">${p.name}</span>
            <span class="text-xs text-blue-500 font-bold">${price > 0 ? price.toLocaleString() + 'đ' : 'Chưa có giá'}</span>
        `;
        if (price > 0) {
            li.onclick = () => {
                addItemRow({
                    product_id: p.id,
                    product_name: p.name,
                    quantity: 1,
                    price_at_sale: price
                });
                document.getElementById('product-dropdown').classList.add('hidden');
                document.getElementById('product-search').value = '';
                updateTotals();
            };
        } else {
            li.classList.add('opacity-50', 'cursor-not-allowed');
            li.title = "Sản phẩm chưa cấu hình giá cho nhóm này";
        }
        list.appendChild(li);
    });
}

function removeRow(btn) {
    btn.closest('tr').remove();
    updateTotals();
}

function updateRowTotal(input) {
    const row = input.closest('tr');
    const price = parseFloat(row.dataset.price);
    const qty = parseInt(input.value) || 0;
    const subtotal = price * qty;
    
    row.querySelector('.row-total').textContent = subtotal.toLocaleString();
    updateTotals();
}

function updateTotals() {
    const rows = document.querySelectorAll('#items-body tr');
    let subtotal = 0;
    
    rows.forEach(row => {
        const price = parseFloat(row.dataset.price);
        const qtyNode = row.querySelector('.qty-input');
        const qty = qtyNode ? (parseInt(qtyNode.value) || 0) : (parseInt(row.querySelector('span.text-gray-600').textContent) || 0);
        subtotal += (price * qty);
    });
    
    const taxValue = MODE === 'edit' ? (parseFloat(document.getElementById('edit-tax').value) || 0) : (parseFloat(saleData.tax) || 0);
    const taxAmount = subtotal * (taxValue / 100);
    const total = subtotal + taxAmount;
    
    document.getElementById('display-subtotal').textContent = `${subtotal.toLocaleString()}đ`;
    if (MODE === 'view') {
        document.getElementById('display-tax').textContent = `${taxValue}%`;
    }
    document.getElementById('display-total').textContent = `${Math.round(total).toLocaleString()}đ`;
}

async function submitChanges() {
    const saveBtn = document.getElementById('save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Đang lưu...';
    
    const products = [];
    document.querySelectorAll('#items-body tr').forEach(row => {
        const qtyNode = row.querySelector('.qty-input');
        const qty = qtyNode ? parseInt(qtyNode.value) : parseInt(row.querySelector('span.text-gray-600').textContent);
        
        products.push({
            name: row.dataset.productName,
            quantity: qty,
            price: parseFloat(row.dataset.price)
        });
    });

    const data = {
        id: SALE_ID,
        tax: document.getElementById('edit-tax').value,
        note: document.getElementById('edit-note').value,
        status: document.getElementById('edit-status').value,
        delivery_employee_id: document.getElementById('edit-delivery-employee').value,
        productList: products
    };

    try {
        const response = await fetch('/api/sale/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            window.location.href = '/sale';
        } else {
            alert('Lỗi: ' + result.message);
            saveBtn.disabled = false;
            saveBtn.textContent = 'Lưu thay đổi';
        }
    } catch (error) {
        console.error('Error updating sale:', error);
        alert('Có lỗi xảy ra khi cập nhật');
        saveBtn.disabled = false;
        saveBtn.textContent = 'Lưu thay đổi';
    }
}

// [Invoice Export]
function exportInvoice() {
    if (!saleData) {
        alert('Dữ liệu đơn hàng chưa tải xong, vui lòng thử lại.');
        return;
    }

    const d = saleData;
    const taxValue = parseFloat(d.tax) || 0;

    // Build items rows
    let subtotal = 0;
    const itemsHTML = d.items.map((item, i) => {
        const lineTotal = item.quantity * item.price_at_sale;
        subtotal += lineTotal;
        return `
            <tr style="border-bottom: 1px solid #f0f0f0;">
                <td style="padding: 10px 8px; color: #374151;">${i + 1}</td>
                <td style="padding: 10px 8px; font-weight: 600; color: #111827;">${item.product_name}</td>
                <td style="padding: 10px 8px; text-align: center; color: #374151;">${item.quantity}</td>
                <td style="padding: 10px 8px; text-align: right; color: #374151;">${item.price_at_sale.toLocaleString('vi-VN')}đ</td>
                <td style="padding: 10px 8px; text-align: right; font-weight: 700; color: #111827;">${lineTotal.toLocaleString('vi-VN')}đ</td>
            </tr>
        `;
    }).join('');

    const taxAmount = subtotal * (taxValue / 100);
    const total = subtotal + taxAmount;

    const statusMap = { pending: 'Chờ xử lý', delivering: 'Đang giao', completed: 'Hoàn thành' };

    const invoiceHTML = `
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8"/>
        <title>Hóa đơn #${d.id} - AquaFlow</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #f8fafc; color: #1f2937; }
            .page { max-width: 800px; margin: 0 auto; background: white; min-height: 100vh; }
            @media print {
                body { background: white; }
                .no-print { display: none !important; }
                .page { box-shadow: none; }
            }
        </style>
    </head>
    <body>
        <div class="page">
            <!-- Print Button (hidden on print) -->
            <div class="no-print" style="padding: 16px 48px; background: #f1f5f9; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: flex-end; gap: 12px;">
                <button onclick="window.print()" style="background: #1e293b; color: white; border: none; padding: 10px 24px; border-radius: 10px; font-size: 14px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px;">
                    🖨️ In hóa đơn
                </button>
                <button onclick="window.close()" style="background: white; color: #64748b; border: 1px solid #e2e8f0; padding: 10px 24px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer;">
                    Đóng
                </button>
            </div>

            <!-- Invoice Content -->
            <div style="padding: 48px;">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 48px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                            <div style="width: 36px; height: 36px; background: #2563eb; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                                <span style="color: white; font-size: 18px; font-weight: 900;">A</span>
                            </div>
                            <span style="font-size: 22px; font-weight: 800; color: #111827; letter-spacing: -0.5px;">AquaFlow</span>
                        </div>
                        <p style="font-size: 13px; color: #6b7280; margin-top: 4px;">Hệ thống quản lý đơn hàng nước</p>
                    </div>
                    <div style="text-align: right;">
                        <p style="font-size: 26px; font-weight: 900; color: #111827; letter-spacing: -1px;">HÓA ĐƠN</p>
                        <p style="font-size: 15px; font-weight: 700; color: #2563eb; margin-top: 4px;">#${d.id}</p>
                        <p style="font-size: 12px; color: #9ca3af; margin-top: 6px;">Ngày tạo: ${d.date_created}</p>
                        <div style="display: inline-block; margin-top: 8px; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
                            ${d.status === 'completed' ? 'background:#dcfce7; color:#15803d;' : d.status === 'delivering' ? 'background:#dbeafe; color:#1d4ed8;' : 'background:#fef9c3; color:#854d0e;'}">
                            ${statusMap[d.status] || d.status}
                        </div>
                    </div>
                </div>

                <!-- Divider -->
                <div style="height: 2px; background: linear-gradient(to right, #2563eb, #e5e7eb); border-radius: 2px; margin-bottom: 40px;"></div>

                <!-- Parties -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-bottom: 40px;">
                    <div>
                        <p style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af; margin-bottom: 10px;">Bên bán</p>
                        <p style="font-size: 15px; font-weight: 700; color: #111827; margin-bottom: 4px;">Công ty AquaFlow</p>
                        <p style="font-size: 13px; color: #6b7280;">📧 contact@aquaflow.vn</p>
                    </div>
                    <div>
                        <p style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af; margin-bottom: 10px;">Bên mua</p>
                        <p style="font-size: 15px; font-weight: 700; color: #111827; margin-bottom: 4px;">${d.customer_name}</p>
                        ${d.customer_phone ? `<p style="font-size: 13px; color: #6b7280;">📞 ${d.customer_phone}</p>` : ''}
                        ${d.customer_address ? `<p style="font-size: 13px; color: #6b7280; margin-top: 2px;">📍 ${d.customer_address}</p>` : ''}
                    </div>
                </div>

                <!-- Items Table -->
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 32px;">
                    <thead>
                        <tr style="background: #1e293b; color: white;">
                            <th style="padding: 12px 8px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 8px 0 0 8px;">#</th>
                            <th style="padding: 12px 8px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Sản phẩm</th>
                            <th style="padding: 12px 8px; text-align: center; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">SL</th>
                            <th style="padding: 12px 8px; text-align: right; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Đơn giá</th>
                            <th style="padding: 12px 8px; text-align: right; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 0 8px 8px 0;">Thành tiền</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${itemsHTML}
                    </tbody>
                </table>

                <!-- Totals -->
                <div style="display: flex; justify-content: flex-end;">
                    <div style="width: 280px;">
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; color: #6b7280;">
                            <span>Tạm tính</span>
                            <span style="font-weight: 600;">${subtotal.toLocaleString('vi-VN')}đ</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; color: #6b7280;">
                            <span>Thuế (${taxValue}%)</span>
                            <span style="font-weight: 600;">${taxAmount.toLocaleString('vi-VN')}đ</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 14px 16px; margin-top: 8px; background: #1e293b; color: white; border-radius: 12px; font-size: 16px;">
                            <span style="font-weight: 700;">TỔNG CỘNG</span>
                            <span style="font-weight: 900; color: #60a5fa;">${Math.round(total).toLocaleString('vi-VN')}đ</span>
                        </div>
                    </div>
                </div>

                ${d.note ? `
                <!-- Note -->
                <div style="margin-top: 40px; padding: 16px; background: #f8fafc; border-left: 4px solid #2563eb; border-radius: 4px;">
                    <p style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #9ca3af; margin-bottom: 6px;">Ghi chú</p>
                    <p style="font-size: 13px; color: #374151; font-style: italic;">${d.note}</p>
                </div>` : ''}

                <!-- Footer -->
                <div style="margin-top: 60px; padding-top: 24px; border-top: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                    <p style="font-size: 12px; color: #d1d5db;">Hóa đơn được tạo tự động bởi AquaFlow</p>
                    <p style="font-size: 12px; color: #d1d5db;">Ngày in: ${new Date().toLocaleDateString('vi-VN')}</p>
                </div>
            </div>
        </div>
    </body>
    </html>`;

    const win = window.open('', '_blank', 'width=900,height=700');
    win.document.write(invoiceHTML);
    win.document.close();
}
