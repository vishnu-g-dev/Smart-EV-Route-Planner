# 🔋 Smart EV Route Planner & Energy Simulator

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)](https://streamlit.io/)
[![OpenRouteService](https://img.shields.io/badge/API-OpenRouteService-red.svg)](https://openrouteservice.org/)
[![OpenWeatherMap](https://img.shields.io/badge/API-OpenWeatherMap-orange.svg)](https://openweathermap.org/)

**[🚀 Try the Live Application Here](https://smart-ev-route-planner.streamlit.app/)**

## 📌 Project Overview
The **Smart EV Route Planner** is an engineering-grade web application designed to eliminate Electric Vehicle (EV) range anxiety. Unlike standard navigation apps that only calculate distance, this simulator uses a **deterministic physics engine** to calculate actual battery consumption. It actively factors in 3D topography (hills and slopes), real-time weather (headwinds and rain friction), and vehicle-specific aerodynamics to predict exactly when and where an EV will need to recharge.

## ✨ Core Engineering Features
* **Real-Time Physics Engine:** Calculates traction power requirements by summing forces of gravity (mg sin θ), rolling resistance (mg Cr cos θ), and aerodynamic drag (0.5 ρ Cd A v²) across micro-segments of the route.
* **Smart Charging Interceptor:** Algorithmically predicts when the battery will breach safe thresholds and dynamically drops predictive fast-charging waypoints on the map.
* **Economic Grid Optimization:** Features a Time-of-Day (ToD) tariff matrix that calculates the exact monetary savings of shifting the journey to off-peak electrical grid hours.
* **Curated EV Database:** Pre-configured with the exact weight, battery capacity, and drag coefficients of 20 popular Indian market EVs (e.g., Tata Nexon EV, BYD Seal, MG ZS EV), plus a fully unlocked **Custom EV Manual Override** for future-proofing.
* **Geospatial Visualization:** Renders interactive maps with Folium and dynamic dual-axis Plotly telemetry charts tracking elevation vs. State of Charge (SoC).

## 🛠️ Technology Stack
* **Frontend/Framework:** Streamlit
* **Data Processing & Math:** Pandas, NumPy, Math
* **Geospatial & Visualization:** Folium, Streamlit-Folium, Plotly
* **External APIs:** * `OpenRouteService API` (Routing & 3D Elevation profiles)
  * `OpenWeatherMap API` (Live wind speed, temperature, and precipitation)

## 💻 Local Installation & Setup

If you wish to run this project locally on your machine, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/vishnu-g-dev/Smart-EV-Route-Planner.git](https://github.com/vishnu-g-dev/Smart-EV-Route-Planner.git)
   cd Smart-EV-Route-Planner
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API Keys:**
   Create a `.env` file in the root directory and add your free API keys:
   ```env
   ORS_API_KEY=your_openrouteservice_key_here
   OWM_API_KEY=your_openweathermap_key_here
   ```

4. **Launch the application:**
   ```bash
   streamlit run app.py
   ```

## 🧠 Future Scope
* Integration of live traffic congestion data to factor in idle battery drain (HVAC usage).
* Dynamic fetching of live charging station availability near the predicted depletion coordinates.
* Enhanced regenerative braking algorithms based on specific deceleration profiles.

---
*Designed and Developed by [Vishnu G](https://www.linkedin.com/in/vishnu-g-eee164) | Electrical and Electronics Engineering, NSS College of Engineering*
