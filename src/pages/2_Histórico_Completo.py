# pages/6_📋_Histórico_Completo.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Importar utilidades
from plotly.subplots import make_subplots
from utils.data_processing import load_data
from utils.formatting import format_time, format_pace

st.set_page_config(page_title="Histórico Completo", page_icon="📋", layout="wide", initial_sidebar_state="expanded")

# Cargar datos (actividades y splits)
activities, splits = load_data()

st.title("📋 Histórico Completo de Actividades")

if activities.empty:
    st.warning("No hay datos de carreras disponibles.")
    st.stop()

# --- PREPARAR DATOS PARA MOSTRAR ---
display_data = activities.copy()

# Columna Notas = description + private_note (tolerante a ausencia de columnas)
desc_col = display_data['description'] if 'description' in display_data.columns else pd.Series('', index=display_data.index)
priv_col = display_data['private_note'] if 'private_note' in display_data.columns else pd.Series('', index=display_data.index)

def _combine_comments(d, p):
    d = '' if pd.isna(d) else str(d).strip()
    p = '' if pd.isna(p) else str(p).strip()
    parts = [x for x in [d, p] if x]
    return ' | '.join(parts)

display_data['Notas'] = [_combine_comments(d, p) for d, p in zip(desc_col, priv_col)]

display_data['Fecha'] = display_data['start_date_local'].dt.strftime('%Y-%m-%d %H:%M')
display_data['Distancia (km)'] = display_data['distance_km'].round(2)
display_data['Tiempo'] = display_data['moving_time'].apply(format_time)
display_data['Ritmo (min/km)'] = display_data['pace_min_km'].apply(format_pace)
display_data['FC Promedio'] = display_data['average_heartrate'].fillna(0).round(0).astype(int).astype(str).replace('0', 'N/A')
display_data['Desnivel (m)'] = display_data['total_elevation_gain'].fillna(0).round(0).astype(int)

# --- FILTROS EN EL CUERPO DE LA PÁGINA ---
st.header("Filtrar Histórico")
col1, col2, col3 = st.columns(3)
with col1:
    sport_types = ['Todos'] + list(display_data['sport_type'].unique())
    selected_sport = st.selectbox("Tipo de deporte:", sport_types)
with col2:
    min_dist_filter = st.number_input("Distancia mínima (km):", min_value=0.0, value=0.0, step=0.5)
with col3:
    max_dist_filter = st.number_input("Distancia máxima (km):", min_value=0.0, value=float(display_data['distance_km'].max()), step=1.0)

# Aplicar filtros
display_filtered = display_data.copy()
if selected_sport != 'Todos':
    display_filtered = display_filtered[display_filtered['sport_type'] == selected_sport]
mask_distance = (display_filtered['distance_km'] >= min_dist_filter) & (display_filtered['distance_km'] <= max_dist_filter)
display_filtered = display_filtered[mask_distance]

st.header("Resultados")
if display_filtered.empty:
    st.warning("No hay actividades que coincidan con los filtros.")
    st.stop()

# Mostrar estadísticas resumidas de los datos filtrados (añado desnivel total)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Actividades Filtradas", len(display_filtered))
with col2:
    st.metric("Total Kilómetros", f"{display_filtered['distance_km'].sum():.1f}")
with col3:
    st.metric("Tiempo Total", format_time(display_filtered['moving_time'].sum()))
with col4:
    st.metric("Ritmo Promedio", format_pace(display_filtered['pace_min_km'].mean()))
with col5:
    st.metric("Desnivel total (m)", int(display_filtered['total_elevation_gain'].fillna(0).sum()))

# --- TABLA INTERACTIVA ---
columns_to_show = [
    'Fecha', 'name', 'Distancia (km)', 'Tiempo', 'Ritmo (min/km)',
    'FC Promedio', 'Desnivel (m)', 'sport_type', 'Notas'
]
column_names = {'name': 'Actividad', 'sport_type': 'Tipo'}
st.dataframe(
    display_filtered[columns_to_show].rename(columns=column_names),
    use_container_width=True,
    hide_index=True,
    height=500
)

# =====================
#   ANÁLISIS DE SPLITS
# =====================
st.divider()
st.subheader("🏃‍♂️ Análisis de Splits")

if splits.empty:
    st.warning("No hay datos de splits disponibles en tu base de datos.")
    st.stop()

# Limitar selección a actividades filtradas arriba
filtered_ids = set(display_filtered['id'])
activity_options = activities[activities['id'].isin(filtered_ids)][
    ['id', 'name', 'start_date_local', 'distance_km']
].copy()

if activity_options.empty:
    st.info("Ajusta los filtros para seleccionar una actividad.")
    st.stop()

