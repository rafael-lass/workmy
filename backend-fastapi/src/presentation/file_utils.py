import base64
import binascii


MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_RECEIPT_TYPES = ALLOWED_IMAGE_TYPES | {"application/pdf"}


def decode_image_data_url(value: str | None) -> tuple[bytes | None, str | None]:
    """Decodifica uma imagem em data URL e aplica limites da API."""
    if not value:
        return None, None

    try:
        header, encoded = value.split(",", 1)
        if not header.startswith("data:") or ";base64" not in header:
            raise ValueError
        mime = header[5:].split(";", 1)[0].lower()
        if mime not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Formato não permitido. Use PNG, JPEG ou WebP.")
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        if isinstance(exc, ValueError) and str(exc):
            raise
        raise ValueError("Imagem inválida ou corrompida.") from exc

    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("A imagem deve ter no máximo 5 MB.")
    return content, mime


def encode_data_url(content: bytes | memoryview | None, mime: str | None) -> str | None:
    if not content:
        return None
    if isinstance(content, memoryview):
        content = content.tobytes()
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mime or 'image/png'};base64,{encoded}"


def decode_receipt_data_url(value: str | None) -> tuple[bytes | None, str | None]:
    """Decodifica comprovantes em imagem ou PDF, limitados a 5 MB."""
    if not value:
        return None, None

    try:
        header, encoded = value.split(",", 1)
        if not header.startswith("data:") or ";base64" not in header:
            raise ValueError
        mime = header[5:].split(";", 1)[0].lower()
        if mime not in ALLOWED_RECEIPT_TYPES:
            raise ValueError("Formato não permitido. Use PDF, PNG, JPEG ou WebP.")
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        if isinstance(exc, ValueError) and str(exc):
            raise
        raise ValueError("Comprovante inválido ou corrompido.") from exc

    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("O comprovante deve ter no máximo 5 MB.")
    return content, mime
