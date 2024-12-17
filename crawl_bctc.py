import time
import pandas as pd
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver  

# Đường dẫn đến ChromeDriver (Cập nhật đường dẫn phù hợp với hệ thống của bạn)
chrome_driver_path = "C:/Users/ADMIN/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe"

# Tạo đối tượng Service với đường dẫn ChromeDriver
service = Service(executable_path=chrome_driver_path)

# Khởi tạo trình duyệt Chrome với Service
driver = webdriver.Chrome(service=service)

company_code = "ssi"
company_code_upper = company_code.upper()

# list_index_url = ["2019/1/-20", "2020/1/-16", "2021/1/-12", "2022/1/-8", "2023/1/-4", "2024/1/0"]
list_index_url = ["2019/1/0/0", "2020/1/0/0", "2021/1/0/0", "2022/1/0/0", "2023/1/0/0", "2024/1/0/0"]
excel_path = f"bctc/Can_doi_ke_toan_{company_code_upper}.xlsx"
df_final = pd.DataFrame()

for ind, index_url in enumerate(list_index_url, 1):
    url = "https://s.cafef.vn/bao-cao-tai-chinh/" + company_code + "/bsheet/" + index_url + "/bao-cao-tai-chinh-.chn"
    driver = webdriver.Chrome(service=service)
    driver.get(url)
    time.sleep(5)

    table = driver.find_element(By.ID, "tableContent")
    table_html = table.get_attribute('outerHTML')
    df = pd.read_html(table_html)[0]
    df = df.drop(df.columns[-2:], axis=1)

    # Kiểm tra nếu ind = 1 thì df_final = df, nếu không thì df_final = df_final + df(4 cột cuối cùng)
    if ind == 1:
        df_final = df
    else:
        df_final = pd.concat([df_final, df.iloc[:, -4:]], axis=1)

    driver.quit()


# Lưu DataFrame vào file Excel
df_final.to_excel(excel_path, index=False)
df_final = pd.read_excel(excel_path)
df_final = df_final.dropna(how='all')
df_final.loc[0] = ["Quý", "Quý 2 - 2018", "Quý 3 - 2018", "Quý 4 - 2018", "Quý 1 - 2019", 
                   "Quý 2 - 2019", "Quý 3 - 2019", "Quý 4 - 2019", "Quý 1 - 2020",
                   "Quý 2 - 2020", "Quý 3 - 2020", "Quý 4 - 2020", "Quý 1 - 2021",
                   "Quý 2 - 2021", "Quý 3 - 2021", "Quý 4 - 2021", "Quý 1 - 2022",
                   "Quý 2 - 2022", "Quý 3 - 2022", "Quý 4 - 2022", "Quý 1 - 2023",
                   "Quý 2 - 2023", "Quý 3 - 2023", "Quý 4 - 2023", "Quý 1 - 2024"] + [""] * (df_final.shape[1] - 25)
# df_final.loc[0](["Quý", "Quý 2 - 2018", "Quý 3 - 2018", "Quý 4 - 2018", "Quý 1 - 2019", "Quý 2 - 2019", "Quý 3 - 2019", "Quý 4 - 2019", "Quý 1 - 2020", "Quý 2 - 2020", "Quý 3 - 2020", "Quý 4 - 2020", "Quý 1 - 2021", "Quý 2 - 2021", "Quý 3 - 2021", "Quý 4 - 2021", "Quý 1 - 2022", "Quý 2 - 2022", "Quý 3 - 2022", "Quý 4 - 2022", "Quý 1 - 2023", "Quý 2 - 2023", "Quý 3 - 2023", "Quý 4 - 2023", "Quý 1 - 2024"], True)
df_final.to_excel(excel_path, index=False)
print("Dữ liệu đã được lưu thành công vào file Excel.")

# Đóng trình duyệt
driver.quit()

# url = "https://s.cafef.vn/bao-cao-tai-chinh/vnm/bsheet/2024/1/0/0/bao-cao-tai-chinh-.chn"
# driver.get(url)

# # Chờ một chút để trang tải hoàn toàn
# time.sleep(5)

# # Tìm bảng có id="tableContent"
# table = driver.find_element(By.ID, "tableContent")

# # Lấy dữ liệu từ bảng và chuyển đổi thành DataFrame của pandas
# table_html = table.get_attribute('outerHTML')
# df = pd.read_html(table_html)[0]

# # Xóa 2 cột cuối cùng
# df = df.drop(df.columns[-2:], axis=1)

# # Lưu DataFrame vào file Excel
# df.to_excel("Can_doi_ke_toan_VNM.xlsx", index=False)

# # Kiểm tra file excel được lưu, nếu dòng nào không chứa bất kỳ dữ liệu nào thì xóa dòng đó
# df = pd.read_excel("Can_doi_ke_toan_VNM.xlsx")
# df = df.dropna(how='all')
# df.to_excel("Can_doi_ke_toan_VNM.xlsx", index=False)

# print("Dữ liệu đã được lưu thành công vào file Excel.")

# # Đóng trình duyệt
# driver.quit()
