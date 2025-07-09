import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from PIL import Image
import plotly.graph_objects as go


st.set_page_config(layout="wide", page_title="Lyo Mono DATA export")

# Display logo
logo = Image.open("Rheavita_logo.png")  # 👈 Make sure the filename matches your image
st.image(logo, width=200)  # 👈 Adjust size as needed

st.title("CSV File Viewer and Plotter")
st.markdown(
    """
    <div style="text-align: center;">
        <img src="Rheavita_logo.png" width="180">
    </div>
    """,
    unsafe_allow_html=True
)

# Title
st.markdown("<h1 style='text-align: center; color: white;'>CSV Signal Viewer & Exporter</h1>", unsafe_allow_html=True)

# Upload CSV file
uploaded_file = st.file_uploader(" Upload your CSV file (semicolon separated)", type=["csv"])

@st.cache_data
def load_data(file):
    df = pd.read_csv(file, sep=';')
    return df

def process_time(df_subset, ref_time):
    time_deltas = []
    for ts in df_subset["Timestamp"]:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
        delta_hours = (dt - ref_time).total_seconds() / 3600
        time_deltas.append(delta_hours)
    return time_deltas

if uploaded_file:
    try:
        df = load_data(uploaded_file)

        st.subheader(" Data Preview")
        st.dataframe(df.head(20), use_container_width=True)

        st.sidebar.header("🔧 Settings")
        x_min = st.sidebar.slider("X Min (hours)", 0.0, 10.0, 0.0, 0.1)
        x_max = st.sidebar.slider("X Max (hours)", 0.0, 10.0, 4.0, 0.1)

        # Filter signals
        signals = {
            "Vial temperature": "Black",
            "Heater power": "Black",
            "Capacitive": "#Black",
            "Pirani": "Black"
        }

        selected_signals = st.sidebar.multiselect("📈 Select signals to plot/export:", list(signals.keys()), default=list(signals.keys()))

        signal_dfs = {}
        ref_time = None

        for label in selected_signals:
            signal_df = df[df["Name"].str.contains(label)].copy()
            if not signal_df.empty:
                if ref_time is None:
                    ref_time = datetime.strptime(signal_df["Timestamp"].iloc[0], "%Y-%m-%d %H:%M:%S.%f")
                signal_df["Time (hours)"] = process_time(signal_df, ref_time)
                signal_dfs[label] = signal_df

        # Plot
        st.subheader(" Signal Plots")
        for label, data in signal_dfs.items():
            mask = (data["Time (hours)"] >= x_min) & (data["Time (hours)"] <= x_max)
            filtered = data.loc[mask]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=filtered["Time (hours)"],
                y=filtered["Value"],
                mode='lines',
                line=dict(color=signals[label], width=2),
                name=label
            ))
            fig.update_layout(
                title=label,
                template="plotly_dark",
                height=300,
                margin=dict(l=30, r=30, t=40, b=30),
                xaxis_title="Time (hours)",
                yaxis_title="Value",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Export to Excel
        st.subheader(" Export Data to Excel")
        export_filename = st.text_input("Enter filename (no extension):", value="exported_signals")

        if st.button("Export Selected Signals"):
            if signal_dfs:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for label, data in signal_dfs.items():
                        data.to_excel(writer, sheet_name=label.replace(" ", "_"), index=False)
                st.download_button(
                    label=" Download Excel File",
                    data=output.getvalue(),
                    file_name=f"{export_filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("No signals selected or available to export.")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")

else:
    st.info(" Upload a CSV file to begin.")
