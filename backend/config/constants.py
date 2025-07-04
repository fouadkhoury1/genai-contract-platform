import os

# API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Database Collections
CONTRACTS_COLLECTION = "contracts"
LOGS_COLLECTION = "logs"
CLIENTS_COLLECTION = "clients"

# Metrics Tracking
request_count = 0
cumulative_latency = 0.0

# AI Model Configuration
DEEPSEEK_MODEL = "deepseek-reasoner"

# Pagination
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100 