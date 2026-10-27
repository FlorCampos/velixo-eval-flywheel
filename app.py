import streamlit as st
from pydantic import BaseModel, Field
from openai import OpenAI

# 1. Page Configuration & Theme
st.set_page_config(
    page_title="Velixo Intelligence | Eval & Self-Healing Flywheel",
    page_icon="⚡",
    layout="wide"
)

# Custom Styling for an Executive SaaS Interface
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stCodeBlock { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# 2. Header & Title
st.title("⚡ Velixo Intelligence: Eval & Self-Healing Flywheel")
st.markdown(
    "A production-grade evaluation harness and automated self-healing loop prototype "
    "for natural language ERP queries (GIQL gateway)."
)

# 3. API Key & Zero-Friction Setup (Safe Local Fallback)
api_key = None
try:
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

with st.sidebar:
    st.header("⚙️ Configuration")
    if not api_key:
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        st.caption("Provide a key for local testing.")
    else:
        st.success("🔒 API Key loaded securely (Zero-Friction Mode)")
        
    st.divider()
    st.markdown("### 🎯 Purpose")
    st.caption(
        "Demonstrates how production failures in GIQL payload generation "
        "are captured, evaluated by an Offline Judge, healed automatically, "
        "and structured into training-ready Supervised Fine-Tuning (SFT) pairs."
    )

if not api_key:
    st.warning("👈 Please enter an OpenAI API Key in the sidebar or configure Streamlit Secrets to proceed.")
    st.stop()

# Initialize OpenAI Client
client = OpenAI(api_key=api_key)

# 4. Pydantic Schema for Structured Judge Evaluation
class JudgeEvaluation(BaseModel):
    syntax_valid: bool = Field(description="Is the generated GIQL/Velixo query payload syntax valid?")
    erp_mapping_accurate: bool = Field(description="Are account numbers, connections, and date filters mapped accurately?")
    overall_score: float = Field(description="Quality evaluation score from 0.0 to 1.0")
    critique: str = Field(description="Detailed explanation of what failed or why it passed")

# 5. User Input Interface
st.markdown("### 💬 Natural Language Financial Query (Press Run Pipeline button)")
col_input, col_btn = st.columns([5, 1])

with col_input:
    user_query = st.text_input(
        "Natural Language Prompt",
        value="Total sales by customer for calendar year 2019",
        label_visibility="collapsed"
    )

with col_btn:
    run_clicked = st.button("Run Pipeline 🚀", use_container_width=True)

# 6. Pipeline Execution
if run_clicked:
    if not user_query.strip():
        st.error("Please enter a valid query prompt.")
        st.stop()

    # 3-Column Clean Dashboard
    col1, col2, col3 = st.columns(3)

    # Step 1: Agent Payload Generation
    with col1:
        st.markdown("#### 1️⃣ Agent Generation")
        st.caption("Natural language translated into structured payload.")
        
        with st.spinner("Translating query..."):
            system_prompt = (
                "You are Velixo Intelligence. Translate natural language user prompts into a structured "
                "JSON query payload for ERP connections (GIQL gateway syntax). Output valid JSON."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                response_format={"type": "json_object"}
            )
            generated_payload = response.choices[0].message.content
            st.code(generated_payload, language="json")

    # Step 2: Offline Judge Evaluation
    with col2:
        st.markdown("#### 2️⃣ Offline Judge")
        st.caption("LLM-as-a-Judge validating output rules.")
        
        with st.spinner("Evaluating payload quality..."):
            judge_prompt = f"Evaluate this generated payload: '{generated_payload}' for the user prompt: '{user_query}'."
            judge_response = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a strict QA Judge for Velixo ERP gateway schemas. Evaluate syntax, filters, and ERP mappings precisely."},
                    {"role": "user", "content": judge_prompt}
                ],
                response_format=JudgeEvaluation
            )
            eval_result = judge_response.choices[0].message.parsed
            
            # High-Visibility Custom Score Card
            score_pct = int(eval_result.overall_score * 100)
            is_passed = eval_result.overall_score >= 0.8
            
            card_bg = "#d4edda" if is_passed else "#f8d7da"
            card_border = "#28a745" if is_passed else "#dc3545"
            text_color = "#155724" if is_passed else "#721c24"
            status_text = "✅ PASSED - OPTIMAL" if is_passed else "❌ FAILED - NEEDS HEALING"

            st.markdown(f"""
                <div style="background-color: {card_bg}; border: 2px solid {card_border}; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;">
                    <span style="font-size: 14px; font-weight: bold; color: {text_color}; text-transform: uppercase;">Quality Score</span>
                    <h1 style="font-size: 42px; margin: 5px 0; color: {text_color};">{score_pct}%</h1>
                    <span style="font-size: 13px; font-weight: bold; color: {text_color};">{status_text}</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.write(f"**Syntax Valid:** `{'✅ Yes' if eval_result.syntax_valid else '❌ No'}`")
            st.write(f"**ERP Mapping:** `{'✅ Correct' if eval_result.erp_mapping_accurate else '❌ Flawed'}`")
            st.info(f"**Judge Feedback:** {eval_result.critique}")

    # Step 3: Self-Healing Flywheel Capture
    with col3:
        st.markdown("#### 3️⃣ Flywheel Loop")
        st.caption("Hard negative capture & auto-repair.")
        
        if eval_result.overall_score < 0.85:
            st.warning("⚠️ Hard negative detected! Triggering self-healing loop...")
            
            with st.spinner("Healing trajectory with critic feedback..."):
                heal_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query},
                        {"role": "assistant", "content": generated_payload},
                        {"role": "user", "content": f"The offline judge rejected this output with feedback: {eval_result.critique}. Fix the JSON schema accordingly."}
                    ],
                    response_format={"type": "json_object"}
                )
                healed_payload = heal_response.choices[0].message.content
                
                st.success("✨ Healed Successfully (SFT Pair Ready):")
                st.code(healed_payload, language="json")
        else:
            st.success("🌟 High-quality interaction! Saved directly to Golden Dataset for regression testing.")
            st.markdown("No healing required. System operates at optimal quality.")