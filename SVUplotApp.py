import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import io
from PIL import Image

st.set_page_config(layout="wide", page_title="Rheavita Signal Viewer")

# Logo
logo = Image.open("Rheavita_logo.png")
st.image(logo, width=200)

st.title("📈 Rheavita Signal Viewer (Multi-file Comparison)")

# Upload multiple CSV files
uploaded_files = st.file_uploader(
    "Upload one or more semicolon-separated CSV files", type=["csv"], accept_multiple_files=True
)

@st.cache_data
def load_data(file):
    return pd.read_csv(file, sep=';')

def process_time(df_subset, ref_time, offset=0.0):
    return [
        ((datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f") - ref_time).total_seconds() / 3600) + offset
        for ts in df_subset["Timestamp"]
    ]

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) loaded successfully.")

    all_data = []
    ref_times = []
    
    # Display signal options from first file
    first_df = load_data(uploaded_files[0])
    available_signals = first_df["Name"].unique().tolist()

    with st.sidebar:
        st.markdown("### 🔧 Global Plot Settings")
        x_min = st.slider("X Min (hours)", 0.0, 4, 0.0, 0.05)
        x_max = st.slider("X Max (hours)", 0.0, 4, 4.0, 0.05)
        selected_signals = st.multiselect(
            "Select signals to plot",
            options=available_signals,
            default=["Vial temperature", "Heater power", "Capacitive", "Pirani"]
        )
        filename = st.text_input("Export filename (no extension)", value="rheavita_signals")

    file_offsets = {}
    for i, file in enumerate(uploaded_files):
        with st.sidebar:
            offset = st.slider(f"⏱ Offset for File {i+1} ({file.name})", -2, 2, 0.0, 0.05)
            file_offsets[file.name] = offset

        df = load_data(file)
        ref_time = datetime.strptime(df["Timestamp"].iloc[0], "%Y-%m-%d %H:%M:%S.%f")
        ref_times.append(ref_time)
        all_data.append((file.name, df, ref_time))

    plots = {signal: go.Figure() for signal in selected_signals}

    for file_name, df, ref_time in all_data:
        offset = file_offsets[file_name]
        for signal in selected_signals:
            df_signal = df[df["Name"].str.contains(signal)].copy()
            df_signal["Time (hours)"] = process_time(df_signal, ref_time, offset)
            df_signal = df_signal[
                (df_signal["Time (hours)"] >= x_min) & (df_signal["Time (hours)"] <= x_max)
            ]

            if not df_signal.empty:
                plots[signal].add_trace(go.Scatter(
                    x=df_signal["Time (hours)"],
                    y=df_signal["Value"],
                    mode="lines",
                    name=f"{signal} ({file_name})"
                ))

    for signal, fig in plots.items():
        fig.update_layout(
            title=signal,
            xaxis_title="Time (hours)",
            yaxis_title="Value",
            template="plotly_dark",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Export button
    export_btn = st.button("📤 Export selected signals to Excel")

    if export_btn:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for file_name, df, ref_time in all_data:
                offset = file_offsets[file_name]
                for signal in selected_signals:
                    df_signal = df[df["Name"].str.contains(signal)].copy()
                    df_signal["Time (hours)"] = process_time(df_signal, ref_time, offset)
                    df_signal = df_signal[
                        (df_signal["Time (hours)"] >= x_min) & (df_signal["Time (hours)"] <= x_max)
                    ]
                    if not df_signal.empty:
                        sheet_name = f"{signal[:20]}_{file_name[:10]}"[:31]
                        df_signal.to_excel(writer, sheet_name=sheet_name, index=False)

        st.download_button(
            label="📥 Download Excel file",
            data=output.getvalue(),
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Upload one or more CSV files to get started.")
