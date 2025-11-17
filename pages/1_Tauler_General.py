# pages/1_📊_Dashboard_General.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# Importar utilitats
from utils.data_processing import load_data, get_timezone_aware_datetime
from utils.formatting import format_time, format_pace
from i18n import t, DAY_NAMES_ES_TO_CA, DAY_NAMES_SHORT, TRAINING_ZONES_CA
from auth import check_password, add_logout_button

st.set_page_config(
    layout="wide"
)

# Verificar autenticació
if not check_password():
    st.stop()

# Afegir botó de logout a la sidebar
add_logout_button()

# Carregar dades (utilitzarà la caché)
activities, splits = load_data()

st.title(t("dashboard_title"))

if activities.empty:
    st.warning(t("no_data_warning"))
    st.stop()

# --- FILTRES AL SIDEBAR ---
st.sidebar.header(t("filters_header"))
min_date = activities['start_date_local'].min().date()
max_date = activities['start_date_local'].max().date()
date_range = st.sidebar.date_input(
    t("date_range"),
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="dash_date_range"
)
min_distance = st.sidebar.slider(
    t("min_distance"), 0.0, float(activities['distance_km'].max()), 0.0, 0.5, key="dash_dist_slider"
)

group_by = st.sidebar.radio(t("group_by"), [t("group_weeks"), t("group_months")], horizontal=True, key="dash_group_by")
long_run_km = st.sidebar.slider(t("long_run_definition"), 8.0, 35.0, 16.0, 1.0, key="dash_longrun_km")
show_coach_tips = st.sidebar.checkbox(t("show_coach_tips"), value=True, key="dash_show_tips")

# Aplicar filtros
if len(date_range) == 2:
    start_date = get_timezone_aware_datetime(datetime.combine(date_range[0], datetime.min.time()))
    end_date = get_timezone_aware_datetime(datetime.combine(date_range[1], datetime.max.time()))
    mask = (
        (activities['start_date_local'] >= start_date) &
        (activities['start_date_local'] <= end_date) &
        (activities['distance_km'] >= min_distance)
    )
    filtered_activities = activities[mask].copy()
else:
    filtered_activities = activities[activities['distance_km'] >= min_distance].copy()

if filtered_activities.empty:
    st.warning(t("no_data_with_filters"))
    st.stop()

# ---------- ENRIQUECER DATA Y HELPERS ----------
filtered_activities['start_hour'] = filtered_activities['start_date_local'].dt.hour
# Semana que empieza el lunes; convertimos Period->Timestamp con .start_time
filtered_activities['week'] = filtered_activities['start_date_local'].dt.to_period('W-MON').apply(lambda r: r.start_time)
filtered_activities['is_long_run'] = filtered_activities['distance_km'] >= long_run_km

def compute_weekly(df: pd.DataFrame) -> pd.DataFrame:
    weekly = df.groupby('week').agg(
        distance_km=('distance_km', 'sum'),
        runs=('id', 'count'),
        moving_time=('moving_time', 'sum'),
        avg_pace=('pace_min_km', 'mean'),
        long_runs=('is_long_run', 'sum'),
    ).reset_index().sort_values('week')
    weekly['km_4w_avg'] = weekly['distance_km'].rolling(4, min_periods=1).mean()
    return weekly

def streaks_from_dates(dates) -> tuple[int, int]:
    """Devuelve (racha_actual, racha_máxima) en días usando fechas únicas."""
    s = pd.to_datetime(dates, errors="coerce").dt.date.dropna()
    d = sorted(set(s))
    if not d:
        return 0, 0
    cur = mx = 1
    for i in range(1, len(d)):
        if (d[i] - d[i-1]).days == 1:
            cur += 1
        else:
            mx = max(mx, cur)
            cur = 1
    mx = max(mx, cur)
    return cur, mx

def compute_pr(df: pd.DataFrame, target_km: float, tol: float = 0.03):
    """Récord aproximado en una distancia objetivo basado en actividades completas ±tol."""
    cand = df[(df['distance_km'] >= target_km * (1 - tol)) &
              (df['distance_km'] <= target_km * (1 + tol)) &
              (df['moving_time'] > 0)].copy()
    if cand.empty:
        return None
    cand['est_time_s'] = cand['moving_time'] * (target_km / cand['distance_km'])
    best = cand.sort_values('est_time_s', ascending=True).iloc[0]
    pace_min_km = (best['est_time_s'] / 60) / target_km
    return int(best['est_time_s']), pace_min_km, best

