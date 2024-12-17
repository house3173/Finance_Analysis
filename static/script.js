document.getElementById('industrySelect').addEventListener('change', async function () {
    const industry = this.value;
    
    if (industry) {
        // Lấy dữ liệu công ty
        const response = await fetch(`/get-companies?industry=${industry}`);
        const companies = await response.json();

        // Lấy tên doanh nghiệp từ API
        const nameResponse = await fetch(`/get-company-names`);
        const companyNames = await nameResponse.json();

        const companyTbody = document.getElementById('companyTbody');
        companyTbody.innerHTML = ''; // Xóa dữ liệu cũ

        companies.forEach((company, index) => {
            const nameEntry = companyNames.find(c => c['Mã CP'] === company['Mã CP']);
            const companyName = nameEntry ? nameEntry['Tên doanh nghiệp'] : 'N/A';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${company['Mã CP']}</td>
                <td>${companyName}</td> <!-- Tên doanh nghiệp -->
                <td>${company['Sàn']}</td>
            `;
            companyTbody.appendChild(row);
        });

        const metricSelect = document.getElementById('metricSelect');
        if (metricSelect.value) {
            updateChart(industry, metricSelect.value);
        }
    }
});



document.getElementById('metricSelect').addEventListener('change', function () {
    const industry = document.getElementById('industrySelect').value;
    const metric = this.value;

    if (industry && metric) {
        updateChart(industry, metric);
    }
});

async function updateChart(industry, metric, elementId = 'chart') {
    const response = await fetch(`/get-chart-data?industry=${industry}&metric=${metric}`);
    const chartData = await response.json();

    const labels = chartData.map(item => item['Mã CP']);
    const data = chartData.map(item => item[metric]);
    console.log(labels, data);

    const ctx = document.getElementById(elementId).getContext('2d');
    if (window.myChart) {
        window.myChart.destroy();
    }
    window.myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: metric,
                data: data,
                backgroundColor: 'rgba(76, 175, 80, 0.2)', // Màu xanh lá trong suốt cho nền cột
                borderColor: 'rgba(76, 175, 80, 1)',       // Màu xanh lá đậm cho viền cột
                borderWidth: 1.5
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Xử lý khi người dùng chọn một công ty trong bảng
document.getElementById('companyTable').addEventListener('click', function (e) {
    if (e.target && e.target.nodeName === 'TD') {
        const companyCode = e.target.parentElement.cells[1].textContent;  // Lấy mã công ty từ cột thứ 2 của hàng

        // Lưu mã công ty đã chọn vào selection cho biểu đồ riêng
        document.getElementById('metricSelectCompany').setAttribute('data-company-code', companyCode);

        const metric = document.getElementById('metricSelectCompany').value;
        if (companyCode && metric) {
            updateCompanyChart(companyCode, metric);
        } else {
            if (window.myCompanyChart) {
                window.myCompanyChart.destroy();
            }
        }
    }
});

// Xử lý khi người dùng chọn thông số để vẽ biểu đồ riêng cho công ty
document.getElementById('metricSelectCompany').addEventListener('change', function () {
    const companyCode = this.getAttribute('data-company-code');
    const metric = this.value;

    console.log(companyCode, metric);

    if (companyCode && metric) {
        updateCompanyChart(companyCode, metric);
    }
});

// Hàm cập nhật biểu đồ riêng cho công ty
async function updateCompanyChart(companyCode, metric) {
    const response = await fetch(`/get-company-chart?company_code=${companyCode}&metric=${metric}`);
    console.log(response);
    // Kiểm tra nếu response không thành công thì xóa biểu đồ hiện tại nếu có và thông báo lỗi
    if (!response.ok) {
        console.log('Error fetching company chart data');
        if (window.myCompanyChart) {
            window.myCompanyChart.destroy();
        }
        document.getElementById('companyChartTitle').textContent = 'Không tìm thấy dữ liệu';
        document.getElementById('companyChartYLabel').textContent = '';
        return;
    }
    
    const chartData = await response.json();
    console.log(chartData);

    const timePoints = chartData.time_points;
    // const values = chartData.values.map(v => v / 1e9); // Chuyển đơn vị từ VND sang tỷ đồng
    // Kiểm tra néu là NaN thì gán giá trị 0, ngược lại là gía trị nguyên thì chuyển đơn vị từ VND sang tỷ đồng
    const values = chartData.values.map(v => isNaN(v) ? 0 : v / 1e9);

    console.log(timePoints, values);
    //['Quý 2 - 2018', 'Quý 3 - 2018', 'Quý 4 - 2018', 'Quý 1 - 2019', 'Quý 2 - 2019', 'Quý 3 - 2019', 'Quý 4 - 2019', 'Quý 1 - 2020'] 
    // [20818678622022, 18360115898846, 20559756794837, 22040432596172, 22089274019449, 22146344620561, 24721565376552, 26461638721175]

    const ctx = document.getElementById('companyChart').getContext('2d');
    
    // Thực hiện vẽ biểu đồ với thư viện Chart.js: trục ngang là thời gian, trục đứng là giá trị
    if (window.myCompanyChart) {
        window.myCompanyChart.destroy();
    }

    // Thực hiện vẽ biểu đồ cột kết hợp với đường
    window.myCompanyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: timePoints,
            datasets: [
                {
                    type: 'bar',
                    label: metric,
                    data: values,
                    backgroundColor: 'rgba(76, 175, 80, 0.2)', // Màu xanh lá trong suốt cho nền cột
                    borderColor: 'rgba(76, 175, 80, 1)',       // Màu xanh lá đậm cho viền cột
                    borderWidth: 1.5
                },
                {
                    type: 'line',
                    label: `${metric} Trend`,
                    data: values,
                    borderColor: 'rgba(255, 99, 132, 1)',      // Màu đỏ cho đường
                    borderWidth: 2,
                    fill: false
                }
            ]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Thay đổi tiêu đề biểu đồ và đơn vị trên trục y
    document.getElementById('companyChartTitle').textContent = `Biểu đồ ${metric} của công ty ${companyCode}`;
    document.getElementById('companyChartYLabel').textContent = ` (Đơn vị: tỷ đồng)`;

}

/*
document.getElementById('overviewAnalysisBtn').addEventListener('click', async function () {
    const companyCode = document.getElementById('metricSelectCompany').getAttribute('data-company-code');
    if (!companyCode) {
        alert('Vui lòng chọn một công ty trước khi phân tích.');
        return;
    }

    // Gửi yêu cầu đến server để lấy dữ liệu
    const response = await fetch(`/get-overview-data?company_code=${companyCode}`);
    if (!response.ok) {
        alert('Không thể lấy dữ liệu phân tích. Vui lòng thử lại sau.');
        return;
    }

    const data = await response.json();
    console.log(data);

    // Hiển thị modal
    const modal = document.getElementById('overviewModal');
    const modalTitle = document.getElementById('modalTitle');
    modal.style.display = 'block';
    modalTitle.textContent = `Phân tích tổng quan doanh nghiệp ${companyCode}`;

    // Cập nhật biểu đồ tròn
    const pieChartData = data.pieChartData;
    const pieChartLabels = data.labels;
    const pieChartValues = data.values;
    // console.log(pieChartData, pieChartLabels, pieChartValues);

    const ctx = document.getElementById('pieChart').getContext('2d');
    if (modal.pieChart) {
        modal.pieChart.destroy();
    }
    modal.pieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: pieChartLabels,
            datasets: [{
                data: pieChartValues,
                backgroundColor: ['#4CAF50', '#FF9800', '#2196F3', '#9C27B0', '#FFC107'],
                borderWidth: 1
            }]
        }
    });

    // Hiển thị phân tích bên dưới biểu đồ
    const maxPercentage = Math.max(...pieChartValues);
    const maxIndex = pieChartValues.indexOf(maxPercentage);
    const maxLabel = pieChartLabels[maxIndex];
    document.getElementById('chartDescription').textContent = "Biểu đồ cơ cấu trong Tài sản ngắn hạn";
    document.getElementById('chartAnalysis').textContent = `Giá trị ${maxLabel} chiếm tỷ lệ ${maxPercentage.toFixed(2)}% lớn nhất trong tài sản ngắn hạn.`;
});
*/

document.getElementById('overviewAnalysisBtn').addEventListener('click', async function () {
    const companyCode = document.getElementById('metricSelectCompany').getAttribute('data-company-code');
    if (!companyCode) {
        alert('Vui lòng chọn một công ty trước khi phân tích.');
        return;
    }

    // Gửi yêu cầu đến server để lấy dữ liệu
    const response = await fetch(`/get-overview-data?company_code=${companyCode}`);
    if (!response.ok) {
        alert('Không thể lấy dữ liệu phân tích. Vui lòng thử lại sau.');
        return;
    }

    const data = await response.json();

    // Hiển thị modal
    const modal = document.getElementById('overviewModal');
    const modalTitle = document.getElementById('modalTitle');
    modal.style.display = 'block';
    modalTitle.textContent = `Phân tích tổng quan doanh nghiệp ${companyCode}`;

    // 1. Biểu đồ cơ cấu Tài sản ngắn hạn
    renderPieChart('shortTermAssetChart', data.shortTerm.labels, data.shortTerm.values, 'Biểu đồ cơ cấu trong Tài sản ngắn hạn');
    document.getElementById('shortTermAssetDesc').textContent = data.shortTerm.description;

    // 2. Biểu đồ cơ cấu Tài sản dài hạn
    renderPieChart('longTermAssetChart', data.longTerm.labels, data.longTerm.values, 'Biểu đồ cơ cấu trong Tài sản dài hạn');
    document.getElementById('longTermAssetDesc').textContent = data.longTerm.description;

    // 3. Biểu đồ cơ cấu Tổng Tài sản
    renderPieChart('totalAssetChart', data.totalAsset.labels, data.totalAsset.values, 'Biểu đồ cơ cấu Tổng Tài sản');
    document.getElementById('totalAssetDesc').textContent = data.totalAsset.description;

    // 4. Biểu đồ cơ cấu Nợ phải trả
    renderPieChart('debtChart', data.debt.labels, data.debt.values, 'Biểu đồ cơ cấu Nợ phải trả');
    document.getElementById('debtDesc').textContent = data.debt.description;

    // 5. Biểu đồ cơ cấu Vốn chủ sở hữu
    renderPieChart('equityChart', data.equity.labels, data.equity.values, 'Biểu đồ cơ cấu Vốn chủ sở hữu');
    document.getElementById('equityDesc').textContent = data.equity.description;

    // 6. Biểu đồ cơ cấu Nguồn vốn
    renderPieChart('capitalChart', data.capital.labels, data.capital.values, 'Biểu đồ cơ cấu Nguồn vốn');
    document.getElementById('capitalDesc').textContent = data.capital.description;

    const industry = document.getElementById('industrySelect').value;
    const metric = document.getElementById('metricSelectModal').value;
    updateChartModal(industry, metric, companyCode, 'chartInModal');

    fetchAndDisplayAnalysis(companyCode);

});

document.getElementById('metricSelectModal').addEventListener('change', function () {
    const industry = document.getElementById('industrySelect').value;
    const metric = this.value;
    const companyCode = document.getElementById('metricSelectCompany').getAttribute('data-company-code');

    if (industry && metric && companyCode) {
        updateChartModal(industry, metric, companyCode, 'chartInModal');
    }
});

// Hàm vẽ biểu đồ tròn
function renderPieChart(canvasId, labels, data, title) {
    const modal = document.getElementById('overviewModal');
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (modal[canvasId]) {
        modal[canvasId].destroy();
    }
    modal[canvasId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#4CAF50', '#FF9800', '#2196F3', '#9C27B0', '#FFC107', '#0000CC'],
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: title
                }
            }
        }
    });
}

async function updateChartModal(industry, metric, companyCode, elementId = 'chart') {
    const response = await fetch(`/get-chart-data?industry=${industry}&metric=${metric}`);
    const chartData = await response.json();

    const labels = chartData.map(item => item['Mã CP']);
    const data = chartData.map(item => item[metric]);

    // Tìm vị trí của companyCode trong dữ liệu
    const companyIndex = labels.indexOf(companyCode);
    const backgroundColors = labels.map((_, index) =>
        index === companyIndex ? 'rgba(255, 99, 132, 0.6)' : 'rgba(76, 175, 80, 0.2)' // Màu đỏ cho companyCode
    );
    const borderColors = labels.map((_, index) =>
        index === companyIndex ? 'rgba(255, 99, 132, 1)' : 'rgba(76, 175, 80, 1)' // Màu viền đỏ cho companyCode
    );

    // Tính mức trung bình
    const averageValue = data.reduce((sum, value) => sum + value, 0) / data.length;

    const ctx = document.getElementById(elementId).getContext('2d');
    if (window.myChart) {
        window.myChart.destroy();
    }
    window.myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: metric,
                data: data,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1.5
            }]
        },
        options: {
            plugins: {
                annotation: {
                    annotations: {
                        // Đường màu đỏ cho cột companyCode
                        redLine: companyIndex !== -1 ? {
                            type: 'line',
                            yMin: data[companyIndex],
                            yMax: data[companyIndex],
                            borderColor: 'rgba(255, 99, 132, 1)', // Màu đỏ
                            borderWidth: 2,
                            label: {
                                enabled: true,
                                content: `Mã CP: ${companyCode}`,
                                position: 'start',
                                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                                color: '#fff',
                                padding: 6
                            }
                        } : null,
                        // Đường màu tím cho mức trung bình
                        averageLine: {
                            type: 'line',
                            yMin: averageValue,
                            yMax: averageValue,
                            borderColor: 'rgba(128, 0, 128, 1)', // Màu tím
                            borderWidth: 2,
                            borderDash: [5, 5], // Đường kẻ nét đứt
                            label: {
                                enabled: true,
                                content: `Trung bình: ${averageValue.toFixed(2)}`,
                                position: 'end',
                                backgroundColor: 'rgba(128, 0, 128, 0.8)',
                                color: '#fff',
                                padding: 6
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function fetchAndDisplayAnalysis(companyCode) {
    const analysisContent = document.getElementById('analysisContent');
    console.log(analysisContent);
    analysisContent.innerHTML = `
        <div class="progress" role="progressbar" aria-label="Animated striped example" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">
            <div class="progress-bar">
                <span class="progress-text">Loading...</span>
            </div>
        </div>
    `; // Hiển thị trạng thái đang tải

    try {
        // Gửi yêu cầu đến API evaluate_company
        const response = await fetch(`/evaluate-company?company_code=${companyCode}`);
        console.log(response);
        if (!response.ok) {
            throw new Error('Lỗi khi gọi API: ' + response.statusText);
        }

        // Nhận kết quả JSON
        const data = await response.json();

        // Kiểm tra nếu API trả về lỗi
        if (data.error) {
            analysisContent.innerHTML = `<p style="color: red;">${data.error}</p>`;
            return;
        }

        // Tạo nội dung phân tích
        const analysisHtml = [];

        // Tạo danh sách cho từng mảng
        const sections = {
            health: "Đánh giá sức khỏe tài chính",
            activity: "Đánh giá hiệu quả hoạt động",
            growth: "Đánh giá mức độ tăng trưởng"
        };

        for (const [key, title] of Object.entries(sections)) {
            if (data[key] && data[key].length > 0) {
                analysisHtml.push(`<ul><strong>${title}</strong>`);
                data[key].forEach(item => {
                    analysisHtml.push(`<li class="analys_li">${item}</li>`);
                });
                analysisHtml.push(`</ul>`);
            } else {
                analysisHtml.push(`<p><strong>${title}</strong>: Không có dữ liệu.</p>`);
            }
        }
        // Bổ sung thêm 1 thẻ ul "Đánh giá rủi ro tài chính theo mô hình nghiên cứu"
        analysisHtml.push(`<ul><strong>Đánh giá điểm doanh nghiệp theo mô hình nghiên cứu: <span class="score">${data['score'].toFixed(2)}</span></strong>`);

        // analysisHtml.push(`
        //     <div class="progress mt-20" role="progressbar" aria-label="Animated striped example" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">
        //         <div class="progress-bar">
        //             <span class="progress-text">Loading...</span>
        //         </div>
        //     </div>
        // `);

        // Gắn nội dung vào thẻ analysisContent
        analysisContent.innerHTML = analysisHtml.join('');
    } catch (error) {
        console.error('Lỗi khi lấy dữ liệu từ API:', error);
        analysisContent.innerHTML = `<p style="color: red;">Không thể tải dữ liệu phân tích. Vui lòng thử lại sau.</p>`;
    }
}

// Đóng modal
document.getElementById('closeModal').addEventListener('click', function () {
    document.getElementById('overviewModal').style.display = 'none';
});


