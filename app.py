import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
import openai
from openai import OpenAI
import json
import time
from typing import Dict, List, Tuple
import re

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Análisis de Iniciativas - Alico",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 0.5rem;
    }
    .initiative-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: bold;
    }
    .high-impact {
        background-color: #10b981;
        color: white;
    }
    .medium-impact {
        background-color: #f59e0b;
        color: white;
    }
    .low-impact {
        background-color: #ef4444;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estado de la sesión
if 'data' not in st.session_state:
    st.session_state.data = None
if 'analyzed_data' not in st.session_state:
    st.session_state.analyzed_data = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

# Función para conectar con Google Sheets
@st.cache_resource
def connect_to_google_sheets():
    """Conecta con Google Sheets usando las credenciales de servicio"""
    try:
        # Las credenciales deberían estar configuradas en Streamlit secrets
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {str(e)}")
        return None

# Función para cargar datos desde Google Sheets
def load_data_from_sheets(sheet_url):
    """Carga los datos desde Google Sheets"""
    try:
        client = connect_to_google_sheets()
        if client is None:
            return None
        
        sheet = client.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(0)  # Primera hoja
        data = worksheet.get_all_records()
        
        if data:
            df = pd.DataFrame(data)
            # Renombrar columnas para facilitar el trabajo
            column_mapping = {
                'Marca temporal': 'timestamp',
                'Nombre de la iniciativa': 'nombre_iniciativa',
                'Cuéntanos brevemente, ¿de qué trata tu iniciativa / idea innovadora?': 'descripcion',
                'Nombre de quién propone': 'proponente',
                'Número de celular al que te podamos contactar ': 'telefono',
                'Correo al que te podamos contactar ': 'correo',
                'Selecciona a qué público de interés perteneces ': 'publico_interes',
                'Selecciona el área o proceso al cual perteneces ': 'area_proceso',
                '¿Cuál el nombre de tu organización?': 'organizacion'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            # Convertir timestamp a datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True, errors='coerce')
            
            return df
        return None
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None

# Función para analizar iniciativas con OpenAI
def analyze_initiative_with_ai(initiative: Dict) -> Dict:
    """Analiza una iniciativa usando OpenAI GPT"""
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        prompt = f"""
        Analiza la siguiente iniciativa de innovación y proporciona una evaluación estructurada:
        
        Nombre: {initiative['nombre_iniciativa']}
        Descripción: {initiative['descripcion']}
        Área: {initiative['area_proceso']}
        
        Por favor, evalúa y proporciona la siguiente información en formato JSON:
        1. Categoría principal (Tecnología, Sostenibilidad, Procesos, Producto, Bienestar, Otros)
        2. Nivel de impacto potencial (1-10)
        3. Nivel de esfuerzo estimado (1-10)
        4. Viabilidad técnica (1-10)
        5. Alineación estratégica (1-10)
        6. Tiempo estimado de implementación (en meses)
        7. Principales beneficios (lista de 3-5 puntos)
        8. Principales riesgos o desafíos (lista de 3-5 puntos)
        9. Recomendaciones específicas (lista de 3-5 puntos)
        10. Puntuación global (1-100)
        
        Responde SOLO con el JSON, sin texto adicional.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en innovación empresarial y análisis de proyectos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parsear la respuesta JSON
        analysis = json.loads(response.choices[0].message.content)
        
        return {
            'categoria': analysis.get('categoria', 'Otros'),
            'impacto': analysis.get('impacto', 5),
            'esfuerzo': analysis.get('esfuerzo', 5),
            'viabilidad_tecnica': analysis.get('viabilidad_tecnica', 5),
            'alineacion_estrategica': analysis.get('alineacion_estrategica', 5),
            'tiempo_implementacion': analysis.get('tiempo_implementacion', 6),
            'beneficios': analysis.get('beneficios', []),
            'riesgos': analysis.get('riesgos', []),
            'recomendaciones': analysis.get('recomendaciones', []),
            'puntuacion_global': analysis.get('puntuacion_global', 50)
        }
    except Exception as e:
        st.warning(f"Error en análisis AI para {initiative['nombre_iniciativa']}: {str(e)}")
        # Retornar valores por defecto
        return {
            'categoria': 'Otros',
            'impacto': 5,
            'esfuerzo': 5,
            'viabilidad_tecnica': 5,
            'alineacion_estrategica': 5,
            'tiempo_implementacion': 6,
            'beneficios': ['Análisis pendiente'],
            'riesgos': ['Análisis pendiente'],
            'recomendaciones': ['Análisis pendiente'],
            'puntuacion_global': 50
        }

# Función para procesar todas las iniciativas
def process_initiatives(df: pd.DataFrame) -> pd.DataFrame:
    """Procesa todas las iniciativas y añade análisis AI"""
    analyzed_df = df.copy()
    
    # Añadir columnas para el análisis
    analysis_columns = ['categoria', 'impacto', 'esfuerzo', 'viabilidad_tecnica', 
                       'alineacion_estrategica', 'tiempo_implementacion', 'beneficios', 
                       'riesgos', 'recomendaciones', 'puntuacion_global']
    
    for col in analysis_columns:
        if col not in analyzed_df.columns:
            analyzed_df[col] = None
    
    # Analizar cada iniciativa
    progress_bar = st.progress(0)
    for idx, row in analyzed_df.iterrows():
        # Solo analizar si no ha sido analizada previamente
        if pd.isna(row['puntuacion_global']):
            with st.spinner(f"Analizando: {row['nombre_iniciativa']}..."):
                analysis = analyze_initiative_with_ai(row.to_dict())
                for key, value in analysis.items():
                    analyzed_df.at[idx, key] = value
        
        progress_bar.progress((idx + 1) / len(analyzed_df))
    
    progress_bar.empty()
    
    # Calcular cuadrante en matriz esfuerzo-impacto
    analyzed_df['cuadrante'] = analyzed_df.apply(
        lambda x: categorizar_cuadrante(x['impacto'], x['esfuerzo']), axis=1
    )
    
    return analyzed_df

def categorizar_cuadrante(impacto: float, esfuerzo: float) -> str:
    """Categoriza la iniciativa en un cuadrante de la matriz esfuerzo-impacto"""
    if impacto >= 7 and esfuerzo <= 4:
        return "Quick Wins"
    elif impacto >= 7 and esfuerzo > 4:
        return "Proyectos Estratégicos"
    elif impacto < 7 and esfuerzo <= 4:
        return "Fill Ins"
    else:
        return "Difíciles de Justificar"

# Función principal de la aplicación
def main():
    # Header
    st.markdown('<h1 class="main-header">💡 Sistema de Análisis de Iniciativas de Innovación</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #6b7280;">Alico SAS BIC - Área de Innovación</p>', unsafe_allow_html=True)
    
    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # URL de Google Sheets
        sheet_url = st.text_input(
            "URL de Google Sheets",
            value="https://docs.google.com/spreadsheets/d/1G57SXlODM0XKtSIozprz9dqPJEqPTpExsk0whv4sxIc/edit",
            help="Ingresa la URL del Google Sheets con las respuestas del formulario"
        )
        
        # Botón para cargar/actualizar datos
        if st.button("🔄 Cargar/Actualizar Datos", type="primary"):
            with st.spinner("Cargando datos desde Google Sheets..."):
                df = load_data_from_sheets(sheet_url)
                if df is not None:
                    st.session_state.data = df
                    st.session_state.last_update = datetime.now()
                    st.success(f"✅ Datos cargados: {len(df)} iniciativas encontradas")
                else:
                    st.error("❌ No se pudieron cargar los datos")
        
        # Mostrar última actualización
        if st.session_state.last_update:
            st.info(f"📅 Última actualización: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M')}")
        
        st.divider()
        
        # Filtros
        st.header("🔍 Filtros")
        
        if st.session_state.analyzed_data is not None:
            df = st.session_state.analyzed_data
            
            # Filtro por categoría
            categorias = ['Todas'] + sorted(df['categoria'].unique().tolist())
            categoria_filtro = st.selectbox("Categoría", categorias)
            
            # Filtro por área
            areas = ['Todas'] + sorted(df['area_proceso'].unique().tolist())
            area_filtro = st.selectbox("Área/Proceso", areas)
            
            # Filtro por cuadrante
            cuadrantes = ['Todos'] + sorted(df['cuadrante'].unique().tolist())
            cuadrante_filtro = st.selectbox("Cuadrante", cuadrantes)
            
            # Filtro por puntuación
            puntuacion_min = st.slider("Puntuación mínima", 0, 100, 0)
    
    # Contenido principal
    if st.session_state.data is not None:
        # Analizar datos si no han sido analizados
        if st.session_state.analyzed_data is None:
            if st.button("🤖 Analizar Iniciativas con IA", type="primary"):
                st.session_state.analyzed_data = process_initiatives(st.session_state.data)
                st.success("✅ Análisis completado")
        
        if st.session_state.analyzed_data is not None:
            df = st.session_state.analyzed_data.copy()
            
            # Aplicar filtros
            if 'categoria_filtro' in locals() and categoria_filtro != 'Todas':
                df = df[df['categoria'] == categoria_filtro]
            if 'area_filtro' in locals() and area_filtro != 'Todas':
                df = df[df['area_proceso'] == area_filtro]
            if 'cuadrante_filtro' in locals() and cuadrante_filtro != 'Todos':
                df = df[df['cuadrante'] == cuadrante_filtro]
            if 'puntuacion_min' in locals():
                df = df[df['puntuacion_global'] >= puntuacion_min]
            
            # Tabs principales
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Dashboard", "📋 Iniciativas", "📈 Matriz Esfuerzo-Impacto", 
                "📑 Informes", "🔍 Análisis Detallado"
            ])
            
            with tab1:
                # Métricas principales
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Total Iniciativas", len(df))
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Puntuación Promedio", f"{df['puntuacion_global'].mean():.1f}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    quick_wins = len(df[df['cuadrante'] == 'Quick Wins'])
                    st.metric("Quick Wins", quick_wins)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    high_impact = len(df[df['impacto'] >= 8])
                    st.metric("Alto Impacto", high_impact)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.divider()
                
                # Gráficos del dashboard
                col1, col2 = st.columns(2)
                
                with col1:
                    # Distribución por categorías
                    fig_cat = px.pie(
                        df, 
                        names='categoria', 
                        title='Distribución por Categorías',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_cat.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_cat, use_container_width=True)
                
                with col2:
                    # Distribución por áreas
                    area_counts = df['area_proceso'].value_counts()
                    fig_area = px.bar(
                        x=area_counts.values,
                        y=area_counts.index,
                        orientation='h',
                        title='Iniciativas por Área',
                        labels={'x': 'Cantidad', 'y': 'Área'},
                        color=area_counts.values,
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig_area, use_container_width=True)
                
                # Timeline de iniciativas
                st.subheader("📅 Timeline de Iniciativas")
                df_timeline = df.copy()
                df_timeline['fecha'] = df_timeline['timestamp'].dt.date
                timeline_data = df_timeline.groupby('fecha').size().reset_index(name='cantidad')
                
                fig_timeline = px.line(
                    timeline_data,
                    x='fecha',
                    y='cantidad',
                    title='Evolución de Iniciativas Propuestas',
                    markers=True,
                    line_shape='spline'
                )
                fig_timeline.update_layout(
                    xaxis_title="Fecha",
                    yaxis_title="Cantidad de Iniciativas",
                    hovermode='x unified'
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                # Top iniciativas
                st.subheader("🏆 Top Iniciativas por Puntuación")
                top_initiatives = df.nlargest(5, 'puntuacion_global')[
                    ['nombre_iniciativa', 'proponente', 'categoria', 'puntuacion_global', 'impacto', 'esfuerzo']
                ]
                
                for idx, row in top_initiatives.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**{row['nombre_iniciativa']}**")
                        st.caption(f"Por: {row['proponente']} | Categoría: {row['categoria']}")
                    with col2:
                        st.metric("Puntuación", f"{row['puntuacion_global']:.0f}")
                    with col3:
                        impact_class = "high-impact" if row['impacto'] >= 8 else "medium-impact" if row['impacto'] >= 5 else "low-impact"
                        st.markdown(f'<span class="status-badge {impact_class}">Impacto: {row["impacto"]:.0f}</span>', unsafe_allow_html=True)
            
            with tab2:
                st.header("📋 Lista de Iniciativas")
                
                # Opciones de visualización
                col1, col2 = st.columns([3, 1])
                with col1:
                    search_term = st.text_input("🔍 Buscar iniciativa", placeholder="Buscar por nombre o descripción...")
                with col2:
                    sort_by = st.selectbox("Ordenar por", ["Puntuación", "Fecha", "Impacto", "Esfuerzo"])
                
                # Filtrar por búsqueda
                if search_term:
                    mask = (
                        df['nombre_iniciativa'].str.contains(search_term, case=False, na=False) |
                        df['descripcion'].str.contains(search_term, case=False, na=False)
                    )
                    df_filtered = df[mask]
                else:
                    df_filtered = df
                
                # Ordenar
                sort_mapping = {
                    "Puntuación": "puntuacion_global",
                    "Fecha": "timestamp",
                    "Impacto": "impacto",
                    "Esfuerzo": "esfuerzo"
                }
                df_filtered = df_filtered.sort_values(by=sort_mapping[sort_by], ascending=False)
                
                # Mostrar iniciativas
                for idx, row in df_filtered.iterrows():
                    with st.expander(f"{row['nombre_iniciativa']} - Puntuación: {row['puntuacion_global']:.0f}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**Proponente:** {row['proponente']}")
                            st.markdown(f"**Área:** {row['area_proceso']}")
                            st.markdown(f"**Categoría:** {row['categoria']}")
                            st.markdown(f"**Fecha:** {row['timestamp'].strftime('%Y-%m-%d')}")
                            
                            st.markdown("**Descripción:**")
                            st.write(row['descripcion'])
                        
                        with col2:
                            # Métricas de evaluación
                            st.markdown("**Evaluación:**")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Impacto", f"{row['impacto']:.0f}/10")
                                st.metric("Viabilidad", f"{row['viabilidad_tecnica']:.0f}/10")
                            with col_b:
                                st.metric("Esfuerzo", f"{row['esfuerzo']:.0f}/10")
                                st.metric("Alineación", f"{row['alineacion_estrategica']:.0f}/10")
                            
                            st.metric("Tiempo Est.", f"{row['tiempo_implementacion']} meses")
                            
                            # Cuadrante
                            cuadrante_color = {
                                "Quick Wins": "🟢",
                                "Proyectos Estratégicos": "🔵",
                                "Fill Ins": "🟡",
                                "Difíciles de Justificar": "🔴"
                            }
                            st.markdown(f"**Cuadrante:** {cuadrante_color.get(row['cuadrante'], '')} {row['cuadrante']}")
                        
                        # Beneficios, riesgos y recomendaciones
                        tab_ben, tab_risk, tab_rec = st.tabs(["✅ Beneficios", "⚠️ Riesgos", "💡 Recomendaciones"])
                        
                        with tab_ben:
                            if isinstance(row['beneficios'], list):
                                for beneficio in row['beneficios']:
                                    st.write(f"• {beneficio}")
                        
                        with tab_risk:
                            if isinstance(row['riesgos'], list):
                                for riesgo in row['riesgos']:
                                    st.write(f"• {riesgo}")
                        
                        with tab_rec:
                            if isinstance(row['recomendaciones'], list):
                                for rec in row['recomendaciones']:
                                    st.write(f"• {rec}")
                        
                        # Información de contacto
                        with st.container():
                            st.divider()
                            st.caption(f"📧 {row['correo']} | 📱 {row['telefono']}")
            
            with tab3:
                st.header("📈 Matriz Esfuerzo-Impacto")
                
                # Crear matriz interactiva
                fig_matrix = px.scatter(
                    df,
                    x='esfuerzo',
                    y='impacto',
                    color='cuadrante',
                    size='puntuacion_global',
                    hover_data=['nombre_iniciativa', 'proponente', 'categoria'],
                    title='Matriz de Priorización: Esfuerzo vs Impacto',
                    labels={'esfuerzo': 'Esfuerzo (1-10)', 'impacto': 'Impacto (1-10)'},
                    color_discrete_map={
                        "Quick Wins": "#10b981",
                        "Proyectos Estratégicos": "#3b82f6",
                        "Fill Ins": "#f59e0b",
                        "Difíciles de Justificar": "#ef4444"
                    }
                )
                
                # Añadir líneas divisorias
                fig_matrix.add_hline(y=7, line_dash="dash", line_color="gray", opacity=0.5)
                fig_matrix.add_vline(x=4, line_dash="dash", line_color="gray", opacity=0.5)
                
                # Añadir anotaciones para los cuadrantes
                fig_matrix.add_annotation(
                    x=2, y=8.5,
                    text="Quick Wins<br>Alto Impacto<br>Bajo Esfuerzo",
                    showarrow=False,
                    font=dict(size=12, color="green"),
                    bgcolor="rgba(16, 185, 129, 0.1)",
                    borderpad=4
                )
                fig_matrix.add_annotation(
                    x=7, y=8.5,
                    text="Proyectos<br>Estratégicos<br>Alto Impacto<br>Alto Esfuerzo",
                    showarrow=False,
                    font=dict(size=12, color="blue"),
                    bgcolor="rgba(59, 130, 246, 0.1)",
                    borderpad=4
                )
                fig_matrix.add_annotation(
                    x=2, y=3.5,
                    text="Fill Ins<br>Bajo Impacto<br>Bajo Esfuerzo",
                    showarrow=False,
                    font=dict(size=12, color="orange"),
                    bgcolor="rgba(245, 158, 11, 0.1)",
                    borderpad=4
                )
                fig_matrix.add_annotation(
                    x=7, y=3.5,
                    text="Difíciles de<br>Justificar<br>Bajo Impacto<br>Alto Esfuerzo",
                    showarrow=False,
                    font=dict(size=12, color="red"),
                    bgcolor="rgba(239, 68, 68, 0.1)",
                    borderpad=4
                )
                
                fig_matrix.update_layout(
                    xaxis=dict(range=[0, 11], dtick=1),
                    yaxis=dict(range=[0, 11], dtick=1),
                    height=600,
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_matrix, use_container_width=True)
                
                # Resumen por cuadrante
                st.subheader("📊 Resumen por Cuadrante")
                
                col1, col2, col3, col4 = st.columns(4)
                
                cuadrantes_info = {
                    "Quick Wins": {"emoji": "🟢", "desc": "Implementar inmediatamente"},
                    "Proyectos Estratégicos": {"emoji": "🔵", "desc": "Planificar cuidadosamente"},
                    "Fill Ins": {"emoji": "🟡", "desc": "Implementar si hay recursos"},
                    "Difíciles de Justificar": {"emoji": "🔴", "desc": "Reconsiderar o rechazar"}
                }
                
                for col, (cuadrante, info) in zip([col1, col2, col3, col4], cuadrantes_info.items()):
                    with col:
                        df_cuadrante = df[df['cuadrante'] == cuadrante]
                        st.markdown(f"### {info['emoji']} {cuadrante}")
                        st.metric("Cantidad", len(df_cuadrante))
                        st.caption(info['desc'])
                        
                        if len(df_cuadrante) > 0:
                            st.markdown("**Top 3:**")
                            for idx, row in df_cuadrante.nlargest(3, 'puntuacion_global').iterrows():
                                st.write(f"• {row['nombre_iniciativa'][:30]}...")
            
            with tab4:
                st.header("📑 Generación de Informes")
                
                # Selector de tipo de informe
                tipo_informe = st.selectbox(
                    "Selecciona el tipo de informe",
                    ["Resumen Ejecutivo", "Análisis por Categorías", "Reporte de Viabilidad", "Informe Completo"]
                )
                
                if st.button("📄 Generar Informe", type="primary"):
                    with st.spinner("Generando informe..."):
                        
                        if tipo_informe == "Resumen Ejecutivo":
                            st.markdown("## 📊 Resumen Ejecutivo de Iniciativas de Innovación")
                            st.markdown(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d')}")
                            st.markdown(f"**Total de Iniciativas Analizadas:** {len(df)}")
                            
                            # Métricas clave
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Puntuación Promedio", f"{df['puntuacion_global'].mean():.1f}/100")
                            with col2:
                                st.metric("Impacto Promedio", f"{df['impacto'].mean():.1f}/10")
                            with col3:
                                st.metric("Tiempo Promedio Implementación", f"{df['tiempo_implementacion'].mean():.1f} meses")
                            
                            # Top iniciativas
                            st.markdown("### 🏆 Top 5 Iniciativas Recomendadas")
                            top_5 = df.nlargest(5, 'puntuacion_global')
                            for idx, row in top_5.iterrows():
                                st.markdown(f"**{idx+1}. {row['nombre_iniciativa']}**")
                                st.write(f"   - Proponente: {row['proponente']}")
                                st.write(f"   - Puntuación: {row['puntuacion_global']:.0f}/100")
                                st.write(f"   - Cuadrante: {row['cuadrante']}")
                            
                            # Distribución por categorías
                            st.markdown("### 📈 Distribución por Categorías")
                            cat_dist = df['categoria'].value_counts()
                            for cat, count in cat_dist.items():
                                st.write(f"- **{cat}:** {count} iniciativas ({count/len(df)*100:.1f}%)")
                            
                            # Recomendaciones generales
                            st.markdown("### 💡 Recomendaciones Generales")
                            quick_wins_count = len(df[df['cuadrante'] == 'Quick Wins'])
                            st.write(f"1. Se identificaron **{quick_wins_count} Quick Wins** que deben ser implementados de inmediato.")
                            st.write("2. Las iniciativas de **Tecnología** muestran el mayor potencial de impacto.")
                            st.write("3. Se recomienda establecer un comité de seguimiento para las iniciativas estratégicas.")
                        
                        elif tipo_informe == "Análisis por Categorías":
                            st.markdown("## 📊 Análisis Detallado por Categorías")
                            
                            for categoria in df['categoria'].unique():
                                df_cat = df[df['categoria'] == categoria]
                                
                                st.markdown(f"### {categoria}")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Iniciativas", len(df_cat))
                                with col2:
                                    st.metric("Puntuación Promedio", f"{df_cat['puntuacion_global'].mean():.1f}")
                                with col3:
                                    st.metric("Impacto Promedio", f"{df_cat['impacto'].mean():.1f}")
                                with col4:
                                    st.metric("Esfuerzo Promedio", f"{df_cat['esfuerzo'].mean():.1f}")
                                
                                # Top 3 de la categoría
                                st.markdown("**Top 3 Iniciativas:**")
                                for idx, row in df_cat.nlargest(3, 'puntuacion_global').iterrows():
                                    st.write(f"• {row['nombre_iniciativa']} (Puntuación: {row['puntuacion_global']:.0f})")
                                
                                st.divider()
                        
                        elif tipo_informe == "Reporte de Viabilidad":
                            st.markdown("## 🎯 Reporte de Viabilidad Técnica")
                            
                            # Iniciativas más viables
                            st.markdown("### ✅ Iniciativas de Alta Viabilidad (≥8/10)")
                            high_viability = df[df['viabilidad_tecnica'] >= 8].sort_values('viabilidad_tecnica', ascending=False)
                            
                            for idx, row in high_viability.iterrows():
                                with st.expander(f"{row['nombre_iniciativa']} - Viabilidad: {row['viabilidad_tecnica']:.0f}/10"):
                                    st.write(f"**Descripción:** {row['descripcion']}")
                                    st.write(f"**Tiempo estimado:** {row['tiempo_implementacion']} meses")
                                    st.write(f"**Impacto esperado:** {row['impacto']:.0f}/10")
                            
                            # Iniciativas que requieren análisis adicional
                            st.markdown("### ⚠️ Iniciativas que Requieren Análisis Adicional (5-7/10)")
                            medium_viability = df[(df['viabilidad_tecnica'] >= 5) & (df['viabilidad_tecnica'] < 8)]
                            
                            if len(medium_viability) > 0:
                                st.write(f"Se identificaron {len(medium_viability)} iniciativas que requieren evaluación adicional:")
                                for idx, row in medium_viability.iterrows():
                                    st.write(f"• {row['nombre_iniciativa']} - Viabilidad: {row['viabilidad_tecnica']:.0f}/10")
                        
                        else:  # Informe Completo
                            st.markdown("## 📋 Informe Completo de Iniciativas de Innovación")
                            st.markdown(f"**Generado el:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                            
                            # Descargar como CSV
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Descargar datos completos (CSV)",
                                data=csv,
                                file_name=f"iniciativas_innovacion_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                            
                            # Vista de tabla completa
                            st.dataframe(
                                df[[
                                    'nombre_iniciativa', 'proponente', 'categoria', 
                                    'puntuacion_global', 'impacto', 'esfuerzo', 
                                    'viabilidad_tecnica', 'cuadrante'
                                ]].sort_values('puntuacion_global', ascending=False),
                                use_container_width=True
                            )
            
            with tab5:
                st.header("🔍 Análisis Detallado de Iniciativa")
                
                # Selector de iniciativa
                iniciativa_seleccionada = st.selectbox(
                    "Selecciona una iniciativa para análisis detallado",
                    df['nombre_iniciativa'].tolist()
                )
                
                if iniciativa_seleccionada:
                    row = df[df['nombre_iniciativa'] == iniciativa_seleccionada].iloc[0]
                    
                    # Información general
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"### {row['nombre_iniciativa']}")
                        st.write(f"**Proponente:** {row['proponente']}")
                        st.write(f"**Área:** {row['area_proceso']}")
                        st.write(f"**Fecha de propuesta:** {row['timestamp'].strftime('%Y-%m-%d')}")
                        
                        st.markdown("**Descripción completa:**")
                        st.info(row['descripcion'])
                    
                    with col2:
                        # Gráfico de radar
                        categories = ['Impacto', 'Viabilidad', 'Alineación', 'Innovación']
                        values = [
                            row['impacto'],
                            row['viabilidad_tecnica'],
                            row['alineacion_estrategica'],
                            row['puntuacion_global']/10
                        ]
                        
                        fig_radar = go.Figure(data=go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name='Evaluación'
                        ))
                        
                        fig_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 10]
                                )),
                            showlegend=False,
                            title="Evaluación Multidimensional"
                        )
                        
                        st.plotly_chart(fig_radar, use_container_width=True)
                    
                    # Métricas detalladas
                    st.markdown("### 📊 Métricas de Evaluación")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Puntuación Global", f"{row['puntuacion_global']:.0f}/100")
                    with col2:
                        st.metric("Impacto", f"{row['impacto']:.0f}/10")
                    with col3:
                        st.metric("Esfuerzo", f"{row['esfuerzo']:.0f}/10")
                    with col4:
                        st.metric("Viabilidad", f"{row['viabilidad_tecnica']:.0f}/10")
                    with col5:
                        st.metric("Tiempo", f"{row['tiempo_implementacion']} meses")
                    
                    # Análisis detallado
                    st.markdown("### 📝 Análisis Detallado")
                    
                    tab1, tab2, tab3, tab4 = st.tabs(["Beneficios", "Riesgos", "Recomendaciones", "Plan de Acción"])
                    
                    with tab1:
                        st.markdown("#### ✅ Beneficios Esperados")
                        if isinstance(row['beneficios'], list):
                            for i, beneficio in enumerate(row['beneficios'], 1):
                                st.success(f"{i}. {beneficio}")
                    
                    with tab2:
                        st.markdown("#### ⚠️ Riesgos Identificados")
                        if isinstance(row['riesgos'], list):
                            for i, riesgo in enumerate(row['riesgos'], 1):
                                st.warning(f"{i}. {riesgo}")
                    
                    with tab3:
                        st.markdown("#### 💡 Recomendaciones")
                        if isinstance(row['recomendaciones'], list):
                            for i, rec in enumerate(row['recomendaciones'], 1):
                                st.info(f"{i}. {rec}")
                    
                    with tab4:
                        st.markdown("#### 📅 Plan de Acción Sugerido")
                        
                        # Generar plan de acción basado en el tiempo estimado
                        meses = int(row['tiempo_implementacion'])
                        fases = []
                        
                        if meses <= 3:
                            fases = [
                                ("Fase 1: Planificación", "Mes 1", "Definir alcance y recursos"),
                                ("Fase 2: Implementación", "Mes 2", "Desarrollo y pruebas"),
                                ("Fase 3: Lanzamiento", "Mes 3", "Despliegue y monitoreo")
                            ]
                        elif meses <= 6:
                            fases = [
                                ("Fase 1: Análisis", "Mes 1-2", "Estudio de viabilidad detallado"),
                                ("Fase 2: Diseño", "Mes 2-3", "Diseño de la solución"),
                                ("Fase 3: Desarrollo", "Mes 3-5", "Implementación"),
                                ("Fase 4: Despliegue", "Mes 5-6", "Lanzamiento y seguimiento")
                            ]
                        else:
                            fases = [
                                ("Fase 1: Investigación", "Mes 1-2", "Análisis profundo"),
                                ("Fase 2: Planificación", "Mes 3-4", "Plan detallado"),
                                ("Fase 3: Desarrollo", f"Mes 5-{meses-2}", "Implementación iterativa"),
                                ("Fase 4: Validación", f"Mes {meses-1}", "Pruebas y ajustes"),
                                ("Fase 5: Lanzamiento", f"Mes {meses}", "Despliegue final")
                            ]
                        
                        for fase, tiempo, descripcion in fases:
                            st.write(f"**{fase}**")
                            st.write(f"📅 {tiempo}: {descripcion}")
                            st.divider()
                        
                        # Recursos estimados
                        st.markdown("#### 💰 Recursos Estimados")
                        if row['impacto'] >= 8:
                            st.write("• **Prioridad:** Alta - Asignar recursos dedicados")
                        elif row['impacto'] >= 5:
                            st.write("• **Prioridad:** Media - Recursos compartidos")
                        else:
                            st.write("• **Prioridad:** Baja - Recursos mínimos")
                        
                        st.write(f"• **Equipo sugerido:** {2 if row['esfuerzo'] < 5 else 3 if row['esfuerzo'] < 8 else 5} personas")
                        st.write(f"• **Área líder:** {row['area_proceso']}")
                    
                    # Información de contacto
                    st.markdown("### 📞 Información de Contacto")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"📧 **Email:** {row['correo']}")
                    with col2:
                        st.write(f"📱 **Teléfono:** {row['telefono']}")
    
    else:
        # Mensaje cuando no hay datos
        st.info("👋 ¡Bienvenido al Sistema de Análisis de Iniciativas de Innovación!")
        st.markdown("""
        Para comenzar:
        1. Ingresa la URL de tu Google Sheets en la barra lateral
        2. Haz clic en **Cargar/Actualizar Datos**
        3. Una vez cargados los datos, haz clic en **Analizar Iniciativas con IA**
        
        El sistema analizará automáticamente cada iniciativa y proporcionará:
        - 📊 Dashboard con métricas clave
        - 📈 Matriz de priorización Esfuerzo-Impacto
        - 📋 Vista detallada de cada iniciativa
        - 📑 Generación de informes personalizados
        - 🔍 Análisis profundo con recomendaciones
        """)
        
        # Mostrar arquitectura del sistema
        with st.expander("🏗️ Arquitectura del Sistema"):
            st.markdown("""
            **Componentes principales:**
            - **Google Sheets API**: Conexión en tiempo real con el formulario
            - **OpenAI GPT-4**: Análisis inteligente de iniciativas
            - **Streamlit**: Interfaz interactiva y visualizaciones
            - **Plotly**: Gráficos dinámicos e interactivos
            
            **Flujo de datos:**
            1. Las respuestas del Google Forms se almacenan en Sheets
            2. La aplicación lee los datos mediante la API
            3. Cada iniciativa se analiza con IA
            4. Los resultados se visualizan en dashboards interactivos
            """)

if __name__ == "__main__":
    main()
