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
import json
import time
from typing import Dict, List, Tuple
import re
import ast
import hashlib

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
            
            # Limpiar filas vacías o incompletas
            df = df.dropna(how='all')  # Eliminar filas completamente vacías
            df = df[df['nombre_iniciativa'].str.strip() != '']  # Eliminar filas con nombre vacío
            
            # Convertir timestamp a datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True, errors='coerce')
            
            # Generar un identificador único basado en nombre_iniciativa, timestamp y descripción
            df['initiative_id'] = df.apply(
                lambda row: hashlib.md5(f"{row['nombre_iniciativa']}_{row['timestamp']}_{row['descripcion']}".encode()).hexdigest(),
                axis=1
            )
            
            return df
        return None
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None

# Función para cargar datos analizados desde Google Sheets
def load_analyzed_data(sheet_url):
    """Carga los datos analizados desde una hoja específica en Google Sheets"""
    try:
        client = connect_to_google_sheets()
        if client is None:
            return None
        
        sheet = client.open_by_url(sheet_url)
        try:
            worksheet = sheet.worksheet("Analyzed Initiatives")
        except gspread.exceptions.WorksheetNotFound:
            # Crear la hoja si no existe
            worksheet = sheet.add_worksheet(title="Analyzed Initiatives", rows=1000, cols=20)
            # Definir encabezados
            headers = [
                'initiative_id', 'timestamp', 'nombre_iniciativa', 'descripcion', 'proponente',
                'telefono', 'correo', 'publico_interes', 'area_proceso', 'organizacion',
                'areas_innovacion', 'impacto_sostenibilidad', 'impacto_viabilidad',
                'impacto_diferenciacion', 'puntuacion_global', 'justificacion', 'impacto',
                'esfuerzo', 'viabilidad_tecnica', 'alineacion_estrategica', 'tiempo_implementacion',
                'categoria', 'beneficios', 'riesgos', 'recomendaciones', 'cuadrante'
            ]
            worksheet.update('A1', [headers])
        
        data = worksheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            # Convertir listas almacenadas como strings a listas reales
            for col in ['areas_innovacion', 'beneficios', 'riesgos', 'recomendaciones']:
                df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x else [])
            # Convertir timestamp a datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            return df
        return None
    except Exception as e:
        st.error(f"Error al cargar datos analizados: {str(e)}")
        return None

# Función para guardar datos analizados en Google Sheets
def save_analyzed_data(sheet_url, analyzed_data):
    """Guarda los datos analizados en la hoja 'Analyzed Initiatives'"""
    try:
        client = connect_to_google_sheets()
        if client is None:
            return
        
        sheet = client.open_by_url(sheet_url)
        try:
            worksheet = sheet.worksheet("Analyzed Initiatives")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title="Analyzed Initiatives", rows=1000, cols=20)
            headers = [
                'initiative_id', 'timestamp', 'nombre_iniciativa', 'descripcion', 'proponente',
                'telefono', 'correo', 'publico_interes', 'area_proceso', 'organizacion',
                'areas_innovacion', 'impacto_sostenibilidad', 'impacto_viabilidad',
                'impacto_diferenciacion', 'puntuacion_global', 'justificacion', 'impacto',
                'esfuerzo', 'viabilidad_tecnica', 'alineacion_estrategica', 'tiempo_implementacion',
                'categoria', 'beneficios', 'riesgos', 'recomendaciones', 'cuadrante'
            ]
            worksheet.update('A1', [headers])
        
        # Convertir DataFrame a lista de listas para guardar
        data_to_save = analyzed_data.copy()
        for col in ['areas_innovacion', 'beneficios', 'riesgos', 'recomendaciones']:
            data_to_save[col] = data_to_save[col].apply(json.dumps)
        data_to_save['timestamp'] = data_to_save['timestamp'].astype(str)
        
        # Obtener datos existentes
        existing_data = worksheet.get_all_records()
        existing_ids = set([row['initiative_id'] for row in existing_data]) if existing_data else set()
        
        # Filtrar solo los registros nuevos
        new_data = data_to_save[~data_to_save['initiative_id'].isin(existing_ids)]
        
        if not new_data.empty:
            # Convertir a lista de listas
            values = new_data.values.tolist()
            # Agregar al final de la hoja
            worksheet.append_rows(values, value_input_option='RAW')
            st.success(f"✅ Guardados {len(new_data)} nuevos análisis en Google Sheets")
    except Exception as e:
        st.error(f"Error al guardar datos analizados: {str(e)}")

