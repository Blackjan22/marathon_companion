# pages/6_📋_Histórico_Completo.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Importar utilitats
from plotly.subplots import make_subplots
from utils.data_processing import load_data
from utils.formatting import format_time, format_pace
from i18n import t
from auth import check_password, add_logout_button

st.set_page_config(page_title=t("history_title"), page_icon="📋", layout="wide", initial_sidebar_state="expanded")

# Verificar autenticació
if not check_password():
    st.stop()

# Afegir botó de logout a la sidebar
add_logout_button()

# Cargar datos (actividades, splits y (opcional) laps)
_result = load_data()

# Compatibilidad hacia atrás:
if isinstance(_result, tuple):
    if len(_result) == 2:
        activities, laps = _result
        splits = pd.DataFrame()
    elif len(_result) >= 3:
        activities, splits, laps = _result[0], _result[1], _result[2]
    else:
        activities = _result[0]
        splits = pd.DataFrame()
        laps = pd.DataFrame()
else:
    activities = _result
    splits = pd.DataFrame()
    laps = pd.DataFrame()

st.title(t("history_title"))

if activities.empty:
    st.warning(t("no_data_warning"))
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

# --- FILTRES AL COS DE LA PÀGINA ---
st.header(t("history_filters"))
col1, col2, col3 = st.columns(3)
with col1:
    sport_types = [t("all_sports")] + list(display_data['sport_type'].unique())
    selected_sport = st.selectbox(t("sport_type"), sport_types)
with col2:
    min_dist_filter = st.number_input(t("min_distance"), min_value=0.0, value=0.0, step=0.5)
with col3:
    max_dist_filter = st.number_input("Distància màxima (km):", min_value=0.0, value=float(display_data['distance_km'].max()), step=1.0)

# Aplicar filtres
display_filtered = display_data.copy()
if selected_sport != t("all_sports"):
    display_filtered = display_filtered[display_filtered['sport_type'] == selected_sport]
mask_distance = (display_filtered['distance_km'] >= min_dist_filter) & (display_filtered['distance_km'] <= max_dist_filter)
display_filtered = display_filtered[mask_distance]

st.header("Resultats")
if display_filtered.empty:
    st.warning("No hi ha activitats que coincideixin amb els filtres.")
    st.stop()

# Mostrar estadístiques resumides de les dades filtrades
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Activitats Filtrades", len(display_filtered))
with col2:
    st.metric(t("total_km"), f"{display_filtered['distance_km'].sum():.1f}")
with col3:
    st.metric("Temps Total", format_time(display_filtered['moving_time'].sum()))
with col4:
    st.metric(t("avg_pace"), format_pace(display_filtered['pace_min_km'].mean()))
with col5:
    st.metric(t("elevation"), int(display_filtered['total_elevation_gain'].fillna(0).sum()))

# --- TAULA INTERACTIVA ---
columns_to_show = [
    'Fecha', 'name', 'Distancia (km)', 'Tiempo', 'Ritmo (min/km)',
    'FC Promedio', 'Desnivel (m)', 'sport_type', 'Notas'
]
column_names = {'name': t('activity_name'), 'sport_type': 'Tipus'}
st.dataframe(
    display_filtered[columns_to_show].rename(columns=column_names),
    use_container_width=True,
    hide_index=True,
    height=500
)

# =====================
#   ANÀLISI DE SPLITS (KM AUTOMÀTICS)
# =====================
st.divider()
st.subheader("Anàlisi de Splits per Km")

if splits.empty:
    st.warning("No hi ha dades de splits disponibles.")
    st.stop()

# Limitar selección a actividades filtradas arriba
filtered_ids = set(display_filtered['id'])
activity_options = activities[activities['id'].isin(filtered_ids)][
    ['id', 'name', 'start_date_local', 'distance_km']
].copy()

if activity_options.empty:
    st.info("Ajusta els filtres per seleccionar una activitat.")
    st.stop()

activity_options['display'] = activity_options.apply(
    lambda x: f"{x['start_date_local'].strftime('%Y-%m-%d')} - {x['name']} ({x['distance_km']:.1f} km)",
    axis=1
)
selected_activity_id = st.selectbox(
    "Tria una cursa per analitzar els seus splits per km:",
    options=activity_options['id'],
    format_func=lambda x: activity_options[activity_options['id'] == x]['display'].iloc[0]
)

activity_splits = splits[splits['activity_id'] == selected_activity_id].copy()
activity_info = activities[activities['id'] == selected_activity_id].iloc[0]

# Mètriques principals
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Distància Total", f"{activity_info['distance_km']:.2f} km")
with col2:
    st.metric("Temps Total", format_time(activity_info['moving_time']))
with col3:
    st.metric(t("avg_pace"), format_pace(activity_info['pace_min_km']))
with col4:
    st.metric("Desnivell Total (m)", int((activity_info.get('total_elevation_gain') or 0)))

# Comentaris de l'activitat seleccionada
comentarios = _combine_comments(
    activity_info['description'] if 'description' in activity_info else None,
    activity_info['private_note'] if 'private_note' in activity_info else None
)
if comentarios:
    st.markdown(f"**Notes:** {comentarios}")

