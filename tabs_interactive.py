# tabs_interactive.py — User-friendly interactive dashboard (no data table)
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

def _tz_convert(series, tz_out="Australia/Sydney"):
    try:
        s = pd.to_datetime(series, utc=True)
        return s.dt.tz_convert(tz_out)
    except Exception:
        return series

def _largest(df):
    has_mag = ("magnitude" in df.columns) and df["magnitude"].notna().any()
    return df.loc[df["magnitude"].idxmax()] if has_mag else None

def _most_recent(df):
    has_time = ("time" in df.columns) and df["time"].notna().any()
    return df.sort_values("time", ascending=False).iloc[0] if has_time and len(df) else None

def render_interactive(df: pd.DataFrame):
    st.subheader("Interactive Dashboard")

    if df.empty:
        st.info("No data for the selected query. Adjust the sidebar filters and fetch again.", icon="ℹ️")
        return

    # -------------------- QUICK FILTERS (client-side) --------------------
    with st.container():
        st.markdown("#### Quick Filters")
        c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.4, 2.2])

        mag_choice = c1.radio("Magnitude", ["All", "≥4.0", "≥5.0", "≥6.0"], index=0, horizontal=True)
        depth_choice = c2.radio("Depth (km)", ["All", "≤30", "30–70", "70–300", "300–700"], index=0, horizontal=True)

        alerts = sorted([x for x in df.get("alert_level", pd.Series()).dropna().unique().tolist()])
        alert_sel = c3.multiselect("Alert level", alerts, default=alerts)

        types = sorted([x for x in df.get("event_type", pd.Series()).dropna().unique().tolist()])
        type_sel = c4.multiselect("Event type", types, default=types)

    c5, c6, c7 = st.columns([2, 1.4, 1.2])
    search_text = c5.text_input("Search in place", placeholder="e.g., Japan, Alaska, Indonesia")
    tz_display = c6.selectbox("Time display", ["UTC", "Australia/Sydney"], index=0)
    show_only_with_coords = c7.checkbox("Map-ready rows only (has lat/lon)", value=True)

    # Apply quick filters
    dfv = df.copy()

    if "magnitude" in dfv.columns:
        if mag_choice == "≥4.0": dfv = dfv[dfv["magnitude"] >= 4.0]
        elif mag_choice == "≥5.0": dfv = dfv[dfv["magnitude"] >= 5.0]
        elif mag_choice == "≥6.0": dfv = dfv[dfv["magnitude"] >= 6.0]

    if "depth" in dfv.columns:
        if depth_choice == "≤30":
            dfv = dfv[dfv["depth"] <= 30]
        elif depth_choice == "30–70":
            dfv = dfv[(dfv["depth"] > 30) & (dfv["depth"] <= 70)]
        elif depth_choice == "70–300":
            dfv = dfv[(dfv["depth"] > 70) & (dfv["depth"] <= 300)]
        elif depth_choice == "300–700":
            dfv = dfv[(dfv["depth"] > 300) & (dfv["depth"] <= 700)]

    if "alert_level" in dfv.columns and len(alerts):
        dfv = dfv[dfv["alert_level"].isin(alert_sel) | dfv["alert_level"].isna()]
    if "event_type" in dfv.columns and len(types):
        dfv = dfv[dfv["event_type"].isin(type_sel)]
    if search_text:
        dfv = dfv[dfv["place"].str.contains(search_text, case=False, na=False)]
    if show_only_with_coords and {"lat","lon"}.issubset(dfv.columns):
        dfv = dfv.dropna(subset=["lat","lon"])

    # Timezone conversion for display (used in tooltips)
    dfv_disp = dfv.copy()
    if tz_display == "Australia/Sydney" and "time" in dfv.columns:
        dfv_disp["time_local"] = _tz_convert(dfv["time"], "Australia/Sydney")
        time_col_to_show = "time_local"
    else:
        time_col_to_show = "time"

    # -------------------- KPI ROW --------------------
    st.markdown("#### Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Events", f"{len(dfv):,}")
    if "magnitude" in dfv.columns and dfv["magnitude"].notna().any():
        c2.metric("Max magnitude", f"{dfv['magnitude'].max():.1f}")
        c3.metric("Median magnitude", f"{dfv['magnitude'].median():.2f}")
    else:
        c2.metric("Max magnitude", "–"); c3.metric("Median magnitude", "–")
    if "depth" in dfv.columns and dfv["depth"].notna().any():
        c4.metric("Mean depth (km)", f"{dfv['depth'].mean():.1f}")
    else:
        c4.metric("Mean depth (km)", "–")
    if "time" in dfv.columns and dfv["time"].notna().any():
        c5.metric("Time range",
                  f"{dfv['time'].min().strftime('%Y-%m-%d %H:%M')} → {dfv['time'].max().strftime('%Y-%m-%d %H:%M')}")
    else:
        c5.metric("Time range", "–")

    # -------------------- SPOTLIGHT CARDS --------------------
    st.markdown("#### Spotlight")
    left, right = st.columns(2, vertical_alignment="top")
    largest = _largest(dfv)
    recent = _most_recent(dfv)

    with left:
        st.markdown("**Largest event**")
        if largest is not None:
            st.write(f"- **Magnitude:** {largest.get('magnitude','–')}")
            st.write(f"- **Depth:** {largest.get('depth','–')} km")
            st.write(f"- **Time ({'Local' if tz_display!='UTC' else 'UTC'}):** "
                     f"{(largest[time_col_to_show] if time_col_to_show in largest else largest.get('time'))}")
            st.write(f"- **Place:** {largest.get('place','–')}")
            if isinstance(largest.get("url"), str): st.write(f"[USGS event page]({largest['url']})")
        else:
            st.info("No magnitude available to identify the largest event.", icon="ℹ️")

    with right:
        st.markdown("**Most recent event**")
        if recent is not None:
            st.write(f"- **Magnitude:** {recent.get('magnitude','–')}")
            st.write(f"- **Depth:** {recent.get('depth','–')} km")
            st.write(f"- **Time ({'Local' if tz_display!='UTC' else 'UTC'}):** "
                     f"{(recent[time_col_to_show] if time_col_to_show in recent else recent.get('time'))}")
            st.write(f"- **Place:** {recent.get('place','–')}")
            if isinstance(recent.get("url"), str): st.write(f"[USGS event page]({recent['url']})")
        else:
            st.info("No time available to identify most recent event.", icon="ℹ️")

    st.divider()

    # -------------------- MAP --------------------
    st.subheader("Earthquake Locations by Magnitude")
    if {"lat","lon"}.issubset(dfv.columns) and dfv[["lat","lon"]].notna().any(axis=None):
        fig_map = px.scatter_mapbox(
            dfv_disp.dropna(subset=["lat","lon"]),
            lat="lat", lon="lon",
            color="magnitude",
            size="magnitude",
            hover_name="place",
            hover_data={time_col_to_show: True, "depth": True, "lat": False, "lon": False, "magnitude": True},
            color_continuous_scale="Turbo",
            size_max=18,
            zoom=1,
            height=520,
        )
        fig_map.update_layout(mapbox_style="open-street-map", margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Map requires valid latitude/longitude rows.", icon="ℹ️")

    st.divider()

    # -------------------- INTERACTIVE CHART #2 --------------------
    # 1) Interactive Timeline (Magnitude over Time) with range slider
    st.subheader("Magnitude over Time (Interactive)")
    if "time" in dfv_disp.columns and "magnitude" in dfv_disp.columns and dfv_disp["time"].notna().any():
        fig_ts = px.scatter(
            dfv_disp.sort_values("time"),
            x="time", y="magnitude",
            hover_name="place",
            hover_data={time_col_to_show: True, "depth": True},
            title=None
        )
        fig_ts.update_traces(mode="markers")
        fig_ts.update_xaxes(rangeslider_visible=True)
        fig_ts.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=420)
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("Need time and magnitude for the interactive timeline.", icon="ℹ️")

    st.subheader("Magnitude Bin Breakdown")
    if "magnitude" in dfv.columns and dfv["magnitude"].notna().any():
        bins = [0, 2, 4, 6, 8, 10]
        labels = ["<2.0","2–3.9","4–5.9","6–7.9","8+"]
        mag_bin = pd.cut(dfv["magnitude"], bins=bins, labels=labels, include_lowest=True, right=True)

        bin_counts = mag_bin.value_counts().sort_index().rename("Events")
        df_bins = bin_counts.reset_index()
        df_bins.columns = ["Magnitude range", "Events"]  # <-- KEY FIX

        fig_bins = px.bar(df_bins, x="Magnitude range", y="Events", title=None)
        fig_bins.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=360)
        st.plotly_chart(fig_bins, use_container_width=True)
    else:
        st.info("Magnitude missing for bin breakdown.", icon="ℹ️")

