import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Iniciativas de Innovación - Alico",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de tu Google Sheets (configurada directamente)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1yWHTveQlQEKi7fLdDxxKPLdEjGvD7PaTzAbRYvSBEp0/edit?usp=sharing"
SHEET_ID = "1yWHTveQlQEKi7fLdDxxKPLdEjGvD7PaTzAbRYvSBEp0"

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
    .quick-win { border-left-color: #28a745 !important; }
    .strategic { border-left-color: #ffc107 !important; }
    .low-priority { border-left-color: #dc3545 !important; }
    .connection-status {
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
        font-weight: bold;
    }
    .success { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
    .error { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
    .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
</style>
""", unsafe_allow_html=True)

# Funciones para cargar datos
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_google_sheets_data():
    """Carga datos directamente desde Google Sheets usando múltiples métodos"""
    
    # Método 1: URL directa de exportación (más confiable)
    urls_to_try = [
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0",
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv",
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0",
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
    ]
    
    for i, csv_url in enumerate(urls_to_try):
        try:
            # Headers para evitar bloqueos
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Intentar cargar los datos
            response = requests.get(csv_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Verificar que la respuesta no esté vacía
            if len(response.text.strip()) < 10:
                continue
                
            # Leer CSV desde la respuesta
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)
            
            # Verificar que el DataFrame tenga datos válidos
            if len(df) > 0 and len(df.columns) > 5:
                return df, True, f"Conectado exitosamente (método {i+1})"
            
        except Exception as e:
            if i == len(urls_to_try) - 1:  # Solo mostrar error en el último intento
                last_error = str(e)
            continue
    
    # Si todos los métodos fallan, intentar método alternativo con requests más permisivo
    try:
        import ssl
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # URL alternativa más simple
        simple_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        
        response = requests.get(
            simple_url,
            headers={'User-Agent': 'Python-requests'},
            timeout=20,
            verify=False  # Ignorar certificados SSL temporalmente
        )
        
        if response.status_code == 200 and len(response.text.strip()) > 10:
            df = pd.read_csv(StringIO(response.text))
            if len(df) > 0:
                return df, True, "Conectado con método alternativo"
                
    except Exception:
        pass
    
    return pd.DataFrame(), False, f"No se pudo conectar. Revisa que el Google Sheets sea público. Último error: {last_error if 'last_error' in locals() else 'Conexión fallida'}"

def load_demo_data():
    """Genera datos de demostración realistas basados en la estructura real"""
    np.random.seed(42)
    
    areas = [
        "Compras y Abastecimiento", "Recursos Humanos", "Tecnología",
        "Operaciones", "Finanzas", "Marketing", "Calidad", "Logística"
    ]
    
    roles = ["Empleado", "Supervisor", "Gerente", "Director", "Proveedor", "Consultor"]
    
    procesos = [
        "Proyectos Estratégicos, Innovación abierta / Universidades",
        "Gestión del Talento, Cultura Organizacional",
        "Transformación Digital, Automatización",
        "Mejora Continua, Optimización de Procesos",
        "Atención al Cliente, Experiencia del Usuario",
        "Sostenibilidad, Responsabilidad Social"
    ]
    
    beneficios_options = [
        "Reducción de tiempos / desperdicios, Mayor satisfacción del cliente",
        "Reducción de costos, Mejora en la calidad",
        "Aumento de productividad, Innovación en productos/servicios",
        "Mejora en la comunicación, Automatización de procesos",
        "Sostenibilidad ambiental, Cumplimiento normativo"
    ]
    
    ideas = [
        "Sistema de gestión inteligente de inventarios",
        "Plataforma de capacitación virtual con IA",
        "Automatización de procesos de aprobación",
        "Dashboard de métricas en tiempo real",
        "Chatbot para atención al cliente 24/7",
        "Sistema de recomendaciones personalizadas",
        "Aplicación móvil para gestión de campo",
        "Plataforma de colaboración interna",
        "Sistema de análisis predictivo de ventas",
        "Portal de autoservicio para empleados",
        "Herramienta de optimización de rutas",
        "Sistema de gestión documental inteligente",
        "Plataforma de feedback continuo",
        "Automatización de reportes financieros",
        "Sistema de monitoreo ambiental"
    ]
    
    problemas = [
        "Ineficiencias en el control de inventario generan sobrecostos",
        "Procesos de capacitación lentos y poco efectivos",
        "Aprobaciones manuales retrasan las operaciones",
        "Falta de visibilidad en tiempo real de KPIs",
        "Atención al cliente limitada por horarios",
        "Dificultad para personalizar la experiencia del cliente",
        "Gestión de campo ineficiente y descoordinada",
        "Comunicación interna fragmentada entre equipos",
        "Dificultad para predecir tendencias de ventas",
        "Procesos administrativos burocráticos para empleados"
    ]
    
    propuestas = [
        "Implementar IA para predicción automática de demanda y reposición",
        "Crear plataforma de e-learning adaptativa con gamificación",
        "Desarrollar workflow automatizado con notificaciones inteligentes",
        "Construir dashboard ejecutivo con alertas en tiempo real",
        "Desplegar chatbot con procesamiento de lenguaje natural",
        "Crear motor de recomendaciones basado en machine learning",
        "Desarrollar app móvil offline-first para equipos de campo",
        "Implementar plataforma colaborativa tipo Slack empresarial",
        "Construir modelo predictivo con análisis de datos históricos",
        "Crear portal self-service con automatización de trámites"
    ]
    
    # Generar 40 iniciativas de ejemplo
    n_samples = 40
    data = []
    
    for i in range(n_samples):
        # Crear correlaciones realistas entre métricas
        strategic_value = np.random.randint(1, 6)
        impact = max(1, min(5, strategic_value + np.random.randint(-1, 2)))
        technical_viability = np.random.randint(2, 6)
        cost_benefit = max(1, min(5, strategic_value + np.random.randint(-2, 2)))
        innovation = np.random.randint(1, 6)
        scalability = max(1, min(5, impact + np.random.randint(-1, 2)))
        implementation_time = np.random.randint(1, 6)
        
        # Generar timestamp realista (últimos 30 días)
        days_ago = np.random.randint(0, 30)
        timestamp = (datetime.now() - pd.Timedelta(days=days_ago)).strftime('%m/%d/%Y %H:%M:%S')
        
        data.append({
            'Marca temporal': timestamp,
            'Nombre completo': f'Colaborador {chr(65 + i % 26)}.{i+1}',
            'Correo electrónico': f'colaborador{i+1}@alico.com',
            'Rol o relación con Alico  ': np.random.choice(roles),
            'Selecciona el área o proceso al cual perteneces ': np.random.choice(areas),
            'Nombre de la idea o iniciativa  ': np.random.choice(ideas) + f' v{i+1}',
            '¿Qué problema, necesidad u oportunidad busca resolver?  ': np.random.choice(problemas),
            '¿Cuál es tu propuesta?  ': np.random.choice(propuestas),
            '¿A qué proceso/s crees que se relaciona tu idea?': np.random.choice(procesos),
            '¿Qué beneficios esperas que genere?  ': np.random.choice(beneficios_options),
            '¿Esta idea la has visto implementada en otro lugar? ': np.random.choice(['Sí', 'No']),
            'Si tu respuesta anterior fue si, especifica dónde y cómo': 'Empresa del sector tecnológico',
            '¿Crees que puede implementarse con los recursos actuales?': np.random.choice(['Sí', 'No', 'Parcialmente']),
            'Valor estratégico': strategic_value,
            'Nivel de impacto': impact,
            'Viabilidad técnica': technical_viability,
            'Costo-beneficio': cost_benefit,
            'Innovación / disrupción ': innovation,
            'Escalabilidad / transversalidad ': scalability,
            'Tiempo de implementación ': implementation_time
        })
    
    return pd.DataFrame(data)

def get_column_name(df, possible_names):
    """Busca el nombre correcto de columna entre varias posibilidades"""
    for name in possible_names:
        if name in df.columns:
            return name
    return None

def safe_get_column(df, possible_names, default='N/A'):
    """Obtiene valores de una columna de forma segura"""
    col_name = get_column_name(df, possible_names)
    if col_name:
        return df[col_name]
    else:
        return default
    """Calcula métricas derivadas y clasificaciones"""
    if df.empty:
        return df
        
    df = df.copy()
    
    # Limpiar nombres de columnas (remover espacios extra)
    df.columns = df.columns.str.strip()
    
    # Mapeo de columnas para manejar variaciones en nombres
    column_mapping = {
        'Valor estratégico': 'valor_estrategico',
        'Nivel de impacto': 'nivel_impacto', 
        'Viabilidad técnica': 'viabilidad_tecnica',
        'Costo-beneficio': 'costo_beneficio',
        'Innovación / disrupción': 'innovacion_disrupcion',
        'Escalabilidad / transversalidad': 'escalabilidad_transversalidad',
        'Tiempo de implementación': 'tiempo_implementacion'
    }
    
    # Convertir columnas numéricas, manejando diferentes formatos
    for col_original, col_clean in column_mapping.items():
        if col_original in df.columns:
            df[col_clean] = pd.to_numeric(df[col_original], errors='coerce').fillna(0)
        else:
            # Buscar columnas similares
            similar_cols = [c for c in df.columns if col_original.lower().replace(' ', '') in c.lower().replace(' ', '')]
            if similar_cols:
                df[col_clean] = pd.to_numeric(df[similar_cols[0]], errors='coerce').fillna(0)
            else:
                df[col_clean] = 0
    
    # Calcular puntuación total (excluyendo tiempo de implementación)
    df['Puntuación Total'] = (
        df['valor_estrategico'] + df['nivel_impacto'] + 
        df['viabilidad_tecnica'] + df['costo_beneficio'] + 
        df['innovacion_disrupcion'] + df['escalabilidad_transversalidad']
    )
    
    # Calcular facilidad de implementación (inversa del tiempo)
    df['Facilidad Implementación'] = 6 - df['tiempo_implementacion']
    
    # Clasificación de iniciativas basada en matriz esfuerzo-impacto
    def classify_initiative(row):
        impact = row['nivel_impacto']
        ease = row['Facilidad Implementación']
        
        if impact >= 4 and ease >= 4:
            return 'Quick Win'
        elif impact >= 4 and ease < 4:
            return 'Estratégica'
        elif impact < 4 and ease >= 4:
            return 'Relleno'
        else:
            return 'Baja Prioridad'
    
    df['Clasificación'] = df.apply(classify_initiative, axis=1)
    
    # Ranking general basado en puntuación total
    df['Ranking'] = df['Puntuación Total'].rank(method='dense', ascending=False).astype(int)
    
    # Limpiar nombres de áreas para mejor visualización
    if 'Selecciona el área o proceso al cual perteneces' in df.columns:
        df['Área'] = df['Selecciona el área o proceso al cual perteneces'].str.strip()
    elif 'Selecciona el área o proceso al cual perteneces ' in df.columns:
        df['Área'] = df['Selecciona el área o proceso al cual perteneces '].str.strip()
    else:
        df['Área'] = 'Sin especificar'
    
    return df

# Configuración en sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/667eea/ffffff?text=ALICO", width=200)
    st.markdown("---")
    st.header("⚙️ Configuración")
    
    # Opciones de fuente de datos
    data_source = st.radio(
        "📊 Fuente de datos:",
        ["🔗 Google Sheets (Automático)", "📁 Subir Archivo CSV", "🧪 Datos de Demostración"],
        help="Google Sheets se conecta automáticamente a tu formulario"
    )
    
    # Configuración según la fuente
    if data_source == "📁 Subir Archivo CSV":
        st.info("💡 **Cómo obtener el CSV:**\n1. Ve a tu Google Sheets\n2. Archivo → Descargar → CSV\n3. Sube el archivo aquí")
        uploaded_file = st.file_uploader(
            "Selecciona tu archivo CSV",
            type=['csv'],
            help="Descarga el CSV directamente desde Google Sheets"
        )
    
    # Estado de conexión
    if data_source == "🔗 Google Sheets (Automático)":
        st.info(f"📋 **Conectado a:** Banco de Iniciativas Alico")
        st.success("🟢 Conexión configurada")
        
        # Botón de actualización manual
        if st.button("🔄 Actualizar Datos", help="Recargar datos desde Google Sheets"):
            st.cache_data.clear()
            st.rerun()
    
    # Filtros avanzados
    st.markdown("---")
    st.subheader("🎛️ Filtros")
    
    min_score_filter = st.slider(
        "Puntuación mínima total",
        0, 30, 0,
        help="Filtrar iniciativas por puntuación total mínima"
    )
    
    show_zeros = st.checkbox(
        "Incluir iniciativas sin evaluar",
        value=True,
        help="Mostrar iniciativas con puntuaciones en 0"
    )
    
    # Información técnica
    st.markdown("---")
    st.subheader("ℹ️ Información")
    st.info(f"""
    **🔗 Fuente de Datos:**
    Google Sheets conectado automáticamente
    
    **📊 Criterios de Evaluación (0-5):**
    • Valor estratégico
    • Nivel de impacto  
    • Viabilidad técnica
    • Costo-beneficio
    • Innovación/disrupción
    • Escalabilidad/transversalidad
    • Tiempo implementación
    
    **🎯 Clasificaciones:**
    🟢 Quick Win: Alto impacto + Fácil implementación
    🟡 Estratégica: Alto impacto + Difícil implementación  
    🔵 Relleno: Bajo impacto + Fácil implementación
    🔴 Baja Prioridad: Bajo impacto + Difícil implementación
    """)

# Título principal
st.markdown("""
<div style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
           padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
    <h1 style='color: white; margin: 0;'>💡 Análisis de Iniciativas de Innovación</h1>
    <p style='color: #f8f9fa; margin: 0.5rem 0 0 0; font-size: 1.2rem;'>Dashboard Ejecutivo - Alico</p>
</div>
""", unsafe_allow_html=True)

# Cargar datos según la fuente seleccionada
if data_source == "🔗 Google Sheets (Automático)":
    df_raw, connection_success, connection_message = load_google_sheets_data()
    
    # Mostrar estado de conexión
    if connection_success:
        st.markdown(f'<div class="connection-status success">✅ {connection_message}</div>', 
                   unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="connection-status error">❌ {connection_message}</div>', 
                   unsafe_allow_html=True)
        st.markdown(f'<div class="connection-status warning">💡 Prueba subiendo el archivo CSV manualmente desde la barra lateral</div>', 
                   unsafe_allow_html=True)
        df_raw = load_demo_data()

elif data_source == "📁 Subir Archivo CSV":
    if 'uploaded_file' in locals() and uploaded_file is not None:
        try:
            df_raw = pd.read_csv(uploaded_file)
            st.markdown(f'<div class="connection-status success">✅ Archivo CSV cargado exitosamente</div>', 
                       unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="connection-status error">❌ Error al leer el archivo: {str(e)}</div>', 
                       unsafe_allow_html=True)
            df_raw = load_demo_data()
    else:
        st.markdown(f'<div class="connection-status warning">⬆️ Sube tu archivo CSV en la barra lateral</div>', 
                   unsafe_allow_html=True)
        df_raw = load_demo_data()

else:
    df_raw = load_demo_data()
    st.markdown(f'<div class="connection-status warning">🧪 Usando datos de demostración</div>', 
               unsafe_allow_html=True)

# Procesar datos
if df_raw.empty:
    st.error("❌ No se pudieron cargar los datos. Verifica la conexión a Google Sheets.")
    st.stop()

st.write("**Información del dataset cargado:**")
st.write(f"- Filas: {len(df_raw)}")
st.write(f"- Columnas: {len(df_raw.columns)}")

# Mostrar una muestra de los datos para debug
with st.expander("🔍 Ver muestra de datos (para debugging)"):
    st.write("**Primeras columnas:**")
    st.write(list(df_raw.columns))
    st.write("**Primeras 3 filas:**")
    st.dataframe(df_raw.head(3))

try:
    df = calculate_scores(df_raw)
except Exception as e:
    st.error(f"❌ Error procesando los datos: {str(e)}")
    st.write("**Intentando con datos de demostración...**")
    df_raw = load_demo_data()
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
    high_impact = len(df[df['nivel_impacto'] >= 4])
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

# Paleta de colores consistente
color_map = {
    'Quick Win': '#28a745',
    'Estratégica': '#ffc107', 
    'Relleno': '#17a2b8',
    'Baja Prioridad': '#dc3545'
}

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Matriz Esfuerzo-Impacto mejorada
        fig_matrix = go.Figure()
        
        for classification in df['Clasificación'].unique():
            subset = df[df['Clasificación'] == classification]
            fig_matrix.add_trace(go.Scatter(
                x=subset['Facilidad Implementación'],
                y=subset['nivel_impacto'],
                mode='markers',
                marker=dict(
                    size=subset['Puntuación Total'] / 1.5,
                    color=color_map[classification],
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                name=classification,
                text=df[df['Clasificación'] == classification]['Nombre_Iniciativa'].str[:25] + '...',
                hovertemplate='<b>%{text}</b><br>' +
                             'Impacto: %{y}<br>' +
                             'Facilidad: %{x}<br>' +
                             'Puntuación: %{marker.size:.0f}<br>' +
                             '<extra></extra>'
            ))
        
        # Líneas de cuadrantes
        fig_matrix.add_hline(y=3.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig_matrix.add_vline(x=3.5, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Etiquetas de cuadrantes
        annotations = [
            dict(x=2, y=4.7, text="Quick Wins", showarrow=False, font=dict(size=14, color="green", family="Arial Black")),
            dict(x=4.5, y=4.7, text="Estratégicas", showarrow=False, font=dict(size=14, color="orange", family="Arial Black")),
            dict(x=2, y=1.3, text="Relleno", showarrow=False, font=dict(size=14, color="blue", family="Arial Black")),
            dict(x=4.5, y=1.3, text="Baja Prioridad", showarrow=False, font=dict(size=14, color="red", family="Arial Black"))
        ]
        
        fig_matrix.update_layout(
            title="🎯 Matriz Facilidad de Implementación vs Impacto",
            xaxis_title="Facilidad de Implementación →",
            yaxis_title="Nivel de Impacto →",
            xaxis=dict(range=[0.5, 5.5], dtick=1),
            yaxis=dict(range=[0.5, 5.5], dtick=1),
            height=500,
            annotations=annotations,
            showlegend=True
        )
        
        st.plotly_chart(fig_matrix, use_container_width=True)
    
    with col2:
        # Distribución por área
        area_analysis = df.groupby('Área').agg({
            'Puntuación Total': ['mean', 'count'],
            'Clasificación': lambda x: (x == 'Quick Win').sum()
        }).round(1)
        
        area_analysis.columns = ['Puntuación Promedio', 'Total Iniciativas', 'Quick Wins']
        area_analysis = area_analysis.reset_index()
        area_analysis = area_analysis.sort_values('Total Iniciativas', ascending=True)
        
        fig_areas = px.bar(
            area_analysis,
            x='Total Iniciativas',
            y='Área',
            color='Puntuación Promedio',
            color_continuous_scale='viridis',
            text='Quick Wins',
            title="📊 Iniciativas por Área",
            height=500
        )
        
        fig_areas.update_traces(texttemplate='QW: %{text}', textposition='inside')
        fig_areas.update_layout(yaxis={'categoryorder': 'total ascending'})
        
        st.plotly_chart(fig_areas, use_container_width=True)
    
    # Segunda fila de gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Radar chart de criterios promedio por clasificación
        criteria = ['valor_estrategico', 'nivel_impacto', 'viabilidad_tecnica', 
                   'costo_beneficio', 'innovacion_disrupcion', 'escalabilidad_transversalidad']
        criteria_labels = ['Valor Estratégico', 'Nivel de Impacto', 'Viabilidad Técnica', 
                          'Costo-Beneficio', 'Innovación/Disrupción', 'Escalabilidad/Transversalidad']
        
        fig_radar = go.Figure()
        
        for classification in ['Quick Win', 'Estratégica', 'Relleno', 'Baja Prioridad']:
            if classification in df['Clasificación'].values:
                subset = df[df['Clasificación'] == classification]
                values = [subset[col].mean() for col in criteria]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=values,
                    theta=criteria_labels,
                    fill='toself',
                    name=classification,
                    line_color=color_map[classification],
                    opacity=0.6
                ))
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            title="🕸️ Perfil Promedio por Clasificación",
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
            title="📈 Distribución de Puntuaciones Totales",
            nbins=12,
            height=400
        )
        fig_hist.update_layout(bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Timeline si hay datos temporales
    st.subheader("📅 Timeline de Iniciativas")
    
    try:
        df['Fecha'] = pd.to_datetime(df['Marca temporal'])
        df['Fecha_Solo'] = df['Fecha'].dt.date
        
        fig_timeline = px.scatter(
            df, 
            x='Fecha', 
            y='Área',
            size='Puntuación Total', 
            color='Clasificación',
            color_discrete_map=color_map,
            hover_data=['Nombre de la idea o iniciativa  ' if 'Nombre de la idea o iniciativa  ' in df.columns else 'Ranking'],
            title="Iniciativas por Área en el Tiempo",
            height=300
        )
        fig_timeline.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_timeline, use_container_width=True)
    except:
        st.info("📅 Datos temporales no disponibles para timeline")

with tab2:
    st.subheader("🔍 Explorador de Iniciativas")
    
    # Filtros interactivos
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        area_filter = st.multiselect(
            "🏢 Áreas",
            options=sorted(df['Área'].unique()),
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
            ['Ranking', 'Puntuación Total', 'nivel_impacto', 'valor_estrategico']
        )
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if area_filter:
        filtered_df = filtered_df[filtered_df['Área'].isin(area_filter)]
    
    if classification_filter:
        filtered_df = filtered_df[filtered_df['Clasificación'].isin(classification_filter)]
    
    filtered_df = filtered_df[
        (filtered_df['nivel_impacto'] >= impact_range[0]) & 
        (filtered_df['nivel_impacto'] <= impact_range[1])
    ]
    
    # Ordenar
    filtered_df = filtered_df.sort_values(sort_by, ascending=False)
    
    st.info(f"📋 Mostrando {len(filtered_df)} de {len(df)} iniciativas")
    
    # Mostrar iniciativas en tarjetas
    for idx, row in filtered_df.head(15).iterrows():
        class_color = color_map.get(row['Clasificación'], '#666')
        
        with st.expander(f"#{row['Ranking']} - {row['Nombre_Iniciativa'][:50]}... ({row['Clasificación']})"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**👤 Propuesto por:** {row['Nombre_Completo']}")
                st.markdown(f"**🏢 Área:** {row['Área']}")
                
                # Buscar columnas de problema, propuesta y beneficios de forma robusta
                problema_col = get_column_name(df, [
                    '¿Qué problema, necesidad u oportunidad busca resolver?',
                    '¿Qué problema, necesidad u oportunidad busca resolver?  ',
                    'Problema',
                    'Necesidad'
                ])
                
                propuesta_col = get_column_name(df, [
                    '¿Cuál es tu propuesta?',
                    '¿Cuál es tu propuesta?  ',
                    'Propuesta',
                    'Solución'
                ])
                
                beneficios_col = get_column_name(df, [
                    '¿Qué beneficios esperas que genere?',
                    '¿Qué beneficios esperas que genere?  ',
                    'Beneficios',
                    'Beneficios esperados'
                ])
                
                if problema_col:
                    st.markdown(f"**🎯 Problema a resolver:**")
                    st.write(row[problema_col])
                
                if propuesta_col:
                    st.markdown(f"**💡 Propuesta:**")
                    st.write(row[propuesta_col])
                
                if beneficios_col:
                    st.markdown(f"**📈 Beneficios esperados:**")
                    st.write(row[beneficios_col])
            
            with col2:
                st.metric("🏆 Ranking", f"#{row['Ranking']}")
                st.metric("📊 Puntuación Total", f"{row['Puntuación Total']:.0f}/30")
                st.metric("🎯 Clasificación", row['Clasificación'])
                st.metric("⏱️ Tiempo Impl.", row['tiempo_implementacion'])
            
            with col3:
                # Mini métricas individuales
                st.metric("💎 Valor Estratégico", f"{row['valor_estrategico']}/5")
                st.metric("📊 Impacto", f"{row['nivel_impacto']}/5")
                st.metric("🔧 Viabilidad", f"{row['viabilidad_tecnica']}/5")
                st.metric("💰 Costo-Beneficio", f"{row['costo_beneficio']}/5")

with tab3:
    st.subheader("📈 Análisis Estadístico Avanzado")
    
    # Análisis de correlaciones
    col1, col2 = st.columns(2)
    
    with col1:
        # Matriz de correlación
        numeric_cols = ['valor_estrategico', 'nivel_impacto', 'viabilidad_tecnica',
                       'costo_beneficio', 'innovacion_disrupcion', 
                       'escalabilidad_transversalidad', 'tiempo_implementacion']
        
        corr_data = df[numeric_cols].rename(columns={
            'valor_estrategico': 'Valor Estratégico',
            'nivel_impacto': 'Nivel Impacto',
            'viabilidad_tecnica': 'Viabilidad Técnica',
            'costo_beneficio': 'Costo-Beneficio',
            'innovacion_disrupcion': 'Innovación',
            'escalabilidad_transversalidad': 'Escalabilidad',
            'tiempo_implementacion': 'Tiempo Impl.'
        })
        
        corr_matrix = corr_data.corr()
        
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            aspect="auto",
            title="🔗 Matriz de Correlación entre Criterios",
            color_continuous_scale='RdBu',
            height=400
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    
    with col2:
        # Análisis de dispersión configurable
        x_options = ['valor_estrategico', 'nivel_impacto', 'viabilidad_tecnica', 'costo_beneficio']
        y_options = ['innovacion_disrupcion', 'escalabilidad_transversalidad', 'Puntuación Total']
        
        x_axis = st.selectbox("Eje X", x_options, index=0, format_func=lambda x: x.replace('_', ' ').title())
        y_axis = st.selectbox("Eje Y", x_options + y_options, index=1, format_func=lambda x: x.replace('_', ' ').title())
        
        fig_scatter = px.scatter(
            df,
            x=x_axis,
            y=y_axis,
            color='Clasificación',
            size='Puntuación Total',
            hover_data=['Área'],
            color_discrete_map=color_map,
            title=f"📊 {x_axis.replace('_', ' ').title()} vs {y_axis.replace('_', ' ').title()}",
            height=400
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Benchmarking por área
    st.subheader("🏆 Benchmarking por Área")
    
    area_benchmarks = df.groupby('Área')[numeric_cols].mean().round(2)
    
    # Seleccionar criterios para mostrar
    selected_criteria = st.multiselect(
        "Selecciona criterios para comparar:",
        options=numeric_cols,
        default=['valor_estrategico', 'nivel_impacto', 'viabilidad_tecnica', 'innovacion_disrupcion'],
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if selected_criteria:
        fig_benchmark = go.Figure()
        
        areas = area_benchmarks.index
        
        for criterion in selected_criteria:
            fig_benchmark.add_trace(go.Bar(
                name=criterion.replace('_', ' ').title(),
                x=areas,
                y=area_benchmarks[criterion],
                text=area_benchmarks[criterion].round(1),
                textposition='auto',
            ))
        
        fig_benchmark.update_layout(
            title="📊 Puntuaciones Promedio por Área",
            xaxis_title="Área",
            yaxis_title="Puntuación Promedio",
            barmode='group',
            height=400,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig_benchmark, use_container_width=True)
    
    # Análisis temporal si disponible
    st.subheader("📅 Análisis Temporal")
    
    try:
        df['Fecha'] = pd.to_datetime(df['Marca temporal'])
        df['Fecha_Solo'] = df['Fecha'].dt.date
        
        temporal_data = df.groupby('Fecha_Solo').agg({
            'Puntuación Total': 'mean',
            'Ranking': 'count'
        }).rename(columns={'Ranking': 'Cantidad'}).reset_index()
        
        if len(temporal_data) > 1:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_temporal_count = px.line(
                    temporal_data,
                    x='Fecha_Solo',
                    y='Cantidad',
                    title="📈 Iniciativas Recibidas por Día",
                    markers=True
                )
                st.plotly_chart(fig_temporal_count, use_container_width=True)
            
            with col2:
                fig_temporal_score = px.line(
                    temporal_data,
                    x='Fecha_Solo',
                    y='Puntuación Total',
                    title="📊 Calidad Promedio por Día",
                    markers=True,
                    color_discrete_sequence=['orange']
                )
                st.plotly_chart(fig_temporal_score, use_container_width=True)
        else:
            st.info("📅 Se necesitan más datos para mostrar tendencias temporales")
    except:
        st.info("📅 Datos temporales no disponibles para análisis")

with tab4:
    st.subheader("🏆 Rankings y Reportes Ejecutivos")
    
    # Top performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥇 Top 10 Iniciativas")
        top_initiatives = df.nlargest(10, 'Puntuación Total')[
            ['Ranking', 'Nombre de la idea o iniciativa  ', 'Área', 'Puntuación Total', 'Clasificación']
        ].reset_index(drop=True)
        
        # Truncar nombres largos para mejor visualización
        if 'Nombre de la idea o iniciativa  ' in top_initiatives.columns:
            top_initiatives['Iniciativa'] = top_initiatives['Nombre de la idea o iniciativa  '].str[:40] + '...'
            top_initiatives = top_initiatives.drop('Nombre de la idea o iniciativa  ', axis=1)
        
        # Formatear tabla con colores
        def highlight_classification(row):
            colors = {
                'Quick Win': 'background-color: #d4edda; color: #155724',
                'Estratégica': 'background-color: #fff3cd; color: #856404',
                'Relleno': 'background-color: #d1ecf1; color: #0c5460',
                'Baja Prioridad': 'background-color: #f8d7da; color: #721c24'
            }
            style = [''] * len(row)
            if row['Clasificación'] in colors:
                style[row.index.get_loc('Clasificación')] = colors[row['Clasificación']]
            return style
        
        st.dataframe(
            top_initiatives.style.format({'Puntuación Total': '{:.0f}'}),
            use_container_width=True, 
            hide_index=True
        )
    
    with col2:
        st.markdown("### 🚀 Quick Wins Recomendados")
        
        quick_wins_columns = ['Ranking', 'Nombre_Iniciativa', 'Área', 'nivel_impacto', 'Facilidad Implementación', 'Puntuación Total']
        available_qw_columns = [col for col in quick_wins_columns if col in df.columns]
        
        quick_wins_df = df[df['Clasificación'] == 'Quick Win']
        
        if not quick_wins_df.empty and len(available_qw_columns) >= 3:
            quick_wins_table = quick_wins_df.nlargest(10, 'Puntuación Total')[available_qw_columns].reset_index(drop=True)
            
            if 'Nombre_Iniciativa' in quick_wins_table.columns:
                quick_wins_table['Iniciativa'] = quick_wins_table['Nombre_Iniciativa'].str[:30] + '...'
                quick_wins_table = quick_wins_table.drop('Nombre_Iniciativa', axis=1)
            
            st.dataframe(quick_wins_table, use_container_width=True, hide_index=True)
        else:
            st.info("🔍 No hay Quick Wins identificados con los filtros actuales")
    
    # Resumen ejecutivo
    st.markdown("### 📋 Resumen Ejecutivo")
    
    total_initiatives = len(df)
    avg_score = df['Puntuación Total'].mean()
    top_area = df['Área'].value_counts().index[0] if len(df) > 0 else "N/A"
    top_area_count = df['Área'].value_counts().iloc[0] if len(df) > 0 else 0
    
    classification_counts = df['Clasificación'].value_counts()
    
    st.markdown(f"""
    **📊 Resumen General ({datetime.now().strftime('%Y-%m-%d')})**
    
    - **Total de iniciativas evaluadas:** {total_initiatives}
    - **Puntuación promedio:** {avg_score:.1f}/30 ({(avg_score/30)*100:.1f}%)
    - **Área más activa:** {top_area} ({top_area_count} iniciativas)
    - **Quick Wins identificados:** {classification_counts.get('Quick Win', 0)} ({(classification_counts.get('Quick Win', 0)/total_initiatives)*100:.1f}%)
    - **Iniciativas estratégicas:** {classification_counts.get('Estratégica', 0)} ({(classification_counts.get('Estratégica', 0)/total_initiatives)*100:.1f}%)
    
    **🎯 Recomendaciones Principales:**
    1. **Priorizar Quick Wins:** Implementar inmediatamente las {classification_counts.get('Quick Win', 0)} iniciativas de alto impacto y fácil implementación
    2. **Planificar estratégicas:** Desarrollar roadmap para las {classification_counts.get('Estratégica', 0)} iniciativas de alto impacto
    3. **Foco en {top_area}:** Apoyar especialmente esta área que muestra mayor actividad innovadora
    4. **Mejorar scoring:** Las iniciativas con puntuación inferior a 15 puntos necesitan refinamiento
    """)
    
    # Análisis por área detallado
    st.markdown("### 📊 Análisis Detallado por Área")
    
    area_summary = df.groupby('Área').agg({
        'Puntuación Total': ['count', 'mean', 'max'],
        'Clasificación': [lambda x: (x == 'Quick Win').sum(), lambda x: (x == 'Estratégica').sum()],
        'nivel_impacto': 'mean',
        'valor_estrategico': 'mean'
    }).round(2)
    
    area_summary.columns = ['Total_Iniciativas', 'Puntuacion_Promedio', 'Puntuacion_Maxima', 'Quick_Wins', 'Estrategicas', 'Impacto_Promedio', 'Valor_Estrategico_Promedio']
    area_summary = area_summary.reset_index().sort_values('Total_Iniciativas', ascending=False)
    
    st.dataframe(area_summary, use_container_width=True, hide_index=True)
    
    # Exportar reportes
    st.markdown("### 💾 Exportar Reportes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Reporte completo
        export_columns = ['Ranking', 'Nombre_Iniciativa', 'Nombre_Completo', 'Área', 'Clasificación', 'Puntuación Total', 
                         'valor_estrategico', 'nivel_impacto', 'viabilidad_tecnica', 'costo_beneficio', 
                         'innovacion_disrupcion', 'escalabilidad_transversalidad', 'tiempo_implementacion']
        
        available_export_columns = [col for col in export_columns if col in df.columns]
        export_df = df[available_export_columns].sort_values('Ranking')
        
        csv_complete = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Reporte Completo (CSV)",
            data=csv_complete,
            file_name=f"reporte_completo_iniciativas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Solo Quick Wins
        quick_wins_export_columns = ['Ranking', 'Nombre_Iniciativa', 'Nombre_Completo', 'Área', 'Puntuación Total']
        
        # Agregar columnas de detalles si existen
        detail_columns = [
            '¿Qué problema, necesidad u oportunidad busca resolver?',
            '¿Qué problema, necesidad u oportunidad busca resolver?  ',
            '¿Cuál es tu propuesta?',
            '¿Cuál es tu propuesta?  ',
            '¿Qué beneficios esperas que genere?',
            '¿Qué beneficios esperas que genere?  '
        ]
        
        for col in detail_columns:
            if col in df.columns:
                quick_wins_export_columns.append(col)
        
        available_qw_export_columns = [col for col in quick_wins_export_columns if col in df.columns]
        quick_wins_export = df[df['Clasificación'] == 'Quick Win'][available_qw_export_columns].sort_values('Ranking')
        
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
        csv_area_summary = area_summary.to_csv(index=False)
        st.download_button(
            label="📊 Resumen por Área (CSV)",
            data=csv_area_summary,
            file_name=f"resumen_areas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# Estadísticas rápidas en sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("📈 Estadísticas Rápidas")
    
    if not df.empty:
        st.metric("💯 Mejor Puntuación", f"{df['Puntuación Total'].max():.0f}/30")
        st.metric("🎯 Promedio de Impacto", f"{df['nivel_impacto'].mean():.1f}/5")
        st.metric("⚡ % Quick Wins", f"{(len(df[df['Clasificación'] == 'Quick Win'])/len(df)*100):.1f}%")
        
        # Mini gráfico de distribución
        classification_counts = df['Clasificación'].value_counts()
        fig_mini_dist = px.pie(
            values=classification_counts.values,
            names=classification_counts.index,
            color_discrete_map=color_map,
            height=200
        )
        fig_mini_dist.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False
        )
        fig_mini_dist.update_traces(textinfo='percent', textfont_size=10)
        st.plotly_chart(fig_mini_dist, use_container_width=True)

# Footer informativo
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>💡 <strong>Sistema de Análisis de Iniciativas de Innovación - Alico</strong></p>
    <p>🔗 Conectado automáticamente a Google Sheets | Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <p>📧 Para soporte técnico contacta al equipo de Innovación</p>
</div>
""", unsafe_allow_html=True)
