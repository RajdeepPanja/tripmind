# TripMind — AI Travel Operating System

> **Tell TripMind where you want to go, your budget and preferences. It researches live travel data, finds flights, hotels and places, builds an optimized itinerary, and verifies your trip.**

TripMind is an AI-powered travel planning system built for the **SerpApi India Hackathon 2026**. Instead of returning a simple list of search results, TripMind combines live web research, constraint-aware optimization, route planning, itinerary generation, and verification into one workflow.

## ✨ What TripMind Does

TripMind takes a travel request containing:
- Origin and destination
- Travel dates
- Number of travelers
- Total trip budget
- Interests such as food, history, photography, nature, etc.

It then:
1. 🔎 **Searches live travel data** — flights, hotels, places and attractions.
2. 🧠 **Understands constraints** — budget, dates, travelers and preferences.
3. 💰 **Optimizes the trip** — evaluates flight + hotel combinations and estimated food, activities, local transport and budget buffer.
4. 🗺️ **Builds an itinerary** — selects relevant places and organizes activities across the trip.
5. ✅ **Verifies the plan** — checks the generated trip against the original request and supports workflow revision when required.
6. 📊 **Presents the result** — trip summary, budget breakdown, selected flight/hotel, activities, route information and verification status.

## 🧩 Core Idea

```text
Search → Understand → Optimize → Verify → Plan → React / Replan
```

The goal is to move beyond a conventional travel chatbot and create a small **AI travel operating system** that can research, reason over constraints, and produce a structured travel plan.

## 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │   Next.js Frontend  │
                         │      JavaScript     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     FastAPI API     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ LangGraph Workflow  │
                         │    Orchestrator     │
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
       ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
       │ Flight Agent   │  │  Hotel Agent   │  │ Places Agent  │
       └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
               │                   │                   │
               └───────────────────┼───────────────────┘
                                   ▼
                         ┌─────────────────────┐
                         │  Trip Optimizer     │
                         │ Budget + Constraints│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Itinerary Agent     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Verification Agent  │
                         └─────────────────────┘

        External live data:
        ┌─────────────────────────────────────────────────┐
        │ SerpApi → Google Flights / Hotels / Maps / Search│
        └─────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Frontend
- **Next.js**
- **React**
- **JavaScript / JSX**
- **Tailwind CSS**
- **shadcn/ui**
- **Lucide**
- **MapLibre**
- **Recharts**

### Backend
- **Python**
- **FastAPI**
- **Pydantic**
- **LangGraph**
- **LangChain**
- **Groq**
- **pytest**

### AI

TripMind uses **Groq** through LangChain with:

```text
openai/gpt-oss-120b
```

### Search / Live Data

TripMind uses **SerpApi** for live web research, including:
- Google Flights
- Google Hotels
- Google Maps
- Google Search

## 🔍 Meaningful SerpApi Usage

SerpApi is not used as a decorative search box. TripMind uses live search results as inputs to its planning workflow.

```text
User constraints
      ↓
Live SerpApi research
      ↓
Structured travel options
      ↓
Budget + constraint analysis
      ↓
Optimization
      ↓
Itinerary
      ↓
Verification
```

## 🤖 Multi-Agent Workflow

### Flight Agent
Searches and processes available flight options.

### Hotel Agent
Searches accommodation options and extracts relevant pricing and details.

### Places Agent
Finds places and activities relevant to the user's interests.

### Trip Optimizer
Evaluates combinations of travel options against the user's budget and constraints. It considers estimated food, activities, local transport and a budget buffer. When no fully feasible combination exists, it can fall back to the cheapest available combination and explicitly communicate the shortfall.

### Itinerary Agent
Turns selected places into a structured day-by-day travel plan.

### Verification Agent
Checks the generated plan against the original request and supports workflow revision when required.

## 💰 Budget-Aware Planning

TripMind treats the budget as a constraint rather than simply displaying prices.

```text
Total Budget
    │
    ├── Flights
    ├── Hotels
    ├── Food estimate
    ├── Activities estimate
    ├── Local transport estimate
    └── Budget buffer
```

If a feasible combination exists, the optimizer selects one that satisfies the available budget. If no feasible combination exists, TripMind shows the cheapest available option and clearly reports the estimated shortfall instead of hiding it.

## 📁 Project Structure

