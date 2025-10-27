# Platform IDE: Refactoring & Deployment Guide

This guide outlines the process of refactoring the Platform IDE project to separate the Next.js frontend from the Python backend scripts. This new architecture is robust, easier to debug, and prepares the application for a scalable production deployment on a cloud server like AWS.

## Architecture Overview

The goal is to move from a tightly-coupled system to a service-oriented one.

-   **Next.js Frontend**: The `web-learner` application will run as a standalone Node.js service. It will handle all user-facing UI.
-   **Python Backend**: The Python scripts in the `scripts/` directory will be wrapped in a **FastAPI** web server, exposing them as a REST API.
-   **Nginx**: In production, Nginx will act as a reverse proxy, directing traffic to the correct service based on the URL. For example, requests for the main website go to the Next.js service, while requests to `/api/generate/...` go to the Python API service.

---

## Phase 1: Local Development Refactoring

**Goal**: Modify the application locally so that the frontend communicates with the Python backend via API calls. This allows for complete testing and debugging before deployment.

### Step 1: Set Up the Python Environment

First, we'll create an isolated Python environment for our new backend service.

1.  **Create a Virtual Environment**: In the project's root directory (`platform-ide-1020/`), run:
    ```bash
    python3 -m venv venv
    ```

2.  **Create `requirements.txt`**: Create a new file named `requirements.txt` in the root directory. Add the necessary Python packages. You will need to add any libraries imported by your scripts (like `langgraph`, etc.).
    ```txt
    # requirements.txt
    fastapi
    uvicorn[standard]
    # Add other libraries your scripts depend on here
    ```

3.  **Install Dependencies**: Activate the virtual environment and install the packages.
    ```bash
    # Activate the environment (do this every time you open a new terminal for the backend)
    source venv/bin/activate

    # Install the packages
    pip install -r requirements.txt
    ```

### Step 2: Create the FastAPI Server

We will now create the API server that exposes your Python scripts.

1.  **Create `scripts/api_server.py`**: Create a new file at `scripts/api_server.py`. This will be the entry point for our backend.

2.  **Add API Code**: Paste the following template into `scripts/api_server.py`.

    ```python
    # scripts/api_server.py
    from fastapi import FastAPI, HTTPException, Body
    from typing import Dict, Any
    import uvicorn
    import logging

    # IMPORTANT: You must refactor your existing scripts into importable functions.
    # This is a placeholder for the actual logic.
    # from pipelines.langgraph.integrated_textbook_pipeline_chained import run_full_pipeline
    # from pipelines.generation.generate_chapters_from_integrated_standalone import main as generate_chapters_main

    logging.basicConfig(level=logging.INFO)
    app = FastAPI()

    # --- Placeholder Functions (Replace with your actual script logic) ---
    def run_outline_generation_logic(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        This function should contain the core logic from your outline generation script.
        It takes a dictionary payload and returns a result dictionary.
        """
        logging.info(f"Received outline generation request with payload: {payload}")
        # Example: subject = payload.get("subject")
        # result = run_full_pipeline(subject, ...)
        # For now, we return a mock result.
        return {
            "status": "success",
            "message": "Outline generation complete (mock response).",
            "reconstructed_outline": {
                "title": payload.get("subject", "Unknown Subject"),
                "groups": [
                    {"id": "g1", "title": "Chapter 1: Introduction", "sections": [{"id": "s1.1", "title": "1.1 Key Concepts"}]},
                    {"id": "g2", "title": "Chapter 2: Core Mechanics", "sections": [{"id": "s2.1", "title": "2.1 How it Works"}]}
                ]
            }
        }

    def run_chapter_generation_logic(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        This function should contain the core logic from your chapter generation script.
        """
        logging.info(f"Received chapter generation request with payload: {payload}")
        # Example: input_file = payload.get("input_file")
        # result = generate_chapters_main(['--input', input_file, ...])
        return {"status": "success", "message": "Chapter generation complete (mock response)."}
    # --- End of Placeholder Functions ---


    @app.post("/api/generate/outline")
    async def generate_outline(payload: Dict[str, Any] = Body(...)):
        try:
            result = run_outline_generation_logic(payload)
            return result
        except Exception as e:
            logging.error(f"Error in generate_outline: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/generate/chapters")
    async def generate_chapters(payload: Dict[str, Any] = Body(...)):
        try:
            result = run_chapter_generation_logic(payload)
            return result
        except Exception as e:
            logging.error(f"Error in generate_chapters: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    def read_root():
        return {"message": "Platform IDE Python API server is running"}

    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)
    ```
    **Action Required**: The most important task here is to refactor the logic from your existing `.py` scripts into the `run_*_logic` functions in the `api_server.py` file.

### Step 3: Configure Next.js Dev Server Proxy

To make calling the Python API from the frontend seamless (and avoid CORS errors), we'll proxy API requests through the Next.js dev server.

1.  **Edit `web-learner/next.config.ts`**: Add the `rewrites` configuration.

    ```typescript
    // In web-learner/next.config.ts
    /** @type {import('next').NextConfig} */
    const nextConfig = {
      // ... any other existing config
      
      async rewrites() {
        // This proxies requests from the frontend (on port 3000) to the backend (on port 8000)
        // It only applies in development.
        return [
          {
            source: '/api/:path*',
            destination: 'http://localhost:8000/api/:path*',
          },
        ];
      },
    };

    export default nextConfig;
    ```

