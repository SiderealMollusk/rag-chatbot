# scripts/jobs/core/config.py

# --- GEMINI CLOUD CONFIGURATION ---

# The Model to use for the Cloud Worker
# Source: User Investigation (API discovery), 2025-12-11
GEMINI_MODEL_NAME = "gemini-2.5-flash-lite"

# --- RATE LIMIT STRATEGY ---
# Distinguishing between what Google gives us (Provider) and what we use (My/Safe).

# 1. PROVIDER LIMITS (The ceiling Google hands us)
# Source: User prompt/docs ("current model has only 5 RPD"?? Assuming RPM logic here for the 10)
# We record these here for reference/provenance.
_PROVIDER_LIMIT_RPM = 10     # Requests Per Minute
_PROVIDER_LIMIT_TPM = 7000   # Tokens Per Minute
_PROVIDER_LIMIT_RPD = 1000   # Requests Per Day

# 2. MY LIMITS (The operational settings we actually use)
# Strategy: "Always at 1/2 of any known limits" to ensure safety.
_MY_RATELIMIT_RPM = int(_PROVIDER_LIMIT_RPM * 0.5) 
_MY_RATELIMIT_TPM = int(_PROVIDER_LIMIT_TPM * 0.5)
_MY_RATELIMIT_RPD = int(_PROVIDER_LIMIT_RPD * 0.5)

# 3. EXPORTS (Bindings for the Conductor/Application)
GEMINI_RATE_LIMIT_RPM = _MY_RATELIMIT_RPM
GEMINI_RATE_LIMIT_TPM = _MY_RATELIMIT_TPM
GEMINI_RATE_LIMIT_RPD = _MY_RATELIMIT_RPD

# --- METAL WORKER CONFIGURATION ---
METAL_QUEUE_DEPTH = 2
METAL_MODEL_NAME = "llama3"

# --- SYSTEM SETTINGS ---
LOG_LEVEL = "INFO"
