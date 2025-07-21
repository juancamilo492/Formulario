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

# URL de tu Google Sheets
SHEET_ID = "1yWHTveQlQEKi7fLdDxxKPLdEjGvD7PaTzAbRYvSBEp0"

# Estilos CSS
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

# Funciones auxiliares
def get_column_name(df, possible_names):
    for name in possible_names:
        if name in df.columns:
            return name
    return None

def calculate_scores(df):
    try:
        if df.empty:
            return df
        
        df = df.copy()
        show_debug = st.session_state.get('show_debug', False)
        
        if show_debug:
            st.write(f"Columnas: {list(df.columns)}")
            st.write(f"Filas: {len(df)}")
        
        df.columns = df.columns.str.strip()
        
        column_mapping = {
            'Valor estratégico': 'valor_estrategico',
            'Nivel de impacto': 'nivel_impacto', 
            'Viabilidad técnica': 'viabilidad_tecnica',
            'Costo-beneficio': 'costo_beneficio',
            'Innovación / disrupción': 'innovacion_disrupcion',
            'Escalabilidad / transversalidad': 'escalabilidad_transversalidad',
            'Tiempo de implementación': 'tiempo_implementacion'
        }
        
        for col_original, col_clean in column_mapping.items():
            if col_original in df.columns:
                df[col_clean] = pd.to_numeric(df[col_original], errors='coerce').fillna(0)
            else:
                similar_cols = [c for c in df.columns if col_original.lower().replace(' ', '') in c.lower().replace(' ', '')]
                if similar_cols:
                    df[col_clean] = pd.to_numeric(df[similar_cols[0]], errors='coerce').fillna(0)
                else:
                    df[col_clean] = 0
        
        df['Puntuación Total'] = (
            df['valor_estrategico'] + df['nivel_impacto'] + 
            df['viabilidad_tecnica'] + df['costo_beneficio'] + 
            df['innovacion_disrupcion'] + df['escalabilidad_transversalidad']
        )
        
        df['Facilidad Implementación'] = 6 - df['tiempo_implementacion']
        
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
        df['Ranking'] = df['Puntuación Total'].rank(method='dense', ascending=False).astype(int)
        
        # Mapear columnas de texto
        area_col = get_column_name(df, ['Selecciona el área o proceso al cual perteneces', 'Área', 'Area'])
        df['Área'] = df[area_col].astype(str).str.strip() if area_col else 'Sin especificar'
        
        name_col = get_column_name(df, ['Nombre de la idea o iniciativa', 'Iniciativa', 'Idea'])
        df['Nombre_Iniciativa'] = df[name_col].astype(str).str.strip() if name_col else df.index.map(lambda x: f'Iniciativa {x+1}')
        
        author_col = get_column_name(df, ['Nombre completo', 'Nombre', 'Autor'])
        df['Nombre_Completo'] = df[author_col].astype(str).str.strip() if author_col else 'Sin especificar'
        
        return df
        
    except Exception as e:
        st.error(f"Error en calculate_scores: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_google_sheets_data():
    urls_to_try = [
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0",
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    ]
    
    for i, csv_url in enumerate(urls_to_try):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible)'}
            response = requests.get(csv_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            if len(response.text.strip()) > 10:
                df = pd.read_csv(StringIO(response.text))
                if len(df) > 0:
                    return df, True, f"Conectado exitosamente (método {i+1})"
        except Exception:
            continue
    
    return pd.DataFrame(), False, "No se pudo conectar a Google Sheets"

def load_demo_data():
    np.random.seed(42)
    areas = ["Tecnología", "Operaciones", "Finanzas", "Marketing", "RRHH"]
    
    data = []
    for i in range(15):
        data.append({
            'Nombre completo': f'Usuario {i+1}',
            'Selecciona el área o proceso al cual perteneces': np.random.choice(areas),
            'Nombre de la idea o iniciativa': f'Iniciativa Demo {i+1}',
            'Valor estratégico': np.random.randint(1, 6),
            'Nivel de impacto': np.random.randint(1, 6),
            'Viabilidad técnica': np.random.randint(1, 6),
            'Costo-beneficio': np.random.randint(1, 6),
            'Innovación / disrupción': np.random.randint(1, 6),
            'Escalabilidad / transversalidad': np.random.randint(1, 6),
            'Tiempo de implementación': np.random.randint(1, 6)
        })
    
    return pd.DataFrame(data)

# Interfaz de usuario
with st.sidebar:
    st.header("⚙️ Configuración")
    
    data_source = st.radio(
        "📊 Fuente de datos:",
        ["🔗 Google Sheets", "📁 Archivo CSV", "🧪 Demo"],
    )
    
    if data_source == "📁 Archivo CSV":
        uploaded_file = st.file_uploader("Selecciona CSV", type=['csv'])
    
    if data_source == "🔗 Google Sheets":
        if st.button("🔄 Actualizar"):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    min_score_filter = st.slider("Puntuación mínima", 0, 30, 0)
    show_debug = st.checkbox("🔧 Debug", value=False)
    show_zeros = st.checkbox("Incluir sin evaluar", value=True)
    
    st.session_state['show_debug'] = show_debug

# Título
st.markdown("""
<div style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
           padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
    <h1 style='color: white; margin: 0;'>💡 Análisis de Iniciativas de Innovación</h1>
    <p style='color: #f8f9fa; margin: 0.5rem 0 0 0; font-size: 1.2rem;'>Dashboard Ejecutivo - Alico</p>
</div>
""", unsafe_allow_html=True)

# Cargar datos
if data_source == "🔗 Google Sheets":
    df_raw, success, message = load_google_sheets_data()
    if success:
        st.markdown(f'<div class="connection-status success">✅ {message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="connection-status error">❌ {message}</div>', unsafe_allow_html=True)
        df_raw = load_demo_data()
elif data_source == "📁 Archivo CSV":
    if 'uploaded_file' in locals() and uploaded_file:
        df_raw = pd.read_csv(uploaded_file)
        st.markdown('<div class="connection-status success">✅ CSV cargado</div>', unsafe_allow_html=True)
    else:
        df_raw = load_demo_data()
        st.markdown('<div class="connection-status warning">⬆️ Sube un CSV</div>', unsafe_allow_html=True)
else:
    df_raw = load_demo_data()
    st.markdown('<div class="connection-status warning">🧪 Datos demo</div>', unsafe_allow_html=True)

if df_raw.empty:
    st.error("No hay datos disponibles")
    st.stop()

# Procesar datos
df = calculate_scores(df_raw)

if not show_zeros:
    df = df[df['Puntuación Total'] > 0]
df = df[df['Puntuación Total'] >= min_score_filter]

if df.empty:
    st.warning("No hay datos con los filtros seleccionados")
    st.stop()

# Métricas principales
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f'<div class="metric-card"><h2 style="margin:0; color: white;">{len(df)}</h2><p style="margin:0; color: #f8f9fa;">Total</p></div>', unsafe_allow_html=True)

