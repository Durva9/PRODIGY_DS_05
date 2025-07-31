import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit.components.v1 import html

# ----------------------------------------
# Page Configuration
st.set_page_config(page_title="US Accidents Dashboard", layout="wide")

# ----------------------------------------
# Load Data with Fix for Date Parsing
@st.cache_data
def load_data():
    df = pd.read_csv("US_Accidents_March23.csv", nrows=100000)  # You can remove nrows later
    # Fix datetime issue by removing nanoseconds
    df["Start_Time"] = pd.to_datetime(df["Start_Time"].str.split(".").str[0])
    df["Hour"] = df["Start_Time"].dt.hour
    df["Year"] = df["Start_Time"].dt.year
    df["Weather_Condition"].fillna("Unknown", inplace=True)

    # Dummy fields for visualization purpose
    df["Road_Condition"] = df["Amenity"].apply(lambda x: "Under Construction" if x else "Normal")
    df["Cause"] = df["Severity"].apply(lambda x: "Drunk Driving" if x == 4 else "Speeding")
    return df

df = load_data()

# ----------------------------------------
# KPIs
st.title("🚦 Global Traffic Accident Analysis Dashboard")
k1, k2, k3, k4 = st.columns(4)

total_accidents = len(df)
total_casualties = int(df["Severity"].sum())
mean_casualties = total_casualties / total_accidents
most_common_cause = df["Cause"].value_counts().idxmax()

k1.metric("Total Casualties", f"{total_casualties:,}")
k2.metric("Total Accidents", f"{total_accidents:,}")
k3.metric("Mean Casualties", f"{mean_casualties:.2f}")
k4.metric("Most Common Cause", most_common_cause)

st.markdown("---")

# ----------------------------------------
# Charts

# Pie Chart: Accidents by Weather
weather_data = df["Weather_Condition"].value_counts().nlargest(6).reset_index()
weather_data.columns = ["Weather", "Count"]
fig_weather = px.pie(weather_data, values="Count", names="Weather", hole=0.4,
                     title="Total Accidents by Weather Condition")

# Bar Chart: Casualties by Cause
cause_data = df.groupby("Cause").agg({"Severity": "sum"}).reset_index()
fig_cause = px.bar(cause_data, x="Cause", y="Severity", color="Cause",
                   title="Casualties by Cause", text_auto=True)

# Line Chart: Hourly Accidents
hour_data = df.groupby("Hour").size().reset_index(name="Total Accidents")
fig_hour = px.line(hour_data, x="Hour", y="Total Accidents", markers=True,
                   title="Total Accidents by Hour of the Day")

# Bar Chart: Road Condition and Weather
road_weather = df.groupby(["Road_Condition", "Weather_Condition"]).size().reset_index(name="Total Accidents")
top_weather = df["Weather_Condition"].value_counts().nlargest(6).index
road_weather = road_weather[road_weather["Weather_Condition"].isin(top_weather)]
fig_road_weather = px.bar(road_weather, x="Road_Condition", y="Total Accidents",
                          color="Weather_Condition", barmode="stack",
                          title="Total Accidents by Road Condition and Weather Condition")

# ----------------------------------------
# Folium Map: Accident Locations
st.subheader("🌍 Accident Locations Map (Sample of 1000)")

m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
marker_cluster = MarkerCluster().add_to(m)

sample_df = df.dropna(subset=["Start_Lat", "Start_Lng"]).sample(1000)

for _, row in sample_df.iterrows():
    folium.CircleMarker(
        location=[row["Start_Lat"], row["Start_Lng"]],
        radius=4,
        color="red",
        fill=True,
        fill_opacity=0.6
    ).add_to(marker_cluster)

m.save("map.html")
with open("map.html", "r", encoding="utf-8") as f:
    html(f.read(), height=600)

# ----------------------------------------
# Layout Charts
left, right = st.columns(2)
left.plotly_chart(fig_weather, use_container_width=True)
right.plotly_chart(fig_cause, use_container_width=True)

left2, right2 = st.columns(2)
left2.plotly_chart(fig_hour, use_container_width=True)
right2.plotly_chart(fig_road_weather, use_container_width=True)
