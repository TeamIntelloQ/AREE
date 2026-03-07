FROM python:3.12-slim

WORKDIR /app

COPY . /app

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
    scikit-learn \
    scipy

EXPOSE 8501

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", \
     "--browser.gatherUsageStats=false"]