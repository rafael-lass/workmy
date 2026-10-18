"""Workbooks com linhas produzidas em blocos, sequenciais ou multiprocessing."""
from datetime import date, datetime
from multiprocessing import get_context
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory, mkstemp
from time import perf_counter
from zipfile import ZIP_STORED, ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET
import os
import pickle
import re
import shutil
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
from src.infrastructure.documents.excel_rows import render_rows


def run_sequential(jobs):
    """Executa a mesma tarefa em um único processo, um bloco após o outro."""
    return [render_rows(job) for job in jobs]


def run_parallel(jobs, workers):
    """Pool de processos reais da biblioteca multiprocessing."""
    if not jobs:
        return []
    with get_context('spawn').Pool(processes=min(workers, len(jobs))) as pool:
        return pool.map(render_rows, jobs)


PAYMENT_COLUMNS = [('id', 'ID'), ('projeto_id', 'Projeto ID'), ('cliente_id', 'Cliente ID'),
    ('cliente', 'Cliente'), ('servico_id', 'Serviço ID'), ('servico', 'Serviço'),
    ('tipo_pagamento', 'Tipo'), ('status', 'Situação'), ('referencia_mes', 'Referência'),
    ('data_vencimento', 'Vencimento'), ('data_pagamento', 'Pagamento'), ('valor', 'Valor (R$)'),
    ('atrasado', 'Em atraso'), ('observacao', 'Observação'), ('motivo_ajuste', 'Motivo do ajuste'),
    ('criado_em', 'Criado em'), ('atualizado_em', 'Atualizado em')]
CLIENT_COLUMNS = [('id', 'ID'), ('nome', 'Nome'), ('empresa', 'Empresa'), ('email', 'E-mail'),
    ('telefone', 'Telefone'), ('criado_em', 'Criado em'), ('deletado_em', 'Excluído em')]
SERVICE_COLUMNS = [('id', 'ID'), ('nome', 'Nome'), ('descricao', 'Descrição'),
    ('criado_em', 'Criado em'), ('deletado_em', 'Excluído em')]
PROJECT_COLUMNS = [('id', 'ID'), ('cliente_id', 'Cliente ID'), ('cliente', 'Cliente'),
    ('servico_id', 'Serviço ID'), ('servico', 'Serviço'), ('status', 'Etapa'),
    ('tipo_recorrencia', 'Tipo'), ('recorrencia_ativa', 'Recorrência ativa'), ('valor', 'Valor (R$)'),
    ('valor_mensal', 'Mensalidade (R$)'), ('dia_vencimento', 'Dia de vencimento'),
    ('recorrencia_inicio', 'Início da recorrência'), ('data_entrega', 'Entrega'),
    ('criado_em', 'Criado em'), ('deletado_em', 'Excluído em')]
STAGES = {'DISCOVERY': 'Planejamento', 'IN_PROGRESS': 'Andamento', 'REVIEW': 'Revisão',
          'COMPLETED': 'Finalizado', 'ARCHIVED': 'Arquivado'}


def write_value(sheet, row, col, value, formats):
    if value is None:
        return
    if isinstance(value, str):
        # Text APIs prevent formula injection, including cells beginning with '='.
        value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', value)
        sheet.write_string(row, col, value[:32767])
    elif isinstance(value, bool):
        sheet.write_string(row, col, 'Sim' if value else 'Não')
    elif isinstance(value, (date, datetime)):
        sheet.write_datetime(row, col, value, formats['date'])
    elif isinstance(value, Decimal):
        sheet.write_number(row, col, float(value), formats['money'])
    else:
        sheet.write(row, col, value)


def write_list(workbook, name, columns, rows, formats):
    sheet = workbook.add_worksheet(name)
    sheet.hide_gridlines(2)
    sheet.freeze_panes(1, 0)
    sheet.set_row(0, 30)
    for col, (key, title) in enumerate(columns):
        width = 42 if key in ('observacao', 'descricao', 'motivo_ajuste') else 27 if key in ('nome', 'cliente', 'servico', 'email', 'empresa') else 19
        sheet.set_column(col, col, width)
        sheet.write_string(0, col, title, formats['header'])
    count = 0
    for count, row in enumerate(rows, 1):
        if count >= 1048576:
            raise ValueError('A exportação ultrapassou o limite de linhas do Excel.')
        for col, (key, _) in enumerate(columns):
            write_value(sheet, count, col, row.get(key), formats)
    sheet.autofilter(0, 0, max(count, 1), len(columns) - 1)
    sheet.repeat_rows(0)
    sheet.set_landscape()
    sheet.fit_to_pages(1, 0)


