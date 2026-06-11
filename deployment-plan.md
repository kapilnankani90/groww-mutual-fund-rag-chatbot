# Deployment Plan: Mutual Fund FAQ Assistant

This document outlines the steps to deploy the **Mutual Fund FAQ Assistant** backend to **Railway** and the static frontend to **Vercel**.

---

## 1. Backend Deployment (Railway)

Railway is used to deploy and run the Python FastAPI backend, database, and background scheduler.

### Prerequisites & Preparation
1. Ensure `backend/requirements.txt` is up-to-date.
2. Ensure you have a **Railway Account** linked to your GitHub repository.

### Step-by-Step Deployment
1. Go to the [Railway Dashboard](https://railway.app) and click **New Project** -> **Deploy from GitHub**.
2. Select the repository containing your codebase.
3. Click **Configure Service**.
4. In the **Variables** tab, add the following environment variables:
   - `GROQ_API_KEY`: *Your actual Groq API key* (required for the RAG pipeline).
   - `PORT`: `8080` (Railway will automatically assign this, but setting it explicitly ensures consistency).
5. In the **Settings** tab:
   - **Build Command**: Railway automatically detects Python and builds dependencies via pip. If needed, configure:
     ```bash
     pip install -r backend/requirements.txt
     ```
   - **Start Command**: Set the start command to run FastAPI via uvicorn:
     ```bash
     uvicorn backend.app:app --host 0.0.0.0 --port $PORT
     ```
6. Click **Deploy**. Railway will build and deploy the container, providing you with a public URL (e.g., `https://your-backend.up.railway.app`). Note down this URL for Vercel configuration.

---

## 2. Frontend Deployment (Vercel)

Vercel is used to host the frontend HTML, CSS, and JS files.

### Prerequisites & Preparation
1. Create a `vercel.json` file at the root of the project to configure routing and directory serving.
2. In the Vercel project settings, we will set up the static output directory as `frontend`.

### vercel.json Configuration
Create a `vercel.json` file in the workspace root with the following configuration to serve static files from the `frontend` folder and route requests:
```json
{
  "version": 2,
  "public": true,
  "cleanUrls": true,
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/frontend/$1"
    }
  ]
}
```

### Step-by-Step Deployment
1. Log in to [Vercel](https://vercel.com) and click **Add New** -> **Project**.
2. Select your GitHub repository.
3. In the project setup panel:
   - **Framework Preset**: Select **Other**.
   - **Root Directory**: Select `./` (root).
4. Click **Deploy**. Vercel will build and host your files, outputting a URL (e.g., `https://your-frontend.vercel.app`).

---

## 3. Environment Integration & CORS

To connect the frontend on Vercel with the backend on Railway:

1. **Frontend API URL Setup**:
   In [frontend/app.js](file:///c:/groww%20mutual%20fund%20milestone/frontend/app.js), set the backend API endpoint dynamically to point to your Railway domain if deployed in production, falling back to local port 8080 during local testing.
   
2. **CORS Settings**:
   In [backend/app.py](file:///c:/groww%20mutual%20fund%20milestone/backend/app.py), ensure CORS is configured to accept requests from your Vercel frontend URL.
