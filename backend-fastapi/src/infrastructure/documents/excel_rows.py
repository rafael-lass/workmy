"""Serialização de blocos de linhas OOXML; workers não acessam banco nem workbook."""
from datetime import date, datetime
from decimal import Decimal
import math
import pickle
import re
from time import perf_counter
from xml.sax.saxutils import escape

from src.domain.service_document import plain_text

STAGES = {'DISCOVERY': 'Planejamento', 'IN_PROGRESS': 'Andamento', 'REVIEW': 'Revisão',
          'COMPLETED': 'Finalizado', 'ARCHIVED': 'Arquivado'}
CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]')
EXCEL_ESCAPE = re.compile(r'(_x[0-9A-Fa-f]{4}_)')


def text_xml(value):
    value = CONTROL.sub('', value)[:32767]
    value = EXCEL_ESCAPE.sub(r'_x005F\1', value).replace('\r', '_x000D_')
    return escape(value)


def cell_xml(ref, value, money_style, date_style):
    if value is None:
        return ''
    if isinstance(value, bool):
        value = 'Sim' if value else 'Não'
    if isinstance(value, str):
        return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{text_xml(value)}</t></is></c>'
    style = ''
    if isinstance(value, (date, datetime)):
        moment = value if isinstance(value, datetime) else datetime.combine(value, datetime.min.time())
        if moment.tzinfo is not None:
            raise ValueError('Datas da exportação devem estar sem fuso horário.')
        value = (moment - datetime(1899, 12, 31)).total_seconds() / 86400
        if value >= 60:
            value += 1  # Calendário Excel 1900, incluindo o dia bissexto fictício.
        style = f' s="{date_style}"'
    elif isinstance(value, Decimal):
        value = float(value)
        style = f' s="{money_style}"'
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'Valor de célula não suportado: {type(value).__name__}')
    return f'<c r="{ref}"{style}><v>{value:.16g}</v></c>'


def render_rows(job):
    """Mesma tarefa para sequential e ProcessPoolExecutor; apenas arquivos privados."""
    source, destination, key, columns, offset, today, money_style, date_style = job
    started = perf_counter()
    # O pickle é produzido nesta exportação, em diretório privado, nunca pelo usuário.
    with open(source, 'rb') as stream:
        rows = pickle.load(stream)
    with open(destination, 'w', encoding='utf-8', newline='') as stream:
        for row_number, original in enumerate(rows, offset + 2):
            row = original.copy()
            if key == 'pagamentos':
                row['atrasado'] = row['status'] == 'PENDENTE' and row['data_vencimento'] < today
            elif key == 'projetos':
                row['status'] = STAGES.get(row['status'], row['status'])
            elif key == 'servicos':
                document = row.get('descricao_documento')
                row['descricao'] = plain_text(document.get('doc')) if document else row.get('descricao')
            cells = ''.join(cell_xml(f'{letter}{row_number}', row.get(field), money_style, date_style)
                            for field, letter in columns)
            stream.write(f'<row r="{row_number}">{cells}</row>')
    return {'rows': len(rows), 'seconds': perf_counter() - started}
