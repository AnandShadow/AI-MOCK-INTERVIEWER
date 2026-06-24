# Production Deployment Guide: Project Oracle

This guide explains how to deploy Project Oracle using the production-ready Docker container to modern Platform-as-a-Service (PaaS) providers like Render or AWS App Runner.

## Docker Architecture
The included `Dockerfile` is optimized for a Streamlit audio application:
- **Base Image:** `python:3.11-slim` provides a lightweight footprint.
- **System Dependencies:** Installs `ffmpeg`, which is critical for parsing and generating complex audio formats used by `edge-tts` and Whisper.
- **Security & Networking:** Exposes port `8501`, binds to `0.0.0.0`, and disables CORS (`--server.enableCORS=false`) to prevent WebSocket connection failures behind cloud load balancers.

---

## Option 1: Deploying to Render (Recommended for Startups)

Render provides native Docker hosting with automatic deployments directly from your Git repository.

### Steps:
1. **Push your code to GitHub.** Ensure the repository contains `Dockerfile`, `requirements.txt`, and your application Python files. *(Reminder: Do NOT commit your `.env` file!)*
2. Log into the [Render Dashboard](https://dashboard.render.com/) and click **New > Web Service**.
3. **Connect Repository:** Select your GitHub repository.
4. **Configuration:**
   - **Name:** `project-oracle`
   - **Environment:** Select `Docker`. (Render will automatically detect your `Dockerfile`).
   - **Region:** Choose the region closest to your user base.
   - **Instance Type:** Select the Free or Starter tier. (At least 512MB RAM is recommended to handle audio processing comfortably).
5. **Environment Variables:**
   - There is no need to configure the `GROQ_API_KEY` here because we implemented the Bring Your Own Key (BYOK) architecture! Users will input their key securely directly in the UI.
6. Click **Create Web Service**. 
7. Render will build the container and deploy it. Your app will be live at `https://project-oracle.onrender.com`.

---

## Option 2: Deploying to AWS App Runner (Enterprise Grade)

AWS App Runner provides scalable, fully managed container hosting suitable for production traffic.

### Steps:
1. **Build and Push the Image to ECR:**
   - Because our application requires system-level dependencies (`ffmpeg`), you must use AWS Elastic Container Registry (ECR) rather than deploying directly from the source code.
   - Authenticate your Docker client to your AWS account.
   - Build the image: `docker build -t project-oracle .`
   - Push the image to your ECR repository.
2. Log into the AWS Console and navigate to **App Runner**.
3. Click **Create an App Runner service**.
4. **Source:**
   - Select **Container registry**.
   - Choose **Amazon ECR** and select the `project-oracle` image you just pushed.
   - Choose an IAM role with pull permissions.
5. **Service configuration:**
   - **Service name:** `project-oracle-prod`
   - **Port:** `8501`
   - **Compute:** 1 vCPU and 2 GB memory is more than sufficient.
6. Click **Create & deploy**.
7. App Runner will pull your image, automatically configure the load balancer to handle Streamlit's WebSocket traffic, and provide a secure AWS endpoint.
