import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Pizza Sales Analysis",
    layout="wide"
)

# ------------------ GLOBAL CSS ------------------
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; }
    h1 { text-align: center; margin-bottom: 0.2rem; }

    section[data-testid="stSidebar"] label {
        color: #000000 !important;
        font-weight: 500;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #d3d3d3 !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] > div:hover,
    section[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within {
        border-color: #bfbfbf !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="tag"] {
        background-color: #f0f0f0 !important;
        color: #000000 !important;
        border: none !important;
    }

    div[data-testid="stTabs"] div[role="tablist"] {
        justify-content: center;
    }

    div[data-testid="stTabs"] button[role="tab"] {
        font-size: 20px;
        font-weight: 600;
        padding: 12px 28px;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        border-bottom: 3px solid #000000;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------ HEADER ------------------
st.title("Pizza Sales Dashboard")

# ------------------ DATA ------------------
@st.cache_data
def load_data():
    df = pd.read_excel(
        r"C:\Users\ssing\Downloads\Data Model - Pizza Sales.xlsx\Data Model - Pizza Sales.xlsx"
    )
    df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
    df["order_month"] = pd.to_datetime(df["order_date"]).dt.month_name()
    df["order_month_num"] = pd.to_datetime(df["order_date"]).dt.month
    df["order_hour"] = df["order_time"].apply(lambda x: x.hour)

    def get_daytime(h):
        if h < 12:
            return "Morning"
        elif h < 17:
            return "Afternoon"
        elif h < 21:
            return "Evening"
        else:
            return "Night"

    df["Daytime"] = df["order_hour"].apply(get_daytime)
    df["ingredient_list"] = df["pizza_ingredients"].astype(str).str.split(",")

    return df

df = load_data()

# ------------------ FILTERS ------------------
# st.sidebar.header("Filters")

month_df = (
    df[["order_month", "order_month_num"]]
    .drop_duplicates()
    .sort_values("order_month_num")
)
MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

months = (
    month_df["order_month"]
    .dropna()
    .unique()
    .tolist()
)

# keep only months that exist in data, but in correct order
months_sorted = [m for m in MONTH_ORDER if m in months]

months_with_all = ["All"] + months_sorted

selected_months = st.sidebar.multiselect(
    "Month",
    options=months_with_all,
    default=["All"]
)



category_filter = st.sidebar.multiselect(
    "Pizza Category",
    options=sorted(df["pizza_category"].unique()),
    default=sorted(df["pizza_category"].unique())
)

size_filter = st.sidebar.multiselect(
    "Pizza Size",
    options=sorted(df["pizza_size"].unique()),
    default=sorted(df["pizza_size"].unique())
)
if "All" in selected_months:
    filtered_months = months   # means no filtering
else:
    filtered_months = selected_months

filtered_df = df.copy()
if selected_months:
    filtered_df = filtered_df[filtered_df["order_month"].isin(filtered_months)]
if category_filter:
    filtered_df = filtered_df[filtered_df["pizza_category"].isin(category_filter)]
if size_filter:
    filtered_df = filtered_df[filtered_df["pizza_size"].isin(size_filter)]

if filtered_df.empty:
    st.info("No data available")
    st.stop()

# ------------------ KPIs ------------------
total_revenue = int(filtered_df["total_price"].sum())
total_orders = int(filtered_df["order_id"].nunique())
total_pizzas = int(filtered_df["quantity"].sum())
avg_order_value = int(total_revenue / total_orders)
avg_pizzas_per_order = round(total_pizzas / total_orders, 2)

top_pizza = (
    filtered_df.groupby("pizza_name")["total_price"]
    .sum()
    .idxmax()
)

def kpi_card(title, value):
    st.markdown(
        f"""
        <div style="height:90px;padding:12px;border-radius:10px;
        background-color:#f2f3f5;text-align:center;">
            <div style="font-size:11px;color:#444";font-weight:500>{title}</div>
            <div style="font-size:25px;font-weight:600">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------ TABS ------------------
overview, trends, product_mix, demand,insights = st.tabs(
    ["Overview", "Trends", "Product Mix", "Demand Pattern","Conclusion and Key Insights"]
)

# ------------------ OVERVIEW ------------------
with overview:
    st.markdown("### Key Metrics")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("Total Revenue ($)", total_revenue)
    with c2: kpi_card("Total Orders", total_orders)
    with c3: kpi_card("Total Pizzas Sold", total_pizzas)
    with c4: kpi_card("Average Order Value ($)", avg_order_value)
    with c5: kpi_card("Average Pizzas per Order", avg_pizzas_per_order)

    st.markdown("### Top Performing Product")
    kpi_card("Highest Revenue Pizza", top_pizza)

# ------------------ TRENDS ------------------
with trends:
    st.markdown("### Revenue and Order Trends")

    trend_view = st.radio("Trend Granularity", ["Daily", "Monthly"], horizontal=True)

    if trend_view == "Daily":
        trend_df = filtered_df.groupby("order_date").agg(
            revenue=("total_price", "sum"),
            orders=("order_id", "nunique")
        ).reset_index()
        x_col, x_label = "order_date", "Order Date"
    else:
        trend_df = filtered_df.groupby("order_month").agg(
            revenue=("total_price", "sum"),
            orders=("order_id", "nunique")
        ).reset_index()
        x_col, x_label = "order_month", "Order Month"

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(
            trend_df, x=x_col, y="revenue",
            title="Revenue Trend Over Time",
            labels={"revenue": "Revenue", x_col: x_label},
            color_discrete_sequence=["#C94A4A"]
        )
        fig.update_layout(title_x=0.2, yaxis_tickformat="d")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(
            trend_df, x=x_col, y="orders",
            title="Order Volume Trend Over Time",
            labels={"orders": "Number of Orders", x_col: x_label},
            color_discrete_sequence=["#6B8E23"]
        )
        fig.update_layout(title_x=0.2, yaxis_tickformat="d")
        st.plotly_chart(fig, use_container_width=True)

# ------------------ PRODUCT MIX ------------------
with product_mix:
    st.markdown("### Revenue Contribution by Product")

    col1, col2, col3 = st.columns(3)

    with col1:
        fig = px.pie(
            filtered_df.groupby("pizza_category")["total_price"].sum().reset_index(),
            names="pizza_category", values="total_price",
            title="Revenue Share by Pizza Category",
            hole=0.4,
            color_discrete_sequence=["#C94A4A", "#6B8E23", "#A47551", "#8FBC8F"]
        )
        fig.update_layout(title_x=0.0)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            filtered_df.groupby("pizza_size")["total_price"].sum().reset_index(),
            x="pizza_size", y="total_price",
            title="Revenue by Pizza Size",
            labels={"pizza_size": "Pizza Size", "total_price": "Revenue"},
            color_discrete_sequence=["#A47551"]
        )
        fig.update_layout(title_x=0.2, yaxis_tickformat="d")
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        fig = px.bar(
            filtered_df.groupby(["pizza_category", "pizza_size"])["total_price"].sum().reset_index(),
            x="pizza_category", y="total_price", color="pizza_size",
            title="Category and Size Revenue Mix",
            labels={"pizza_category": "Pizza Category", "total_price": "Revenue"},
            color_discrete_sequence=["#C94A4A", "#6B8E23", "#8FBC8F"]
        )
        fig.update_layout(title_x=0.0, yaxis_tickformat="d")
        st.plotly_chart(fig, use_container_width=True)

# ------------------ DEMAND PATTERN ------------------
with demand:
    st.markdown("### Customer Demand Patterns")
    st.caption("Multiple demand views available below")

    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)

    with r1c1:
        ingredient_counts = (
            filtered_df["ingredient_list"]
            .explode()
            .str.strip()
            .value_counts()
            .head(10)
            .reset_index()
        )
        ingredient_counts.columns = ["Ingredient", "Usage Count"]

        fig = px.treemap(
            ingredient_counts,
            path=["Ingredient"],
            values="Usage Count",
            title="Top 10 Ingredients by Usage",
            color="Usage Count",
            color_continuous_scale="YlOrRd"
        )
        fig.update_layout(title_x=0.1, height=350)
        st.plotly_chart(fig, use_container_width=False)
    with r1c2:
        exploded = filtered_df.explode("ingredient_list")
        exploded["ingredient_list"] = exploded["ingredient_list"].str.strip()

        top_ingredients = ingredient_counts["Ingredient"].head(5).tolist()

        heat_df = (
            exploded[exploded["ingredient_list"].isin(top_ingredients)]
            .groupby(["ingredient_list", "pizza_category"])["quantity"]
            .sum()
            .reset_index()
        )

        fig = px.density_heatmap(
            heat_df,
            x="pizza_category",
            y="ingredient_list",
            z="quantity",
            title="Ingredient Usage Across Pizza Categories",
            labels={
                "pizza_category": "Pizza Category",
                "ingredient_list": "Ingredient",
                "quantity": "Units Sold"
            },
            color_continuous_scale="YlOrRd"
        )
        fig.update_layout(title_x=0.1, height=350)
        st.plotly_chart(fig, use_container_width=True)

        
    with r2c1:
        fig = px.pie(
            filtered_df.groupby("Daytime")["quantity"].sum().reset_index(),
            names="Daytime",
            values="quantity",
            hole = 0.35,
            title="Share of Pizzas Sold by Time of Day",
            color_discrete_sequence=["#C94A4A", "#6B8E23", "#8FBC8F", "#A47551"]
        )
        fig.update_layout(title_x=0.1, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with r2c2:
        fig = px.bar(
            filtered_df.groupby("pizza_name")["total_price"].sum()
            .sort_values(ascending=False).head(5).reset_index(),
            x="total_price", y="pizza_name", orientation="h",
            title="Top 5 Pizzas by Revenue",
            
            labels={"total_price": "Revenue", "pizza_name": "Pizza Name"},
            color_discrete_sequence=["#C94A4A"]
        )
        fig.update_layout(title_x=0.2, height=350, yaxis_tickformat="d")
        st.plotly_chart(fig, use_container_width=True)

        # fig = px.bar(
        #     filtered_df.groupby(["pizza_category", "Daytime"])["quantity"]
        #     .sum().reset_index(),
        #     x="pizza_category", y="quantity", color="Daytime",
        #     barmode="group",
        #     title="Pizzas Sold by Category and Time of Day",
        #     labels={"pizza_category": "Pizza Category", "quantity": "Pizzas Sold"},
        #     color_discrete_sequence=["#C94A4A", "#6B8E23", "#8FBC8F", "#A47551"]
        # )
        # fig.update_layout(title_x=0.1, height=350, yaxis_tickformat="d")
        # st.plotly_chart(fig, use_container_width=True)

# ------------------ KEY INSIGHTS ------------------
# ------------------ CONCLUSION / KEY INSIGHTS ------------------
with insights:
    st.markdown("### Key Insights Summary")
    st.caption("Insights below are dynamically generated based on selected filters")

    # ---------- Insight Calculations ----------
    top_category = (
        filtered_df.groupby("pizza_category")["total_price"]
        .sum()
        .idxmax()
    )

    category_revenue_share = (
        filtered_df.groupby("pizza_category")["total_price"]
        .sum()
        / filtered_df["total_price"].sum()
        * 100
    )

    top_category_share = round(category_revenue_share.max(), 1)

    top_daytime = (
        filtered_df.groupby("Daytime")["quantity"]
        .sum()
        .idxmax()
    )

    top_ingredient = (
        filtered_df["ingredient_list"]
        .explode()
        .str.strip()
        .value_counts()
        .idxmax()
    )

    top_pizza_by_revenue = (
        filtered_df.groupby("pizza_name")["total_price"]
        .sum()
        .idxmax()
    )

    # ---------- Insight Presentation ----------
    st.markdown("#### Revenue & Sales Drivers")
    st.markdown(
        f"""
        • **{top_category} pizzas** generate the highest revenue under the current selection.  
        • The top category contributes approximately **{top_category_share}%** of total revenue.  
        • **{top_pizza_by_revenue}** is the highest revenue-generating pizza.
        """
    )

    st.markdown("#### Demand Patterns")
    st.markdown(
        f"""
        • **{top_daytime}** accounts for the highest volume of pizzas sold.  
        • Demand patterns suggest operational focus during **{top_daytime.lower()} hours**.
        """
    )

    st.markdown("#### Product & Ingredient Insights")
    st.markdown(
        f"""
        • **{top_ingredient}** is the most frequently used ingredient across pizzas.  
        • Ingredient usage indicates strong dependency on a small set of core ingredients.
        """
    )

    st.markdown("---")
    st.caption(
        "These insights automatically update based on applied filters and reflect patterns visible across the dashboard."
    )

