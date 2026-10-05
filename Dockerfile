FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	API_HOST=0.0.0.0 \
	API_PORT=8000

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/agents ./agents
COPY src/api ./api
COPY src/graph ./graph
COPY src/state ./state
COPY src/tools ./tools
COPY src/config.py ./config.py
COPY src/main.py ./main.py

EXPOSE 8000

CMD ["python", "main.py"]
