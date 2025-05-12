FROM python:3.9-slim

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /videoenv
ENV PATH="/videoenv/bin:$PATH"

RUN pip install --upgrade pip \
    && pip install streamlit opencv-python requests numpy


COPY . /app/

WORKDIR /app
RUN mkdir -p /app/output && chmod 777 /app/output
EXPOSE 8501

CMD ["streamlit", "run", "main.py"]