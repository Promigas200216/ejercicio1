import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Salud Mental en Adultos Mayores", layout="wide")

st.title("Análisis Geográfico y de Género del Malestar Mental Frecuente")

st.markdown("""
Este dashboard analiza la prevalencia de malestar mental frecuente en adultos mayores 
en los estados de EE.UU., utilizando datos públicos del CDC.
""")

@st.cache_data
def load_data():
    df = pd.read_csv("Alzheimer's_Disease_and_Healthy_Aging_Data_20260221.csv")
    return df

df = load_data()

# -----------------------------
# LIMPIEZA DE DATOS
# -----------------------------

# Convertir coma decimal a punto
df["Data_Value"] = df["Data_Value"].astype(str).str.replace(",", ".")
df["Data_Value"] = pd.to_numeric(df["Data_Value"], errors="coerce")

# Filtrar solo lo relevante
df = df[
    (df["Class"] == "Mental Health") &
    (df["Topic"] == "Frequent mental distress") &
    (df["Data_Value_Type"] == "Percentage") &
    (df["StratificationCategory1"] == "Sex")
]

# Eliminar regiones agregadas (LocationID > 1000 suelen ser regiones)
df = df[df["LocationID"] < 100]

# -----------------------------
# FILTROS INTERACTIVOS
# -----------------------------

st.sidebar.header("Filtros")

anio = st.sidebar.selectbox(
    "Seleccionar año",
    sorted(df["YearStart"].unique())
)

sexo = st.sidebar.selectbox(
    "Seleccionar género",
    df["Stratification1"].unique()
)

df_filtrado = df[
    (df["YearStart"] == anio) &
    (df["Stratification1"] == sexo)
]

# -----------------------------
# MAPA DE CALOR
# -----------------------------

st.subheader("Mapa de prevalencia por estado")

fig_mapa = px.choropleth(
    df_filtrado,
    locations="LocationAbbr",
    locationmode="USA-states",
    color="Data_Value",
    scope="usa",
    color_continuous_scale="Reds",
    labels={"Data_Value": "Prevalencia (%)"},
    title="Prevalencia de malestar mental frecuente"
)

st.plotly_chart(fig_mapa, use_container_width=True)

# -----------------------------
# RANKING DE ESTADOS
# -----------------------------

st.subheader("Ranking de estados")

ranking = df_filtrado.sort_values("Data_Value", ascending=False)

fig_bar = px.bar(
    ranking,
    x="LocationDesc",
    y="Data_Value",
    labels={"Data_Value": "Prevalencia (%)", "LocationDesc": "Estado"},
)

st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------
# COMPARACIÓN POR GÉNERO
# -----------------------------

st.subheader("Comparación hombres vs mujeres")

df_genero = df[df["YearStart"] == anio]

fig_genero = px.bar(
    df_genero,
    x="LocationDesc",
    y="Data_Value",
    color="Stratification1",
    barmode="group",
    labels={"Data_Value": "Prevalencia (%)", "LocationDesc": "Estado"}
)

st.plotly_chart(fig_genero, use_container_width=True)

# -----------------------------
# DOCUMENTACIÓN
# -----------------------------

st.markdown("---")
st.markdown("""
### Fuente de datos

Fuente: Centers for Disease Control and Prevention (CDC)  
Dataset: Healthy Aging Data Portal  
Fecha de descarga: Febrero 2026  
Licencia: Datos públicos del gobierno de EE.UU.

Para actualizar el dashboard, se debe descargar la versión más reciente del dataset desde el portal del CDC y reemplazar el archivo CSV.
""")
