
"""AEGIS Security Dashboard - Streamlit frontend."""

import httpx
import streamlit as st
from collections import Counter
from datetime import datetime


st.set_page_config(
    page_title="AEGIS Security Console",
    page_icon="🛡️",
    layout="wide",
)

DEFAULT_API = "http://127.0.0.1:8000"

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛡️ AEGIS Security Console")
st.caption("AI Agent Security & Authorization Gateway")

with st.sidebar:
    st.header("Configuration")
    api_url = st.text_input("Backend API URL", DEFAULT_API).rstrip("/")
    refresh = st.button("🔄 Refresh dashboard", use_container_width=True)
    st.divider()
    st.caption("AEGIS | Security Monitoring")
    st.caption("FastAPI + Streamlit")


def api_get(path: str, params: dict | None = None):
    """Fetch data from the AEGIS API."""

    try:
        response = httpx.get(
            f"{api_url}{path}",
            params=params,
            timeout=5.0,
        )
        response.raise_for_status()
        return response.json(), None
    except httpx.HTTPError as exc:
        return None, str(exc)

def api_post(path: str, payload: dict, token: str):
    """Submit an authenticated approval decision."""

    try:
        response = httpx.post(
            f"{api_url}{path}",
            json=payload,
            headers={
                "X-AEGIS-Approver-Token": token,
            },
            timeout=5.0,
        )
        response.raise_for_status()
        return response.json(), None
    except httpx.HTTPError as exc:
        return None, str(exc)


health, health_error = api_get("/health")
audit_data, audit_error = api_get("/audit", {"limit": 500})


if health_error:
    st.error(f"Backend connection failed: {health_error}")
    st.info("Start FastAPI using: uvicorn backend.app:app --reload")
    st.stop()

if audit_error:
    st.error(f"Could not retrieve audit records: {audit_error}")
    st.stop()

events = audit_data.get("events", [])

# Dashboard metrics
decisions = Counter(event["decision"] for event in events)
total_events = len(events)
allowed = decisions.get("ALLOW", 0)
denied = decisions.get("DENY", 0)
pending = decisions.get("REQUIRES_APPROVAL", 0)
errors = decisions.get("ERROR", 0)

st.success("Backend connected successfully")

st.subheader("Security Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Events", total_events)
col2.metric("Allowed", allowed)
col3.metric("Denied", denied)
col4.metric("Pending Approval", pending)
col5.metric("Errors", errors)

st.divider()

# Approval Management Console
st.subheader("Approval Management Console")
st.caption("Review, authorize, and inspect AI agent approval requests.")

reviewer_id = st.text_input(
    "Reviewer ID",
    placeholder="Enter reviewer identity",
    key="reviewer_id",
)

reviewer_token = st.text_input(
    "Reviewer Authentication Token",
    type="password",
    placeholder="Enter your reviewer secret",
    key="reviewer_token",
)

approval_statuses = ["PENDING", "APPROVED", "REJECTED", "EXPIRED"]

selected_status = st.selectbox(
    "Filter approval requests",
    ["ALL"] + approval_statuses,
    index=1,
    key="approval_status_filter",
)

# Fetch approval requests according to the selected status.
if selected_status == "ALL":
    all_approvals = []
    approval_errors = []

    for status in approval_statuses:
        data, error = api_get("/approvals", {"status": status})

        if error:
            approval_errors.append(f"{status}: {error}")
        elif data is not None:
            all_approvals.extend(data.get("approvals", []))

    approval_data = {"approvals": all_approvals}
    approval_error = "; ".join(approval_errors) if approval_errors else None

else:
    approval_data, approval_error = api_get(
        "/approvals",
        {"status": selected_status},
    )

if approval_error:
    st.error(f"Could not retrieve approvals: {approval_error}")