with col2:
    quick_wins = len(df[df['Clasificación'] == 'Quick Win'])
    st.markdown(f'<div class="metric-card"><h2 style="margin:0; color: white;">{quick_wins}</h2><p style="margin:0; color: #f8f9fa;">Quick Wins</p></div>', unsafe_allow_html=True)

with col3:
    avg_score = df['Puntuación Total'].mean()
    st.markdown(f'<div class="metric-card"><h2 style="margin:0; color: white;">{avg_score:.1f}</h2><p style="margin:0; color: #f8f9fa;">Promedio</p></div>', unsafe_allow_html=True)

with col4:
    high_impact = len(df[df['nivel_impacto'] >= 4])
    st.markdown(f'<div class="metric-card"><h2 style="margin:0; color: white;">{high_impact}</h2><p style="margin:0; color: #f8f9fa;">Alto Impacto</p></div>', unsafe_allow_html=True)

with col5:
    strategic = len(df[df['Clasificación'] == 'Estratégica'])
    st.markdown(f'<div class="metric-card"><h2 style="margin:0; color: white;">{strategic}</h2><p style="margin:0; color: #f8f9fa;">Estratégicas</p></div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💡 Iniciativas", "📈 Análisis", "📋 Reportes"])

color_map = {
    'Quick Win': '#28a745',
    'Estratégica': '#ffc107', 
    'Relleno': '#17a2b8',
    'Baja Prioridad': '#dc3545'
}

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Matriz Esfuerzo-Impacto
        fig_matrix = go.Figure()
        
        for classification in df['Clasificación'].unique():
            subset = df[df['Clasificación'] == classification]
            fig_matrix.add_trace(go.Scatter(
                x=subset['Facilidad Implementación'],
                y=subset['nivel_impacto'],
                mode='markers',
                marker=dict(
                    size=subset['Puntuación Total'] / 1.5,
                    color=color_map.get(classification, '#666'),
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                name=classification,
                text=subset['Nombre_Iniciativa'].str[:25] + '...',
                hovertemplate='<b>%{text}</b><br>Impacto: %{y}<br>Facilidad: %{x}<extra></extra>'
            ))
        
        fig_matrix.add_hline(y=3.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig_matrix.add_vline(x=3.5, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig_matrix.update_layout(
            title="🎯 Matriz Facilidad vs Impacto",
            xaxis_title="Facilidad →",
            yaxis_title="Impacto →",
            height=500
        )
        
        st.plotly_chart(fig_matrix, use_container_width=True)
    
    with col2:
        # Distribución por área
        area_analysis = df.groupby('Área').agg({
            'Puntuación Total': ['mean', 'count'],
            'Clasificación': lambda x: (x == 'Quick Win').sum()
        }).round(1)
        
        area_analysis.columns = ['Promedio', 'Total', 'Quick Wins']
        area_analysis = area_analysis.reset_index()
        
        fig_areas = px.bar(
            area_analysis,
            x='Total',
            y='Área',
            color='Promedio',
            text='Quick Wins',
            title="📊 Iniciativas por Área"
        )
        
        st.plotly_chart(fig_areas, use_container_width=True)

with tab2:
    st.subheader("🔍 Explorar Iniciativas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        area_filter = st.multiselect("🏢 Áreas", df['Área'].unique())
    
    with col2:
        classification_filter = st.multiselect("🎯 Clasificación", df['Clasificación'].unique())
    
    with col3:
        sort_by = st.selectbox("🔢 Ordenar por", ['Ranking', 'Puntuación Total', 'nivel_impacto'])
    
    # Aplicar filtros
    filtered_df = df.copy()
    if area_filter:
        filtered_df = filtered_df[filtered_df['Área'].isin(area_filter)]
    if classification_filter:
        filtered_df = filtered_df[filtered_df['Clasificación'].isin(classification_filter)]
    
    filtered_df = filtered_df.sort_values(sort_by, ascending=False)
    
    st.info(f"Mostrando {len(filtered_df)} de {len(df)} iniciativas")
    
    # Mostrar iniciativas
    for idx, row in filtered_df.head(10).iterrows():
        with st.expander(f"#{row['Ranking']} - {row['Nombre_Iniciativa'][:50]}... ({row['Clasificación']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**👤 Propuesto por:** {row['Nombre_Completo']}")
                st.markdown(f"**🏢 Área:** {row['Área']}")
                st.markdown(f"**🎯 Clasificación:** {row['Clasificación']}")
            
            with col2:
                st.metric("🏆 Ranking", f"#{row['Ranking']}")
                st.metric("📊 Puntuación", f"{row['Puntuación Total']:.0f}/30")
                st.metric("📈 Impacto", f"{row['nivel_impacto']}/5")

with tab3:
    st.subheader("📈 Análisis Estadístico")
    
    # Correlaciones
    numeric_cols = ['valor_estrategico', 'nivel_impacto', 'viabilidad_tecnica', 'costo_beneficio']
    corr_matrix = df[numeric_cols].corr()
    
    fig_corr = px.imshow(
        corr_matrix,
        text_auto=".2f",
        title="🔗 Correlaciones",
        color_continuous_scale='RdBu'
    )
    st.plotly_chart(fig_corr, use_container_width=True)
    
    # Distribución de puntuaciones
    fig_hist = px.histogram(
        df, 
        x='Puntuación Total',
        color='Clasificación',
        color_discrete_map=color_map,
        title="📈 Distribución de Puntuaciones"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with tab4:
    st.subheader("🏆 Rankings y Reportes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥇 Top 10 Iniciativas")
        top_initiatives = df.nlargest(10, 'Puntuación Total')[
            ['Ranking', 'Nombre_Iniciativa', 'Área', 'Puntuación Total', 'Clasificación']
        ].reset_index(drop=True)
        
        st.dataframe(top_initiatives, hide_index=True)
    
    with col2:
        st.markdown("### 🚀 Quick Wins")
        quick_wins_df = df[df['Clasificación'] == 'Quick Win'].nlargest(5, 'Puntuación Total')[
            ['Ranking', 'Nombre_Iniciativa', 'Área', 'Puntuación Total']
        ].reset_index(drop=True)
        
        if not quick_wins_df.empty:
            st.dataframe(quick_wins_df, hide_index=True)
        else:
            st.info("No hay Quick Wins disponibles")
    
    # Resumen ejecutivo
    st.markdown("### 📋 Resumen Ejecutivo")
    
    total_initiatives = len(df)
    avg_score = df['Puntuación Total'].mean()
    top_area = df['Área'].value_counts().index[0] if len(df) > 0 else "N/A"
    classification_counts = df['Clasificación'].value_counts()
    
    st.markdown(f"""
    **Resumen General ({datetime.now().strftime('%Y-%m-%d')})**
    
    - Total de iniciativas: {total_initiatives}
    - Puntuación promedio: {avg_score:.1f}/30 ({(avg_score/30)*100:.1f}%)
    - Área más activa: {top_area}
    - Quick Wins: {classification_counts.get('Quick Win', 0)}
    - Iniciativas estratégicas: {classification_counts.get('Estratégica', 0)}
    """)
    
    # Exportar datos
    st.markdown("### 💾 Exportar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_df = df[['Ranking', 'Nombre_Iniciativa', 'Nombre_Completo', 'Área', 'Clasificación', 'Puntuación Total']]
        csv_complete = export_df.to_csv(index=False)
        st.download_button(
            "📥 Reporte Completo (CSV)",
            csv_complete,
            f"reporte_iniciativas_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
    
    with col2:
        if not df[df['Clasificación'] == 'Quick Win'].empty:
            quick_wins_export = df[df['Clasificación'] == 'Quick Win'][['Ranking', 'Nombre_Iniciativa', 'Área', 'Puntuación Total']]
            csv_quick_wins = quick_wins_export.to_csv(index=False)
            st.download_button(
                "🚀 Quick Wins (CSV)",
                csv_quick_wins,
                f"quick_wins_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>💡 <strong>Sistema de Análisis de Iniciativas - Alico</strong></p>
    <p>Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>
""", unsafe_allow_html=True)
