# MCQ Generation

A modular workflow for **automated multiple-choice question (MCQ) generation** using large language models (LLMs).  
This project provides a **Python package** for question generation and evaluation, a **FastAPI-based demo backend**, and a **Next.js frontend** for interactive testing and visualization.

## Overview

This repository includes three main components:

- **MCQ-generation package (src/):** Core logic for automated question generation and evaluation.
- **Demo app (demo/):** Combines a FastAPI backend and a Next.js frontend for running interactive demos.
- **Notebooks (notebook/):** Exploratory notebooks for data wrangling, workflow analysis, and MCQ quality assessment.

The goal of this system is to automate the end-to-end process of generating and assessing MCQs from text passages, leveraging large language models through the CreateAI API.

## Features

- Modular, extendable architecture
- Prompt-driven question generation using YAML templates
- Evaluation and ranking of generated MCQs
- FastAPI demo backend with authentication utilities
- Interactive frontend built with **Next.js**
- Simple environment-based configuration with `.env`

## Prerequisites

Make sure you have the following installed:

- **Python** ≥ 3.10
- **Node.js** ≥ 18
- **npm** or **pnpm**
- **Git**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/terryyutian/MCQ-generation.git
cd MCQ-generation
```

### 2. Backend Setup (Python + FastAPI)

#### Create and Activate a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
# or
.\.venv\Scripts\activate   # Windows
```

#### Install Dependencies

```bash
pip install --upgrade pip
pip install --editable .
```

#### Create an Environment File

Copy the example environment file and fill in your values:

```bash
cp env.example .env
```

#### Run the Backend

```bash
uvicorn demo.app:app --reload
```

The FastAPI backend will start at **http://127.0.0.1:8000**.

### 3. Frontend: Build Static Files for Production (Recommended for full auth flow)

For local development you can run the Next.js frontend in dev mode, but **to test the full authentication flow** and integrate with the FastAPI backend (which serves static files and handles SSO), we recommend generating static build files and copying them to the demo static directory.

#### From `demo/frontend`:

Install dependencies:

```bash
cd demo/frontend
npm install
# or
pnpm install
```

Build and export static site:

```bash
npm run build
npm run export
```

This produces a static `out/` directory (Next.js exported site). Note: depending on your `package.json` scripts, `npm run export` may be `next export` or combined with `build` (adjust if necessary).

Copy exported files into the backend static folder (so FastAPI can serve them):

```bash
# macOS / Linux (from demo/frontend)
rm -rf ../static/*
cp -r out/* ../static/
```

Windows (PowerShell):

```powershell
Remove-Item -Recurse -Force ..\static\*
Copy-Item -Recurse -Force .\out\* ..\static\
```

Open the app in your browser at **http://127.0.0.1:8000** and the FastAPI server will serve the exported frontend from `demo/static`. This is the recommended path to test the full ASU SSO authentication flow.

#### Optional: Run in Dev Mode (no static export)

If you prefer working with hot-reload and development features:

```bash
# from demo/frontend
npm run dev
```

Dev mode runs the Next.js dev server (usually at `http://localhost:3000`) but may bypass or not fully represent the production static-serving + backend SSO flow. Use dev mode for UI development and rapid iteration; use static export + FastAPI for full-auth testing.

---

## Authentication and Access

The **MCQ Generation system** integrates with the **CreateAI API**, which requires valid **ASU Single Sign-On (SSO)** authentication.  
Access to all backend and workflow functionalities — including the FastAPI server and the MCQ generation pipeline — is restricted to authenticated ASU users.

When the application starts, users are redirected to the ASU SSO login page.  
After successful authentication, the system uses the issued token to access the CreateAI API for generating and evaluating multiple-choice questions.

If you are **not an ASU user**, you will not be able to authenticate or use the API-dependent components of the workflow.  
For questions or access requests, please contact **Terry Y. Tian**.

---

## Development Notes

- Configuration is handled via environment variables defined in `.env`.
- The FastAPI backend uses **python-jose** for authentication and **uvicorn** as the server.
- The frontend is built with **Next.js + TypeScript + TailwindCSS**.
- Use the notebooks in the `notebook/` folder for experimentation and data exploration.

## License

This project is licensed under the **MIT License**.  
See [LICENSE](LICENSE) for details.