```text
tripmind/
│
├── backend/
│   ├── agents/
│   │   ├── flight_agent.py
│   │   ├── hotel_agent.py
│   │   ├── places_agent.py
│   │   ├── itinerary_agent.py
│   │   └── verification_agent.py
│   ├── api/
│   │   └── main.py
│   ├── core/
│   ├── db/
│   ├── graph/
│   ├── models/
│   ├── services/
│   ├── tests/
│   ├── scripts/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── page.jsx
│   │   ├── plan/page.jsx
│   │   └── globals.css
│   ├── components/trip/
│   │   ├── TripForm.jsx
│   │   ├── PlanningScreen.jsx
│   │   └── ResultsDashboard.jsx
│   ├── lib/
│   ├── package.json
│   └── .env.local.example
│
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/RajdeepPanja/tripmind.git
cd tripmind
```

# Backend Setup

### 2. Create and activate a virtual environment

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Add your credentials to `.env`:

```env
SERPAPI_API_KEY=your_serpapi_key
GROQ_API_KEY=your_groq_key
```

**Never commit your real `.env` file or API keys to GitHub.**

### 5. Start the backend

```powershell
python -m uvicorn api.main:app --port 8001
```

Backend:

```text
http://localhost:8001
```

# Frontend Setup

### 6. Install dependencies

Open a second terminal:

```powershell
cd D:\tripmind\frontend
npm install
```

### 7. Configure frontend environment

If required by the current frontend configuration:

```powershell
Copy-Item .env.local.example .env.local
```

Do not commit `.env.local`.

### 8. Start the frontend

```powershell
npm run dev
```

Frontend:

```text
http://localhost:3000
```

## 🔄 Running TripMind

Use two terminals.

### Terminal 1 — Backend

```powershell
cd D:\tripmind\backend
.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --port 8001
```

### Terminal 2 — Frontend

```powershell
cd D:\tripmind\frontend
npm run dev
```

Then open `http://localhost:3000`.

## 🧪 Testing

The backend includes automated tests for agents, workflow, API endpoints, optimization and verification.

```powershell
cd D:\tripmind\backend
.venv\Scripts\Activate.ps1
pytest
```

## 🎥 Demo

**Demo video:** https://youtu.be/veIr7_Mk3sQ

The demo shows TripMind running locally and demonstrates the travel-planning workflow.

## 🎯 Example Workflow

```text
From: Kolkata
To: Jaipur
Dates: 24 Sep → 30 Sep
Travelers: 4
Budget: ₹85,000
Interests: History, Food, Photography
```

TripMind processes the request as:

```text
Flight options
      +
Hotel options
      +
Places / activities
      ↓
Budget-aware optimization
      ↓
Route planning
      ↓
Day-by-day itinerary
      ↓
Verification
```

If the requested budget cannot support a complete plan, TripMind communicates the constraint instead of silently exceeding it.

## 🧠 Why This Is More Than a Travel Chatbot

A conventional travel chatbot can answer:

> “What are some places to visit in Jaipur?”

TripMind instead attempts to solve:

> “Plan my Jaipur trip for these dates, for these travelers, within this budget, according to these interests, using current travel data.”

That requires multiple stages:
- Live research
- Structured extraction
- Constraint handling
- Budget reasoning
- Option selection
- Route planning
- Itinerary generation
- Verification

The LLM is therefore one component inside a larger planning system rather than the entire application.

## 🔐 Security

API keys are loaded through environment variables. The repository excludes `.env`, virtual environments, `node_modules`, Next.js build output and other local files through `.gitignore`.

Do not place API keys directly inside source code.

## 📝 Current Scope

TripMind currently focuses on flight-based travel planning with hotel and place research.

The current implementation does **not** claim to search trains, buses, or multimodal transport when a suitable flight is unavailable. When no suitable flight is found, the system communicates that limitation rather than presenting unsearched transport results as verified results.

## 🏆 Hackathon

Built for the **SerpApi India Hackathon 2026**.

The project focuses on:
- AI-driven travel planning
- Meaningful SerpApi usage
- Multi-agent orchestration
- Constraint-aware optimization
- Practical usefulness
- Transparent handling of budget limitations

## 👤 Author

**Rajdeep Panja**

GitHub: https://github.com/RajdeepPanja

Project: https://github.com/RajdeepPanja/tripmind

## 📄 License

This project is provided for hackathon and project demonstration purposes.
