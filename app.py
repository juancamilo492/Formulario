# -*- coding: utf-8 -*-
"""
Analizador de Iniciativas de Innovación
Sistema de Análisis y Priorización de Propuestas
Desarrollado para el equipo de Innovación
"""

# ==========================================
# IMPORTACIONES
# ==========================================
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
import bcrypt  # Added for password hashing

# Importaciones para PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para evitar problemas en servidores sin display

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Analizador de Iniciativas de Innovación",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CSS PERSONALIZADO
# ==========================================
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
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 4px solid #2d5aa0;
        margin: 0.8rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card h4 {
        margin-bottom: 0.8rem;
        color: #1f4e79;
    }
    .metric-card p {
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }
    .priority-alta {
        border-left-color: #28a745 !important;
        background: #d4edda !important;
    }
    .priority-media {
        border-left-color: #ffc107 !important;
        background: #fff3cd !important;
    }
    .priority-baja {
        border-left-color: #dc3545 !important;
        background: #f8d7da !important;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .login-header {
        text-align: center;
        color: #1f4e79;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def fix_encoding(text):
    """Corrige problemas de encoding UTF-8"""
    if pd.isna(text) or text == "":
        return text
    
    text = str(text)
    
    # Diccionario de reemplazos para caracteres mal codificados
    replacements = {
        'Ã¡': 'á',
        'Ã©': 'é',
        'Ã­': 'í',
        'Ã³': 'ó',
        'Ãº': 'ú',
        'Ã±': 'ñ',
        'ÃÁ': 'Á',
        'ÃÉ': 'É',
        'ÃÍ': 'Í',
        'ÃÓ': 'Ó',
        'ÃÚ': 'Ú',
        'ÃÑ': 'Ñ',
        'Â¿': '¿',
        'Â¡': '¡',
        'Â°': '°',
        'âœ…': '✅',
        'â€œ': '"',
        'â€': '"',
        'â€"': '–',
        'â€"': '—'
    }
    
    # Aplicar reemplazos
    for bad_char, good_char in replacements.items():
        text = text.replace(bad_char, good_char)
    
    return text

# ==========================================
# FUNCIONES DE CARGA DE DATOS
# ==========================================

@st.cache_data
def load_data_from_url():
    """Carga los datos desde Google Sheets"""
    try:
        sheet_id = "1yWHTveQlQEKi7fLdDxxKPLdEjGvD7PaTzAbRYvSBEp0"
        
        urls_to_try = [
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0",
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv",
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        ]
        
        for url in urls_to_try:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                # Intentar diferentes encodings para manejar caracteres especiales
                try:
                    df = pd.read_csv(StringIO(response.text), encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(StringIO(response.content.decode('latin-1')))
                    except:
                        df = pd.read_csv(StringIO(response.text))
                
                if len(df) > 0:
                    st.success(f"✅ Datos cargados exitosamente desde Google Sheets ({len(df)} registros)")
                    return df
                    
            except Exception as e:
                continue
                
        # Si ninguna URL funciona
        st.error("❌ No se pudieron cargar los datos desde Google Sheets.")
        st.warning("🔧 **Para solucionar este problema:**")
        st.markdown("""
        1. **Hacer el Google Sheets público:**
           - Abrir el Google Sheets
           - Clic en "Compartir" (esquina superior derecha)
           - Clic en "Cambiar a cualquier persona con el enlace"
           - Seleccionar "Visualizador"
           - Guardar
        
        2. **Verificar el ID del sheet en la URL**
        3. **Como alternativa, subir el archivo manualmente**
        """)
        return None
        
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
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

# ==========================================
# FUNCIÓN PARA PROCESAR FECHAS
# ==========================================

def process_dates(df):
    """Procesa las fechas del DataFrame"""
    if df is None:
        return df
    
    # Buscar columna de fecha/marca temporal
    date_columns = ['Fecha', 'Marca temporal', 'Timestamp', 'Date', 'fecha', 'marca_temporal']
    date_col = None
    
    for col in df.columns:
        col_clean = str(col).strip().lower()
        if any(date_term in col_clean for date_term in ['marca temporal', 'timestamp', 'fecha', 'date']):
            date_col = col
            break
    
    if date_col is not None:
        try:
            # Intentar convertir a datetime
            df['Fecha_Procesada'] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Si hay fechas válidas, crear columnas adicionales
            if df['Fecha_Procesada'].notna().any():
                df['Fecha_Solo'] = df['Fecha_Procesada'].dt.date
                df['Semana'] = df['Fecha_Procesada'].dt.to_period('W').astype(str)
                df['Mes'] = df['Fecha_Procesada'].dt.to_period('M').astype(str)
                df['Dia_Semana'] = df['Fecha_Procesada'].dt.day_name()
                df['Hora'] = df['Fecha_Procesada'].dt.hour
                
                return df
            else:
                st.warning("No se pudieron procesar las fechas correctamente")
                return df
        except Exception as e:
            st.warning(f"Error al procesar fechas: {str(e)}")
            return df
    else:
        st.warning("No se encontró columna de fecha en los datos")
        return df

# ==========================================
# FUNCIÓN DE PROCESAMIENTO DE DATOS
# ==========================================

def clean_and_process_data(df):
    """Limpia y procesa los datos"""
    if df is None:
        return None
    
    # Crear una copia para trabajar
    df_clean = df.copy()
    
    # Limpiar nombres de columnas
    df_clean.columns = [col.strip().rstrip() for col in df_clean.columns]
    
    # Mapeo inteligente de columnas que maneja encoding issues
    column_mapping = {}
    
    for col in df_clean.columns:
        col_clean = col.strip()
        
        # Mapeo basado en contenido clave de las columnas
        if 'Marca temporal' in col_clean:
            column_mapping[col] = 'Fecha'
        elif 'Nombre completo' in col_clean:
            column_mapping[col] = 'Nombre_Colaborador'
        elif 'Correo electr' in col_clean:  # Maneja "Correo electrÃ³nico"
            column_mapping[col] = 'Correo'
        elif 'Rol o relaci' in col_clean:  # Maneja "Rol o relaciÃ³n con Alico"
            column_mapping[col] = 'Rol'
        elif 'rea o proceso' in col_clean:  # Maneja "Selecciona el Ã¡rea o proceso"
            column_mapping[col] = 'Area'
        elif 'Nombre de la idea' in col_clean:
            column_mapping[col] = 'Nombre_Iniciativa'
        elif 'problema, necesidad' in col_clean:
            column_mapping[col] = 'Problema'
        elif 'Cu' in col_clean and 'l es tu propuesta' in col_clean:  # Maneja "Â¿CuÃ¡l es tu propuesta?"
            column_mapping[col] = 'Propuesta'
        elif 'proceso/s crees' in col_clean:
            column_mapping[col] = 'Proceso_Relacionado'
        elif 'beneficios esperas' in col_clean:
            column_mapping[col] = 'Beneficios'
        elif 'idea la has visto' in col_clean:
            column_mapping[col] = 'Vista_Otro_Lugar'
        elif 'respuesta anterior' in col_clean:
            column_mapping[col] = 'Donde_Como'
        elif 'puede implementarse' in col_clean:
            column_mapping[col] = 'Recursos_Actuales'
        # Campos numéricos con encoding issues
        elif 'Valor estrat' in col_clean:  # Maneja "Valor estratÃ©gico"
            column_mapping[col] = 'Valor_Estrategico'
        elif 'Nivel de impacto' in col_clean:
            column_mapping[col] = 'Nivel_Impacto'
        elif 'Viabilidad t' in col_clean:  # Maneja "Viabilidad tÃ©cnica"
            column_mapping[col] = 'Viabilidad_Tecnica'
        elif 'Costo-beneficio' in col_clean:
            column_mapping[col] = 'Costo_Beneficio'
        elif 'Innovaci' in col_clean and 'disrupci' in col_clean:  # Maneja "InnovaciÃ³n / disrupciÃ³n"
            column_mapping[col] = 'Innovacion_Disrupcion'
        elif 'Escalabilidad' in col_clean and 'transversalidad' in col_clean:
            column_mapping[col] = 'Escalabilidad_Transversalidad'
        elif 'Tiempo de implementaci' in col_clean:  # Maneja "Tiempo de implementaciÃ³n"
            column_mapping[col] = 'Tiempo_Implementacion'
    
    # Aplicar mapeo de columnas
    df_clean = df_clean.rename(columns=column_mapping)
    
    # Verificar columnas necesarias
    numeric_columns = ['Valor_Estrategico', 'Nivel_Impacto', 'Viabilidad_Tecnica', 
                      'Costo_Beneficio', 'Innovacion_Disrupcion', 
                      'Escalabilidad_Transversalidad', 'Tiempo_Implementacion']
    
    required_columns = ['Nombre_Colaborador', 'Nombre_Iniciativa', 'Area'] + numeric_columns
    
    missing_columns = [col for col in required_columns if col not in df_clean.columns]
    
    if missing_columns:
        st.error(f"❌ Columnas faltantes: {missing_columns}")
        return None
    
    # Corregir encoding en columnas de texto
    text_columns = ['Nombre_Colaborador', 'Area', 'Nombre_Iniciativa', 'Problema', 'Propuesta', 'Beneficios', 'Proceso_Relacionado']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(fix_encoding)
    
    # Filtrar registros válidos
    valid_mask = (
        df_clean['Nombre_Colaborador'].notna() & 
        df_clean['Nombre_Iniciativa'].notna() &
        (df_clean['Nombre_Colaborador'].astype(str).str.strip() != '') &
        (df_clean['Nombre_Iniciativa'].astype(str).str.strip() != '')
    )
    df_clean = df_clean[valid_mask].copy()
    
    # Convertir campos numéricos
    for field in numeric_columns:
        if field in df_clean.columns:
            df_clean[field] = pd.to_numeric(df_clean[field], errors='coerce').fillna(0)
    
    # Calcular métricas derivadas
    df_clean['Puntuacion_Total'] = (
        df_clean['Valor_Estrategico'] + df_clean['Nivel_Impacto'] + 
        df_clean['Viabilidad_Tecnica'] + df_clean['Costo_Beneficio'] + 
        df_clean['Innovacion_Disrupcion'] + df_clean['Escalabilidad_Transversalidad'] + 
        df_clean['Tiempo_Implementacion']
    )
    
    # Calcular puntuación ponderada (criterio de priorización inteligente)
    df_clean['Puntuacion_Ponderada'] = (
        df_clean['Valor_Estrategico'] * 0.20 +      # 20% Valor estratégico
        df_clean['Nivel_Impacto'] * 0.20 +          # 20% Nivel de impacto
        df_clean['Viabilidad_Tecnica'] * 0.15 +     # 15% Viabilidad técnica
        df_clean['Costo_Beneficio'] * 0.15 +        # 15% Costo-beneficio
        df_clean['Innovacion_Disrupcion'] * 0.10 +  # 10% Innovación
        df_clean['Escalabilidad_Transversalidad'] * 0.10 + # 10% Escalabilidad
        df_clean['Tiempo_Implementacion'] * 0.10    # 10% Tiempo (más rápido = mejor)
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
    
    # Calcular facilidad de implementación
    df_clean['Facilidad_Implementacion'] = (
        (df_clean['Viabilidad_Tecnica'] + df_clean['Costo_Beneficio'] + 
         df_clean['Tiempo_Implementacion']) / 3
    )
    
    return df_clean

# ==========================================
# FUNCIÓN PARA GENERAR PDF
# ==========================================

def generate_pdf_report(df_filtered):
    """Genera un reporte ejecutivo en PDF profesional"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=18)
    
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
    
    # Tabla de resumen
    summary_data = [
        ['Métrica', 'Valor', 'Observaciones'],
        ['Total de iniciativas', str(total_initiatives), 'Propuestas recibidas'],
        ['Alta prioridad', f"{high_priority} ({high_priority/total_initiatives*100:.1f}%)", 'Para implementación inmediata'],
        ['Prioridad media', f"{medium_priority} ({medium_priority/total_initiatives*100:.1f}%)", 'Requieren análisis adicional'],
        ['Prioridad baja', f"{low_priority} ({low_priority/total_initiatives*100:.1f}%)", 'Para revisión a largo plazo'],
        ['Puntuación promedio', f"{avg_score:.2f}/5.0", 'Calidad general de propuestas'],
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
        nombre_iniciativa = fix_encoding(row['Nombre_Iniciativa'])
        nombre_colaborador = fix_encoding(row['Nombre_Colaborador'])
        area = fix_encoding(row['Area'])
        problema = fix_encoding(str(row.get('Problema', 'No especificado')))
        propuesta = fix_encoding(str(row.get('Propuesta', 'No especificada')))
        
        elements.append(Paragraph(f"<b>{i}. {nombre_iniciativa}</b>", normal_style))
        elements.append(Paragraph(f"<b>Propuesto por:</b> {nombre_colaborador} ({area})", normal_style))
        elements.append(Paragraph(f"<b>Puntuación:</b> {row['Puntuacion_Ponderada']:.2f}/5.0", normal_style))
        elements.append(Paragraph(f"<b>Problema que resuelve:</b> {problema[:150]}...", normal_style))
        elements.append(Paragraph(f"<b>Propuesta:</b> {propuesta[:150]}...", normal_style))
        elements.append(Spacer(1, 10))
    
    # Recomendaciones
    elements.append(Paragraph("RECOMENDACIONES ESTRATÉGICAS", heading_style))
    
    recomendaciones = [
        f"Priorizar las {high_priority} iniciativas de alta puntuación",
        f"Realizar análisis detallado de las {medium_priority} iniciativas de prioridad media",
        "Establecer cronograma de implementación con hitos específicos",
        "Definir métricas de seguimiento para iniciativas implementadas"
    ]
    
    for rec in recomendaciones:
        elements.append(Paragraph(f"• {rec}", normal_style))
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================
# FUNCIONES DE LOGIN MEJORADAS
# ==========================================

def check_credentials(username, password):
    """Verifica las credenciales del usuario contra st.secrets usando bcrypt"""
    try:
        users = st.secrets["users"]
        for user_key in users:
            user_data = users[user_key]
            if user_data["username"] == username:
                # Verificar contraseña hasheada
                stored_hashed_password = user_data["password"].encode('utf-8')
                return bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password)
        return False
    except Exception as e:
        st.error(f"Error al verificar credenciales: {str(e)}")
        return False

def check_session():
    """Verifica si la sesión está activa"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if "session_time" not in st.session_state:
        st.session_state["session_time"] = datetime.now()
    
    # Opcional: Expirar sesión después de X horas (descomenta si quieres tiempo límite)
    # session_duration = datetime.now() - st.session_state["session_time"]
    # if session_duration.total_seconds() > 28800:  # 8 horas
    #     st.session_state["authenticated"] = False
    #     st.warning("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")

def login_page():
    """Muestra la página de login"""
    st.markdown("""
    <div class="login-container">
        <h2 class="login-header">Iniciar Sesión</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form(key="login_form"):
        username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
        remember_session = st.checkbox("Mantener sesión iniciada", value=True)
        submit_button = st.form_submit_button("Iniciar Sesión")
        
        if submit_button:
            if check_credentials(username, password):
                st.session_state["authenticated"] = True
                st.session_state["session_time"] = datetime.now()
                st.session_state["username"] = username
                st.session_state["remember_session"] = remember_session
                st.success("✅ Inicio de sesión exitoso")
                st.rerun()  # Refresca la página para mostrar el contenido principal
            else:
                st.error("❌ Usuario o contraseña incorrectos")

# ==========================================
# NUEVAS FUNCIONES PARA GRÁFICOS DE FECHAS
# ==========================================

def create_timeline_charts(df):
    """Crea gráficos de línea de tiempo de iniciativas"""
    if 'Fecha_Procesada' not in df.columns or df['Fecha_Procesada'].isna().all():
        st.warning("No hay datos de fecha disponibles para mostrar la línea de tiempo")
        return
    
    # Filtrar solo registros con fecha válida
    df_with_dates = df[df['Fecha_Procesada'].notna()].copy()
    
    if len(df_with_dates) == 0:
        st.warning("No hay registros con fechas válidas")
        return
    
    # Crear diferentes visualizaciones temporales
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico por día
        daily_counts = df_with_dates.groupby('Fecha_Solo').size().reset_index()
        daily_counts.columns = ['Fecha', 'Cantidad']
        daily_counts['Fecha'] = pd.to_datetime(daily_counts['Fecha'])
        
        fig_daily = px.line(
            daily_counts,
            x='Fecha',
            y='Cantidad',
            title="📅 Iniciativas Recibidas por Día",
            markers=True,
            line_shape='spline'
        )
        
        fig_daily.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Número de Iniciativas",
            hovermode='x unified'
        )
        
        fig_daily.update_traces(
            line=dict(color='#2d5aa0', width=3),
            marker=dict(size=8, color='#1f4e79')
        )
        
        st.plotly_chart(fig_daily, use_container_width=True)
    
    with col2:
        # Gráfico acumulativo
        daily_counts_sorted = daily_counts.sort_values('Fecha')
        daily_counts_sorted['Acumulado'] = daily_counts_sorted['Cantidad'].cumsum()
        
        fig_cumulative = px.area(
            daily_counts_sorted,
            x='Fecha',
            y='Acumulado',
            title="📈 Iniciativas Acumuladas",
            line_shape='spline'
        )
        
        fig_cumulative.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Total Acumulado",
            hovermode='x unified'
        )
        
        fig_cumulative.update_traces(
            fill='tonexty',
            fillcolor='rgba(45, 90, 160, 0.3)',
            line=dict(color='#2d5aa0', width=2)
        )
        
        st.plotly_chart(fig_cumulative, use_container_width=True)
    
    # Gráfico por semana
    weekly_counts = df_with_dates.groupby('Semana').size().reset_index()
    weekly_counts.columns = ['Semana', 'Cantidad']
    
    fig_weekly = px.bar(
        weekly_counts,
        x='Semana',
        y='Cantidad',
        title="📊 Iniciativas por Semana",
        color='Cantidad',
        color_continuous_scale='Blues'
    )
    
    fig_weekly.update_layout(
        xaxis_title="Semana",
        yaxis_title="Número de Iniciativas",
        xaxis_tickangle=45
    )
    
    st.plotly_chart(fig_weekly, use_container_width=True)
    
    # Análisis por día de la semana y hora
    col3, col4 = st.columns(2)
    
    with col3:
        # Distribución por día de la semana
        weekday_counts = df_with_dates['Dia_Semana'].value_counts()
        
        # Ordenar días de la semana
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_names_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        weekday_ordered = []
        labels_ordered = []
        for i, day in enumerate(day_order):
            if day in weekday_counts.index:
                weekday_ordered.append(weekday_counts[day])
                labels_ordered.append(day_names_es[i])
            else:
                weekday_ordered.append(0)
                labels_ordered.append(day_names_es[i])
        
        fig_weekday = px.bar(
            x=labels_ordered,
            y=weekday_ordered,
            title="📅 Distribución por Día de la Semana",
            color=weekday_ordered,
            color_continuous_scale='Viridis'
        )
        
        fig_weekday.update_layout(
            xaxis_title="Día de la Semana",
            yaxis_title="Número de Iniciativas",
            showlegend=False
        )
        
        st.plotly_chart(fig_weekday, use_container_width=True)
    
    with col4:
        # Distribución por hora del día
        hour_counts = df_with_dates['Hora'].value_counts().sort_index()
        
        fig_hour = px.bar(
            x=hour_counts.index,
            y=hour_counts.values,
            title="🕐 Distribución por Hora del Día",
            color=hour_counts.values,
            color_continuous_scale='Sunset'
        )
        
        fig_hour.update_layout(
            xaxis_title="Hora del Día",
            yaxis_title="Número de Iniciativas",
            showlegend=False,
            xaxis=dict(tickmode='linear', tick0=0, dtick=2)
        )
        
        st.plotly_chart(fig_hour, use_container_width=True)
    
    # Estadísticas temporales
    st.subheader("📊 Estadísticas Temporales")
    
    # Calcular estadísticas
    first_date = df_with_dates['Fecha_Procesada'].min()
    last_date = df_with_dates['Fecha_Procesada'].max()
    days_active = (last_date - first_date).days + 1
    avg_per_day = len(df_with_dates) / days_active if days_active > 0 else 0
    
    # Período más activo
    most_active_day = daily_counts.loc[daily_counts['Cantidad'].idxmax()]
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.metric(
            "📅 Primer registro",
            first_date.strftime('%d/%m/%Y')
        )
    
    with col_stat2:
        st.metric(
            "📅 Último registro",
            last_date.strftime('%d/%m/%Y')
        )
    
    with col_stat3:
        st.metric(
            "⏱️ Promedio por día",
            f"{avg_per_day:.1f}"
        )
    
    with col_stat4:
        st.metric(
            "🔥 Día más activo",
            most_active_day['Fecha'].strftime('%d/%m/%Y'),
            delta=f"{int(most_active_day['Cantidad'])} iniciativas"
        )

# ==========================================
# FUNCIÓN PRINCIPAL DE LA APLICACIÓN
# ==========================================

def main():
    """Función principal de la aplicación"""
    
    # Verificar sesión
    check_session()
    
    if not st.session_state["authenticated"]:
        login_page()
        return
    
    # Header principal con información de usuario
    username = st.session_state.get("username", "Usuario")
    st.markdown(f'''
    <div class="main-header">
        <h1>💡 Analizador de Iniciativas de Innovación</h1>
        <p>Sistema de Análisis y Priorización de Propuestas</p>
        <p style="font-size: 0.9em; opacity: 0.8;">Bienvenido, {username}</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Botón de cerrar sesión en la sidebar
    st.sidebar.markdown(f"👤 **Usuario:** {username}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        # Limpiar todas las variables de sesión relacionadas con autenticación
        st.session_state["authenticated"] = False
        if "session_time" in st.session_state:
            del st.session_state["session_time"]
        if "username" in st.session_state:
            del st.session_state["username"]
        if "remember_session" in st.session_state:
            del st.session_state["remember_session"]
        st.success("Sesión cerrada exitosamente")
        st.rerun()
    
    # ==========================================
    # SIDEBAR - CONFIGURACIÓN
    # ==========================================
    
    st.sidebar.header("⚙️ Configuración")
    
    # Opción para cargar datos
    data_source = st.sidebar.radio(
        "Fuente de datos:",
        ["Google Sheets (Automático)", "Subir archivo"]
    )
    
    # Cargar datos
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
    
    # ==========================================
    # PROCESAMIENTO DE DATOS
    # ==========================================
    
    if df is not None:
        # Procesar fechas ANTES de limpiar los datos
        df = process_dates(df)
        df_processed = clean_and_process_data(df)
        
        if df_processed is not None and len(df_processed) > 0:
            
            # ==========================================
            # FILTROS SIDEBAR
            # ==========================================
            
            st.sidebar.subheader("🔍 Filtros")
            
            # Filtro por área (multi-selección)
            areas_disponibles = sorted(df_processed['Area'].dropna().unique().tolist())
            areas_selected = st.sidebar.multiselect("Áreas:", areas_disponibles, default=areas_disponibles)
            
            # Filtro por prioridad (multi-selección)
            prioridades_disponibles = sorted(df_processed['Prioridad'].dropna().unique().tolist())
            prioridades_selected = st.sidebar.multiselect("Prioridades:", prioridades_disponibles, default=prioridades_disponibles)
            
            # Filtro por proceso
            if 'Proceso_Relacionado' in df_processed.columns:
                # Obtener todos los procesos únicos, manejando valores separados por comas
                all_processes = []
                for proc in df_processed['Proceso_Relacionado'].dropna():
                    if isinstance(proc, str):
                        # Separar por comas y limpiar espacios
                        processes = [p.strip() for p in proc.split(',')]
                        all_processes.extend(processes)
                
                unique_processes = sorted(list(set(all_processes)))
                procesos_selected = st.sidebar.multiselect("Procesos relacionados:", unique_processes, default=unique_processes)
            else:
                procesos_selected = []
            
            # Aplicar filtros
            df_filtered = df_processed.copy()
            if areas_selected:
                df_filtered = df_filtered[df_filtered['Area'].isin(areas_selected)]
            if prioridades_selected:
                df_filtered = df_filtered[df_filtered['Prioridad'].isin(prioridades_selected)]
            if procesos_selected and 'Proceso_Relacionado' in df_filtered.columns:
                df_filtered = df_filtered[
                    df_filtered['Proceso_Relacionado'].apply(
                        lambda x: any(proc.lower() in str(x).lower() for proc in procesos_selected)
                    )
                ]
            
            # ==========================================
            # MÉTRICAS PRINCIPALES
            # ==========================================
            
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
            
            # ==========================================
            # PESTAÑAS PRINCIPALES
            # ==========================================
            
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📈 Análisis General", 
                "🏆 Ranking de Iniciativas", 
                "📊 Análisis por Área",
                "🔍 Detalle de Iniciativas",
                "⚙️ Análisis por Proceso", 
                "📅 Línea de Tiempo",  # NUEVA PESTAÑA
                "📋 Reporte Ejecutivo"
            ])
            
            # ==========================================
            # TAB 1: ANÁLISIS GENERAL
            # ==========================================
            
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
                            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
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
            
            # ==========================================
            # TAB 2: RANKING DE INICIATIVAS
            # ==========================================
            
            with tab2:
                st.subheader("🏆 Ranking de Iniciativas")
                
                # Top iniciativas
                df_ranked = df_filtered.sort_values('Puntuacion_Ponderada', ascending=False).reset_index(drop=True)
                
                for idx, row in df_ranked.head(10).iterrows():
                    priority_class = f"priority-{row['Prioridad'].lower()}"
                    
                    # Aplicar corrección de encoding
                    nombre_iniciativa = fix_encoding(row['Nombre_Iniciativa'])
                    nombre_colaborador = fix_encoding(row['Nombre_Colaborador'])
                    area = fix_encoding(row['Area'])
                    problema = fix_encoding(str(row.get('Problema', 'No especificado')))
                    propuesta = fix_encoding(str(row.get('Propuesta', 'No especificada')))
                    
                    st.markdown(f"""
                    <div class="metric-card {priority_class}">
                        <h4>#{idx+1} {nombre_iniciativa}</h4>
                        <p><strong>👤 Propuesto por:</strong> {nombre_colaborador} ({area})</p>
                        <p><strong>⭐ Puntuación:</strong> {row['Puntuacion_Ponderada']:.2f}/5.0 | 
                           <strong>🎯 Prioridad:</strong> {row['Prioridad']}</p>
                        <p><strong>🔍 Problema que resuelve:</strong> {problema[:100]}{'...' if len(problema) > 100 else ''}</p>
                        <p><strong>💡 Propuesta:</strong> {propuesta[:120]}{'...' if len(propuesta) > 120 else ''}</p>
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
                    
                    # Líneas de referencia
                    fig_scatter.add_hline(y=2.5, line_dash="dash", line_color="gray")
                    fig_scatter.add_vline(x=2.5, line_dash="dash", line_color="gray")
                    
                    st.plotly_chart(fig_scatter, use_container_width=True)
            
            # ==========================================
            # TAB 3: ANÁLISIS POR ÁREA
            # ==========================================
            
            with tab3:
                st.subheader("📊 Análisis por Área")
                
                # Análisis por área
                area_analysis = df_filtered.groupby('Area').agg({
                    'Puntuacion_Ponderada': ['count', 'mean'],
                    'Valor_Estrategico': 'mean',
                    'Nivel_Impacto': 'mean',
                    'Viabilidad_Tecnica': 'mean',
                    'Costo_Beneficio': 'mean',
                    'Innovacion_Disrupcion': 'mean',
                    'Escalabilidad_Transversalidad': 'mean',
                    'Tiempo_Implementacion': 'mean'
                }).round(2)
                
                area_analysis.columns = ['Num_Iniciativas', 'Puntuacion_Promedio',
                                       'Val_Estrategico', 'Impacto', 'Viabilidad', 'Costo_Beneficio',
                                       'Innovacion', 'Escalabilidad', 'Tiempo_Impl']
                
                # Gráficos por área
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_bar = px.bar(
                        x=area_analysis.index,
                        y=area_analysis['Num_Iniciativas'],
                        title="Número de Iniciativas por Área"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    fig_bar2 = px.bar(
                        x=area_analysis.index,
                        y=area_analysis['Puntuacion_Promedio'],
                        title="Puntuación Promedio por Área"
                    )
                    st.plotly_chart(fig_bar2, use_container_width=True)
                
                # Tabla resumen
                st.subheader("📋 Resumen por Área")
                st.dataframe(area_analysis, use_container_width=True)
            
            # ==========================================
            # TAB 4: DETALLE DE INICIATIVAS
            # ==========================================
            
            with tab4:
                st.subheader("🔍 Detalle de Iniciativas")
                
                iniciativas_list = df_filtered['Nombre_Iniciativa'].tolist()
                
                if iniciativas_list:
                    selected_initiative = st.selectbox(
                        "Selecciona una iniciativa para ver detalles:",
                        iniciativas_list
                    )
                    
                    # Mostrar detalles
                    init_data = df_filtered[df_filtered['Nombre_Iniciativa'] == selected_initiative].iloc[0]
                    
                    # Aplicar corrección de encoding
                    nombre_iniciativa = fix_encoding(init_data['Nombre_Iniciativa'])
                    nombre_colaborador = fix_encoding(init_data['Nombre_Colaborador'])
                    area = fix_encoding(init_data['Area'])
                    problema = fix_encoding(str(init_data.get('Problema', 'No especificado')))
                    propuesta = fix_encoding(str(init_data.get('Propuesta', 'No especificada')))
                    beneficios = fix_encoding(str(init_data.get('Beneficios', 'No especificados')))
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"""
                        ### {nombre_iniciativa}
                        
                        **👤 Propuesta por:** {nombre_colaborador}  
                        **🏢 Área:** {area}  
                        **⭐ Puntuación Ponderada:** {init_data['Puntuacion_Ponderada']:.2f}/5.0  
                        **🎯 Prioridad:** {init_data['Prioridad']}
                        
                        **📝 Problema que resuelve:**
                        {problema}
                        
                        **💡 Propuesta:**
                        {propuesta}
                        
                        **✅ Beneficios esperados:**
                        {beneficios}
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
            
            # ==========================================
            # TAB 5: ANÁLISIS POR PROCESO
            # ==========================================
            
            with tab5:
                st.subheader("⚙️ Análisis por Proceso")
                
                if 'Proceso_Relacionado' in df_filtered.columns:
                    # Crear un DataFrame expandido para análisis por proceso
                    process_data = []
                    for _, row in df_filtered.iterrows():
                        if pd.notna(row['Proceso_Relacionado']) and row['Proceso_Relacionado'] != '':
                            processes = [p.strip() for p in str(row['Proceso_Relacionado']).split(',')]
                            for process in processes:
                                if process:  # Solo si el proceso no está vacío
                                    new_row = row.copy()
                                    new_row['Proceso_Individual'] = process
                                    process_data.append(new_row)
                    
                    if process_data:
                        df_process_expanded = pd.DataFrame(process_data)
                        
                        # Análisis por proceso
                        process_analysis = df_process_expanded.groupby('Proceso_Individual').agg({
                            'Puntuacion_Ponderada': ['count', 'mean'],
                            'Valor_Estrategico': 'mean',
                            'Nivel_Impacto': 'mean',
                            'Viabilidad_Tecnica': 'mean',
                            'Costo_Beneficio': 'mean',
                            'Innovacion_Disrupcion': 'mean',
                            'Escalabilidad_Transversalidad': 'mean',
                            'Tiempo_Implementacion': 'mean'
                        }).round(2)
                        
                        process_analysis.columns = ['Num_Iniciativas', 'Puntuacion_Promedio',
                                                   'Val_Estrategico', 'Impacto', 'Viabilidad', 'Costo_Beneficio',
                                                   'Innovacion', 'Escalabilidad', 'Tiempo_Impl']
                        
                        # Ordenar por número de iniciativas
                        process_analysis = process_analysis.sort_values('Num_Iniciativas', ascending=False)
                        
                        # Gráficos por proceso
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_bar_proc = px.bar(
                                x=process_analysis.index,
                                y=process_analysis['Num_Iniciativas'],
                                title="Número de Iniciativas por Proceso",
                                labels={'x': 'Proceso', 'y': 'Número de Iniciativas'}
                            )
                            fig_bar_proc.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_bar_proc, use_container_width=True)
                        
                        with col2:
                            fig_bar_proc2 = px.bar(
                                x=process_analysis.index,
                                y=process_analysis['Puntuacion_Promedio'],
                                title="Puntuación Promedio por Proceso",
                                labels={'x': 'Proceso', 'y': 'Puntuación Promedio'}
                            )
                            fig_bar_proc2.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_bar_proc2, use_container_width=True)
                        
                        # Distribución de prioridades por proceso
                        st.subheader("🎯 Distribución de Prioridades por Proceso")
                        
                        priority_by_process = df_process_expanded.groupby(['Proceso_Individual', 'Prioridad']).size().unstack(fill_value=0)
                        
                        if not priority_by_process.empty:
                            fig_stack = px.bar(
                                priority_by_process,
                                title="Distribución de Prioridades por Proceso",
                                labels={'value': 'Número de Iniciativas', 'index': 'Proceso'},
                                color_discrete_map={'Alta': '#28a745', 'Media': '#ffc107', 'Baja': '#dc3545'}
                            )
                            fig_stack.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_stack, use_container_width=True)
                        
                        # Heatmap de métricas por proceso
                        if len(process_analysis) > 1:
                            st.subheader("🌡️ Mapa de Calor: Métricas por Proceso")
                            metrics_cols = ['Val_Estrategico', 'Impacto', 'Viabilidad', 'Costo_Beneficio',
                                           'Innovacion', 'Escalabilidad', 'Tiempo_Impl']
                            
                            fig_heatmap_proc = px.imshow(
                                process_analysis[metrics_cols].T,
                                labels=dict(x="Proceso", y="Métrica", color="Puntuación"),
                                x=process_analysis.index,
                                y=['Valor Estratégico', 'Impacto', 'Viabilidad', 'Costo-Beneficio',
                                   'Innovación', 'Escalabilidad', 'Tiempo Impl.'],
                                title="Mapa de Calor: Métricas por Proceso",
                                aspect="auto"
                            )
                            fig_heatmap_proc.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_heatmap_proc, use_container_width=True)
                        
                        # Top iniciativas por proceso
                        st.subheader("🏆 Top Iniciativas por Proceso")
                        
                        process_list = process_analysis.index.tolist()
                        selected_process_detail = st.selectbox(
                            "Selecciona un proceso para ver sus mejores iniciativas:",
                            process_list
                        )
                        
                        if selected_process_detail:
                            process_initiatives = df_process_expanded[
                                df_process_expanded['Proceso_Individual'] == selected_process_detail
                            ].nlargest(3, 'Puntuacion_Ponderada')
                            
                            for i, (_, row) in enumerate(process_initiatives.iterrows(), 1):
                                priority_class = f"priority-{row['Prioridad'].lower()}"
                                
                                nombre_iniciativa = fix_encoding(row['Nombre_Iniciativa'])
                                nombre_colaborador = fix_encoding(row['Nombre_Colaborador'])
                                area = fix_encoding(row['Area'])
                                
                                st.markdown(f"""
                                <div class="metric-card {priority_class}">
                                    <h4>#{i} {nombre_iniciativa}</h4>
                                    <p><strong>👤 Propuesto por:</strong> {nombre_colaborador} ({area})</p>
                                    <p><strong>⭐ Puntuación:</strong> {row['Puntuacion_Ponderada']:.2f}/5.0 | 
                                       <strong>🎯 Prioridad:</strong> {row['Prioridad']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Tabla resumen por proceso
                        st.subheader("📋 Resumen por Proceso")
                        st.dataframe(process_analysis, use_container_width=True)
                        
                        # Insights por proceso
                        st.subheader("💡 Insights por Proceso")
                        
                        # Proceso con más iniciativas
                        most_active_process = process_analysis.index[0]
                        most_initiatives_count = process_analysis.iloc[0]['Num_Iniciativas']
                        
                        # Proceso con mejor puntuación promedio
                        best_scored_process = process_analysis.loc[process_analysis['Puntuacion_Promedio'].idxmax()]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.info(f"""
                            **🔥 Proceso más activo:**  
                            **{most_active_process}** con {int(most_initiatives_count)} iniciativas
                            """)
                        
                        with col2:
                            st.success(f"""
                            **⭐ Proceso mejor puntuado:**  
                            **{best_scored_process.name}** con {best_scored_process['Puntuacion_Promedio']:.2f}/5.0 promedio
                            """)
                    
                    else:
                        st.warning("No se encontraron datos de procesos para analizar.")
                
                else:
                    st.warning("La columna de procesos no está disponible en los datos actuales.")
            
            # ==========================================
            # TAB 6: LÍNEA DE TIEMPO
            # ==========================================
            
            with tab6:
                st.subheader("📅 Línea de Tiempo de Iniciativas")
                
                if 'Fecha_Procesada' in df_filtered.columns:
                    create_timeline_charts(df_filtered)
                    
                    # Tabla de iniciativas por fecha
                    st.subheader("📋 Registro Cronológico")
                    
                    if 'Fecha_Procesada' in df_filtered.columns and df_filtered['Fecha_Procesada'].notna().any():
                        df_timeline = df_filtered[df_filtered['Fecha_Procesada'].notna()].copy()
                        df_timeline = df_timeline.sort_values('Fecha_Procesada', ascending=False)
                        
                        # Crear tabla resumida
                        timeline_table = df_timeline[['Fecha_Procesada', 'Nombre_Iniciativa', 'Nombre_Colaborador', 
                                                     'Area', 'Puntuacion_Ponderada', 'Prioridad']].copy()
                        
                        timeline_table['Fecha'] = timeline_table['Fecha_Procesada'].dt.strftime('%d/%m/%Y %H:%M')
                        timeline_table = timeline_table.drop('Fecha_Procesada', axis=1)
                        
                        # Aplicar corrección de encoding
                        for col in ['Nombre_Iniciativa', 'Nombre_Colaborador', 'Area']:
                            if col in timeline_table.columns:
                                timeline_table[col] = timeline_table[col].apply(fix_encoding)
                        
                        timeline_table['Puntuacion_Ponderada'] = timeline_table['Puntuacion_Ponderada'].round(2)
                        
                        # Reordenar columnas
                        timeline_table = timeline_table[['Fecha', 'Nombre_Iniciativa', 'Nombre_Colaborador', 
                                                        'Area', 'Puntuacion_Ponderada', 'Prioridad']]
                        
                        st.dataframe(
                            timeline_table,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Fecha": "📅 Fecha de Registro",
                                "Nombre_Iniciativa": "💡 Iniciativa",
                                "Nombre_Colaborador": "👤 Colaborador", 
                                "Area": "🏢 Área",
                                "Puntuacion_Ponderada": "⭐ Puntuación",
                                "Prioridad": "🎯 Prioridad"
                            }
                        )
                        
                        # Opción de descarga de cronológico
                        csv_timeline = timeline_table.to_csv(index=False)
                        st.download_button(
                            label="⬇️ Descargar Cronológico CSV",
                            data=csv_timeline,
                            file_name=f"cronologico_iniciativas_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    
                else:
                    st.warning("No hay información de fechas disponible en los datos actuales.")
                    st.info("Para ver la línea de tiempo, asegúrate de que los datos incluyan la columna 'Marca temporal' del Google Forms.")
            
            # ==========================================
            # TAB 7: REPORTE EJECUTIVO
            # ==========================================
            
            with tab7:
                st.subheader("📋 Reporte Ejecutivo")
                
                # Botones superiores
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                
                with col_btn1:
                    # Botón PDF
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
                
                with col_btn2:
                    # Botón CSV
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
                
                fecha_reporte = datetime.now().strftime('%B %Y')
                st.markdown("### 📊 Resumen Ejecutivo")
                st.markdown(f"**Período de análisis:** {fecha_reporte}")
                
                # Métricas clave
                st.markdown("#### Métricas Clave:")
                met_col1, met_col2, met_col3, met_col4 = st.columns(4)
                
                with met_col1:
                    st.metric("Total Iniciativas", total_initiatives)
                
                with met_col2:
                    st.metric("Alta Prioridad", f"{high_priority}", 
                             delta=f"{high_priority/total_initiatives*100:.1f}%" if total_initiatives > 0 else "0%")
                
                with met_col3:
                    st.metric("Puntuación Promedio", f"{avg_score:.2f}/5.0")
                
                with met_col4:
                    st.metric("Área Más Activa", fix_encoding(top_area))
                
                # Distribución de prioridades
                st.markdown("#### 🎯 Distribución de Prioridades")
                priority_col1, priority_col2 = st.columns([1, 2])
                
                with priority_col1:
                    priority_data = pd.DataFrame({
                        'Prioridad': ['Alta', 'Media', 'Baja'],
                        'Cantidad': [high_priority, medium_priority, low_priority],
                        'Porcentaje': [
                            f"{high_priority/total_initiatives*100:.1f}%" if total_initiatives > 0 else "0%",
                            f"{medium_priority/total_initiatives*100:.1f}%" if total_initiatives > 0 else "0%",
                            f"{low_priority/total_initiatives*100:.1f}%" if total_initiatives > 0 else "0%"
                        ]
                    })
                    st.dataframe(priority_data, hide_index=True)
                
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
                
                # Top 3 iniciativas
                st.markdown("#### 🏆 Top 3 Iniciativas Recomendadas")
                top_3 = df_filtered.nlargest(3, 'Puntuacion_Ponderada')
                
                for i, (_, row) in enumerate(top_3.iterrows(), 1):
                    priority_class = f"priority-{row['Prioridad'].lower()}"
                    
                    # Aplicar corrección de encoding
                    nombre_iniciativa = fix_encoding(row['Nombre_Iniciativa'])
                    nombre_colaborador = fix_encoding(row['Nombre_Colaborador'])
                    area = fix_encoding(row['Area'])
                    problema = fix_encoding(str(row.get('Problema', 'No especificado')))
                    
                    # Calcular fortalezas
                    metrics_dict = {
                        'Valor_Estrategico': 'Valor Estratégico',
                        'Nivel_Impacto': 'Nivel de Impacto',
                        'Viabilidad_Tecnica': 'Viabilidad Técnica',
                        'Costo_Beneficio': 'Costo-Beneficio',
                        'Innovacion_Disrupcion': 'Innovación',
                        'Escalabilidad_Transversalidad': 'Escalabilidad',
                        'Tiempo_Implementacion': 'Tiempo de Implementación'
                    }
                    
                    fortalezas = [f"{metric_name} ({row[metric_key]}/5)" 
                                 for metric_key, metric_name in metrics_dict.items() 
                                 if row[metric_key] >= 4]
                    
                    fortalezas_text = ", ".join(fortalezas) if fortalezas else "Perfil equilibrado"
                    
                    st.markdown(f"""
<div class="metric-card {priority_class}">
    <h4>🏆 #{i} {nombre_iniciativa}</h4>
    <p><strong>👤 Propuesto por:</strong> {nombre_colaborador} ({area})</p>
    <p><strong>⭐ Puntuación:</strong> {row['Puntuacion_Ponderada']:.2f}/5.0 | 
       <strong>🎯 Prioridad:</strong> {row['Prioridad']}</p>
    <p><strong>💪 Fortalezas:</strong> {fortalezas_text}</p>
    <p><strong>🔍 Problema que resuelve:</strong> {problema[:100]}{'...' if len(problema) > 100 else ''}</p>
    <p><strong>💡 Propuesta:</strong> {fix_encoding(str(row.get('Propuesta', 'No especificada')))[:100]}{'...' if len(str(row.get('Propuesta', ''))) > 100 else ''}</p>
</div>
                    """, unsafe_allow_html=True)
                
                # Recomendaciones estratégicas
                st.markdown("#### 💡 Recomendaciones Estratégicas")
                
                recommendations = []
                
                if high_priority > 0:
                    recommendations.append(f"**🚀 Implementación inmediata:** Priorizar las {high_priority} iniciativas de alta puntuación")
                
                if medium_priority > 0:
                    recommendations.append(f"**🔍 Análisis detallado:** Las {medium_priority} iniciativas de prioridad media requieren evaluación adicional")
                
                low_viability = len(df_filtered[df_filtered['Viabilidad_Tecnica'] < 3])
                if low_viability > 0:
                    recommendations.append(f"**📚 Desarrollo de capacidades:** {low_viability} iniciativas presentan desafíos de viabilidad técnica")
                
                high_scalability = len(df_filtered[df_filtered['Escalabilidad_Transversalidad'] >= 4])
                if high_scalability > 0:
                    recommendations.append(f"**🔄 Potencial de escalabilidad:** {high_scalability} iniciativas muestran alto potencial de replicación")
                
                recommendations.append(f"**👏 Reconocimiento:** El área de '{fix_encoding(top_area)}' muestra el mayor nivel de participación")
                
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
                
                # Información sobre PDF
                st.markdown("---")
                st.info("""
                💡 **Sobre el Reporte PDF:**
                - Incluye todas las métricas y análisis mostrados arriba
                - Formato profesional optimizado para presentaciones ejecutivas
                - Contiene gráficos y tablas de fácil lectura
                - Ideal para compartir con la dirección y stakeholders
                """)
        
        else:
            st.warning("No se encontraron datos válidos en el archivo.")
            st.info("Verifica que el archivo contenga las columnas necesarias y datos válidos.")
    
    else:
        # ==========================================
        # PÁGINA DE INFORMACIÓN
        # ==========================================
        
        st.info("👆 Selecciona una fuente de datos en la barra lateral para comenzar el análisis.")
        
        st.markdown("""
        ## 💡 Acerca de este sistema
        
        Esta aplicación analiza automáticamente las iniciativas de innovación propuestas por los colaboradores, 
        utilizando las puntuaciones generadas por IA en Zapier.
        
        ### Características principales:
        - ✅ Carga automática desde Google Sheets
        - 📊 Visualizaciones interactivas 
        - 🎯 Sistema de priorización ponderado
        - 🏆 Rankings y comparaciones
        - 📋 Reportes ejecutivos en PDF
        - 🔍 Análisis detallado por iniciativa
        - 🔧 Corrección automática de caracteres especiales
        - 📅 Línea de tiempo de iniciativas
        - 🔐 Sistema de autenticación seguro
        
        ### Criterios de evaluación (escala 0-5):
        - **Valor estratégico (20%):** Contribución a objetivos estratégicos
        - **Nivel de impacto (20%):** Valor o transformación esperada
        - **Viabilidad técnica (15%):** Posibilidad de implementación
        - **Costo-beneficio (15%):** Justificación del esfuerzo/costo
        - **Innovación/disrupción (10%):** Novedad de la propuesta
        - **Escalabilidad/transversalidad (10%):** Potencial de replicación
        - **Tiempo de implementación (10%):** Velocidad de puesta en marcha
        
        ### Cómo usar:
        1. **Inicia sesión** con tus credenciales
        2. **Selecciona fuente de datos** en la barra lateral
        3. **Explora las 6 pestañas** de análisis disponibles
        4. **Aplica filtros** por área o prioridad según necesites
        5. **Analiza la línea de tiempo** para ver patrones temporales
        6. **Genera reportes PDF** para presentaciones ejecutivas
        7. **Exporta datos** en CSV para análisis adicionales
        """)

    # ==========================================
    # FOOTER
    # ==========================================
    
    st.markdown("---")
    st.markdown("🚀 **Sistema de Análisis de Iniciativas** | Desarrollado para el equipo de Innovación")

# ==========================================
# EJECUTAR APLICACIÓN
# ==========================================

if __name__ == "__main__":
    main()
