
from backend.tools.broker import ToolBroker


def test_registered_read_tool_executes():
    broker = ToolBroker()

    result = broker.execute(
        "read_document",
        "public_report.pdf",
    )

    assert result["success"] is True
    assert result["resource"] == "public_report.pdf"


def test_search_tool_respects_allowed_resources():
    broker = ToolBroker()

    result = broker.execute(
        "search_documents",
        ".txt",
        allowed_resources=frozenset({"public_report.pdf"}),
    )

    assert result["success"] is True
    assert result["matches"] == []


def test_unregistered_tool_is_rejected():
    broker = ToolBroker()

    result = broker.execute(
        "delete_database",
        "database",
    )

    assert result["success"] is False
    assert result["error"] == "Tool is not registered"


def test_email_requires_destination_and_content():
    broker = ToolBroker()

    result = broker.execute(
        "send_email",
        "email",
    )

    assert result["success"] is False
    assert result["error"] == (
        "Email destination and content are required"
    )


def test_email_tool_is_simulated():
    broker = ToolBroker()

    result = broker.execute(
        "send_email",
        "email",
        destination="demo@example.com",
        content="Test message",
    )

    assert result["success"] is True
    assert result["simulated"] is True