### Step 4: Update Frontend Code to Use the API

Now, modify the components that trigger script generation to call our new API endpoints using `fetch`.

1.  **Locate the Triggering Logic**: Find the functions in your Zustand store (e.g., `useThemeGeneratorStore`) that currently run the local scripts.

2.  **Modify the Logic**: Change them to make HTTP POST requests.

    **Example "Before" (conceptual):**
    ```typescript
    // in useThemeGeneratorStore.ts
    // This is a guess at how it might work now.
    startOutlineGeneration: async () => {
      const { themeName, content } = get();
      // Some mechanism that invokes a python script directly
      const result = await window.electronAPI.runPythonScript('generate_outline', { themeName, content });
      set({ outlineResult: result });
    }
    ```

    **Example "After" (implement this):**
    ```typescript
    // in useThemeGeneratorStore.ts
    startOutlineGeneration: async () => {
      const { themeName, content, generationStyle } = get();
      set({ stage: 'generating_outline', isSubscribing: true, logs: ['Sending request to backend...'] });

      try {
        // The request goes to the Next.js dev server, which proxies it to Python
        const response = await fetch('/api/generate/outline', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            subject: themeName,
            expected_content: content,
            learning_style: generationStyle,
            // Add any other parameters your script needs
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to generate outline');
        }

        const result = await response.json();
        set({ outlineResult: result, stage: 'outline_ready', isSubscribing: false });
      } catch (error) {
        console.error('Outline generation failed:', error);
        const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred.';
        set({ 
            stage: 'generating_outline', 
            collectStage: { status: 'error', detail: errorMessage },
            isSubscribing: false 
        });
      }
    }
    ```

### Step 5: Run and Test Locally

You now need two separate terminals to run the full application stack.

1.  **Terminal 1: Start the Python Backend**
    ```bash
    # Navigate to the project root
    cd /path/to/platform-ide-1020

    # Activate the virtual environment
    source venv/bin/activate

    # Start the FastAPI server with auto-reload
    uvicorn scripts.api_server:app --reload --port 8000
    ```
    You should see a confirmation that the Uvicorn server is running on `http://0.0.0.0:8000`.

2.  **Terminal 2: Start the Next.js Frontend**
    ```bash
    # Navigate to the project root
    cd /path/to/platform-ide-1020

    # Start the web app
    pnpm dev:web
    ```
    The frontend is now running on `http://localhost:3000`.

Open your browser to `http://localhost:3000`, use your "Theme Generator" feature, and watch the logs in both terminals. The frontend should make a request, which will appear in the Next.js logs and then be forwarded to the FastAPI server, where you'll see the Python logs.

---

## Phase 2: Deployment to AWS

Once the local refactoring is complete and tested, you can deploy to your AWS server.

### Step 1: Server Preparation

Connect to your AWS instance via SSH and install all necessary tools.

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Git, Nginx, and Python environment tools
sudo apt install -y git nginx python3-pip python3.10-venv

# Install Node.js via nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
source ~/.bashrc
nvm install --lts

# Install pnpm and pm2 globally
npm install -g pnpm pm2
```

### Step 2: Deploy Code and Install Dependencies

1.  **Clone Your Repository**:
    ```bash
    git clone <your-repository-url>
    cd platform-ide-1020
    ```

2.  **Install Python Dependencies**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Install Frontend Dependencies and Build**:
    ```bash
    pnpm install
    pnpm build:web # This runs the 'build' script inside web-learner/package.json
    ```

### Step 3: Run Services with PM2

We'll use the process manager `pm2` to run both services in the background and ensure they restart on failure or server reboot.

1.  **Start the Python API Service**:
    ```bash
    # Make sure you are in the project root and the venv is active
    source venv/bin/activate
    pm2 start "uvicorn scripts.api_server:app --host 0.0.0.0 --port 8000" --name "python-api"
    ```

2.  **Start the Next.js App**:
    ```bash
    # Navigate to the web-learner directory
    cd web-learner
    pm2 start pnpm --name "web-learner" -- start # The 'start' script should run 'next start'
    ```

3.  **Check Status and Save**:
    ```bash
    pm2 status  # Verify both apps are 'online'
    pm2 save    # Save the process list to resurrect on reboot
    ```

### Step 4: Configure Nginx

Finally, configure Nginx to route traffic correctly.

1.  **Create Nginx Config File**:
    ```bash
    sudo nano /etc/nginx/sites-available/platform-ide
    ```

2.  **Paste This Configuration**: Replace `your_domain_or_ip` with your server's public IP address or your domain name.

    ```nginx
    server {
        listen 80;
        server_name your_domain_or_ip;

        # Route API calls to the Python/FastAPI service
        location /api/ {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Route all other traffic to the Next.js app
        location / {
            proxy_pass http://127.0.0.1:3000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
    ```

3.  **Enable the Site and Restart Nginx**:
    ```bash
    # Create a symbolic link to enable the site
    sudo ln -s /etc/nginx/sites-available/platform-ide /etc/nginx/sites-enabled/

    # Test the configuration for syntax errors
    sudo nginx -t

    # Restart Nginx to apply the changes
    sudo systemctl restart nginx
    ```

Your application should now be live and accessible via your server's IP address or domain name.
