df[criteria] = df[criteria].apply(pd.to_numeric, errors="coerce")
    df["promedio"] = df[criteria].mean(axis=1)

# Filtros laterales
with st.sidebar:
    st.header("🔍 Filtros")
    if "Rol o relación con Alico  " in df.columns:
        roles = df["Rol o relación con Alico  "].dropna().unique().tolist()
        rol_selected = st.multiselect("Filtrar por rol o relación:", roles, default=roles)
        df = df[df["Rol o relación con Alico  "].isin(rol_selected)]

    if "Selecciona el área o proceso al cual perteneces " in df.columns:
        areas = df["Selecciona el área o proceso al cual perteneces "].dropna().unique().tolist()
        area_selected = st.multiselect("Filtrar por área o proceso:", areas, default=areas)
        df = df[df["Selecciona el área o proceso al cual perteneces "].isin(area_selected)]

    min_promedio = st.slider("Puntaje promedio mínimo", 0.0, 5.0, 0.0, 0.1)

# Filtrado de ideas
if "promedio" in df.columns:
    filtrado = df[df["promedio"] >= min_promedio]
else:
    filtrado = df.copy()

# Tabla general
st.subheader("📋 Tabla de Evaluaciones")
st.dataframe(filtrado, use_container_width=True)

# Radar chart
if not filtrado.empty and criteria:
    st.subheader("🔘 Perfil por Criterios")
    idx = st.selectbox("Selecciona una idea para ver radar:", filtrado.index)
    idea_row = filtrado.loc[idx]
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[idea_row[c] for c in criteria],
        theta=criteria,
        fill='toself',
        name=idea_row.get("Nombre de la idea o iniciativa  ", f"Fila {idx}")
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# Gráfico de barras de promedios generales
if criteria:
    st.subheader("📈 Promedio General por Criterio")
    promedios = filtrado[criteria].mean().round(2)
    fig_bar = px.bar(promedios, orientation='v', labels={'value': 'Promedio', 'index': 'Criterio'})
    fig_bar.update_yaxes(range=[0, 5])
    st.plotly_chart(fig_bar, use_container_width=True)

# Heatmap de correlaciones
if len(criteria) > 1:
    st.subheader("🧠 Matriz de Correlación entre Criterios")
    corr = filtrado[criteria].corr().round(2)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    st.pyplot(fig)

# Exportar CSV
st.download_button("📥 Descargar datos filtrados", data=filtrado.to_csv(index=False), file_name="ideas_filtradas.csv", mime="text/csv")
