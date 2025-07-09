import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import io

# App configuration
st.set_page_config(page_title="Rheavita Signal Viewer", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for black look (overrides Streamlit defaults)
st.markdown("""
    <style>
        body, .stApp {
            background-color: #111;
            color: #fff;
        }
        .stTextInput, .stSelectbox, .stSlider, .stFileUploader {
            background-color: #222;
        }
        .stButton button {
            background-color: #444;
            color: white;
        }
        .stExpanderHeader {
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Rheavita Signal Viewer")

# Upload CSV
uploaded_file = st.file_uploader("Upload a semicolon-separated CSV file", type=["csv"])

# Load Data
@st.cache_data
def load_data(file):
    df = pd.read_csv(file, sep=';')
    return df

def process_time(df_subset, ref_time):
    return [
        (datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f") - ref_time).total_seconds() / 3600
        for ts in df_subset["Timestamp"]
    ]

if uploaded_file:
    try:
        df = load_data(uploaded_file)
        st.success("✅ CSV file loaded successfully.")

        with st.expander(" Data Preview"):
            st.dataframe(df.head(20), use_container_width=True)

        with st.sidebar:
            st.markdown("### 🔧 Plot Settings")
            x_min = st.slider("X Min (hours)", 0.0, 10.0, 0.0, 0.1)
            x_max = st.slider("X Max (hours)", 0.0, 10.0, 4.0, 0.1)
            selected_signals = st.multiselect(
                "Select signals to plot/export",
                options=df["Name"].unique().tolist(),
                default=["Vial temperature", "Heater power", "Capacitive", "Pirani"]
            )
            filename = st.text_input("Export filename (no extension)", value="rheavita_signals")

        if selected_signals:
            plots = []
            ref_time = datetime.strptime(df["Timestamp"].iloc[0], "%Y-%m-%d %H:%M:%S.%f")

            for signal in selected_signals:
                df_signal = df[df["Name"].str.contains(signal)].copy()
                df_signal["Time (hours)"] = process_time(df_signal, ref_time)

                # Filter by time
                df_signal = df_signal[
                    (df_signal["Time (hours)"] >= x_min) & (df_signal["Time (hours)"] <= x_max)
                ]

                # Plot
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_signal["Time (hours)"],
                    y=df_signal["Value"],
                    mode='lines',
                    name=signal,
                    line=dict(width=2)
                ))
                fig.update_layout(
                    title=signal,
                    xaxis_title="Time (hours)",
                    yaxis_title="Value",
                    template="plotly_dark",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

                # Save for export
                plots.append((signal, df_signal))

            # Export Button
            export_btn = st.button(" Export selected signals to Excel")
            if export_btn:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    for signal_name, df_signal in plots:
                        sheet = signal_name[:31]  # Excel sheet name limit
                        df_signal.to_excel(writer, sheet_name=sheet, index=False)
                    writer.save()
                st.download_button(
                    label=" Download Excel file",
                    data=output.getvalue(),
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        else:
            st.warning("Please select at least one signal to display.")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
else:
    st.info(" Upload a CSV file to get started.")

