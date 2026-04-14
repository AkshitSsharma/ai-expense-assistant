import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Hanks AI Expense Dashboard", layout="wide")

st.title("💰 Hanks AI Expense Dashboard")

# ---------- CONNECT DB ----------
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

# ✅ CREATE TABLE IF NOT EXISTS (FIX FOR DEPLOYMENT)
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    amount INTEGER,
    category TEXT,
    date TEXT
)
""")
conn.commit()

# ---------- LOAD DATA ----------
df = pd.read_sql_query("SELECT * FROM expenses", conn)

# ---------- IF EMPTY ----------
if df.empty:
    st.warning("No data yet. Add expenses using your voice assistant locally.")

else:
    df["date"] = pd.to_datetime(df["date"])

    # ---------- TOTAL ----------
    total = df["amount"].sum()
    st.metric("💸 Total Spending", f"₹{total:,}")

    col1, col2 = st.columns(2)

    # ---------- CATEGORY PIE ----------
    with col1:
        st.subheader("Category Distribution")
        cat_data = df.groupby("category")["amount"].sum()

        fig1, ax1 = plt.subplots()
        ax1.pie(cat_data, labels=cat_data.index, autopct='%1.1f%%')
        ax1.set_title("Category Split")
        st.pyplot(fig1)

    # ---------- BAR CHART ----------
    with col2:
        st.subheader("Spending by Category")
        fig2, ax2 = plt.subplots()
        cat_data.plot(kind="bar", ax=ax2)
        ax2.set_ylabel("Amount (₹)")
        ax2.set_title("Category Spending")
        st.pyplot(fig2)

    # ---------- DAILY TREND ----------
    st.subheader("📈 Daily Spending Trend")
    daily = df.groupby("date")["amount"].sum()

    fig3, ax3 = plt.subplots()
    daily.plot(ax=ax3)
    ax3.set_ylabel("Amount (₹)")
    ax3.set_title("Spending Over Time")
    st.pyplot(fig3)

    # ---------- TABLE ----------
    st.subheader("📋 All Transactions")
    st.dataframe(df, use_container_width=True)

# ---------- CLOSE DB ----------
conn.close()