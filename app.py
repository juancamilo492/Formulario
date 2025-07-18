import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# Configuración inicial
st.set_page_config(page_title="Panel de Evaluación de Ideas", layout="wide")
st.title("📊 Análisis de Ideas Innovadoras")

# Cargar datos desde Google Sheets (o DataFrame local para prueba)
# Usa st.secrets o reemplaza directamente por una URL o ruta local
sheet_url = st.secrets["gsheets_url"]
df = pd.read_csv(sheet_url)

# Columnas de criterios
criteria = [
    "valor_estrategico", "impacto", "viabilidad", "costobeneficio",
    "innovacion", "alineacion", "escalabilidad", "tiempo"
]

if not all(col in df.columns for col in criteria):
    st.error("Faltan columnas requeridas en la base de datos.")
    st.stop()

# Calcular promedio por idea
if "promedio" not in df.columns:
    df["promedio"] = df[criteria].mean(axis=1)

# Filtro lateral
with st.sidebar:
    st.header("🔍 Filtros")
    min_promedio = st.slider("Puntaje promedio mínimo", 0.0, 5.0, 0.0, 0.1)
    selected = st.selectbox("Selecciona una idea para ver radar:", df.index)

# Filtrado de ideas
filtrado = df[df["promedio"] >= min_promedio]

# Tabla general
st.subheader("📋 Tabla de Evaluaciones")
st.dataframe(filtrado, use_container_width=True)

# Radar chart
if not filtrado.empty:
    st.subheader("🔘 Perfil por Criterios")
    idea_row = df.loc[selected]
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[idea_row[c] for c in criteria],
        theta=criteria,
        fill='toself',
        name=idea_row.get("Idea", f"Fila {selected}")
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# Gráfico de barras de promedios generales
st.subheader("📈 Promedio General por Criterio")
promedios = df[criteria].mean().round(2)
fig_bar = px.bar(promedios, orientation='v', labels={'value': 'Promedio', 'index': 'Criterio'})
fig_bar.update_yaxes(range=[0, 5])
st.plotly_chart(fig_bar, use_container_width=True)

# Heatmap de correlaciones
st.subheader("🧠 Matriz de Correlación entre Criterios")
corr = df[criteria].corr().round(2)
fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
st.pyplot(fig)

# Exportar CSV
st.download_button("📥 Descargar datos filtrados", data=filtrado.to_csv(index=False), file_name="ideas_filtradas.csv", mime="text/csv")
