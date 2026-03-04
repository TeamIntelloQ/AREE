import subprocess
import time

REMEDIATIONS = {
    "db": "kubectl scale deployment db --replicas=3",
    "api": "kubectl delete pod api-risky-xyz",  # Mock isolate
    "cache": "kubectl apply -f cache-fix.yaml"
}

def auto_remediate(service: str, re_pct: float):
    if re_pct > 0.85:
        cmd = REMEDIATIONS.get(service, "echo 'Manual intervention'")
        subprocess.run(cmd, shell=True)
        print(f"✅ Remediated {service}")
        time.sleep(2)  # Simulate
        return True
    return False
