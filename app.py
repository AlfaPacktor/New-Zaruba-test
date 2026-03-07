import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

EMPLOYEES = [
    "Константинов Я.",
    "Михно Д.",
    "Ласковая А.",
    "Фельдман Л.",
    "Орлик Л.",
    "Шевчак В.",
    "Колесникова А.",
    "Шувалов И.",
    "Шабунина Д."
]

PRODUCTS = [
    "Кредит Наличными",
    "Коробочное Страхование"
]


SHEET_NAME = "sales_competition"
WORKSHEET = "data"


# -----------------------
# подключение к Google Sheets
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

    sheet = client.open(SHEET_NAME).worksheet(WORKSHEET)

    return sheet


# -----------------------
# загрузка данных
# -----------------------

def load_data():

    sheet = connect_sheet()

    data = sheet.get_all_records()

    if not data:
        return pd.DataFrame(columns=["employee", "product", "value"])

    return pd.DataFrame(data)


# -----------------------
# обновление значения
# -----------------------

def update_value(employee, product, value, operation):

    sheet = connect_sheet()

    data = load_data()

    row = data[
        (data["employee"] == employee) &
        (data["product"] == product)
    ]

    if row.empty:

        new_value = value if operation == "+" else -value

        sheet.append_row([employee, product, new_value])

    else:

        index = row.index[0]

        current = row.iloc[0]["value"]

        if operation == "+":
            new_value = current + value
        else:
            new_value = current - value

        cell_row = index + 2

        sheet.update_cell(cell_row, 3, new_value)


# -----------------------
# ввод данных
# -----------------------

def input_section():

    st.header("Ввод данных")

    employee = st.selectbox(
        "Выберите сотрудника",
        EMPLOYEES
    )

    entries = {}

    for product in PRODUCTS:

        col1, col2 = st.columns([3, 1])

        with col1:
            value = st.number_input(
                product,
                min_value=0,
                step=1,
                key=f"value_{product}"
            )

        with col2:
            operation = st.radio(
                "Операция",
                ["+", "-"],
                horizontal=True,
                key=f"op_{product}"
            )

        entries[product] = (value, operation)

    if st.button("Принять данные"):

        for product, (value, operation) in entries.items():

            if value > 0:

                update_value(employee, product, value, operation)

        st.success("Данные обновлены")

        st.rerun()


# -----------------------
# рейтинг
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

                row = product_df[
                    product_df["employee"] == emp
                ]

                value = row["value"].sum() if not row.empty else 0

                ranking.append({
                    "Сотрудник": emp,
                    "Продажи": value
                })

            ranking_df = pd.DataFrame(ranking)

            ranking_df = ranking_df.sort_values(
                by="Продажи",
                ascending=False
            ).reset_index(drop=True)

            ranking_df.index += 1

            st.dataframe(
                ranking_df,
                use_container_width=True
            )


# -----------------------
# main
# -----------------------

def main():

    st.set_page_config(
        page_title="Конкурс продаж",
        layout="wide"
    )

    st.title("🏆 Конкурс продаж")

    input_section()

    st.divider()

    leaderboard()


if name == "__main__":
    main()
    
