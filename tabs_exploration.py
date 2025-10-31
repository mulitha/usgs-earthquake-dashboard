# tabs_exploration.py — SIMPLE INSIGHTS ONLY (no charts, no 'key' on metrics)
import numpy as np
import pandas as pd
import streamlit as st

def _safe(series, fn, default=None):
    if series is None:
        return default
    if getattr(series, "dtype", None) == "O":
        series = pd.to_numeric(series, errors="coerce")
    s = series.dropna()
    return fn(s) if len(s) else default

def _region_from_place(place: str) -> str:
    if not isinstance(place, str) or not place:
        return "Unknown"
    if "," in place:
        tail = place.split(",")[-1].strip()
        return tail or "Unknown"
    if " of " in place.lower():
        return place.lower().split(" of ")[-1].strip().title()
    return place

def _insight_bullets(df: pd.DataFrame) -> list[str]:
    bullets = []
    if df.empty:
        return ["No events returned for the current query."]

    # Magnitude
    if "magnitude" in df.columns:
        mag = pd.to_numeric(df["magnitude"], errors="coerce").dropna()
        if len(mag):
            bullets.append(f"Typical magnitude ≈ {mag.median():.1f} (median), max {mag.max():.1f}.")
            bullets.append(f"~{(mag < 4).mean()*100:.0f}% of events are minor (<4.0); "
                           f"~{(mag >= 5).mean()*100:.0f}% are ≥5.0.")

    # Depth
    if "depth" in df.columns:
        dep = pd.to_numeric(df["depth"], errors="coerce").dropna()
        if len(dep):
            bullets.append(f"{(dep <= 30).mean()*100:.0f}% are shallow (≤30 km). "
                           f"Depth range {dep.min():.0f}–{dep.max():.0f} km (avg {dep.mean():.0f} km).")

    # Time span
    if "time" in df.columns and df["time"].notna().any():
        tmin, tmax = df["time"].min(), df["time"].max()
        bullets.append(f"Time coverage: UTC {tmin.strftime('%Y-%m-%d %H:%M')} → {tmax.strftime('%Y-%m-%d %H:%M')}.")

    # Locations (derived)
    if "place" in df.columns and df["place"].notna().any():
        top_regions = df["place"].apply(_region_from_place).value_counts().head(3)
        if len(top_regions):
            bullets.append("Most frequent locations: " + "; ".join(f"{k} ({v})" for k, v in top_regions.items()) + ".")

    # Alert/type
    if "alert_level" in df.columns and df["alert_level"].notna().any():
        ac = df["alert_level"].value_counts()
        bullets.append(f"Alert levels present; most common: {ac.idxmax()} ({ac.max()} events).")
    if "event_type" in df.columns and df["event_type"].notna().any():
        bullets.append("Event types include: " + ", ".join(df["event_type"].value_counts().index[:3]) + " ...")

    return bullets

def render_exploration(df: pd.DataFrame):
    st.subheader("Key insights (numbers only)")

    # ----- KPI row (no 'key' on metrics) -----
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Events", f"{len(df):,}")

    if not df.empty and "magnitude" in df.columns:
        mag = pd.to_numeric(df["magnitude"], errors="coerce")
        maxmag = _safe(mag, pd.Series.max, None)
        medmag = _safe(mag, pd.Series.median, None)
        meandepth = None
        if "depth" in df.columns:
            meandepth = _safe(pd.to_numeric(df["depth"], errors="coerce"), pd.Series.mean, None)

        c2.metric("Max magnitude", f"{maxmag:.1f}" if maxmag is not None else "–")
        c3.metric("Median mag", f"{medmag:.2f}" if medmag is not None else "–")
        c4.metric("Mean depth (km)", f"{meandepth:.1f}" if meandepth is not None else "–")
    else:
        c2.metric("Max magnitude", "–")
        c3.metric("Median mag", "–")
        c4.metric("Mean depth (km)", "–")

    st.divider()

    # ----- Largest event (facts only) -----
    st.markdown("### Largest event")
    if not df.empty and "magnitude" in df.columns and df["magnitude"].notna().any():
        top = df.loc[df["magnitude"].idxmax()]
        left, right = st.columns([1, 3], vertical_alignment="top")
        with left:
            st.metric("Magnitude", f"{top['magnitude']:.1f}")
            st.write(f"**Depth:** {top.get('depth', '–')} km")
        with right:
            st.write(f"**Place:** {top.get('place','–')}")
            st.write(f"**Time (UTC):** {top.get('time')}")
            if isinstance(top.get("url"), str):
                st.write(f"[USGS event page]({top['url']})")
    else:
        st.info("No magnitude available to determine a largest event.", icon="ℹ️")

    st.divider()

    # ----- Compact numeric tables (no charts) -----
    st.markdown("### Distributions (compact tables)")
    tables = []

    if not df.empty and "magnitude" in df.columns and df["magnitude"].notna().any():
        mag = pd.to_numeric(df["magnitude"], errors="coerce").dropna()
        perc = pd.Series({
            "Min": mag.min(),
            "25th": mag.quantile(0.25),
            "Median": mag.median(),
            "75th": mag.quantile(0.75),
            "95th": mag.quantile(0.95),
            "Max": mag.max(),
        }).round(2).to_frame("Magnitude")
        tables.append(("Magnitude percentiles", perc))

    if "depth" in df.columns and pd.to_numeric(df["depth"], errors="coerce").notna().any():
        dep = pd.to_numeric(df["depth"], errors="coerce").dropna()
        dsum = pd.Series({
            "Min (km)": round(dep.min(), 1),
            "Median (km)": round(dep.median(), 1),
            "Mean (km)": round(dep.mean(), 1),
            "Max (km)": round(dep.max(), 1),
            "Shallow ≤30km (%)": round((dep <= 30).mean() * 100, 0),
        }).to_frame("Depth")
        tables.append(("Depth summary", dsum))

    if "time" in df.columns and df["time"].notna().any():
        hourly = df.set_index("time").resample("1H").size()
        hsum = pd.Series({
            "Active hours": int((hourly > 0).sum()),
            "Peak hour events": int(hourly.max()),
            "Average per active hour": round(hourly[hourly > 0].mean(), 2) if (hourly > 0).any() else 0,
        }).to_frame("Counts")
        tables.append(("Hourly frequency (counts)", hsum))

    if tables:
        for title, tdf in tables:
            st.markdown(f"**{title}**")
            st.dataframe(tdf, use_container_width=True)
    else:
        st.info("No numeric fields available to summarize.", icon="ℹ️")

    st.divider()

    # ----- Bullet insights (plain text) -----
    st.markdown("### Bullet insights")
    for line in _insight_bullets(df):
        st.write(f"- {line}")
