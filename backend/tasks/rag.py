from celery import Celery
import os
import json
import random
import requests
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tasks import app
from loguru import logger

# Config
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://host.docker.internal:11434/api/chat') # Access host from container

PROMPT_FILE = "/app/data/passes/02_deep_profiling/prompt.md"
OUTPUT_FILE = "/app/data/passes/02_deep_profiling/corpus.02.annotated.jsonl"

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_system_prompt() -> str:
    try:
        with open(PROMPT_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""

# --- HELPER: Result Writer ---
def append_results(valid_results):
    if not valid_results: return
    # Atomic-ish append
    try:
        with open(OUTPUT_FILE, 'a') as f:
            for r in valid_results:
                f.write(json.dumps(r) + "\n")
    except Exception as e:
        logger.error(f"Failed to write results: {e}")
        raise e

# --- TASK 1: CLOUD (Gemini) ---
@app.task(name="tasks.rag.process_batch_gemini", bind=True, max_retries=5)
def process_batch_gemini(self, batch_ids: list, batch_data: list):
    """
    Process batch using Gemini 2.5 Flash.
    """
    log = logger.bind(task="gemini", id=self.request.id[:8])

    if not GEMINI_API_KEY:
        log.error("Missing API Key")
        return {"status": "failed", "reason": "no_key"}

    system_prompt = get_system_prompt()
    batch_text = "\n".join([json.dumps(r) for r in batch_data])
    prompt = f"{system_prompt}\n\nINPUT DATA:\n{batch_text}"
    
    # Use the configured model
    from core.config import GEMINI_MODEL_NAME
    model = genai.GenerativeModel(GEMINI_MODEL_NAME, safety_settings=SAFETY_SETTINGS)

    try:
        log.info(f"Sending Batch {len(batch_ids)} items to Cloud...")
        resp = model.generate_content(prompt)

        # Rate Limit / Block Check
        if not resp.parts and resp.prompt_feedback:
             log.warning(f"Response blocked! {resp.prompt_feedback}")
             return {"status": "blocked"}

        # Parse
        clean_text = resp.text.replace('```json', '').replace('```', '').strip()
        results = []
        try:
            data = json.loads(clean_text)
            results = data if isinstance(data, list) else [data]
        except:
             # Fallback line parser
             for line in clean_text.split('\n'):
                if line.strip().startswith('{'):
                    try: results.append(json.loads(line.rstrip(',')))
                    except: pass

        # Filter & Save
        valid = [r for r in results if r.get('id') in batch_ids]
        if valid:
            append_results(valid)
            log.success(f"Cloud Success: {len(valid)}/{len(batch_ids)}")
            return {"status": "success", "count": len(valid)}
        else:
            log.warning("Cloud Parsed 0 valid records.")
            return {"status": "empty"}

    except Exception as e:
        err = str(e)
        if "429" in err or "503" in err or "Quota" in err:
            wait = 10 * (2 ** self.request.retries) + random.randint(1, 5)
            log.warning(f"Cloud Rate Limit ({e}). Sleeping {wait}s.")
            raise self.retry(exc=e, countdown=wait)
        else:
            log.error(f"Cloud Error: {e}")
            raise e


# --- TASK 2: METAL (Ollama) ---
@app.task(name="tasks.rag.process_batch_ollama", bind=True, max_retries=3)
def process_batch_ollama(self, batch_ids: list, batch_data: list):
    """
    Process batch using Local Ollama (Phi/Llama/Mistral).
    """
    log = logger.bind(task="metal", id=self.request.id[:8])
    
    system_prompt = get_system_prompt()
    batch_text = "\n".join([json.dumps(r) for r in batch_data])
    
    # Use generic model from env or default
    model_name = os.environ.get("OLLAMA_MODEL", "llama3")
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": batch_text}
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096}
    }

    try:
        log.info(f"Sending Batch {len(batch_ids)} to Metal ({model_name})...")
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300) # Long timeout for local
        resp.raise_for_status()
        
        content = resp.json()['message']['content']
        
        # Parse (Reuse logic? For now copy-paste for isolation)
        clean_text = content.replace('```json', '').replace('```', '').strip()
        results = []
        try:
            data = json.loads(clean_text)
            results = data if isinstance(data, list) else [data]
        except:
             for line in clean_text.split('\n'):
                if line.strip().startswith('{'):
                    try: results.append(json.loads(line.rstrip(',')))
                    except: pass
                    
        valid = [r for r in results if r.get('id') in batch_ids]
        
        if valid:
            append_results(valid)
            log.success(f"Metal Success: {len(valid)}/{len(batch_ids)}")
            return {"status": "success", "count": len(valid)}
        else:
            log.warning(f"Metal Parsed 0 valid records. Raw len: {len(content)}")
            return {"status": "empty"}

    except Exception as e:
        log.error(f"Metal Error: {e}")
        # Metal retries are shorter, assuming transient glitch
        raise self.retry(exc=e, countdown=10)
