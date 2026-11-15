package aegis.agent_access

default allow := false

# Permit research_agent to read the public report.
allow if {
    input.agent_id == "research_agent"
    input.action == "read_document"
    input.resource == "public_report.pdf"
}

# Permit non-empty document search queries.
allow if {
    input.agent_id == "research_agent"
    input.action == "search_documents"
    is_string(input.resource)
    input.resource != ""
}

allow if {
    input.agent_id == "supervised_research_agent"
    input.action == "send_email"
    input.resource == "email"
    is_string(input.destination)
    input.destination != ""
    is_string(input.content)
    input.content != ""
}
# Permit the explicitly registered trusted test document.
allow if {
    input.agent_id == "research_agent"
    input.action == "read_document"
    input.resource == "trusted_research_report.pdf"
}
