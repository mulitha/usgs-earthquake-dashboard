# tabs_visuals.py — ALL VISUALS with updated titles
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

def render_visuals(df: pd.DataFrame):
    st.subheader("Storyboard + Visuals")

    if df.empty:
        st.info("No data for the selected query. Change the sidebar filters and fetch again.", icon="ℹ️")
        return


    # ------------- HISTOGRAM -------------
    st.markdown("### Magnitude Distribution of Earthquakes")
    if "magnitude" in df.columns and df["magnitude"].notna().any():
        mag = pd.to_numeric(df["magnitude"], errors="coerce").dropna()
        fig_hist = px.histogram(
            mag, nbins=30, labels={"value":"Magnitude", "count":"Events"},
            title="Magnitude Distribution of Earthquakes"
        )
        fig_hist.update_layout(margin=dict(l=0,r=0,t=60,b=0))
        st.plotly_chart(fig_hist, use_container_width=True, key="v_hist")
    else:
        st.info("Magnitude column missing for histogram.", icon="ℹ️")

    st.divider()

    # ------------- TIMELINE -------------
    st.markdown("### Hourly Earthquake Events (UTC)")
    if "time" in df.columns and df["time"].notna().any():
        hourly = df.set_index("time").resample("1H").size().rename("events")
        fig_line = px.line(
            hourly.reset_index(), x="time", y="events",
            markers=True, title="Hourly Earthquake Events (UTC)"
        )
        fig_line.update_layout(margin=dict(l=0,r=0,t=60,b=0))
        st.plotly_chart(fig_line, use_container_width=True, key="v_timeline")
    else:
        st.info("Time column missing for timeline.", icon="ℹ️")

    st.divider()

    # ------------- BOX PLOTS -------------
    st.markdown("### Distribution Box Plots")
    cols = st.columns(2)

    if "magnitude" in df.columns and df["magnitude"].notna().any():
        with cols[0]:
            fig_box_mag = px.box(
                df, y="magnitude", points="outliers",
                title="Magnitude Distribution (Box Plot)"
            )
            fig_box_mag.update_layout(margin=dict(l=0,r=0,t=60,b=0), height=400)
            st.plotly_chart(fig_box_mag, use_container_width=True, key="v_box_mag")
    else:
        cols[0].info("No magnitude values for box plot.", icon="ℹ️")

    if "depth" in df.columns and df["depth"].notna().any():
        with cols[1]:
            fig_box_dep = px.box(
                df, y="depth", points="outliers",
                title="Depth Distribution (Box Plot)"
            )
            fig_box_dep.update_layout(margin=dict(l=0,r=0,t=60,b=0), height=400)
            st.plotly_chart(fig_box_dep, use_container_width=True, key="v_box_depth")
    else:
        cols[1].info("No depth values for box plot.", icon="ℹ️")

    st.divider()

    # ------------- SCATTER -------------
    st.markdown("### Magnitude vs Depth Scatter Plot")
    if {"magnitude","depth"}.issubset(df.columns) and df[["magnitude","depth"]].notna().any(axis=None):
        fig_scatter = px.scatter(
            df, x="depth", y="magnitude",
            hover_name="place", hover_data=["time"],
            title="Magnitude vs Depth Scatter Plot"
        )
        fig_scatter.update_layout(margin=dict(l=0,r=0,t=60,b=0), height=460)
        st.plotly_chart(fig_scatter, use_container_width=True, key="v_scatter")
    else:
        st.info("Need both magnitude and depth for scatter.", icon="ℹ️")

    st.divider()

    # ------------- HEATMAP -------------
    st.markdown("### Earthquake Events Heatmap (Hour × Magnitude Bin)")
    if "time" in df.columns and "magnitude" in df.columns and df["time"].notna().any() and df["magnitude"].notna().any():
        tmp = df[["time","magnitude"]].dropna().copy()
        tmp["hour"] = tmp["time"].dt.hour
        bins = [0, 2, 4, 6, 8, 10]
        labels = ["<2.0","2–3.9","4–5.9","6–7.9","8+"]
        tmp["mag_bin"] = pd.cut(tmp["magnitude"], bins=bins, labels=labels, include_lowest=True, right=True)
        piv = tmp.pivot_table(index="hour", columns="mag_bin", values="magnitude", aggfunc="count").fillna(0)
        fig_hm = px.imshow(
            piv, aspect="auto", origin="lower",
            labels=dict(x="Magnitude bin", y="Hour (UTC)", color="Events"),
            title="Earthquake Events Heatmap (Hour × Magnitude Bin)"
        )
        fig_hm.update_layout(margin=dict(l=0,r=0,t=60,b=0), height=520)
        st.plotly_chart(fig_hm, use_container_width=True, key="v_heatmap")
    else:
        st.info("Need time and magnitude for heatmap.", icon="ℹ️")
