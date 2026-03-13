# gunicorn.conf.py
import multiprocessing
import os

# Binding
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Gunicorn Worker Settings for Uvicorn
# Dynamically scale workers to CPU cores for maximum concurrent Webhook handling
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Threads and connections
threads = 2
backlog = 2048

# Timeouts
timeout = 120
keepalive = 5

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# The FastAPI hooks will automatically spin up their own DB pools via Supabase/PostgreSQL.
