import streamlit as st
import gpxpy
import folium
from geopy.distance import geodesic
from streamlit_folium import st_folium

# Function to load and parse GPX
@st.cache_data
def load_gpx_track(uploaded_file):
    gpx = gpxpy.parse(uploaded_file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    return points

# Function to compute cumulative distances
def calculate_distances(track):
    distances = [0.0]
    for i in range(1, len(track)):
        d = geodesic(track[i-1], track[i]).meters
        distances.append(distances[-1] + d)
    return distances

# Interpolation to find position at distance
def get_position(track, distances, target_distance):
    if target_distance >= distances[-1]:
        return track[-1]

    for i in range(1, len(distances)):
        if distances[i] >= target_distance:
            ratio = (target_distance - distances[i-1]) / (distances[i] - distances[i-1])
            lat1, lon1 = track[i-1]
            lat2, lon2 = track[i]
            lat = lat1 + (lat2 - lat1) * ratio
            lon = lon1 + (lon2 - lon1) * ratio
            return (lat, lon)

# Streamlit UI
st.title("🏃‍♂️ Runner Simulation on GPX Track")

uploaded_file = st.file_uploader("Upload a GPX track file", type="gpx")

if uploaded_file:
    track = load_gpx_track(uploaded_file)
    distances = calculate_distances(track)

    st.success(f"Loaded track with {len(track)} points. Total distance: {distances[-1]:.2f} m")

    # Speed in km/h
    runner_speeds = [8, 12, 16]
    colors = ["red", "green", "purple"]

    # Elapsed time
    elapsed_minutes = st.slider("Elapsed Time (minutes)", min_value=0, max_value=60, value=5)
    elapsed_seconds = elapsed_minutes * 60

    # Create folium map
    m = folium.Map(location=track[0], zoom_start=15)
    folium.PolyLine(track, color="blue", weight=3).add_to(m)

    for i, speed_kmh in enumerate(runner_speeds):
        speed_mps = speed_kmh / 3.6
        distance_covered = speed_mps * elapsed_seconds
        pos = get_position(track, distances, distance_covered)
        folium.Marker(
            location=pos,
            popup=f"Runner {i+1} ({speed_kmh} km/h)",
            icon=folium.Icon(color=colors[i])
        ).add_to(m)

    # Display map
    st_data = st_folium(m, width=700, height=500)
