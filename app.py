import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import requests
import io

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Iniciativas de Innovación - Alico",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .priority-high { color: #ff4444; font-weight: bold; }
    .priority-medium { color: #ffaa00; font-weight: bold; }
    .priority-low { color: #00aa00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">💡 Dashboard de Iniciativas de Innovación</h1>', unsafe_allow_html=True)
st.markdown("### Análisis inteligente de propuestas para toma de decisiones estratégicas")
st.markdown("---")

# Configuración de conexión
st.sidebar.header("⚙️ Configuración")
connection_type = st.sidebar.selectbox(
    "Tipo de conexión:",
    ["Google Sheets (URL pública)", "Upload manual", "Google Sheets API"]
)

# Función para cargar datos
@st.cache_data(ttl=300)
def load_data_from_sheets(sheet_url=None):
    """Carga datos desde Google Sheets"""
    if connection_type == "Google Sheets (URL pública)":
        # Extraer ID del sheet desde la URL
        if sheet_url and "spreadsheets/d/" in sheet_url:
            sheet_id = sheet_url.split("/spreadsheets/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            
            try:
                response = requests.get(csv_url)
                response.raise_for_status()
                df = pd.read_csv(io.StringIO(response.text))
                return process_dataframe(df)
            except Exception as e:
                st.error(f"Error al cargar desde Google Sheets: {str(e)}")
                return pd.DataFrame()
    
    return pd.DataFrame()

def process_dataframe(df):
    """Procesa y limpia el DataFrame"""
    if df.empty:
        return df
    
    # Limpiar nombres de columnas - más agresivo
    df.columns = df.columns.str.strip().str.replace('\n', ' ').str.replace('\r', ' ')
    
    # Debug: mostrar columnas disponibles
    st.sidebar.write("🔍 Columnas detectadas:")
    for i, col in enumerate(df.columns):
        st.sidebar.write(f"{i+1}. '{col}'")
    
    # Mapeo flexible de columnas - buscar por palabras clave
    column_mapping = {}
    
    # Buscar columnas por palabras clave
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'nombre completo' in col_lower:
            column_mapping['nombre_completo'] = col
        elif 'nombre de la idea' in col_lower or 'iniciativa' in col_lower:
            column_mapping['nombre_iniciativa'] = col
        elif 'área' in col_lower or 'proceso' in col_lower:
            column_mapping['area'] = col
        elif 'rol' in col_lower and 'alico' in col_lower:
            column_mapping['rol'] = col
        elif 'problema' in col_lower or 'oportunidad' in col_lower:
            column_mapping['problema'] = col
        elif 'propuesta' in col_lower and 'cuál' in col_lower:
            column_mapping['propuesta'] = col
        elif 'beneficios' in col_lower:
            column_mapping['beneficios'] = col
        elif 'valor estratégico' in col_lower or 'valor estrategico' in col_lower:
            column_mapping['valor_estrategico'] = col
        elif 'nivel de impacto' in col_lower or 'impacto' in col_lower:
            column_mapping['nivel_impacto'] = col
        elif 'viabilidad técnica' in col_lower or 'viabilidad tecnica' in col_lower:
            column_mapping['viabilidad_tecnica'] = col
        elif 'costo-beneficio' in col_lower or 'costo beneficio' in col_lower:
            column_mapping['costo_beneficio'] = col
        elif 'innovación' in col_lower or 'innovacion' in col_lower or 'disrupción' in col_lower:
            column_mapping['innovacion'] = col
        elif 'escalabilidad' in col_lower or 'transversalidad' in col_lower:
            column_mapping['escalabilidad'] = col
        elif 'tiempo de implementación' in col_lower or 'tiempo implementacion' in col_lower:
            column_mapping['tiempo_implementacion'] = col
    
    # Filtrar filas vacías usando columnas encontradas
    subset_cols = []
    if 'nombre_completo' in column_mapping:
        subset_cols.append(column_mapping['nombre_completo'])
    if 'nombre_iniciativa' in column_mapping:
        subset_cols.append(column_mapping['nombre_iniciativa'])
    
    if subset_cols:
        df = df.dropna(subset=subset_cols, how='all')
    
    # Procesar columnas numéricas
    numeric_mappings = [
        'valor_estrategico', 'nivel_impacto', 'viabilidad_tecnica',
        'costo_beneficio', 'innovacion', 'escalabilidad', 'tiempo_implementacion'
    ]
    
    for mapping_key in numeric_mappings:
        if mapping_key in column_mapping:
            col = column_mapping[mapping_key]
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df[col] = df[col].clip(0, 5)
    
    # Agregar mapeo al DataFrame para uso posterior
    df.attrs['column_mapping'] = column_mapping
    
    return df

def calculate_derived_metrics(df):
    """Calcula métricas derivadas para análisis"""
    if df.empty:
        return df
        
    df = df.copy()
    
    # Obtener mapeo de columnas
    column_mapping = getattr(df, 'attrs', {}).get('column_mapping', {})
    
    # Verificar que tenemos las columnas necesarias
    required_metrics = [
        'valor_estrategico', 'nivel_impacto', 'viabilidad_tecnica',
        'costo_beneficio', 'innovacion', 'escalabilidad', 'tiempo_implementacion'
    ]
    
    missing_metrics = []
    for metric in required_metrics:
        if metric not in column_mapping:
            missing_metrics.append(metric)
    
    if missing_metrics:
        st.warning(f"⚠️ No se encontraron las siguientes columnas: {missing_metrics}")
        st.info("Verifique que los nombres de las columnas en Google Sheets coincidan con los esperados.")
        
        # Crear columnas dummy con valor 0 para evitar errores
        for metric in missing_metrics:
            df[f'dummy_{metric}'] = 0
            column_mapping[metric] = f'dummy_{metric}'
    
    # Score de prioridad ponderado (escala 0-5)
    df['score_prioridad'] = (
        df[column_mapping.get('valor_estrategico', 'dummy_valor_estrategico')] * 0.25 +
        df[column_mapping.get('nivel_impacto', 'dummy_nivel_impacto')] * 0.25 +
        df[column_mapping.get('viabilidad_tecnica', 'dummy_viabilidad_tecnica')] * 0.20 +
        df[column_mapping.get('costo_beneficio', 'dummy_costo_beneficio')] * 0.15 +
        df[column_mapping.get('innovacion', 'dummy_innovacion')] * 0.10 +
        df[column_mapping.get('escalabilidad', 'dummy_escalabilidad')] * 0.05
    )
    
    # Facilidad de implementación (viabilidad técnica + inversión del tiempo)
    viabilidad_col = column_mapping.get('viabilidad_tecnica', 'dummy_viabilidad_tecnica')
    tiempo_col = column_mapping.get('tiempo_implementacion', 'dummy_tiempo_implementacion')
    
    df['facilidad_implementacion'] = (df[viabilidad_col] + (5 - df[tiempo_col])) / 2
    
    # Potencial de impacto (impacto + escalabilidad + innovación)
    impacto_col = column_mapping.get('nivel_impacto', 'dummy_nivel_impacto')
    escalabilidad_col = column_mapping.get('escalabilidad', 'dummy_escalabilidad')
    innovacion_col = column_mapping.get('innovacion', 'dummy_innovacion')
    
    df['potencial_impacto'] = (df[impacto_col] + df[escalabilidad_col] + df[innovacion_col]) / 3
    
    # Categorización por prioridad
    df['categoria_prioridad'] = pd.cut(
        df['score_prioridad'], 
        bins=[0, 2, 3.5, 5], 
        labels=['Baja', 'Media', 'Alta'],
        include_lowest=True
    )
    
    # Guardar el mapeo actualizado
    df.attrs['column_mapping'] = column_mapping
    
    return df

# Carga de datos
if connection_type == "Google Sheets (URL pública)":
    sheet_url = st.sidebar.text_input(
        "URL del Google Sheet:", 
        value="https://docs.google.com/spreadsheets/d/1yWHTveQlQEKi7fLdDxxKPLdEjGvD7PaTzAbRYvSBEp0/edit?usp=sharing"
    )
    if st.sidebar.button("🔄 Actualizar datos"):
        st.cache_data.clear()
    df = load_data_from_sheets(sheet_url)
    
elif connection_type == "Upload manual":
    uploaded_file = st.sidebar.file_uploader(
        "Cargar archivo Excel/CSV", 
        type=['xlsx', 'csv']
    )
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df = process_dataframe(df)
    else:
        df = pd.DataFrame()
        
else:  # Google Sheets API
    st.sidebar.info("📝 Requiere configuración de credenciales de Google Cloud")
    df = pd.DataFrame()

# Verificar si hay datos
if df.empty:
    st.warning("⚠️ No hay datos disponibles. Por favor configura la fuente de datos en el panel lateral.")
    st.stop()

# Procesar datos
df = calculate_derived_metrics(df)

# SIDEBAR - Filtros
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros")

# Filtro por área
area_col = column_mapping.get('area', 'Selecciona el área o proceso al cual perteneces')
if area_col in df.columns:
    areas_disponibles = ['Todas'] + list(df[area_col].dropna().unique())
else:
    areas_disponibles = ['Todas']
area_seleccionada = st.sidebar.selectbox("Filtrar por área:", areas_disponibles)

# Filtro por rol
rol_col = column_mapping.get('rol', 'Rol o relación con Alico')
if rol_col in df.columns:
    roles_disponibles = ['Todos'] + list(df[rol_col].dropna().unique())
else:
    roles_disponibles = ['Todos']
rol_seleccionado = st.sidebar.selectbox("Filtrar por rol:", roles_disponibles)

# Filtro por rango de prioridad
min_prioridad, max_prioridad = st.sidebar.slider(
    "Rango de score de prioridad:",
    min_value=0.0,
    max_value=5.0,
    value=(0.0, 5.0),
    step=0.1
)

# Aplicar filtros
df_filtrado = df.copy()
column_mapping = getattr(df, 'attrs', {}).get('column_mapping', {})

# Filtros usando columnas mapeadas
area_col = column_mapping.get('area', 'Selecciona el área o proceso al cual perteneces')
rol_col = column_mapping.get('rol', 'Rol o relación con Alico')

if area_seleccionada != 'Todas' and area_col in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[area_col] == area_seleccionada]

if rol_seleccionado != 'Todos' and rol_col in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[rol_col] == rol_seleccionado]

df_filtrado = df_filtrado[
    (df_filtrado['score_prioridad'] >= min_prioridad) & 
    (df_filtrado['score_prioridad'] <= max_prioridad)
]

# Verificar datos filtrados
if df_filtrado.empty:
    st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados.")
    st.stop()

# DASHBOARD PRINCIPAL
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📊 Total Iniciativas", 
        value=len(df_filtrado),
        delta=f"de {len(df)} totales"
    )