class DashboardExcelRenderer:
    def __init__(self, workers=4, batch_size=25000):
        if workers < 1 or batch_size < 1:
            raise ValueError('Workers e tamanho do bloco devem ser positivos.')
        self.workers, self.batch_size = workers, batch_size

    def _render_one(self, name, columns, rows, path):
        with xlsxwriter.Workbook(str(path), {'constant_memory': True, 'tmpdir': str(path.parent), 'strings_to_formulas': False,
                                              'strings_to_urls': False}) as workbook:
            formats = {
                'header': workbook.add_format({'bold': True, 'bg_color': '#13253B', 'font_color': '#FFFFFF', 'valign': 'vcenter'}),
                'money': workbook.add_format({'num_format': '"R$" #,##0.00;[Red]("R$" #,##0.00);"R$" 0.00'}),
                'date': workbook.add_format({'num_format': 'dd/mm/yyyy'}),
            }
            write_list(workbook, name, columns, rows, formats)

    def render(self, data, period, mode='parallel'):
        if mode not in {'sequential', 'parallel'}:
            raise ValueError('Modo de exportação inválido.')
        descriptor, filename = mkstemp(prefix='workmy-relatorios-', suffix='.zip')
        os.close(descriptor)
        archive_path = Path(filename)
        timings, sizes = {}, {}
        try:
            with TemporaryDirectory(prefix='workmy-excel-') as temporary:
                folder = Path(temporary)
                sheets = [
                    ('pagamentos', 'Pagamentos', PAYMENT_COLUMNS, data['pagamentos']),
                    ('clientes', 'Clientes', CLIENT_COLUMNS, data['clientes']),
                    ('servicos', 'Serviços', SERVICE_COLUMNS, data['servicos']),
                    ('projetos', 'Projetos', PROJECT_COLUMNS, data['projetos']),
                ]
                workbook_paths = []
                jobs = []
                plans = []
                started = perf_counter()
                for key, name, columns, rows in sheets:
                    if len(rows) > 1048575:
                        raise ValueError('A exportação ultrapassou o limite de linhas do Excel.')
                    path = folder / f'workmy-{key}-{period.key}-{period.today.isoformat()}.xlsx'
                    template = folder / f'{key}-template.xlsx'
                    # Linha técnica removida do resultado; registra moeda e data no template.
                    self._render_one(name, columns, [{columns[0][0]: Decimal(1), columns[1][0]: date(2000, 1, 1)}], template)
                    with ZipFile(template) as book:
                        xml = book.read('xl/worksheets/sheet1.xml').decode('utf-8')
                    namespace = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    sentinel = ET.fromstring(xml).find("s:sheetData/s:row[@r='2']", namespace)
                    money_style, date_style = (cell.attrib['s'] for cell in sentinel)
                    prefix, rest = xml.split('<sheetData>', 1)
                    sheet_rows, suffix = rest.split('</sheetData>', 1)
                    header = re.search(r'<row r="1".*?</row>', sheet_rows).group()
                    last_col = xl_col_to_name(len(columns) - 1)
                    prefix = re.sub(r'<dimension ref="[^"]+"/>', f'<dimension ref="A1:{last_col}{len(rows) + 1}"/>', prefix)
                    suffix = re.sub(r'<autoFilter ref="[^"]+"/>', f'<autoFilter ref="A1:{last_col}{max(2, len(rows) + 1)}"/>', suffix)
                    fragments = []
                    for offset in range(0, len(rows), self.batch_size):
                        source, destination = folder / f'{key}-{offset}.pickle', folder / f'{key}-{offset}.xml'
                        with source.open('wb') as stream:
                            pickle.dump(rows[offset:offset + self.batch_size], stream, protocol=pickle.HIGHEST_PROTOCOL)
                        jobs.append((source, destination, key, [(field, xl_col_to_name(i)) for i, (field, _) in enumerate(columns)],
                                     offset, period.today, money_style, date_style))
                        fragments.append(destination)
                    plans.append((template, path, prefix + '<sheetData>' + header, '</sheetData>' + suffix, fragments))
                    workbook_paths.append((path, path.name))
                timings['preparar_blocos'] = perf_counter() - started
                started = perf_counter()
                results = run_parallel(jobs, self.workers) if mode == 'parallel' else run_sequential(jobs)
                timings['processar_blocos'] = perf_counter() - started
                if sum(item['rows'] for item in results) != sum(len(rows) for rows in data.values()):
                    raise RuntimeError('Quantidade de linhas processadas inconsistente.')
                started = perf_counter()
                for template, path, prefix, suffix, fragments in plans:
                    with ZipFile(template) as original, ZipFile(path, 'w', compression=ZIP_DEFLATED, allowZip64=True) as book:
                        for item in original.infolist():
                            if item.filename != 'xl/worksheets/sheet1.xml':
                                book.writestr(item, original.read(item.filename))
                        with book.open('xl/worksheets/sheet1.xml', 'w', force_zip64=True) as sheet:
                            sheet.write(prefix.encode('utf-8'))
                            for fragment in fragments:
                                with fragment.open('rb') as stream:
                                    shutil.copyfileobj(stream, sheet, length=1024 * 1024)
                            sheet.write(suffix.encode('utf-8'))
                timings['montar_xlsx'] = perf_counter() - started
                for path, _ in workbook_paths:
                    sizes[path.name] = path.stat().st_size
                zip_started = perf_counter()
                with ZipFile(archive_path, 'w', compression=ZIP_STORED, allowZip64=True) as archive:
                    for path, arcname in workbook_paths:
                        archive.write(path, arcname)
                timings['pacote_zip'] = perf_counter() - zip_started
            sizes['pacote_zip'] = archive_path.stat().st_size
            return archive_path, timings, sizes
        except BaseException:
            archive_path.unlink(missing_ok=True)
            raise
