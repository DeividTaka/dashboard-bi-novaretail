import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="NovaRetail BI | Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    div[data-testid="metric-container"] {
        background-color: #1A1F2C;
        border: 1px solid #2D3748;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    h1, h2, h3 {color: #F7FAFC; font-family: 'Segoe UI', sans-serif;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    np.random.seed(42)
    n_records = 3500
    
    fechas = pd.date_range(start="2025-01-01", end="2026-10-31", freq="D")
    dates = np.random.choice(fechas, n_records)
    
    categorias = ["Electrónica", "Computación", "Hogar Inteligente", "Audio y Video", "Accesorios"]
    regiones = ["Centro", "Norte", "Sur", "Occidente", "Bajío"]
    segmentos = ["Consumidor Final", "Corporativo", "PyME"]
    
    df = pd.DataFrame({
        "Fecha": pd.to_datetime(dates),
        "Categoría": np.random.choice(categorias, n_records, p=[0.25, 0.25, 0.20, 0.15, 0.15]),
        "Región": np.random.choice(regiones, n_records, p=[0.30, 0.25, 0.15, 0.15, 0.15]),
        "Segmento": np.random.choice(segmentos, n_records, p=[0.60, 0.25, 0.15]),
        "Unidades": np.random.randint(1, 15, n_records)
    })
    
    precios_base = {
        "Electrónica": 450, "Computación": 850, 
        "Hogar Inteligente": 220, "Audio y Video": 310, "Accesorios": 65
    }
    df["Precio_Unitario"] = df["Categoría"].map(precios_base) * np.random.uniform(0.85, 1.25, n_records)
    
    df["Descuento_Pct"] = np.random.uniform(0.0, 0.15, n_records)
    df.loc[df["Categoría"] == "Hogar Inteligente", "Descuento_Pct"] = np.random.uniform(0.15, 0.38, len(df[df["Categoría"] == "Hogar Inteligente"]))
    df.loc[df["Región"] == "Sur", "Descuento_Pct"] += 0.08
    
    df["Ventas_Brutas"] = df["Unidades"] * df["Precio_Unitario"]
    df["Monto_Descuento"] = df["Ventas_Brutas"] * df["Descuento_Pct"]
    df["Ventas_Netas"] = df["Ventas_Brutas"] - df["Monto_Descuento"]
    
    costo_factor = np.random.uniform(0.55, 0.68, n_records)
    df["Costo_Total"] = df["Ventas_Brutas"] * costo_factor
    df.loc[df["Región"] == "Sur", "Costo_Total"] *= 1.14 
    
    df["Utilidad_Neta"] = df["Ventas_Netas"] - df["Costo_Total"]
    df["Margen_Pct"] = (df["Utilidad_Neta"] / df["Ventas_Netas"]) * 100
    df["Mes_Año"] = df["Fecha"].dt.to_period("M").astype(str)
    
    return df.sort_values("Fecha")

df = load_data()

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)
st.sidebar.title("Panel de Control")
st.sidebar.markdown("Filtra los indicadores operativos:")

regiones_sel = st.sidebar.multiselect(
    "Seleccionar Región:", options=df["Región"].unique(), default=df["Región"].unique()
)
categorias_sel = st.sidebar.multiselect(
    "Seleccionar Categoría:", options=df["Categoría"].unique(), default=df["Categoría"].unique()
)
segmentos_sel = st.sidebar.multiselect(
    "Segmento de Cliente:", options=df["Segmento"].unique(), default=df["Segmento"].unique()
)

df_filtered = df[
    (df["Región"].isin(regiones_sel)) &
    (df["Categoría"].isin(categorias_sel)) &
    (df["Segmento"].isin(segmentos_sel))
]

st.title("📊 NovaRetail Latam | Inteligencia Comercial y Rentabilidad")
st.markdown("**Análisis Ejecutivo de Ventas, Márgenes Operativos e Impacto Promocional (2025 - 2026)**")
st.divider()

col1, col2, col3, col4 = st.columns(4)

ventas_totales = df_filtered["Ventas_Netas"].sum()
utilidad_total = df_filtered["Utilidad_Neta"].sum()
margen_promedio = (utilidad_total / ventas_totales * 100) if ventas_totales > 0 else 0
descuento_promedio = df_filtered["Descuento_Pct"].mean() * 100

col1.metric("💰 Ventas Netas Totales", f"${ventas_totales:,.0f}", "+12.4% vs obj.")
col2.metric("📈 Utilidad Neta", f"${utilidad_total:,.0f}", f"{margen_promedio:.1f}% Margen")
col3.metric("🏷️ Descuento Promedio", f"{descuento_promedio:.1f}%", "-1.8% alerta", delta_color="inverse")
col4.metric("📦 Órdenes Procesadas", f"{len(df_filtered):,}", f"{df_filtered['Unidades'].sum():,} uds.")

st.markdown("<br>", unsafe_allow_html=True)

c1, c2 = st.columns((6, 4))

