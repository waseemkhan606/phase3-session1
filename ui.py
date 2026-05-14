"""
Enterprise AI Support Platform — Session 1 UI
Streamlit frontend for the LangGraph support agent.
Run: streamlit run ui.py
"""

import streamlit as st
from support_agent import (
    run_ticket,
    stream_ticket,
    run_session_verification,
    build_initial_state,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Enterprise AI Support Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ─────────────────────────────────────────────────────
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_ticket" not in st.session_state:
    st.session_state.last_ticket = ""
if "sample_ticket" not in st.session_state:
    st.session_state.sample_ticket = ""
if "exec_steps" not in st.session_state:
    st.session_state.exec_steps = []


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("🏢 AI Support Platform")
    st.caption("Enterprise Multi-Agent System")

    st.divider()

    st.markdown("**Session Progress**")

    sessions = [
        ("1", "The Blueprint",   True),
        ("2", "The Hands",       False),
        ("3", "The Loop",        False),
        ("4", "The Memory",      False),
        ("5", "The Summarizer",  False),
        ("6", "The Shield",      False),
        ("7", "The Specialist",  False),
        ("8", "The Supervisor",  False),
        ("9", "The Swarm",       False),
        ("10", "The Writer",     False),
        ("11", "The Gatekeeper", False),
        ("12", "The Auditor",    False),
    ]

    for num, name, active in sessions:
        icon = "🟢" if active else "⚪"
        weight = "**" if active else ""
        st.markdown(f"{icon} {weight}Session {num}: {name}{weight}")

    st.divider()

    with st.expander("Session 1 Info"):
        st.markdown(
            "**What's built:**\n"
            "- Gemini classifier (4 categories)\n"
            "- Conditional router\n"
            "- 4 handler stubs\n"
            "- Streaming graph execution\n\n"
            "**Not built yet:**\n"
            "- CRM / KB tool calls (Session 2)\n"
            "- ReAct loop + memory (Sessions 3–5)\n"
            "- PII & injection security (Session 6)\n"
            "- Multi-agent orchestration (Sessions 8–9)\n"
            "- Human approval gate (Session 11)\n"
            "- Full audit trail (Session 12)"
        )


# ══════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════

st.title("🏢 Enterprise AI Support Platform")
st.caption("Session 1 — The Blueprint")

st.divider()

left_col, right_col = st.columns([3, 2])


# ── LEFT COLUMN: Ticket Input & Response ──────────────────────────────────────
with left_col:
    st.subheader("📨 Submit Support Ticket")

    # Sample ticket buttons
    sample_tickets = {
        "🔧 Technical": "The API is returning HTTP 500 on every POST request to /v2/users",
        "💳 Billing":   "My payment was deducted twice but my subscription is still inactive",
        "🚨 Fraud":     "I received an alert for a $847 transaction I did not authorize",
        "❓ General":   "How do I add a team member and set their permissions to read-only?",
    }

    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    button_cells = [row1_col1, row1_col2, row2_col1, row2_col2]
    for cell, (label, sample) in zip(button_cells, sample_tickets.items()):
        with cell:
            if st.button(label, use_container_width=True):
                st.session_state.sample_ticket = sample

    ticket_text = st.text_area(
        "Describe your issue",
        height=120,
        placeholder="Type your support ticket here, or click a sample above...",
        value=st.session_state.get("sample_ticket", ""),
        key="ticket_input",
    )

    submitted = st.button("🚀 Submit Ticket", type="primary", use_container_width=True)

    if submitted:
        if not ticket_text.strip():
            st.warning("Please enter a ticket before submitting.")
        else:
            # Collect streaming steps
            exec_steps = []
            status_placeholder = st.empty()

            with st.spinner("Analyzing your ticket..."):
                for node_name, snapshot in stream_ticket(ticket_text):
                    exec_steps.append((node_name, snapshot))
                    status_placeholder.markdown(f"⚙️ Running: `{node_name}`")

                # Full result for final state values
                result = run_ticket(ticket_text)

            status_placeholder.empty()

            # Persist to session state
            st.session_state.last_result = result
            st.session_state.last_ticket = ticket_text
            st.session_state.exec_steps = exec_steps

            # ── Result display ────────────────────────────────────────────────
            category = result.get("category", "general")

            category_config = {
                "technical": ("🔧", "Technical",  "blue"),
                "billing":   ("💳", "Billing",    "orange"),
                "fraud":     ("🚨", "Fraud",      "red"),
                "general":   ("❓", "General",    "grey"),
            }
            icon, label, color = category_config.get(
                category, ("❓", "General", "grey")
            )

            color_map = {
                "blue":   "#1E88E5",
                "orange": "#FB8C00",
                "red":    "#E53935",
                "grey":   "#757575",
            }
            badge_color = color_map[color]

            st.markdown(
                f"**Category Detected:** "
                f'<span style="background:{badge_color};color:white;'
                f'padding:3px 10px;border-radius:12px;font-size:0.85em;">'
                f"{icon} {label}</span>",
                unsafe_allow_html=True,
            )

            st.divider()

            st.markdown("**Response:**")
            st.info(result.get("final_response", ""))


# ── RIGHT COLUMN: Execution Inspector ─────────────────────────────────────────
with right_col:
    st.subheader("🔍 Execution Inspector")

    if st.session_state.last_result is None:
        st.info("Submit a ticket to see the execution trace here.")
    else:
        result = st.session_state.last_result
        exec_steps = st.session_state.exec_steps

        # Graph Execution expander
        with st.expander("Graph Execution", expanded=True):
            if exec_steps:
                for step_num, (node_name, snapshot) in enumerate(exec_steps, 1):
                    st.markdown(f"**Step {step_num}: `{node_name}`**")
                    if node_name == "classify_node":
                        raw_preview = result.get("raw_input", "")[:60]
                        category_val = snapshot.get("category", result.get("category", ""))
                        st.markdown(f"- Input: *{raw_preview}...*")
                        st.markdown(f"- Output: `category = '{category_val}'`")
                    else:
                        st.markdown("- Output: response generated")
                    if step_num < len(exec_steps):
                        st.markdown("---")
            else:
                st.caption("No steps recorded.")

        # State Inspector expander
        with st.expander("State Inspector", expanded=False):
            raw_input_preview = (result.get("raw_input") or "")[:50]
            table_rows = [
                ("raw_input",       f"{raw_input_preview}..."),
                ("category",        result.get("category", "")),
                ("is_safe",         str(result.get("is_safe", True))),
                ("pii_detected",    f"{result.get('pii_detected', False)} (Session 6)"),
                ("iteration_count", f"{result.get('iteration_count', 0)} (Session 3)"),
            ]

            header = "| Field | Value |\n|---|---|\n"
            rows = "\n".join(f"| `{f}` | {v} |" for f, v in table_rows)
            st.markdown(header + rows)
            st.caption("Grey fields activated in future sessions.")

        # Coming in future sessions
        with st.expander("Coming in Future Sessions", expanded=False):
            st.markdown(
                "- **Session 2:** Tool calls panel — which tools fired, what they returned\n"
                "- **Session 3:** Loop counter and circuit breaker status\n"
                "- **Session 4:** Conversation memory and thread selector\n"
                "- **Session 6:** PII detection — before/after sanitization view\n"
                "- **Session 9:** Parallel agent scratchpad\n"
                "- **Session 11:** Human approval gate (Approve / Deny / Edit buttons)\n"
                "- **Session 12:** Full audit timeline"
            )

        # ── SESSION 2: Tool Call Panel ───────────────────────────────────────
        # Will show: which tool was called, arguments passed, raw tool result
        # Activated when: agent_node and tool_node exist in the graph
        # ────────────────────────────────────────────────────────────────────

        # ── SESSION 3: ReAct Loop Panel ──────────────────────────────────────
        # Will show: iteration counter, circuit breaker threshold,
        #            each Thought→Action→Observation step
        # ────────────────────────────────────────────────────────────────────

        # ── SESSION 4: Memory Panel ──────────────────────────────────────────
        # Will show: thread selector dropdown, conversation history,
        #            "This conversation survived a process restart" indicator
        # ────────────────────────────────────────────────────────────────────

        # ── SESSION 6: Security Panel ────────────────────────────────────────
        # Will show: PII detection results, before/after sanitization,
        #            injection detection badge
        # ────────────────────────────────────────────────────────────────────

        # ── SESSION 9: Parallel Agents Panel ────────────────────────────────
        # Will show: which agents fired in parallel, scratchpad contents,
        #            each agent's finding in real time
        # ────────────────────────────────────────────────────────────────────

        # ── SESSION 11: Human Approval Gate ─────────────────────────────────
        # Will show: GitHub issue draft, Approve / Deny / Edit buttons,
        #            approval status and final issue URL
        # ────────────────────────────────────────────────────────────────────

        # ── SESSION 12: Audit Timeline ──────────────────────────────────────
        # Will show: full checkpoint history, time travel controls,
        #            human intervention markers
        # ────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════
# SESSION VERIFICATION TAB
# ══════════════════════════════════════════════════════════════════

st.divider()

with st.expander("🧪 Session Verification Test", expanded=False):
    st.markdown(
        "Run the automated verification test to confirm Session 1 is "
        "working correctly before moving to Session 2."
    )

    if st.button("▶️ Run Verification Test", use_container_width=True):
        with st.spinner("Running 5 verification checks..."):
            passed = run_session_verification()

        if passed:
            st.success("✅ All verification checks passed!")
            st.info("Session 2 is unblocked. The foundation is solid.")
        else:
            st.error("❌ Verification failed. Fix issues before Session 2.")
            st.warning("Check the terminal for detailed failure output.")

        st.markdown(
            """
**What was verified:**
- Technical ticket → classified as technical ✓
- Billing ticket → classified as billing ✓
- Fraud ticket → classified as fraud ✓
- General ticket → classified as general ✓
- Gibberish input → handled gracefully (no crash) ✓
- All 5 returned non-empty responses ✓
            """
        )


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Enterprise AI Support Platform | Session 1 of 12 | The Blueprint")