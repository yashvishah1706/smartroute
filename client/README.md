SmartRoute

Dynamic Route Planning with Flask, React, and PostgreSQL

📌 Overview

SmartRoute is a web application that computes and visualizes optimal routes on a map using graph algorithms such as Dijkstra and A*. It integrates:

Flask (Python backend) for route computation.

React (Vite + React Leaflet frontend) for interactive maps.

PostgreSQL (optional) for persistent storage and scaling.

OSMnx & NetworkX for graph-based shortest path algorithms.

This project is designed to demonstrate DSA concepts applied in real-world navigation systems.

⚙️ Features

✅ Compute shortest path (distance-based)
✅ Compute fastest path (time-based)
✅ Option to avoid highways
✅ Interactive map with draggable origin/destination pins
✅ Algorithm selection (Dijkstra, A*)
✅ Modern React + Leaflet UI

🛠️ Tech Stack

Frontend: React (Vite), React-Leaflet, Leaflet

Backend: Flask, Flask-CORS, dotenv

Algorithms: NetworkX (Dijkstra, A*)

Mapping: OSMnx + OpenStreetMap data

Database (Phase 1): PostgreSQL

🖥️ Setup & Installation
1. Clone the Repository
git clone https://github.com/yashvishah1706/smartroute.git
cd smartroute

2. Backend Setup (Flask)
cd server
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

pip install -r requirements.txt
python main.py


Server runs at: http://127.0.0.1:5000

3. Frontend Setup (React)
cd client
npm install
npm run dev


Frontend runs at: http://localhost:5173

🔍 Example Usage

Enter place → Hoboken, New Jersey

Set origin & destination coordinates (drag pins on map)

Select algorithm (Dijkstra / A*).

Choose weight (distance or time).

Hit Compute Route → The map will display the path
