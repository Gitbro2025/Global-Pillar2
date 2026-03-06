import streamlit as st
import pandas as pd
import anthropic

st.set_page_config(page_title="Pillar II GloBE", page_icon="P2", layout="wide")

JUR_INFO = {
    "ZA": {"name": "South Africa", "role": "HQ / UPE", "std_rate": 27.0},
    "AU": {"name": "Australia", "role": "Subsidiary", "std_rate": 30.0},
    "IE": {"name": "Ireland", "role": "Subsidiary", "std_rate": 12.5},
}

def init_state():
    if "entities" not in st.session_state:
        st.session_state.entities = pd.DataFrame([
            {"Entity": "OUTsurance Holdings Ltd", "Jurisdiction": "ZA", "Type": "Insurance", "Revenue": 8500.0, "PBT": 2100.0, "CoveredTaxes": 567.0, "DeferredTaxAdj": 45.0, "Payroll": 320.0, "TangibleAssets": 1200.0, "Active": True},
            {"Entity": "OUTsurance Life Ltd", "Jurisdiction": "ZA", "Type": "Life Insurance", "Revenue": 3200.0, "PBT": 890.0, "CoveredTaxes": 240.0, "DeferredTaxAdj": 18.0, "Payroll": 85.0, "TangibleAssets": 340.0, "Active": True},
            {"Entity": "OUTsurance Australia Pty", "Jurisdiction": "AU", "Type": "Gen. Insurance", "Revenue": 1800.0, "PBT": 420.0, "CoveredTaxes": 126.0, "DeferredTaxAdj": 12.0, "Payroll": 55.0, "TangibleAssets": 180.0, "Active": True},
            {"Entity": "OUTsurance Ireland Ltd", "Jurisdiction": "IE", "Type": "Reinsurance", "Revenue": 950.0, "PBT": 280.0, "CoveredTaxes": 35.0, "DeferredTaxAdj": 8.0, "Payroll": 22.0, "TangibleAssets": 95.0, "Active": True},
        ])
    if "transactions" not in st.session_state:
        st.session_state.transactions = pd.DataFrame([
            {"Description": "Reinsurance premium ZA to IE", "From": "OUTsurance Holdings Ltd", "To": "OUTsurance Ireland Ltd", "Amount": 120.0, "Type": "Reinsurance Premium", "TP_Method": "TNMM", "ArmsLength": True},
            {"Description": "Management fee ZA to AU", "From": "OUTsurance Holdings Ltd", "To": "OUTsurance Australia Pty", "Amount": 45.0, "Type": "Management Fee", "TP_Method": "CUP", "ArmsLength": True},
            {"Description": "IT licence fee ZA to IE", "From": "OUTsurance Holdings Ltd", "To": "OUTsurance Ireland Ltd", "Amount": 30.0, "Type": "Royalty / IP", "TP_Method": "TNMM", "ArmsLength": False},
        ])
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

init_state()

def calc_globe():
    active = st.session_state.entities[st.session_state.entities["Active"] == True].copy()
    results = []
    for jur, grp in active.groupby("Jurisdiction"):
        globe_income = (grp["PBT"] - grp["DeferredTaxAdj"]).sum()
        adj_cov_tax = (grp["CoveredTaxes"] + grp["DeferredTaxAdj"]).sum()
        sbie = (0.05 * grp["Payroll"] + 0.05 * grp["TangibleAssets"]).sum()
        net_income = max(0, globe_income - sbie)
        etr = (adj_cov_tax / globe_income * 100) if globe_income > 0 else 0
        top_up_rate = max(0, 15 - etr)
        top_up_tax = (top_up_rate / 100) * net_income
        j = JUR_INFO.get(jur, {"name": jur, "role": "", "std_rate": 0})
        status = "Compliant" if etr >= 15 else ("Marginal" if top_up_rate < 1 else "EXPOSURE")
        results.append({
            "Jur": jur, "Name": j["name"], "Role": j["role"],
            "Entities": len(grp), "GloBE_Income": globe_income,
            "Adj_Cov_Tax": adj_cov_tax, "SBIE": sbie,
            "ETR": etr, "TopUp_Rate": top_up_rate,
            "TopUp_Tax": top_up_tax,
            "QDMTT": "Yes" if top_up_rate > 0 else "No",
            "Status": status,
        })
    return pd.DataFrame(results)

def call_claude(prompt):
    key = st.session_state.get("api_key", "")
    if not key:
        try:
            key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            return "No API key set. Add your Anthropic API key in the sidebar."
    try:
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return "API Error: " + str(e)

