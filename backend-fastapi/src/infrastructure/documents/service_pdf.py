"""Commercial service presentation. Never fetches external resources."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import reportlab
from PIL import Image as PillowImage, ImageOps, UnidentifiedImageError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem, KeepTogether

from src.domain.service_document import plain_text, safe_link


# Bitstream Vera fonts and their license are bundled with the pinned ReportLab
# package, including in the Docker image. No runtime downloads are required.
_fonts = Path(reportlab.__file__).parent / "fonts"
for _name, _file in [("Service", "Vera.ttf"), ("Service-Bold", "VeraBd.ttf"),
                     ("Service-Italic", "VeraIt.ttf"), ("Service-BoldItalic", "VeraBI.ttf")]:
    pdfmetrics.registerFont(TTFont(_name, str(_fonts / _file)))
pdfmetrics.registerFontFamily("Service", normal="Service", bold="Service-Bold", italic="Service-Italic", boldItalic="Service-BoldItalic")


class ServicePdfRenderer:
    def render(self, service, contact: dict) -> bytes:
        output = BytesIO()
        indigo = colors.HexColor("#4f46e5")
        green = colors.HexColor("#08705a")
        width = A4[0] - 100
        styles = {
            "body": ParagraphStyle("Body", fontName="Service", fontSize=10, leading=16, textColor=colors.HexColor("#334155"), spaceAfter=10, splitLongWords=True),
            "title": ParagraphStyle("Title", fontName="Service-Bold", fontSize=28, leading=34, textColor=indigo, spaceAfter=14, keepWithNext=True),
            "h1": ParagraphStyle("H1", fontName="Service-Bold", fontSize=20, leading=26, textColor=indigo, spaceBefore=16, spaceAfter=10, keepWithNext=True),
            "h2": ParagraphStyle("H2", fontName="Service-Bold", fontSize=15, leading=21, textColor=indigo, spaceBefore=14, spaceAfter=8, keepWithNext=True),
            "h3": ParagraphStyle("H3", fontName="Service-Bold", fontSize=12, leading=18, textColor=green, spaceBefore=12, spaceAfter=6, keepWithNext=True),
            "small": ParagraphStyle("Small", fontName="Service", fontSize=9, leading=14, textColor=green, spaceAfter=12),
            "quote": ParagraphStyle("Quote", fontName="Service-Italic", fontSize=10, leading=16, leftIndent=16, borderPadding=10, textColor=green, spaceAfter=12),
        }

        def inline(node):
            if node["type"] == "hardBreak":
                return "<br/>"
            text = escape(node.get("text", ""))
            for mark in node.get("marks", []):
                if mark["type"] == "bold":
                    text = f"<b>{text}</b>"
                elif mark["type"] == "italic":
                    text = f"<i>{text}</i>"
                elif mark["type"] == "link" and safe_link(mark["attrs"]["href"]):
                    text = f'<a href={quoteattr(mark["attrs"]["href"])} color="#4f46e5">{text}</a>'
            return text

        def blocks(nodes, quote=False):
            flow = []
            for node in nodes:
                kind = node["type"]
                if kind in {"paragraph", "heading"}:
                    style = styles[f'h{node["attrs"]["level"]}'] if kind == "heading" else styles["quote" if quote else "body"]
                    flow.append(Paragraph("".join(inline(child) for child in node.get("content", [])) or "<br/>", style))
                elif kind == "blockquote":
                    flow.extend(blocks(node.get("content", []), quote=True))
                elif kind in {"bulletList", "orderedList"}:
                    items = [ListItem(blocks(child["content"]), leftIndent=12) for child in node["content"]]
                    flow.append(ListFlowable(items, bulletType="1" if kind == "orderedList" else "bullet",
                                             start=node.get("attrs", {}).get("start", 1) if kind == "orderedList" else "\u2022",
                                             leftIndent=18, bulletFontName="Service", bulletFontSize=9, spaceAfter=12))
            return flow

        story = [Paragraph("APRESENTAÇÃO DE SERVIÇO", styles["small"]),
                 Paragraph(escape(service.nome), styles["title"]),
                 Paragraph(escape(contact["nome_profissional"]), styles["body"])]
        if service.etiquetas:
            story.append(Paragraph(" · ".join(escape(tag["nome"]) for tag in service.etiquetas), styles["small"]))
        if service.imagem_bytes:
            try:
                with PillowImage.open(BytesIO(service.imagem_bytes)) as original:
                    cover = ImageOps.exif_transpose(original).convert("RGB")
                    cover.thumbnail((1600, 1600))
                    image_buffer = BytesIO()
                    cover.save(image_buffer, format="JPEG", quality=88)
                    image_buffer.seek(0)
                    factor = min(width / cover.width, 180 / cover.height)
                    story.extend([Image(image_buffer, width=cover.width * factor, height=cover.height * factor), Spacer(1, 18)])
            except (UnidentifiedImageError, OSError, ValueError, PillowImage.DecompressionBombError):
                pass  # Legacy invalid covers must not prevent exporting the text.
        doc = (service.descricao_documento or {}).get("doc")
        if plain_text(doc).strip():
            story.extend(blocks(doc["content"]))
        contact_lines = [Paragraph("Vamos conversar?", styles["h2"]),
                         Paragraph(escape(contact["nome_profissional"]), styles["small"]),
                         Paragraph(escape(str(contact["email"])), styles["small"])]
        if contact.get("telefone"):
            contact_lines.append(Paragraph(escape(contact["telefone"]), styles["small"]))
        story.extend([Spacer(1, 20), KeepTogether(contact_lines)])

        def footer(canvas, document):
            canvas.saveState()
            canvas.setStrokeColor(indigo)
            canvas.setLineWidth(2)
            canvas.line(50, 42, A4[0] - 50, 42)
            canvas.setFont("Service", 8)
            canvas.setFillColor(colors.HexColor("#64748b"))
            canvas.drawString(50, 28, "Apresentação de serviço")
            canvas.drawRightString(A4[0] - 50, 28, f"{document.page}")
            canvas.restoreState()

        SimpleDocTemplate(output, pagesize=A4, leftMargin=50, rightMargin=50,
                          topMargin=48, bottomMargin=62, title=service.nome,
                          author=contact["nome_profissional"]).build(story, onFirstPage=footer, onLaterPages=footer)
        return output.getvalue()
