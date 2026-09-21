"""Análises observacionais agregadas; consome derivações e junções validadas."""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
from auditoria_inicial import pair_records
from preparacao_coortes import load_prepared, origin_exclusion
from dados_pede import ROOT
from rastreabilidade import sha256_file, find_source_files, public_text_issues

MIN_PROFILE = 10
INDICATORS = ('ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv', 'inde')
YEARS = (2022, 2023, 2024)
STONES = ('Quartzo', 'Ágata', 'Ametista', 'Topázio')
STONE_LABELS = {'quartzo': 'Quartzo', 'agata': 'Ágata', 'ágata': 'Ágata',
                'ametista': 'Ametista', 'topázio': 'Topázio'}
METRICS = 'reports/metricas_analises_negocio.json'
REPORT = 'reports/relatorio_analises_negocio.md'
OFFICIAL = ('reports/metricas_modelagem.json', 'reports/relatorio_modelagem.md',
            'artifacts/schema_modelo.json', 'artifacts/configuracao_congelada.json')


def summary(values):
    s = pd.Series(list(values), dtype='float64')
    n = int(s.notna().sum())
    if len(s) < MIN_PROFILE or 0 < n < MIN_PROFILE:
        return {'status': 'suprimido: n < 10'}
    return {'status': 'disponivel' if n else 'sem_observacoes', 'total': len(s),
            'n': n, 'ausentes': int(s.isna().sum()), 'cobertura': n / len(s) if len(s) else None,
            'media': float(s.mean()) if n else None, 'mediana': float(s.median()) if n else None,
            'dp': float(s.std()) if n > 1 else None,
            'q25': float(s.quantile(.25)) if n else None, 'q75': float(s.quantile(.75)) if n else None}


def distribution(values, categories):
    """Suprime a partição inteira se célula pequena: evita subtração de margens."""
    counts = Counter(values)
    if set(counts) - set(categories):
        raise ValueError('Categorias não cobrem a partição observada')
    cells = {str(c): counts[c] for c in categories}
    if any(0 < n < MIN_PROFILE for n in cells.values()) or len(values) < MIN_PROFILE:
        return {'status': 'suprimido: particao com celula < 10'}
    total = sum(cells.values())
    return {'status': 'disponivel', 'denominador': total,
            'contagens': cells, 'proporcoes': {k: n / total if total else None for k, n in cells.items()}}


def grouped_summaries(groups):
    """Protege também a única célula omitida de uma tabela de perfis."""
    result = {str(k): summary(values) for k, values in groups.items()}
    hidden = [k for k, v in result.items() if v['status'].startswith('suprimido')]
    visible = [k for k in result if k not in hidden]
    if len(hidden) == 1 and visible:
        other = min(visible, key=lambda k: (result[k]['total'], k))
        result[other] = {'status': 'suprimido: complemento de privacidade'}
    return result


def association(x, y, years=None):
    d = pd.DataFrame({'x': x, 'y': y}, dtype='float64').dropna()
    if len(d) < MIN_PROFILE:
        return {'status': 'suprimido: n < 10'}
    ranks = d.rank(method='average')
    if years is not None:
        ranks['ano'] = pd.Series(years).loc[d.index].values
        ranks[['x', 'y']] -= ranks.groupby('ano')[['x', 'y']].transform('mean')
    rho = ranks.x.corr(ranks.y) if ranks.x.std() > 0 and ranks.y.std() > 0 else None
    rho = float(rho) if rho is not None and np.isfinite(rho) else None
    return {'status': 'estimada' if rho is not None else 'constante', 'n': len(d),
            'total': len(x), 'ausentes_par': len(x) - len(d), 'rho': rho,
            'direcao': None if rho is None else 'positiva' if rho > 0 else 'negativa' if rho < 0 else 'nula',
            'intensidade': None if rho is None else 'fraca' if abs(rho) < .3 else 'moderada' if abs(rho) < .6 else 'forte'}


def analytic_frame(records):
    """Lista positiva; nenhum identificador ou texto livre entra no frame analítico."""
    return pd.DataFrame([{'ano': r['ano_referencia'], 'fase': r['fase_extraida'],
                         'pedra': STONE_LABELS.get(r['pedra_padronizado'], 'Indisponível'),
                         'd': r['defasagem_registrada'], 'categoria': r['categoria_defasagem'],
                         'divergente': r['ian_divergente_defasagem'],
                         **{k: r[k + '_numerico'] for k in INDICATORS}} for r in records])


