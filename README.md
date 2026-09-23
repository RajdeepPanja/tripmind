# TripMind — AI Travel Operating System

TripMind plans real, verifiable trips using live travel data (via SerpApi),
multi-agent reasoning (LangGraph), deterministic optimization, and automatic
replanning ("Trip Doctor") when disruptions happen.

Core loop: **SEARCH → UNDERSTAND → OPTIMIZE → VERIFY → PLAN → REPLAN**

## Tech Stack

- **Frontend:** Next.js (JavaScript/JSX only — no TypeScript), Tailwind CSS,
  shadcn/ui, Lucide, MapLibre GL JS, Recharts
- **Backend:** Python, FastAPI, Pydantic, LangGraph
- **Live data:** SerpApi (Google Flights, Google Hotels, Google Maps, Google
  Search, Google News)

## Project Structure
tripmind/
├── frontend/ # Next.js + JavaScript + Tailwind + shadcn/ui
├── backend/ # FastAPI + Pydantic + LangGraph + SerpApi
├── README.md
└── .gitignore


## Prerequisites

- Node.js 18.18+ and npm
- Python 3.11+
- A SerpApi key (https://serpapi.com)
- An Anthropic API key (https://console.anthropic.com)

## Setup

1. Copy `backend/.env.example` → `backend/.env` and fill in keys.
2. Copy `frontend/.env.local.example` → `frontend/.env.local`.
3. Install and run the backend (see commands below).
4. Install and run the frontend (see commands below).

## Status

**Phase 1 complete:** project scaffolding, FastAPI skeleton with a health
endpoint, Next.js + Tailwind + shadcn/ui skeleton (JavaScript only),
LangGraph and SerpApi folder structure in place (stubs only — no agent
logic, no live SerpApi calls yet).

Agents, data models, and SerpApi integrations are implemented in subsequent
phases.