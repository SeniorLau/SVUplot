import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import plotly.graph_objects as go

# App config
st.set_page_config(layout="wide", page_title="CSV Viewer & Plotter")
st.title("CSV File Viewer and Plotter")

# Upload CSV file
uploaded_file = st.file_uploader("Upload CSV file (semicolon separated)", type=["csv"])

# Load and cache CSV
@st.cache_data
def load_data(file):
    return pd.read_csv(file, sep=';')

# Process time for plotting
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

        st.subheader("Data Preview")
        st.dataframe(df.head(20), use_container_width=True)

        # Sidebar: X-axis limits
        st.sidebar.subheader("X-axis (Time in hours) Limits")
        x_min = st.sidebar.slider("X Min", 0.0, 10.0, 0.0, 0.1)
        x_max = st.sidebar.slider("X Max", 0.0, 10.0, 4.0, 0.1)

        # Sidebar: Signal selection for export
        st.sidebar.subheader("Select Signals to Export")
        export_vial = st.sidebar.checkbox("Vial temperature", value=True)
        export_heater = st.sidebar.checkbox("Heater power", value=True)
        export_cap = st.sidebar.checkbox("Capacitive", value=True)
        export_pirani = st.sidebar.checkbox("Pirani", value=True)

        # Filter subsets
        df1 = df[df["Name"].str.contains("Vial temperature")].copy()
        df2 = df[df["Name"].str.contains("Heater power")].copy()
        df3 = df[df["Name"].str.contains("Capacitive")].copy()
        df4 = df[df["Name"].str.contains("Pirani")].copy()

        # Check and process
        if df1.empty:
            st.warning("No data found with 'Vial temperature' in Name column.")
        else:
            ref_time = datetime.strptime(df1["Timestamp"].iloc[0], "%Y-%m-%d %H:%M:%S.%f")

            df1["Time (hours)"] = process_time(df1, ref_time)
            df2["Time (hours)"] = process_time(df2, ref_time)
            df3["Time (hours)"] = process_time(df3, ref_time)
            df4["Time (hours)"] = process_time(df4, ref_time)

            # Plotting function
            def create_plot(df_sub, name, color):
                mask = (df_sub["Time (hours)"] >= x_min) & (df_sub["Time (hours)"] <= x_max)
                filtered = df_sub.loc[mask]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=filtered["Time (hours)"],
                    y=filtered["Value"],
                    mode='lines',
                    line=dict(color=color),
                    name=name
                ))
                fig.update_layout(
                    title=name,
                    xaxis_title="Time (hours)",
                    yaxis_title="Value",
                    template="plotly_white",
                    height=300,
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                return fig

            # Display plots
            st.plotly_chart(create_plot(df1, "Vial temperature", "#000000"), use_container_width=True)
            st.plotly_chart(create_plot(df2, "Heater power", "#333333"), use_container_width=True)
            st.plotly_chart(create_plot(df3, "Capacitive", "#666666"), use_container_width=True)
            st.plotly_chart(create_plot(df4, "Pirani", "#999999"), use_container_width=True)

            # File export section
            st.subheader("Export to Excel")
            file_name = st.text_input("Enter file name (without extension)", "exported_data")

            if st.button("Export Selected Signals"):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    if export_vial:
                        df1.to_excel(writer, sheet_name='Vial_temperature', index=False)
                    if export_heater:
                        df2.to_excel(writer, sheet_name='Heater_power', index=False)
                    if export_cap:
                        df3.to_excel(writer, sheet_name='Capacitive', index=False)
                    if export_pirani:
                        df4.to_excel(writer, sheet_name='Pirani', index=False)
                    writer.close()
                    processed_data = output.getvalue()

                st.success("File ready for download!")
                st.download_button(
                    label="Download Excel File",
                    data=processed_data,
                    file_name=f"{file_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.info("Please upload a CSV file to get started.")
