import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Deterioro Cognitivo en Adultos Mayores", layout="wide")

st.title("Dificultades Funcionales Asociadas al Deterioro Cognitivo Subjetivo")

st.markdown("""
Este dashboard analiza la prevalencia de dificultades funcionales asociadas 
al deterioro cognitivo subjetivo en adultos mayores en los estados de EE.UU.
""")

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    return df

df = load_data()

# -----------------------------
# LIMPIEZA
# -----------------------------

df["Data_Value"] = df["Data_Value"].astype(str).str.replace(",", ".")
df["Data_Value"] = pd.to_numeric(df["Data_Value"], errors="coerce")

df["LocationID"] = pd.to_numeric(df["LocationID"], errors="coerce")

# Solo porcentaje y sexo
df = df[
    (df["Data_Value_Type"] == "Percentage") &
    (df["StratificationCategory1"] == "Sex")
]

# Solo estados reales
df = df[df["LocationID"] < 100]

# -----------------------------
# FILTROS
# -----------------------------

st.sidebar.header("Filtros")

anio = st.sidebar.selectbox(
    "Seleccionar año",
    sorted(df["YearStart"].dropna().unique())
)

sexo = st.sidebar.selectbox(
    "Seleccionar género",
    sorted(df["Stratification1"].unique())
)

df_filtrado = df[
    (df["YearStart"] == anio) &
    (df["Stratification1"] == sexo)
]

# -----------------------------
# MAPA
# -----------------------------

st.subheader("Mapa de prevalencia por estado")

fig_mapa = px.choropleth(
    df_filtrado,
    locations="LocationID",
    locationmode="USA-states",
    color="Data_Value",
    scope="usa",
    color_continuous_scale="Reds",
    labels={"Data_Value": "Prevalencia (%)"},
)

st.plotly_chart(fig_mapa, use_container_width=True)

# -----------------------------
# RANKING
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
    labels={"Data_Value": "Prevalencia (%)", "LocationDesc": "Estado"},
)

st.plotly_chart(fig_genero, use_container_width=True)

# -----------------------------
# DOCUMENTACIÓN
# -----------------------------

st.markdown("---")
st.markdown("""
### Fuente de datos

Fuente: CDC Healthy Aging Data Portal  
Indicador: Functional difficulties associated with subjective cognitive decline  
Fecha de descarga: Febrero 2026  
Licencia: Datos públicos del gobierno de EE.UU.

Para actualizar el dashboard, se debe descargar la versión más reciente del dataset y reemplazar el archivo CSV.
""")
