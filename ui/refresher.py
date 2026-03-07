import time
import random
import os

# Create dummy file for Streamlit to watch
dummy_path = "dummy.py"

print("🔄 Auto-refresher started - dashboard will update every 30 seconds...")
print(f"📁 Watching: {dummy_path}")

while True:
    # Write random number to trigger Streamlit reload
    with open(dummy_path, "w") as f:
        f.write(f"ref={random.randint(1, 10000)}")
    
    print(f"✅ Updated {dummy_path} - waiting 30 seconds...")
    time.sleep(30)
