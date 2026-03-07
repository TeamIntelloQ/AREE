import streamlit as st
import requests
import pandas as pd

# YOUR API KEY — already set!
ABUSEIPDB_KEY = "70aba9d4158da46b5b2210c3ec6b37096cd7851874c23626bb85edc49d28ea9d6366255f9a549cb9"

@st.cache_data(ttl=300)  # Refresh every 5 mins
def fetch_live_threats():
    """Fetch LIVE malicious IPs from AbuseIPDB blacklist."""
    url = "https://api.abuseipdb.com/api/v2/blacklist"
    
    headers = {
        "Key": ABUSEIPDB_KEY,
        "Accept": "application/json"
    }
    
    params
