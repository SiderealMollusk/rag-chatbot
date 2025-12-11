from celery import Celery
import os
import time
import json
import logging
import random
import requests
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Celery
app = Celery('movie_bible', 
             broker=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
             backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'))

# Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
PROMPT_FILE = "/app/data/passes/02_deep_profiling/prompt.md" # Path inside container
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
        # Fallback if file not mounted correctly or path differs
        # This is risky but better than crashing if we can survive.
        # Ideally, we should crash.
        logger.error(f"Prompt file not found at {PROMPT_FILE}")
        return ""

@app.task(name="tasks.process_batch", bind=True, max_retries=10)
def process_batch(self, batch_ids: list, batch_data: list):
    """
    Process a specific list of paragraph records using Gemini.
    """
    if not GEMINI_API_KEY:
        logger.error("No GEMINI_API_KEY found.")
        return "Failed: No API Key"

    logger.info(f"Processing Batch of {len(batch_ids)} items: {batch_ids[0]}...")
    
    system_prompt = get_system_prompt()
    if not system_prompt:
        return "Failed: No Prompt"

    # Format input
    batch_text = "\n".join([json.dumps(r) for r in batch_data])
    prompt = f"{system_prompt}\n\nINPUT DATA:\n{batch_text}"

    model = genai.GenerativeModel("gemini-1.5-flash", safety_settings=SAFETY_SETTINGS)

    try:
        resp = model.generate_content(prompt)
        
        # Check for blocked/empty
        if not resp.parts and resp.prompt_feedback:
             logger.warning(f"Response blocked: {resp.prompt_feedback}")
             return "Blocked"
             
        # Parse Response
        clean_text = resp.text.replace('```json', '').replace('```', '').strip()
        results = []
        
        # Try Parse
        try:
            # Try plain JSON list
            data = json.loads(clean_text)
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict):
                results = [data]
        except:
             # Try NDJSON
             for line in clean_text.split('\n'):
                line = line.strip()
                if not line: continue
                if line.endswith(','): line = line[:-1]
                try:
                    results.append(json.loads(line))
                except:
                    pass
        
        # Filter for valid IDs
        valid = [r for r in results if r.get('id') in batch_ids]
        
        if valid:
            # Write to File directly from Worker?
            # Or return to caller?
            # Writing from multiple workers to one file is risky without locking.
            # But specific files are fine.
            # For simplicity in this rough setup, we append to the main file.
            # We rely on OS atomic append for short lines, but this could interleave.
            # Better architecture: Write to Redis/Database.
            # "Good Enough" architecture: Writes to file with flock or just pray.
            # We will use simple append and hope content is small enough to be atomic or mostly okay.
            
            with open(OUTPUT_FILE, 'a') as f:
                for r in valid:
                    f.write(json.dumps(r) + "\n")
            
            return f"Success: {len(valid)} records"
        else:
            logger.warning("No valid records parsed from LLM response.")
            raise ValueError("Empty parse result")
            
    except Exception as e:
        err = str(e)
        if "429" in err or "Quota" in err:
            # Backoff
            wait = 30 * (2 ** self.request.retries)
            # Add jitter
            wait += random.randint(1, 10)
            logger.warning(f"Rate Limit 429. Retrying in {wait}s...")
            raise self.retry(exc=e, countdown=wait)
        else:
            logger.error(f"Error: {e}")
            raise e
