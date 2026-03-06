{\rtf1\ansi\ansicpg1252\cocoartf2758
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
import anthropic\
\
st.set_page_config(\
page_title=\'93OUTsurance Pillar II GloBE\'94,\
page_icon=\'93P2\'94,\
layout=\'93wide\'94,\
initial_sidebar_state=\'93expanded\'94\
)\
\
st.markdown(\'94\'94\'94\
\
<style>\
.stApp \{ background-color: #0B0F1A; \}\
section[data-testid="stSidebar"] \{ background-color: #111827; \}\
h1, h2, h3 \{ color: #E2E8F0; \}\
p \{ color: #94A3B8; \}\
</style>\
\
\'93\'94\'94, unsafe_allow_html=True)\
\
JUR_INFO = \{\
\'93ZA\'94: \{\'93name\'94: \'93South Africa\'94, \'93role\'94: \'93HQ / UPE\'94, \'93std_rate\'94: 27.0\},\
\'93AU\'94: \{\'93name\'94: \'93Australia\'94,    \'93role\'94: \'93Subsidiary\'94, \'93std_rate\'94: 30.0\},\
\'93IE\'94: \{\'93name\'94: \'93Ireland\'94,      \'93role\'94: \'93Subsidiary\'94, \'93std_rate\'94: 12.5\},\
\}\
\
def init_state():\
if \'93entities\'94 not in st.session_state:\
st.session_state.entities = pd.DataFrame([\
\{\'93Entity\'94: \'93OUTsurance Holdings Ltd\'94,  \'93Jurisdiction\'94: \'93ZA\'94, \'93Type\'94: \'93Insurance\'94,      \'93Revenue\'94: 8500.0, \'93PBT\'94: 2100.0, \'93CoveredTaxes\'94: 567.0, \'93DeferredTaxAdj\'94: 45.0, \'93Payroll\'94: 320.0, \'93TangibleAssets\'94: 1200.0, \'93Active\'94: True\},\
\{\'93Entity\'94: \'93OUTsurance Life Ltd\'94,       \'93Jurisdiction\'94: \'93ZA\'94, \'93Type\'94: \'93Life Insurance\'94, \'93Revenue\'94: 3200.0, \'93PBT\'94: 890.0,  \'93CoveredTaxes\'94: 240.0, \'93DeferredTaxAdj\'94: 18.0, \'93Payroll\'94: 85.0,  \'93TangibleAssets\'94: 340.0,  \'93Active\'94: True\},\
\{\'93Entity\'94: \'93OUTsurance Australia Pty\'94,  \'93Jurisdiction\'94: \'93AU\'94, \'93Type\'94: \'93Gen. Insurance\'94, \'93Revenue\'94: 1800.0, \'93PBT\'94: 420.0,  \'93CoveredTaxes\'94: 126.0, \'93DeferredTaxAdj\'94: 12.0, \'93Payroll\'94: 55.0,  \'93TangibleAssets\'94: 180.0,  \'93Active\'94: True\},\
\{\'93Entity\'94: \'93OUTsurance Ireland Ltd\'94,    \'93Jurisdiction\'94: \'93IE\'94, \'93Type\'94: \'93Reinsurance\'94,    \'93Revenue\'94: 950.0,  \'93PBT\'94: 280.0,  \'93CoveredTaxes\'94: 35.0,  \'93DeferredTaxAdj\'94: 8.0,  \'93Payroll\'94: 22.0,  \'93TangibleAssets\'94: 95.0,   \'93Active\'94: True\},\
])\
if \'93transactions\'94 not in st.session_state:\
st.session_state.transactions = pd.DataFrame([\
\{\'93Description\'94: \'93Reinsurance premium ZA to IE\'94, \'93From\'94: \'93OUTsurance Holdings Ltd\'94, \'93To\'94: \'93OUTsurance Ireland Ltd\'94,   \'93Amount\'94: 120.0, \'93Type\'94: \'93Reinsurance Premium\'94, \'93TP_Method\'94: \'93TNMM\'94, \'93ArmsLength\'94: True\},\
\{\'93Description\'94: \'93Management fee ZA to AU\'94,      \'93From\'94: \'93OUTsurance Holdings Ltd\'94, \'93To\'94: \'93OUTsurance Australia Pty\'94, \'93Amount\'94: 45.0,  \'93Type\'94: \'93Management Fee\'94,       \'93TP_Method\'94: \'93CUP\'94,  \'93ArmsLength\'94: True\},\
\{\'93Description\'94: \'93IT licence fee ZA to IE\'94,      \'93From\'94: \'93OUTsurance Holdings Ltd\'94, \'93To\'94: \'93OUTsurance Ireland Ltd\'94,   \'93Amount\'94: 30.0,  \'93Type\'94: \'93Royalty / IP\'94,         \'93TP_Method\'94: \'93TNMM\'94, \'93ArmsLength\'94: False\},\
])\
if \'93api_key\'94 not in st.session_state:\
st.session_state.api_key = \'93\'94\
\
init_state()\
\
def calc_globe():\
active = st.session_state.entities[st.session_state.entities[\'93Active\'94] == True].copy()\
results = []\
for jur, grp in active.groupby(\'93Jurisdiction\'94):\
globe_income = (grp[\'93PBT\'94] - grp[\'93DeferredTaxAdj\'94]).sum()\
adj_cov_tax  = (grp[\'93CoveredTaxes\'94] + grp[\'93DeferredTaxAdj\'94]).sum()\
sbie         = (0.05 * grp[\'93Payroll\'94] + 0.05 * grp[\'93TangibleAssets\'94]).sum()\
net_income   = max(0, globe_income - sbie)\
etr          = (adj_cov_tax / globe_income * 100) if globe_income > 0 else 0\
top_up_rate  = max(0, 15 - etr)\
top_up_tax   = (top_up_rate / 100) * net_income\
qdmtt        = top_up_rate > 0\
status       = \'93Compliant\'94 if etr >= 15 else (\'93Marginal\'94 if top_up_rate < 1 else \'93EXPOSURE\'94)\
j            = JUR_INFO.get(jur, \{\'93name\'94: jur, \'93role\'94: \'93\'94, \'93std_rate\'94: 0\})\
results.append(\{\
\'93Jur\'94: jur, \'93Name\'94: j[\'93name\'94], \'93Role\'94: j[\'93role\'94],\
\'93Entities\'94: len(grp), \'93GloBE_Income\'94: globe_income, \'93Adj_Cov_Tax\'94: adj_cov_tax,\
\'93SBIE\'94: sbie, \'93Net_Income\'94: net_income, \'93ETR\'94: etr,\
\'93TopUp_Rate\'94: top_up_rate, \'93TopUp_Tax\'94: top_up_tax,\
\'93QDMTT\'94: \'93Yes\'94 if qdmtt else \'93No\'94, \'93Status\'94: status,\
\})\
return pd.DataFrame(results)\
\
def call_claude(prompt):\
key = st.session_state.get(\'93api_key\'94, \'93\'94)\
if not key:\
try:\
key = st.secrets[\'93ANTHROPIC_API_KEY\'94]\
except Exception:\
return \'93No API key set. Add your Anthropic API key in the sidebar or Streamlit secrets.\'94\
try:\
client = anthropic.Anthropic(api_key=key)\
msg = client.messages.create(\
model=\'93claude-opus-4-5\'94,\
max_tokens=2048,\
messages=[\{\'93role\'94: \'93user\'94, \'93content\'94: prompt\}]\
)\
return msg.content[0].text\
except Exception as e:\
return \'93API Error: \'93 + str(e)\
\
def get_summary():\
results = calc_globe()\
lines = []\
for _, r in results.iterrows():\
lines.append(r[\'93Name\'94] + \'93 (\'94 + r[\'93Jur\'94] + \'93): GloBE Income ZAR\'94 + str(round(r[\'93GloBE_Income\'94],1)) + \'93m, ETR \'93 + str(round(r[\'93ETR\'94],2)) + \'93%, Top-up Tax ZAR\'94 + str(round(r[\'93TopUp_Tax\'94],1)) + \'93m\'94)\
return \'93\\n\'94.join(lines)\
\
# Sidebar\
\
with st.sidebar:\
st.markdown(\'94## OUTsurance\\n### Pillar II GloBE\'94)\
st.markdown(\'94\'97\'94)\
st.markdown(\'94#### Anthropic API Key\'94)\
api_input = st.text_input(\'93API Key\'94, value=st.session_state.api_key, type=\'93password\'94, placeholder=\'93sk-ant-\'85\'94, label_visibility=\'93collapsed\'94)\
if api_input:\
st.session_state.api_key = api_input\
st.success(\'93Key saved\'94)\
st.markdown(\'94\'97\'94)\
st.markdown(\'94#### Navigation\'94)\
page = st.radio(\'93Go to\'94, [\'93Dashboard\'94, \'93Entities\'94, \'93Transactions\'94, \'93Upload Data\'94, \'93AI Templates\'94, \'93Benchmarking\'94], label_visibility=\'93collapsed\'94)\
st.markdown(\'94\'97\'94)\
results_sidebar = calc_globe()\
total_topup_s = results_sidebar[\'93TopUp_Tax\'94].sum() if not results_sidebar.empty else 0\
st.metric(\'93Est. Top-up Tax\'94, \'93ZAR \'93 + str(round(total_topup_s, 1)) + \'93m\'94)\
st.metric(\'93Active Entities\'94, len(st.session_state.entities[st.session_state.entities[\'93Active\'94] == True]))\
\
# Header\
\
st.markdown(\'94# OUTsurance - Pillar II GloBE Reporting\'94)\
st.markdown(\'93OECD Global Minimum Tax | FY 2024 | South Africa - Australia - Ireland\'94)\
st.markdown(\'94\'97\'94)\
\
# \
\
if page == \'93Dashboard\'94:\
results = calc_globe()\
if results.empty:\
st.warning(\'93No active entities. Go to Entities tab to add entities.\'94)\
else:\
total_income = results[\'93GloBE_Income\'94].sum()\
total_tax    = results[\'93Adj_Cov_Tax\'94].sum()\
total_topup  = results[\'93TopUp_Tax\'94].sum()\
group_etr    = (total_tax / total_income * 100) if total_income > 0 else 0\
\
```\
    k1, k2, k3, k4 = st.columns(4)\
    k1.metric("Group ETR", str(round(group_etr, 2)) + "%", "Above 15% min" if group_etr >= 15 else "BELOW 15% min", delta_color="normal" if group_etr >= 15 else "inverse")\
    k2.metric("Est. Top-up Tax", "ZAR " + str(round(total_topup, 1)) + "m", delta_color="inverse" if total_topup > 0 else "normal")\
    k3.metric("GloBE Income", "ZAR " + str(round(total_income, 1)) + "m")\
    k4.metric("Active Entities", len(st.session_state.entities[st.session_state.entities["Active"] == True]))\
\
    st.markdown("---")\
    st.markdown("#### Jurisdiction GloBE Summary")\
    disp = results.copy()\
    disp["ETR (%)"]       = disp["ETR"].map(lambda x: str(round(x, 2)) + "%")\
    disp["TopUp_Rate (%)"]= disp["TopUp_Rate"].map(lambda x: str(round(x, 2)) + "%")\
    show_cols = \{"Name": "Jurisdiction", "Role": "Role", "Entities": "Entities",\
                 "GloBE_Income": "GloBE Income (ZARm)", "Adj_Cov_Tax": "Cov. Taxes (ZARm)",\
                 "SBIE": "SBIE (ZARm)", "ETR (%)": "ETR", "TopUp_Rate (%)": "Top-up Rate",\
                 "TopUp_Tax": "Top-up Tax (ZARm)", "QDMTT": "QDMTT", "Status": "Status"\}\
    st.dataframe(disp.rename(columns=show_cols)[[v for v in show_cols.values() if v in disp.rename(columns=show_cols).columns]], use_container_width=True, hide_index=True)\
\
    st.markdown("---")\
    st.markdown("#### Safe Harbour Assessment")\
    cols = st.columns(len(results))\
    for i, (_, r) in enumerate(results.iterrows()):\
        with cols[i]:\
            st.markdown("**" + r["Name"] + "**")\
            st.markdown(("OK" if r["ETR"] >= 15 else "FAIL") + " Simplified ETR: **" + str(round(r["ETR"], 2)) + "%**")\
            st.markdown("OK SBIE Exclusion: **ZAR " + str(round(r["SBIE"], 1)) + "m**")\
            if r["QDMTT"] == "Yes":\
                st.error("QDMTT Required: ZAR " + str(round(r["TopUp_Tax"], 1)) + "m")\
            else:\
                st.success("No top-up tax required")\
\
    st.markdown("---")\
    st.markdown("#### Entity ETR Overview")\
    active_e = st.session_state.entities[st.session_state.entities["Active"] == True].copy()\
    active_e["ETR %"] = (active_e["CoveredTaxes"] / active_e["PBT"].replace(0, 1)) * 100\
    st.bar_chart(active_e.set_index("Entity")[["ETR %"]])\
```\
\
# \
\
elif page == \'93Entities\'94:\
st.markdown(\'94## Entity Management\'94)\
st.markdown(\'93All figures in ZAR millions. Edit directly in the table.\'94)\
\
```\
tab1, tab2 = st.tabs(["View / Edit Entities", "Add New Entity"])\
\
with tab1:\
    edited = st.data_editor(\
        st.session_state.entities,\
        use_container_width=True,\
        num_rows="dynamic",\
        column_config=\{\
            "Jurisdiction":   st.column_config.SelectboxColumn("Jurisdiction", options=["ZA", "AU", "IE"]),\
            "Type":           st.column_config.SelectboxColumn("Type", options=["Insurance", "Life Insurance", "Gen. Insurance", "Reinsurance", "Holding", "Other"]),\
            "Revenue":        st.column_config.NumberColumn("Revenue (ZARm)",    format="%.1f"),\
            "PBT":            st.column_config.NumberColumn("Profit Before Tax", format="%.1f"),\
            "CoveredTaxes":   st.column_config.NumberColumn("Covered Taxes",     format="%.1f"),\
            "DeferredTaxAdj": st.column_config.NumberColumn("Deferred Tax Adj",  format="%.1f"),\
            "Payroll":        st.column_config.NumberColumn("Payroll",           format="%.1f"),\
            "TangibleAssets": st.column_config.NumberColumn("Tangible Assets",   format="%.1f"),\
            "Active":         st.column_config.CheckboxColumn("In Scope"),\
        \},\
        hide_index=True\
    )\
    if st.button("Save Changes", type="primary"):\
        st.session_state.entities = edited\
        st.success("Saved!")\
        st.rerun()\
\
with tab2:\
    c1, c2, c3 = st.columns(3)\
    with c1:\
        n_name = st.text_input("Entity Name")\
        n_jur  = st.selectbox("Jurisdiction", ["ZA", "AU", "IE"])\
        n_type = st.selectbox("Type", ["Insurance", "Life Insurance", "Gen. Insurance", "Reinsurance", "Holding", "Other"])\
    with c2:\
        n_rev = st.number_input("Revenue (ZARm)", value=0.0)\
        n_pbt = st.number_input("Profit Before Tax (ZARm)", value=0.0)\
        n_tax = st.number_input("Covered Taxes (ZARm)", value=0.0)\
    with c3:\
        n_dtx = st.number_input("Deferred Tax Adj (ZARm)", value=0.0)\
        n_pay = st.number_input("Payroll (ZARm)", value=0.0)\
        n_tan = st.number_input("Tangible Assets (ZARm)", value=0.0)\
    if st.button("Add Entity", type="primary"):\
        if n_name:\
            new_row = pd.DataFrame([\{"Entity": n_name, "Jurisdiction": n_jur, "Type": n_type, "Revenue": n_rev, "PBT": n_pbt, "CoveredTaxes": n_tax, "DeferredTaxAdj": n_dtx, "Payroll": n_pay, "TangibleAssets": n_tan, "Active": True\}])\
            st.session_state.entities = pd.concat([st.session_state.entities, new_row], ignore_index=True)\
            st.success("Added " + n_name)\
            st.rerun()\
        else:\
            st.error("Please enter an entity name.")\
```\
\
# \
\
elif page == \'93Transactions\'94:\
st.markdown(\'94## Intercompany Transaction Register\'94)\
tab1, tab2 = st.tabs([\'93Transaction Register\'94, \'93Add Transaction\'94])\
entity_names = list(st.session_state.entities[\'93Entity\'94])\
\
```\
with tab1:\
    edited_tx = st.data_editor(\
        st.session_state.transactions,\
        use_container_width=True,\
        num_rows="dynamic",\
        column_config=\{\
            "From":       st.column_config.SelectboxColumn("From Entity", options=entity_names),\
            "To":         st.column_config.SelectboxColumn("To Entity",   options=entity_names),\
            "Type":       st.column_config.SelectboxColumn("Type", options=["Reinsurance Premium", "Ceding Commission", "Management Fee", "Royalty / IP", "Loan Interest", "Capital Contribution", "Dividend", "Claims Reimbursement"]),\
            "TP_Method":  st.column_config.SelectboxColumn("TP Method", options=["CUP", "TNMM", "CPS", "PSM", "CPM"]),\
            "Amount":     st.column_config.NumberColumn("Amount (ZARm)", format="%.1f"),\
            "ArmsLength": st.column_config.CheckboxColumn("Arms Length"),\
        \},\
        hide_index=True\
    )\
    if st.button("Save Transactions", type="primary"):\
        st.session_state.transactions = edited_tx\
        st.success("Saved!")\
    flagged = st.session_state.transactions[st.session_state.transactions["ArmsLength"] == False]\
    if len(flagged) > 0:\
        st.warning(str(len(flagged)) + " transaction(s) flagged as NOT arms length - review required.")\
\
with tab2:\
    c1, c2 = st.columns(2)\
    with c1:\
        tx_desc = st.text_input("Description")\
        tx_from = st.selectbox("From Entity", entity_names)\
        tx_to   = st.selectbox("To Entity", entity_names, index=min(3, len(entity_names)-1))\
        tx_amt  = st.number_input("Amount (ZARm)", value=0.0)\
    with c2:\
        tx_type = st.selectbox("Transaction Type", ["Reinsurance Premium", "Ceding Commission", "Management Fee", "Royalty / IP", "Loan Interest", "Capital Contribution", "Dividend", "Claims Reimbursement"])\
        tx_tp   = st.selectbox("TP Method", ["CUP", "TNMM", "CPS", "PSM", "CPM"])\
        tx_arm  = st.checkbox("Arms Length", value=True)\
    if st.button("Add Transaction", type="primary"):\
        new_tx = pd.DataFrame([\{"Description": tx_desc, "From": tx_from, "To": tx_to, "Amount": tx_amt, "Type": tx_type, "TP_Method": tx_tp, "ArmsLength": tx_arm\}])\
        st.session_state.transactions = pd.concat([st.session_state.transactions, new_tx], ignore_index=True)\
        st.success("Added!")\
        st.rerun()\
```\
\
# \
\
elif page == \'93Upload Data\'94:\
st.markdown(\'94## Upload and Auto-Populate\'94)\
st.markdown(\'93Upload trial balance, statutory accounts or CbCR data (CSV or Excel) to populate entity fields automatically.\'94)\
\
```\
template_df = pd.DataFrame(\{"Entity": ["Entity Name"], "Jurisdiction": ["ZA"], "Type": ["Insurance"], "Revenue": [0.0], "PBT": [0.0], "CoveredTaxes": [0.0], "DeferredTaxAdj": [0.0], "Payroll": [0.0], "TangibleAssets": [0.0]\})\
st.download_button("Download CSV Template", data=template_df.to_csv(index=False), file_name="pillar2_template.csv", mime="text/csv")\
\
st.markdown("---")\
uploaded = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])\
if uploaded:\
    try:\
        df_raw = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)\
        st.markdown("**Preview:**")\
        st.dataframe(df_raw.head(20), use_container_width=True)\
\
        targets = \{\
            "Entity":         ["entity", "name", "company"],\
            "Jurisdiction":   ["jurisdiction", "jur", "country"],\
            "Type":           ["type", "entity type"],\
            "Revenue":        ["revenue", "turnover", "gross premium"],\
            "PBT":            ["pbt", "profit before tax", "profit"],\
            "CoveredTaxes":   ["covered taxes", "tax", "income tax"],\
            "DeferredTaxAdj": ["deferred", "deferred tax"],\
            "Payroll":        ["payroll", "staff costs", "wages"],\
            "TangibleAssets": ["tangible", "ppe", "fixed assets"],\
        \}\
        col_map = \{\}\
        for target, aliases in targets.items():\
            for col in df_raw.columns:\
                if any(a in col.lower() for a in aliases):\
                    col_map[target] = col\
                    break\
\
        st.markdown("**Map columns:**")\
        final_map = \{\}\
        for target in targets:\
            detected = col_map.get(target, "")\
            options = ["(skip)"] + list(df_raw.columns)\
            idx = (list(df_raw.columns).index(detected) + 1) if detected in df_raw.columns else 0\
            chosen = st.selectbox(target, options, index=idx, key="map_" + target)\
            if chosen != "(skip)":\
                final_map[target] = chosen\
\
        if st.button("Import Data", type="primary"):\
            imported = pd.DataFrame()\
            for target, src in final_map.items():\
                imported[target] = df_raw[src]\
            for col, default in [("Active", True), ("Type", "Insurance"), ("DeferredTaxAdj", 0.0), ("Payroll", 0.0), ("TangibleAssets", 0.0)]:\
                if col not in imported.columns:\
                    imported[col] = default\
            for nc in ["Revenue", "PBT", "CoveredTaxes", "DeferredTaxAdj", "Payroll", "TangibleAssets"]:\
                if nc in imported.columns:\
                    imported[nc] = pd.to_numeric(imported[nc], errors="coerce").fillna(0.0)\
            st.session_state.entities = pd.concat([st.session_state.entities, imported], ignore_index=True)\
            st.success("Imported " + str(len(imported)) + " entities!")\
            st.rerun()\
    except Exception as e:\
        st.error("Error reading file: " + str(e))\
```\
\
# \
\
elif page == \'93AI Templates\'94:\
st.markdown(\'94## AI Template Generator\'94)\
st.markdown(\'93Generate professional Pillar II templates populated with live OUTsurance data.\'94)\
\
```\
TEMPLATES = [\
    "GloBE Information Return (GIR)",\
    "QDMTT Calculation Worksheet",\
    "IIR Allocation Memorandum",\
    "Transfer Pricing Impact Analysis",\
    "Insurance-Specific Deferred Tax Adjustment Workpaper",\
    "Substance-Based Income Exclusion (SBIE) Workpaper",\
    "Transitional Safe Harbour Assessment",\
    "Country-by-Country Report (CbCR) Reconciliation",\
    "Board Tax Governance Report",\
    "BEPS Action 13 Master File Summary",\
    "Permanent Establishment Risk Assessment",\
    "Annual Pillar II Compliance Checklist",\
]\
\
selected = st.selectbox("Select Template", TEMPLATES)\
generate = st.button("Generate Template", type="primary")\
\
st.markdown("**Quick select:**")\
cols = st.columns(3)\
for i, t in enumerate(TEMPLATES):\
    if cols[i % 3].button(t, key="tpl_" + str(i), use_container_width=True):\
        selected = t\
        generate = True\
\
if generate:\
    summary = get_summary()\
    entity_list = ", ".join([r["Entity"] + " (" + r["Jurisdiction"] + ", " + r["Type"] + ")" for _, r in st.session_state.entities[st.session_state.entities["Active"] == True].iterrows()])\
    tx_list = ", ".join([r["Description"] + " ZAR" + str(r["Amount"]) + "m (" + r["Type"] + ")" for _, r in st.session_state.transactions.iterrows()])\
\
    prompt = (\
        "You are a senior international tax expert specialising in OECD Pillar II GloBE rules and insurance sector tax.\\n\\n"\
        "Generate a professional, detailed \\"" + selected + "\\" for the OUTsurance Group, "\
        "a South African insurance holding company with operations in South Africa (HQ/UPE), Australia, and Ireland.\\n\\n"\
        "LIVE GROUP DATA:\\n"\
        "Entities: " + entity_list + "\\n\\n"\
        "GloBE results:\\n" + summary + "\\n\\n"\
        "Transactions: " + tx_list + "\\n\\n"\
        "REQUIREMENTS:\\n"\
        "1. Follow OECD GloBE Model Rules (2021) and Administrative Guidance (2023/2024)\\n"\
        "2. Address insurance-specific considerations: technical provisions, DAC, long-tail claims, equalisation reserves\\n"\
        "3. Reference: South Africa TLAB 2023, Australia Treasury Laws Amendment Act 2024, Ireland Finance Act 2024\\n"\
        "4. Include section headers, data tables, calculation methodology and GloBE rule cross-references\\n"\
        "5. Highlight Ireland 12.5% STR QDMTT exposure and calculate specific liability\\n"\
        "6. Include SBIE calculation with transitional rates\\n"\
        "7. Benchmark against KPMG, Deloitte, PwC and EY insurance sector guidance\\n"\
        "8. Flag transfer pricing interactions affecting GloBE income\\n"\
        "9. Include action steps and filing deadlines per jurisdiction\\n\\n"\
        "Format as a complete professional compliance document. Be specific and technical."\
    )\
\
    with st.spinner("Generating " + selected + "..."):\
        output = call_claude(prompt)\
\
    st.markdown("---")\
    st.markdown("### Generated: " + selected)\
    st.text_area("Output", value=output, height=500, label_visibility="collapsed")\
    st.download_button("Download as TXT", data=output, file_name=selected.replace(" ", "_") + ".txt", mime="text/plain")\
```\
\
# \
\
elif page == \'93Benchmarking\'94:\
st.markdown(\'94## Global Best Practice Benchmarking\'94)\
st.markdown(\'93Ask any Pillar II question specific to OUTsurance. Benchmarked against OECD guidance and Big Four best practice.\'94)\
\
```\
PRESETS = [\
    "How should OUTsurance Ireland handle the QDMTT vs IIR interaction for FY2024?",\
    "What are the insurance-specific deferred tax adjustments under GloBE Article 4.4?",\
    "Benchmark OUTsurance group ETR against global insurance peers such as Zurich and Munich Re",\
    "What transitional safe harbour elections should OUTsurance make for 2024 to 2026?",\
    "How do intragroup reinsurance flows between ZA and IE affect GloBE income allocation?",\
    "What documentation is required for the GloBE Information Return in South Africa?",\
    "Explain the UTPR rules and whether OUTsurance is exposed as a South African HQ",\
    "What are the Pillar II implications of OUTsurance deferred acquisition costs (DAC)?",\
]\
\
st.markdown("**Suggested questions:**")\
cols = st.columns(2)\
selected_preset = None\
for i, p in enumerate(PRESETS):\
    if cols[i % 2].button(p, key="preset_" + str(i), use_container_width=True):\
        selected_preset = p\
\
st.markdown("---")\
query = st.text_area("Or type your question:", value=selected_preset or "", height=80, placeholder="e.g. How does the insurance technical provision exclusion work under GloBE rules?")\
\
if st.button("Get AI Analysis", type="primary") and query:\
    summary = get_summary()\
    prompt = (\
        "You are a Pillar II GloBE expert advising the OUTsurance Group tax team.\\n"\
        "OUTsurance is a South African non-life insurance holding company (UPE in ZA) with subsidiaries in Australia and Ireland.\\n\\n"\
        "CURRENT GROUP POSITION:\\n" + summary + "\\n\\n"\
        "QUESTION: " + query + "\\n\\n"\
        "Please provide:\\n"\
        "1. A direct, specific answer\\n"\
        "2. Relevant OECD GloBE Model Rule article(s)\\n"\
        "3. Insurance-sector specific considerations\\n"\
        "4. How this applies to OUTsurance three-jurisdiction structure\\n"\
        "5. Benchmarking against KPMG/Deloitte/PwC/EY published guidance\\n"\
        "6. Practical action steps for the tax team\\n"\
        "7. Relevant filing deadlines or elections\\n\\n"\
        "Be specific and technical. Reference rule numbers."\
    )\
    with st.spinner("Analysing..."):\
        answer = call_claude(prompt)\
    st.markdown("---")\
    st.markdown("### AI Analysis")\
    st.markdown(answer)\
    st.download_button("Save Analysis", data=answer, file_name="pillar2_analysis.txt", mime="text/plain")\
\
st.markdown("---")\
st.markdown("### Jurisdiction Reference")\
c1, c2, c3 = st.columns(3)\
with c1:\
    with st.expander("South Africa", expanded=True):\
        st.markdown("- Legislation: TLAB 2023\\n- QDMTT: effective 1 Jan 2024\\n- STR: 27% - above 15%\\n- Filing: SARS GIR 12 months post year-end\\n- Role: UPE / IIR filing entity")\
with c2:\
    with st.expander("Australia", expanded=True):\
        st.markdown("- Legislation: Treasury Laws Amendment Act 2024\\n- STR: 30% - no top-up expected\\n- Filing: ATO CbCR + GIR required\\n- Safe harbour: transitional 2024-2026")\
with c3:\
    with st.expander("Ireland", expanded=True):\
        st.markdown("- Legislation: Finance Act 2024\\n- STR: 12.5% - QDMTT top-up to 15%\\n- PRIMARY RISK for OUTsurance\\n- Revenue guidance: December 2023\\n- Action: quantify and provision QDMTT")\
```}