import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
import json

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Iniciativas de Innovación - Alico",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .initiative-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #667eea;
    }
    .quick-win {
        border-left-color: #28a745 !important;
    }
    .strategic {
        border-left-color: #ffc107 !important;
    }
    .low-priority {
        border-left-color: #dc3545 !important;
    }
    .stSelectbox > div > div {
        background-color: #f8f9fa;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Configuración en sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/667eea/ffffff?text=ALICO", width=200)
    st.markdown("---")
    st.header("⚙️ Configuración")
    
    # Opciones de conexión
    data_source = st.radio(
        "Fuente de datos:",
        ["📊 Google Sheets", "📁 Archivo local", "🧪 Datos demo"]
    )
    
    if data_source == "📊 Google Sheets":
        st.subheader("🔑 Credenciales Google")
        
        # Método simple para credenciales
        credentials_method = st.radio(
            "Método de autenticación:",
            ["JSON Key", "Service Account"]
        )
        
        if credentials_method == "JSON Key":
            uploaded_key = st.file_uploader(
                "Sube tu archivo JSON de credenciales",
                type=['json'],
                help="Descarga desde Google Cloud Console"
            )
            
        spreadsheet_url = st.text_input(
            "URL de Google Sheets",
            placeholder="https://docs.google.com/spreadsheets/d/..."
        )
        
        sheet_name = st.text_input(
            "Nombre de la hoja",
            value="Respuestas de formulario 1"
        )
    
    elif data_source == "📁 Archivo local":
        uploaded_file = st.file_uploader(
            "Sube tu archivo Excel",
            type=['xlsx', 'xls', 'csv']
        )
    
    # Filtros avanzados
    st.markdown("---")
    st.subheader("🎛️ Filtros Avanzados")
    
    min_score_filter = st.slider(
        "Puntuación mínima total",
        0, 30, 0,
        help="Suma de todos los criterios numéricos"
    )
    
    show_zeros = st.checkbox(
        "Mostrar iniciativas sin evaluar",
        value=True,
        help="Incluir iniciativas con puntuaciones en 0"
    )

# Funciones auxiliares
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_google_sheets_data(credentials_dict, spreadsheet_url, sheet_name):
    """Carga datos desde Google Sheets de forma simplificada"""
    try:
        # Configurar credenciales
        scope = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Extraer ID de la URL
        if '/d/' in spreadsheet_url:
            sheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
        else:
            sheet_id = spreadsheet_url
        
        # Abrir hoja y obtener datos
        sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
        data = sheet.get_all_records()
        
        return pd.DataFrame(data)
    
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

def load_demo_data():
    """Genera datos de demostración realistas"""
    np.random.seed(42)  # Para resultados consistentes
    
    areas = [
        "Compras y Abastecimiento", "Recursos Humanos", "Tecnología",
        "Operaciones", "Finanzas", "Marketing", "Calidad"
    ]
    
    roles = ["Empleado", "Supervisor", "Gerente", "Director", "Proveedor"]
    
    procesos = [
        "Proyectos Estratégicos",
        "Innovación abierta / Universidades",
        "Gestión del Talento",
        "Transformación Digital",
        "Mejora Continua",
        "Atención al Cliente"
    ]
    
    beneficios = [
        "Reducción de tiempos / desperdicios",
        "Mayor satisfacción del cliente",
        "Reducción de costos",
        "Mejora en la calidad",
        "Aumento de productividad",
        "Innovación en productos/servicios"
    ]
    
    # Generar 50 iniciativas de ejemplo
    n_samples = 50
    data = []
    
    for i in range(n_samples):
        # Crear correlaciones realistas entre métricas
        strategic_value = np.random.randint(1, 6)
        impact = max(1, strategic_value + np.random.randint(-1, 2))
        technical_viability = np.random.randint(2, 6)
        cost_benefit = max(1, min(5, strategic_value + np.random.randint(-2, 2)))
        innovation = np.random.randint(1, 6)
        scalability = max(1, min(5, impact + np.random.randint(-1, 2)))
        implementation_time = np.random.randint(1, 6)
        
        data.append({
            'Marca temporal': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'Nombre completo': f'Empleado {i+1}',
            'Correo electrónico': f'empleado{i+1}@alico.com',
            'Rol o relación con Alico': np.random.choice(roles),
            'Selecciona el área o proceso al cual perteneces': np.random.choice(areas),
            'Nombre de la idea o iniciativa': f'Iniciativa de Innovación {i+1}',
            '¿Qué problema, necesidad u oportunidad busca resolver?': f'Problema identificado en el área {np.random.choice(areas)}',
            '¿Cuál es tu propuesta?': f'Propuesta de mejora {i+1}',
            '¿A qué proceso/s crees que se relaciona tu idea?': ', '.join(np.random.choice(procesos, 2)),
            '¿Qué beneficios esperas que genere?': ', '.join(np.random.choice(beneficios, 2)),
            '¿Esta idea la has visto implementada en otro lugar?': np.random.choice(['Sí', 'No']),
            'Si tu respuesta anterior fue si, especifica dónde y cómo': 'Empresa similar en el sector',
            '¿Crees que puede implementarse con los recursos actuales?': np.random.choice(['Sí', 'No', 'Parcialmente']),
            'Valor estratégico': strategic_value,
            'Nivel de impacto': impact,
            'Viabilidad técnica': technical_viability,
            'Costo-beneficio': cost_benefit,
            'Innovación / disrupción': innovation,
            'Escalabilidad / transversalidad': scalability,
            'Tiempo de implementación': implementation_time
        })
    
    return pd.DataFrame(data)

def calculate_scores(df):
    """Calcula métricas derivadas y clasificaciones"""
    df = df.copy()
    
    # Convertir columnas numéricas
    numeric_cols = [
        'Valor estratégico', 'Nivel de impacto', 'Viabilidad técnica',
        'Costo-beneficio', 'Innovación / disrupción', 
        'Escalabilidad / transversalidad', 'Tiempo de implementación'
    ]
    
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calcular puntuación total (excluyendo tiempo de implementación)
    df['Puntuación Total'] = (
        df['Valor estratégico'] + df['Nivel de impacto'] + 
        df['Viabilidad técnica'] + df['Costo-beneficio'] + 
        df['Innovación / disrupción'] + df['Escalabilidad / transversalidad']
    )
    
    # Calcular puntuación de prioridad (inversa del tiempo)
    df['Esfuerzo'] = 6 - df['Tiempo de implementación']  # Invertir escala
    
    # Clasificación de iniciativas
    def classify_initiative(row):
        if row['Nivel de impacto'] >= 4 and row['Esfuerzo'] >= 4:
            return 'Quick Win'
        elif row['Nivel de impacto'] >= 4 and row['Esfuerzo'] < 4:
            return 'Estratégica'
        elif row['Nivel de impacto'] < 4 and row['Esfuerzo'] >= 4:
            return 'Relleno'
        else:
            return 'Baja Prioridad'
    
    df['Clasificación'] = df.apply(classify_initiative, axis=1)
    
    # Ranking general
    df['Ranking'] = df['Puntuación Total'].rank(method='dense', ascending=False).astype(int)
    
    return df

# Cargar datos según la fuente seleccionada
@st.cache_data
def load_data():
    if data_source == "🧪 Datos demo":
        return load_demo_data()
    elif data_source == "📁 Archivo local" and 'uploaded_file' in locals():
        if uploaded_file is not None:
            if uploaded_file.name.endswith('.csv'):
                return pd.read_csv(uploaded_file)
            else:
                return pd.read_excel(uploaded_file)
    elif data_source == "📊 Google Sheets":
        if 'uploaded_key' in locals() and uploaded_key is not None and spreadsheet_url:
            credentials_dict = json.load(uploaded_key)
            return load_google_sheets_data(credentials_dict, spreadsheet_url, sheet_name)
    
    return pd.DataFrame()

# Título principal con métricas destacadas
st.markdown("""
<div style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
           padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
    <h1 style='color: white; margin: 0;'>💡 Análisis de Iniciativas de Innovación</h1>
    <p style='color: #f8f9fa; margin: 0.5rem 0 0 0; font-size: 1.2rem;'>Dashboard Ejecutivo - Alico</p>
</div>
""", unsafe_allow_html=True)

# Cargar y procesar datos
df_raw = load_data()

if df_raw.empty:
    st.warning("⚠️ No hay datos disponibles. Selecciona una fuente de datos en la barra lateral.")
    st.info("""
    ### 🚀 Para comenzar:
    1. **Datos demo**: Activa esta opción para ver el dashboard con datos de ejemplo
    2. **Google Sheets**: Sube tu archivo JSON de credenciales y proporciona la URL
    3. **Archivo local**: Sube tu archivo Excel directamente
    """)
    st.stop()

# Procesar datos
df = calculate_scores(df_raw)

# Aplicar filtros
if not show_zeros:
    df = df[df['Puntuación Total'] > 0]

df = df[df['Puntuación Total'] >= min_score_filter]

if df.empty:
    st.warning("⚠️ No hay datos que cumplan los filtros seleccionados.")
    st.stop()

# Métricas principales
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h2 style="margin:0; color: white;">{len(df)}</h2>
        <p style="margin:0; color: #f8f9fa;">Total Iniciativas</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    quick_wins = len(df[df['Clasificación'] == 'Quick Win'])
    st.markdown(f"""
    <div class="metric-card">
        <h2 style="margin:0; color: white;">{quick_wins}</h2>
        <p style="margin:0; color: #f8f9fa;">Quick Wins</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    avg_score = df['Puntuación Total'].mean()
    st.markdown(f"""
    <div class="metric-card">
        <h2 style="margin:0; color: white;">{avg_score:.1f}</h2>
        <p style="margin:0; color: #f8f9fa;">Puntuación Promedio</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    high_impact = len(df[df['Nivel de impacto'] >= 4])
    st.markdown(f"""
    <div class="metric-card">
        <h2 style="margin:0; color: white;">{high_impact}</h2>
        <p style="margin:0; color: #f8f9fa;">Alto Impacto</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    strategic = len(df[df['Clasificación'] == 'Estratégica'])
    st.markdown(f"""
    <div class="metric-card">
        <h2 style="margin:0; color: white;">{strategic}</h2>
        <p style="margin:0; color: #f8f9fa;">Estratégicas</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard Ejecutivo", "💡 Explorar Iniciativas", "📈 Análisis Detallado", "📋 Rankings & Reportes"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Matriz Esfuerzo-Impacto mejorada
        fig_matrix = go.Figure()
        
        # Colores por clasificación
        color_map = {
            'Quick Win': '#28a745',
            'Estratégica': '#ffc107', 
            'Relleno': '#17a2b8',
            'Baja Prioridad': '#dc3545'
        }
        
        for classification in df['Clasificación'].unique():
            subset = df[df['Clasificación'] == classification]
            fig_matrix.add_trace(go.Scatter(
                x=subset['Esfuerzo'],
                y=subset['Nivel de impacto'],
                mode='markers',
                marker=dict(
                    size=subset['Puntuación Total'] / 2,  # Tamaño por puntuación
                    color=color_map[classification],
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                name=classification,
                text=subset['Nombre de la idea o iniciativa'].str[:30] + '...',
                hovertemplate='<b>%{text}</b><br>' +
                             'Impacto: %{y}<br>' +
                             'Esfuerzo: %{x}<br>' +
                             'Puntuación: %{marker.size}<br>' +
                             '<extra></extra>'
            ))
        
        # Líneas de cuadrantes
        fig_matrix.add_hline(y=3.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig_matrix.add_vline(x=3.5, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Etiquetas de cuadrantes
        fig_matrix.add_annotation(x=2, y=4.7, text="Quick Wins", showarrow=False,
                                 font=dict(size=14, color="green", family="Arial Black"))
        fig_matrix.add_annotation(x=4.5, y=4.7, text="Estratégicas", showarrow=False,
                                 font=dict(size=14, color="orange", family="Arial Black"))
        fig_matrix.add_annotation(x=2, y=1.3, text="Relleno", showarrow=False,
                                 font=dict(size=14, color="blue", family="Arial Black"))
        fig_matrix.add_annotation(x=4.5, y=1.3, text="Baja Prioridad", showarrow=False,
                                 font=dict(size=14, color="red", family="Arial Black"))
        
        fig_matrix.update_layout(
            title="🎯 Matriz Esfuerzo-Impacto",
            xaxis_title="Facilidad de Implementación →",
            yaxis_title="Nivel de Impacto →",
            xaxis=dict(range=[0.5, 5.5], dtick=1),
            yaxis=dict(range=[0.5, 5.5], dtick=1),
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig_matrix, use_container_width=True)
    
    with col2:
        # Distribución por área con puntuaciones
        area_analysis = df.groupby('Selecciona el área o proceso al cual perteneces').agg({
            'Puntuación Total': ['mean', 'count'],
            'Clasificación': lambda x: (x == 'Quick Win').sum()
        }).round(1)
        
        area_analysis.columns = ['Puntuación Promedio', 'Total Iniciativas', 'Quick Wins']
        area_analysis = area_analysis.reset_index()
        
        fig_areas = px.bar(
            area_analysis,
            x='Total Iniciativas',
            y='Selecciona el área o proceso al cual perteneces',
            color='Puntuación Promedio',
            color_continuous_scale='viridis',
            text='Quick Wins',
            title="📊 Iniciativas por Área",
            labels={'Selecciona el área o proceso al cual perteneces': 'Área'}
        )
        
        fig_areas.update_traces(texttemplate='QW: %{text}', textposition='inside')
        fig_areas.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        
        st.plotly_chart(fig_areas, use_container_width=True)
    
    # Radar chart de criterios promedio
    st.subheader("🕸️ Análisis Multidimensional")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Radar por clasificación
        criteria = ['Valor estratégico', 'Nivel de impacto', 'Viabilidad técnica', 
                   'Costo-beneficio', 'Innovación / disrupción', 'Escalabilidad / transversalidad']
        
        fig_radar = go.Figure()
        
        for classification in ['Quick Win', 'Estratégica', 'Relleno', 'Baja Prioridad']:
            if classification in df['Clasificación'].values:
                subset = df[df['Clasificación'] == classification]
                values = [subset[col].mean() for col in criteria]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=values,
                    theta=criteria,
                    fill='toself',
                    name=classification,
                    line_color=color_map[classification]
                ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 5])
            ),
            title="Perfil por Clasificación",
            height=400
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col2:
        # Distribución de puntuaciones
        fig_hist = px.histogram(
            df, 
            x='Puntuación Total',
            color='Clasificación',
            color_discrete_map=color_map,
            title="📈 Distribución de Puntuaciones",
            nbins=15
        )
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)

with tab2:
    st.subheader("🔍 Explorador de Iniciativas")
    
    # Filtros interactivos
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        area_filter = st.multiselect(
            "🏢 Áreas",
            options=df['Selecciona el área o proceso al cual perteneces'].unique(),
            default=[]
        )
    
    with col2:
        classification_filter = st.multiselect(
            "🎯 Clasificación",
            options=df['Clasificación'].unique(),
            default=[]
        )
    
    with col3:
        impact_range = st.select_slider(
            "📊 Nivel de Impacto",
            options=list(range(1, 6)),
            value=(1, 5)
        )
    
    with col4:
        sort_by = st.selectbox(
            "🔢 Ordenar por",
            ['Ranking', 'Puntuación Total', 'Nivel de impacto', 'Valor estratégico']
        )
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if area_filter:
        filtered_df = filtered_df[filtered_df['Selecciona el área o proceso al cual perteneces'].isin(area_filter)]
    
    if classification_filter:
        filtered_df = filtered_df[filtered_df['Clasificación'].isin(classification_filter)]
    
    filtered_df = filtered_df[
        (filtered_df['Nivel de impacto'] >= impact_range[0]) & 
        (filtered_df['Nivel de impacto'] <= impact_range[1])
    ]
    
    # Ordenar
    filtered_df = filtered_df.sort_values(sort_by, ascending=False)
    
    st.info(f"📋 Mostrando {len(filtered_df)} de {len(df)} iniciativas")
    
    # Mostrar iniciativas
    for idx, row in filtered_df.head(20).iterrows():
        class_style = ""
        if row['Clasificación'] == 'Quick Win':
            class_style = "quick-win"
        elif row['Clasificación'] == 'Estratégica':
            class_style = "strategic"
        elif row['Clasificación'] == 'Baja Prioridad':
            class_style = "low-priority"
        
        with st.expander(f"#{row['Ranking']} - {row['Nombre de la idea o iniciativa']} ({row['Clasificación']})"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**👤 Propuesto por:** {row['Nombre completo']}")
                st.markdown(f"**🏢 Área:** {row['Selecciona el área o proceso al cual perteneces']}")
                st.markdown(f"**🎯 Problema a resolver:**")
                st.write(row['¿Qué problema, necesidad u oportunidad busca resolver?'])
                st.markdown(f"**💡 Propuesta:**")
                st.write(row['¿Cuál es tu propuesta?'])
                st.markdown(f"**📈 Beneficios esperados:**")
                st.write(row['¿Qué beneficios esperas que genere?'])
            
            with col2:
                st.metric("🏆 Ranking", f"#{row['Ranking']}")
                st.metric("📊 Puntuación Total", f"{row['Puntuación Total']:.0f}/30")
                st.metric("🎯 Clasificación", row['Clasificación'])
                st.metric("⏱️ Tiempo Impl.", row['Tiempo de implementación'])
            
            with col3:
                # Mini radar chart para la iniciativa
                mini_criteria = ['Valor estratégico', 'Nivel de impacto', 'Viabilidad técnica']
                mini_values = [row[col] for col in mini_criteria]
                
                fig_mini_radar = go.Figure()
                fig_mini_radar.add_trace(go.Scatterpolar(
                    r=mini_values + [mini_values[0]],  # Cerrar el polígono
                    theta=mini_criteria + [mini_criteria[0]],
                    fill='toself',
                    line_color=color_map.get(row['Clasificación'], '#666'),
                    showlegend=False
                ))
                
                fig_mini_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 5], showticklabels=False)),
                    height=250,
                    margin=dict(l=10, r=10, t=30, b=10)
                )
                
                st.plotly_chart(fig_mini_radar, use_container_width=True)

