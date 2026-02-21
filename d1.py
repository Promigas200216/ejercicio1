import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Configuración técnica de la página
st.set_page_config(
    page_title="Informe: Salud Cognitiva y Envejecimiento",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo formal personalizado mediante CSS
st.markdown("""
    <style>
    .main { background-color: #F5F7F9; }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #E6E9EF;
    }
    h1, h2, h3 {
        color: #1E3A8A;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE PROCESAMIENTO ---

def extract_coords(point_str):
    """Extracción técnica de coordenadas geográficas"""
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
    """Carga y normalización del conjunto de datos"""
    file_path = "Alzheimer's_Disease_and_Healthy_Aging_Data_20260221.csv"
    try:
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
        
        # Normalización de variables numéricas
        cols_to_fix = ['Data_Value', 'Low_Confidence_Limit', 'High_Confidence_Limit']
        for col in cols_to_fix:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Procesamiento de datos espaciales
        if 'Geolocation' in df.columns:
            coords = df['Geolocation'].apply(extract_coords)
            df[['lat', 'lon']] = pd.DataFrame(coords.tolist(), index=df.index)
            
        return df
    except Exception as e:
        st.error(f"Error en la carga de datos: {e}")
        return None

# --- INICIO DE LA APLICACIÓN ---

df = load_data()

if df is not None:
    # Encabezado principal
    st.title("Informe Nacional: Salud Cognitiva y Envejecimiento")
    
    # Barra lateral - Información de Autoría y Filtros
    st.sidebar.markdown("### Integrantes del Proyecto")
    st.sidebar.markdown("""
    * Valentina Torres
    * Melanie Paola Perez 
    * Natalia Sojo 
    * Dana Valentina Ramirez
    """)
    st.sidebar.divider()

    st.sidebar.header("Parámetros de Análisis")
    
    col_tema = 'Topic' if 'Topic' in df.columns else 'Question'
    temas = sorted(df[col_tema].dropna().unique())
    tema_sel = st.sidebar.selectbox("Seleccione el Tema de Análisis:", temas)

    df_solo_edad = df[df['StratificationCategory1'] == 'Age Group']
    edades = sorted(df_solo_edad['Stratification1'].dropna().unique())
    if not edades:
        edades = sorted(df['Stratification1'].dropna().unique())
    edad_sel = st.sidebar.selectbox("Seleccione el Grupo Etario:", edades)

    # Filtrado de datos según parámetros
    df_base_tema = df[df[col_tema] == tema_sel]
    df_mapa = df_base_tema[df_base_tema['Stratification1'] == edad_sel]

    # --- INDICADORES CLAVE ---
    col1, col2, col3, col4 = st.columns(4)
    avg_val = df_mapa['Data_Value'].mean()
    
    col1.metric("Prevalencia Promedio", f"{avg_val:.2f}%" if not pd.isna(avg_val) else "N/A")
    col2.metric("Total de Registros", len(df_mapa))
    col3.metric("Estados Analizados", df_mapa['LocationAbbr'].nunique())
    col4.metric("Actualización", "Feb 2026")

    st.divider()

    # --- ESTRUCTURA DE CONTENIDO ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Distribución Geográfica", 
        "Ranking de Estados", 
        "Análisis por Género", 
        "Repositorio de Datos",
        "Documentación y QUEST"
    ])

    with tab1:
        st.subheader("Visualización Geoespacial de Prevalencia")
        df_geo = df_mapa.groupby(['LocationAbbr', 'LocationDesc'])['Data_Value'].mean().reset_index()
        
        if not df_geo.empty:
            fig_map = px.choropleth(
                df_geo, locations='LocationAbbr', locationmode="USA-states",
                color='Data_Value', scope="usa", color_continuous_scale="Blues",
                labels={'Data_Value': 'Prevalencia (%)'},
                hover_name='LocationDesc'
            )
            fig_map.update_layout(geo_scope='usa', margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)

    with tab2:
        st.subheader("Comparativa de Extremos: Top 5 vs Bottom 5")
        df_ranking = df_mapa.groupby('LocationDesc')['Data_Value'].mean().sort_values(ascending=False).reset_index()

        if not df_ranking.empty:
            c_top, c_bot = st.columns(2)
            
            with c_top:
                st.markdown("**Estados con mayor prevalencia**")
                fig_top = px.bar(df_ranking.head(5), x='Data_Value', y='LocationDesc', orientation='h',
                                 color='Data_Value', color_continuous_scale='Reds')
                fig_top.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)

            with c_bot:
                st.markdown("**Estados con menor prevalencia**")
                fig_bot = px.bar(df_ranking.tail(5), x='Data_Value', y='LocationDesc', orientation='h',
                                 color='Data_Value', color_continuous_scale='Greens')
                fig_bot.update_layout(showlegend=False, yaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_bot, use_container_width=True)

    with tab3:
        st.subheader("Análisis de Prevalencia por Edad y Género")
        gender_data = df_base_tema[df_base_tema['Stratification2'].isin(['Female', 'Male'])] \
                        .groupby(['Stratification1', 'Stratification2'])['Data_Value'] \
                        .mean().reset_index()

        if not gender_data.empty:
            fig_gen = px.bar(
                gender_data, x='Stratification1', y='Data_Value', color='Stratification2',
                barmode='group', color_discrete_map={'Female': '#D97706', 'Male': '#2563EB'},
                labels={'Data_Value': 'Promedio (%)', 'Stratification1': 'Edad'}
            )
            st.plotly_chart(fig_gen, use_container_width=True)
            st.markdown("### Resumen Estadístico")
            st.table(gender_data)

    with tab4:
        st.subheader("Explorador de Datos del Informe")
        st.dataframe(df_mapa, use_container_width=True)

    with tab5:
        st.header("Metodología y Sostenibilidad de Datos")
        
        st.subheader("1. Fuente de Datos Oficial")
        st.markdown("""
        **Origen:** Centers for Disease Control and Prevention (CDC).  
        **Dataset:** Alzheimer's Disease and Healthy Aging Data.  
        **URL:** [Portal de Datos del CDC](https://data.cdc.gov/Healthy-Aging/Alzheimer-s-Disease-and-Healthy-Aging-Data/hfr9-rurv/about_data)  
        **Fecha de acceso:** Febrero 2026.
        """)

        st.subheader("2. Framework QUEST Aplicado")
        st.info("""
        * **Question:** ¿Cómo impacta el deterioro cognitivo a los diferentes estados y géneros en EE.UU.?
        * **Understand:** Análisis de variables demográficas y métricas de salud pública.
        * **Explore:** Identificación de valores atípicos mediante rankings y mapas de calor geográficos.
        * **Synthesize:** Correlación entre la edad avanzada y la disparidad de género en los reportes de salud.
        * **Tell:** Visualización orientada a la toma de decisiones para audiencias no técnicas.
        """)

        st.subheader("3. Diccionario de Variables")
        st.markdown("""
        | Variable | Descripción | Tipo de Dato |
        | :--- | :--- | :--- |
        | **LocationDesc** | Nombre de la ubicación geográfica analizada. | Texto |
        | **Topic** | Descripción del tema de salud estudiado. | Texto |
        | **Question** | Pregunta realizada en la encuesta. | Texto |
        | **Data_Value** | Valor numérico de la prevalencia. | Número |
        | **Stratification1** | Clasificación por grupo de edad. | Texto |
        | **Stratification2** | Clasificación por género. | Texto |
        | **Geolocation** | Coordenadas para la representación en mapas. | Geográfico |
        """)

        st.subheader("4. Guía de Actualización")
        st.write("""
        Para mantener este dashboard vigente, se debe descargar el archivo actualizado desde el portal Open Data del CDC. 
        Al reemplazar el archivo en el repositorio, las métricas y visualizaciones se recalcularán de manera inmediata.
        """)

    # Pie de página formal
    st.divider()
    st.markdown("""
        <div style="text-align: center; color: #6B7280; font-size: 0.8em;">
            Informe Técnico - Alzheimer’s Disease and Healthy Aging Data<br>
            Elaborado por: Valentina Torres, Melanie Paola Perez, Natalia Sojo y Dana Valentina Ramirez.
        </div>
        """, unsafe_allow_html=True)

else:
    st.error("Error al cargar el recurso de datos. Verifique la integridad del archivo CSV.")