elif approval_data is not None:
    approvals = approval_data.get("approvals", [])

    approvals.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    pending_count = sum(
        item.get("status") == "PENDING" and not item.get("is_expired")
        for item in approvals
    )

    approved_count = sum(
        item.get("status") == "APPROVED" for item in approvals
    )

    rejected_count = sum(
        item.get("status") == "REJECTED" for item in approvals
    )

    expired_count = sum(
        item.get("status") == "EXPIRED" for item in approvals
    )

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Pending", pending_count)
    metric2.metric("Approved", approved_count)
    metric3.metric("Rejected", rejected_count)
    metric4.metric("Expired", expired_count)

    st.caption(f"Showing {len(approvals)} request(s).")

    if not approvals:
        st.info("No approval requests found for this filter.")

    for item in approvals:
        status = item.get("status", "UNKNOWN")

        with st.container(border=True):
            st.markdown(
                f"**Agent:** `{item['agent_id']}`"
            )

            st.write(f"**Approval ID:** `{item['approval_id']}`")
            st.write(f"**Action:** `{item['action']}`")
            st.write(f"**Resource:** `{item['resource']}`")
            st.write(f"**Status:** `{status}`")
            st.write(f"**Created:** {item['created_at']}")
            st.write(f"**Expires:** {item['expires_at']}")

            if status != "PENDING":
                continue

            if item.get("is_expired"):
                st.warning("This request has expired.")
                continue

            approve_col, reject_col = st.columns(2)

            if approve_col.button(
                "Approve",
                key=f"approve_{item['approval_id']}",
                use_container_width=True,
                disabled=not reviewer_id.strip() or not reviewer_token,
            ):
                result, error = api_post(
                    f"/approvals/{item['approval_id']}/review",
                    {
                        "decision": "APPROVE",
                        "reviewer_id": reviewer_id.strip(),
                    },
                    reviewer_token,
                )

                if error:
                    st.error(f"Approval failed: {error}")
                else:
                    st.success("Approval recorded successfully.")
                    st.rerun()

            if reject_col.button(
                "Reject",
                key=f"reject_{item['approval_id']}",
                use_container_width=True,
                disabled=not reviewer_id.strip() or not reviewer_token,
            ):
                result, error = api_post(
                    f"/approvals/{item['approval_id']}/review",
                    {
                        "decision": "REJECT",
                        "reviewer_id": reviewer_id.strip(),
                    },
                    reviewer_token,
                )

                if error:
                    st.error(f"Rejection failed: {error}")
                else:
                    st.success("Request rejected successfully.")
                    st.rerun()


# Overview charts
left, right = st.columns(2)

with left:
    st.subheader("Decision Distribution")

    if decisions:
        st.bar_chart(
            {
                "Events": {
                    decision: count
                    for decision, count in decisions.items()
                }
            }
        )
    else:
        st.info("No audit events recorded yet.")

with right:
    st.subheader("Agent Activity")

    agent_counts = Counter(
        event["agent_id"] for event in events
    )

    if agent_counts:
        st.bar_chart(
            {
                "Actions": dict(agent_counts)
            }
        )
    else:
        st.info("No agent activity available.")

st.divider()

# Event explorer
st.subheader("🔍 Security Event Explorer")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    decision_options = ["ALL"] + sorted(
        {event["decision"] for event in events}
    )
    selected_decision = st.selectbox(
        "Filter by decision",
        decision_options,
    )

with filter_col2:
    agent_options = ["ALL"] + sorted(
        {event["agent_id"] for event in events}
    )
    selected_agent = st.selectbox(
        "Filter by agent",
        agent_options,
    )

filtered_events = events

if selected_decision != "ALL":
    filtered_events = [
        event for event in filtered_events
        if event["decision"] == selected_decision
    ]

if selected_agent != "ALL":
    filtered_events = [
        event for event in filtered_events
        if event["agent_id"] == selected_agent
    ]

display_events = []

for event in filtered_events:
    display_events.append(
        {
            "ID": event["id"],
            "Timestamp": event["timestamp"],
            "Agent": event["agent_id"],
            "Action": event["action"],
            "Resource": event["resource"],
            "Decision": event["decision"],
            "Reason": event["reason"],
            "Trace ID": event.get("trace_id"),
            "Attack ID": event.get("attack_id"),
            "Approval ID": event.get("approval_id"),
            "Tool Invoked": event["tool_invoked"],
            "Tool Succeeded": event["tool_succeeded"],
        }
    )

