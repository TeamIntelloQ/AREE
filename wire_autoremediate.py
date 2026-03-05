# -*- coding: utf-8 -*-
with open("ui/app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import
old_import = "from core.mock_data import ("
new_import = "from core.auto_remediate import auto_remediate, get_remediation_log, get_system_status\nfrom core.mock_data import ("
if old_import in content:
    content = content.replace(old_import, new_import, 1)
    print("Step 1 OK: import added")
else:
    print("Step 1 FAIL: import not found")

# 2. Add auto-remediation block after data loading
old_data = "# \u2500\u2500 Scenario Modifiers"
new_data = (
    "# \u2500\u2500 Auto Remediation \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "data, auto_actions = auto_remediate(data, critical_threshold)\n"
    "if auto_actions:\n"
    "    for act in auto_actions:\n"
    "        st.toast(f\"AUTO-FIXED {act['service']}: RE {act['re_before']} -> {act['re_after']}\")\n"
    "\n"
    "# \u2500\u2500 Scenario Modifiers"
)
if old_data in content:
    content = content.replace(old_data, new_data, 1)
    print("Step 2 OK: auto-remediation block added")
else:
    print("Step 2 FAIL: scenario modifiers marker not found")

# 3. Add remediation log at end
log_block = (
    "\n"
    "# \u2500\u2500 Auto-Remediation Log \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "st.markdown('---')\n"
    "st.markdown('### Auto-Remediation Log')\n"
    "rem_log = get_remediation_log()\n"
    "if rem_log.empty:\n"
    "    st.success('No interventions triggered this session - system stable.')\n"
    "else:\n"
    "    for _, row in rem_log.iterrows():\n"
    "        color = '#ef4444' if row['severity'] == 'CRITICAL' else '#f97316'\n"
    "        st.markdown(\n"
    "            f'<div style=\"background:#0f172a; border-left:4px solid {color}; '\n"
    "            f'padding:10px 16px; border-radius:6px; margin-bottom:8px;\">'\n"
    "            f'<span style=\"color:#9CA3AF; font-size:12px;\">{row[\"timestamp\"]}</span>'\n"
    "            f'<span style=\"color:white; font-weight:bold; margin-left:12px;\">{row[\"service\"]}</span>'\n"
    "            f'<span style=\"color:{color}; margin-left:12px;\">RE: {row[\"re_before\"]} -> {row[\"re_after\"]}</span>'\n"
    "            f'<div style=\"color:#d1d5db; font-size:13px; margin-top:4px;\">{row[\"action\"]}</div>'\n"
    "            f'</div>',\n"
    "            unsafe_allow_html=True\n"
    "        )\n"
)
content = content.rstrip() + "\n" + log_block

with open("ui/app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("SUCCESS: Auto-remediation fully integrated.")