# Función para analizar iniciativas con OpenAI
def analyze_initiative_with_ai(text):
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    prompt = (
        f"Analiza la siguiente iniciativa:\n\n"
        f"{text}\n\n"
        "Devuelve el análisis como un JSON válido con esta estructura exacta, sin incluir markdown ni texto adicional fuera del JSON:\n"
        "{\n"
        "  \"areas_innovacion\": [\"producto\", \"proceso\"],\n"
        "  \"impacto_sostenibilidad\": 70,\n"
        "  \"impacto_viabilidad\": 80,\n"
        "  \"impacto_diferenciacion\": 75,\n"
        "  \"puntuacion_global\": 78,\n"
        "  \"justificacion\": \"Texto corto explicando la puntuación\",\n"
        "  \"impacto\": 8,\n"
        "  \"esfuerzo\": 4,\n"
        "  \"viabilidad_tecnica\": 8,\n"
        "  \"alineacion_estrategica\": 7,\n"
        "  \"tiempo_implementacion\": 6,\n"
        "  \"categoria\": \"Tecnología\",\n"
        "  \"beneficios\": [\"Beneficio 1\", \"Beneficio 2\"],\n"
        "  \"riesgos\": [\"Riesgo 1\", \"Riesgo 2\"],\n"
        "  \"recomendaciones\": [\"Recomendación 1\", \"Recomendación 2\"]\n"
        "}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en innovación empresarial. Responde únicamente con un JSON válido, sin markdown ni texto adicional."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=700
        )
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code fences and any leading/trailing whitespace
        content = re.sub(r'^```json\n|```$|\n\s*\n', '', content, flags=re.MULTILINE).strip()
        
        # Attempt to parse JSON
        try:
            analysis = json.loads(content)
        except json.JSONDecodeError as parse_err:
            st.error(f"Error al parsear JSON: {parse_err}")
            st.write(f"Contenido recibido: {content}")
            return {
                "areas_innovacion": [],
                "impacto_sostenibilidad": 0,
                "impacto_viabilidad": 0,
                "impacto_diferenciacion": 0,
                "puntuacion_global": 0,
                "justificacion": "Error en el análisis: respuesta no válida",
                "impacto": 0,
                "esfuerzo": 0,
                "viabilidad_tecnica": 0,
                "alineacion_estrategica": 0,
                "tiempo_implementacion": 0,
                "categoria": "Sin categoría",
                "beneficios": [],
                "riesgos": [],
                "recomendaciones": []
            }
        
        # Validate that the response contains all required keys
        required_keys = [
            "areas_innovacion", "impacto_sostenibilidad", "impacto_viabilidad",
            "impacto_diferenciacion", "puntuacion_global", "justificacion",
            "impacto", "esfuerzo", "viabilidad_tecnica", "alineacion_estrategica",
            "tiempo_implementacion", "categoria", "beneficios", "riesgos", "recomendaciones"
        ]
        if not all(key in analysis for key in required_keys):
            missing_keys = [key for key in required_keys if key not in analysis]
            st.error(f"Error: Faltan claves en la respuesta JSON: {missing_keys}")
            return {
                "areas_innovacion": [],
                "impacto_sostenibilidad": 0,
                "impacto_viabilidad": 0,
                "impacto_diferenciacion": 0,
                "puntuacion_global": 0,
                "justificacion": "Error en el análisis: estructura JSON incompleta",
                "impacto": 0,
                "esfuerzo": 0,
                "viabilidad_tecnica": 0,
                "alineacion_estrategica": 0,
                "tiempo_implementacion": 0,
                "categoria": "Sin categoría",
                "beneficios": [],
                "riesgos": [],
                "recomendaciones": []
            }
        
        return analysis
    except Exception as e:
        st.error(f"Error en análisis AI: {str(e)}")
        return {
            "areas_innovacion": [],
            "impacto_sostenibilidad": 0,
            "impacto_viabilidad": 0,
            "impacto_diferenciacion": 0,
            "puntuacion_global": 0,
            "justificacion": f"Error en el análisis: {str(e)}",
            "impacto": 0,
            "esfuerzo": 0,
            "viabilidad_tecnica": 0,
            "alineacion_estrategica": 0,
            "tiempo_implementacion": 0,
            "categoria": "Sin categoría",
            "beneficios": [],
            "riesgos": [],
            "recomendaciones": []
        }