def paired_frames(records, origin, target):
    pairs = pair_records(records, origin, target, how='inner')
    left = [records[int(i)] for i in pairs.record_index_origem]
    right = [records[int(i)] for i in pairs.record_index_destino]
    return analytic_frame(left), analytic_frame(right)


def official_model(root):
    m, _, schema, frozen = [json.loads((root / p).read_text(encoding='utf-8')) if p.endswith('.json')
                             else (root / p).read_text(encoding='utf-8') for p in OFFICIAL]
    if not (m['limiar'] == schema['limiar'] == frozen['configuracao']['limiar']):
        raise ValueError('Limiar oficial inconsistente')
    if not (m['configuracao_sha256'] == schema['configuracao_sha256'] == frozen['sha256']):
        raise ValueError('Configuração oficial inconsistente')
    return {'modelo': m['modelo'], 'limiar': m['limiar'], 'preditores': schema['colunas'],
            'tipo': schema['tipo'], 'oof': m['oof']['metricas'], 'temporal': m['temporal']['metricas'],
            'diferencas': m['diferenca_temporal_menos_oof'],
            'intervalos': m['robustez']['intervalos'], 'distribuicao': m['robustez']['distribuicao'],
            'interpretabilidade': m['interpretabilidade']}


def analyze(records):
    df = analytic_frame(records)
    out = {'anuais': {}, 'ida_fase': {}, 'associacoes': {}, 'autoavaliacao': {},
           'longitudinal': {}, 'ipp': {}, 'ipv': {}, 'inde': {}, 'pedras': {}, 'perdas': {}}
    pairs = [('ieg', 'ida'), ('ieg', 'ipv'), ('iaa', 'ida'), ('iaa', 'ieg')]
    for year in YEARS:
        g = df[df.ano == year].reset_index(drop=True)
        if g.empty:
            continue
        if year == 2022 and g.ipp.notna().any():
            raise ValueError('IPP/2022 deve permanecer estruturalmente ausente')
        out['anuais'][str(year)] = {'total': len(g), 'indicadores': {k: summary(g[k]) for k in INDICATORS},
            'ian_distribuicao': distribution(['Ausente' if pd.isna(v) else v if v in (2.5, 5., 10.) else 'Outros valores' for v in g.ian], [2.5, 5., 10., 'Outros valores', 'Ausente']),
            'categorias': distribution(g.categoria.fillna('Ausente').tolist(), ['sem_defasagem', 'moderada', 'severa', 'Ausente']),
            'sinal_d': distribution(['Ausente' if pd.isna(d) else 'D<0' if d < 0 else 'D=0' if d == 0 else 'D>0' for d in g.d], ['D<0', 'D=0', 'D>0', 'Ausente']),
            'ian_divergencias': distribution(g.divergente.fillna('Indisponível').tolist(), [True, False, 'Indisponível'])}
        out['ida_fase'][str(year)] = grouped_summaries({str(int(f)): h.ida for f, h in g.groupby('fase')})
        out['associacoes'][str(year)] = {f'{a} x {b}': association(g[a], g[b]) for a, b in pairs}
        out['autoavaliacao'][str(year)] = {f'iaa - {b}': summary(g.iaa - g[b]) for b in ('ida', 'ieg')}
        out['ipp'][str(year)] = {'status': 'ausencia_estrutural'} if year == 2022 else {
            'ipp x ian': association(g.ipp, g.ian), 'ipp x d': association(g.ipp, g.d),
            'por_categoria': grouped_summaries({str(c): h.ipp for c, h in g.groupby('categoria')})}
        if year != 2022:
            valid = g.dropna(subset=['ipp', 'd'])
            median = float(valid.ipp.median())
            labels = [('IPP abaixo da mediana' if r.ipp < median else 'IPP na mediana ou acima') +
                      (' / D<0' if r.d < 0 else ' / D>=0') for r in valid.itertuples()]
            out['ipp'][str(year)]['mediana_ipp'] = median
            out['ipp'][str(year)]['perfis'] = distribution(labels, [a + b for a in ('IPP abaixo da mediana', 'IPP na mediana ou acima') for b in (' / D<0', ' / D>=0')])
        out['ipv'][str(year)] = {'associacoes': {k: association(g[k], g.ipv) for k in ('ida', 'ieg', 'iaa', 'ips', 'ipp') if year != 2022 or k != 'ipp'},
                                  'por_fase': grouped_summaries({str(int(f)): h.ipv for f, h in g.groupby('fase')})}
        features = ['ida', 'ieg', 'ips'] + ([] if year == 2022 else ['ipp'])
        complete = g.dropna(subset=features + ['inde']).copy()
        medians = {k: float(complete[k].median()) for k in features}
        complete['perfil'] = complete.apply(lambda r: ' / '.join(k.upper() + (' alto' if r[k] >= medians[k] else ' baixo') for k in features), axis=1)
        profile_groups = list(complete.groupby('perfil'))
        profiles = {p: summary(h.inde) for p, h in profile_groups if len(h) >= MIN_PROFILE}
        if sum(len(h) < MIN_PROFILE for _, h in profile_groups) == 1 and profiles:
            # Segunda supressão evita recuperar a única contagem pequena pelo total.
            profiles.pop(min(profiles, key=lambda p: (profiles[p]['n'], p)))
        out['inde'][str(year)] = {'criterio': 'alto >= mediana dos casos completos do ano; baixo < mediana',
            'medianas': medians, 'total': len(g), 'n_completos': len(complete),
            'perfis_publicados': profiles, 'nota': 'Perfis com menos de 10 não publicados; sem margens desses perfis.'}
        out['pedras'][str(year)] = {'distribuicao': distribution(g.pedra.tolist(), [*STONES, 'Indisponível']),
            'indicadores': {p: {k: summary(h[k]) for k in INDICATORS} for p, h in g.groupby('pedra') if p in STONES}}
    out['ida_fase']['agregado'] = grouped_summaries({str(int(f)): g.ida for f, g in df.groupby('fase')})
    out['associacoes']['ajustado_ano'] = {f'{a} x {b}': association(df[a], df[b], df.ano) for a, b in pairs}
    for origin, target in ((2022, 2023), (2023, 2024)):
        key = f'{origin}→{target}'
        a, b = paired_frames(records, origin, target)
        entry = {'n_correspondidos': len(a), 'mudancas': {}, 'ips': {}, 'ipv_futuro': {}}
        for k in ('ida', 'ieg'):
            delta = b[k] - a[k]
            entry['mudancas'][k] = summary(delta)
            valid = pd.DataFrame({'ips': a.ips, 'delta': delta}).dropna()
            entry['ips'][k] = {'associacao': association(a.ips, delta),
                'sensibilidade': {str(cut): distribution(['queda' if x < -cut else 'sem_queda' for x in valid.delta], ['queda', 'sem_queda']) for cut in (0, .5, 1)},
                'perfis': {str(cut): {label: summary(h.ips) for label, h in valid.assign(grupo=np.where(valid.delta < -cut, 'queda', 'sem_queda')).groupby('grupo')} for cut in (0, .5, 1)},
                'delta_por_ips': {label: summary(h.delta) for label, h in valid.assign(grupo=np.where(valid.ips < valid.ips.median(), 'abaixo_mediana', 'mediana_ou_acima')).groupby('grupo')}}
        for k in ('ida', 'ieg', 'iaa', 'ips', 'ipp'):
            if origin == 2022 and k == 'ipp':
                continue
            entry['ipv_futuro'][k] = association(a[k], b.ipv)
        transitions = [f'{x} → {y}' for x, y in zip(a.pedra, b.pedra) if x in STONES and y in STONES]
        entry['pedras_transicoes'] = distribution(transitions, [f'{x} → {y}' for x in STONES for y in STONES])
        change = ['melhoria' if STONES.index(y) > STONES.index(x) else 'piora' if STONES.index(y) < STONES.index(x) else 'estabilidade' for x, y in zip(a.pedra, b.pedra) if x in STONES and y in STONES]
        entry['pedras_evolucao'] = distribution(change, ['melhoria', 'estabilidade', 'piora'])
        entry['ida_por_pedra_origem'] = {p: summary((b.ida - a.ida)[a.pedra == p]) for p in STONES}
        out['longitudinal'][key] = entry
        joined = pair_records(records, origin, target, how='left')
        groups = {'encontrados': [], 'nao_encontrados': []}
        outcome_states = []
        for row in joined.to_dict('records'):
            r = records[int(row['record_index_origem'])]
            if origin_exclusion(r) is None:
                found = row['_merge'] == 'both'
                groups['encontrados' if found else 'nao_encontrados'].append(r)
                future = records[int(row['record_index_destino'])]['defasagem_registrada'] if found else None
                outcome_states.append('destino_ausente' if not found else 'destino_sem_defasagem_valida' if future is None else 'desfecho_observado')
        out['perdas'][key] = {'populacao': 'elegiveis na origem conforme contrato',
            'desfecho': distribution(outcome_states, ['destino_ausente', 'destino_sem_defasagem_valida', 'desfecho_observado']),
            'distribuicao': distribution([k for k, rows in groups.items() for _ in rows], list(groups)),
            'perfis': {k: {v: summary([r[v + '_numerico'] for r in rows]) for v in ('ida', 'ieg', 'iaa', 'ips', 'ipv')} for k, rows in groups.items()},
            'fases': {k: distribution([str(r['fase_extraida']) for r in rows], [str(f) for f in range(8)]) for k, rows in groups.items()},
            'defasagem': {k: summary([r['defasagem_registrada'] for r in rows]) for k, rows in groups.items()}}
    return out


