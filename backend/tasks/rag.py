from celery import Celery
import os
import json
import random
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tasks import app
from loguru import logger

# Config
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
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

@app.task(name="tasks.process_batch", bind=True, max_retries=10)
def process_batch(self, batch_ids: list, batch_data: list):
    """
    Process a specific list of paragraph records using Gemini.
    """
    if not GEMINI_API_KEY:
        logger.error("No GEMINI_API_KEY found.")
        return {"status": "failed", "reason": "no_key"}

    log = logger.bind(task_id=self.request.id, batch_size=len(batch_ids))
    log.info(f"Processing Batch ({batch_ids[0]}...)")
    
    system_prompt = get_system_prompt()
    if not system_prompt:
        return {"status": "failed", "reason": "no_prompt"}

    # Format input
    batch_text = "\n".join([json.dumps(r) for r in batch_data])
    prompt = f"{system_prompt}\n\nINPUT DATA:\n{batch_text}"

    model = genai.GenerativeModel("gemini-1.5-flash", safety_settings=SAFETY_SETTINGS)

    try:
        resp = model.generate_content(prompt)
        
        if not resp.parts and resp.prompt_feedback:
             log.warning(f"Response blocked: {resp.prompt_feedback}")
             return {"status": "blocked"}
             
        clean_text = resp.text.replace('```json', '').replace('```', '').strip()
        results = []
        
        try:
            data = json.loads(clean_text)
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict):
                results = [data]
        except:
             for line in clean_text.split('\n'):
                line = line.strip()
                if not line: continue
                if line.endswith(','): line = line[:-1]
                try: results.append(json.loads(line))
                except: pass
        
        valid = [r for r in results if r.get('id') in batch_ids]
        
        if valid:
            # Atomic Append?
            # Ideally we send to a RESULT queue or DB.
            # Here we append to file as per v1 spec.
            with open(OUTPUT_FILE, 'a') as f:
                for r in valid:
                    f.write(json.dumps(r) + "\n")
            
            log.success(f"Processed {len(valid)} records")
            return {"status": "success", "count": len(valid), "ids": [r['id'] for r in valid]}
        else:
            log.warning("No valid records parsed")
            raise ValueError("Empty parse result")
            
    except Exception as e:
        err = str(e)
        if "429" in err or "Quota" in err:
            wait = 30 * (2 ** self.request.retries) + random.randint(1, 10)
            log.warning(f"Rate Limit 429. Retrying in {wait}s...")
            raise self.retry(exc=e, countdown=wait)
        else:
            log.error(f"Error: {e}")
            raise e