# Función para procesar todas las iniciativas
def process_initiatives(data, sheet_url):
    resultados = []
    total = len(data)
    
    # Cargar datos analizados previamente
    analyzed_data = load_analyzed_data(sheet_url)
    existing_ids = set(analyzed_data['initiative_id']) if analyzed_data is not None else set()
    
    for i, row in data.iterrows():
        initiative_id = row['initiative_id']
        
        # Verificar si la iniciativa ya fue analizada
        if initiative_id in existing_ids:
            st.write(f"Iniciativa '{row['nombre_iniciativa']}' ya analizada, recuperando datos...")
            existing_row = analyzed_data[analyzed_data['initiative_id'] == initiative_id].iloc[0]
            result = existing_row.to_dict()
            resultados.append(result)
        else:
            with st.spinner(f"Analizando iniciativa {i + 1} de {total}..."):
                analysis = analyze_initiative_with_ai(row["descripcion"])
                
                if isinstance(analysis, dict):
                    result = {
                        "initiative_id": initiative_id,
                        "timestamp": row["timestamp"],
                        "nombre_iniciativa": row["nombre_iniciativa"],
                        "descripcion": row["descripcion"],
                        "proponente": row["proponente"],
                        "telefono": row["telefono"],
                        "correo": row["correo"],
                        "publico_interes": row["publico_interes"],
                        "area_proceso": row["area_proceso"],
                        "organizacion": row["organizacion"],
                        **analysis,
                        "cuadrante": categorizar_cuadrante(analysis.get("impacto", 0), analysis.get("esfuerzo", 0))
                    }
                    resultados.append(result)
    
    # Convertir resultados a DataFrame
    result_df = pd.DataFrame(resultados)
    
    # Guardar nuevos análisis en Google Sheets
    if not result_df.empty:
        save_analyzed_data(sheet_url, result_df)
    
    return result_df

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
                    
                    # Intentar cargar datos analizados
                    with st.spinner("Verificando datos analizados..."):
                        analyzed_data = load_analyzed_data(sheet_url)
                        if analyzed_data is not None:
                            # Filtrar iniciativas que necesitan análisis
                            existing_ids = set(analyzed_data['initiative_id'])
                            new_initiatives = df[~df['initiative_id'].isin(existing_ids)]
                            if new_initiatives.empty:
                                st.session_state.analyzed_data = analyzed_data
                                st.success("✅ Todas las iniciativas ya están analizadas")
                            else:
                                with st.spinner(f"Analizando {len(new_initiatives)} nuevas iniciativas..."):
                                    new_analyzed_data = process_initiatives(new_initiatives, sheet_url)
                                    # Combinar datos analizados existentes con nuevos
                                    st.session_state.analyzed_data = pd.concat([analyzed_data, new_analyzed_data], ignore_index=True)
                                    st.success("✅ Análisis completado para nuevas iniciativas")
                        else:
                            # Si no hay datos analizados, procesar todo
                            with st.spinner("Analizando todas las iniciativas..."):
                                st.session_state.analyzed_data = process_initiatives(df, sheet_url)
                                st.success("✅ Análisis completado")
                else:
                    st.error("❌ No se pudieron cargar los datos")
        
        # Botón para forzar re-análisis
        if st.session_state.data is not None:
            if st.button("🤖 Forzar Re-análisis de Iniciativas", type="secondary"):
                with st.spinner("Analizando todas las iniciativas..."):
                    st.session_state.analyzed_data = process_initiatives(st.session_state.data, sheet_url)
                    st.success("✅ Análisis completado")
        
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
    if st.session_state.data is not None and st.session_state.analyzed_data is not None:
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
            df['puntuacion_global'] = pd.to_numeric(df['puntuacion_global'], errors='coerce')
            df_sorted = df.dropna(subset=['puntuacion_global'])
            top_initiatives = df_sorted.nlargest(5, 'puntuacion_global')[
                ['timestamp', 'nombre_iniciativa', 'descripcion', 'puntuacion_global', 'proponente', 'categoria', 'impacto']
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
            
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("🔍 Buscar iniciativa", placeholder="Buscar por nombre o descripción...")
            with col2:
                sort_by = st.selectbox("Ordenar por", ["Puntuación", "Fecha", "Impacto", "Esfuerzo"])
            
            if search_term:
                mask = (
                    df['nombre_iniciativa'].str.contains(search_term, case=False, na=False) |
                    df['descripcion'].str.contains(search_term, case=False, na=False)
                )
                df_filtered = df[mask]
            else:
                df_filtered = df
            
            sort_mapping = {
                "Puntuación": "puntuacion_global",
                "Fecha": "timestamp",
                "Impacto": "impacto",
                "Esfuerzo": "esfuerzo"
            }
            df_filtered = df_filtered.sort_values(by=sort_mapping[sort_by], ascending=False)
            
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
                        st.markdown("**Evaluación:**")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Impacto", f"{row['impacto']:.0f}/10")
                            st.metric("Viabilidad", f"{row['viabilidad_tecnica']:.0f}/10")
                        with col_b:
                            st.metric("Esfuerzo", f"{row['esfuerzo']:.0f}/10")
                            st.metric("Alineación", f"{row['alineacion_estrategica']:.0f}/10")
                        
                        st.metric("Tiempo Est.", f"{row['tiempo_implementacion']} meses")
                        
                        cuadrante_color = {
                            "Quick Wins": "🟢",
                            "Proyectos Estratégicos": "🔵",
                            "Fill Ins": "🟡",
                            "Difíciles de Justificar": "🔴"
                        }
                        st.markdown(f"**Cuadrante:** {cuadrante_color.get(row['cuadrante'], '')} {row['cuadrante']}")
                    
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
                    
                    with st.container():
                        st.divider()
                        st.caption(f"📧 {row['correo']} | 📱 {row['telefono']}")
        
        with tab3:
            st.header("📈 Matriz Esfuerzo-Impacto")
            
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
            
            fig_matrix.add_hline(y=7, line_dash="dash", line_color="gray", opacity=0.5)
            fig_matrix.add_vline(x=4, line_dash="dash", line_color="gray", opacity=0.5)
            
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
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Puntuación Promedio", f"{df['puntuacion_global'].mean():.1f}/100")
                        with col2:
                            st.metric("Impacto Promedio", f"{df['impacto'].mean():.1f}/10")
                        with col3:
                            st.metric("Tiempo Promedio Implementación", f"{df['tiempo_implementacion'].mean():.1f} meses")
                        
                        st.markdown("### 🏆 Top 5 Iniciativas Recomendadas")
                        top_5 = df.nlargest(5, 'puntuacion_global')
                        for idx, row in top_5.iterrows():
                            st.markdown(f"**{idx+1}. {row['nombre_iniciativa']}**")
                            st.write(f"   - Proponente: {row['proponente']}")
                            st.write(f"   - Puntuación: {row['puntuacion_global']:.0f}/100")
                            st.write(f"   - Cuadrante: {row['cuadrante']}")
                        
                        st.markdown("### 📈 Distribución por Categorías")
                        cat_dist = df['categoria'].value_counts()
                        for cat, count in cat_dist.items():
                            st.write(f"- **{cat}:** {count} iniciativas ({count/len(df)*100:.1f}%)")
                        
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
                            
                            st.markdown("**Top 3 Iniciativas:**")
                            for idx, row in df_cat.nlargest(3, 'puntuacion_global').iterrows():
                                st.write(f"• {row['nombre_iniciativa']} (Puntuación: {row['puntuacion_global']:.0f})")
                            
                            st.divider()
                    
                    elif tipo_informe == "Reporte de Viabilidad":
                        st.markdown("## 🎯 Reporte de Viabilidad Técnica")
                        
                        st.markdown("### ✅ Iniciativas de Alta Viabilidad (≥8/10)")
                        high_viability = df[df['viabilidad_tecnica'] >= 8].sort_values('viabilidad_tecnica', ascending=False)
                        
                        for idx, row in high_viability.iterrows():
                            with st.expander(f"{row['nombre_iniciativa']} - Viabilidad: {row['viabilidad_tecnica']:.0f}/10"):
                                st.write(f"**Descripción:** {row['descripcion']}")
                                st.write(f"**Tiempo estimado:** {row['tiempo_implementacion']} meses")
                                st.write(f"**Impacto esperado:** {row['impacto']:.0f}/10")
                        
                        st.markdown("### ⚠️ Iniciativas que Requieren Análisis Adicional (5-7/10)")
                        medium_viability = df[(df['viabilidad_tecnica'] >= 5) & (df['viabilidad_tecnica'] < 8)]
                        
                        if len(medium_viability) > 0:
                            st.write(f"Se identificaron {len(medium_viability)} iniciativas que requieren evaluación adicional:")
                            for idx, row in medium_viability.iterrows():
                                st.write(f"• {row['nombre_iniciativa']} - Viabilidad: {row['viabilidad_tecnica']:.0f}/10")
                    
                    else:  # Informe Completo
                        st.markdown("## 📋 Informe Completo de Iniciativas de Innovación")
                        st.markdown(f"**Generado el:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                        
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Descargar datos completos (CSV)",
                            data=csv,
                            file_name=f"iniciativas_innovacion_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                        
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
            
            iniciativa_seleccionada = st.selectbox(
                "Selecciona una iniciativa para análisis detallado",
                df['nombre_iniciativa'].tolist()
            )
            
            if iniciativa_seleccionada:
                row = df[df['nombre_iniciativa'] == iniciativa_seleccionada].iloc[0]
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"### {row['nombre_iniciativa']}")
                    st.write(f"**Proponente:** {row['proponente']}")
                    st.write(f"**Área:** {row['area_proceso']}")
                    st.write(f"**Fecha de propuesta:** {row['timestamp'].strftime('%Y-%m-%d')}")
                    
                    st.markdown("**Descripción completa:**")
                    st.info(row['descripcion'])
                
                with col2:
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
                    
                    st.markdown("#### 💰 Recursos Estimados")
                    if row['impacto'] >= 8:
                        st.write("• **Prioridad:** Alta - Asignar recursos dedicados")
                    elif row['impacto'] >= 5:
                        st.write("• **Prioridad:** Media - Recursos compartidos")
                    else:
                        st.write("• **Prioridad:** Baja - Recursos mínimos")
                    
                    st.write(f"• **Equipo sugerido:** {2 if row['esfuerzo'] < 5 else 3 if row['esfuerzo'] < 8 else 5} personas")
                    st.write(f"• **Área líder:** {row['area_proceso']}")
                
                st.markdown("### 📞 Información de Contacto")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📧 **Email:** {row['correo']}")
                with col2:
                    st.write(f"📱 **Teléfono:** {row['telefono']}")
    
    else:
        st.info("👋 ¡Bienvenido al Sistema de Análisis de Iniciativas de Innovación!")
        st.markdown("""
        Para comenzar:
        1. Ingresa la URL de tu Google Sheets en la barra lateral
        2. Haz clic en **Cargar/Actualizar Datos**
        3. Los datos se analizarán automáticamente si es necesario
        
        El sistema analizará automáticamente cada iniciativa y proporcionará:
        - 📊 Dashboard con métricas clave
        - 📈 Matriz de priorización Esfuerzo-Impacto
        - 📋 Vista detallada de cada iniciativa
        - 📑 Generación de informes personalizados
        - 🔍 Análisis profundo con recomendaciones
        """)
        
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
            3. Se verifica si las iniciativas ya fueron analizadas
            4. Las nuevas iniciativas se analizan con IA y se guardan
            5. Los resultados se visualizan en dashboards interactivos
            """)

if __name__ == "__main__":
    main()
