from flask import Flask, render_template, jsonify, request
import pandas as pd
import json

app = Flask(__name__)

# Đọc file Excel
df = pd.read_excel('LIST_COMPANY.xlsx')

# Loại bỏ các hàng trùng lặp
df.drop_duplicates(subset=['Mã CP'], inplace=True)

# Lấy danh sách ngành nghề
industries = df['Ngành'].unique().tolist()
metrics = df.columns[3:].tolist()

# Đojc file Excel chứa cân đối kế toán của công ty
df_company = pd.read_excel('bctc/Can_doi_ke_toan_VNM.xlsx')
# các thông số của công ty nằm ở cột đầu tiên bắt đầu từ dòng thứ 3
metrics_company = df_company.iloc[1:, 0].tolist()

# Đọc file Excel chứa kết quả hoạt động kinh doanh của công ty
df_company_hdkd = pd.read_excel('kqhdkd/Ket_qua_hoat_dong_kinh_doanh_VIC.xlsx')
# Lấy danh sách các thông số của công ty
metrics_company_hdkd = df_company_hdkd.iloc[1:, 0].tolist()

# Merge 2 danh sách thông số của công ty
metrics_company.extend(metrics_company_hdkd)

company_code = 'VIC'

@app.route('/')
def index():
    return render_template('index.html', industries=industries, metrics=metrics, metrics_company=metrics_company, company_code=company_code)

# API để lấy danh sách Mã CP và Sàn theo ngành
@app.route('/get-companies', methods=['GET'])
def get_companies():
    industry = request.args.get('industry')
    filtered_df = df[df['Ngành'] == industry][['Mã CP', 'Sàn']]
    companies = filtered_df.to_dict(orient='records')
    return jsonify(companies)

@app.route('/get-company-names')
def get_company_names():
    with open('static/companies.json', 'r', encoding='utf-8') as f:
        companies = json.load(f)
    return jsonify(companies)

# API để lấy dữ liệu biểu đồ theo ngành và thông số
@app.route('/get-chart-data', methods=['GET'])
def get_chart_data():
    industry = request.args.get('industry')
    metric = request.args.get('metric')
    filtered_df = df[df['Ngành'] == industry][['Mã CP', metric]]
    chart_data = filtered_df.to_dict(orient='records')
    return jsonify(chart_data)

@app.route('/get-company-chart', methods=['GET'])
def get_company_chart():
    company_code = request.args.get('company_code')  # Lấy mã công ty từ request
    metric = request.args.get('metric')  # Lấy thông số cần vẽ từ request

    # Đường dẫn đến file Excel của công ty
    file_path_cdkt = f'bctc/Can_doi_ke_toan_{company_code}.xlsx'
    # file_path_kqhdkd = f'kqhdkd/Ket_qua_hoat_dong_kinh_doanh_{company_code}.xlsx'
    
    try:
        # Đọc dữ liệu Excel bỏ qua hàng đầu tiên
        df_cdkt = pd.read_excel(file_path_cdkt, header=1)
        # df_kqhdkd = pd.read_excel(file_path_kqhdkd, header=1)
        
        # # Kiểm tra nếu thông số tồn tại trong file
        # if metric not in df_cdkt['Quý'].values and metric not in df_kqhdkd['Quý'].values:
        #     return jsonify({'error': 'Metric not found'}), 400
        # else:
        #     if metric in df_cdkt['Quý'].values:
        #         # Lọc hàng dữ liệu cho thông số được chọn
        #         metric_data = df_cdkt[df_cdkt['Quý'] == metric].iloc[0, 1:]  # Lấy hàng dữ liệu cho metric
        #     else:
        #         metric_data = df_kqhdkd[df_kqhdkd['Quý'] == metric].iloc[0, 1:]
        # Kiểm tra nếu thông số tồn tại trong file
        if metric not in df_cdkt['Quý'].values:
            return jsonify({'error': 'Metric not found'}), 400
        else:
            metric_data = df_cdkt[df_cdkt['Quý'] == metric].iloc[0, 1:]  # Lấy hàng dữ liệu cho metric

        # Lọc hàng dữ liệu cho thông số được chọn
        # metric_data = df[df['Quý'] == metric].iloc[0, 1:]  # Lấy hàng dữ liệu cho metric
        
        # Chuẩn bị dữ liệu cho JSON response
        time_points = metric_data.index.tolist()  # Danh sách các mốc thời gian
        values = metric_data.values.tolist()  # Danh sách giá trị theo thời gian
        # kiểm tra values nếu là NaN thì gán giá trị 0
        for i in range(len(values)):
            if pd.isna(values[i]):
                values[i] = 0

        return jsonify({
            'time_points': time_points,
            'values': values
        })

    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-overview-data')
