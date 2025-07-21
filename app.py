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
    
    # Mapeo exacto basado en el archivo real
    column_mapping = {}
    
    # Buscar columnas exactas
    for col in df.columns:
        col_clean = col.strip()
        if col_clean == 'Nombre completo':
            column_mapping['nombre_completo'] = col
        elif col_clean == 'Nombre de la idea o iniciativa':
            column_mapping['nombre_iniciativa'] = col
        elif col_clean == 'Selecciona el área o proceso al cual perteneces':
            column_mapping['area'] = col
        elif col_clean == 'Rol o relación con Alico':
            column_mapping['rol'] = col
        elif col_clean == '¿Qué problema, necesidad u oportunidad busca resolver?':
            column_mapping['problema'] = col
        elif col_clean == '¿Cuál es tu propuesta?':
            column_mapping['propuesta'] = col
        elif col_clean == '¿Qué beneficios esperas que genere?':
            column_mapping['beneficios'] = col
        elif col_clean == 'Valor estratégico':
            column_mapping['valor_estrategico'] = col
        elif col_clean == 'Nivel de impacto':
            column_mapping['nivel_impacto'] = col
        elif col_clean == 'Viabilidad técnica':
            column_mapping['viabilidad_tecnica'] = col
        elif col_clean == 'Costo-beneficio':
            column_mapping['costo_beneficio'] = col
        elif col_clean == 'Innovación / disrupción':
            column_mapping['innovacion'] = col
        elif col_clean == 'Escalabilidad / transversalidad':
            column_mapping['escalabilidad'] = col
        elif col_clean == 'Tiempo de implementación':
            column_mapping['tiempo_implementacion'] = col
        elif col_clean == '¿Esta idea la has visto implementada en otro lugar?':
            column_mapping['implementada_otro_lugar'] = col
        elif col_clean == 'Si tu respuesta anterior fue si, especifica dónde y cómo':
            column_mapping['donde_implementada'] = col
        elif col_clean == '¿Crees que puede implementarse con los recursos actuales?':
            column_mapping['recursos_actuales'] = col
        elif col_clean == '¿A qué proceso/s crees que se relaciona tu idea?':
            column_mapping['procesos_relacionados'] = col
        elif col_clean == 'Correo electrónico':
            column_mapping['correo'] = col
        elif col_clean == 'Marca temporal':
            column_mapping['fecha'] = col
    
    # Mostrar mapeo encontrado
    st.sidebar.write("📋 Columnas mapeadas:")
    for key, value in column_mapping.items():
        st.sidebar.write(f"• {key}: '{value}'")
    
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
column_mapping = getattr(df, 'attrs', {}).get('column_mapping', {})

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
        delta=f"{high_priority/len(df_filtrado)*100:.1f}% del total" if len(df_filtrado) > 0 else "0%"
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
        nombre_col = column_mapping.get('nombre_iniciativa', 'Nombre')
        area_col = column_mapping.get('area', 'Area')
        
        hover_data = []
        if nombre_col in df_filtrado.columns:
            hover_data.append(nombre_col)
        if area_col in df_filtrado.columns:
            hover_data.append(area_col)
        
        fig = px.scatter(
            df_filtrado,
            x='facilidad_implementacion',
            y='potencial_impacto',
            size='score_prioridad',
            color='categoria_prioridad',
            hover_data=hover_data,
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
        
        nombre_col = column_mapping.get('nombre_iniciativa', 'nombre')
        
        if not ganadores_rapidos.empty:
            st.success("**🚀 Ganadores Rápidos:**")
            for _, row in ganadores_rapidos.iterrows():
                nombre = row[nombre_col] if nombre_col in row else 'Iniciativa sin nombre'
                st.write(f"• {nombre}")
        
        # Proyectos de alto impacto pero difíciles
        alto_impacto = df_filtrado[
            (df_filtrado['facilidad_implementacion'] < 3.5) & 
            (df_filtrado['potencial_impacto'] >= 3.5)
        ]
        
        if not alto_impacto.empty:
            st.warning("**⚡ Alto Impacto - Planificar:**")
            for _, row in alto_impacto.iterrows():
                nombre = row[nombre_col] if nombre_col in row else 'Iniciativa sin nombre'
                st.write(f"• {nombre}")

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
        area_col = column_mapping.get('area', None)
        if area_col and area_col in df_filtrado.columns:
            area_counts = df_filtrado[area_col].value_counts()
            
            fig_bar = px.bar(
                x=area_counts.index,
                y=area_counts.values,
                title="Iniciativas por Área",
                labels={'x': 'Área', 'y': 'Número de Iniciativas'}
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos de área disponibles")
    
    # Radar chart de métricas promedio
    st.subheader("📡 Perfil Promedio de Iniciativas")
    
    # Usar columnas mapeadas para las métricas
    metrics_mapped = []
    metric_labels = []
    
    metric_mappings = [
        ('valor_estrategico', 'Valor Estratégico'),
        ('nivel_impacto', 'Nivel de Impacto'), 
        ('viabilidad_tecnica', 'Viabilidad Técnica'),
        ('costo_beneficio', 'Costo-Beneficio'),
        ('innovacion', 'Innovación'),
        ('escalabilidad', 'Escalabilidad')
    ]
    
    for mapping_key, label in metric_mappings:
        if mapping_key in column_mapping:
            col_name = column_mapping[mapping_key]
            if col_name in df_filtrado.columns:
                metrics_mapped.append(col_name)
                metric_labels.append(label)
    
    if metrics_mapped:
        avg_values = [df_filtrado[metric].mean() for metric in metrics_mapped]
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=avg_values,
            theta=metric_labels,
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
    else:
        st.warning("No hay métricas numéricas disponibles para el gráfico radar")

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
        "Valor Estratégico": column_mapping.get('valor_estrategico', 'score_prioridad'),
        "Nivel de Impacto": column_mapping.get('nivel_impacto', 'potencial_impacto'),
        "Innovación": column_mapping.get('innovacion', 'score_prioridad')
    }
    
    columna_criterio = criterio_map[criterio_ranking]
    
    # Verificar que la columna existe
    if columna_criterio not in df_filtrado.columns:
        st.warning(f"La columna {criterio_ranking} no está disponible en los datos.")
        columna_criterio = "score_prioridad"  # Fallback
    
    # Crear ranking
    df_ranking = df_filtrado.sort_values(columna_criterio, ascending=False).reset_index(drop=True)
    df_ranking['Posición'] = range(1, len(df_ranking) + 1)
    
    # Mostrar top 10
    st.subheader(f"🥇 Top 10 - {criterio_ranking}")
    
    nombre_col = column_mapping.get('nombre_iniciativa', 'nombre')
    area_col = column_mapping.get('area', 'area')
    
    cols_display = ['Posición']
    if nombre_col in df_ranking.columns:
        cols_display.append(nombre_col)
    if area_col in df_ranking.columns:
        cols_display.append(area_col)
    cols_display.extend([columna_criterio, 'categoria_prioridad'])
    
    # Filtrar solo columnas que existen
    cols_display = [col for col in cols_display if col in df_ranking.columns]
    
    df_display = df_ranking[cols_display].head(10).copy()
    if columna_criterio in df_display.columns:
        df_display[columna_criterio] = df_display[columna_criterio].round(2)
    
    # Formatear la tabla
    def color_priority(val):
        if val == 'Alta':
            return 'background-color: #90EE90'
        elif val == 'Media':
            return 'background-color: #FFE4B5'
        else:
            return 'background-color: #FFB6C1'
    
    if 'categoria_prioridad' in df_display.columns:
        styled_df = df_display.style.applymap(color_priority, subset=['categoria_prioridad'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.dataframe(df_display, use_container_width=True)
    
    # Gráfico de barras del ranking
    if len(df_ranking) > 0:
        top_10 = df_ranking.head(10)
        y_col = nombre_col if nombre_col in top_10.columns else 'Posición'
        
        fig_ranking = px.bar(
            top_10,
            x=columna_criterio,
            y=y_col,
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
    nombre_col = column_mapping.get('nombre_iniciativa', 'nombre')
    if nombre_col in df_filtrado.columns:
        iniciativas_disponibles = df_filtrado[nombre_col].tolist()
        iniciativa_seleccionada = st.selectbox("Seleccionar iniciativa:", iniciativas_disponibles)
        
        if iniciativa_seleccionada:
            # Obtener datos de la iniciativa
            iniciativa_data = df_filtrado[df_filtrado[nombre_col] == iniciativa_seleccionada].iloc[0]
            
            # Layout en columnas
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(f"🎯 {iniciativa_seleccionada}")
                
                # Mostrar información disponible
                info_mappings = [
                    ('nombre_completo', 'Proponente'),
                    ('area', 'Área'),
                    ('rol', 'Rol'),
                    ('problema', 'Problema/Oportunidad'),
                    ('propuesta', 'Propuesta'),
                    ('beneficios', 'Beneficios Esperados')
                ]
                
                for mapping_key, label in info_mappings:
                    if mapping_key in column_mapping:
                        col_name = column_mapping[mapping_key]
                        if col_name in iniciativa_data.index and pd.notna(iniciativa_data[col_name]):
                            st.write(f"**{label}:** {iniciativa_data[col_name]}")
            
            with col2:
                # Métricas de la iniciativa
                st.markdown("### 📊 Métricas")
                
                priority_color = {
                    'Alta': '🟢',
                    'Media': '🟡', 
                    'Baja': '🔴'
                }
                
                if 'categoria_prioridad' in iniciativa_data.index:
                    prioridad = iniciativa_data['categoria_prioridad']
                    st.markdown(f"**Prioridad:** {priority_color.get(prioridad, '⚪')} {prioridad}")
                
                st.metric("Score Prioridad", f"{iniciativa_data['score_prioridad']:.2f}/5")
                st.metric("Potencial Impacto", f"{iniciativa_data['potencial_impacto']:.2f}/5")
                st.metric("Facilidad Implementación", f"{iniciativa_data['facilidad_implementacion']:.2f}/5")
                
                # Gráfico de radar individual
                metrics_individuales = []
                metric_labels_individuales = []
                
                metric_mappings_individuales = [
                    ('valor_estrategico', 'Valor Estratégico'),
                    ('nivel_impacto', 'Nivel de Impacto'), 
                    ('viabilidad_tecnica', 'Viabilidad Técnica'),
                    ('costo_beneficio', 'Costo-Beneficio'),
                    ('innovacion', 'Innovación'),
                    ('escalabilidad', 'Escalabilidad')
                ]
                
                for mapping_key, label in metric_mappings_individuales:
                    if mapping_key in column_mapping:
                        col_name = column_mapping[mapping_key]
                        if col_name in iniciativa_data.index:
                            metrics_individuales.append(iniciativa_data[col_name])
                            metric_labels_individuales.append(label)
                
                if metrics_individuales:
                    fig_individual = go.Figure()
                    fig_individual.add_trace(go.Scatterpolar(
                        r=metrics_individuales,
                        theta=metric_labels_individuales,
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
                else:
                    st.info("No hay métricas disponibles para el gráfico radar")
    else:
        st.warning("No hay iniciativas disponibles para mostrar")

with tab5:
    st.header("📈 Análisis Comparativo")
    
    # Comparar hasta 3 iniciativas
    st.subheader("🔍 Comparador de Iniciativas")
    
    nombre_col = column_mapping.get('nombre_iniciativa', 'nombre')
    if nombre_col in df_filtrado.columns:
        iniciativas_disponibles = df_filtrado[nombre_col].tolist()
        
        col1, col2, col3 = st.columns(3)
        
        iniciativas_para_comparar = []
        with col1:
            init1 = st.selectbox("Iniciativa 1:", [None] + iniciativas_disponibles, key="comp1")
            if init1:
                iniciativas_para_comparar.append(init1)
        
        with col2:
            opciones2 = [None] + [i for i in iniciativas_disponibles if i != init1]
            init2 = st.selectbox("Iniciativa 2:", opciones2, key="comp2")
            if init2:
                iniciativas_para_comparar.append(init2)
        
        with col3:
            opciones3 = [None] + [i for i in iniciativas_disponibles if i not in [init1, init2]]
            init3 = st.selectbox("Iniciativa 3:", opciones3, key="comp3")
            if init3:
                iniciativas_para_comparar.append(init3)
        
        if len(iniciativas_para_comparar) >= 2:
            # Crear gráfico comparativo
            df_comparativo = df_filtrado[df_filtrado[nombre_col].isin(iniciativas_para_comparar)]
            
            # Métricas para comparar
            metrics_comp = []
            metric_labels_comp = []
            
            metric_mappings_comp = [
                ('valor_estrategico', 'Valor Estratégico'),
                ('nivel_impacto', 'Nivel de Impacto'), 
                ('viabilidad_tecnica', 'Viabilidad Técnica'),
                ('costo_beneficio', 'Costo-Beneficio'),
                ('innovacion', 'Innovación'),
                ('escalabilidad', 'Escalabilidad')
            ]
            
            for mapping_key, label in metric_mappings_comp:
                if mapping_key in column_mapping:
                    col_name = column_mapping[mapping_key]
                    if col_name in df_comparativo.columns:
                        metrics_comp.append(col_name)
                        metric_labels_comp.append(label)
            
            if metrics_comp:
                fig_comp = go.Figure()
                
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
                for i, iniciativa in enumerate(iniciativas_para_comparar):
                    data = df_comparativo[df_comparativo[nombre_col] == iniciativa].iloc[0]
                    values = [data[metric] for metric in metrics_comp]
                    
                    fig_comp.add_trace(go.Scatterpolar(
                        r=values,
                        theta=metric_labels_comp,
                        fill='toself',
                        name=iniciativa,
                        line_color=colors[i] if i < len(colors) else colors[0]
                    ))
                
                fig_comp.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                    showlegend=True,
                    title="Comparación de Iniciativas"
                )
                
                st.plotly_chart(fig_comp, use_container_width=True)
                
                # Tabla comparativa
                st.subheader("📊 Tabla Comparativa")
                
                cols_comparar = [nombre_col, 'score_prioridad', 'potencial_impacto', 
                               'facilidad_implementacion', 'categoria_prioridad']
                cols_comparar = [col for col in cols_comparar if col in df_comparativo.columns]
                
                df_tabla_comp = df_comparativo[cols_comparar].copy()
                
                # Renombrar columnas para mejor presentación
                column_names = {
                    nombre_col: 'Iniciativa',
                    'score_prioridad': 'Score Prioridad',
                    'potencial_impacto': 'Potencial Impacto',
                    'facilidad_implementacion': 'Facilidad Implementación',
                    'categoria_prioridad': 'Categoría'
                }
                
                df_tabla_comp = df_tabla_comp.rename(columns=column_names)
                
                # Redondear valores numéricos
                for col in df_tabla_comp.columns:
                    if df_tabla_comp[col].dtype in ['float64', 'int64'] and col != 'Iniciativa':
                        df_tabla_comp[col] = df_tabla_comp[col].round(2)
                
                st.dataframe(df_tabla_comp, use_container_width=True)
            else:
                st.warning("No hay métricas disponibles para la comparación")
        elif len(iniciativas_para_comparar) == 1:
            st.info("Selecciona al menos 2 iniciativas para comparar")
        else:
            st.info("Selecciona las iniciativas que deseas comparar")
    else:
        st.warning("No hay datos de iniciativas disponibles para comparar")

# Footer
st.markdown("---")
st.markdown("**💡 Dashboard de Iniciativas de Innovación - Alico**")
st.markdown("*Desarrollado para facilitar la toma de decisiones estratégicas basada en datos*")

# Información adicional en el sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Algoritmo de Puntuación")
st.sidebar.markdown("""
**Score de Prioridad:**
- Valor Estratégico: 25%
- Nivel de Impacto: 25%
- Viabilidad Técnica: 20%
- Costo-Beneficio: 15%
- Innovación: 10%
- Escalabilidad: 5%
""")

st.sidebar.markdown("### 🔄 Actualización")
st.sidebar.markdown("Los datos se actualizan automáticamente cada 5 minutos desde Google Sheets.")

# Debug info (opcional - puedes comentar estas líneas en producción)
with st.expander("🔧 Información de Debug"):
    st.write("**Columnas disponibles:**", list(df.columns))
    st.write("**Mapeo de columnas:**", column_mapping)
    st.write("**Número de filas originales:**", len(df))
    st.write("**Número de filas filtradas:**", len(df_filtrado))
    if not df_filtrado.empty:
        st.write("**Rango de scores de prioridad:**", 
                f"{df_filtrado['score_prioridad'].min():.2f} - {df_filtrado['score_prioridad'].max():.2f}")
    st.write("**Filtros activos:**")
    st.write(f"- Área: {area_seleccionada}")
    st.write(f"- Rol: {rol_seleccionado}")
    st.write(f"- Rango prioridad: {min_prioridad} - {max_prioridad}")
