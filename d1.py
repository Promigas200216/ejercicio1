import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Configuración de la página
st.set_page_config(page_title="Alzheimer & Aging Stats", layout="wide")

# --- FUNCIONES DE LIMPIEZA ---

def extract_coords(point_str):
    """Extrae lat/lon del formato 'POINT (lon lat)'"""
    try:
        if pd.isna(point_str) or str(point_str).strip() == "":
            return None, None
        coords = re.findall(r"[-+]?\d*\.\d+|\d+", str(point_str))
        if len(coords) >= 2:
            return float(coords[1]), float(coords[0]) 
    except:
        return None, None
    return None, None

@st.cache_data
def load_data():
    """Carga y limpia el dataset automáticamente"""
    file_path = "Alzheimer's_Disease_and_Healthy_Aging_Data_20260221.csv"
    try:
        # sep=None detecta automáticamente si es coma o punto y coma
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
        
        # Limpieza de valores numéricos (manejo de comas decimales)
        for col in ['Data_Value', 'Low_Confidence_Limit', 'High_Confidence_Limit']:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Procesar geolocalización para mapas
        if 'Geolocation' in df.columns:
            coords = df['Geolocation'].apply(extract_coords)
            df[['lat', 'lon']] = pd.DataFrame(coords.tolist(), index=df.index)
            
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None

# --- EJECUCIÓN DEL DASHBOARD ---

df = load_data()

if df is not None:
    st.title("🧠 Dashboard: Salud Cognitiva y Envejecimiento")
    st.markdown("Análisis nacional basado en el dataset de Alzheimer y Aging.")

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("⚙️ Configuración Global")
    
    # El Tema y la Edad definen el color del mapa
    temas = sorted(df['Topic'].dropna().unique())
    tema_sel = st.sidebar.selectbox("1. Selecciona el Tema:", temas)

    edades = sorted(df['Age Group'].dropna().unique())
    edad_sel = st.sidebar.selectbox("2. Grupo de Edad:", edades)

    # Filtrado base para el mapa nacional
    df_mapa = df[(df['Topic'] == tema_sel) & (df['Age Group'] == edad_sel)]

    # --- DISEÑO POR PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["🌍 Mapa Nacional", "📊 Comparativa de Estados", "📄 Datos Detallados"])

    with tab1:
        st.subheader(f"Intensidad de {tema_sel}")
        st.write(f"Mapa interactivo: El color oscuro indica mayor porcentaje de impacto.")

        # Agrupamos por estado para el mapa de coropletas
        df_geo = df_mapa.groupby(['LocationAbbr', 'LocationDesc'])['Data_Value'].mean().reset_index()

        fig_choropleth = px.choropleth(
            df_geo,
            locations='LocationAbbr',
            locationmode="USA-states",
            color='Data_Value',
            scope="usa",
            color_continuous_scale="Reds", # Escala de color claro a oscuro
            labels={'Data_Value': '% Prevalencia'},
            hover_name='LocationDesc'
        )
        fig_choropleth.update_layout(geo_scope='usa', margin={"r":0,"t":0,"l":0,"b":0}, height=550)
        st.plotly_chart(fig_choropleth, use_container_width=True)

    with tab2:
        st.subheader("Filtro por Estados Específicos")
        # Filtro multiselect solo para las gráficas de comparación
        estados_sel = st.multiselect(
            "Selecciona estados para analizar en detalle:", 
            options=sorted(df_mapa['LocationDesc'].unique()),
            default=sorted(df_mapa['LocationDesc'].unique())[:5]
        )
        
        df_filtered = df_mapa[df_mapa['LocationDesc'].isin(estados_sel)]

        if not df_filtered.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Desglose por Estratificación**")
                fig_bar = px.bar(df_filtered, x='Stratification1', y='Data_Value', color='LocationDesc',
                                 barmode='group', template="plotly_white")
                st.plotly_chart(fig_bar, use_container_width=True)
            with c2:
                st.write("**Dispersión de Valores**")
                fig_scatter = px.scatter(df_filtered, x='Low_Confidence_Limit', y='High_Confidence_Limit', 
                                         color='LocationDesc', hover_data=['Stratification1'])
                st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("Selecciona al menos un estado para ver las gráficas comparativas.")

    with tab3:
        st.subheader("Explorador de Datos Crudos")
        st.dataframe(df_filtered if not df_filtered.empty else df_mapa, use_container_width=True)

else:
    st.error("No se pudo inicializar el dashboard. Verifica que el archivo CSV esté en la raíz del proyecto.")

# Pie de página informativo
st.sidebar.divider()
st.sidebar.caption("Dashboard actualizado - Feb 2026")
