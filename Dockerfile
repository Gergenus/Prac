FROM python:3.9-slim

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /videoenv
ENV PATH="/videoenv/bin:$PATH"

RUN pip install --no-cache-dir torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir ultralytics==8.0.124
RUN pip install streamlit opencv-python requests


COPY . /app/

WORKDIR /app
RUN mkdir -p /app/output && chmod 777 /app/output
EXPOSE 8501

CMD ["streamlit", "run", "main.py"]