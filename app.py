import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
import openai
import json
import time

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Iniciativas de Innovación",
    page_icon="💡",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .initiative-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.title("🚀 Análisis de Iniciativas de Innovación")
st.markdown("---")

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # API Keys
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    
    # Google Sheets Configuration
    st.subheader("📊 Configuración Google Sheets")
    spreadsheet_id = st.text_input("ID de la hoja de cálculo")
    sheet_name = st.text_input("Nombre de la hoja", value="Respuestas")
    
    # Credenciales de Google (en producción, usar secrets)
    use_demo_data = st.checkbox("Usar datos de demostración", value=True)
    
    # Botón de actualización
    if st.button("🔄 Actualizar datos"):
        st.rerun()

# Funciones auxiliares
def get_google_sheets_data(spreadsheet_id, sheet_name, credentials):
    """Obtiene datos de Google Sheets"""
    try:
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:Z"
        ).execute()
        values = result.get('values', [])
        
        if not values:
            return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

def generate_demo_data():
    """Genera datos de demostración"""
    data = {
        'Timestamp': [
            '2025-01-15 10:30:00', '2025-01-15 11:45:00', '2025-01-15 14:20:00',
            '2025-01-16 09:15:00', '2025-01-16 10:00:00', '2025-01-16 15:30:00',
            '2025-01-17 08:45:00', '2025-01-17 11:20:00', '2025-01-17 13:00:00',
            '2025-01-18 10:10:00'
        ],
        'Nombre': [
            'Ana García', 'Carlos López', 'María Rodríguez', 'Juan Pérez',
            'Laura Martínez', 'Pedro Sánchez', 'Sofia Hernández', 'Diego Torres',
            'Carmen Ruiz', 'Andrés Morales'
        ],
        'Departamento': [
            'Ventas', 'IT', 'Marketing', 'Operaciones', 'RRHH',
            'IT', 'Finanzas', 'Marketing', 'Ventas', 'IT'
        ],
        'Título de la iniciativa': [
            'CRM inteligente con IA para predicción de ventas',
            'Automatización de procesos de testing con ML',
            'Campaña de marketing personalizada con análisis predictivo',
            'Optimización de rutas de entrega con algoritmos genéticos',
            'Plataforma de bienestar empleados con gamificación',
            'Chatbot interno para soporte técnico',
            'Dashboard financiero en tiempo real',
            'Sistema de recomendación de contenido para clientes',
            'App móvil para gestión de clientes en campo',
            'Migración a arquitectura de microservicios'
        ],
        'Descripción': [
            'Implementar un CRM que use IA para predecir qué clientes tienen mayor probabilidad de compra',
            'Crear suite de testing automatizado que aprenda de errores previos para mejorar cobertura',
            'Desarrollar sistema que personalice campañas según comportamiento histórico del cliente',
            'Sistema que calcule rutas óptimas considerando tráfico, clima y prioridades de entrega',
            'App que incentive hábitos saludables mediante puntos y recompensas',
            'Bot inteligente que resuelva consultas técnicas frecuentes del personal',
            'Visualización en tiempo real de KPIs financieros con alertas automáticas',
            'Motor de recomendaciones basado en historial y preferencias del cliente',
            'Aplicación móvil offline-first para gestión de visitas comerciales',
            'Modernizar arquitectura monolítica actual a microservicios escalables'
        ],
        'Beneficios esperados': [
            'Aumento del 30% en conversión de ventas',
            'Reducción del 50% en tiempo de testing',
            'Incremento del 25% en engagement de clientes',
            'Ahorro del 20% en costos de combustible',
            'Reducción del 15% en ausentismo laboral',
            'Disminución del 40% en tickets de soporte',
            'Detección temprana de desviaciones presupuestarias',
            'Aumento del 35% en ventas cruzadas',
            'Mejora del 30% en productividad de vendedores',
            'Reducción del 60% en tiempo de despliegue'
        ],
        'Recursos necesarios': [
            'Licencias de IA, 2 desarrolladores, 3 meses',
            '1 ingeniero QA senior, herramientas de testing, 2 meses',
            'Plataforma de marketing automation, 1 analista, 2 meses',
            'Servicio de mapas, 2 desarrolladores, 4 meses',
            'Diseñador UX, 2 desarrolladores, partner de wellness, 3 meses',
            'Plataforma de chatbot, 1 desarrollador, 1 mes',
            'Licencias de BI, 1 analista, 2 meses',
            'Infraestructura ML, 2 data scientists, 4 meses',
            '2 desarrolladores móviles, diseñador, 3 meses',
            'Equipo de 5 desarrolladores, consultor de arquitectura, 6 meses'
        ],
        'Tiempo estimado': [
            '3 meses', '2 meses', '2 meses', '4 meses', '3 meses',
            '1 mes', '2 meses', '4 meses', '3 meses', '6 meses'
        ],
        'Presupuesto estimado': [
            '$25,000', '$15,000', '$20,000', '$35,000', '$30,000',
            '$8,000', '$12,000', '$40,000', '$25,000', '$80,000'
        ]
    }
    
    return pd.DataFrame(data)

