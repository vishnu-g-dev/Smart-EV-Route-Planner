import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd
import requests
import os
import math
from dotenv import load_dotenv

# Load secret API Keys
load_dotenv()
ORS_KEY = os.getenv("ORS_API_KEY")
OWM_KEY = os.getenv("OWM_API_KEY")

# Page Configuration
st.set_page_config(
    page_title="Smart EV Route Planner & Cost Optimizer",
    page_icon="⚡",
    layout="wide"
)

# ─── EV MODEL HARDWARE DATABASE (20 Popular Indian EVs) ────────────
POPULAR_INDIAN_EVS = {
    "Tata Nexon EV (Creative 45)": {"battery_capacity": 45.0, "weight": 1450, "drag_coeff": 0.29, "frontal_area": 2.2},
    "Tata Nexon EV (Medium Range)": {"battery_capacity": 30.0, "weight": 1330, "drag_coeff": 0.29, "frontal_area": 2.2},
    "Tata Punch EV (Long Range)": {"battery_capacity": 40.0, "weight": 1360, "drag_coeff": 0.32, "frontal_area": 2.3},
    "Tata Punch EV (Medium Range)": {"battery_capacity": 30.0, "weight": 1240, "drag_coeff": 0.32, "frontal_area": 2.3},
    "Tata Curvv EV (55 kWh)": {"battery_capacity": 55.0, "weight": 1600, "drag_coeff": 0.28, "frontal_area": 2.3},
    "Tata Tiago EV (Long Range)": {"battery_capacity": 24.0, "weight": 1150, "drag_coeff": 0.33, "frontal_area": 2.1},
    "Tata Tigor EV": {"battery_capacity": 26.0, "weight": 1235, "drag_coeff": 0.33, "frontal_area": 2.1},
    "MG ZS EV": {"battery_capacity": 50.3, "weight": 1600, "drag_coeff": 0.32, "frontal_area": 2.4},
    "MG Windsor EV": {"battery_capacity": 38.0, "weight": 1550, "drag_coeff": 0.30, "frontal_area": 2.4},
    "MG Comet EV": {"battery_capacity": 17.3, "weight": 815, "drag_coeff": 0.39, "frontal_area": 2.0},
    "Mahindra XUV400": {"battery_capacity": 39.4, "weight": 1580, "drag_coeff": 0.33, "frontal_area": 2.4},
    "Mahindra XUV 3XO EV": {"battery_capacity": 39.4, "weight": 1520, "drag_coeff": 0.33, "frontal_area": 2.4},
    "BYD Atto 3 (Extended)": {"battery_capacity": 60.5, "weight": 1750, "drag_coeff": 0.29, "frontal_area": 2.5},
    "BYD Seal (Dynamic)": {"battery_capacity": 61.4, "weight": 1920, "drag_coeff": 0.22, "frontal_area": 2.2},
    "BYD e6 (MPV)": {"battery_capacity": 71.7, "weight": 1930, "drag_coeff": 0.29, "frontal_area": 2.6},
    "Hyundai Ioniq 5": {"battery_capacity": 72.6, "weight": 2000, "drag_coeff": 0.28, "frontal_area": 2.6},
    "Hyundai Kona Electric": {"battery_capacity": 39.2, "weight": 1535, "drag_coeff": 0.29, "frontal_area": 2.3},
    "Kia EV6 (GT-Line)": {"battery_capacity": 77.4, "weight": 2100, "drag_coeff": 0.28, "frontal_area": 2.5},
    "Volvo XC40 Recharge": {"battery_capacity": 78.0, "weight": 2180, "drag_coeff": 0.32, "frontal_area": 2.6},
    "BMW i4 (eDrive40)": {"battery_capacity": 80.7, "weight": 2050, "drag_coeff": 0.24, "frontal_area": 2.3}
}

dropdown_options = list(POPULAR_INDIAN_EVS.keys()) + ["Custom EV (Manual Override)"]

# ─── SESSION STATE STORAGE MEMORY ──────────────────────────────────
if "route_coords" not in st.session_state:
    st.session_state.route_coords = None
if "distance" not in st.session_state:
    st.session_state.distance = 0
if "duration" not in st.session_state:
    st.session_state.duration = 0