def get_summary():
    results = calc_globe()
    lines = []
    for _, r in results.iterrows():
        lines.append(r["Name"] + " (" + r["Jur"] + "): GloBE Income ZAR" + str(round(r["GloBE_Income"], 1)) + "m, ETR " + str(round(r["ETR"], 2)) + "%, Top-up Tax ZAR" + str(round(r["TopUp_Tax"], 1)) + "m")
    return "\n".join(lines)

with st.sidebar:
    st.markdown("## OUTsurance\n### Pillar II GloBE")
    st.markdown("---")
    st.markdown("#### Anthropic API Key")
    api_input = st.text_input("API Key", value=st.session_state.api_key, type="password", placeholder="sk-ant-...", label_visibility="collapsed")
    if api_input:
        st.session_state.api_key = api_input
        st.success("Key saved")
    st.markdown("---")
    page = st.radio("Go to", ["Dashboard", "Entities", "Transactions", "Upload Data", "AI Templates", "Benchmarking"], label_visibility="collapsed")
    st.markdown("---")
    r_side = calc_globe()
    ttu = r_side["TopUp_Tax"].sum() if not r_side.empty else 0
    st.metric("Est. Top-up Tax", "ZAR " + str(round(ttu, 1)) + "m")
    st.metric("Active Entities", len(st.session_state.entities[st.session_state.entities["Active"] == True]))

st.markdown("# OUTsurance - Pillar II GloBE Reporting")
st.markdown("OECD Global Minimum Tax | FY 2024 | South Africa - Australia - Ireland")
st.markdown("---")

if page == "Dashboard":
    results = calc_globe()
    if results.empty:
        st.warning("No active entities.")
    else:
        total_income = results["GloBE_Income"].sum()
        total_tax = results["Adj_Cov_Tax"].sum()
        total_topup = results["TopUp_Tax"].sum()
        group_etr = (total_tax / total_income * 100) if total_income > 0 else 0
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Group ETR", str(round(group_etr, 2)) + "%", "Above 15%" if group_etr >= 15 else "BELOW 15%", delta_color="normal" if group_etr >= 15 else "inverse")
        k2.metric("Est. Top-up Tax", "ZAR " + str(round(total_topup, 1)) + "m", delta_color="inverse" if total_topup > 0 else "normal")
        k3.metric("GloBE Income", "ZAR " + str(round(total_income, 1)) + "m")
        k4.metric("Active Entities", len(st.session_state.entities[st.session_state.entities["Active"] == True]))
        st.markdown("---")
        st.markdown("#### Jurisdiction GloBE Summary")
        disp = results.copy()
        disp["ETR (%)"] = disp["ETR"].map(lambda x: str(round(x, 2)) + "%")
        disp["TopUp (%)"] = disp["TopUp_Rate"].map(lambda x: str(round(x, 2)) + "%")
        disp["TopUp Tax"] = disp["TopUp_Tax"].map(lambda x: "ZAR " + str(round(x, 1)) + "m")
        st.dataframe(disp[["Name", "Role", "Entities", "GloBE_Income", "Adj_Cov_Tax", "SBIE", "ETR (%)", "TopUp (%)", "TopUp Tax", "QDMTT", "Status"]], use_container_width=True, hide_index=True)
        st.markdown("---")
        st.markdown("#### Safe Harbour Assessment")
        cols = st.columns(len(results))
        for i, (_, r) in enumerate(results.iterrows()):
            with cols[i]:
                st.markdown("**" + r["Name"] + "**")
                if r["ETR"] >= 15:
                    st.success("ETR OK: " + str(round(r["ETR"], 2)) + "%")
                else:
                    st.error("ETR LOW: " + str(round(r["ETR"], 2)) + "%")
                st.info("SBIE: ZAR " + str(round(r["SBIE"], 1)) + "m excluded")
                if r["QDMTT"] == "Yes":
                    st.error("QDMTT: ZAR " + str(round(r["TopUp_Tax"], 1)) + "m due")
                else:
                    st.success("No top-up required")
        st.markdown("---")
        st.markdown("#### Entity ETR")
        ae = st.session_state.entities[st.session_state.entities["Active"] == True].copy()
        ae["ETR %"] = (ae["CoveredTaxes"] / ae["PBT"].replace(0, 1)) * 100
        st.bar_chart(ae.set_index("Entity")[["ETR %"]])

