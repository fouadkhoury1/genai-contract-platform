# GenAI Contract Platform

GenAI Contract Platform demonstrates how generative AI can help evaluate legal contracts. It consists of a Django REST API backend and a Next.js frontend that work together for authentication, contract uploads and AI-powered analysis.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [Development Tips](#development-tips)

## Overview
The platform uses the DeepSeek API to extract key clauses from uploaded PDF or text contracts and assess potential risks. Uploaded documents are stored in MongoDB, and metrics are collected for API usage.

## Features
- **Authentication** – register and log in with JWT tokens
- **Contract storage** – upload PDF or text contracts to MongoDB
- **AI analysis** – DeepSeek API extracts clauses and evaluates risk
- **Metrics** – view logs and usage statistics

## Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (for MongoDB)
- Python 3.11+
- Node.js 18+

## Setup

### 1. Clone and configure
```bash
git clone <repo-url>
cd genai-contract-platform
cp .env.example .env  # update the DB URI and DEEPSEEK_API_KEY
```

### 2. Start MongoDB
```bash
docker-compose up -d mongodb
```

### 3. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements/base.txt
python manage.py migrate
python manage.py runserver 8000
```
The API is served at `http://localhost:8000/`.

### 4. Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
The app is available at `http://localhost:3000/`.

You can now create an account, upload contracts and see the AI-generated analysis in the web UI.

## Development Tips
- Backend settings live in `backend/config` and read from `.env`.
- The frontend is a Next.js app within `frontend/`.
- MongoDB data persists in the `mongo_data` Docker volume.
