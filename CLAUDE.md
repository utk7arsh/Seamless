# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Seamless is an in-movie ad recommendation platform. It pairs a Netflix-style streaming frontend with a Python backend that generates contextual ad overlays by analyzing video scenes and user profiles, then fetches real products from the Kroger API.

## Repository Structure

This is a monorepo with two independent stacks:

- **`frontend/`** — React SPA (Vite + TypeScript + Tailwind + shadcn/ui)
- **`seamless_ads/`** — Python package (Pydantic models + Kroger API integration)
- **`tests/`** — Python test suite for the backend

## Commands

### Frontend (run from `frontend/`)

```bash
npm install          # install dependencies
npm run dev          # dev server on port 8080
npm run build        # production build
npm run lint         # ESLint
npm run test         # vitest (single run)
npm run test:watch   # vitest in watch mode
```

### Backend (run from repo root)

```bash
# Run the CLI pipeline
python -m seamless_ads <scene_json> <user_json>
# Example:
python -m seamless_ads seamless_ads/samples/scene_1.json seamless_ads/samples/user_1.json

# Run tests (pytest)
python -m pytest tests/
python -m pytest tests/test_seamless_ads.py::test_end_to_end_service  # single test
```

## Architecture

### Backend Pipeline

`SeamlessAdService.generate_ad_response()` orchestrates the full pipeline:

1. **AdRecommender** — Rule-based engine that picks a product key (`pizza`, `coke`, or `laptop`) and targeting attributes from user profile + scene metadata
2. **Kroger product search** — `find_kroger_products()` fetches 3 matching products via Kroger API
3. **Overlay placement** — Positions the ad overlay on a detected object's bounding box in the scene

Key abstraction: `ToolClient` is an abstract base in `kroger_search.py` with two implementations:
- `MockKrogerToolClient` — deterministic mock for tests (no API calls)
- `KrogerAPIClient` — real OAuth2 client requiring env vars

### Backend Data Flow

`UserProfile` + `VideoMetadata` → `AdRecommender.recommend()` → product key + `AdAttributes` → `find_kroger_products()` → `SeamlessAdResponse` (includes overlay spec, products, rationale)

All models are Pydantic v2 schemas in `schemas.py`.

### Frontend

Single-page app with React Router. The main page (`pages/Index.tsx`) renders a Netflix-style UI with `Navbar`, `HeroBanner`, `ContentRow`, and `VideoViewer` components. Static content data lives in `data/content.ts`.

Path alias: `@/*` maps to `frontend/src/*`.

UI components in `components/ui/` are shadcn/ui — generated and not hand-written.

### Environment Variables (Backend)

- `KROGER_CLIENT_ID` / `KROGER_CLIENT_SECRET` — required for real Kroger API
- `KROGER_ACCESS_TOKEN` — optional, auto-generated via OAuth2
- `KROGER_LOCATION_ID` — optional store location
- `KROGER_ENV` — defaults to `"production"`

Tests use `MockKrogerToolClient` and need no env vars.