if "wind" not in st.session_state:
    st.session_state.wind = 0
if "temperature" not in st.session_state:
    st.session_state.temperature = 25
if "raining_status" not in st.session_state:
    st.session_state.raining_status = "Clear"
if "soc_profile" not in st.session_state:
    st.session_state.soc_profile = None
if "total_kwh_used" not in st.session_state:
    st.session_state.total_kwh_used = 0
if "charging_stops" not in st.session_state:
    st.session_state.charging_stops = []

# ─── API HELPER FUNCTIONS ──────────────────────────────────────────
def get_coordinates(city_name):
    """Converts a city name into [longitude, latitude]"""
    url = f"https://api.openrouteservice.org/geocode/search?api_key={ORS_KEY}&text={city_name}&size=1"
    try:
        response = requests.get(url).json()
        coords = response['features'][0]['geometry']['coordinates']
        return coords
    except Exception as e:
        return None

def get_route_with_elevation(start_coords, end_coords):
    """Fetches driving coordinates using POST to guarantee [lon, lat, elevation]"""
    url = f"https://api.openrouteservice.org/v2/directions/driving-car/geojson?api_key={ORS_KEY}"
    body = {"coordinates": [start_coords, end_coords], "elevation": True}
    try:
        response = requests.post(url, json=body).json()
        if 'error' in response:
            st.error(f"API Error: {response['error'].get('message', 'Route not found')}")
            return None, None, None
            
        geometry = response['features'][0]['geometry']['coordinates']
        properties = response['features'][0]['properties']['segments'][0]
        distance_km = properties['distance'] / 1000.0
        duration_hrs = properties['duration'] / 3600.0
        return geometry, distance_km, duration_hrs
    except Exception as e:
        return None, None, None

def get_weather_data(lat, lon):
    """Fetches real-time weather details"""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        weather_main = res['weather'][0]['main'].lower()
        wind_speed = res['wind']['speed']
        temp = res['main']['temp']
        is_raining = True if "rain" in weather_main or "drizzle" in weather_main else False
        return wind_speed, temp, is_raining
    except Exception as e:
        return 0, 25, False

# ─── REAL PHYSICS PROPULSION ENGINE ────────────────────────────────
def calculate_haversine_distance(lon1, lat1, lon2, lat2):
    R = 6371.0
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def simulate_ev_journey(geometry, mass, c_d, area, total_cap, initial_soc, wind_speed, is_raining, safety_threshold):
    """Step-by-step physical model simulating battery drop and recommending charging stops"""
    current_soc = float(initial_soc)
    current_energy = (current_soc / 100.0) * total_cap
    
    soc_history = []
    distance_history = []
    stops_found = []
    
    cumulative_dist = 0.0
    soc_history.append(current_soc)
    distance_history.append(cumulative_dist)
    
    g = 9.81
    rho = 1.225
    c_r = 0.015 if not is_raining else 0.022
    v_car = 16.67
    powertrain_efficiency = 0.85
    
    total_kwh_charged_on_way = 0.0
    
    for i in range(len(geometry) - 1):
        lon1, lat1, alt1 = geometry[i]
        lon2, lat2, alt2 = geometry[i+1]
        
        seg_dist_km = calculate_haversine_distance(lon1, lat1, lon2, lat2)
        if seg_dist_km == 0:
            continue
            
        seg_dist_m = seg_dist_km * 1000.0
        elevation_delta_m = alt2 - alt1
        slope = math.atan2(elevation_delta_m, seg_dist_m)
        
        f_gravity = mass * g * math.sin(slope)
        f_rolling = mass * g * c_r * math.cos(slope)
        f_aerodynamic = 0.5 * rho * c_d * area * (v_car + wind_speed)**2
        
        f_total = f_gravity + f_rolling + f_aerodynamic
        work_joules = f_total * seg_dist_m
        energy_kwh = work_joules / 3600000.0
        
        if energy_kwh > 0:
            actual_kwh_spent = energy_kwh / powertrain_efficiency
        else:
            actual_kwh_spent = energy_kwh * 0.60
            
        current_energy -= actual_kwh_spent
        current_energy = max(0.0, min(current_energy, total_cap))
        current_soc = (current_energy / total_cap) * 100.0
        
        cumulative_dist += seg_dist_km
        
        if current_soc < safety_threshold:
            energy_needed = (0.80 * total_cap) - current_energy
            total_kwh_charged_on_way += energy_needed
            
            stops_found.append({
                "coord": [lat2, lon2],
                "at_km": cumulative_dist,
                "arrival_soc": current_soc
            })
            current_soc = 80.0
            current_energy = (current_soc / 100.0) * total_cap
            
        soc_history.append(current_soc)
        distance_history.append(cumulative_dist)
        
    net_trip_depletion = ((initial_soc - current_soc) / 100.0) * total_cap
    total_energy_provided = max(0.0, net_trip_depletion + total_kwh_charged_on_way)
    
    df_profile = pd.DataFrame({"Distance (km)": distance_history, "Battery %": soc_history})
    return df_profile, total_energy_provided, stops_found