weekly = compute_weekly(filtered_activities)
last4 = weekly.tail(4)
prev4 = weekly.iloc[-8:-4] if len(weekly) >= 8 else pd.DataFrame(columns=weekly.columns)
vol_change = None
if not prev4.empty:
    prev_sum = prev4['distance_km'].sum()
    if prev_sum > 0:
        vol_change = (last4['distance_km'].sum() - prev_sum) / prev_sum * 100
avg_weekly_km_4w = last4['distance_km'].mean() if not last4.empty else 0.0
runs_per_week_8w = weekly.tail(8)['runs'].mean() if not weekly.empty else 0
long_runs_4w = int(last4['long_runs'].sum()) if not last4.empty else 0
current_streak, max_streak = streaks_from_dates(filtered_activities['start_date_local'])

# Ventanas 30d para deltas de ritmo
thirty_days_ago = get_timezone_aware_datetime(datetime.now() - timedelta(days=30))
last_30 = filtered_activities[filtered_activities['start_date_local'] >= thirty_days_ago]
prev_30 = filtered_activities[
    (filtered_activities['start_date_local'] < thirty_days_ago) &
    (filtered_activities['start_date_local'] >= get_timezone_aware_datetime(datetime.now() - timedelta(days=60)))
]

# --- MÈTRIQUES PRINCIPALS ---
st.subheader(t("training_metrics"))
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label=t("total_runs"), value=len(filtered_activities), delta=f"{len(last_30)} {t('last_30d')}")

with col2:
    total_km = filtered_activities['distance_km'].sum()
    recent_km = last_30['distance_km'].sum()
    st.metric(label=t("total_km"), value=f"{total_km:.1f} km", delta=f"{recent_km:.1f} km {t('last_30d')}")

with col3:
    avg_pace_total = filtered_activities['pace_min_km'].mean()
    avg_pace_recent = last_30['pace_min_km'].mean() if not last_30.empty else None
    avg_pace_prev = prev_30['pace_min_km'].mean() if not prev_30.empty else None
    delta_text = None
    if avg_pace_recent is not None and avg_pace_prev is not None:
        diff = avg_pace_recent - avg_pace_prev
        sign = "+" if diff >= 0 else "-"
        delta_text = f"{sign}{abs(diff):.2f} min/km {t('vs_prev_30d')}"
    st.metric(label=t("avg_pace"), value=format_pace(avg_pace_total),
              delta=delta_text or "—", delta_color="inverse")

with col4:
    total_time = filtered_activities['moving_time'].sum()
    st.metric(label=t("longest_run"), value=f"{filtered_activities['distance_km'].max():.1f} km")

# --- MÈTRIQUES DE CONSISTÈNCIA I QUALITAT ---
col1b, col2b, col3b, col4b = st.columns(4)
with col1b:
    st.metric(t("weekly_avg_4w"), f"{avg_weekly_km_4w:.1f} km")
with col2b:
    delta_vol = f"{vol_change:+.0f}% vs prev. 4s" if vol_change is not None else "—"
    st.metric(t("volume_change"), f"{last4['distance_km'].sum():.1f} km", delta=delta_vol)
with col3b:
    st.metric(t("runs_per_week_8w"), f"{runs_per_week_8w:.1f}")
with col4b:
    st.metric(t("current_streak"), f"{current_streak} {t('days')}", help=f"{t('max_streak')}: {max_streak} {t('days')}")