with c1:
    st.subheader("1. Evolución Temporal: Ingresos Netos vs. Margen (%)")
    df_trend = df_filtered.groupby("Mes_Año").agg({
        "Ventas_Netas": "sum",
        "Utilidad_Neta": "sum"
    }).reset_index()
    df_trend["Margen_Mes"] = (df_trend["Utilidad_Neta"] / df_trend["Ventas_Netas"]) * 100

    fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_dual.add_trace(
        go.Bar(
            x=df_trend["Mes_Año"], y=df_trend["Ventas_Netas"],
            name="Ventas Netas ($)", marker_color="#3B82F6", opacity=0.85
        ), secondary_y=False
    )
    fig_dual.add_trace(
        go.Scatter(
            x=df_trend["Mes_Año"], y=df_trend["Margen_Mes"],
            name="Margen Neto (%)", mode="lines+markers",
            line=dict(color="#10B981", width=3), marker=dict(size=7)
        ), secondary_y=True
    )
    fig_dual.add_hline(y=18, line_dash="dot", line_color="#EF4444", secondary_y=True,
                       annotation_text="Meta Mínima Margen (18%)", annotation_position="bottom right")

    fig_dual.update_layout(
        template="plotly_dark", height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    fig_dual.update_yaxes(title_text="Ventas Netas ($ USD)", secondary_y=False, showgrid=False)
    fig_dual.update_yaxes(title_text="Margen (%)", secondary_y=True, range=[0, 35])
    st.plotly_chart(fig_dual, use_container_width=True)

with c2:
    st.subheader("2. Jerarquía de Rentabilidad (Región > Categoría)")
    df_sun = df_filtered.groupby(["Región", "Categoría"]).agg({
        "Ventas_Netas": "sum",
        "Utilidad_Neta": "sum"
    }).reset_index()
    df_sun["Margen_Pct"] = (df_sun["Utilidad_Neta"] / df_sun["Ventas_Netas"]) * 100

    fig_sun = px.sunburst(
        df_sun, path=["Región", "Categoría"], values="Ventas_Netas",
        color="Margen_Pct", color_continuous_scale="RdYlGn",
        color_continuous_midpoint=18,
        hover_data={"Margen_Pct": ":.2f"}
    )
    fig_sun.update_layout(
        template="plotly_dark", height=420,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    st.plotly_chart(fig_sun, use_container_width=True)

c3, c4 = st.columns((5, 5))

with c3:
    st.subheader("3. Elasticidad: Impacto del Descuento en el Margen")
    df_sample = df_filtered.sample(min(600, len(df_filtered)), random_state=42)
    
    fig_scatter = px.scatter(
        df_sample, x="Descuento_Pct", y="Margen_Pct",
        color="Categoría", size="Ventas_Netas",
        opacity=0.75,
        labels={"Descuento_Pct": "Descuento Aplicado (%)", "Margen_Pct": "Margen Neto (%)"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="#EF4444", annotation_text="Zona de Pérdida (<0%)")
    fig_scatter.update_xaxes(tickformat=".0%")
    fig_scatter.update_layout(
        template="plotly_dark", height=420,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with c4:
    st.subheader("4. Puente Financiero: De Venta Bruta a Utilidad")
    v_bruta = df_filtered["Ventas_Brutas"].sum()
    desc = -df_filtered["Monto_Descuento"].sum()
    costo = -df_filtered["Costo_Total"].sum()
    u_neta = df_filtered["Utilidad_Neta"].sum()

    fig_waterfall = go.Figure(go.Waterfall(
        name="Flujo Financiero", orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Ventas Brutas", "Descuentos Otorgados", "Costos y Logística", "Utilidad Neta"],
        textposition="outside",
        text=[f"${v_bruta/1e6:.2f}M", f"${desc/1e6:.2f}M", f"${costo/1e6:.2f}M", f"${u_neta/1e6:.2f}M"],
        y=[v_bruta, desc, costo, u_neta],
        connector={"line": {"color": "#64748B"}},
        decreasing={"marker": {"color": "#EF4444"}},
        increasing={"marker": {"color": "#3B82F6"}},
        totals={"marker": {"color": "#10B981"}}
    ))
    fig_waterfall.update_layout(
        template="plotly_dark", height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis_title="Monto ($ USD)"
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

st.divider()
st.subheader("🧠 Interpretación Ejecutiva y Hallazgos Clave")

col_text1, col_text2 = st.columns(2)

with col_text1:
    st.info("""
    **1. Diagnóstico de Erosión de Margen (Gráficas 2 y 3):**
    * La categoría **Hogar Inteligente** presenta un volumen atractivo de ventas, pero opera con descuentos superiores al **25%**, empujando múltiples transacciones a la **zona de pérdida neta (<0%)**.
    * En el gráfico *Sunburst*, la **Región Sur** resalta en tonos rojizos/naranjas debido a la combinación de promociones excesivas y un sobrecosto logístico del **+14%** respecto al resto del país.
    """)

with col_text2:
    st.success("""
    **2. Recomendaciones Estratégicas Accionables:**
    * **Tope Promocional:** Limitar los descuentos máximos en *Hogar Inteligente* al **15%** y sustituir rebajas directas por paquetes (*bundles*) con *Accesorios* (categoría de alto margen).
    * **Optimización Logística en Región Sur:** Renegociar tarifas con operadores 3PL locales o establecer un monto mínimo de compra para envío gratuito en esa zona.
    """)
