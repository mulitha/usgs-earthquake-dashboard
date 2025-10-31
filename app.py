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