# --- GRÀFICS PRINCIPALS ---
colg1, colg2 = st.columns(2)
with colg1:
    if group_by == t("group_weeks"):
        st.subheader(t("weekly_volume_chart"))
        fig = px.bar(weekly, x='week', y='distance_km',
                     labels={'week': t('week'), 'distance_km': t('distance_km')})
        # Mitjana mòbil 4 setmanes
        fig.add_scatter(x=weekly['week'], y=weekly['km_4w_avg'], mode='lines', name=t('avg_4w'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.subheader("Evolució de la distància mensual")
        monthly_data = filtered_activities.groupby('month_year').agg(
            distance_km=('distance_km', 'sum')
        ).reset_index()
        fig = px.bar(monthly_data, x='month_year', y='distance_km',
                     labels={'distance_km': t('distance_km'), 'month_year': 'Mes'})
        st.plotly_chart(fig, use_container_width=True)

with colg2:
    st.subheader("Distribució de Distàncies")
    fig = px.histogram(filtered_activities, x='distance_km', nbins=20,
                       labels={'distance_km': t('distance'), 'count': t('frequency')})
    try:
        fig.add_vline(x=float(long_run_km), line_dash="dash",
                      annotation_text="Tirada llarga", annotation_position="top")
    except Exception:
        pass
    st.plotly_chart(fig, use_container_width=True)

# --- ANÀLISI PER DIA DE LA SETMANA ---
st.subheader(t("training_by_day"))
colw1, colw2 = st.columns(2)
day_analysis = filtered_activities.groupby('day_of_week').agg(
    carreras=('id', 'count'),
    distance_km=('distance_km', 'mean')
).reset_index()
day_order_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_analysis['day_of_week'] = pd.Categorical(day_analysis['day_of_week'],
                                             categories=day_order_en, ordered=True)
day_analysis = day_analysis.sort_values('day_of_week')
day_analysis['día'] = day_analysis['day_of_week'].map(DAY_NAMES_SHORT)
with colw1:
    fig = px.bar(day_analysis, x='día', y='carreras', title=t("runs_per_week_chart"),
                 labels={'carreras': t('runs'), 'día': t('day_of_week')})
    st.plotly_chart(fig, use_container_width=True)
with colw2:
    fig = px.bar(day_analysis, x='día', y='distance_km', title=t("avg_runs_per_day"),
                 labels={'distance_km': t('total_distance'), 'día': t('day_of_week')})
    st.plotly_chart(fig, use_container_width=True)

# --- HÀBITS D'ENTRENAMENT ---
st.subheader(t("training_by_hour"))
hab1, hab2 = st.columns(2)
bins = [0, 6, 10, 14, 18, 24]
labels_ca = [t("morning_label"), t("morning_early_label"), t("midday_label"), t("afternoon_label"), t("evening_label")]
filtered_activities['franja'] = pd.cut(filtered_activities['start_hour'], bins=bins, labels=labels_ca,
                                       right=False, include_lowest=True)
with hab1:
    franja_counts = filtered_activities['franja'].value_counts().reindex(labels_ca, fill_value=0)
    fig = px.pie(values=franja_counts.values, names=franja_counts.index, title="Quan surts a córrer?")
    st.plotly_chart(fig, use_container_width=True)
with hab2:
    fig = px.bar(weekly, x='week', y='runs', title=t("runs_per_week_chart"),
                 labels={'week': t('week'), 'runs': t('runs')})
    st.plotly_chart(fig, use_container_width=True)

# --- DISTRIBUCIÓ DE RITMES (Zones adaptatives) ---
st.subheader(t("training_zones"))
pace_series = filtered_activities['pace_min_km'].dropna()
if len(pace_series) >= 5:
    q75 = pace_series.quantile(0.75)
    q50 = pace_series.quantile(0.50)
    q25 = pace_series.quantile(0.25)

    def pace_zone(p):
        if pd.isna(p):
            return None
        if p >= q75: return TRAINING_ZONES_CA['easy']
        if p >= q50: return TRAINING_ZONES_CA['moderate']
        if p >= q25: return TRAINING_ZONES_CA['tempo']
        return TRAINING_ZONES_CA['fast']

    filtered_activities['zona'] = filtered_activities['pace_min_km'].apply(pace_zone)
    zone_order = [TRAINING_ZONES_CA['easy'], TRAINING_ZONES_CA['moderate'], TRAINING_ZONES_CA['tempo'], TRAINING_ZONES_CA['fast']]
    zone_counts = filtered_activities['zona'].value_counts().reindex(zone_order, fill_value=0)
    zc1, zc2 = st.columns(2)
    with zc1:
        fig = px.bar(x=zone_counts.index, y=zone_counts.values,
                     labels={'x': t('zone'), 'y': t('run_count')})
        st.plotly_chart(fig, use_container_width=True)
    with zc2:
        fig = px.scatter(filtered_activities, x='distance_km', y='pace_min_km', color='zona',
                         labels={'distance_km': t('distance_km'), 'pace_min_km': t('pace_min_km')},
                         title="Relació distància-ritme")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Encara no hi ha suficients dades per definir zones adaptatives de ritme.")

# --- QUALITAT DE RITME: Estabilitat per splits ---
st.subheader("Estabilitat de ritme per cursa (variació en splits)")
# Asegura que pace_min_km es numérico
split_source = splits.copy()
split_source['pace_min_km'] = pd.to_numeric(split_source['pace_min_km'], errors='coerce')

split_stats = split_source.groupby('activity_id').agg(
    mean_pace=('pace_min_km', 'mean'),
    std_pace=('pace_min_km', 'std'),
    n_splits=('pace_min_km', 'count')
).reset_index()

# Evita división por cero/NaN y fuerza dtype float antes del round
denom = split_stats['mean_pace']
numer = split_stats['std_pace']
cv_pct = np.where(denom > 0, (numer / denom) * 100, np.nan)
split_stats['cv_pace_%'] = pd.Series(cv_pct).astype(float).round(1)

stab = split_stats.merge(
    filtered_activities[['id', 'start_date_local', 'distance_km']],
    left_on='activity_id', right_on='id', how='inner'
)
stab = stab[stab['n_splits'] >= 3].sort_values('cv_pace_%')
top5 = stab.head(5)[['start_date_local', 'distance_km', 'n_splits', 'cv_pace_%']]
top5.rename(columns={'start_date_local': t('date'), 'distance_km': t('distance'),
                     'n_splits': '# splits', 'cv_pace_%': 'CV ritme %'}, inplace=True)
st.dataframe(top5, use_container_width=True)

# --- RÈCORDS PERSONALS APROXIMATS ---
st.subheader(t("personal_records"))
pr_targets = [(5.0, t("pr_5k")), (10.0, t("pr_10k")), (21.097, t("pr_half")), (42.195, t("pr_marathon"))]
cols = st.columns(len(pr_targets))
for (target, label), c in zip(pr_targets, cols):
    pr = compute_pr(filtered_activities, target)
    if pr is None:
        c.metric(f"Rècord {label}", "—", help=t("no_pr_data"))
    else:
        t_s, pace_minkm, best_row = pr
        c.metric(f"Rècord {label}", format_time(int(t_s)), help=f"Ritme estimat: {format_pace(pace_minkm)}")

# --- ACTIVITAT EN EL TEMPS ---
st.subheader("Activitat en el temps")
fig = px.bar(filtered_activities.sort_values('start_date_local'),
             x='start_date_local', y='distance_km',
             color='is_long_run',
             labels={'start_date_local': t('date'), 'distance_km': t('distance_km'), 'is_long_run': 'Tirada llarga'},
             title="Volum per sortida")
st.plotly_chart(fig, use_container_width=True)

# --- DESCÀRREGA I INSIGHTS DE L'ENTRENADOR ---
csv = filtered_activities.drop(columns=['franja'], errors='ignore').to_csv(index=False).encode('utf-8')
st.download_button("⬇️ Descarregar activitats filtrades (CSV)", data=csv,
                   file_name="activitats_filtrades.csv", mime="text/csv")

if show_coach_tips:
    st.markdown(f"### {t('coach_tips')}")
    tips = []
    if vol_change is not None:
        if vol_change > 10:
            tips.append(f"Bon progrés: el volum de les últimes 4 setmanes és **{vol_change:.0f}%** major vs. les 4 anteriors. Mantén la progressió ≤10–15%/setmana.")
        elif vol_change < -10:
            tips.append(f"El volum ha baixat **{abs(vol_change):.0f}%** vs. les 4 setmanes anteriors. Si no és setmana de descàrrega, torna a la rutina amb 2–3 sortides/setmana.")
        else:
            tips.append("Volum estable entre blocs: afegeix 1 sessió de tècnica/força per millorar economia.")
    if long_runs_4w < 3 and avg_weekly_km_4w >= 30:
        tips.append(f"Només {long_runs_4w} tirades llargues (≥ {long_run_km:.0f} km) en 4 setmanes; objectiu **3–4** si prepares mitja/marató.")
    if not last_30.empty and not prev_30.empty and (last_30['pace_min_km'].mean() - prev_30['pace_min_km'].mean()) < 0:
        tips.append("El ritme mitjà dels últims 30 dies és més ràpid que el bloc anterior. No converteixis tots els rodatges en tempo; respecta dies fàcils.")
    if runs_per_week_8w < 3:
        tips.append("La consistència és clau: apunta a **3+** curses per setmana encara que siguin curtes.")
    if not tips:
        tips.append("Progressió sòlida. Mantén 1 tirada llarga, 1 sessió de qualitat (intervals/tempo) i 1–2 rodatges fàcils per setmana.")
    for tip in tips:
        st.markdown(f"- {tip}")