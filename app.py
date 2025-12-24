import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# ==========================
# Number formatting (Indian currency)
# ==========================
def format_currency(val):
    try:
        val = int(val)
    except:
        return "₹ 0"

    s = str(val)
    if len(s) <= 3:
        return f"₹ {s}"
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        formatted = ",".join(parts) + "," + last3
        return f"₹ {formatted}"

# ==========================
# Load dataset & train model
# ==========================
df = pd.read_excel("RetailChain_Financials.xlsx")

X = df[['Marketing_Spend', 'Store_Ops_Cost', 'Online_Ops_Cost']]
y = df['Revenue']

model = LinearRegression()
model.fit(X, y)

# ==========================
# Tool functions
# ==========================
def forecast_tool(marketing, store, online):
    return model.predict([[marketing, store, online]])[0]

def roi_tool(revenue, marketing):
    return (revenue - marketing) / marketing

def profit_tool(revenue, store, online):
    return revenue - store - online

def margin_tool(profit, revenue):
    return (profit / revenue) * 100

def scenario_tool(base_marketing, delta):
    base = forecast_tool(base_marketing, 200000, 100000)
    new = forecast_tool(base_marketing + delta, 200000, 100000)
    return base, new

def extract_number(text):
    nums = [int(s) for s in text.split() if s.isdigit()]
    return nums[0] if nums else None

# ==========================
# Streamlit UI
# ==========================
st.title("💼 Financial Forecasting Agent")

tab_dash, tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Dashboard", "📈 Forecast & Metrics", "💸 Scenario Analysis",
     "📉 Charts", "🤖 Agent Chat", "📁 Raw Data"]
)

# ==========================
# TAB: DASHBOARD (UPDATED & CLEAN)
# ==========================
with tab_dash:
    st.markdown("""
        <style>
        div[data-testid="metric-container"] {
            background-color: #F8F9FA;
            border-radius: 10px;
            padding: 10px;
            margin: 5px;
            border: 1px solid #E0E0E0;
            box-shadow: 0px 1px 3px rgba(0,0,0,0.08);
        }
        div[data-testid="metric-container"] > div {
            font-size: 18px !important;
            color: #1A1A1A;
        }
        div[data-testid="metric-container"] label {
            font-size: 12px !important;
            color: #4F4F4F;
        }
        h1, h2, h3, h4 {
            color: #2E2E2E;
        }
        </style>
    """, unsafe_allow_html=True)

    st.header("📊 Business Dashboard")

    avg_rev = round(df['Revenue'].mean())
    avg_profit = round((df['Revenue'] - df['COGS'] - df['Store_Ops_Cost'] - df['Online_Ops_Cost']).mean())
    avg_marketing = round(df['Marketing_Spend'].mean())
    avg_margin = round(((df['Revenue'] - df['COGS'] - df['Store_Ops_Cost'] - df['Online_Ops_Cost']) / df['Revenue']).mean() * 100, 2)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Revenue", format_currency(avg_rev))
    col2.metric("Avg Profit", format_currency(avg_profit))
    col3.metric("Avg Marketing Spend", format_currency(avg_marketing))
    col4.metric("Avg Gross Margin", f"{avg_margin}%")

    st.markdown("---")

    st.subheader("Revenue Trend")

    fig, ax = plt.subplots()
    ax.plot(df['Month'], df['Revenue'], linewidth=2, color="#2E86C1")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# ==========================
# TAB: FORECAST & METRICS
# ==========================
with tab1:
    st.header("Forecast & Financial Metrics")

    marketing = st.slider("Marketing Spend", 50000, 500000, 200000, 10000)
    store = st.slider("Store Operations Cost", 100000, 300000, 200000, 10000)
    online = st.slider("Online Operations Cost", 50000, 200000, 100000, 5000)

    if st.button("Run Forecast"):
        revenue = forecast_tool(marketing, store, online)
        profit = profit_tool(revenue, store, online)
        margin = margin_tool(profit, revenue)
        roi = roi_tool(revenue, marketing)

        st.success(f"Projected Revenue: {format_currency(revenue)}")
        st.info(f"Projected Profit: {format_currency(profit)}")
        st.warning(f"Gross Margin: {round(margin, 2)}%")
        st.write(f"ROI: {round(roi, 2)}")

    if st.button("Export Results to Excel"):
        output = io.BytesIO()
        result_df = pd.DataFrame({
            "Marketing Spend": [marketing],
            "Store Ops Cost": [store],
            "Online Ops Cost": [online],
            "Revenue": [revenue],
            "Profit": [profit],
            "Gross Margin %": [margin],
            "ROI": [roi]
        })
        result_df.to_excel(output, index=False)
        st.download_button("Download Excel File", data=output.getvalue(),
                           file_name="financial_results.xlsx")

# ==========================
# TAB: SCENARIO ANALYSIS
# ==========================
with tab2:
    st.header("Scenario Analysis: Change Marketing")

    delta = st.slider("Increase Marketing by:", 10000, 100000, 50000, 5000)
    base, new = scenario_tool(200000, delta)

    st.write(f"Base Revenue: {format_currency(base)}")
    st.write(f"New Revenue (+₹{delta}): {format_currency(new)}")
    uplift = new - base
    st.success(f"Revenue Uplift: {format_currency(uplift)}")

# ==========================
# TAB: CHARTS
# ==========================
with tab3:
    st.header("Trend Charts")

    st.subheader("Marketing Spend vs Revenue")
    fig, ax = plt.subplots()
    ax.scatter(df['Marketing_Spend'], df['Revenue'])
    ax.set_xlabel("Marketing Spend")
    ax.set_ylabel("Revenue")
    ax.set_title("Marketing vs Revenue")
    st.pyplot(fig)

# ==========================
# TAB: AGENT CHAT
# ==========================
with tab4:
    st.header("Ask the Financial Agent")

    query = st.text_input("Ask your question:")

    if st.button("Submit"):
        q = query.lower()
        num = extract_number(q)

        if "forecast" in q:
            val = num if num else 200000
            revenue = forecast_tool(val, 200000, 100000)
            response = f"Projected revenue for {format_currency(val)} marketing is {format_currency(revenue)}."

        elif "roi" in q:
            val = num if num else 200000
            revenue = forecast_tool(val, 200000, 100000)
            roi = roi_tool(revenue, val)
            response = f"ROI for spend {format_currency(val)} is {round(roi,2)}."

        elif "profit" in q:
            revenue = forecast_tool(200000, 200000, 100000)
            response = f"Estimated profit: {format_currency(profit_tool(revenue,200000,100000))}."

        elif "increase" in q or "what if" in q:
            delta = num if num else 50000
            base, new = scenario_tool(200000, delta)
            response = f"Uplift for +{format_currency(delta)} is {format_currency(new-base)}."

        else:
            response = (
                "I can help with:\n"
                "- Revenue forecast\n"
                "- ROI\n"
                "- Profit\n"
                "- Marketing scenarios\n"
                "Try: 'Forecast revenue for 250000 marketing'"
            )

        st.write(response)

# ==========================
# TAB: RAW DATA
# ==========================
with tab5:
    st.header("Dataset")
    st.dataframe(df)
