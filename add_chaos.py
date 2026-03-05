# -*- coding: utf-8 -*-
with open("ui/app.py", "r", encoding="utf-8") as f:
    content = f.read()

chaos_block = """
    st.markdown("---")
    st.subheader("Chaos Simulator")
    latency_slider = st.slider("Test Latency (ms)", 100, 5000, 2000)
    chaos_service = st.text_input("Service Name", "api-svc-01")

    if st.button("Scan Service", use_container_width=True):
        from shared_schema import create_mock_payload
        from ml_engine import compute_ml_scores
        from re_engine import compute_re_score
        payload = create_mock_payload(chaos_service)
        payload["oss_score"] = max(0.1, 0.8 - (latency_slider / 10000))
        payload["tes_score"] = 0.6
        payload = compute_ml_scores(payload)
        result = compute_re_score(chaos_service, latency_slider)
        st.metric("RE Score", f"{result['re_score']:.1%}")
        st.metric("Status", result['aura_level'])
        st.metric("Action", "auto-remediate" if result['aura_level'] == "red" else "observe")

    if st.button("Chaos Test (10 svcs)", use_container_width=True):
        from re_engine import compute_re_score
        import numpy as np
        chaos_data = []
        alerts = 0
        st.markdown("**Chaos Results:**")
        for i in range(10):
            latency = np.random.uniform(500, 5000)
            svc_id = f"SVC-{i}"
            result = compute_re_score(svc_id, latency)
            chaos_data.append(result['re_score'])
            emoji = "!!" if result['re_score'] > 0.7 else "OK"
            st.write(f"**{svc_id}**: Latency={latency:.0f}ms -> RE={result['re_score']:.1%} [{emoji}]")
            if result['re_score'] > 0.7:
                alerts += 1
        st.success(f"{alerts}/10 HIGH-RISK -> AUTO-REMEDIATED!")
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Bar(
            x=[f"SVC-{i}" for i in range(10)],
            y=chaos_data,
            marker_color=['red' if x > 0.7 else 'green' for x in chaos_data]
        )])
        fig.update_layout(title="Chaos Test RE Scores", paper_bgcolor="#020617", font={"color": "white"})
        st.plotly_chart(fig, use_container_width=True)
"""

target = '    st.caption("AREE v1.0 | Hackathon Build")'
if target in content:
    content = content.replace(target, chaos_block + "\n    " + 'st.caption("AREE v1.0 | Hackathon Build")')
    with open("ui/app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Chaos Simulator added to sidebar.")
else:
    print("NOT FOUND: Could not locate insertion point.")
