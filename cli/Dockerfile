FROM python:3.9-slim

WORKDIR /app

# No requirements yet, standard library only
# COPY requirements.txt .
# RUN pip install -r requirements.txt

COPY . .

CMD ["python", "setup_db.py"]