activity_options['display'] = activity_options.apply(
    lambda x: f"{x['start_date_local'].strftime('%Y-%m-%d')} - {x['name']} ({x['distance_km']:.1f} km)",
    axis=1
)
selected_activity_id = st.selectbox(
    "Elige una carrera para analizar sus splits:",
    options=activity_options['id'],
    format_func=lambda x: activity_options[activity_options['id'] == x]['display'].iloc[0]
)

activity_splits = splits[splits['activity_id'] == selected_activity_id].copy()
activity_info = activities[activities['id'] == selected_activity_id].iloc[0]

# Métricas principales (incluye desnivel total)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Distancia Total", f"{activity_info['distance_km']:.2f} km")
with col2:
    st.metric("Tiempo Total", format_time(activity_info['moving_time']))
with col3:
    st.metric("Ritmo Promedio", format_pace(activity_info['pace_min_km']))
with col4:
    st.metric("Desnivel Total (m)", int((activity_info.get('total_elevation_gain') or 0)))

# Comentarios de la actividad seleccionada
comentarios = _combine_comments(
    activity_info['description'] if 'description' in activity_info else None,
    activity_info['private_note'] if 'private_note' in activity_info else None
)
if comentarios:
    st.markdown(f"**Notas:** {comentarios}")

# Gráficos y detalle
if not activity_splits.empty:
    
    st.subheader("Ritmo y Desnivel por Split")

    # Series base
    x = pd.to_numeric(activity_splits['split'], errors='coerce')
    pace = activity_splits['pace_min_km']
    has_elev = 'elevation_difference' in activity_splits.columns
    elev = activity_splits['elevation_difference'].fillna(0) if has_elev else None

    # Figura con eje secundario
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # PERFIL EN ÁREA: Desnivel (Y izquierda)
    if has_elev:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=elev,
                mode="lines",
                fill="tozeroy",
                name="Desnivel (m)",
                line=dict(width=0),        # solo área, sin contorno marcado
                opacity=0.45,
                hovertemplate="Split: %{x}<br>Desnivel: %{y:.0f} m<extra></extra>",
                connectgaps=False
            ),
            secondary_y=False
        )

    # LÍNEA PUNTEADA: Ritmo (Y derecha invertida)
    fig.add_trace(
        go.Scatter(
            x=x,
            y=pace,
            mode="lines+markers",
            name="Ritmo (min/km)",
            line=dict(width=2, dash="dot"),
            marker=dict(size=6),
            hovertemplate="Split: %{x}<br>Ritmo: %{text}<extra></extra>",
            text=pace.apply(format_pace),
            connectgaps=False
        ),
        secondary_y=True
    )

    # Línea media de ritmo (sobre y2)
    avg_pace = float(pace.mean())
    fig.add_shape(
        type="line",
        x0=float(x.min()), x1=float(x.max()),
        y0=avg_pace, y1=avg_pace,
        xref="x", yref="y2",
        line=dict(dash="dash", width=1.5)
    )
    fig.add_annotation(
        x=1.0, xref="paper",
        y=avg_pace, yref="y2",
        text=f"Ritmo medio: {format_pace(avg_pace)}",
        showarrow=False, xanchor="left", yanchor="bottom", xshift=8
    )

    # Ejes y layout (evitamos solapes visuales)
    y2_min, y2_max = float(pace.min()), float(pace.max())
    pad = 0.15
    fig.update_xaxes(
        title_text="Split (km)",
        type="linear",           # evita wrap de categorías
        dtick=1
    )
    fig.update_yaxes(
        title_text="Desnivel (m)",
        secondary_y=False,
        showgrid=True, zeroline=True, zerolinewidth=1
    )
    fig.update_yaxes(
        title_text="Ritmo (min/km)",
        secondary_y=True,
        showgrid=False, showline=True, ticks="outside",
        autorange=False,
        range=[y2_max + pad, y2_min - pad]   # invertido (más rápido arriba)
    )

    fig.update_layout(
        title="Ritmo y Desnivel por Split",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detalle de Splits")
    
    splits_display = activity_splits.copy()
    splits_display['Ritmo'] = splits_display['pace_min_km'].apply(format_pace)
    splits_display['Tiempo'] = splits_display['elapsed_time'].apply(format_time)
    splits_display['Distancia (m)'] = splits_display['distance'].round(0)
    if 'elevation_difference' in splits_display.columns:
        splits_display['Desnivel (m)'] = splits_display['elevation_difference'].fillna(0).round(0).astype(int)
        cols = ['split', 'Distancia (m)', 'Tiempo', 'Ritmo', 'Desnivel (m)']
    else:
        cols = ['split', 'Distancia (m)', 'Tiempo', 'Ritmo']

    st.dataframe(
        splits_display[cols].rename(columns={'split': 'Split (km)'}),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Esta actividad no tiene datos de splits disponibles.")