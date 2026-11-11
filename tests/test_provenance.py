from backend.agent.graph import run_agent


def test_public_document_provenance_is_collected():
    result = run_agent(
        "read_document",
        "research_agent",
        "public_report.pdf",
    )

    assert len(result["source_provenance"]) == 1
    assert result["source_provenance"][0]["source_id"] == "doc-public-001"


def test_confidential_provenance_is_not_exposed():
    result = run_agent(
        "read_document",
        "research_agent",
        "confidential_notes.txt",
    )

    assert result["source_provenance"] == []
    assert result["output_provenance"] == []


def test_search_does_not_expose_unauthorized_provenance():
    result = run_agent(
        "search_documents",
        "research_agent",
        ".txt",
    )

    assert result["source_provenance"] == []
    assert result["output_provenance"] == []


def test_output_preserves_source_trust_and_sensitivity():
    result = run_agent(
        "read_document",
        "research_agent",
        "public_report.pdf",
    )

    source = result["source_provenance"][0]
    output = result["output_provenance"][0]

    assert output["trust_level"] == source["trust_level"]
    assert output["sensitivity"] == source["sensitivity"]
    assert output["parent_source_ids"] == [source["source_id"]]