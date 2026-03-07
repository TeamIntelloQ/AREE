FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install only essential packages for Railway
RUN pip install --no-cache-dir \
    streamlit \
    plotly \
    networkx \
    matplotlib \
    numpy \
    pandas \
    requests \
    python-dotenv \
    slack-sdk \
    psutil \
    flask \
    flask-cors \
    scikit-learn \
    scipy

# Copy all project files
COPY . /app

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
