import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import requests
from io import BytesIO, StringIO
import base64

# Importaciones para PDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para evitar problemas en servidores sin display

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Iniciativas de Innovación",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2d5aa0;
        margin: 0.5rem 0;
    }
    .priority-high {
        border-left-color: #28a745 !important;
        background: #d4edda !important;
    }
    .priority-medium {
        border-left-color: #ffc107 !important;
        background: #fff3cd !important;
    }
    .priority-low {
        border-left-color: #dc3545 !important;
        background: #f8d7da !important;
    }
</style>
""", unsafe_allow_html=True)

# Función para cargar datos
@st.cache_data
def load_data_from_url():
    """Carga los datos desde Google Sheets"""
    try:
        # URL directa para descargar el CSV desde Google Sheets
        sheet_id = "1yWHTveQlQEKi7fLdDxxKPLdEjGvD7PaTzAbRYvSBEp0"
        
        # Intentar diferentes formatos de URL
        urls_to_try = [
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0",
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv",
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Respuestas de formulario 1"
        ]
        
        for url in urls_to_try:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                # Leer el contenido como CSV
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                
                if len(df) > 0:
                    st.success(f"✅ Datos cargados exitosamente desde Google Sheets ({len(df)} registros)")
                    return df
                    
            except Exception as e:
                continue
                
        # Si ninguna URL funciona, mostrar instrucciones
        st.error("❌ No se pudieron cargar los datos desde Google Sheets.")
        st.warning("🔧 **Para solucionar este problema:**")
        st.markdown("""
        1. **Hacer el Google Sheets público:**
           - Abrir el Google Sheets
           - Clic en "Compartir" (esquina superior derecha)
           - Clic en "Cambiar a cualquier persona con el enlace"
           - Seleccionar "Visualizador"
           - Guardar
        
        2. **Verificar el ID del sheet:**
           - El ID debe estar entre `/d/` y `/edit` en la URL
           - Ejemplo: `https://docs.google.com/spreadsheets/d/[ID_AQUI]/edit`
        
        3. **Como alternativa, subir el archivo manualmente** usando la opción en la barra lateral.
        """)
        return None
        
    except Exception as e:
        st.error(f"Error al cargar datos desde Google Sheets: {str(e)}")
        return None

@st.cache_data
def load_data_from_file(uploaded_file):
    """Carga los datos desde archivo subido"""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return None

def clean_and_process_data(df):
    """Limpia y procesa los datos"""
    if df is None:
        return None
    
    # Crear una copia para trabajar
    df_clean = df.copy()
    
    # Limpiar nombres de columnas
    df_clean.columns = [col.strip() for col in df_clean.columns]
    
    # Mapeo de nombres de columnas (para manejar variaciones)
    column_mapping = {
        'Nombre de la idea o iniciativa  ': 'Nombre_Iniciativa',
        'Nombre de la idea o iniciativa': 'Nombre_Iniciativa',
        'Nombre completo': 'Nombre_Colaborador',
        'Selecciona el área o proceso al cual perteneces ': 'Area',
        'Selecciona el área o proceso al cual perteneces': 'Area',
        '¿Qué problema, necesidad u oportunidad busca resolver?  ': 'Problema',
        '¿Qué problema, necesidad u oportunidad busca resolver?': 'Problema',
        '¿Cuál es tu propuesta?  ': 'Propuesta',
        '¿Cuál es tu propuesta?': 'Propuesta',
        '¿Qué beneficios esperas que genere?  ': 'Beneficios',
        '¿Qué beneficios esperas que genere?': 'Beneficios',
        'Valor estratégico': 'Valor_Estrategico',
        'Nivel de impacto': 'Nivel_Impacto',
        'Viabilidad técnica': 'Viabilidad_Tecnica',
        'Costo-beneficio': 'Costo_Beneficio',
        'Innovación / disrupción ': 'Innovacion_Disrupcion',
        'Innovación / disrupción': 'Innovacion_Disrupcion',
        'Escalabilidad / transversalidad ': 'Escalabilidad_Transversalidad',
        'Escalabilidad / transversalidad': 'Escalabilidad_Transversalidad',
        'Tiempo de implementación ': 'Tiempo_Implementacion',
        'Tiempo de implementación': 'Tiempo_Implementacion',
        'Marca temporal': 'Fecha'
    }
    
    # Aplicar mapeo de columnas
    df_clean = df_clean.rename(columns=column_mapping)
    
    # Filtrar registros válidos
    valid_mask = (
        df_clean['Nombre_Colaborador'].notna() & 
        df_clean['Nombre_Iniciativa'].notna() &
        (df_clean['Nombre_Colaborador'].astype(str).str.strip() != '') &
        (df_clean['Nombre_Iniciativa'].astype(str).str.strip() != '')
    )
    df_clean = df_clean[valid_mask].copy()
    
    # Convertir campos numéricos
    numeric_fields = ['Valor_Estrategico', 'Nivel_Impacto', 'Viabilidad_Tecnica', 
                     'Costo_Beneficio', 'Innovacion_Disrupcion', 
                     'Escalabilidad_Transversalidad', 'Tiempo_Implementacion']
    
    for field in numeric_fields:
        if field in df_clean.columns:
            df_clean[field] = pd.to_numeric(df_clean[field], errors='coerce').fillna(0)
    
    # Calcular métricas derivadas
    df_clean['Puntuacion_Total'] = (
        df_clean['Valor_Estrategico'] + 
        df_clean['Nivel_Impacto'] + 
        df_clean['Viabilidad_Tecnica'] + 
        df_clean['Costo_Beneficio'] + 
        df_clean['Innovacion_Disrupcion'] + 
        df_clean['Escalabilidad_Transversalidad'] + 
        df_clean['Tiempo_Implementacion']
    )
    
    # Calcular puntuación ponderada (criterio de priorización)
    df_clean['Puntuacion_Ponderada'] = (
        df_clean['Valor_Estrategico'] * 0.20 +  # 20% Valor estratégico
        df_clean['Nivel_Impacto'] * 0.20 +      # 20% Nivel de impacto
        df_clean['Viabilidad_Tecnica'] * 0.15 + # 15% Viabilidad técnica
        df_clean['Costo_Beneficio'] * 0.15 +    # 15% Costo-beneficio
        df_clean['Innovacion_Disrupcion'] * 0.10 + # 10% Innovación
        df_clean['Escalabilidad_Transversalidad'] * 0.10 + # 10% Escalabilidad
        df_clean['Tiempo_Implementacion'] * 0.10   # 10% Tiempo (más rápido = mejor)
    )
    
    # Categorizar prioridad
    def categorizar_prioridad(score):
        if score >= 3.5:
            return "Alta"
        elif score >= 2.5:
            return "Media"
        else:
            return "Baja"
    
    df_clean['Prioridad'] = df_clean['Puntuacion_Ponderada'].apply(categorizar_prioridad)
    
    # Calcular índice de facilidad de implementación
    df_clean['Facilidad_Implementacion'] = (
        (df_clean['Viabilidad_Tecnica'] + df_clean['Costo_Beneficio'] + df_clean['Tiempo_Implementacion']) / 3
    )
    
def generate_pdf_report(df_filtered):
    """Genera un reporte ejecutivo en PDF profesional"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Centrado
        textColor=colors.HexColor('#2d5aa0')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#1f4e79')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=0
    )
    
    # Elementos del documento
    elements = []
    
    # Título principal
    elements.append(Paragraph("REPORTE EJECUTIVO", title_style))
    elements.append(Paragraph("Análisis de Iniciativas de Innovación", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    # Fecha del reporte
    fecha_actual = datetime.now().strftime("%d de %B de %Y")
    elements.append(Paragraph(f"<b>Fecha del reporte:</b> {fecha_actual}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Resumen ejecutivo
    total_initiatives = len(df_filtered)
    high_priority = len(df_filtered[df_filtered['Prioridad'] == 'Alta'])
    medium_priority = len(df_filtered[df_filtered['Prioridad'] == 'Media'])
    low_priority = len(df_filtered[df_filtered['Prioridad'] == 'Baja'])
    avg_score = df_filtered['Puntuacion_Ponderada'].mean()
    
    elements.append(Paragraph("RESUMEN EJECUTIVO", heading_style))
    
    summary_data = [
        ['Métrica', 'Valor', 'Observaciones'],
        ['Total de iniciativas evaluadas', str(total_initiatives), 'Propuestas recibidas en el período'],
        ['Iniciativas de alta prioridad', f"{high_priority} ({high_priority/total_initiatives*100:.1f}%)", 'Recomendadas para implementación inmediata'],
        ['Iniciativas de prioridad media', f"{medium_priority} ({medium_priority/total_initiatives*100:.1f}%)", 'Requieren análisis adicional'],
        ['Iniciativas de prioridad baja', f"{low_priority} ({low_priority/total_initiatives*100:.1f}%)", 'Para revisión a largo plazo'],
        ['Puntuación promedio general', f"{avg_score:.2f}/5.0", 'Calidad general de las propuestas'],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Top 5 iniciativas
    elements.append(Paragraph("TOP 5 INICIATIVAS RECOMENDADAS", heading_style))
    
    top_5 = df_filtered.nlargest(5, 'Puntuacion_Ponderada')
    
    for i, (_, row) in enumerate(top_5.iterrows(), 1):
        elements.append(Paragraph(f"<b>{i}. {row['Nombre_Iniciativa']}</b>", normal_style))
        elements.append(Paragraph(f"<b>Propuesta por:</b> {row['Nombre_Colaborador']} ({row['Area']})", normal_style))
        elements.append(Paragraph(f"<b>Puntuación:</b> {row['Puntuacion_Ponderada']:.2f}/5.0 - <b>Prioridad:</b> {row['Prioridad']}", normal_style))
        
        # Mostrar fortalezas principales
        metrics = {
            'Valor_Estrategico': 'Valor Estratégico',
            'Nivel_Impacto': 'Nivel de Impacto',
            'Viabilidad_Tecnica': 'Viabilidad Técnica',
            'Costo_Beneficio': 'Costo-Beneficio',
            'Innovacion_Disrupcion': 'Innovación',
            'Escalabilidad_Transversalidad': 'Escalabilidad',
            'Tiempo_Implementacion': 'Tiempo de Implementación'
        }
        
        fortalezas = []
        for metric_key, metric_name in metrics.items():
            if row[metric_key] >= 4:
                fortalezas.append(f"{metric_name} ({row[metric_key]}/5)")
        
        if fortalezas:
            elements.append(Paragraph(f"<b>Fortalezas:</b> {', '.join(fortalezas)}", normal_style))
        
        problema = row.get('Problema', 'No especificado')
        if len(problema) > 100:
            problema = problema[:100] + "..."
        elements.append(Paragraph(f"<b>Problema que resuelve:</b> {problema}", normal_style))
        elements.append(Spacer(1, 10))
    
    # Análisis por área
    elements.append(Paragraph("ANÁLISIS POR ÁREA ORGANIZACIONAL", heading_style))
    
    area_analysis = df_filtered.groupby('Area').agg({
        'Puntuacion_Ponderada': ['count', 'mean'],
        'Prioridad': lambda x: (x == 'Alta').sum()
    }).round(2)
    
    area_analysis.columns = ['Num_Iniciativas', 'Puntuacion_Promedio', 'Alta_Prioridad']
    area_analysis = area_analysis.sort_values('Puntuacion_Promedio', ascending=False)
    
    area_data = [['Área', 'N° Iniciativas', 'Puntuación Promedio', 'Alta Prioridad']]
    for area, data in area_analysis.iterrows():
        area_data.append([
            area,
            str(int(data['Num_Iniciativas'])),
            f"{data['Puntuacion_Promedio']:.2f}",
            str(int(data['Alta_Prioridad']))
        ])
    
    area_table = Table(area_data, colWidths=[2*inch, 1.2*inch, 1.5*inch, 1.2*inch])
    area_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(area_table)
    elements.append(Spacer(1, 20))
    
    # Recomendaciones estratégicas
    elements.append(Paragraph("RECOMENDACIONES ESTRATÉGICAS", heading_style))
    
    recomendaciones = []
    
    if high_priority > 0:
        recomendaciones.append(f"<b>Implementación inmediata:</b> Priorizar las {high_priority} iniciativas de alta puntuación para obtener resultados rápidos y visibles.")
    
    if medium_priority > 0:
        recomendaciones.append(f"<b>Análisis detallado:</b> Las {medium_priority} iniciativas de prioridad media requieren evaluación adicional de recursos y timeline.")
    
    # Identificar área más activa
    most_active_area = df_filtered['Area'].value_counts().index[0] if len(df_filtered) > 0 else "N/A"
    recomendaciones.append(f"<b>Reconocimiento:</b> El área de '{most_active_area}' muestra el mayor nivel de participación en el proceso de innovación.")
    
    # Análisis de viabilidad
    low_viability = len(df_filtered[df_filtered['Viabilidad_Tecnica'] < 3])
    if low_viability > 0:
        recomendaciones.append(f"<b>Desarrollo de capacidades:</b> {low_viability} iniciativas presentan desafíos de viabilidad técnica que requieren fortalecimiento de capacidades.")
    
    # Oportunidades de escalabilidad
    high_scalability = len(df_filtered[df_filtered['Escalabilidad_Transversalidad'] >= 4])
    if high_scalability > 0:
        recomendaciones.append(f"<b>Potencial de escalabilidad:</b> {high_scalability} iniciativas muestran alto potencial de replicación en otras áreas.")
    
    for recom in recomendaciones:
        elements.append(Paragraph(f"• {recom}", normal_style))
        elements.append(Spacer(1, 8))
    
    # Próximos pasos
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("PRÓXIMOS PASOS SUGERIDOS", heading_style))
    
    next_steps = [
        "Convocar comité de evaluación para revisar iniciativas de alta prioridad",
        "Asignar recursos y equipos para las 3 mejores iniciativas",
        "Establecer cronograma de implementación con hitos específicos",
        "Definir métricas de éxito y sistema de seguimiento",
        "Comunicar resultados a los colaboradores participantes",
        "Planificar siguiente ciclo de recolección de iniciativas"
    ]
    
    for step in next_steps:
        elements.append(Paragraph(f"• {step}", normal_style))
        elements.append(Spacer(1, 6))
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("___", normal_style))
    elements.append(Paragraph("Reporte generado automáticamente por el Sistema de Análisis de Iniciativas de Innovación", 
                              ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)))
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Header principal
st.markdown('<div class="main-header"><h1>💡 Analizador de Iniciativas de Innovación</h1><p>Sistema de Análisis y Priorización de Propuestas</p></div>', unsafe_allow_html=True)

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Opción para cargar datos
data_source = st.sidebar.radio(
    "Fuente de datos:",
    ["Google Sheets (Automático)", "Subir archivo"]
)

# Cargar datos según la opción seleccionada
df = None
if data_source == "Google Sheets (Automático)":
    if st.sidebar.button("🔄 Actualizar datos"):
        st.cache_data.clear()
    df = load_data_from_url()
else:
    uploaded_file = st.sidebar.file_uploader(
        "Subir archivo Excel/CSV",
        type=['xlsx', 'xls', 'csv'],
        help="Sube tu archivo de iniciativas"
    )
    if uploaded_file is not None:
        df = load_data_from_file(uploaded_file)

# Procesar datos si están disponibles
if df is not None:
    df_processed = clean_and_process_data(df)
    
    if df_processed is not None and len(df_processed) > 0:
        
        # Filtros en sidebar
        st.sidebar.subheader("🔍 Filtros")
        
        # Filtro por área
        areas_disponibles = ['Todas'] + sorted(df_processed['Area'].unique().tolist())
        area_selected = st.sidebar.selectbox("Área:", areas_disponibles)
        
        # Filtro por prioridad
        prioridades = ['Todas'] + sorted(df_processed['Prioridad'].unique().tolist())
        prioridad_selected = st.sidebar.selectbox("Prioridad:", prioridades)
        
        # Aplicar filtros
        df_filtered = df_processed.copy()
        if area_selected != 'Todas':
            df_filtered = df_filtered[df_filtered['Area'] == area_selected]
        if prioridad_selected != 'Todas':
            df_filtered = df_filtered[df_filtered['Prioridad'] == prioridad_selected]
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📊 Total de Iniciativas",
                value=len(df_filtered),
                delta=f"de {len(df_processed)} totales"
            )
        
        with col2:
            avg_score = df_filtered['Puntuacion_Ponderada'].mean()
            st.metric(
                label="⭐ Puntuación Promedio",
                value=f"{avg_score:.2f}",
                delta="(escala 0-5)"
            )
        
        with col3:
            high_priority = len(df_filtered[df_filtered['Prioridad'] == 'Alta'])
            st.metric(
                label="🚀 Alta Prioridad",
                value=high_priority,
                delta=f"{high_priority/len(df_filtered)*100:.1f}%" if len(df_filtered) > 0 else "0%"
            )
        
        with col4:
            areas_activas = df_filtered['Area'].nunique()
            st.metric(
                label="🏢 Áreas Participantes",
                value=areas_activas,
                delta=f"de {df_processed['Area'].nunique()} totales"
            )
        
        # Pestañas principales
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Análisis General", 
            "🏆 Ranking de Iniciativas", 
            "📊 Análisis por Área", 
            "🔍 Detalle de Iniciativas",
            "📋 Reporte Ejecutivo"
        ])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de radar promedio
                if len(df_filtered) > 0:
                    metrics = ['Valor_Estrategico', 'Nivel_Impacto', 'Viabilidad_Tecnica', 
                              'Costo_Beneficio', 'Innovacion_Disrupcion', 
                              'Escalabilidad_Transversalidad', 'Tiempo_Implementacion']
                    
                    avg_values = [df_filtered[metric].mean() for metric in metrics]
                    
                    fig_radar = go.Figure()
                    
                    fig_radar.add_trace(go.Scatterpolar(
                        r=avg_values,
                        theta=['Valor Estratégico', 'Nivel Impacto', 'Viabilidad Técnica',
                               'Costo-Beneficio', 'Innovación', 'Escalabilidad', 'Tiempo Impl.'],
                        fill='toself',
                        name='Promedio General',
                        line=dict(color='#2d5aa0')
                    ))
                    
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 5])
                        ),
                        showlegend=False,
                        title="Perfil Promedio de Iniciativas"
                    )
                    
                    st.plotly_chart(fig_radar, use_container_width=True)
            
            with col2:
                # Distribución por prioridad
                priority_counts = df_filtered['Prioridad'].value_counts()
                
                fig_pie = px.pie(
                    values=priority_counts.values,
                    names=priority_counts.index,
                    title="Distribución por Prioridad",
                    color_discrete_map={'Alta': '#28a745', 'Media': '#ffc107', 'Baja': '#dc3545'}
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Histograma de puntuaciones
            fig_hist = px.histogram(
                df_filtered,
                x='Puntuacion_Ponderada',
                nbins=20,
                title="Distribución de Puntuaciones Ponderadas",
                labels={'Puntuacion_Ponderada': 'Puntuación Ponderada', 'count': 'Número de Iniciativas'}
            )
            fig_hist.update_layout(showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with tab2:
            st.subheader("🏆 Ranking de Iniciativas")
            
            # Top iniciativas
            df_ranked = df_filtered.sort_values('Puntuacion_Ponderada', ascending=False).reset_index(drop=True)
            
            for idx, row in df_ranked.head(10).iterrows():
                priority_class = f"priority-{row['Prioridad'].lower()}"
                
                st.markdown(f"""
                <div class="metric-card {priority_class}">
                    <h4>#{idx+1} {row['Nombre_Iniciativa']}</h4>
                    <p><strong>Propuesto por:</strong> {row['Nombre_Colaborador']} ({row['Area']})</p>
                    <p><strong>Puntuación:</strong> {row['Puntuacion_Ponderada']:.2f}/5.0 | 
                       <strong>Prioridad:</strong> {row['Prioridad']}</p>
                    <p><strong>Problema:</strong> {row.get('Problema', 'No especificado')[:100]}...</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Matriz de comparación
            if len(df_filtered) > 1:
                st.subheader("📊 Matriz de Análisis: Impacto vs Facilidad de Implementación")
                
                fig_scatter = px.scatter(
                    df_filtered,
                    x='Facilidad_Implementacion',
                    y='Nivel_Impacto',
                    size='Puntuacion_Ponderada',
                    color='Prioridad',
                    hover_name='Nombre_Iniciativa',
                    hover_data=['Nombre_Colaborador', 'Area'],
                    title="Matriz de Priorización",
                    labels={
                        'Facilidad_Implementacion': 'Facilidad de Implementación',
                        'Nivel_Impacto': 'Nivel de Impacto'
                    },
                    color_discrete_map={'Alta': '#28a745', 'Media': '#ffc107', 'Baja': '#dc3545'}
                )
                
                # Añadir líneas de referencia
                fig_scatter.add_hline(y=2.5, line_dash="dash", line_color="gray", annotation_text="Impacto Medio")
                fig_scatter.add_vline(x=2.5, line_dash="dash", line_color="gray", annotation_text="Facilidad Media")
                
                st.plotly_chart(fig_scatter, use_container_width=True)
        
        with tab3:
            st.subheader("📊 Análisis por Área")
            
            # Análisis por área
            area_analysis = df_filtered.groupby('Area').agg({
                'Puntuacion_Ponderada': ['count', 'mean', 'std'],
                'Valor_Estrategico': 'mean',
                'Nivel_Impacto': 'mean',
                'Viabilidad_Tecnica': 'mean',
                'Costo_Beneficio': 'mean',
                'Innovacion_Disrupcion': 'mean',
                'Escalabilidad_Transversalidad': 'mean',
                'Tiempo_Implementacion': 'mean'
            }).round(2)
            
            area_analysis.columns = ['Num_Iniciativas', 'Puntuacion_Promedio', 'Desv_Estandar',
                                   'Val_Estrategico', 'Impacto', 'Viabilidad', 'Costo_Beneficio',
                                   'Innovacion', 'Escalabilidad', 'Tiempo_Impl']
            
            # Gráfico de barras por área
            col1, col2 = st.columns(2)
            
            with col1:
                fig_bar = px.bar(
                    x=area_analysis.index,
                    y=area_analysis['Num_Iniciativas'],
                    title="Número de Iniciativas por Área",
                    labels={'x': 'Área', 'y': 'Número de Iniciativas'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                fig_bar2 = px.bar(
                    x=area_analysis.index,
                    y=area_analysis['Puntuacion_Promedio'],
                    title="Puntuación Promedio por Área",
                    labels={'x': 'Área', 'y': 'Puntuación Promedio'}
                )
                st.plotly_chart(fig_bar2, use_container_width=True)
            
            # Heatmap de métricas por área
            if len(area_analysis) > 1:
                metrics_cols = ['Val_Estrategico', 'Impacto', 'Viabilidad', 'Costo_Beneficio',
                               'Innovacion', 'Escalabilidad', 'Tiempo_Impl']
                
                fig_heatmap = px.imshow(
                    area_analysis[metrics_cols].T,
                    labels=dict(x="Área", y="Métrica", color="Puntuación"),
                    x=area_analysis.index,
                    y=['Valor Estratégico', 'Impacto', 'Viabilidad', 'Costo-Beneficio',
                       'Innovación', 'Escalabilidad', 'Tiempo Impl.'],
                    title="Mapa de Calor: Métricas por Área",
                    aspect="auto"
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Tabla resumen
            st.subheader("📋 Resumen por Área")
            st.dataframe(area_analysis, use_container_width=True)
        
        with tab4:
            st.subheader("🔍 Detalle de Iniciativas")
            
            # Selector de iniciativa
            iniciativas_list = df_filtered['Nombre_Iniciativa'].tolist()
            
            if iniciativas_list:
                selected_initiative = st.selectbox(
                    "Selecciona una iniciativa para ver detalles:",
                    iniciativas_list
                )
                
                # Mostrar detalles de la iniciativa seleccionada
                init_data = df_filtered[df_filtered['Nombre_Iniciativa'] == selected_initiative].iloc[0]
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    ### {init_data['Nombre_Iniciativa']}
                    
                    **👤 Propuesta por:** {init_data['Nombre_Colaborador']}  
                    **🏢 Área:** {init_data['Area']}  
                    **⭐ Puntuación Ponderada:** {init_data['Puntuacion_Ponderada']:.2f}/5.0  
                    **🎯 Prioridad:** {init_data['Prioridad']}
                    
                    **📝 Problema que resuelve:**
                    {init_data.get('Problema', 'No especificado')}
                    
                    **💡 Propuesta:**
                    {init_data.get('Propuesta', 'No especificada')}
                    
                    **✅ Beneficios esperados:**
                    {init_data.get('Beneficios', 'No especificados')}
                    """)
                
                with col2:
                    # Gráfico radar individual
                    metrics = ['Valor_Estrategico', 'Nivel_Impacto', 'Viabilidad_Tecnica', 
                              'Costo_Beneficio', 'Innovacion_Disrupcion', 
                              'Escalabilidad_Transversalidad', 'Tiempo_Implementacion']
                    
                    values = [init_data[metric] for metric in metrics]
                    
                    fig_individual = go.Figure()
                    
                    fig_individual.add_trace(go.Scatterpolar(
                        r=values,
                        theta=['Val. Estratégico', 'Impacto', 'Viabilidad',
                               'Costo-Beneficio', 'Innovación', 'Escalabilidad', 'Tiempo'],
                        fill='toself',
                        name=selected_initiative,
                        line=dict(color='#2d5aa0')
                    ))
                    
                    fig_individual.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                        showlegend=False,
                        title="Perfil de la Iniciativa"
                    )
                    
                    st.plotly_chart(fig_individual, use_container_width=True)
                
                # Métricas detalladas
                st.subheader("📊 Métricas Detalladas")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Valor Estratégico", f"{init_data['Valor_Estrategico']}/5")
                    st.metric("Nivel de Impacto", f"{init_data['Nivel_Impacto']}/5")
                
                with col2:
                    st.metric("Viabilidad Técnica", f"{init_data['Viabilidad_Tecnica']}/5")
                    st.metric("Costo-Beneficio", f"{init_data['Costo_Beneficio']}/5")
                
                with col3:
                    st.metric("Innovación", f"{init_data['Innovacion_Disrupcion']}/5")
                    st.metric("Escalabilidad", f"{init_data['Escalabilidad_Transversalidad']}/5")
                
                with col4:
                    st.metric("Tiempo Implementación", f"{init_data['Tiempo_Implementacion']}/5")
                    st.metric("Puntuación Total", f"{init_data['Puntuacion_Total']}/35")
        
        with tab5:
            st.subheader("📋 Reporte Ejecutivo")
            
            # Botones en la parte superior
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            
            with col_btn1:
                # Botón para descargar reporte PDF
                if st.button("📄 Generar Reporte PDF", type="primary"):
                    try:
                        with st.spinner("Generando reporte PDF..."):
                            pdf_buffer = generate_pdf_report(df_filtered)
                            
                        st.download_button(
                            label="⬇️ Descargar Reporte PDF",
                            data=pdf_buffer,
                            file_name=f"reporte_ejecutivo_innovacion_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf"
                        )
                        st.success("✅ Reporte PDF generado exitosamente!")
                        
                    except Exception as e:
                        st.error(f"Error al generar PDF: {str(e)}")
                        st.info("💡 Tip: Asegúrate de que todas las dependencias estén instaladas correctamente")
            
            with col_btn2:
                # Botón para descargar datos CSV
                if st.button("📊 Descargar Datos CSV"):
                    csv = df_filtered.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Descargar CSV",
                        data=csv,
                        file_name=f"iniciativas_innovacion_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            st.markdown("---")
            
            # Resumen ejecutivo
            total_initiatives = len(df_filtered)
            high_priority = len(df_filtered[df_filtered['Prioridad'] == 'Alta'])
            medium_priority = len(df_filtered[df_filtered['Prioridad'] == 'Media'])
            low_priority = len(df_filtered[df_filtered['Prioridad'] == 'Baja'])
            avg_score = df_filtered['Puntuacion_Ponderada'].mean()
            top_area = df_filtered['Area'].value_counts().index[0] if len(df_filtered) > 0 else "N/A"
            
            st.markdown(f"""
            ### 📊 Resumen Ejecutivo
            
            **Período de análisis:** {datetime.now().strftime('%B %Y')}
            
            #### Métricas Clave:
            """)
            
            # Métricas en columnas
            met_col1, met_col2, met_col3, met_col4 = st.columns(4)
            
            with met_col1:
                st.metric(
                    label="Total Iniciativas",
                    value=total_initiatives,
                    help="Número total de propuestas evaluadas"
                )
            
            with met_col2:
                st.metric(
                    label="Alta Prioridad",
                    value=f"{high_priority}",
                    delta=f"{high_priority/total_initiatives*100:.1f}%" if total_initiatives > 0 else "0%",
                    help="Iniciativas recomendadas para implementación inmediata"
                )
            
            with met_col3:
                st.metric(
                    label="Puntuación Promedio",
                    value=f"{avg_score:.2f}/5.0",
                    help="Calidad general de las propuestas"
                )
            
            with met_col4:
                st.metric(
                    label="Área Más Activa",
                    value=top_area,
                    help="Área con mayor número de propuestas"
                )
            
            # Distribución de prioridades (gráfico más compacto)
            st.markdown("#### 🎯 Distribución de Prioridades")
            priority_col1, priority_col2 = st.columns([1, 2])
            
            with priority_col1:
                priority_data = {
                    'Prioridad': ['Alta', 'Media', 'Baja'],
                    'Cantidad': [high_priority, medium_priority, low_priority],
                    'Porcentaje': [
                        f"{high_priority/total_initiatives*100:.1f}%" if total_initiatives > 0 else "0%",
                        f"{medium_priority/total_initiatives*100:.1f}%" if total_initiatives > 0 else "0%",
                        f"{low_priority/total_initiatives*100:.1f}%" if total_initiatives > 0 else "0%"
                    ]
                }
                st.dataframe(pd.DataFrame(priority_data), hide_index=True)
            
            with priority_col2:
                if total_initiatives > 0:
                    fig_priority_pie = px.pie(
                        values=[high_priority, medium_priority, low_priority],
                        names=['Alta', 'Media', 'Baja'],
                        color_discrete_map={'Alta': '#28a745', 'Media': '#ffc107', 'Baja': '#dc3545'},
                        height=300
                    )
                    fig_priority_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_priority_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                    st.plotly_chart(fig_priority_pie, use_container_width=True)
            
            st.markdown("#### 🏆 Top 3 Iniciativas Recomendadas")
            
            # Top 3 iniciativas con diseño mejorado
            top_3 = df_filtered.nlargest(3, 'Puntuacion_Ponderada')
            
            for i, (_, row) in enumerate(top_3.iterrows(), 1):
                priority_class = f"priority-{row['Prioridad'].lower()}"
                
                # Calcular fortalezas
                metrics = {
                    'Valor_Estrategico': 'Valor Estratégico',
                    'Nivel_Impacto': 'Nivel de Impacto',
                    'Viabilidad_Tecnica': 'Viabilidad Técnica',
                    'Costo_Beneficio': 'Costo-Beneficio',
                    'Innovacion_Disrupcion': 'Innovación',
                    'Escalabilidad_Transversalidad': 'Escalabilidad',
                    'Tiempo_Implementacion': 'Tiempo de Implementación'
                }
                
                fortalezas = []
                for metric_key, metric_name in metrics.items():
                    if row[metric_key] >= 4:
                        fortalezas.append(f"{metric_name} ({row[metric_key]}/5)")
                
                fortalezas_text = ", ".join(fortalezas) if fortalezas else "Perfil equilibrado"
                
                st.markdown(f"""
<div class="metric-card {priority_class}">
    <h4>🏆 #{i} {row['Nombre_Iniciativa']}</h4>
    <p><strong>👤 Propuesto por:</strong> {row['Nombre_Colaborador']} ({row['Area']})</p>
    <p><strong>⭐ Puntuación:</strong> {row['Puntuacion_Ponderada']:.2f}/5.0 | 
       <strong>🎯 Prioridad:</strong> {row['Prioridad']}</p>
    <p><strong>💪 Fortalezas:</strong> {fortalezas_text}</p>
    <p><strong>📝 Problema:</strong> {row.get('Problema', 'No especificado')[:120]}{'...' if len(str(row.get('Problema', ''))) > 120 else ''}</p>
</div>
                """, unsafe_allow_html=True)
            
            # Recomendaciones estratégicas
            st.markdown("#### 💡 Recomendaciones Estratégicas")
            
            recommendations = []
            
            if high_priority > 0:
                recommendations.append(f"**🚀 Implementación inmediata:** Priorizar las {high_priority} iniciativas de alta puntuación para obtener resultados rápidos y visibles.")
            
            if medium_priority > 0:
                recommendations.append(f"**🔍 Análisis detallado:** Las {medium_priority} iniciativas de prioridad media requieren evaluación adicional de recursos y timeline.")
            
            # Análisis de viabilidad
            low_viability = len(df_filtered[df_filtered['Viabilidad_Tecnica'] < 3])
            if low_viability > 0:
                recommendations.append(f"**📚 Desarrollo de capacidades:** {low_viability} iniciativas presentan desafíos de viabilidad técnica que requieren fortalecimiento de capacidades.")
            
            # Oportunidades de escalabilidad
            high_scalability = len(df_filtered[df_filtered['Escalabilidad_Transversalidad'] >= 4])
            if high_scalability > 0:
                recommendations.append(f"**🔄 Potencial de escalabilidad:** {high_scalability} iniciativas muestran alto potencial de replicación en otras áreas.")
            
            recommendations.append(f"**👏 Reconocimiento:** El área de '{top_area}' muestra el mayor nivel de participación en el proceso de innovación.")
            
            for rec in recommendations:
                st.markdown(f"• {rec}")
            
            # Próximos pasos
            st.markdown("#### 📋 Próximos Pasos Sugeridos")
            
            next_steps = [
                "Convocar comité de evaluación para revisar iniciativas de alta prioridad",
                "Asignar recursos y equipos para las 3 mejores iniciativas",
                "Establecer cronograma de implementación con hitos específicos",
                "Definir métricas de éxito y sistema de seguimiento",
                "Comunicar resultados a los colaboradores participantes",
                "Planificar siguiente ciclo de recolección de iniciativas"
            ]
            
            for i, step in enumerate(next_steps, 1):
                st.markdown(f"**{i}.** {step}")
            
            # Información adicional sobre el reporte PDF
            st.markdown("---")
            st.info("""
            💡 **Sobre el Reporte PDF:**
            - Incluye todas las métricas y análisis mostrados arriba
            - Formato profesional optimizado para presentaciones ejecutivas
            - Contiene gráficos y tablas de fácil lectura
            - Ideal para compartir con la dirección y stakeholders
            """)
         %Y')}
            
            #### Métricas Clave:
            - **Total de iniciativas evaluadas:** {total_initiatives}
            - **Iniciativas de alta prioridad:** {high_priority} ({high_priority/total_initiatives*100:.1f}% del total)
            - **Puntuación promedio:** {avg_score:.2f}/5.0
            - **Área más activa:** {top_area}
            
            #### Top 3 Iniciativas Recomendadas:
            """)
            
            # Top 3 iniciativas
            top_3 = df_filtered.nlargest(3, 'Puntuacion_Ponderada')
            
            for i, (_, row) in enumerate(top_3.iterrows(), 1):
                st.markdown(f"""
                **{i}. {row['Nombre_Iniciativa']}**
                - Propuesta por: {row['Nombre_Colaborador']} ({row['Area']})
                - Puntuación: {row['Puntuacion_Ponderada']:.2f}/5.0
                - Fortalezas: Valor estratégico ({row['Valor_Estrategico']}/5), Impacto ({row['Nivel_Impacto']}/5)
                """)
            
            # Recomendaciones
            st.markdown("""
            #### 💡 Recomendaciones:
            
            1. **Implementación inmediata:** Priorizar las iniciativas de alta puntuación que requieren recursos mínimos
            2. **Análisis detallado:** Revisar iniciativas con alto potencial pero baja viabilidad técnica
            3. **Fomento de la participación:** Incentivar la participación de áreas con menor actividad
            4. **Seguimiento:** Establecer métricas de seguimiento para las iniciativas implementadas
            """)
            
            # Botón para descargar reporte
            if st.button("📥 Descargar Datos para Análisis"):
                csv = df_filtered.to_csv(index=False)
                st.download_button(
                    label="⬇️ Descargar CSV",
                    data=csv,
                    file_name=f"iniciativas_innovacion_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    else:
        st.warning("No se encontraron datos válidos en el archivo.")
        st.info("Verifica que el archivo contenga las columnas necesarias y datos válidos.")

else:
    st.info("👆 Selecciona una fuente de datos en la barra lateral para comenzar el análisis.")
    
    # Información sobre el sistema
    st.markdown("""
    ## 💡 Acerca de este sistema
    
    Esta aplicación analiza automáticamente las iniciativas de innovación propuestas por los colaboradores, 
    utilizando las puntuaciones generadas por IA en Zapier.
    
    ### Características principales:
    - ✅ Carga automática desde Google Sheets
    - 📊 Visualizaciones interactivas 
    - 🎯 Sistema de priorización ponderado
    - 🏆 Rankings y comparaciones
    - 📋 Reportes ejecutivos
    - 🔍 Análisis detallado por iniciativa
    
    ### Criterios de evaluación (escala 0-5):
    - **Valor estratégico:** Contribución a objetivos estratégicos
    - **Nivel de impacto:** Valor o transformación esperada
    - **Viabilidad técnica:** Posibilidad de implementación
    - **Costo-beneficio:** Justificación del esfuerzo/costo
    - **Innovación/disrupción:** Novedad de la propuesta
    - **Escalabilidad/transversalidad:** Potencial de replicación
    - **Tiempo de implementación:** Velocidad de puesta en marcha
    """)

# Footer
st.markdown("---")
st.markdown("🚀 **Sistema de Análisis de Iniciativas de Innovación** | Desarrollado para el equipo de Innovación")
