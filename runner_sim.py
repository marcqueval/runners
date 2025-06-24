import streamlit as st
import gpxpy
import folium
from geopy.distance import geodesic
from streamlit_folium import st_folium
import time

# ---- Function Definitions ----

@st.cache_data
def load_gpx_track(uploaded_file):
    gpx = gpxpy.parse(uploaded_file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    return points

def calculate_distances(track):
    distances = [0.0]
    for i in range(1, len(track)):
        d = geodesic(track[i-1], track[i]).meters
        distances.append(distances[-1] + d)
    return distances

def get_position(track, distances, target_distance):
    if target_distance >= distances[-1]:
        return track[-1]
    for i in range(1, len(distances)):
        if distances[i] >= target_distance:
            denominator = distances[i] - distances[i-1]
            if denominator == 0:
                ratio = 0  # or 1, or whatever default makes sense in your context
            else:
                ratio = (target_distance - distances[i-1]) / denominator
            lat1, lon1 = track[i-1]
            lat2, lon2 = track[i]
            lat = lat1 + (lat2 - lat1) * ratio
            lon = lon1 + (lon2 - lon1) * ratio
            return (lat, lon)

# ---- Streamlit App UI ----

st.set_page_config(page_title="Runner Simulation", layout="wide")
st.title("🏃‍♂️ GPX Runner Simulation with Start/Stop")

uploaded_file = st.file_uploader("Upload a GPX file", type="gpx")

if uploaded_file:
    # Session state init
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False
    if 'elapsed_seconds' not in st.session_state:
        st.session_state.elapsed_seconds = 0

    # Load and parse GPX
    track = load_gpx_track(uploaded_file)
    distances = calculate_distances(track)
    total_length = distances[-1]

    st.success(f"Track loaded: {len(track)} points | Total distance: {total_length:.0f} m")

    # Controls
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("▶️ Start"):
            st.session_state.is_running = True
    with col2:
        if st.button("⏸️ Stop"):
            st.session_state.is_running = False
    with col3:
        st.write(f"⏱️ Elapsed time: **{int(st.session_state.elapsed_seconds)}** seconds")

    # Speed settings
    runner_speeds = [8, 12, 16]  # km/h
    colors = ["red", "green", "purple"]

    # Folium map
    m = folium.Map(location=track[0], zoom_start=15)
    folium.PolyLine(track, color="blue", weight=3).add_to(m)

    # Calculate runner positions
    for i, speed_kmh in enumerate(runner_speeds):
        speed_mps = speed_kmh / 3.6
        distance_covered = speed_mps * st.session_state.elapsed_seconds
        pos = get_position(track, distances, distance_covered)
        folium.Marker(
            location=pos,
            popup=f"Runner {i+1} ({speed_kmh} km/h)",
            icon=folium.Icon(color=colors[i])
        ).add_to(m)

    st_folium(m, width=800, height=550)

    # Auto update every 0.5 seconds if running
    if st.session_state.is_running:
        time.sleep(0.5)
        st.session_state.elapsed_seconds += 60
        st.experimental_rerun()