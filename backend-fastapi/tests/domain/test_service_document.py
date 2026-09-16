import pytest
from src.domain.service_document import validate_document, plain_text


def document(node):
    return {"version": 1, "doc": {"type": "doc", "content": [node]}}


@pytest.mark.parametrize("node", [
    {"type": "image", "attrs": {"src": "https://example.com/a.png"}},
    {"type": []}, {"type": "heading", "attrs": [1]},
    {"type": "heading", "attrs": {"level": []}},
    {"type": "paragraph", "content": [{"type": "text", "text": "X", "marks": None}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "X", "marks": [{"type": []}]}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "X", "marks": [{"type": "link", "attrs": {"href": "javascript:alert(1)"}}]}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "X", "marks": [{"type": "link", "attrs": {"href": "https://["}}]}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "x" * 20001}]},
])
def test_rejects_unsupported_or_malformed_documents(node):
    with pytest.raises(ValueError):
        validate_document(document(node))


def test_preserves_supported_formatting_and_sanitizes_link_attributes():
    value = document({"type": "paragraph", "content": [{"type": "text", "text": "Olá, ação!", "marks": [{"type": "bold"}, {"type": "link", "attrs": {"href": "https://example.com", "target": "_blank", "rel": "noopener"}}]}]})
    result = validate_document(value)
    assert plain_text(result["doc"]) == "Olá, ação!"
    assert result["doc"]["content"][0]["content"][0]["marks"][1]["attrs"] == {"href": "https://example.com"}