# ─── WEB APP USER INTERFACE ────────────────────────────────────────
st.title("⚡ Smart EV Route Planner & Cost Optimizer")
st.caption("Optimize your route using real-time physics, elevation, and weather data.")
st.markdown("---")

# Sidebar Configuration
st.sidebar.header("📍 Journey Configuration")
source = st.sidebar.text_input("Starting Point", value="Palakkad")
destination = st.sidebar.text_input("Destination", value="Kodaikanal")

st.sidebar.markdown("---")
st.sidebar.header("🚗 EV Specifications")

ev_model = st.sidebar.selectbox("Select EV Model", dropdown_options)

if ev_model == "Custom EV (Manual Override)":
    st.sidebar.caption("⚙️ Manual Vehicle Design Input")
    batt_cap = st.sidebar.number_input("Battery Capacity (kWh)", value=45.0, step=1.0)
    weight = st.sidebar.number_input("Total Weight (kg)", value=1450, step=10)
    drag_c = st.sidebar.number_input("Drag Coefficient (Cd)", value=0.30, step=0.01)
    area = st.sidebar.number_input("Frontal Area (m²)", value=2.3, step=0.1)
else:
    specs = POPULAR_INDIAN_EVS[ev_model]
    batt_cap = specs["battery_capacity"]
    weight = specs["weight"]
    drag_c = specs["drag_coeff"]
    area = specs["frontal_area"]
    
    st.sidebar.text(f"🔋 Battery Size: {batt_cap} kWh")
    st.sidebar.text(f"⚖️ Curb Weight: {weight} kg")
    st.sidebar.text(f"💨 Aero Drag: {drag_c} Cd")

initial_soc = st.sidebar.slider("Current Battery Charge (%)", 10, 100, 80)
target_soc = st.sidebar.slider("Desired Destination Battery Charge (%)", 10, 50, 20)

plan_route = st.sidebar.button("Calculate Optimal Route 🚀", width="stretch")

