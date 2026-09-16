"""Generate deterministic PDF samples for visual QA; no database or network access."""
from io import BytesIO
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw
from src.domain.entities.servico import ServicoEntity
from src.domain.service_document import validate_document
from src.infrastructure.documents.service_pdf import ServicePdfRenderer


def samples():
    paragraph = lambda text, **kwargs: {"type": "paragraph", "content": [{"type": "text", "text": text, **kwargs}]}
    heading = {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Sobre o serviço"}]}
    content = [heading, paragraph("Uma apresentação clara para seu trabalho. Atenção, criação e colaboração com o cliente.", marks=[{"type": "bold"}]),
               {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "O que está incluído"}]},
               {"type": "bulletList", "content": [{"type": "listItem", "content": [paragraph(text)]} for text in ["Alinhamento de objetivos e escopo", "Etapas de revisão combinadas", "Orientações para entrega"]]},
               {"type": "blockquote", "content": [paragraph("Cada trabalho começa com uma conversa sobre suas necessidades.")]},
               paragraph("Conheça o portfólio", marks=[{"type": "link", "attrs": {"href": "https://example.com/portfolio"}}])]
    contact = {"nome_profissional": "João & Ana — Estúdio Criativo", "email": "contato@example.com", "telefone": "(11) 99999-9999"}
    cover = Image.new('RGB', (1200, 500), '#eef2ff')
    drawing = ImageDraw.Draw(cover)
    drawing.rounded_rectangle((90, 70, 1110, 430), radius=35, fill='#4f46e5')
    drawing.ellipse((870, 150, 1040, 320), fill='#10b981')
    image = BytesIO(); cover.save(image, format='PNG')
    for name, nodes, image_bytes in [('without-cover', content, None), ('with-cover', content, image.getvalue()), ('long', content + [paragraph(f'{index + 1}. ' + 'Planejamento, atenção aos detalhes e comunicação durante as etapas do serviço. ' * 7) for index in range(26)], image.getvalue()), ('empty', [], None)]:
        document = validate_document({"version": 1, "doc": {"type": "doc", "content": nodes}}) if nodes else None
        service = ServicoEntity(usuario_id=1, nome='Design & presença digital', descricao_documento=document, etiquetas=[{"id": 1, "nome": "Design"}, {"id": 2, "nome": "Identidade visual"}], imagem_bytes=image_bytes)
        yield name, ServicePdfRenderer().render(service, contact)


if __name__ == '__main__':
    destination = Path(sys.argv[1] if len(sys.argv) > 1 else '../tmp/pdfs')
    destination.mkdir(parents=True, exist_ok=True)
    for name, pdf in samples():
        path = destination / f'{name}.pdf'
        path.write_bytes(pdf)
        print(path.resolve())