elif page == "Entities":
    st.markdown("## Entity Management")
    tab1, tab2 = st.tabs(["View / Edit", "Add New"])
    with tab1:
        edited = st.data_editor(
            st.session_state.entities,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Jurisdiction": st.column_config.SelectboxColumn("Jurisdiction", options=["ZA", "AU", "IE"]),
                "Type": st.column_config.SelectboxColumn("Type", options=["Insurance", "Life Insurance", "Gen. Insurance", "Reinsurance", "Holding", "Other"]),
                "Revenue": st.column_config.NumberColumn("Revenue (ZARm)", format="%.1f"),
                "PBT": st.column_config.NumberColumn("Profit Before Tax", format="%.1f"),
                "CoveredTaxes": st.column_config.NumberColumn("Covered Taxes", format="%.1f"),
                "DeferredTaxAdj": st.column_config.NumberColumn("Deferred Tax Adj", format="%.1f"),
                "Payroll": st.column_config.NumberColumn("Payroll", format="%.1f"),
                "TangibleAssets": st.column_config.NumberColumn("Tangible Assets", format="%.1f"),
                "Active": st.column_config.CheckboxColumn("In Scope"),
            },
            hide_index=True
        )
        if st.button("Save Changes", type="primary"):
            st.session_state.entities = edited
            st.success("Saved!")
            st.rerun()
    with tab2:
        c1, c2, c3 = st.columns(3)
        with c1:
            n_name = st.text_input("Entity Name")
            n_jur = st.selectbox("Jurisdiction", ["ZA", "AU", "IE"])
            n_type = st.selectbox("Type", ["Insurance", "Life Insurance", "Gen. Insurance", "Reinsurance", "Holding", "Other"])
        with c2:
            n_rev = st.number_input("Revenue (ZARm)", value=0.0)
            n_pbt = st.number_input("Profit Before Tax", value=0.0)
            n_tax = st.number_input("Covered Taxes", value=0.0)
        with c3:
            n_dtx = st.number_input("Deferred Tax Adj", value=0.0)
            n_pay = st.number_input("Payroll", value=0.0)
            n_tan = st.number_input("Tangible Assets", value=0.0)
        if st.button("Add Entity", type="primary"):
            if n_name:
                new_row = pd.DataFrame([{"Entity": n_name, "Jurisdiction": n_jur, "Type": n_type, "Revenue": n_rev, "PBT": n_pbt, "CoveredTaxes": n_tax, "DeferredTaxAdj": n_dtx, "Payroll": n_pay, "TangibleAssets": n_tan, "Active": True}])
                st.session_state.entities = pd.concat([st.session_state.entities, new_row], ignore_index=True)
                st.success("Added " + n_name)
                st.rerun()

elif page == "Transactions":
    st.markdown("## Intercompany Transaction Register")
    tab1, tab2 = st.tabs(["Register", "Add New"])
    entity_names = list(st.session_state.entities["Entity"])
    with tab1:
        edited_tx = st.data_editor(
            st.session_state.transactions,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "From": st.column_config.SelectboxColumn("From", options=entity_names),
                "To": st.column_config.SelectboxColumn("To", options=entity_names),
                "Type": st.column_config.SelectboxColumn("Type", options=["Reinsurance Premium", "Ceding Commission", "Management Fee", "Royalty / IP", "Loan Interest", "Capital Contribution", "Dividend", "Claims Reimbursement"]),
                "TP_Method": st.column_config.SelectboxColumn("TP Method", options=["CUP", "TNMM", "CPS", "PSM", "CPM"]),
                "Amount": st.column_config.NumberColumn("Amount (ZARm)", format="%.1f"),
                "ArmsLength": st.column_config.CheckboxColumn("Arms Length"),
            },
            hide_index=True
        )
        if st.button("Save Transactions", type="primary"):
            st.session_state.transactions = edited_tx
            st.success("Saved!")
        flagged = st.session_state.transactions[st.session_state.transactions["ArmsLength"] == False]
        if len(flagged) > 0:
            st.warning(str(len(flagged)) + " transaction(s) flagged for review.")
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            tx_desc = st.text_input("Description")
            tx_from = st.selectbox("From", entity_names)
            tx_to = st.selectbox("To", entity_names, index=min(3, len(entity_names) - 1))
            tx_amt = st.number_input("Amount (ZARm)", value=0.0)
        with c2:
            tx_type = st.selectbox("Type", ["Reinsurance Premium", "Ceding Commission", "Management Fee", "Royalty / IP", "Loan Interest", "Capital Contribution", "Dividend", "Claims Reimbursement"])
            tx_tp = st.selectbox("TP Method", ["CUP", "TNMM", "CPS", "PSM", "CPM"])
            tx_arm = st.checkbox("Arms Length", value=True)
        if st.button("Add Transaction", type="primary"):
            new_tx = pd.DataFrame([{"Description": tx_desc, "From": tx_from, "To": tx_to, "Amount": tx_amt, "Type": tx_type, "TP_Method": tx_tp, "ArmsLength": tx_arm}])
            st.session_state.transactions = pd.concat([st.session_state.transactions, new_tx], ignore_index=True)
            st.success("Added!")
            st.rerun()