if plan_route:
    with st.spinner("Analyzing environment layers & running propulsion math models..."):
        start_pt = get_coordinates(source)
        end_pt = get_coordinates(destination)
        
        if start_pt and end_pt:
            coords, dist, dur = get_route_with_elevation(start_pt, end_pt)
            
            if coords:
                st.session_state.route_coords = coords
                st.session_state.distance = dist
                st.session_state.duration = dur
                
                mid_point = coords[len(coords) // 2]
                wind, temp, is_raining = get_weather_data(lat=mid_point[1], lon=mid_point[0])
                st.session_state.wind = wind
                st.session_state.temperature = temp
                st.session_state.raining_status = "🌧️ Raining" if is_raining else "☀️ No Rain"
                
                safety_trigger = target_soc + 5
                
                # We pass the unpacked variables directly to the engine now
                df_profile, kwh_used, stops = simulate_ev_journey(
                    coords, weight, drag_c, area, batt_cap, initial_soc, wind, is_raining, safety_trigger
                )
                st.session_state.soc_profile = df_profile
                st.session_state.total_kwh_used = kwh_used
                st.session_state.charging_stops = stops
        else:
            st.error("Could not locate the cities entered. Please check the spelling.")

# Layout Columns (Exactly as requested)
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Optimal Eco-Route Map")
    map_center = [10.5, 76.5]
    
    if st.session_state.route_coords:
        folium_coords = [[coord[1], coord[0]] for coord in st.session_state.route_coords]
        map_center = folium_coords[0]
        
        my_map = folium.Map(location=map_center, zoom_start=9)
        folium.PolyLine(folium_coords, color="blue", weight=5).add_to(my_map)
        
        folium.Marker(folium_coords[0], popup="Start", icon=folium.Icon(color='green', icon='play')).add_to(my_map)
        folium.Marker(folium_coords[-1], popup="Destination", icon=folium.Icon(color='red', icon='flag')).add_to(my_map)
        
        for idx, stop in enumerate(st.session_state.charging_stops):
            stop_info = f"Smart Charging Stop #{idx+1}<br>At: {stop['at_km']:.1f} km<br>Arrival Charge: {stop['arrival_soc']:.1f}%"
            folium.Marker(
                location=stop['coord'],
                popup=stop_info,
                tooltip="⚡ Recommended Charging Station",
                icon=folium.Icon(color='orange', icon='flash')
            ).add_to(my_map)
    else:
        my_map = folium.Map(location=map_center, zoom_start=8)
        
    st_folium(my_map, width=700, height=450, key="ev_map")

with col2:
    st.subheader("📊 Environment & Route Insights")
    if st.session_state.route_coords:
        st.metric(label="Total Distance", value=f"{st.session_state.distance:.2f} km")
        st.metric(label="Estimated Travel Time", value=f"{st.session_state.duration:.2f} hours")
        st.metric(label="Midpoint Ambient Temp", value=f"{st.session_state.temperature:.1f} °C")
        st.metric(label="Wind Speed & Precipitation", value=f"{st.session_state.wind} m/s | {st.session_state.raining_status}")
        st.metric(label="Predicted Energy Consumed", value=f"{st.session_state.total_kwh_used:.2f} kWh")
        
        num_stops = len(st.session_state.charging_stops)
        st.info(f"💡 Recommended Charging Stops Required: **{num_stops}**")
    else:
        st.metric(label="Total Distance", value="-- km")
        st.metric(label="Estimated Travel Time", value="-- hours")
        st.metric(label="Midpoint Ambient Temp", value="-- °C")
        st.metric(label="Wind Speed & Precipitation", value="--")
        st.metric(label="Predicted Energy Consumed", value="-- kWh")

st.markdown("---")

col_chart, col_matrix = st.columns([3, 2])

with col_chart:
    st.subheader("📈 Battery State of Charge (%) Profile")
    if st.session_state.soc_profile is not None:
        fig = px.line(st.session_state.soc_profile, x='Distance (km)', y='Battery %')
        fig.update_yaxes(range=[0, 105])
    else:
        mock_data = pd.DataFrame({'Distance (km)': [0, 50, 100], 'Battery %': [initial_soc, initial_soc, initial_soc]})
        fig = px.line(mock_data, x='Distance (km)', y='Battery %')
        fig.update_yaxes(range=[0, 105])
    st.plotly_chart(fig, width="stretch")

with col_matrix:
    st.subheader("💰 Time-of-Day (ToD) Cost Optimization")
    if st.session_state.route_coords:
        energy = st.session_state.total_kwh_used
        
        cost_off_peak = energy * 8.0   
        cost_standard = energy * 15.0  
        cost_peak = energy * 22.0      
        
        cost_data = {
            "Charging Window": ["Off-Peak (11 PM - 5 AM)", "Standard (5 AM - 6 PM)", "Peak Hour (6 PM - 11 PM)"],
            "Tariff Rate": ["₹ 8.00 / kWh", "₹ 15.00 / kWh", "₹ 22.00 / kWh"],
            "Total Trip Expense": [f"₹ {cost_off_peak:.2f}", f"₹ {cost_standard:.2f}", f"₹ {cost_peak:.2f}"]
        }
        df_matrix = pd.DataFrame(cost_data)
        st.table(df_matrix)
        
        savings = cost_peak - cost_off_peak
        st.success(f"🌱 Smart Choice: Charging during Off-Peak windows saves **₹ {savings:.2f}** on this single journey!")
    else:
        st.write("Click 'Calculate Optimal Route' to generate economic analysis reports.")