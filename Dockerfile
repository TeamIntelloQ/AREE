FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir \
    streamlit==1.31.0 \
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
    scipy \
    flask \
    flask-cors

EXPOSE 8501

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]