def get_overview_data():
    company_code = request.args.get('company_code')
    if not company_code:
        return jsonify({'error': 'Mã công ty không hợp lệ'}), 400

    try:
        file_path = f'bctc/Can_doi_ke_toan_{company_code}.xlsx'
        df = pd.read_excel(file_path, header = 1)
        df = df.fillna(0)

        # Biểu đồ cơ cấu Tài sản ngắn hạn
        short_term = df[df['Quý'].isin([
            "I. Tiền và các khoản tương đương tiền",
            "II. Các khoản đầu tư tài chính ngắn hạn",
            "III. Các khoản phải thu ngắn hạn",
            "IV. Hàng tồn kho",
            "V.Tài sản ngắn hạn khác"
        ])]
        total_short_term = df[df['Quý'] == "A- TÀI SẢN NGẮN HẠN"]["Quý 1 - 2024"].values[0]
        short_term['Percentage'] = (short_term['Quý 1 - 2024'] / total_short_term) * 100

        # Biểu đồ cơ cấu Tài sản dài hạn
        long_term = df[df['Quý'].isin([
            "I. Các khoản phải thu dài hạn",
            "II. Tài sản cố định",
            "III. Bất động sản đầu tư",
            "IV. Tài sản dở dang dài hạn",
            "V. Đầu tư tài chính dài hạn",
            "VI. Tài sản dài hạn khác"
        ])]
        total_long_term = df[df['Quý'] == "B. TÀI SẢN DÀI HẠN"]["Quý 1 - 2024"].values[0]
        long_term['Percentage'] = (long_term['Quý 1 - 2024'] / total_long_term) * 100

        # Biểu đồ cơ cấu Tổng Tài sản
        total_assets = df[df['Quý'].isin(["A- TÀI SẢN NGẮN HẠN", "B. TÀI SẢN DÀI HẠN"])]
        total_sum = df[df['Quý'] == "TỔNG CỘNG TÀI SẢN"]["Quý 1 - 2024"].values[0]
        total_assets['Percentage'] = (total_assets['Quý 1 - 2024'] / total_sum) * 100

        # Biểu đồ cơ cấu Nợ phải trả
        debts = df[df['Quý'].isin(["I. Nợ ngắn hạn", "II. Nợ dài hạn"])]
        total_debt = df[df['Quý'] == "C. NỢ PHẢI TRẢ"]["Quý 1 - 2024"].values[0]
        debts['Percentage'] = (debts['Quý 1 - 2024'] / total_debt) * 100

        # Biểu đồ cơ cấu Vốn chủ sở hữu
        equity = df[df['Quý'].isin([
            "1. Vốn góp của chủ sở hữu",
            "2. Thặng dư vốn cổ phần",
            "4. Vốn khác của chủ sở hữu",
            "11. Lợi nhuận sau thuế chưa phân phối",
            "13. Lợi ích cổ đông không kiểm soát"
        ])]

        # Tính tổng giá trị Vốn chủ sở hữu
        total_equity = df[df['Quý'] == "I. Vốn chủ sở hữu"]["Quý 1 - 2024"].values[0]

        # Tính tỷ lệ phần trăm
        equity['Percentage'] = (equity['Quý 1 - 2024'] / total_equity) * 100

        # Tính phần còn lại (Vốn khác)
        rest_equity = 100 - equity['Percentage'].sum()

        # Tạo dòng dữ liệu mới cho 'Vốn khác'
        new_row = pd.DataFrame({
            'Quý': ['Vốn khác'],
            'Quý 1 - 2024': [rest_equity * total_equity / 100],  # Quy đổi phần trăm về giá trị gốc
            'Percentage': [rest_equity]
        })

        # Kết hợp dữ liệu
        equity = pd.concat([equity, new_row], ignore_index=True)


        # Biểu đồ cơ cấu Nguồn vốn
        capital = df[df['Quý'].isin(["C. NỢ PHẢI TRẢ", "D.VỐN CHỦ SỞ HỮU"])]
        total_capital = df[df['Quý'] == "TỔNG CỘNG TÀI SẢN"]["Quý 1 - 2024"].values[0]
        capital['Percentage'] = (capital['Quý 1 - 2024'] / total_capital) * 100

        return jsonify({
            'shortTerm': {
                'labels': short_term['Quý'].tolist(),
                'values': short_term['Percentage'].tolist(),
                'description': f"Giá trị {short_term.loc[short_term['Percentage'].idxmax(), 'Quý']} chiếm tỷ lệ lớn nhất."
            },
            'longTerm': {
                'labels': long_term['Quý'].tolist(),
                'values': long_term['Percentage'].tolist(),
                'description': f"Giá trị {long_term.loc[long_term['Percentage'].idxmax(), 'Quý']} chiếm tỷ lệ lớn nhất."
            },
            'totalAsset': {
                'labels': total_assets['Quý'].tolist(),
                'values': total_assets['Percentage'].tolist(),
                'description': f"Giá trị {total_assets.loc[total_assets['Percentage'].idxmax(), 'Quý']} chiếm tỷ lệ lớn nhất."
            },
            'debt': {
                'labels': debts['Quý'].tolist(),
                'values': debts['Percentage'].tolist(),
                'description': f"Giá trị {debts.loc[debts['Percentage'].idxmax(), 'Quý']} chiếm tỷ lệ lớn nhất."
            },
            'equity': {
                'labels': equity['Quý'].tolist(),
                'values': equity['Percentage'].tolist(),
                'description': f"Giá trị {equity.loc[equity['Percentage'].idxmax(), 'Quý']} chiếm tỷ lệ lớn nhất."
            },
            'capital': {
                'labels': capital['Quý'].tolist(),
                'values': capital['Percentage'].tolist(),
                'description': f"Giá trị {capital.loc[capital['Percentage'].idxmax(), 'Quý']} chiếm tỷ lệ lớn nhất."
            }
        })
    except Exception as e:
        print(f"Lỗi xử lý dữ liệu: {e}")
        return jsonify({'error': 'Lỗi xử lý dữ liệu'}), 500


