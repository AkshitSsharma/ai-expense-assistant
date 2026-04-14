import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.title("💰 Hanks AI Expense Dashboard")

conn = sqlite3.connect("expenses.db")
df = pd.read_sql_query("SELECT * FROM expenses", conn)

if df.empty:
    st.warning("No data yet")
else:
    df["date"] = pd.to_datetime(df["date"])

    # ---------- TOTAL ----------
    total = df["amount"].sum()
    st.metric("Total Spending", f"₹{total:,}")

    # ---------- CATEGORY PIE ----------
    st.subheader("Category Distribution")
    cat_data = df.groupby("category")["amount"].sum()

    fig1, ax1 = plt.subplots()
    ax1.pie(cat_data, labels=cat_data.index, autopct='%1.1f%%')
    st.pyplot(fig1)

    # ---------- BAR CHART ----------
    st.subheader("Spending by Category")
    fig2, ax2 = plt.subplots()
    cat_data.plot(kind="bar", ax=ax2)
    st.pyplot(fig2)

    # ---------- DAILY TREND ----------
    st.subheader("Daily Spending Trend")
    daily = df.groupby("date")["amount"].sum()

    fig3, ax3 = plt.subplots()
    daily.plot(ax=ax3)
    st.pyplot(fig3)

    # ---------- TABLE ----------
    st.subheader("All Transactions")
    st.dataframe(df)