def analyze_initiative_with_ai(initiative, openai_api_key):
    """Analiza una iniciativa usando OpenAI"""
    if not openai_api_key:
        # Análisis simple sin IA
        return {
            "viabilidad": np.random.randint(60, 95),
            "impacto": np.random.randint(1, 6),
            "esfuerzo": np.random.randint(1, 6),
            "categoria": np.random.choice(["Tecnología", "Procesos", "Cultura", "Producto"]),
            "riesgos": ["Falta de recursos", "Resistencia al cambio"],
            "recomendaciones": ["Iniciar con piloto", "Formar equipo multidisciplinario"]
        }
    
    try:
        openai.api_key = openai_api_key
        
        prompt = f"""
        Analiza la siguiente iniciativa de innovación y proporciona una evaluación en formato JSON:
        
        Título: {initiative['Título de la iniciativa']}
        Descripción: {initiative['Descripción']}
        Beneficios: {initiative['Beneficios esperados']}
        Recursos: {initiative['Recursos necesarios']}
        Tiempo: {initiative['Tiempo estimado']}
        Presupuesto: {initiative['Presupuesto estimado']}
        
        Responde con un JSON que contenga:
        - viabilidad: puntuación de 0-100
        - impacto: del 1-5 (5 siendo el mayor impacto)
        - esfuerzo: del 1-5 (5 siendo el mayor esfuerzo)
        - categoria: clasificación principal (Tecnología, Procesos, Cultura, Producto)
        - riesgos: lista de 2-3 riesgos principales
        - recomendaciones: lista de 2-3 recomendaciones
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        return json.loads(response.choices[0].message.content)
    
    except Exception as e:
        st.error(f"Error en análisis con IA: {e}")
        return analyze_initiative_with_ai(initiative, None)

# Cargar datos
if use_demo_data:
    df = generate_demo_data()
    st.info("📊 Usando datos de demostración")
else:
    if spreadsheet_id and sheet_name:
        # En producción, cargar credenciales apropiadamente
        df = pd.DataFrame()  # Placeholder
        st.warning("⚠️ Configura las credenciales de Google para conectar con Sheets real")
    else:
        df = pd.DataFrame()
        st.warning("⚠️ Configura el ID de la hoja de cálculo en la barra lateral")

if not df.empty:
    # Análisis de cada iniciativa
    if 'analyzed_data' not in st.session_state:
        st.session_state.analyzed_data = []
        
        with st.spinner("🤖 Analizando iniciativas con IA..."):
            progress_bar = st.progress(0)
            for idx, row in df.iterrows():
                analysis = analyze_initiative_with_ai(row, openai_api_key)
                row_dict = row.to_dict()
                row_dict.update(analysis)
                st.session_state.analyzed_data.append(row_dict)
                progress_bar.progress((idx + 1) / len(df))
            progress_bar.empty()
    
    analyzed_df = pd.DataFrame(st.session_state.analyzed_data)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Iniciativas", len(analyzed_df))
    
    with col2:
        avg_viability = analyzed_df['viabilidad'].mean()
        st.metric("Viabilidad Promedio", f"{avg_viability:.1f}%")
    
    with col3:
        high_impact = len(analyzed_df[analyzed_df['impacto'] >= 4])
        st.metric("Alto Impacto", high_impact)
    
    with col4:
        low_effort = len(analyzed_df[analyzed_df['esfuerzo'] <= 2])
        st.metric("Bajo Esfuerzo", low_effort)
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💡 Iniciativas", "📈 Análisis", "📋 Informes"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Matriz Esfuerzo-Impacto
            fig_matrix = go.Figure()
            
            # Definir colores por cuadrante
            colors = []
            for _, row in analyzed_df.iterrows():
                if row['impacto'] >= 3 and row['esfuerzo'] <= 3:
                    colors.append('#00cc44')  # Quick wins
                elif row['impacto'] >= 3 and row['esfuerzo'] > 3:
                    colors.append('#ff9900')  # Proyectos estratégicos
                elif row['impacto'] < 3 and row['esfuerzo'] <= 3:
                    colors.append('#3366cc')  # Fill-ins
                else:
                    colors.append('#cc0000')  # Evitar
            
            fig_matrix.add_trace(go.Scatter(
                x=analyzed_df['esfuerzo'],
                y=analyzed_df['impacto'],
                mode='markers+text',
                marker=dict(size=15, color=colors),
                text=analyzed_df['Título de la iniciativa'].str[:20] + '...',
                textposition="top center",
                textfont=dict(size=9),
                hovertemplate='<b>%{text}</b><br>Esfuerzo: %{x}<br>Impacto: %{y}<extra></extra>'
            ))
            
            # Añadir cuadrantes
            fig_matrix.add_shape(type="line", x0=3, y0=0, x1=3, y1=5,
                                line=dict(color="gray", width=1, dash="dash"))
            fig_matrix.add_shape(type="line", x0=0, y0=3, x1=5, y1=3,
                                line=dict(color="gray", width=1, dash="dash"))
            
            # Etiquetas de cuadrantes
            fig_matrix.add_annotation(x=1.5, y=4.5, text="Quick Wins", showarrow=False,
                                     font=dict(size=12, color="green"))
            fig_matrix.add_annotation(x=4, y=4.5, text="Estratégicos", showarrow=False,
                                     font=dict(size=12, color="orange"))
            fig_matrix.add_annotation(x=1.5, y=1.5, text="Fill-ins", showarrow=False,
                                     font=dict(size=12, color="blue"))
            fig_matrix.add_annotation(x=4, y=1.5, text="Evitar", showarrow=False,
                                     font=dict(size=12, color="red"))
            
            fig_matrix.update_layout(
                title="Matriz Esfuerzo-Impacto",
                xaxis_title="Esfuerzo →",
                yaxis_title="Impacto →",
                xaxis=dict(range=[0.5, 5.5]),
                yaxis=dict(range=[0.5, 5.5]),
                height=400
            )
            
            st.plotly_chart(fig_matrix, use_container_width=True)
        
        with col2:
            # Distribución por categorías
            category_counts = analyzed_df['categoria'].value_counts()
            fig_pie = px.pie(values=category_counts.values, names=category_counts.index,
                            title="Distribución por Categorías",
                            color_discrete_map={
                                'Tecnología': '#1f77b4',
                                'Procesos': '#ff7f0e',
                                'Cultura': '#2ca02c',
                                'Producto': '#d62728'
                            })
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Timeline de iniciativas
        st.subheader("📅 Timeline de Propuestas")
        analyzed_df['Timestamp'] = pd.to_datetime(analyzed_df['Timestamp'])
        
        fig_timeline = px.scatter(analyzed_df, x='Timestamp', y='Departamento',
                                 size='viabilidad', color='categoria',
                                 hover_data=['Título de la iniciativa', 'viabilidad'],
                                 title="Iniciativas por Departamento en el Tiempo")
        fig_timeline.update_layout(height=300)
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Top iniciativas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top 5 - Mayor Viabilidad")
            top_viable = analyzed_df.nlargest(5, 'viabilidad')[['Título de la iniciativa', 'viabilidad', 'Departamento']]
            st.dataframe(top_viable, hide_index=True)
        
        with col2:
            st.subheader("⚡ Top 5 - Quick Wins")
            quick_wins = analyzed_df[(analyzed_df['impacto'] >= 3) & (analyzed_df['esfuerzo'] <= 3)]
            quick_wins = quick_wins.nlargest(5, 'viabilidad')[['Título de la iniciativa', 'impacto', 'esfuerzo']]
            st.dataframe(quick_wins, hide_index=True)
    
    with tab2:
        st.subheader("💡 Detalle de Iniciativas")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dept_filter = st.multiselect("Departamento", analyzed_df['Departamento'].unique())
        
        with col2:
            cat_filter = st.multiselect("Categoría", analyzed_df['categoria'].unique())
        
        with col3:
            viab_filter = st.slider("Viabilidad mínima", 0, 100, 50)
        
        # Aplicar filtros
        filtered_df = analyzed_df.copy()
        if dept_filter:
            filtered_df = filtered_df[filtered_df['Departamento'].isin(dept_filter)]
        if cat_filter:
            filtered_df = filtered_df[filtered_df['categoria'].isin(cat_filter)]
        filtered_df = filtered_df[filtered_df['viabilidad'] >= viab_filter]
        
        # Mostrar iniciativas
        for idx, row in filtered_df.iterrows():
            with st.expander(f"{row['Título de la iniciativa']} - {row['Nombre']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Viabilidad", f"{row['viabilidad']}%")
                    st.metric("Categoría", row['categoria'])
                
                with col2:
                    st.metric("Impacto", f"{row['impacto']}/5")
                    st.metric("Departamento", row['Departamento'])
                
                with col3:
                    st.metric("Esfuerzo", f"{row['esfuerzo']}/5")
                    st.metric("Tiempo", row['Tiempo estimado'])
                
                st.markdown("**Descripción:**")
                st.write(row['Descripción'])
                
                st.markdown("**Beneficios esperados:**")
                st.write(row['Beneficios esperados'])
                
                st.markdown("**Recursos necesarios:**")
                st.write(row['Recursos necesarios'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🚨 Riesgos identificados:**")
                    for risk in row['riesgos']:
                        st.write(f"• {risk}")
                
                with col2:
                    st.markdown("**✅ Recomendaciones:**")
                    for rec in row['recomendaciones']:
                        st.write(f"• {rec}")
    
    with tab3:
        st.subheader("📈 Análisis Detallado")
        
        # Análisis por departamento
        dept_analysis = analyzed_df.groupby('Departamento').agg({
            'viabilidad': 'mean',
            'impacto': 'mean',
            'esfuerzo': 'mean',
            'Título de la iniciativa': 'count'
        }).round(2)
        dept_analysis.columns = ['Viabilidad Promedio', 'Impacto Promedio', 'Esfuerzo Promedio', 'Cantidad']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_dept = px.bar(dept_analysis.reset_index(), x='Departamento', y='Cantidad',
                             title="Iniciativas por Departamento",
                             color='Cantidad', color_continuous_scale='Blues')
            st.plotly_chart(fig_dept, use_container_width=True)
        
        with col2:
            fig_viab_dept = px.bar(dept_analysis.reset_index(), x='Departamento', y='Viabilidad Promedio',
                                  title="Viabilidad Promedio por Departamento",
                                  color='Viabilidad Promedio', color_continuous_scale='Greens')
            st.plotly_chart(fig_viab_dept, use_container_width=True)
        
        # Correlación entre variables
        st.subheader("🔍 Análisis de Correlaciones")
        
        # Convertir presupuesto a numérico
        analyzed_df['Presupuesto_num'] = analyzed_df['Presupuesto estimado'].str.replace('$', '').str.replace(',', '').astype(float)
        
        correlation_data = analyzed_df[['viabilidad', 'impacto', 'esfuerzo', 'Presupuesto_num']]
        
        fig_corr = px.scatter_matrix(correlation_data,
                                     dimensions=['viabilidad', 'impacto', 'esfuerzo', 'Presupuesto_num'],
                                     title="Matriz de Correlación",
                                     height=600)
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Distribución de viabilidad
        fig_hist = px.histogram(analyzed_df, x='viabilidad', nbins=20,
                               title="Distribución de Puntajes de Viabilidad",
                               labels={'viabilidad': 'Viabilidad (%)', 'count': 'Cantidad'})
        fig_hist.update_traces(marker_color='lightblue', marker_line_color='darkblue', marker_line_width=1)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with tab4:
        st.subheader("📋 Generación de Informes")
        
        report_type = st.selectbox("Tipo de informe", 
                                  ["Resumen Ejecutivo", "Informe Detallado", "Reporte Quick Wins", "Análisis por Departamento"])
        
        if st.button("📄 Generar Informe"):
            with st.spinner("Generando informe..."):
                time.sleep(2)  # Simular generación
                
                if report_type == "Resumen Ejecutivo":
                    st.markdown("### 📊 Resumen Ejecutivo - Iniciativas de Innovación")
                    st.markdown(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d')}")
                    st.markdown("---")
                    
                    st.markdown(f"""
                    **Resumen General:**
                    - Total de iniciativas recibidas: {len(analyzed_df)}
                    - Viabilidad promedio: {analyzed_df['viabilidad'].mean():.1f}%
                    - Iniciativas de alto impacto: {len(analyzed_df[analyzed_df['impacto'] >= 4])}
                    - Quick wins identificados: {len(analyzed_df[(analyzed_df['impacto'] >= 3) & (analyzed_df['esfuerzo'] <= 3)])}
                    
                    **Distribución por Categorías:**
                    """)
                    
                    for cat, count in analyzed_df['categoria'].value_counts().items():
                        st.markdown(f"- {cat}: {count} iniciativas ({count/len(analyzed_df)*100:.1f}%)")
                    
                    st.markdown("""
                    **Recomendaciones Principales:**
                    1. Priorizar las iniciativas identificadas como Quick Wins
                    2. Formar equipos multidisciplinarios para proyectos estratégicos
                    3. Asignar recursos a las iniciativas con viabilidad superior al 80%
                    """)
                    
                    st.success("✅ Informe generado exitosamente")
                
                elif report_type == "Reporte Quick Wins":
                    st.markdown("### ⚡ Reporte de Quick Wins")
                    quick_wins_df = analyzed_df[(analyzed_df['impacto'] >= 3) & (analyzed_df['esfuerzo'] <= 3)]
                    quick_wins_df = quick_wins_df.sort_values('viabilidad', ascending=False)
                    
                    for idx, row in quick_wins_df.head(10).iterrows():
                        st.markdown(f"""
                        **{idx+1}. {row['Título de la iniciativa']}**
                        - Propuesto por: {row['Nombre']} ({row['Departamento']})
                        - Viabilidad: {row['viabilidad']}%
                        - Impacto: {row['impacto']}/5 | Esfuerzo: {row['esfuerzo']}/5
                        - Presupuesto: {row['Presupuesto estimado']}
                        - Tiempo: {row['Tiempo estimado']}
                        ---
                        """)
        
        # Exportar datos
        st.subheader("💾 Exportar Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = analyzed_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV completo",
                data=csv,
                file_name=f"iniciativas_innovacion_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Preparar datos para Excel (simplificado)
            excel_data = analyzed_df[['Timestamp', 'Nombre', 'Departamento', 'Título de la iniciativa',
                                     'viabilidad', 'impacto', 'esfuerzo', 'categoria']].copy()
            
            csv_excel = excel_data.to_csv(index=False)
            st.download_button(
                label="📥 Descargar resumen",
                data=csv_excel,
                file_name=f"resumen_iniciativas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

else:
    st.warning("⚠️ No hay datos disponibles. Configura la conexión a Google Sheets o activa los datos de demostración.")
    
    # Mostrar estructura esperada del formulario
    st.info("""
    ### 📝 Estructura del Google Forms sugerida:
    
    1. **Información del solicitante:**
       - Nombre completo
       - Correo electrónico
       - Departamento
    
    2. **Detalles de la iniciativa:**
       - Título de la iniciativa
       - Descripción detallada
       - Beneficios esperados
       - Recursos necesarios
       - Tiempo estimado de implementación
       - Presupuesto estimado
    
    3. **Información adicional:**
       - ¿Requiere colaboración con otros departamentos?
       - ¿Existen riesgos identificados?
       - Nivel de prioridad (Alta/Media/Baja)
    """)

# Footer
st.markdown("---")
st.markdown("💡 **Sistema de Análisis de Iniciativas de Innovación** | Desarrollado con Streamlit")
