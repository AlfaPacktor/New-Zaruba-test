import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Список сотрудников и продуктов
EMPLOYEES = [
    "Константинов Я.",
    "Михно Д.",
    "Ласковая А.",
    "Фельдман Л.",
    "Орлик Л.",
    "Шевчак В.",
    "Колесникова А.",
    "Шувалов И.",
    "Шабунина Д.",
    "Мысин А.",
    "Сайбель С."
]

PRODUCTS = [
    "Кредит Наличными",
    "КСП",
    "ДК на 3 лицо"
]

SHEET_NAME = "sales_competition"
WORKSHEET = "data"

# -----------------------
# Подключение к Google Sheets
# -----------------------
@st.cache_resource
def connect_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1BQrUxvUsewpOfgOU7Mzr8I668oadQdn6o51xzJESuJs").worksheet(WORKSHEET)
    return sheet

# -----------------------
# Загрузка данных
# -----------------------
def load_data():
    sheet = connect_sheet()
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["employee", "product", "value"])
    
    df = pd.DataFrame(data)
    
    # Приводим value к числу
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)
    
    return df

# -----------------------
# Обновление данных
# -----------------------
def update_value(employee, product, value, operation):
    sheet = connect_sheet()
    df = load_data()
    row = df[(df["employee"] == employee) & (df["product"] == product)]

    if row.empty:
        new_value = value if operation == "+" else -value
        sheet.append_row([employee, product, int(new_value)])
    else:
        index = row.index[0]
        current = float(row.iloc[0]["value"])

        if operation == "+":
            new_value = current + value
        else:
            new_value = current - value

        cell_row = index + 2
        sheet.update_cell(cell_row, 3, int(new_value))

# -----------------------
# Ввод данных
# -----------------------
def input_section():
    st.header("Ввод данных")
    employee = st.selectbox("Выберите сотрудника", EMPLOYEES)
    entries = {}

    for product in PRODUCTS:
        col1, col2 = st.columns([3, 1])
        with col1:
            value = st.number_input(product, min_value=0, step=1, key=f"value_{product}")
        with col2:
            operation = st.radio("Операция", ["+", "-"], horizontal=True, key=f"op_{product}")
        entries[product] = (value, operation)

    # КНОПКИ
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Принять данные"):
            for product, (value, operation) in entries.items():
                if value > 0:
                    update_value(employee, product, value, operation)
            st.success("Данные обновлены")
            st.rerun()

    with col2:
        st.link_button(
            "Заруба Хантеров",
            "https://hunterfight.streamlit.app/"
        )

# -----------------------
# Рейтинг сотрудников
# -----------------------
def leaderboard():
    st.header("Рейтинг")
    df = load_data()
    if df.empty:
        st.info("Пока нет данных")
        return
    tabs = st.tabs(PRODUCTS)
    for i, product in enumerate(PRODUCTS):
        with tabs[i]:
            product_df = df[df["product"] == product]
            ranking = []
            for emp in EMPLOYEES:
                row = product_df[product_df["employee"] == emp]
                value = row["value"].sum() if not row.empty else 0
                ranking.append({"Сотрудник": emp, "Продажи": value})
            ranking_df = pd.DataFrame(ranking)
            ranking_df = ranking_df.sort_values(by="Продажи", ascending=False).reset_index(drop=True)
            ranking_df.index += 1
            st.dataframe(ranking_df, use_container_width=True)

# -----------------------
# Главная функция
# -----------------------
def main():
    st.set_page_config(page_title="Конкурс продаж", layout="wide")

    st.markdown("""
    <style>
    a[data-testid="stLinkButton"] {
        background-color: #1f1f1f;
        color: white !important;
        padding: 10px 16px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
    }
    a[data-testid="stLinkButton"]:hover {
        background-color: #333333;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🏆 Конкурс продаж")
    input_section()
    st.divider()
    leaderboard()

if __name__ == "__main__":
    main()