elif page == "Upload Data":
    st.markdown("## Upload and Auto-Populate")
    st.markdown("Upload trial balance or statutory accounts CSV/Excel to populate entity fields.")
    template_df = pd.DataFrame({"Entity": ["Example Co"], "Jurisdiction": ["ZA"], "Type": ["Insurance"], "Revenue": [0.0], "PBT": [0.0], "CoveredTaxes": [0.0], "DeferredTaxAdj": [0.0], "Payroll": [0.0], "TangibleAssets": [0.0]})
    st.download_button("Download CSV Template", data=template_df.to_csv(index=False), file_name="pillar2_template.csv", mime="text/csv")
    st.markdown("---")
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    if uploaded:
        try:
            df_raw = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            st.dataframe(df_raw.head(20), use_container_width=True)
            targets = {
                "Entity": ["entity", "name", "company"],
                "Jurisdiction": ["jurisdiction", "jur", "country"],
                "Type": ["type", "entity type"],
                "Revenue": ["revenue", "turnover", "gross premium"],
                "PBT": ["pbt", "profit before tax", "profit"],
                "CoveredTaxes": ["covered taxes", "tax", "income tax"],
                "DeferredTaxAdj": ["deferred", "deferred tax"],
                "Payroll": ["payroll", "staff costs", "wages"],
                "TangibleAssets": ["tangible", "ppe", "fixed assets"],
            }
            col_map = {}
            for target, aliases in targets.items():
                for col in df_raw.columns:
                    if any(a in col.lower() for a in aliases):
                        col_map[target] = col
                        break
            final_map = {}
            for target in targets:
                detected = col_map.get(target, "")
                options = ["(skip)"] + list(df_raw.columns)
                idx = (list(df_raw.columns).index(detected) + 1) if detected in df_raw.columns else 0
                chosen = st.selectbox(target, options, index=idx, key="map_" + target)
                if chosen != "(skip)":
                    final_map[target] = chosen
            if st.button("Import Data", type="primary"):
                imported = pd.DataFrame()
                for target, src in final_map.items():
                    imported[target] = df_raw[src]
                for col, default in [("Active", True), ("Type", "Insurance"), ("DeferredTaxAdj", 0.0), ("Payroll", 0.0), ("TangibleAssets", 0.0)]:
                    if col not in imported.columns:
                        imported[col] = default
                for nc in ["Revenue", "PBT", "CoveredTaxes", "DeferredTaxAdj", "Payroll", "TangibleAssets"]:
                    if nc in imported.columns:
                        imported[nc] = pd.to_numeric(imported[nc], errors="coerce").fillna(0.0)
                st.session_state.entities = pd.concat([st.session_state.entities, imported], ignore_index=True)
                st.success("Imported " + str(len(imported)) + " entities!")
                st.rerun()
        except Exception as e:
            st.error("Error: " + str(e))

