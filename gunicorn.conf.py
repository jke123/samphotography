import os

# Port dynamique Render
port = os.getenv("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Workers
workers = 2
worker_class = "sync"

# Timeouts — nécessaire pour upload de photos
timeout = 180
keepalive = 5

# ⚠️ Limites de taille de requête — fix erreur 413
limit_request_line    = 0   # illimité
limit_request_fields  = 200
limit_request_field_size = 0  # illimité

# Logs
accesslog = "-"
errorlog  = "-"
loglevel  = "info"