if display_events:
    st.dataframe(
        display_events,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No events match the selected filters.")

st.divider()

# Trace explorer
st.subheader("🧭 Attack / Execution Trace Explorer")

trace_ids = sorted(
    {
        event["trace_id"]
        for event in events
        if event.get("trace_id")
    },
    reverse=True,
)

if trace_ids:
    selected_trace = st.selectbox(
        "Select an execution trace",
        trace_ids,
    )

    if st.button("Inspect selected trace"):
        trace_data, trace_error = api_get(
            f"/audit/traces/{selected_trace}"
        )

        if trace_error:
            st.error(f"Trace retrieval failed: {trace_error}")
        else:
            st.success(
                f"Trace loaded: {trace_data['event_count']} event(s)"
            )
            st.json(trace_data)

else:
    st.info("No execution traces available yet.")

st.divider()

# Attack correlation explorer
st.divider()
st.subheader("Attack Correlation Explorer")

attack_ids = sorted({
    event.get("attack_id")
    for event in events
    if event.get("attack_id")
})

if attack_ids:
    selected_attack = st.selectbox(
        "Select attack ID",
        attack_ids,
        key="attack_correlation_selector",
    )

    attack_data, attack_error = api_get(
        f"/audit/attacks/{selected_attack}"
    )

    if attack_error:
        st.error(f"Could not retrieve attack trace: {attack_error}")
    else:
        attack_events = attack_data.get("events", [])

        st.metric(
            "Correlated Security Events",
            attack_data.get("event_count", len(attack_events)),
        )

        st.dataframe(
            [
                {
                    "Timestamp": event["timestamp"],
                    "Agent": event["agent_id"],
                    "Action": event["action"],
                    "Resource": event["resource"],
                    "Decision": event["decision"],
                    "Reason": event["reason"],
                    "Trace ID": event["trace_id"],
                    "Tool Invoked": event["tool_invoked"],
                    "Tool Succeeded": event["tool_succeeded"],
                }
                for event in attack_events
            ],
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info(
        "No correlated attack events yet. "
        "Run the prompt-injection simulation to generate one."
    )

# Latest activity
st.subheader("Latest Security Activity")

for event in events[:5]:
    decision = event["decision"]

    if decision == "ALLOW":
        icon = "🟢"
    elif decision == "DENY":
        icon = "🔴"
    elif decision == "REQUIRES_APPROVAL":
        icon = "🟡"
    else:
        icon = "⚠️"

    timestamp = event["timestamp"]

    st.markdown(
        f"**{icon} {decision}** — "
        f"`{event['agent_id']}` → "
        f"`{event['action']}` on `{event['resource']}`"
    )
    st.caption(f"{timestamp} | {event['reason']}")


# Execution timeline
st.divider()
st.subheader("🛡️ Execution Security Timeline")

if trace_ids:
    timeline_trace = st.selectbox(
        "Choose execution to investigate",
        trace_ids,
        key="timeline_trace",
    )

    timeline_events = [
        event for event in events
        if event.get("trace_id") == timeline_trace
    ]

    timeline_events.sort(
        key=lambda event: event["timestamp"]
    )

    for index, event in enumerate(timeline_events, start=1):
        decision = event["decision"]

        if decision == "ALLOW":
            status_icon = "🟢"
        elif decision == "DENY":
            status_icon = "🔴"
        elif decision == "REQUIRES_APPROVAL":
            status_icon = "🟡"
        else:
            status_icon = "⚠️"

        st.markdown(
            f"### {status_icon} Step {index}: {decision}"
        )

        st.write(
            f"**Agent:** `{event['agent_id']}`"
        )
        st.write(
            f"**Action:** `{event['action']}`"
        )
        st.write(
            f"**Resource:** `{event['resource']}`"
        )
        st.write(
            f"**Reason:** {event['reason']}"
        )

        tool_col1, tool_col2 = st.columns(2)

        tool_col1.metric(
            "Tool invoked",
            "Yes" if event["tool_invoked"] else "No",
        )

        tool_col2.metric(
            "Tool succeeded",
            "Yes" if event["tool_succeeded"] else "No",
        )

        st.caption(event["timestamp"])
        st.divider()

else:
    st.info("No execution traces available.")