with tab3:
    st.subheader("📈 Análisis Estadístico Avanzado")
    
    # Análisis de correlaciones
    col1, col2 = st.columns(2)
    
    with col1:
        # Matriz de correlación
        numeric_cols = ['Valor estratégico', 'Nivel de impacto', 'Viabilidad técnica',
                       'Costo-beneficio', 'Innovación / disrupción', 
                       'Escalabilidad / transversalidad', 'Tiempo de implementación']
        
        corr_matrix = df[numeric_cols].corr()
        
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title="🔗 Matriz de Correlación entre Criterios",
            color_continuous_scale='RdBu'
        )
        fig_corr.update_layout(height=400)
        st.plotly_chart(fig_corr, use_container_width=True)
    
    with col2:
        # Análisis de dispersión
        x_axis = st.selectbox("Eje X", numeric_cols, index=0)
        y_axis = st.selectbox("Eje Y", numeric_cols, index=1)
        
        fig_scatter = px.scatter(
            df,
            x=x_axis,
            y=y_axis,
            color='Clasificación',
            size='Puntuación Total',
            hover_data=['Nombre de la idea o iniciativa'],
            color_discrete_map=color_map,
            title=f"📊 {x_axis} vs {y_axis}"
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Benchmarking por área
    st.subheader("🏆 Benchmarking por Área")
    
    area_benchmarks = df.groupby('Selecciona el área o proceso al cual perteneces')[numeric_cols].mean().round(2)
    
    # Crear gráfico de barras agrupadas
    fig_benchmark = go.Figure()
    
    areas = area_benchmarks.index
    criteria_subset = ['Valor estratégico', 'Nivel de impacto', 'Viabilidad técnica', 'Innovación / disrupción']
    
    for i, criterion in enumerate(criteria_subset):
        fig_benchmark.add_trace(go.Bar(
            name=criterion,
            x=areas,
            y=area_benchmarks[criterion],
            text=area_benchmarks[criterion],
            textposition='auto',
        ))
    
    fig_benchmark.update_layout(
        title="📊 Puntuaciones Promedio por Área",
        xaxis_title="Área",
        yaxis_title="Puntuación Promedio",
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig_benchmark, use_container_width=True)
    
    # Análisis temporal si hay suficientes datos
    st.subheader("📅 Análisis Temporal")
    
    df['Fecha'] = pd.to_datetime(df['Marca temporal']).dt.date
    temporal_data = df.groupby('Fecha').agg({
        'Puntuación Total': 'mean',
        'Nombre de la idea o iniciativa': 'count'
    }).rename(columns={'Nombre de la idea o iniciativa': 'Cantidad'})
    
    if len(temporal_data) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_temporal_count = px.line(
                temporal_data.reset_index(),
                x='Fecha',
                y='Cantidad',
                title="📈 Iniciativas Recibidas por Día",
                markers=True
            )
            st.plotly_chart(fig_temporal_count, use_container_width=True)
        
        with col2:
            fig_temporal_score = px.line(
                temporal_data.reset_index(),
                x='Fecha',
                y='Puntuación Total',
                title="📊 Calidad Promedio por Día",
                markers=True,
                color_discrete_sequence=['orange']
            )
            st.plotly_chart(fig_temporal_score, use_container_width=True)
    else:
        st.info("📅 Se necesitan más datos para mostrar tendencias temporales")

with tab4:
    st.subheader("🏆 Rankings y Reportes Ejecutivos")
    
    # Top performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥇 Top 10 Iniciativas")
        top_initiatives = df.nlargest(10, 'Puntuación Total')[
            ['Ranking', 'Nombre de la idea o iniciativa', 'Selecciona el área o proceso al cual perteneces', 
             'Puntuación Total', 'Clasificación']
        ].reset_index(drop=True)
        
        # Formatear la tabla
        def format_classification(val):
            colors = {
                'Quick Win': 'background-color: #d4edda; color: #155724',
                'Estratégica': 'background-color: #fff3cd; color: #856404',
                'Relleno': 'background-color: #d1ecf1; color: #0c5460',
                'Baja Prioridad': 'background-color: #f8d7da; color: #721c24'
            }
            return colors.get(val, '')
        
        styled_table = top_initiatives.style.applymap(
            format_classification, subset=['Clasificación']
        ).format({'Puntuación Total': '{:.0f}'})
        
        st.dataframe(styled_table, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### 🚀 Quick Wins Recomendados")
        quick_wins_table = df[df['Clasificación'] == 'Quick Win'].nlargest(10, 'Puntuación Total')[
            ['Ranking', 'Nombre de la idea o iniciativa', 'Selecciona el área o proceso al cual perteneces',
             'Nivel de impacto', 'Esfuerzo', 'Puntuación Total']
        ].reset_index(drop=True)
        
        if not quick_wins_table.empty:
            st.dataframe(quick_wins_table, use_container_width=True, hide_index=True)
        else:
            st.info("No hay Quick Wins identificados con los filtros actuales")
    
    # Resumen ejecutivo
    st.markdown("### 📋 Resumen Ejecutivo")
    
    total_initiatives = len(df)
    avg_score = df['Puntuación Total'].mean()
    top_area = df['Selecciona el área o proceso al cual perteneces'].value_counts().index[0]
    top_area_count = df['Selecciona el área o proceso al cual perteneces'].value_counts().iloc[0]
    
    classification_counts = df['Clasificación'].value_counts()
    
    st.markdown(f"""
    **📊 Resumen General ({datetime.now().strftime('%Y-%m-%d')})**
    
    - **Total de iniciativas evaluadas:** {total_initiatives}
    - **Puntuación promedio:** {avg_score:.1f}/30 ({(avg_score/30)*100:.1f}%)
    - **Área más activa:** {top_area} ({top_area_count} iniciativas)
    - **Quick Wins identificados:** {classification_counts.get('Quick Win', 0)} ({(classification_counts.get('Quick Win', 0)/total_initiatives)*100:.1f}%)
    - **Iniciativas estratégicas:** {classification_counts.get('Estratégica', 0)} ({(classification_counts.get('Estratégica', 0)/total_initiatives)*100:.1f}%)
    
    **🎯 Recomendaciones Principales:**
    1. **Priorizar Quick Wins:** Implementar inmediatamente las {classification_counts.get('Quick Win', 0)} iniciativas de alto impacto y bajo esfuerzo
    2. **Planificar estratégicas:** Desarrollar roadmap para las {classification_counts.get('Estratégica', 0)} iniciativas de alto impacto
    3. **Foco en {top_area}:** Apoyar especialmente esta área que muestra mayor actividad innovadora
    4. **Mejorar scoring:** Las iniciativas con puntuación inferior a 15 necesitan refinamiento
    """)
    
    # Exportar reportes
    st.markdown("### 💾 Exportar Reportes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Reporte completo
        export_df = df[[
            'Ranking', 'Nombre de la idea o iniciativa', 'Nombre completo',
            'Selecciona el área o proceso al cual perteneces', 'Clasificación',
            'Puntuación Total', 'Valor estratégico', 'Nivel de impacto',
            'Viabilidad técnica', 'Costo-beneficio', 'Innovación / disrupción',
            'Escalabilidad / transversalidad', 'Tiempo de implementación'
        ]].sort_values('Ranking')
        
        csv_complete = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Reporte Completo (CSV)",
            data=csv_complete,
            file_name=f"reporte_completo_iniciativas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Solo Quick Wins
        quick_wins_export = df[df['Clasificación'] == 'Quick Win'][[
            'Ranking', 'Nombre de la idea o iniciativa', 'Nombre completo',
            'Selecciona el área o proceso al cual perteneces', 'Puntuación Total',
            '¿Qué problema, necesidad u oportunidad busca resolver?',
            '¿Cuál es tu propuesta?', '¿Qué beneficios esperas que genere?'
        ]].sort_values('Ranking')
        
        if not quick_wins_export.empty:
            csv_quick_wins = quick_wins_export.to_csv(index=False)
            st.download_button(
                label="🚀 Quick Wins (CSV)",
                data=csv_quick_wins,
                file_name=f"quick_wins_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.button("🚀 Quick Wins (CSV)", disabled=True, help="No hay Quick Wins para exportar")
    
    with col3:
        # Resumen por área
        area_summary = df.groupby('Selecciona el área o proceso al cual perteneces').agg({
            'Puntuación Total': ['count', 'mean', 'max'],
            'Clasificación': lambda x: (x == 'Quick Win').sum()
        }).round(2)
        
        area_summary.columns = ['Total_Iniciativas', 'Puntuacion_Promedio', 'Puntuacion_Maxima', 'Quick_Wins']
        area_summary = area_summary.reset_index()
        
        csv_area_summary = area_summary.to_csv(index=False)
        st.download_button(
            label="📊 Resumen por Área (CSV)",
            data=csv_area_summary,
            file_name=f"resumen_areas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Panel de control para filtros de exportación
    with st.expander("⚙️ Configurar Exportación Personalizada"):
        export_cols = st.multiselect(
            "Selecciona columnas a exportar:",
            options=df.columns.tolist(),
            default=['Ranking', 'Nombre de la idea o iniciativa', 'Clasificación', 'Puntuación Total']
        )
        
        export_filter_area = st.multiselect(
            "Filtrar por área:",
            options=df['Selecciona el área o proceso al cual perteneces'].unique(),
            default=[]
        )
        
        export_filter_classification = st.multiselect(
            "Filtrar por clasificación:",
            options=df['Clasificación'].unique(),
            default=[]
        )
        
        if st.button("📥 Generar Exportación Personalizada"):
            custom_export = df.copy()
            
            if export_filter_area:
                custom_export = custom_export[custom_export['Selecciona el área o proceso al cual perteneces'].isin(export_filter_area)]
            
            if export_filter_classification:
                custom_export = custom_export[custom_export['Clasificación'].isin(export_filter_classification)]
            
            if export_cols:
                custom_export = custom_export[export_cols]
            
            csv_custom = custom_export.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Exportación Personalizada",
                data=csv_custom,
                file_name=f"exportacion_personalizada_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

# Footer informativo
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>💡 <strong>Sistema de Análisis de Iniciativas de Innovación - Alico</strong></p>
    <p>Desarrollado con Streamlit | Última actualización: {}</p>
    <p>📧 Para soporte técnico contacta al equipo de Innovación</p>
</div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M')), unsafe_allow_html=True)

# Configuración adicional en sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("📈 Estadísticas Rápidas")
    
    if not df.empty:
        st.metric("💯 Mejor Puntuación", f"{df['Puntuación Total'].max():.0f}/30")
        st.metric("🎯 Promedio de Impacto", f"{df['Nivel de impacto'].mean():.1f}/5")
        st.metric("⚡ % Quick Wins", f"{(len(df[df['Clasificación'] == 'Quick Win'])/len(df)*100):.1f}%")
        
        # Mini gráfico de distribución
        fig_mini_dist = px.pie(
            df['Clasificación'].value_counts().reset_index(),
            values='count',
            names='Clasificación',
            color_discrete_map=color_map
        )
        fig_mini_dist.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False
        )
        fig_mini_dist.update_traces(textinfo='percent', textfont_size=10)
        st.plotly_chart(fig_mini_dist, use_container_width=True)
    
    # Información del sistema
    st.markdown("---")
    st.subheader("ℹ️ Información")
    st.info(f"""
    **Criterios de Evaluación:**
    - Valor estratégico (0-5)
    - Nivel de impacto (0-5)  
    - Viabilidad técnica (0-5)
    - Costo-beneficio (0-5)
    - Innovación/disrupción (0-5)
    - Escalabilidad (0-5)
    - Tiempo implementación (0-5)
    
    **Clasificaciones:**
    - 🟢 Quick Win: Alto impacto, bajo esfuerzo
    - 🟡 Estratégica: Alto impacto, alto esfuerzo  
    - 🔵 Relleno: Bajo impacto, bajo esfuerzo
    - 🔴 Baja Prioridad: Bajo impacto, alto esfuerzo
    """)

# Actualización automática (opcional)
if st.button("🔄 Actualizar Datos", help="Recargar datos desde la fuente"):
    st.cache_data.clear()
    st.rerun()