# Gràfics i detall
if not activity_splits.empty:

    st.subheader("Perfil d'Elevació i Ritme")

    # ----- Preparar series -----
    def _get_split_no(df: pd.DataFrame) -> pd.Series:
        if 'split' in df.columns:
            return pd.to_numeric(df['split'], errors='coerce')
        else:
            return pd.Series(range(1, len(df) + 1), index=df.index)

    x = _get_split_no(activity_splits)

    dist_m = pd.to_numeric(activity_splits.get('distance', pd.Series(index=activity_splits.index)), errors='coerce')
    elap_s  = pd.to_numeric(activity_splits.get('elapsed_time', pd.Series(index=activity_splits.index)), errors='coerce')
    avg_v  = pd.to_numeric(activity_splits.get('average_speed', pd.Series(index=activity_splits.index)), errors='coerce')

    def _pace_min_km(distance_m, elapsed_time_s, avg_speed_mps):
        # Prioriza velocidad media si está disponible; si no, calcula por distancia/tiempo.
        if pd.notnull(avg_speed_mps) and avg_speed_mps > 0:
            return 16.6666667 / float(avg_speed_mps)  # (1000/60) / m/s
        if pd.notnull(distance_m) and pd.notnull(elapsed_time_s) and distance_m > 0 and elapsed_time_s > 0:
            return (float(elapsed_time_s) / float(distance_m)) * (1000.0 / 60.0)
        return None

    pace = [ _pace_min_km(dm, et, spd) for dm, et, spd in zip(dist_m, elap_s, avg_v) ]

    # IMPORTANT: Crear perfil d'elevació acumulat (com Strava)
    has_elev = 'elevation_difference' in activity_splits.columns
    if has_elev:
        # Sumar acumulativament els elevation_difference per obtenir el perfil
        elev_cumsum = activity_splits['elevation_difference'].fillna(0).cumsum()
        # Normalitzar perquè el mínim sigui 0 (desplaçar tot el perfil cap amunt)
        elev_min = elev_cumsum.min()
        elev_normalized = elev_cumsum - elev_min
    else:
        elev_normalized = None

    # ----- Figura con eje secundario -----
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # PERFIL EN ÁREA: Elevació normalitzada (perfil continu)
    if has_elev and elev_normalized is not None:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=elev_normalized,
                mode="lines",
                fill="tozeroy",
                name="Perfil d'elevació",
                line=dict(width=2, color='rgb(100, 149, 237)'),
                fillcolor='rgba(100, 149, 237, 0.2)',
                hovertemplate="Km: %{x}<br>Elevació relativa: %{y:.1f} m<extra></extra>",
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
            name="Ritme (min/km)",
            line=dict(width=2, dash="dot"),
            marker=dict(size=6),
            hovertemplate="Km: %{x}<br>Ritme: %{text}<extra></extra>",
            text=[format_pace(p) if p is not None else t("not_available") for p in pace],
            connectgaps=False
        ),
        secondary_y=True
    )

    # Línia mitjana de ritme (sobre y2) si hi ha dades vàlides
    pace_series = pd.Series([p for p in pace if p is not None])
    if not pace_series.empty:
        avg_pace = float(pace_series.mean())
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
            text=f"Ritme mitjà: {format_pace(avg_pace)}",
            showarrow=False, xanchor="left", yanchor="bottom", xshift=8
        )
        y2_min, y2_max = float(pace_series.min()), float(pace_series.max())
    else:
        # Valores por defecto para evitar errores si todo es N/A
        y2_min, y2_max = 4.0, 8.0  # rango razonable en min/km

    pad = 0.15
    fig.update_xaxes(title_text="Distància (km)", type="linear", dtick=1)
    fig.update_yaxes(
        title_text="Elevació relativa (m)",
        secondary_y=False,
        showgrid=True, zeroline=True, zerolinewidth=1.5,
        rangemode='tozero'
    )
    fig.update_yaxes(
        title_text="Ritme (min/km)",
        secondary_y=True,
        showgrid=False, showline=True, ticks="outside",
        autorange=False,
        range=[y2_max + pad, y2_min - pad]   # invertit (més ràpid a dalt)
    )

    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    # ----- Taula de detall de splits -----
    st.subheader("Detall per Km")

    splits_display = activity_splits.copy()
    splits_display['Ritme'] = [format_pace(p) if p is not None else t("not_available") for p in pace]

    if 'elapsed_time' in splits_display.columns:
        splits_display['Temps'] = splits_display['elapsed_time'].apply(format_time)
    if 'distance' in splits_display.columns:
        splits_display['Distància (m)'] = splits_display['distance'].round(0)
    # IMPORTANT: Usar elevation_difference (amb signe) en lloc de total_elevation_gain
    if 'elevation_difference' in splits_display.columns:
        splits_display['Desnivell (m)'] = splits_display['elevation_difference'].fillna(0).round(1)

    # Columna d'índex de split
    if 'split' in splits_display.columns:
        idx_col = 'split'
    else:
        idx_col = '_split_tmp_index'
        splits_display[idx_col] = range(1, len(splits_display) + 1)

    cols = [idx_col] + [c for c in ['Distància (m)', 'Temps', 'Ritme', 'Desnivell (m)'] if c in splits_display.columns]

    st.dataframe(
        splits_display[cols].rename(columns={idx_col: 'Km #'}),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Aquesta activitat no té dades de splits disponibles.")