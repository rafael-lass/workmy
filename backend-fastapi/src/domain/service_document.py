"""Restricted, versioned rich text shared by API validation and PDF rendering."""
from urllib.parse import urlsplit


def plain_text(node: dict | None) -> str:
    if not node:
        return ""
    if node.get("type") == "text":
        return node["text"]
    separator = "" if node.get("type") in {"paragraph", "heading"} else "\n"
    return separator.join(plain_text(child) for child in node.get("content", []))


def safe_link(value: str) -> bool:
    if any(c.isspace() or ord(c) < 32 for c in value):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (parsed.scheme in {"http", "https"} and bool(parsed.netloc)) or (
        parsed.scheme == "mailto" and "@" in parsed.path
    )


def validate_document(document: dict | None) -> dict | None:
    if document is None:
        return None
    if not isinstance(document, dict) or set(document) != {"version", "doc"} or document["version"] != 1:
        raise ValueError("Formato de descrição inválido.")
    count = 0
    text_length = 0
    blocks = {"paragraph", "heading", "bulletList", "orderedList", "blockquote"}

    def visit(node, parent=None, depth=0):
        nonlocal count, text_length
        count += 1
        if depth > 12 or count > 5000 or not isinstance(node, dict):
            raise ValueError("Descrição excessivamente complexa.")
        kind = node.get("type")
        allowed = {None: {"doc"}, "doc": blocks, "paragraph": {"text", "hardBreak"},
                   "heading": {"text", "hardBreak"}, "blockquote": blocks,
                   "bulletList": {"listItem"}, "orderedList": {"listItem"}, "listItem": blocks}
        if not isinstance(kind, str) or kind not in allowed.get(parent, set()):
            raise ValueError("Elemento de descrição não permitido.")
        if set(node) - {"type", "content", "attrs", "text", "marks"}:
            raise ValueError("Propriedade de descrição não permitida.")
        result = {"type": kind}
        attrs = node.get("attrs") or {}
        if not isinstance(attrs, dict):
            raise ValueError("Atributos inválidos.")
        if kind == "heading":
            if set(attrs) - {"level"} or type(attrs.get("level")) is not int or attrs["level"] not in {1, 2, 3}:
                raise ValueError("Título inválido.")
            result["attrs"] = attrs
        elif kind == "orderedList":
            start = attrs.get("start", 1)
            if set(attrs) - {"start", "type"} or type(start) is not int or not 1 <= start <= 9999:
                raise ValueError("Lista inválida.")
            result["attrs"] = {"start": start}
        elif attrs:
            raise ValueError("Atributo de descrição não permitido.")
        if kind == "text":
            value = node.get("text")
            if not isinstance(value, str) or not value or node.get("content"):
                raise ValueError("Texto inválido.")
            text_length += len(value)
            result["text"] = value
            marks = []
            source_marks = node.get("marks", [])
            if not isinstance(source_marks, list) or len(source_marks) > 3:
                raise ValueError("Formatação inválida.")
            for mark in source_marks:
                if not isinstance(mark, dict) or set(mark) - {"type", "attrs"}:
                    raise ValueError("Formatação inválida.")
                name = mark.get("type")
                if not isinstance(name, str) or not isinstance(mark.get("attrs") or {}, dict):
                    raise ValueError("Formatação inválida.")
                if name in {"bold", "italic"} and not mark.get("attrs"):
                    marks.append({"type": name})
                elif name == "link":
                    href = (mark.get("attrs") or {}).get("href", "")
                    if not isinstance(href, str) or len(href) > 2000 or not safe_link(href):
                        raise ValueError("Link inválido. Use https://, http:// ou mailto:.")
                    marks.append({"type": "link", "attrs": {"href": href}})
                else:
                    raise ValueError("Formatação não permitida.")
            if marks:
                result["marks"] = marks
        else:
            if node.get("text") or node.get("marks"):
                raise ValueError("Conteúdo inválido.")
            children = node.get("content", [])
            if not isinstance(children, list) or (kind == "hardBreak" and children):
                raise ValueError("Conteúdo inválido.")
            if kind in {"doc", "listItem", "bulletList", "orderedList", "blockquote"} and not children:
                raise ValueError("Bloco vazio inválido.")
            if kind == "listItem" and (not isinstance(children[0], dict) or children[0].get("type") != "paragraph"):
                raise ValueError("Item de lista deve começar com parágrafo.")
            if kind != "hardBreak":
                result["content"] = [visit(child, kind, depth + 1) for child in children]
        return result

    doc = visit(document["doc"])
    if text_length > 20000:
        raise ValueError("A descrição deve ter no máximo 20 mil caracteres.")
    return {"version": 1, "doc": doc}