with col2:
    avg_priority = df_filtrado['score_prioridad'].mean()
    st.metric(
        label="⭐ Prioridad Promedio", 
        value=f"{avg_priority:.2f}/5",
        delta=f"{avg_priority:.1f}"
    )

with col3:
    high_priority = len(df_filtrado[df_filtrado['categoria_prioridad'] == 'Alta'])
    st.metric(
        label="🚀 Alta Prioridad", 
        value=high_priority,
        delta=f"{high_priority/len(df_filtrado)*100:.1f}% del total"
    )

with col4:
    avg_feasibility = df_filtrado['facilidad_implementacion'].mean()
    st.metric(
        label="⚡ Facilidad Implementación", 
        value=f"{avg_feasibility:.2f}/5",
        delta=f"{avg_feasibility:.1f}"
    )

st.markdown("---")

# TABS PRINCIPALES
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Matriz Esfuerzo-Impacto", 
    "📊 Análisis de Portafolio", 
    "🏆 Rankings", 
    "📋 Detalle de Iniciativas",
    "📈 Análisis Comparativo"
])

with tab1:
    st.header("📈 Matriz Esfuerzo vs Impacto")
    st.markdown("*Visualización para priorizar iniciativas basada en impacto potencial vs facilidad de implementación*")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Matriz Esfuerzo-Impacto
        fig = px.scatter(
            df_filtrado,
            x='facilidad_implementacion',
            y='potencial_impacto',
            size='score_prioridad',
            color='categoria_prioridad',
            hover_data=['Nombre de la idea o iniciativa', 'Selecciona el área o proceso al cual perteneces'],
            title="Matriz Esfuerzo vs Impacto",
            labels={
                'facilidad_implementacion': 'Facilidad de Implementación (0-5)',
                'potencial_impacto': 'Potencial de Impacto (0-5)',
                'categoria_prioridad': 'Prioridad'
            },
            color_discrete_map={
                'Baja': '#ff9999',
                'Media': '#ffcc99', 
                'Alta': '#99ff99'
            }
        )
        
        # Añadir líneas de referencia
        fig.add_hline(y=2.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=2.5, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Añadir anotaciones de cuadrantes
        fig.add_annotation(x=1.25, y=4.5, text="Alto Impacto<br>Difícil Implementación", showarrow=False, opacity=0.6)
        fig.add_annotation(x=4.5, y=4.5, text="GANADORES<br>RÁPIDOS", showarrow=False, opacity=0.8, bgcolor="lightgreen")
        fig.add_annotation(x=1.25, y=1.25, text="Bajo Impacto<br>Difícil Implementación", showarrow=False, opacity=0.6)
        fig.add_annotation(x=4.5, y=1.25, text="Bajo Impacto<br>Fácil Implementación", showarrow=False, opacity=0.6)
        
        fig.update_layout(height=600, width=800)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Recomendaciones")
        
        # Identificar ganadores rápidos
        ganadores_rapidos = df_filtrado[
            (df_filtrado['facilidad_implementacion'] >= 3.5) & 
            (df_filtrado['potencial_impacto'] >= 3.5)
        ]
        
        if not ganadores_rapidos.empty:
            st.success("**🚀 Ganadores Rápidos:**")
            for _, row in ganadores_rapidos.iterrows():
                st.write(f"• {row['Nombre de la idea o iniciativa']}")
        
        # Proyectos de alto impacto pero difíciles
        alto_impacto = df_filtrado[
            (df_filtrado['facilidad_implementacion'] < 3.5) & 
            (df_filtrado['potencial_impacto'] >= 3.5)
        ]
        
        if not alto_impacto.empty:
            st.warning("**⚡ Alto Impacto - Planificar:**")
            for _, row in alto_impacto.iterrows():
                st.write(f"• {row['Nombre de la idea o iniciativa']}")

with tab2:
    st.header("📊 Análisis de Portafolio")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución por categoría de prioridad
        priority_counts = df_filtrado['categoria_prioridad'].value_counts()
        
        fig_pie = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            title="Distribución por Prioridad",
            color_discrete_map={
                'Baja': '#ff9999',
                'Media': '#ffcc99', 
                'Alta': '#99ff99'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Distribución por área
        if 'Selecciona el área o proceso al cual perteneces' in df_filtrado.columns:
            area_counts = df_filtrado['Selecciona el área o proceso al cual perteneces'].value_counts()
            
            fig_bar = px.bar(
                x=area_counts.index,
                y=area_counts.values,
                title="Iniciativas por Área",
                labels={'x': 'Área', 'y': 'Número de Iniciativas'}
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Radar chart de métricas promedio
    st.subheader("📡 Perfil Promedio de Iniciativas")
    
    metrics = [
        'Valor estratégico', 'Nivel de impacto', 'Viabilidad técnica',
        'Costo-beneficio', 'Innovación / disrupción', 
        'Escalabilidad / transversalidad'
    ]
    
    avg_values = [df_filtrado[metric].mean() for metric in metrics]
    
    fig_radar = go.Figure()
    
    fig_radar.add_trace(go.Scatterpolar(
        r=avg_values,
        theta=metrics,
        fill='toself',
        name='Promedio Iniciativas'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )),
        showlegend=True,
        title="Perfil Promedio de Métricas (Escala 0-5)"
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)

with tab3:
    st.header("🏆 Rankings de Iniciativas")
    
    # Selector de criterio de ranking
    criterio_ranking = st.selectbox(
        "Seleccionar criterio de ranking:",
        ["Score de Prioridad", "Potencial de Impacto", "Facilidad de Implementación", 
         "Valor Estratégico", "Nivel de Impacto", "Innovación"]
    )
    
    # Mapear criterio a columna
    criterio_map = {
        "Score de Prioridad": "score_prioridad",
        "Potencial de Impacto": "potencial_impacto", 
        "Facilidad de Implementación": "facilidad_implementacion",
        "Valor Estratégico": "Valor estratégico",
        "Nivel de Impacto": "Nivel de impacto",
        "Innovación": "Innovación / disrupción"
    }
    
    columna_criterio = criterio_map[criterio_ranking]
    
    # Crear ranking
    df_ranking = df_filtrado.sort_values(columna_criterio, ascending=False).reset_index(drop=True)
    df_ranking['Posición'] = range(1, len(df_ranking) + 1)
    
    # Mostrar top 10
    st.subheader(f"🥇 Top 10 - {criterio_ranking}")
    
    cols_display = [
        'Posición', 'Nombre de la idea o iniciativa', 
        'Selecciona el área o proceso al cual perteneces',
        columna_criterio, 'categoria_prioridad'
    ]
    
    df_display = df_ranking[cols_display].head(10).copy()
    df_display[columna_criterio] = df_display[columna_criterio].round(2)
    
    # Formatear la tabla
    def color_priority(val):
        if val == 'Alta':
            return 'background-color: #90EE90'
        elif val == 'Media':
            return 'background-color: #FFE4B5'
        else:
            return 'background-color: #FFB6C1'
    
    styled_df = df_display.style.applymap(color_priority, subset=['categoria_prioridad'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Gráfico de barras del ranking
    top_10 = df_ranking.head(10)
    fig_ranking = px.bar(
        top_10,
        x=columna_criterio,
        y='Nombre de la idea o iniciativa',
        orientation='h',
        title=f"Top 10 Iniciativas por {criterio_ranking}",
        color=columna_criterio,
        color_continuous_scale='Viridis'
    )
    fig_ranking.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_ranking, use_container_width=True)

with tab4:
    st.header("📋 Detalle de Iniciativas")
    
    # Selector de iniciativa
    iniciativas_disponibles = df_filtrado['Nombre de la idea o iniciativa'].tolist()
    iniciativa_seleccionada = st.selectbox("Seleccionar iniciativa:", iniciativas_disponibles)
    
    if iniciativa_seleccionada:
        # Obtener datos de la iniciativa
        iniciativa_data = df_filtrado[df_filtrado['Nombre de la idea o iniciativa'] == iniciativa_seleccionada].iloc[0]
        
        # Layout en columnas
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"🎯 {iniciativa_seleccionada}")
            st.write(f"**Proponente:** {iniciativa_data['Nombre completo']}")
            st.write(f"**Área:** {iniciativa_data['Selecciona el área o proceso al cual perteneces']}")
            st.write(f"**Rol:** {iniciativa_data['Rol o relación con Alico']}")
            
            st.markdown("---")
            st.write("**Problema/Oportunidad:**")
            st.write(iniciativa_data['¿Qué problema, necesidad u oportunidad busca resolver?'])
            
            st.write("**Propuesta:**")
            st.write(iniciativa_data['¿Cuál es tu propuesta?'])
            
            st.write("**Beneficios Esperados:**")
            st.write(iniciativa_data['¿Qué beneficios esperas que genere?'])
        
        with col2:
            # Métricas de la iniciativa
            st.markdown("### 📊 Métricas")
            
            priority_color = {
                'Alta': '🟢',
                'Media': '🟡', 
                'Baja': '🔴'
            }
            
            prioridad = iniciativa_data['categoria_prioridad']
            st.markdown(f"**Prioridad:** {priority_color.get(prioridad, '⚪')} {prioridad}")
            st.metric("Score Prioridad", f"{iniciativa_data['score_prioridad']:.2f}/5")
            st.metric("Potencial Impacto", f"{iniciativa_data['potencial_impacto']:.2f}/5")
            st.metric("Facilidad Implementación", f"{iniciativa_data['facilidad_implementacion']:.2f}/5")
            
            # Gráfico de radar individual
            metrics_individuales = [
                'Valor estratégico', 'Nivel de impacto', 'Viabilidad técnica',
                'Costo-beneficio', 'Innovación / disrupción', 
                'Escalabilidad / transversalidad'
            ]
            
            values_individuales = [iniciativa_data[metric] for metric in metrics_individuales]
            
            fig_individual = go.Figure()
            fig_individual.add_trace(go.Scatterpolar(
                r=values_individuales,
                theta=metrics_individuales,
                fill='toself',
                name=iniciativa_seleccionada
            ))
            
            fig_individual.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                showlegend=False,
                title="Perfil de la Iniciativa",
                height=400
            )
            
            st.plotly_chart(fig_individual, use_container_width=True)

with tab5:
    st.header("📈 Análisis Comparativo")
    
    # Comparar hasta 3 iniciativas
    st.subheader("🔍 Comparador de Iniciativas")
    
    col1, col2, col3 = st.columns(3)
    
    iniciativas_para_comparar = []
    with col1:
        init1 = st.selectbox("Iniciativa 1:", [None] + iniciativas_disponibles, key="comp1")
        if init1:
            iniciativas_para_comparar.append(init1)
    
    with col2:
        init2 = st.selectbox("Iniciativa 2:", [None] + iniciativas_disponibles, key="comp2")
        if init2 and init2 != init1:
            iniciativas_para_comparar.append(init2)
    
    with col3:
        init3 = st.selectbox("Iniciativa 3:", [None] + iniciativas_disponibles, key="comp3")
        if init3 and init3 not in [init1, init2]:
            iniciativas_para_comparar.append(init3)
    
    if len(iniciativas_para_comparar) >= 2:
        # Crear gráfico comparativo
        df_comparativo = df_filtrado[df_filtrado['Nombre de la idea o iniciativa'].isin(iniciativas_para_comparar)]
        
        metrics_comp = [
            'Valor estratégico', 'Nivel de impacto', 'Viabilidad técnica',
            'Costo-beneficio', 'Innovación / disrupción', 
            'Escalabilidad / transversalidad'
        ]
        
        fig_comp = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        for i, iniciativa in enumerate(iniciativas_para_comparar):
            data = df_comparativo[df_comparativo['Nombre de la idea o iniciativa'] == iniciativa].iloc[0]
            values = [data[metric] for metric in metrics_comp]
            
            fig_comp.add_trace(go.Scatterpolar(
                r=values,
                theta=metrics_comp,
                fill='toself',
                name=iniciativa,
                line_color=colors[i]
            ))
        
        fig_comp.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            showlegend=True,
            title="Comparación de Iniciativas"
        )
        
        st.plotly_chart(fig_comp, use_container_width=True)
        
        # Tabla comparativa
        st.subheader("📊 Tabla Comparativa")
        
        df_tabla_comp = df_comparativo[[
            'Nombre de la idea o iniciativa', 'score_prioridad', 'potencial_impacto', 
            'facilidad_implementacion', 'categoria_prioridad'
        ]].copy()
        
        df_tabla_comp.columns = ['Iniciativa', 'Score Prioridad', 'Potencial Impacto', 
                                'Facilidad Implementación', 'Categoría']
        
        st.dataframe(df_tabla_comp, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**💡 Dashboard de Iniciativas de Innovación - Alico**")
st.markdown("*Desarrollado para facilitar la toma de decisiones estratégicas basada en datos*")
