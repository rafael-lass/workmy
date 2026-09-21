"""Render the reviewed WorkMy backlog. No network access or Trello mutations.

Run: python docs/trello/render_board.py [--check]
The JSON is the source of truth; generated Markdown is portable and copyable.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def link(path: str, from_dir: Path) -> str:
    import os
    relative = Path(os.path.relpath(ROOT / path, from_dir)).as_posix()
    return f"[{path}]({relative})"


def render_card(card: dict, board: dict) -> str:
    out = [f"# {card['id']} — {card['title']}", "",
           f"Lista: **{card['list']}**  ",
           f"Prioridade: **{card['priority'] or 'Entrega existente'}**  ",
           f"Etiquetas: {', '.join(card['labels'])}  ",
           f"Responsáveis futuros: {', '.join(card['owners']) or 'Não atribuídos retrospectivamente'}  ",
           f"QA/revisão futura: {', '.join(card['reviewers']) or 'Não atribuída retrospectivamente'}  ",
           f"Dependências: {', '.join(card['dependencies']) or 'Nenhuma'}", "",
           "## Objetivo", "", card['objective'], "",
           "## Escopo técnico", ""]
    if card.get('trello_url'):
        out[2:2] = [f"Trello: [{card['trello_url']}]({card['trello_url']})", ""]
    checked = 'x' if card['list'] == 'Concluído' or card.get('implementation_complete') else ' '
    out += [f"- [{checked}] {item}" for item in card['implementation']]
    out += ["", "## Referências de código", "",
            f"Base da análise: `{board['baseline_commit']}`. As referências descrevem a versão analisada, não uma futura entrega.", ""]
    for ref in card['references']:
        out.append(f"- {link(ref['path'], HERE / 'cards')} — {ref['detail']}")
    out += ["", "## Critérios de aceite", ""]
    out += [f"- {item}" for item in card['acceptance']]
    for case in card['tests']:
        out += ["", f"## {case['id']} — {case['title']}", "",
                f"**Tipo:** {case['kind']}  ", f"**Status:** {case['status']}", "",
                "**Pré-condições**", ""]
        out += [f"- {item}" for item in case['preconditions']]
        out += ["", "**Passos**", ""]
        out += [f"{i}. {item}" for i, item in enumerate(case['steps'], 1)]
        out += ["", "**Resultado esperado**", ""]
        out += [f"- {item}" for item in case['expected']]
        out += ["", "**Resultado obtido**", "", case['actual'], ""]
        if case.get('automated_refs'):
            out += ["**Testes existentes relacionados**", ""]
            for ref in case['automated_refs']:
                out.append(f"- {link(ref['path'], HERE / 'cards')} — `{ref['name']}`")
            out += [""]
        out += ["**Evidências**", ""]
        if case['evidence']:
            out += [f"- {link(path, HERE / 'cards')}" for path in case['evidence']]
        else:
            out += ["- Pendente de execução; anexar relatório, comando, data, ambiente e versão."]
    if card['limitations']:
        out += ["", "## Limites e observações", ""]
        out += [f"- {item}" for item in card['limitations']]
    out += ["", "## Registro da próxima execução", "",
            "- Versão/commit:", "- Data e ambiente:", "- Executor:",
            "- Comando ou passos executados:", "- Resultado obtido:",
            "- Status: Não executado / Aprovado / Reprovado / Bloqueado",
            "- Evidência:", "- Bug relacionado, se houver:", ""]
    return '\n'.join(out)


def outputs(board: dict) -> dict[Path, str]:
    ids = [c['id'] for c in board['cards']]
    assert len(ids) == 21 and len(set(ids)) == 21, 'Expected 21 unique cards'
    assert set(ids) == {f'WM-{n:03d}' for n in range(1, 22)}
    rendered = {}
    summary = [f"# {board['name']}", "", board['purpose'], "",
               f"Base: `{board['baseline_commit']}` · Análise: {board['review_date']}", "",
               "Fonte editável: [board.json](board.json). Este arquivo e os cartões são gerados por `render_board.py`.", "",
               (f"Quadro publicado: [{board['remote']['url']}]({board['remote']['url']}). "
                "Mapeamento e conferência: [publicacao.json](publicacao.json)."
                if board.get('remote') else "Publicação no Trello: pendente."), "",
               "## Fluxo", "", ' → '.join(board['lists'][:4]) + ' · Bloqueado para impedimentos.', "",
               "## Como interpretar os estados", "", *board['state_rules'], ""]
    for name in board['lists']:
        cards = [c for c in board['cards'] if c['list'] == name]
        summary += [f"## {name} ({len(cards)})", ""]
        if not cards:
            summary += ['Nenhum cartão nesta classificação inicial.', '']
        for card in cards:
            summary += [f"- [{card['id']} — {card['title']}](cards/{card['id']}.md)"]
        summary += ['']
    summary += ['## Responsabilidades futuras', '',
                '- Rafael: PO e desenvolvimento; regras, API, banco e consolidação da versão.',
                '- Gabriel: frontend e validação técnica; interface, BFF e E2E.',
                '- Tais: QA e documentação; revisão funcional, requisitos e rastreabilidade.', '',
                'Não atribuir autores ou datas às entregas passadas sem confirmação. Não convidar pessoas nem enviar notificações como parte da preparação local.', '',
                '## Critério de conclusão para novos cartões', '']
    summary += [f'{i}. {x}' for i, x in enumerate(board['definition_of_done'], 1)]
    summary += ['', '## Ordem recomendada', '',
                'WM-013 → WM-014 → WM-015 → WM-016 → WM-017 → WM-021. WM-018, WM-019 e WM-020 compõem a evolução técnica seguinte.', '',
                '## Evidências e reprodução', '',
                '- [Relatório da análise e execução](evidencias/2026-09-21/RELATORIO.md)',
                '- [Correção WM-017 e relatório de testes para N1](evidencias/2026-09-21-reteste-WM017/RELATORIO.md)',
                '- [Log backend](evidencias/2026-09-21/backend.log) · [JUnit backend](evidencias/2026-09-21/backend.xml)',
                '- [Log frontend](evidencias/2026-09-21/frontend.log) · [JUnit frontend](evidencias/2026-09-21/frontend.xml)', '',
                '## Manutenção', '',
                'Edite `board.json`, execute `python docs/trello/render_board.py` na raiz e confira com `python docs/trello/render_board.py --check`.', '',
                'O JSON é uma fonte local estruturada, não um arquivo de importação nativa do Trello. Cada Markdown contém a descrição completa para o cartão correspondente. A publicação remota deve conservar IDs, listas, descrições e checklists, evitando duplicatas por ID WM.', '',
                'O quadro trata do software. Ficha, vídeo, entrega acadêmica e apresentação não são cartões deste backlog.', '']
    rendered[HERE / 'README.md'] = '\n'.join(summary)
    for c in board['cards']:
        assert c['list'] in board['lists']
        assert all(d in ids and d != c['id'] for d in c['dependencies'])
        assert c['implementation'] and c['acceptance'] and c['references']
        for ref in c['references']:
            assert (ROOT / ref['path']).is_file(), f"Missing reference: {ref['path']}"
        for t in c['tests']:
            assert t['preconditions'] and t['steps'] and t['expected'] and t['actual']
            for ref in t.get('automated_refs', []):
                source = ROOT / ref['path']
                assert source.is_file(), f'Missing test: {source}'
                assert ref['name'] in source.read_text(encoding='utf-8'), f"Missing test name: {ref['name']}"
            for e in t['evidence']:
                assert (ROOT / e).is_file(), f'Missing evidence: {e}'
        rendered[HERE / 'cards' / f"{c['id']}.md"] = render_card(c, board)
    return rendered


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    board = json.loads((HERE / 'board.json').read_text(encoding='utf-8'))
    for path, content in outputs(board).items():
        if args.check:
            assert path.is_file() and path.read_text(encoding='utf-8') == content, f'Outdated: {path}'
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
    print(f"{'Verified' if args.check else 'Generated'} 21 cards and board index; references and evidence validated.")