def input_hashes(root):
    files = [root / p for p in OFFICIAL] + list((root / 'artifacts').glob('*'))
    files += [root / 'local_data/base_longitudinal.jsonl', root / 'local_data/base_longitudinal.csv']
    files += list((root / 'local_data').glob('*coorte*'))
    files += [root / 'docs/contrato_metodologico.md', root / 'docs/registro_decisoes.md']
    return {p.relative_to(root).as_posix(): sha256_file(p) for p in sorted(set(files)) if p.is_file()}


def validate_artifacts(root):
    m = json.loads((root / METRICS).read_text(encoding='utf-8'))
    if m['schema_version'] != 1 or set(m['perguntas']) != {str(i) for i in range(1, 12)}:
        raise ValueError('Schema das análises inválido')
    if m['input_hashes'] != input_hashes(root):
        raise ValueError('Entradas das análises alteradas')
    sources = {f['relative_path']: f['sha256'] for f in find_source_files(root / 'DATATHON')}
    if m['source_hashes'] != sources:
        raise ValueError('Fontes das análises alteradas')
    for p, digest in {**m['output_hashes'], **m['code_hashes']}.items():
        if sha256_file(root / p) != digest:
            raise ValueError('Saída ou código das análises divergente: ' + p)
    if m['modelo'] != official_model(root):
        raise ValueError('Métricas oficiais divergentes')
    if public_text_issues((root / REPORT).read_text(encoding='utf-8')):
        raise ValueError('Relatório não portátil')
    return {'analises_11_perguntas': True, 'analises_figuras': len(m['figuras']),
            'analises_hashes_preservados': True, 'analises_modelo_oficial_preservado': True}


