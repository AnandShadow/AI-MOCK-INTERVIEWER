# Deploying Project Oracle

Project Oracle is designed to be easily deployed for free using Streamlit Community Cloud. This allows you to host your AI Mock Interview Platform continuously without infrastructure costs, while still relying on the free-tier capabilities of Groq and Edge-TTS.

## Prerequisites
1. **GitHub Account:** Your code must be hosted in a public or private GitHub repository.
2. **Streamlit Account:** Sign up at [share.streamlit.io](https://share.streamlit.io/) using your GitHub account.
3. **Groq API Key:** You must have your `GROQ_API_KEY` ready.

## Step 1: Push to GitHub
Ensure all your files are committed and pushed to a GitHub repository. Your repository should contain at least:
```text
├── app.py
├── interview_engine.py
├── evaluator.py
└── requirements.txt
```
*(Note: **DO NOT** commit your `.env` file to GitHub. Ensure it is added to your `.gitignore`.)*

## Step 2: Deploy on Streamlit Community Cloud
1. Log into your [Streamlit Cloud Dashboard](https://share.streamlit.io/).
2. Click the **"New app"** button.
3. Select the repository, branch, and main file path. For the main file path, enter `app.py` (or `project_oracle/app.py` depending on your repository structure).
4. **DO NOT click "Deploy" yet.** Proceed to Step 3.

## Step 3: Configure Environment Variables (Secrets)
Because you cannot commit your `.env` file, you must provide your Groq API key securely to Streamlit.

1. Before clicking Deploy, click on **"Advanced settings..."** at the bottom of the deployment configuration screen.
2. A modal will open with a section labeled **"Secrets"**.
3. Paste your environment variables in TOML format. Streamlit automatically converts these secrets to environment variables, making them compatible with `python-dotenv` and `os.getenv`. It should look exactly like this:
   ```toml
   GROQ_API_KEY = "your-actual-api-key-here"
   ```
4. Click **Save**.

*(Note: If you have already deployed the app, you can add secrets by clicking the three-dot menu (⋮) next to your app in the Streamlit dashboard, selecting **Settings**, and navigating to the **Secrets** tab.)*

## Step 4: Launch and Test
1. Click **Deploy!**
2. Streamlit will provision a container, install the dependencies defined in your `requirements.txt`, and launch your app.
3. Once live, give Streamlit microphone permissions when prompted by your browser, and test the full voice interface and grading engine.
