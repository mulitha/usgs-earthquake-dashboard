# ---------------USGS Earthquakes------------------

#Uses USGS FDSN Event API (geojson)
#Renders three tabs via separate modules

import requests
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta, timezone

from tabs_interactive import render_interactive
from tabs_visuals import render_visuals
from tabs_exploration import render_exploration

st.set_page_config(page_title="USGS Earthquakes — Dashboard", layout="wide")
USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

from textwrap import dedent




def render_front_page():
    html = dedent("""
    <style>
      /* === General Layout === */
      .fp-wrap {
        max-width: 1080px;
        margin: 0 auto;
        text-align: center;
      }

      /* === Header Ribbon === */
      .fp-ribbon {
        display: block;
        width: 100%;
        background: #1e90ff;  /* Change to #c8102e for Murdoch red */
        color: #fff;
        padding: 14px 20px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1.3rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(30,144,255,0.4);
        margin-bottom: 20px;
      }

      /* === Section Cards === */
      .fp-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 18px 20px;
        margin: 12px 0;
        text-align: left;
        box-shadow: 0 3px 14px rgba(0,0,0,.08);
      }

      /* === Typography === */
      .fp-h2 {
        margin: 4px 0 10px;
        font-size: 1.1rem;
        font-weight: 800;
      }
      .fp-p {
        margin: 0 0 6px;
        line-height: 1.45;
      }

      /* === Hypothesis section === */
      .fp-bullets { margin: 4px 0 0 18px; padding: 0; }
      .fp-bullets li { margin: 6px 0; }
      .fp-badge {
        display: inline-block;
        font-size: .78rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 999px;
        background: #0ea5e9;
        color: #fff;
        margin-left: 6px;
      }
      .fp-badge--warn { background: #f59e0b; }

      /* === Grid for Dataset & Hypothesis === */
      .fp-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 14px;
      }
      @media (min-width: 920px) {
        .fp-grid { grid-template-columns: 1fr 1fr; }
      }

      /* === Footer === */
      .fp-footer {
        margin-top: 24px;
        padding: 10px 14px;
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        font-size: 0.95rem;
        text-align: center;
        line-height: 1.6;
        letter-spacing: 0.2px;
        color: rgba(255,255,255,0.75);
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
      }

      @media (prefers-color-scheme: light) {
        .fp-card { background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08); }
        .fp-footer { background: rgba(0,0,0,0.03); color: rgba(0,0,0,0.65); }
      }
    </style>
    <div class="fp-wrap">
      <div class="fp-ribbon">Real-Time Global Earthquake Visualisation Dashboard (USGS Data) — Summary</div>
      <div class="fp-card">
        <div class="fp-h2">Introduction to the Case</div>
        <p class="fp-p"><b>Problem:</b> Earthquake data from the United States Geological Survey (USGS) is delivered in raw, technical formats that are difficult for non-experts to interpret.</p>
        <p class="fp-p"><b>Central message:</b> Real-time seismic information becomes meaningful when presented as an interactive visual story.</p>
        <p class="fp-p"><b>Goal:</b> Build an interactive dashboard that reveals where earthquakes occur, how strong they are, and when they happen.</p>
        <p class="fp-p"><b>Narrative:</b> Three core visuals guide the user: a global map (where), a magnitude histogram (how strong), and a timeline (when).</p>
        <p class="fp-p"><b>Target audience:</b> Researchers and students, emergency planners and policymakers, and the general public.</p>
      </div>
      <div class="fp-grid">
        <div class="fp-card">
          <div class="fp-h2">Dataset Introduction</div>
          <p class="fp-p"><b>Source:</b> USGS Earthquake Hazards Program (FDSN Event API).</p>
          <p class="fp-p"><b>Feed:</b> <i>All Earthquakes – Past Day</i> in <b>GeoJSON</b> (time, magnitude, depth, coordinates), updated approximately every minute.</p>
        </div>
        <div class="fp-card">
          <div class="fp-h2">Summary of Analysis & Hypotheses</div>
          <p class="fp-p">Exploration, discovery, and storytelling with Python, Pandas, Plotly, and Streamlit.</p>
          <ul class="fp-bullets">
            <li><b>H1.</b> Stronger earthquakes (≥5.0) concentrate along the Pacific Ring of Fire <span class="fp-badge">Supported</span></li>
            <li><b>H2.</b> Most earthquakes are minor (magnitude &lt; 4.0) <span class="fp-badge">Supported</span></li>
            <li><b>H3.</b> Earthquakes are uniformly distributed across time <span class="fp-badge fp-badge--warn">Partially</span></li>
          </ul>
        </div>
      </div>
      <div class="fp-footer">
        <b>Group VISUALS</b> — Checho Gyeltshen (33465063), Mulitha Jayawardana (35270163), 
        Nima Zangmo (34868584), Vatsal Maniya (35122621), Baghirath Deshani (34719536) • 
        <i>October 31, 2025</i>
      </div>
    </div>
    """)

    st.markdown(html, unsafe_allow_html=True)

    # Centered button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Go to Dashboard", type="primary", use_container_width=True):
            st.session_state.show_dashboard = True
            st.rerun()