def load_excel(file_path, header=1):
    """Hàm hỗ trợ đọc file Excel với xử lý lỗi."""
    try:
        df = pd.read_excel(file_path, header=header)
        df.fillna(0, inplace=True)
        return df
    except Exception as e:
        print(f"Không thể tải file {file_path}: {e}")
        raise ValueError(f"Lỗi đọc file: {file_path}")
    
def calculate_revenue_growth_and_profit_growth_four_quarters(company_code):
    df_kqhdkd = load_excel(f'kqhdkd/Ket_qua_hoat_dong_kinh_doanh_{company_code}.xlsx')
    list_quarters = ["Quý 1 - 2023", "Quý 2 - 2023", "Quý 3 - 2023", "Quý 4 - 2023", "Quý 1 - 2024"]
    revenue_growth = 0
    number_of_quarters_revenue = 4
    profit_growth = 0
    number_of_quarters_profit = 4
    for i in range(1, len(list_quarters)):
        revenue_last_quarter = df_kqhdkd[df_kqhdkd['Quý'] == "3. Doanh thu thuần về bán hàng và cung cấp dịch vụ (10 = 01 - 02)"][list_quarters[i - 1]].values[0]
        revenue_current_quarter = df_kqhdkd[df_kqhdkd['Quý'] == "3. Doanh thu thuần về bán hàng và cung cấp dịch vụ (10 = 01 - 02)"][list_quarters[i]].values[0]
        if revenue_last_quarter == 0 or revenue_current_quarter == 0:
            number_of_quarters_revenue -= 1
        else:
            revenue_growth += ((revenue_current_quarter - revenue_last_quarter) / revenue_last_quarter) * 100

        profit_last_quarter = df_kqhdkd[df_kqhdkd['Quý'] == "18. Lợi nhuận sau thuế thu nhập doanh nghiệp(60=50-51-52)"][list_quarters[i - 1]].values[0]
        profit_current_quarter = df_kqhdkd[df_kqhdkd['Quý'] == "18. Lợi nhuận sau thuế thu nhập doanh nghiệp(60=50-51-52)"][list_quarters[i]].values[0]
        if profit_last_quarter == 0 or profit_current_quarter == 0:
            number_of_quarters_profit -= 1
        else:
            profit_growth += ((profit_current_quarter - profit_last_quarter) / profit_last_quarter) * 100
    
    if number_of_quarters_revenue == 0:
        revenue_growth = 0
    else:
        revenue_growth /= number_of_quarters_revenue
    if number_of_quarters_profit == 0:
        profit_growth = 0
    else:
        profit_growth /= number_of_quarters_profit
    return revenue_growth, profit_growth

def calculate_average_ratio(industry_companies, df_all_company, ratio_type):
    """Tính trung bình một chỉ số (D/E, Biên LN, Tăng trưởng) trong ngành."""
    ratios = []
    ratios_profit = []
    for company in industry_companies:
        try:
            if ratio_type == 'de_ratio':
                df_cdkt = load_excel(f'bctc/Can_doi_ke_toan_{company}.xlsx')
                total_debt = df_cdkt[df_cdkt['Quý'] == "C. NỢ PHẢI TRẢ"]["Quý 1 - 2024"].values[0]
                total_all_equity = df_cdkt[df_cdkt['Quý'] == "D.VỐN CHỦ SỞ HỮU"]["Quý 1 - 2024"].values[0]
                ratios.append(total_debt / total_all_equity)
            elif ratio_type == 'da_ratio':
                df_cdkt = load_excel(f'bctc/Can_doi_ke_toan_{company}.xlsx')
                total_debt = df_cdkt[df_cdkt['Quý'] == "C. NỢ PHẢI TRẢ"]["Quý 1 - 2024"].values[0]
                total_assets = df_cdkt[df_cdkt['Quý'] == "TỔNG CỘNG TÀI SẢN"]["Quý 1 - 2024"].values[0]
                ratios.append(total_debt / total_assets)
            elif ratio_type == 'gross_margin':
                gross_margin = df_all_company[df_all_company['Mã CP'] == company]['Biên LN thuần từ HDKD'].values[0]
                ratios.append(gross_margin)
            elif ratio_type == 'asset_turnover':
                df_kqhdkd = load_excel(f'kqhdkd/Ket_qua_hoat_dong_kinh_doanh_{company}.xlsx')
                df_cdkt = load_excel(f'bctc/Can_doi_ke_toan_{company}.xlsx')
                total_revenue = df_kqhdkd[df_kqhdkd['Quý'] == "3. Doanh thu thuần về bán hàng và cung cấp dịch vụ (10 = 01 - 02)"]["Quý 1 - 2024"].values[0]
                total_assets = df_cdkt[df_cdkt['Quý'] == "TỔNG CỘNG TÀI SẢN"]["Quý 1 - 2024"].values[0]
                print(f"Asset_turnover: {company}: {total_revenue / total_assets}")
                ratios.append(total_revenue / total_assets)
            elif ratio_type == 'roa':
                roa = df_all_company[df_all_company['Mã CP'] == company]['ROA'].values[0]
                ratios.append(roa)
            elif ratio_type == 'roe':
                roe = df_all_company[df_all_company['Mã CP'] == company]['ROE'].values[0]
                ratios.append(roe)
            elif ratio_type == 'revenue_profit':
                revenue_growth = calculate_revenue_growth_and_profit_growth_four_quarters(company)[0]
                profit_growth = calculate_revenue_growth_and_profit_growth_four_quarters(company)[1]
                ratios.append(revenue_growth)
                ratios_profit.append(profit_growth)
            elif ratio_type == 'revenue_growth':
                revenue = df_all_company[df_all_company['Mã CP'] == company]['Tăng trưởng DT (tỷ đồng) - 4 Quý'].values[0]
                ratios.append(revenue)
            elif ratio_type == 'profit_growth':
                profit = df_all_company[df_all_company['Mã CP'] == company]['Tăng trưởng lợi nhuận (tỷ đồng) - 4 Quý'].values[0]
                ratios.append(profit)
        except Exception:
            continue
    if ratio_type == 'revenue_profit':
        return sum(ratios) / len(ratios) if len(ratios) > 0 else 0, sum(ratios_profit) / len(ratios_profit) if len(ratios_profit) > 0 else 0
    if ratio_type == 'asset_turnover':
        print('Number of companies:', len(ratios))
    return sum(ratios) / len(ratios) if len(ratios) > 0 else 0

