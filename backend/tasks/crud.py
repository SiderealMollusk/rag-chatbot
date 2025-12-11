import time
import uuid
import sqlalchemy
from sqlalchemy import create_engine, text
from backend.tasks import app
from loguru import logger
import os

# We need a dedicated DB engine for the worker to avoid import cycles with the main app if possible.
# Ideally we import from backend.database, but for this test we'll create a fresh engine.
DB_URL = os.environ.get("DATABASE_URL", "sqlite:////data/bible.db")
engine = create_engine(DB_URL)

@app.task(name="tasks.fast_crud_task", bind=True)
def fast_crud_task(self, data: str):
    """
    Performs a full Create-Read-Update-Delete cycle on a 'job_test' table.
    Returns: {"lifecycle": ["created", "verified", "delted"]} checks.
    """
    task_id = self.request.id
    log = logger.bind(task_id=task_id, data=data)
    
    unique_val = f"{data}_{uuid.uuid4().hex[:6]}"
    receipt = {"lifecycle": []}
    
    try:
        with engine.connect() as conn:
            # 0. Ensure table exists (Lazy check)
            conn.execute(text("CREATE TABLE IF NOT EXISTS job_test (id TEXT PRIMARY KEY, value TEXT)"))
            conn.commit()

            # 1. CREATE
            log.trace(f"Starting CRUD Cycle for {task_id}")
            log.debug(f"Generating unique value: {unique_val}")
            
            log.info("Step 1: Create")
            conn.execute(text("INSERT INTO job_test (id, value) VALUES (:id, :val)"), {"id": task_id, "val": unique_val})
            conn.commit()
            receipt["lifecycle"].append("created")

            # 2. READ
            log.info("Step 2: Read")
            res = conn.execute(text("SELECT value FROM job_test WHERE id = :id"), {"id": task_id}).fetchone()
            if not res or res[0] != unique_val:
                log.warning(f"Read mismatch! Expected {unique_val}, Got {res}")
                raise ValueError("Read mismatch")
            log.debug("Read verification passed.")
            receipt["lifecycle"].append("read")

            # 3. UPDATE
            log.info("Step 3: Update")
            new_val = unique_val + "_UPDATED"
            conn.execute(text("UPDATE job_test SET value = :val WHERE id = :id"), {"val": new_val, "id": task_id})
            conn.commit()
            receipt["lifecycle"].append("updated")

            # 4. RE-READ
            log.info("Step 4: Re-Read")
            res = conn.execute(text("SELECT value FROM job_test WHERE id = :id"), {"id": task_id}).fetchone()
            if not res or res[0] != new_val:
                 log.error("Update failed to persist!")
                 raise ValueError("Update verification mismatch")
            log.debug(f"Update verified: {res[0]}")
            receipt["lifecycle"].append("verified")

            # 5. DELETE
            log.info("Step 5: Delete")
            conn.execute(text("DELETE FROM job_test WHERE id = :id"), {"id": task_id})
            conn.commit()
            receipt["lifecycle"].append("deleted")

            # 6. CONFIRM GONE
            res = conn.execute(text("SELECT value FROM job_test WHERE id = :id"), {"id": task_id}).fetchone()
            if res:
                log.critical("Zombie record found! Delete failed.")
                raise ValueError("Delete failed")
            receipt["lifecycle"].append("confirmed_gone")
            
            log.success("CRUD Cycle Complete successfully.")
            return receipt

    except Exception as e:
        log.error(f"CRUD Failed: {e}")
        raise e

@app.task(name="tasks.sleep_crud_task", bind=True)
def sleep_crud_task(self, seconds: int, data: str):
    """
    Sleeps then performs CRUD. Tests connection holding.
    """
    logger.bind(task_id=self.request.id).info(f"Holding connection... sleeping {seconds}s")
    # We purposefully do NOT hold the DB transaction open during sleep here (that would lock sqlite).
    # We sleep *before* the operation to simulate queue latency.
    time.sleep(seconds)
    return fast_crud_task(self, data)