elif page == "AI Templates":
    st.markdown("## AI Template Generator")
    TEMPLATES = ["GloBE Information Return (GIR)", "QDMTT Calculation Worksheet", "IIR Allocation Memorandum", "Transfer Pricing Impact Analysis", "Insurance-Specific Deferred Tax Adjustment", "SBIE Workpaper", "Transitional Safe Harbour Assessment", "CbCR Reconciliation", "Board Tax Governance Report", "BEPS Action 13 Master File Summary"]
    selected = st.selectbox("Select Template", TEMPLATES)
    generate = st.button("Generate Template", type="primary")
    st.markdown("Quick select:")
    cols = st.columns(3)
    for i, t in enumerate(TEMPLATES):
        if cols[i % 3].button(t, key="tpl_" + str(i), use_container_width=True):
            selected = t
            generate = True
    if generate:
        summary = get_summary()
        entity_list = ", ".join([r["Entity"] + " (" + r["Jurisdiction"] + ")" for _, r in st.session_state.entities[st.session_state.entities["Active"] == True].iterrows()])
        tx_list = ", ".join([r["Description"] + " ZAR" + str(r["Amount"]) + "m" for _, r in st.session_state.transactions.iterrows()])
        prompt = (
            "You are a senior international tax expert in OECD Pillar II GloBE rules and insurance tax.\n\n"
            "Generate a professional " + selected + " for OUTsurance Group, a South African insurance holding company with operations in South Africa (HQ/UPE), Australia, and Ireland.\n\n"
            "LIVE DATA:\nEntities: " + entity_list + "\n\nGloBE results:\n" + summary + "\n\nTransactions: " + tx_list + "\n\n"
            "Requirements:\n"
            "1. Follow OECD GloBE Model Rules 2021 and Administrative Guidance 2023/2024\n"
            "2. Address insurance-specific items: technical provisions, DAC, long-tail claims, equalisation reserves\n"
            "3. Reference South Africa TLAB 2023, Australia Treasury Laws Amendment Act 2024, Ireland Finance Act 2024\n"
            "4. Include section headers, data tables, calculation methodology and GloBE rule references\n"
            "5. Highlight Ireland 12.5% STR QDMTT exposure\n"
            "6. Include SBIE calculation with transitional rates\n"
            "7. Benchmark against KPMG, Deloitte, PwC and EY guidance\n"
            "8. Include action steps and filing deadlines\n\n"
            "Format as a complete professional compliance document."
        )
        with st.spinner("Generating " + selected + "..."):
            output = call_claude(prompt)
        st.markdown("---")
        st.markdown("### " + selected)
        st.text_area("Output", value=output, height=500, label_visibility="collapsed")
        st.download_button("Download as TXT", data=output, file_name=selected.replace(" ", "_") + ".txt", mime="text/plain")

elif page == "Benchmarking":
    st.markdown("## Global Best Practice Benchmarking")
    PRESETS = [
        "How should OUTsurance Ireland handle the QDMTT vs IIR interaction for FY2024?",
        "What are the insurance-specific deferred tax adjustments under GloBE Article 4.4?",
        "Benchmark OUTsurance ETR against global insurance peers such as Zurich and Munich Re",
        "What transitional safe harbour elections should OUTsurance make for 2024 to 2026?",
        "How do intragroup reinsurance flows between ZA and IE affect GloBE income allocation?",
        "What documentation is required for the GloBE Information Return in South Africa?",
        "Explain the UTPR rules and whether OUTsurance is exposed as South African HQ",
        "What are the Pillar II implications of OUTsurance deferred acquisition costs?",
    ]
    st.markdown("Suggested questions:")
    cols = st.columns(2)
    selected_preset = None
    for i, p in enumerate(PRESETS):
        if cols[i % 2].button(p, key="preset_" + str(i), use_container_width=True):
            selected_preset = p
    st.markdown("---")
    query = st.text_area("Or type your question:", value=selected_preset or "", height=80)
    if st.button("Get AI Analysis", type="primary") and query:
        summary = get_summary()
        prompt = (
            "You are a Pillar II GloBE expert advising OUTsurance Group tax team.\n"
            "OUTsurance is a South African non-life insurance holding company with subsidiaries in Australia and Ireland.\n\n"
            "GROUP POSITION:\n" + summary + "\n\n"
            "QUESTION: " + query + "\n\n"
            "Provide:\n1. Direct specific answer\n2. Relevant GloBE Model Rule articles\n"
            "3. Insurance-sector considerations\n4. Application to OUTsurance three-jurisdiction structure\n"
            "5. Benchmarking against Big Four guidance\n6. Practical action steps\n7. Filing deadlines\n\n"
            "Be specific and technical."
        )
        with st.spinner("Analysing..."):
            answer = call_claude(prompt)
        st.markdown("---")
        st.markdown("### AI Analysis")
        st.markdown(answer)
        st.download_button("Save Analysis", data=answer, file_name="pillar2_analysis.txt", mime="text/plain")
    st.markdown("---")
    st.markdown("### Jurisdiction Reference")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.expander("South Africa", expanded=True):
            st.markdown("- Legislation: TLAB 2023\n- QDMTT: 1 Jan 2024\n- STR: 27%\n- Role: UPE / IIR filer\n- Filing: 12 months post year-end")
    with c2:
        with st.expander("Australia", expanded=True):
            st.markdown("- Legislation: Treasury Laws Amendment Act 2024\n- STR: 30%\n- No top-up expected\n- Safe harbour: 2024-2026")
    with c3:
        with st.expander("Ireland", expanded=True):
            st.markdown("- Legislation: Finance Act 2024\n- STR: 12.5%\n- QDMTT top-up to 15% required\n- PRIMARY RISK for OUTsurance")
