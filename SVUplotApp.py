import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="CSV Viewer & Plotter")

st.title("CSV File Viewer and Plotter")

# Upload CSV file
uploaded_file = st.file_uploader("Upload CSV file (semicolon separated)", type=["csv"])

@st.cache_data
def load_data(file):
    # Read CSV with semicolon separator
    df = pd.read_csv(file, sep=';')
    return df

def process_time(df_subset, ref_time):
    # Convert timestamp to hours elapsed from reference time
    time_deltas = []
    for ts in df_subset["Timestamp"]:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
        delta_hours = (dt - ref_time).total_seconds() / 3600
        time_deltas.append(delta_hours)
    return time_deltas

if uploaded_file:
    try:
        df = load_data(uploaded_file)

        st.subheader("Data Preview")
        st.dataframe(df.head(20))

        # Sliders for x-axis range (time in hours)
        st.sidebar.subheader("X-axis (Time in hours) Limits")
        x_min = st.sidebar.slider("X Min", 0.0, 10.0, 0.0, 0.1)
        x_max = st.sidebar.slider("X Max", 0.0, 10.0, 4.0, 0.1)

        # Filter data subsets
        df1 = df[df["Name"].str.contains("Vial temperature")].copy()
        df2 = df[df["Name"].str.contains("Heater power")].copy()
        df3 = df[df["Name"].str.contains("Capacitive")].copy()
        df4 = df[df["Name"].str.contains("Pirani")].copy()

        if df1.empty:
            st.warning("No data found with 'Vial temperature' in Name column.")
        else:
            # Reference time for time delta calculation
            ref_time = datetime.strptime(df1["Timestamp"].iloc[0], "%Y-%m-%d %H:%M:%S.%f")

            # Calculate time deltas
            df1["Time (hours)"] = process_time(df1, ref_time)
            df2["Time (hours)"] = process_time(df2, ref_time)
            df3["Time (hours)"] = process_time(df3, ref_time)
            df4["Time (hours)"] = process_time(df4, ref_time)

            # Create plotly subplots for each dataset
            def create_trace(df_sub, name, color):
                # Filter data in selected x-axis range
                mask = (df_sub["Time (hours)"] >= x_min) & (df_sub["Time (hours)"] <= x_max)
                filtered = df_sub.loc[mask]
                return go.Scatter(
                    x=filtered["Time (hours)"],
                    y=filtered["Value"],
                    mode='lines',
                    line=dict(color=color),
                    name=name
                )

            fig = go.Figure()
            fig.add_trace(create_trace(df1, "Vial temperature", "#000000"))
            fig.add_trace(create_trace(df2, "Heater power", "#333333"))
            fig.add_trace(create_trace(df3, "Capacitive", "#666666"))
            fig.add_trace(create_trace(df4, "Pirani", "#999999"))

            fig.update_layout(
                title="Sensor Data Over Time",
                xaxis_title="Time (hours)",
                yaxis_title="Value",
                legend_title="Sensor",
                height=600,
                template="plotly_white"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Prepare Excel file for download
            def to_excel():
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df1.to_excel(writer, sheet_name='Vial_temperature', index=False)
                    df2.to_excel(writer, sheet_name='Heater_power', index=False)
                    df3.to_excel(writer, sheet_name='Capacitive', index=False)
                    df4.to_excel(writer, sheet_name='Pirani', index=False)
                processed_data = output.getvalue()
                return processed_data

            excel_data = to_excel()

            st.download_button(
                label="Download Excel file",
                data=excel_data,
                file_name="processed_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.info("Please upload a CSV file to get started.")