@app.route('/evaluate-company')
def evaluate_company():
    company_code = request.args.get('company_code')
    if not company_code:
        return jsonify({'error': 'Mã công ty không hợp lệ'}), 400

    evaluate_health = []
    evaluate_activity = []
    evaluate_growth = []
    print(f"Đánh giá công ty {company_code}")

    try:
        # Load dữ liệu
        df_cdkt = load_excel(f'bctc/Can_doi_ke_toan_{company_code}.xlsx')
        df_kqhdkd = load_excel(f'kqhdkd/Ket_qua_hoat_dong_kinh_doanh_{company_code}.xlsx')
        df_all_company = load_excel('LIST_COMPANY.xlsx', header=0)

        # Tổng hợp dữ liệu từ bảng cân đối kế toán
        total_debt = df_cdkt[df_cdkt['Quý'] == "C. NỢ PHẢI TRẢ"]["Quý 1 - 2024"].values[0]
        total_all_equity = df_cdkt[df_cdkt['Quý'] == "D.VỐN CHỦ SỞ HỮU"]["Quý 1 - 2024"].values[0]

        # Lấy thông tin ngành
        industry = df_all_company[df_all_company['Mã CP'] == company_code]['Ngành'].values[0]
        industry_companies = df_all_company[df_all_company['Ngành'] == industry]['Mã CP'].tolist()

        # Bước 1: Đánh giá sức khỏe tài chính 
        # 1. Chỉ số đòn bẩy tài chính (D/E)
        de_ratio = total_debt / total_all_equity
        avg_de_ratio = calculate_average_ratio(industry_companies, df_all_company, 'de_ratio')
        if de_ratio < avg_de_ratio:
            de_ratio_evaluate = f"Chỉ số đòn bẩy tài chính D/E của công ty {company_code} là {de_ratio:.2f}, thấp hơn so với trung bình ngành ({avg_de_ratio:.2f}) cho thấy doanh nghiệp ít phụ thuộc vào vốn vay hơn các doanh nghiệp cùng ngành."
            if de_ratio < 1:
                de_ratio_evaluate += " Đồng thời, chỉ số này cũng cho thấy cho thấy doanh nghiệp có sức mạnh tài chính và ít phụ thuộc vào vốn nợ. Tuy nhiên, điều này cũng có thể làm giảm lợi ích của lãi suất thuế và cơ hội mở rộng hoạt động kinh doanh."
        else:
            de_ratio_evaluate = f"Chỉ số đòn bẩy tài chính D/E của công ty {company_code} là {de_ratio:.2f}, cao hơn so với trung bình ngành ({avg_de_ratio:.2f}) cho thấy doanh nghiệp phụ thuộc nhiều vào vốn vay hơn các doanh nghiệp cùng ngành, có thể gặp khó khăn trong dài hạn."
            if de_ratio > 8:
                de_ratio_evaluate += " Đồng thời, chỉ số này hiện đang cao, có thể đem lại lợi ích ngắn hạn nhưng cũng tăng rủi ro tài chính cho doanh nghiệp."
        evaluate_health.append(de_ratio_evaluate)

        # 2. Chỉ số nợ trên tổng tài sản Debt-to-Assets Ratio (D/A)
        total_assets = df_cdkt[df_cdkt['Quý'] == "TỔNG CỘNG TÀI SẢN"]["Quý 1 - 2024"].values[0]
        da_ratio = total_debt / total_assets
        avg_da_ratio = calculate_average_ratio(industry_companies, df_all_company, 'da_ratio')
        if da_ratio < avg_da_ratio:
            da_ratio_evaluate = f"Chỉ số nợ trên tổng tài sản D/A của công ty {company_code} là {da_ratio:.2f}, thấp hơn so với trung bình ngành ({avg_da_ratio:.2f}) cho thấy doanh nghiệp ít vay nợ hơn các doanh nghiệp cùng ngành."
            if da_ratio < 0.2:
                da_ratio_evaluate += " Đồng thời, chỉ số này thấp cũng cho thấy cho thấy doanh nghiệp tự chủ tài chính tốt. Tuy nhiên, điều này cũng thể hiện rằng doanh nghiệp chưa khai thác, tận dụng tốt nguồn vốn vay để thúc đẩy hoạt động sản xuất kinh doanh, gia tăng doanh thu và lợi nhuận."
        else:
            da_ratio_evaluate = f"Chỉ số nợ trên tổng tài sản D/A của công ty {company_code} là {da_ratio:.2f}, cao hơn so với trung bình ngành ({avg_da_ratio:.2f}) cho thấy doanh nghiệp vay nợ nhiều hơn các doanh nghiệp cùng ngành."
            if da_ratio > 0.8:
                da_ratio_evaluate += " Đồng thời, chỉ số này hiện đang cao, cho thấy doanh nghiệp gặp khó khăn trong tự chủ tài chính, tăng rủi ro tài chính trong dài hạn."
        evaluate_health.append(da_ratio_evaluate)

        # 3. Current Ratio (Tỷ lệ thanh toán ngắn hạn), Quick Ratio (Tỷ lệ thanh toán nhanh), Cash Ratio (Tỷ lệ thanh toán bằng tiền mặt)
        current_assets = df_cdkt[df_cdkt['Quý'] == "A- TÀI SẢN NGẮN HẠN"]["Quý 1 - 2024"].values[0]
        current_liabilities = df_cdkt[df_cdkt['Quý'] == "C. NỢ PHẢI TRẢ"]["Quý 1 - 2024"].values[0]
        quick_assets = df_cdkt[df_cdkt['Quý'] == "A- TÀI SẢN NGẮN HẠN"]["Quý 1 - 2024"].values[0] - df_cdkt[df_cdkt['Quý'] == "IV. Hàng tồn kho"]["Quý 1 - 2024"].values[0]
        cash_assets = df_cdkt[df_cdkt['Quý'] == "I. Tiền và các khoản tương đương tiền"]["Quý 1 - 2024"].values[0]
        current_ratio = current_assets / current_liabilities
        quick_ratio = quick_assets / current_liabilities
        cash_ratio = cash_assets / current_liabilities

        if current_ratio > 2.5:
            if quick_ratio > 1.5:
                if cash_ratio > 1:
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, cao hơn 2.5 cho thấy công ty có khả năng thanh toán các khoản nợ ngắn hạn. Bên cạnh đó, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f}, cao hơn 1.5 cho thấy công ty có khả năng thanh toán ngắn hạn mà không bị phụ thuộc vào hàng tồn kho. Đồng thời, tỷ lệ thanh toán bằng tiền mặt (Cash Ratio) là {cash_ratio:.2f}, cho thấy công ty có khả năng thanh toán nhanh chóng, trong thời gian ngắn bằng các khoản tiền và tương đương tiền. Những chỉ số này khẳng định sức khỏe tài chính doanh nghiệp tốt trong ngắn hạn. Tuy nhiên, cần chú ý phân phối vốn đầu tư hiệu quả để tối ưu hóa lợi nhuận."
                else:
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, cao hơn 2.5 cho thấy công ty có khả năng thanh toán các khoản nợ ngắn hạn. Tuy nhiên, tỷ lệ thanh toán bằng tiền mặt (Cash Ratio) là {cash_ratio:.2f}, cho thấy công ty có thể gặp khó khăn trong việc thanh toán nhanh chóng, tức thời các khoản nợ ngắn hạn. Mặt khác, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f}, cao hơn 1.5 cho thấy công ty có khả năng thanh toán ngắn hạn mà không bị phụ thuộc vào hàng tồn kho. Điều này có thể làm giảm rủi ro tài chính trong ngắn hạn."
            else:
                if cash_ratio > 1:
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, cao hơn 2.5 cho thấy công ty có khả năng thanh toán các khoản nợ ngắn hạn. Đồng thời, tỷ lệ thanh toán bằng tiền mặt (Cash Ratio) là {cash_ratio:.2f}, cho thấy công ty có khả năng thanh toán nhanh chóng, trong thời gian ngắn bằng các khoản tiền và tương đương tiền. Điều này vẫn giữ được sức khỏe tài chính của doanh nghiệp trong ngắn hạn. Tuy nhiên, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f}, thấp hơn 1.5 cho thấy tài sản ngắn hạn của doanh nghiệp ở hàng tồn kho chiếm tỷ trọng tương đối lớn. Đồng thời, cần chú ý phân phối vốn đầu tư hiệu quả để tối ưu hóa lợi nhuận."
                else:
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, cao hơn 2.5 cho thấy công ty có khả năng thanh toán các khoản nợ ngắn hạn. Tuy nhiên, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f}, thấp hơn 1.5 cho thấy tài sản ngắn hạn của doanh nghiệp ở hàng tồn kho chiếm tỷ trọng tương đối lớn. Ngoài ra, tỷ lệ thanh toán bằng tiền mặt (Cash Ratio) là {cash_ratio:.2f}, cho thấy công ty có thể gặp khó khăn trong việc thanh toán nhanh chóng, tức thời các khoản nợ ngắn hạn. Những chỉ số này có thể làm tăng rủi ro tài chính trong ngắn hạn, thể hiện cơ cấu trong tài sản ngắn hạn không phù hợp, cần thực hiện các chiến lược thay đổi hoạt động kinh doanh."
        elif current_ratio > 1:
            if quick_ratio > 1.5:
                if cash_ratio > 1:
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, cao hơn 1 cho thấy công ty có khả năng thanh toán các khoản nợ ngắn hạn. Bên cạnh đó, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f}, cao hơn 1.5 cho thấy công ty có khả năng thanh toán ngắn hạn mà không bị phụ thuộc vào hàng tồn kho. Đồng thời, tỷ lệ thanh toán bằng tiền mặt (Cash Ratio) là {cash_ratio:.2f}, cho thấy công ty có khả năng thanh toán nhanh chóng, trong thời gian ngắn bằng các khoản tiền và tương đương tiền. Những chỉ số này khẳng định sức khỏe tài chính doanh nghiệp tốt trong ngắn hạn."
                else:
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, cao hơn 1 cho thấy công ty có khả năng thanh toán các khoản nợ ngắn hạn. Tuy nhiên, tỷ lệ thanh toán bằng tiền mặt (Cash Ratio) là {cash_ratio:.2f}, cho thấy công ty có thể gặp khó khăn trong việc thanh toán nhanh chóng, tức thời các khoản nợ ngắn hạn. Mặt khác, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f}, cao hơn 1.5 cho thấy công ty có khả năng thanh toán ngắn hạn mà không bị phụ thuộc vào hàng tồn kho. Điều này có thể làm giảm rủi ro tài chính trong ngắn hạn."
            else:
                if cash_ratio > 1:
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, cao hơn 1 cho thấy công ty có khả năng thanh toán các khoản nợ ngắn hạn. Đồng thời, tỷ lệ thanh toán bằng tiền mặt (Cash Ratio) là {cash_ratio:.2f}, cho thấy công ty có khả năng thanh toán nhanh chóng, trong thời gian ngắn bằng các khoản tiền và tương đương tiền. Điều này vẫn giữ được sức khỏe tài chính của doanh nghiệp trong ngắn hạn. Tuy nhiên, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f}, thấp hơn 1.5 cho thấy tài sản ngắn hạn của doanh nghiệp ở hàng tồn kho chiếm tỷ trọng tương đối lớn."
                else:
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, cao hơn 1 cho thấy công ty có khả năng thanh toán các khoản nợ ngắn hạn. Tuy nhiên, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f}, thấp hơn 1.5 cho thấy tài sản ngắn hạn của doanh nghiệp ở hàng tồn kho chiếm tỷ trọng tương đối lớn. Ngoài ra, tỷ lệ thanh toán bằng tiền mặt (Cash Ratio) là {cash_ratio:.2f}, cho thấy công ty có thể gặp khó khăn trong việc thanh toán nhanh chóng, tức thời các khoản nợ ngắn hạn. Những chỉ số này có thể làm tăng rủi ro tài chính trong ngắn hạn, thể hiện cơ cấu trong tài sản ngắn hạn không phù hợp, cần thực hiện các chiến lược thay đổi hoạt động kinh doanh."
        else:
            if quick_ratio < 0.4:
                if cash_ratio < 0.2:    
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, thấp hơn 1 cho thấy công ty có khả năng thanh toán nợ ngắn hạn không tốt. Đồng thời, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f} thấp cho thấy công ty có thể gặp khó khăn trong việc thanh toán nhanh chóng, tức thời các khoản nợ ngắn hạn do tài sản phụ thuộc vào hàng tồn kho. Hơn nữa, tỷ lệ thanh toán bằng tiền mặt (Cash Ratio) là {cash_ratio:.2f} rất thấp. Doanh nghiệp có sức khỏe tài chính rất kém, có nguy cơ phá sản cao. Cần phải chú ý đến việc quản lý tài chính, tăng cường thanh khoản và giảm rủi ro tài chính trong ngắn hạn."
                else:
                    liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, thấp hơn 1 cho thấy công ty có khả năng thanh toán nợ ngắn hạn không tốt. Đồng thời, tỷ lệ thanh toán nhanh (Quick Ratio) là {quick_ratio:.2f} thấp cho thấy công ty có thể gặp khó khăn trong việc thanh toán nhanh chóng, tức thời các khoản nợ ngắn hạn do tài sản phụ thuộc vào hàng tồn kho. Doanh nghiệp có sức khỏe tài chính kém, có nguy cơ phá sản. Cần phải chú ý đến việc quản lý tài chính, tăng cường thanh khoản và giảm rủi ro tài chính trong ngắn hạn."
            else:
                liquidity_evaluate = f"Tỷ lệ thanh toán ngắn hạn (Current Ratio) của công ty {company_code} là {current_ratio:.2f}, thấp hơn 1 cho thấy công ty có khả năng thanh toán nợ ngắn hạn không tốt. Cần phải chú ý đến việc quản lý tài chính, tăng cường thanh khoản và giảm rủi ro tài chính trong ngắn hạn để tránh nguy cơ phá sản."
        evaluate_health.append(liquidity_evaluate)

        # Bước 2: Đánh giá hoạt động kinh doanh 
        # 1. Biên lợi nhuận thuần từ hoạt động kinh doanh (Gross Margin)
        gross_margin = df_all_company[df_all_company['Mã CP'] == company_code]['Biên LN thuần từ HDKD'].values[0]
        avg_gross_margin = calculate_average_ratio(industry_companies, df_all_company, 'gross_margin')
        if gross_margin > avg_gross_margin:
            gross_margin_evaluate = f"Biên lợi nhuận thuần từ hoạt động kinh doanh của công ty {company_code} là {(gross_margin * 100):.2f}%, cao hơn so với trung bình ngành ({(avg_gross_margin * 100):.2f}%) cho thấy công ty có khả năng sinh lời tốt hơn các doanh nghiệp cùng ngành."
            # if gross_margin > 0.5:
            #     gross_margin_evaluate += " Biên lợi nhuận thuần cao cho thấy hiệu quả trong hoạt động kinh doanh của doanh nghiệp và có thể mở rộng hoạt động kinh doanh."
        else:
            gross_margin_evaluate = f"Biên lợi nhuận thuần từ hoạt động kinh doanh của công ty {company_code} là {(gross_margin * 100):.2f}%, thấp hơn so với trung bình ngành ({(avg_gross_margin * 100):.2f}%) cho thấy công ty có khả năng sinh lời kém hơn các doanh nghiệp cùng ngành."
            # if gross_margin < 0.1:
            #     gross_margin_evaluate += " Biên lợi nhuận thuần thấp có thể cho thấy doanh nghiệp đang gặp khó khăn trong hoạt động kinh doanh, doanh thu tập trung vào giá vốn hàng bán và các chi phí (chi phí bán hàng, chi phí quản lý ...)."
            # if gross_margin < 0:
            #     gross_margin_evaluate += " Đồng thời, biên lợi nhuận âm cho thấy doanh nghiệp đang hoạt động không hiệu quả, gặp khó khăn trong việc sinh lời từ hoạt động kinh doanh, cần phải tái cấu trúc cách hoạt động và thay đổi quy trình kinh doanh."
        evaluate_activity.append(gross_margin_evaluate)

        # 2. Tốc độ quay vòng tài sản (Asset Turnover)
        total_assets = df_cdkt[df_cdkt['Quý'] == "TỔNG CỘNG TÀI SẢN"]["Quý 1 - 2024"].values[0]
        total_revenue = df_kqhdkd[df_kqhdkd['Quý'] == "3. Doanh thu thuần về bán hàng và cung cấp dịch vụ (10 = 01 - 02)"]["Quý 1 - 2024"].values[0]
        asset_turnover = total_revenue / total_assets
        avg_asset_turnover = calculate_average_ratio(industry_companies, df_all_company, 'asset_turnover')
        total_assets_last_year = df_cdkt[df_cdkt['Quý'] == "TỔNG CỘNG TÀI SẢN"]["Quý 1 - 2023"].values[0]
        total_revenue_last_year = df_kqhdkd[df_kqhdkd['Quý'] == "3. Doanh thu thuần về bán hàng và cung cấp dịch vụ (10 = 01 - 02)"]["Quý 1 - 2023"].values[0]
        asset_turnover_last_year = total_revenue_last_year / total_assets_last_year
        if asset_turnover > avg_asset_turnover:
            asset_turnover_evaluate = f"Tốc độ quay vòng tài sản của công ty {company_code} là {(asset_turnover):.2f}%, cao hơn so với trung bình ngành ({(avg_asset_turnover):.2f}%) cho thấy công ty quản lý, đầu tư và sử dụng tài sản hiệu quả hơn các doanh nghiệp cùng ngành."
            if asset_turnover > asset_turnover_last_year:
                asset_turnover_evaluate += " Hơn nữa, tốc độ quay vòng tài sản tăng so với cùng kỳ năm trước cho thấy công ty đang phát triển hoạt động kinh doanh, tăng cường thị phần và cơ hội sinh lời."
        else:
            asset_turnover_evaluate = f"Tốc độ quay vòng tài sản của công ty {company_code} là {(asset_turnover):.2f}%, thấp hơn so với trung bình ngành ({(avg_asset_turnover):.2f}%) cho thấy công ty quản lý, đầu tư và sử dụng tài sản chưa hiệu quả bằng các doanh nghiệp cùng ngành."
            if asset_turnover < asset_turnover_last_year:
                asset_turnover_evaluate += " Bên cạnh đó, tốc độ quay vòng tài sản giảm so với cùng kỳ năm trước cho thấy công ty đang gặp khó khăn trong hoạt động kinh doanh, cần phải tìm kiếm cơ hội mới để phát triển, sử dụng hiệu quả hơn nữa các nguồn lực."
        evaluate_activity.append(asset_turnover_evaluate)

        # 3. ROA (Return on Assets) - Tỷ suất sinh lời trên tài sản
        roa = df_all_company[df_all_company['Mã CP'] == company_code]['ROA'].values[0]
        avg_roa = calculate_average_ratio(industry_companies, df_all_company, 'roa')
        if roa > avg_roa:
            roa_evaluate = f"Tỷ suất sinh lời trên tài sản ROA của công ty {company_code} là {(roa * 100):.2f}%, cao hơn so với trung bình ngành ({(avg_roa * 100):.2f}%) cho thấy công ty sinh lời hiệu quả hơn các doanh nghiệp cùng ngành, thể hiện tính hiệu quả của doanh nghiệp trong quá trình tổ chức, quản lý và thực hiện hoạt động kinh doanh."
        else:
            roa_evaluate = f"Tỷ suất sinh lời trên tài sản ROA của công ty {company_code} là {(roa * 100):.2f}%, thấp hơn so với trung bình ngành ({(avg_roa * 100):.2f}%) cho thấy công ty sinh lời kém hơn các doanh nghiệp cùng ngành, thể hiện sự chưa hiệu quả trong quá trình tổ chức, quản lý và thực hiện hoạt động kinh doanh."
        evaluate_activity.append(roa_evaluate)

        # 4. ROE (Return on Equity) - Tỷ suất sinh lời trên vốn chủ sở hữu
        roe = df_all_company[df_all_company['Mã CP'] == company_code]['ROE'].values[0]
        avg_roe = calculate_average_ratio(industry_companies, df_all_company, 'roe')
        if roe > avg_roe:
            roe_evaluate = f"Tỷ suất sinh lời trên vốn chủ sở hữu ROE của công ty {company_code} là {(roe * 100):.2f}%, cao hơn so với trung bình ngành ({(avg_roe * 100):.2f}%) cho thấy doanh nghiệp đang sử dụng vốn sở hữu hiệu quả hơn các doanh nghiệp cùng ngành."
        else:
            roe_evaluate = f"Tỷ suất sinh lời trên vốn chủ sở hữu ROE của công ty {company_code} là {(roe * 100):.2f}%, thấp hơn so với trung bình ngành ({(avg_roe * 100):.2f}%) cho thấy doanh nghiệp chưa sử dụng vốn sở hữu hiệu quả như các doanh nghiệp cùng ngành."
        evaluate_activity.append(roe_evaluate)

        # Bước 3: Đánh giá tốc độ tăng trưởng 
        # 1. Tăng trưởng doanh thu (Revenue Growth)   
        # revenue_growth, profit_growth = calculate_revenue_growth_and_profit_growth_four_quarters(company_code)
        revenue_growth = df_all_company[df_all_company['Mã CP'] == company_code]['Tăng trưởng DT (tỷ đồng) - 4 Quý'].values[0]
        profit_growth = df_all_company[df_all_company['Mã CP'] == company_code]['Tăng trưởng lợi nhuận (tỷ đồng) - 4 Quý'].values[0]
        avg_revenue_growth= calculate_average_ratio(industry_companies, df_all_company, 'revenue_growth')
        avg_profit_growth= calculate_average_ratio(industry_companies, df_all_company, 'profit_growth')

        if revenue_growth > avg_revenue_growth:
            revenue_growth_evaluate = f"Tốc độ tăng trưởng doanh thu của công ty {company_code} là {(revenue_growth):.2f}%, cao hơn so với trung bình ngành ({(avg_revenue_growth):.2f}%) cho thấy công ty đang phát triển mạnh mẽ hơn các doanh nghiệp cùng ngành."
        else:
            revenue_growth_evaluate = f"Tốc độ tăng trưởng doanh thu của công ty {company_code} là {(revenue_growth):.2f}%, thấp hơn so với trung bình ngành ({(avg_revenue_growth):.2f}%) cho thấy công ty đang phát triển chậm hơn các doanh nghiệp cùng ngành."

        # 2. Tăng trưởng lợi nhuận (Profit Growth)
        if profit_growth > avg_profit_growth:
            revenue_growth_evaluate += f" Tốc độ tăng trưởng lợi nhuận của công ty {company_code} là {(profit_growth):.2f}%, cao hơn so với trung bình ngành ({(avg_profit_growth):.2f}%) cho thấy công ty đang kinh doanh rất tốt và có khả năng quản lý chi phí hiệu quả hơn các doanh nghiệp cùng ngành."
        else:
            revenue_growth_evaluate += f" Tốc độ tăng trưởng lợi nhuận của công ty {company_code} là {(profit_growth):.2f}%, thấp hơn so với trung bình ngành ({(avg_profit_growth):.2f}%) cho thấy công ty đang kinh doanh chưa hiệu quả bằng các doanh nghiệp cùng ngành."
        
        # if (profit_growth < 0 and avg_profit_growth < 0) or (revenue_growth < 0 and avg_revenue_growth < 0):
        #     revenue_growth_evaluate += " Bên cạnh đó, tốc độ tăng trưởng âm trong tình hình tốc độ tăng trưởng trung bình ngành âm có thể do các yếu tố thị trường tác động, doanh nghiệp cần phân tích kỹ lưỡng để hiểu nguyên nhân và có biện pháp kịp thời."
        # if (profit_growth < 0 and avg_profit_growth > 0) or (revenue_growth < 0 and avg_revenue_growth > 0):
        #     revenue_growth_evaluate += " Bên cạnh đó, tốc độ tăng trưởng âm trong tình hình tốc độ tăng trưởng trung bình ngành dương có thể do doanh nghiệp gặp khó khăn trong hoạt động kinh doanh, cần phải phân tích chi tiết nguyên nhân và tìm kiếm cơ hội mới để phát triển."
        evaluate_growth.append(revenue_growth_evaluate)

        # Bước 4: Lấy điểm đánh giá doanh nghiệp từ mô hình
        score = df_all_company[df_all_company['Mã CP'] == company_code]['Score'].values[0]

        return jsonify({
            'health': evaluate_health,
            'activity': evaluate_activity,
            'growth': evaluate_growth,
            'score': score
        })

    except Exception as e:
        print(f"Lỗi xử lý dữ liệu: {e}")
        return jsonify({'error': 'Lỗi xử lý dữ liệu'}), 500

if __name__ == '__main__':
    app.run(debug=True)