def main():
    from relatorio_analises import render_report, figures
    before = input_hashes(ROOT)
    sources = {f['relative_path']: f['sha256'] for f in find_source_files(ROOT / 'DATATHON')}
    results = analyze(load_prepared(ROOT))
    model = official_model(ROOT)
    figs = figures(ROOT, results, model)
    report = render_report(results, model, figs)
    (ROOT / REPORT).write_text(report, encoding='utf-8')
    if before != input_hashes(ROOT) or sources != {f['relative_path']: f['sha256'] for f in find_source_files(ROOT / 'DATATHON')}:
        raise ValueError('Entradas alteradas durante as análises')
    payload = {'schema_version': 1, 'command': 'python src/analises_negocio.py',
        'perguntas': {str(i): title for i, title in enumerate(('IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'INDE', 'Modelo', 'Pedras', 'Insights'), 1)},
        'privacidade': {'minimo_perfil': MIN_PROFILE, 'particoes_pequenas': 'supressao integral'},
        'analises': results, 'modelo': model, 'figuras': figs, 'input_hashes': before, 'source_hashes': sources,
        'code_hashes': {p: sha256_file(ROOT / p) for p in ('src/analises_negocio.py', 'src/relatorio_analises.py', 'tests/test_analises_negocio.py')},
        'output_hashes': {p: sha256_file(ROOT / p) for p in [REPORT, *figs]}}
    (ROOT / METRICS).write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    validate_artifacts(ROOT)
    print(f'Análises concluídas: 11 perguntas, {len(figs)} figuras; entradas preservadas.')


if __name__ == '__main__':
    main()
