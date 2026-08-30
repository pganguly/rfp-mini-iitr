import json
from pathlib import Path
import pandas as pd
import streamlit as st

from app.config import DB_PATH, DEFAULT_MODEL, OPENROUTER_BASE_URL
from app.db import init_db, get_active_criteria, validate_active_weights
from app.orchestrator import evaluate_batch

st.set_page_config(page_title="Agentic RFP Evaluation", layout="wide")
init_db(DB_PATH)

st.title("Agentic RFP Evaluation & Supplier Ranking")
st.caption("LangGraph orchestrates the workflow. OpenRouter supplies the LLM; deterministic Python performs validation, scoring, peer comparison, tie-breaks, and final ranking.")

with st.sidebar:
    st.header("Evaluation mode")
    mode_label = st.radio("Mode", ["Offline demo", "OpenRouter LLM"], index=0)
    mode = "mock" if mode_label == "Offline demo" else "llm"
    model = st.text_input("Model", value=DEFAULT_MODEL)
    api_key = st.text_input("OpenRouter API key", type="password", help="Optional if OPENROUTER_API_KEY is configured in the environment.")
    base_url = st.text_input("OpenRouter base URL", value=OPENROUTER_BASE_URL, disabled=True)

tabs = st.tabs(["Criteria", "Supplier input", "Leaderboard / Scorecards"])

with tabs[0]:
    st.subheader("Active evaluation criteria")
    criteria = get_active_criteria(DB_PATH)
    ok, total = validate_active_weights(criteria)
    st.dataframe(pd.DataFrame(criteria), use_container_width=True)
    if ok:
        st.success(f"Active weights total {total:.0f}%.")
    else:
        st.error(f"Active weights total {total:.2f}%; they must total 100%.")

with tabs[1]:
    st.subheader("Supplier input")
    uploaded = st.file_uploader("Upload supplier RFP PDFs", type=["pdf"], accept_multiple_files=True)

    suppliers = []
    if uploaded:
        for i, f in enumerate(uploaded):
            st.markdown(f"**{f.name}**")
            c1, c2, c3 = st.columns(3)
            with c1:
                name = st.text_input("Supplier name", key=f"name_{i}", value=Path(f.name).stem.replace("_"," "))
            with c2:
                d = st.date_input("Submission date", key=f"date_{i}")
            with c3:
                exp = st.number_input("Historical experience rating", min_value=0.0, max_value=10.0, value=5.0, step=0.5, key=f"exp_{i}")
            suppliers.append({
                "supplier_name": name.strip(),
                "submission_date": d.isoformat(),
                "experience_rating": exp,
                "pdf_bytes": f.getvalue(),
            })

    if st.button("Evaluate batch", type="primary", disabled=not bool(uploaded)):
        bad = [s for s in suppliers if not s["supplier_name"]]
        if bad:
            st.error("Every supplier must have a name.")
        else:
            try:
                with st.spinner("Evaluating suppliers..."):
                    run_id, criteria, ranked = evaluate_batch(
                        suppliers, DB_PATH,
                        mode=mode,
                        model=model or None,
                        api_key=api_key or None,
                        base_url=base_url or None,
                        pdf_backend=pdf_backend,
                    )
                st.session_state["run_id"] = run_id
                st.session_state["criteria"] = criteria
                st.session_state["ranked"] = ranked
                st.success(f"Evaluation completed. RFP_RUN_ID: {run_id}")
            except Exception as e:
                st.exception(e)

with tabs[2]:
    ranked = st.session_state.get("ranked")
    run_id = st.session_state.get("run_id")
    if not ranked:
        st.info("Run an evaluation batch first.")
    else:
        st.subheader("Leaderboard")
        leaderboard = pd.DataFrame([{
            "Rank": r["final_rank"],
            "Supplier": r["supplier_name"],
            "Absolute Score": r["absolute_score"],
            "PPI": r["ppi"],
            "Submission Date": r["submission_date"],
            "Experience Rating": r["experience_rating"],
        } for r in ranked])
        st.dataframe(leaderboard, use_container_width=True, hide_index=True)

        st.subheader("Detailed scorecards")
        for r in ranked:
            with st.expander(f'#{r["final_rank"]} {r["supplier_name"]} — PPI {r["ppi"]:.2f}'):
                st.write(r["overall_summary"])
                if r["warnings"]:
                    st.warning("\n".join(r["warnings"]))
                if r["risks"]:
                    st.write("**Risks:**", r["risks"])
                df = pd.DataFrame(r["criteria"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(r["tie_break_explanation"])

        export_obj = {"rfp_run_id": run_id, "results": ranked}
        export_json = json.dumps(export_obj, indent=2, ensure_ascii=False)
        st.download_button(
            "Download complete result as JSON",
            data=export_json,
            file_name=f"{run_id}.json",
            mime="application/json",
        )