def render_main_app():

    st.title("Real-Time Global Earthquake Visualisation Dashboard (USGS Data)")

    if st.button("⬅️ Back to Front Page"):
        st.session_state.show_dashboard = False
        st.rerun()

# ---------- Sidebar: Query Parameters ----------
    with st.sidebar:
        st.title("🔧 Query Parameters")

        # Time window selector
        window_label = st.selectbox(
            "Time window",
            ["Past hour", "Past 24 hours", "Past 7 days", "Custom dates"]
        )
        now_utc = datetime.now(timezone.utc)

        if window_label == "Past hour":
            starttime = now_utc - timedelta(hours=1)
            endtime = now_utc
        elif window_label == "Past 24 hours":
            starttime = now_utc - timedelta(days=1)
            endtime = now_utc
        elif window_label == "Past 7 days":
            starttime = now_utc - timedelta(days=7)
            endtime = now_utc
        else:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date (UTC)", (now_utc - timedelta(days=1)).date())
            with col2:
                end_date = st.date_input("End date (UTC)", now_utc.date())
            # Interpret as full-day bounds
            starttime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            endtime = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

        # Magnitude range
        st.subheader("Magnitude filter")
        minmag, maxmag = st.slider("Min/Max magnitude", 0.0, 10.0, (0.0, 10.0), 0.1)

        # Depth range
        st.subheader("Depth filter (km)")
        mindepth, maxdepth = st.slider("Min/Max depth", 0.0, 700.0, (0.0, 700.0), 1.0)

        # Region mode
        st.subheader("Region filter (choose one)")
        region_mode = st.radio("Mode", ["Global", "Bounding box", "Radius from point"], horizontal=True)

        bbox = None
        circle = None
        if region_mode == "Bounding box":
            st.caption("Set a lat/lon box (South ≤ North, West ≤ East)")
            col1, col2 = st.columns(2)
            with col1:
                minlat = st.number_input("South (min latitude)", value=-60.0, step=0.1, format="%.4f")
                minlon = st.number_input("West (min longitude)", value=100.0, step=0.1, format="%.4f")
            with col2:
                maxlat = st.number_input("North (max latitude)", value=60.0, step=0.1, format="%.4f")
                maxlon = st.number_input("East (max longitude)", value=160.0, step=0.1, format="%.4f")
            bbox = (minlat, maxlat, minlon, maxlon)

        elif region_mode == "Radius from point":
            st.caption("Great-circle search from a center point")
            col1, col2 = st.columns(2)
            with col1:
                lat0 = st.number_input("Center latitude", value=-31.9505, step=0.1, format="%.4f")
                lon0 = st.number_input("Center longitude", value=115.8605, step=0.1, format="%.4f")
            with col2:
                radius_km = st.number_input("Radius (km)", value=500.0, min_value=1.0, step=10.0)
            circle = (lat0, lon0, radius_km)

        st.subheader("Advanced")
        orderby = st.selectbox("Order by", ["time", "time-asc", "magnitude", "magnitude-asc"], index=0)
        limit = st.number_input("Max results (limit)", min_value=1, max_value=20000, value=20000, step=100)

        st.divider()
        run_btn = st.button("Fetch data", type="primary", use_container_width=True)

    # ---------- Fetch from USGS ----------
    @st.cache_data(show_spinner=True, ttl=60)
    def fetch_usgs_geojson(params: dict) -> dict:
        r = requests.get(USGS_API, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def build_query_params():
        q = {
            "format": "geojson",
            "starttime": starttime.strftime("%Y-%m-%dT%H:%M:%S"),
            "endtime": endtime.strftime("%Y-%m-%dT%H:%M:%S"),
            "minmagnitude": minmag,
            "maxmagnitude": maxmag,
            "orderby": orderby,
            "limit": int(limit),
        }
        if region_mode == "Bounding box" and bbox:
            q.update({
                "minlatitude": bbox[0],
                "maxlatitude": bbox[1],
                "minlongitude": bbox[2],
                "maxlongitude": bbox[3],
            })
        elif region_mode == "Radius from point" and circle:
            lat0, lon0, rkm = circle
            q.update({
                "latitude": lat0,
                "longitude": lon0,
                "maxradiuskm": rkm,
            })
        return q

    def clean_earthquakes(geojson: dict) -> pd.DataFrame:
        feats = geojson.get("features", [])
        if not feats:
            return pd.DataFrame(columns=[
                "time","place","magnitude","depth","lat","lon","event_type","alert_level","url","id"
            ])
        df = pd.json_normalize(feats)

        keep = [
            "id",
            "properties.time",
            "properties.place",
            "properties.mag",
            "properties.type",
            "properties.alert",
            "properties.url",
            "geometry.coordinates",
        ]
        df = df[[c for c in keep if c in df.columns]].copy()

        # Split coords [lon, lat, depth]
        coords = pd.DataFrame(df["geometry.coordinates"].tolist(), index=df.index)
        df["lon"] = coords.get(0)
        df["lat"] = coords.get(1)
        df["depth"] = coords.get(2)
        df.drop(columns=["geometry.coordinates"], inplace=True, errors="ignore")

        # Rename, convert, order
        df.rename(columns={
            "properties.time":  "time_epoch_ms",
            "properties.place": "place",
            "properties.mag":   "magnitude",
            "properties.type":  "event_type",
            "properties.alert": "alert_level",
            "properties.url":   "url",
        }, inplace=True)

        df["time"] = pd.to_datetime(df["time_epoch_ms"], unit="ms", utc=True)
        df.drop(columns=["time_epoch_ms"], inplace=True)

        for col in ["magnitude", "depth", "lat", "lon"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Depth range post-filter (client-side)
        df = df[(df["depth"].isna()) | ((df["depth"] >= mindepth) & (df["depth"] <= maxdepth))]

        order = ["time","place","magnitude","depth","lat","lon","event_type","alert_level","url","id"]
        df = df[[c for c in order if c in df.columns]]
        return df

    # Initial auto-fetch on first load, or when user clicks
    query_params = build_query_params()
    if run_btn or "df_cache" not in st.session_state:
        try:
            geo = fetch_usgs_geojson(query_params)
            st.session_state["df_cache"] = clean_earthquakes(geo)
            st.session_state["q_cache"] = query_params
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            st.stop()

    df = st.session_state["df_cache"]

    # ---------- Tabs ----------
    tab1, tab2, tab3 = st.tabs(["🗺️ Interactive dashboard", "🎬 Storyboarding visuals", "🔎 Exploration"])

    with tab1:
        render_interactive(df)

    with tab2:
        render_visuals(df)

    with tab3:
        render_exploration(df)


# ---------- 3) Entry Point ----------
def main():
    # Show front page first time only
    if "show_dashboard" not in st.session_state:
        st.session_state.show_dashboard = False

    if st.session_state.show_dashboard:
        render_main_app()
    else:
        render_front_page()

if __name__ == "__main__":
    main()