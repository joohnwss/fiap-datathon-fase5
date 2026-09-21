"""Relatório e figuras públicas derivados exclusivamente de agregados."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analises_negocio import INDICATORS, STONES


def fmt(x):
    if x is None:
        return '—'
    if isinstance(x, float):
        return f'{x:.3f}'
    return str(x)


def table(headers, rows):
    def cell(value):
        return fmt(value).replace('|', r'\|').replace('\n', ' ')
    return '| ' + ' | '.join(headers) + ' |\n|' + '|'.join([' --- '] * len(headers)) + '|\n' + '\n'.join('| ' + ' | '.join(cell(v) for v in row) + ' |' for row in rows) + '\n\n'


def stats_table(groups):
    return table(['Grupo', 'Total', 'n observado', 'Ausentes', 'Cobertura', 'Média', 'Mediana', 'DP', 'Q25', 'Q75', 'Estado'],
                 [[k, *[s.get(v) for v in ('total', 'n', 'ausentes', 'cobertura', 'media', 'mediana', 'dp', 'q25', 'q75')], s['status']] for k, s in groups.items()])


def corr_table(groups):
    return table(['Grupo / associação', 'n pares', 'Total', 'Ausentes no par', 'Spearman', 'Direção', 'Intensidade', 'Estado'],
                 [[k, *[s.get(v) for v in ('n', 'total', 'ausentes_par', 'rho', 'direcao', 'intensidade', 'status')]] for k, s in groups.items()])


def dist_table(groups):
    rows = []
    for group, d in groups.items():
        if 'contagens' not in d:
            rows.append([group, d['status'], None, None, None])
        else:
            rows += [[group, k, n, d['denominador'], 100 * d['proporcoes'][k] if d['denominador'] else None] for k, n in d['contagens'].items()]
    return table(['Grupo', 'Categoria', 'n', 'Denominador', '%'], rows)


def figures(root, a, model):
    target = root / 'reports/figures'
    target.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.prop_cycle': plt.cycler(color=['#236A80', '#C88A36', '#748557', '#95658B'])})
    paths = []
    def save(fig, name, note='Fonte: base longitudinal validada. Somente agregados; células pequenas suprimidas.'):
        fig.text(.02, .015, note, fontsize=8, color='#505050')
        fig.tight_layout(rect=(0, .05, 1, 1))
        p = target / (name + '.png'); fig.savefig(p, dpi=180); plt.close(fig)
        paths.append(p.relative_to(root).as_posix())
    years = list(a['anuais'])
    fig, ax = plt.subplots(figsize=(10, 5))
    bottom = np.zeros(len(years))
    for cat, label in [('sem_defasagem', 'Sem defasagem'), ('moderada', 'Moderada'), ('severa', 'Severa')]:
        v = [100 * a['anuais'][y]['categorias'].get('proporcoes', {}).get(cat, np.nan) for y in years]
        ax.bar(years, v, bottom=bottom, label=label); bottom += np.nan_to_num(v)
    ax.set_xticks(range(len(years)), years)
    for i, y in enumerate(years):
        if 'proporcoes' not in a['anuais'][y]['categorias']:
            ax.text(i, 50, 'Detalhamento\nsuprimido', ha='center', color='#505050')
    ax.set_xlim(-.5, len(years)-.5)
    ax.set(title='Adequação: composição anual da defasagem', ylabel='% dos registros do ano', xlabel='Ano de referência'); ax.legend(loc='lower right')
    save(fig, '01_defasagem')
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for y in years:
        s = a['anuais'][y]['indicadores']['ida']; axes[0].errorbar([y], [s['media']], yerr=[s['dp']], fmt='o', capsize=5, label=f"{y}: n={s['n']}")
        vals = a['ida_fase'][y]; axes[1].plot(list(vals), [v.get('media', np.nan) for v in vals.values()], 'o-', label=y)
    axes[0].set(title='IDA anual: média e desvio padrão', ylabel='IDA', xlabel='Ano'); axes[0].legend()
    axes[1].set(title='IDA médio por fase educacional', xlabel='Código da fase', ylabel='IDA'); axes[1].legend()
    save(fig, '02_ida', 'Barras: dispersão (DP), não intervalo de confiança. Fase não é Pedra; equivalência curricular não confirmada.')
    fig, ax = plt.subplots(figsize=(11, 5))
    labels = list(a['associacoes'][years[0]])
    for i, y in enumerate([*years, 'ajustado_ano']):
        ax.bar(np.arange(len(labels)) + (i-1.5)*.19, [a['associacoes'][y][k].get('rho', np.nan) for k in labels], .19, label=y.replace('ajustado_ano', 'Ajustado por ano'))
    ax.set_xticks(range(len(labels)), [s.upper() for s in labels]); ax.set(ylabel='Correlação de postos', title='Engajamento e autoavaliação: associações observadas', ylim=(-1, 1)); ax.axhline(0, color='gray', lw=.8); ax.legend()
    save(fig, '03_associacoes', 'n de pares e ausências no relatório. Ajuste: resíduos dos postos após remoção da média de cada ano.')
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, k in zip(axes, ('ida', 'ieg')):
        for i, (t, data) in enumerate(a['longitudinal'].items()):
            vals=data['ips'][k]['delta_por_ips']
            ax.bar(np.arange(len(vals)) + (i-.5)*.35, [v.get('media', np.nan) for v in vals.values()], .35, label=t)
        ax.set_xticks([0,1], ['IPS abaixo da mediana', 'IPS na mediana ou acima'], rotation=10)
        ax.set(title=f'IPS de origem e mudança futura de {k.upper()}', ylabel='Mudança média (destino − origem)'); ax.axhline(0,color='gray'); ax.legend()
    save(fig, '04_ips', 'Somente pares com IPS na origem e indicador nos dois anos. Mediana calculada em cada amostra de pares válidos.')
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, y in enumerate(('2023', '2024')):
        vals=a['ipp'][y]['por_categoria']; ax.bar(np.arange(len(vals))+(i-.5)*.35, [v.get('media',np.nan) for v in vals.values()], .35, label=y)
    ax.set_xticks(range(len(vals)), list(vals)); ax.set(title='IPP médio por adequação registrada', ylabel='IPP', xlabel='Categoria documental de defasagem'); ax.legend()
    save(fig, '05_ipp', 'IPP/2022 estruturalmente ausente. Barras omitidas: supressão primária/complementar. Categorias do D registrado, sem diagnóstico.')
    fig, ax = plt.subplots(figsize=(10, 5))
    keys=['ida','ieg','iaa','ips','ipp']
    for i,y in enumerate(years):
        ax.bar(np.arange(5)+(i-1)*.25,[a['ipv'][y]['associacoes'].get(k,{}).get('rho',np.nan) for k in keys],.25,label=y)
    ax.set_xticks(range(5),[k.upper() for k in keys]); ax.set(title='IPV: associações contemporâneas por ano', ylabel='Spearman', ylim=(-1,1)); ax.legend()
    save(fig, '06_ipv', 'Associações descritivas; n de pares no relatório. IPP não observado em 2022. Não indica influência causal.')
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    for ax,y in zip(axes,years):
        profiles=sorted(a['inde'][y]['perfis_publicados'].items(),key=lambda item:item[1]['media'])
        selected=profiles[:2]+profiles[-2:]
        labels=[p.replace(' alto','↑').replace(' baixo','↓').replace(' / ',' ') for p,s in selected]
        ax.barh(range(len(selected)),[s['media'] for p,s in selected]); ax.set_yticks(range(len(selected)),labels,fontsize=8)
        ax.set(title=y,xlabel='INDE médio',xlim=(0,10))
    fig.suptitle('Combinações observadas: dois menores e dois maiores INDE médios')
    save(fig,'07_inde','↑: na mediana ou acima; ↓: abaixo da mediana anual dos casos completos. n ≥ 10; composição matemática, sem causalidade.')
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for i,y in enumerate(years):
        vals=a['pedras'][y]['indicadores']; axes[0].bar(np.arange(4)+(i-1)*.25,[vals[p]['ida'].get('media',np.nan) for p in STONES],.25,label=y)
    axes[0].set_xticks(range(4),STONES); axes[0].set(title='IDA médio por Pedra observada',ylabel='IDA'); axes[0].legend()
    for i,(t,s) in enumerate(a['longitudinal'].items()):
        d=s['pedras_evolucao']; axes[1].bar(np.arange(3)+(i-.5)*.35,[100*d.get('proporcoes',{}).get(k,np.nan) for k in ('melhoria','estabilidade','piora')],.35,label=t)
    axes[1].set_xticks(range(3),['Melhoria','Estabilidade','Piora']); axes[1].set(title='Mudança de Pedra nos correspondidos',ylabel='% dos pares com Pedra válida'); axes[1].legend()
    save(fig,'08_pedras','Pedras são classificações de desempenho. Não há grupo de controle; transições não demonstram impacto causal.')
    fig,ax=plt.subplots(figsize=(10,5)); keys=['average_precision','roc_auc','precisao','recall','f1','brier']
    for i,k in enumerate(('oof','temporal')):
        ax.bar(np.arange(6)+(i-.5)*.35,[model[k][v] for v in keys],.35,label=f"{k}: n={model[k]['n']}, eventos={model[k]['eventos']}")
    ax.set_xticks(range(6),['AP','ROC-AUC','Precisão','Recall','F1','Brier']); ax.set(title='Modelo avaliado: métricas oficiais com limiar congelado',ylabel='Valor',ylim=(0,1)); ax.legend()
    save(fig,'09_modelo','Artefatos oficiais, sem nova avaliação. Brier: menor é melhor. OOF pós-seleção não substitui teste temporal.')
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for y in years:
        axes[0].plot([k.upper() for k in INDICATORS],[100*a['anuais'][y]['indicadores'][k].get('cobertura',np.nan) for k in INDICATORS],'o-',label=y)
    axes[0].set(title='Disponibilidade dos indicadores',ylabel='% dos registros anuais',ylim=(-5,105)); axes[0].legend()
    vals=model['distribuicao']['numericos']; axes[1].barh([k.upper() for k in vals],[v['diferenca_padronizada'] for v in vals.values()]); axes[1].axvline(0,color='gray'); axes[1].set(title='Mudança entre coortes oficiais',xlabel='Diferença padronizada (teste − desenvolvimento)')
    save(fig,'10_insights','Cobertura não é desempenho. Diferenças entre coortes reproduzidas dos artefatos oficiais; sem ajuste do modelo.')
    return paths


def render_report(a, m, figs):
    text = ['# Análises das perguntas de negócio — FIAP Datathon Fase 5\n\n',
        'Documento regenerável por `python src/analises_negocio.py`. Base: registros anuais de 2022–2024; os totais anuais não representam alunos únicos. A leitura, os estados de ausência, os indicadores, as fases e a defasagem são os da preparação validada. Nenhum indicador foi recomposto.\n\n',
        'As análises são observacionais: sem grupo de controle ou contrafactual, não identificam efeito causal. “Ao longo do ano” é interpretado como comparação entre anos de referência. Fase educacional e Pedra são variáveis distintas. Códigos 8 e 9 permanecem nas descrições, com limitações de aplicabilidade e equivalência curricular.\n\n',
        'Privacidade: perfis e correlações requerem pelo menos 10 observações válidas. Uma partição com célula não vazia menor que 10 é integralmente suprimida, inclusive margens. Médias, medianas, quartis e desvio padrão usam somente valores disponíveis; zero observado é preservado. Não há imputação. DP descreve dispersão, não incerteza da média. Detalhes complementares estão em [métricas estruturadas](metricas_analises_negocio.json).\n\n',
        'Spearman usa pares completos, postos médios para empates e informa n. Intensidade descritiva: |ρ| < 0,3 fraca; 0,3–<0,6 moderada; ≥0,6 forte. Esses cortes não são testes de hipótese. O agregado ajustado por ano correlaciona resíduos de postos globais após retirar a média dos postos de cada ano; não é média das correlações anuais. A repetição de estudantes e comparações exploratórias impedem tratar associações como evidência independente ou causal. Não foram calculados p-valores ou novos intervalos.\n\n']
    matrix=[]
    def section(n,title,method,evidence,interpretation,limitation,recommendation,fig=None):
        text.append(f'## {n}. {title}\n\n**Pergunta.** {title}\n\n**Método.** {method}\n\n**Evidências quantitativas.**\n\n{evidence}')
        text.append(f'**Interpretação.** {interpretation}\n\n**Limitação.** {limitation}\n\n**Recomendação.** {recommendation}\n\n')
        if fig is not None:
            text.append(f'![{title}]({Path(fig).relative_to("reports").as_posix()})\n\n')
        matrix.append([str(n),interpretation,method,limitation,recommendation])
    annual=a['anuais']; years=list(annual)
    first,last=annual[years[0]],annual[years[-1]]
    p1='; '.join(f"{y}: {100*s['categorias']['proporcoes']['moderada']:.1f}% moderada e {100*s['categorias']['proporcoes']['severa']:.1f}% severa" for y,s in annual.items() if 'proporcoes' in s['categorias'])
    p1 += '. Anos com detalhamento suprimido não autorizam concluir ausência de defasagem severa'
    e=dist_table({y:s['categorias'] for y,s in annual.items()})+dist_table({y:s['sinal_d'] for y,s in annual.items()})+dist_table({y:s['ian_distribuicao'] for y,s in annual.items()})+ 'Divergência IAN registrado versus esperado (True = divergente):\n\n'+dist_table({y:s['ian_divergencias'] for y,s in annual.items()})
    section(1,'Qual é o perfil de defasagem e como evolui?', 'Distribuições anuais; D≥0 sem defasagem, −2≤D<0 moderada, D<−2 severa. IAN esperado: 10, 5 e 2,5, respectivamente, conforme regra documental já aplicada.',e,p1+'.','IAN incorpora D; sua associação com adequação é matemática. Divergências são sinalizadas, sem correção. Mudanças de composição impedem inferir evolução individual pelas proporções.','Priorizar acompanhamento pedagógico da defasagem e revisar divergências na origem, mantendo o valor registrado.',figs[0])
    e=stats_table({y:s['indicadores']['ida'] for y,s in annual.items()})
    e+=stats_table({f'{y} / fase {f}':s for y,g in a['ida_fase'].items() for f,s in g.items()})
    e+='Mudança do mesmo estudante (destino − origem):\n\n'+stats_table({t:s['mudancas']['ida'] for t,s in a['longitudinal'].items()})
    p2='IDA médio anual: '+ '; '.join(f"{y}: {s['indicadores']['ida']['media']:.2f}" for y,s in annual.items())+'. Nos pares: '+ '; '.join(f"{t}: mudança média {s['mudancas']['ida']['media']:+.2f} (n={s['mudancas']['ida']['n']})" for t,s in a['longitudinal'].items())+'.'
    section(2,'O IDA melhora, permanece estável ou cai entre fases e anos?','Média, mediana, DP e quartis por ano, fase e ano × fase. Mudanças individuais apenas nos pares com IDA nos dois anos.',e,p2,'Fases agregadas misturam anos e estudantes repetidos. Códigos não provam equivalência curricular; dispersão não é intervalo de confiança.','Monitorar IDA e cobertura por fase, distinguindo composição da turma e progresso dos acompanhados.',figs[1])
    for n,prefix,title,limit,rec in [(3,'ieg','Qual a associação de IEG com IDA e IPV?','Associação contemporânea pode refletir contexto comum e mecanismos de avaliação.','Acompanhar engajamento junto ao desempenho, sem usar correlação como efeito de intervenção.'),(4,'iaa','A autoavaliação IAA é coerente com IDA e IEG?','Indicadores não medem o mesmo construto; diferença de pontos não é erro de percepção ou diagnóstico.','Usar discrepâncias como tema de escuta pedagógica e revisar a comparabilidade dos instrumentos.')]:
        selected={f'{y} / {k}':s for y,g in a['associacoes'].items() for k,s in g.items() if k.startswith(prefix)}
        e=corr_table(selected)
        if n==4: e+=stats_table({f'{y} / {k}':s for y,g in a['autoavaliacao'].items() for k,s in g.items()})
        p='; '.join(f"{k}: ρ={s['rho']:.2f} ({s['intensidade']}, n={s['n']})" for k,s in selected.items() if k.startswith('ajustado_ano') and s.get('rho') is not None)+'.'
        if n==4: p+=' Coerência é descrita por ordenação e diferença assinada IAA − indicador; não há classificação de alunos como coerentes/incoerentes.'
        section(n,title,'Spearman anual e ajustado por ano; para IAA, diferenças assinadas entre escalas, sem corte diagnóstico.',e,p,limit,rec,figs[2] if n==3 else None)
    e=corr_table({f'{t} / IPS → Δ{k.upper()}':v['associacao'] for t,s in a['longitudinal'].items() for k,v in s['ips'].items()})
    e+=stats_table({f'{t} / Δ{k.upper()}':v for t,s in a['longitudinal'].items() for k,v in s['mudancas'].items()})
    e+=dist_table({f'{t} / {k.upper()} / Δ < −{c}':d for t,s in a['longitudinal'].items() for k,v in s['ips'].items() for c,d in v['sensibilidade'].items()})
    e+=stats_table({f'{t} / {k.upper()} / corte {c} / {label}':d for t,s in a['longitudinal'].items() for k,v in s['ips'].items() for c,g in v['perfis'].items() for label,d in g.items()})
    p5='; '.join(f"{t}, Δ{k.upper()}: ρ={v['associacao'].get('rho',0):.2f}" for t,s in a['longitudinal'].items() for k,v in s['ips'].items())+'. Os cortes complementam a mudança contínua e não definem queda clinicamente relevante.'
    p5 += ' As correlações contínuas próximas de zero não sustentam um padrão monotônico útil de antecedência nesta base; isso não exclui relações não lineares ou dependentes do contexto.'
    section(5,'Existem padrões de IPS que antecedem quedas futuras de IDA ou IEG?','RA único nos dois anos. IPS na origem versus Δ = destino − origem. Definição prévia: queda Δ<0; sensibilidade Δ<−0,5 e Δ<−1 ponto. Cada taxa exige IPS e indicador nos dois anos.',e,p5,'Antecedência temporal não estabelece causa; regressão à média, cobertura, contexto e instrumentos podem explicar mudanças. Cortes são descritivos.','Acompanhar IPS e mudanças futuras em conjunto, registrar alterações de instrumento e não criar triagem automática pelo IPS.',figs[3])
    e=corr_table({f'{y} / {k}':s for y,g in a['ipp'].items() if y!='2022' for k,s in g.items() if k in ('ipp x ian','ipp x d')})
    e+=stats_table({f'{y} / {c}':s for y,g in a['ipp'].items() if y!='2022' for c,s in g['por_categoria'].items()})
    e+=dist_table({y:g['perfis'] for y,g in a['ipp'].items() if y!='2022'})
    e+='Medianas anuais de IPP nos pares com D: '+ '; '.join(f"{y}: {g['mediana_ipp']:.3f}" for y,g in a['ipp'].items() if y!='2022')+'.\n\n'
    p6='; '.join(f"{y}, IPP × IAN: ρ={g['ipp x ian']['rho']:.2f}" for y,g in a['ipp'].items() if y!='2022')+'. Não se exige concordância perfeita entre adequação escolar e avaliação psicopedagógica.'
    section(6,'IPP confirma ou contradiz a defasagem identificada por IAN?','Somente 2023/2024. Contraste descritivo: IPP abaixo da mediana e D<0, ou IPP na mediana/acima e D≥0, são perfis alinhados; as combinações restantes são contrastantes. Não há padrão clínico de referência.',e,p6,'IPP/2022 é ausência estrutural, nunca zero. Mediana é relativa ao ano; alinhamento não valida diagnóstico. IAN e D têm relação matemática.','Investigar perfis contrastantes com a equipe pedagógica e preservar cobertura e contexto de avaliação.',figs[4])
    e=corr_table({f'{y} / {k.upper()} × IPV':s for y,g in a['ipv'].items() for k,s in g['associacoes'].items()})
    e+=stats_table({f'{y} / fase {f} / IPV':s for y,g in a['ipv'].items() for f,s in g['por_fase'].items()})
    e+=corr_table({f'{t} / {k.upper()} origem × IPV destino':s for t,g in a['longitudinal'].items() for k,s in g['ipv_futuro'].items()})
    p7='; '.join(f"{y}: maior |ρ| contemporâneo em {max(g['associacoes'],key=lambda k:abs(g['associacoes'][k].get('rho') or 0)).upper()}" for y,g in a['ipv'].items())+'. O ranking é descritivo e pode mudar entre anos e no horizonte futuro.'
    section(7,'Quais indicadores estão mais associados ao IPV?','Spearman por ano e indicadores na origem versus IPV no destino; contexto por fase. Sem regressão explicativa adicional.',e,p7,'As correlações não isolam efeitos próprios dos indicadores nem ajustam todas as diferenças por fase. IPV também integra o INDE.','Monitorar os indicadores associados em conjunto e avaliar mudanças de instrumento antes de interpretar tendências.',figs[5])
    e='Alto/baixo usa mediana dos casos completos do ano; empates pertencem ao grupo alto. IPP omitido somente em 2022.\n\n'
    for y,g in a['inde'].items():
        e+=f"Ano {y}: {g['n_completos']}/{g['total']} casos completos. Medianas: "+', '.join(f'{k.upper()}={v:.3f}' for k,v in g['medianas'].items())+'.\n\n'+stats_table(g['perfis_publicados'])
    p8='; '.join(f"{y}: maior média publicável {max(g['perfis_publicados'].values(),key=lambda s:s['media'])['media']:.2f}, perfil {max(g['perfis_publicados'],key=lambda k:g['perfis_publicados'][k]['media'])}" for y,g in a['inde'].items())+'.'
    section(8,'Quais combinações de IDA, IEG, IPS e IPP se associam a maior INDE?','Perfis binários anuais em casos completos, com pelo menos 10 observações; todos os perfis publicáveis no quadro.',e,p8,'Circularidade: INDE combina esses indicadores com IAN, IAA e IPV; pesos/aplicabilidade diferem por fase. Não se recalcula a fórmula, nem se interpreta associação como descoberta causal. Perfis anuais não são diretamente equivalentes.','Usar perfis para descrição multidimensional; evitar priorizar um componente apenas por sua associação matemática ao INDE.',figs[6])
    keys=['n','eventos','average_precision','roc_auc','precisao','recall','f1','brier']
    e=table(['População','n','Eventos','AP','ROC-AUC','Precisão','Recall','F1','Brier'],[[k,*[m[k][v] for v in keys]] for k in ('oof','temporal')])
    e+=table(['Métrica','IC95% temporal inferior','Superior'],[[k,*v['ic95']] for k,v in m['intervalos']['completo'].items()])
    e+=f"Modelo: **{m['modelo']}**; limiar congelado: **{m['limiar']}**. Preditores: "+', '.join('`'+p+'`' for p in m['preditores'])+'.\n\n'
    e+=f"Matriz temporal [[VN, FP], [FN, VP]]: `{m['temporal']['matriz_confusao']}`. AP/ROC-AUC/Brier usam todos os observados; recall usa eventos, precisão usa sinalizados e F1 combina precisão/recall.\n\n"
    e+=table(['Preditor numérico', 'Coeficiente log-odds por DP do desenvolvimento'],
             [[k.removeprefix('numericos__'), v] for k,v in m['interpretabilidade']['valores'].items() if k.startswith('numericos__')])
    e+='Coeficientes oficiais condicionais: valores positivos se associam a maior escore e negativos a menor escore, mantendo as demais variáveis do modelo. Não demonstram causas; correlação entre preditores limita sua interpretação isolada. Fase é categórica e não tem coeficiente numérico único.\n\n'
    p9=f"Recall cai de {m['oof']['recall']:.1%} no OOF para {m['temporal']['recall']:.1%} no teste ({100*m['diferencas']['recall']:.1f} pontos percentuais). A meta interna não se mantém no ano seguinte."
    section(9,'Como o modelo avaliado apoia a previsão de risco?','Leitura exclusiva das métricas, relatório, schema e configuração oficiais; sem treino, novas previsões ou reabertura da avaliação. ICs oficiais: bootstrap percentil, 2.000 reamostragens, semente 42, unidade transição/aluno do teste, pipeline e limiar fixos.',e,p9,'Desenvolvimento pequeno, único teste temporal, perdas e sobreposição de estudantes. OOF após seleção tem otimismo. O alvo é entrada em defasagem entre elegíveis, não qualquer queda de desempenho.','Usar como apoio à revisão humana, monitorando cobertura e falsos negativos. Modelo operacional futuro terá identificação própria; não foi criado nesta etapa.',figs[8])
    e=dist_table({y:g['distribuicao'] for y,g in a['pedras'].items()})
    e+=stats_table({f'{y} / {p} / {k.upper()}':s for y,g in a['pedras'].items() for p,values in g['indicadores'].items() for k,s in values.items()})
    e+=dist_table({t:g['pedras_evolucao'] for t,g in a['longitudinal'].items()})
    e+=dist_table({t:g['pedras_transicoes'] for t,g in a['longitudinal'].items()})
    e+=stats_table({f'{t} / {p} / ΔIDA':s for t,g in a['longitudinal'].items() for p,s in g['ida_por_pedra_origem'].items()})
    p10='; '.join(f"{t}: melhoria de Pedra {100*g['pedras_evolucao']['proporcoes']['melhoria']:.1f}%, piora {100*g['pedras_evolucao']['proporcoes']['piora']:.1f}%" for t,g in a['longitudinal'].items() if 'proporcoes' in g['pedras_evolucao'])+'.'
    section(10,'O que os indicadores mostram sobre evolução nas Pedras?','Pedras observadas na ordem Quartzo, Ágata, Ametista, Topázio; normalização apenas das grafias Ágata/agata. Não se recalculam faixas. Transições exigem classificação reconhecida nos dois anos.',e,p10,'Sem controle ou contrafactual, evolução não confirma impacto do programa. Pedra deriva do desempenho/INDE; faixas documentais divergem. Matriz detalhada pode ser suprimida por células pequenas.','Acompanhar permanência, regressões e avanços junto à cobertura, sem confundir Pedra com fase escolar.',figs[7])
    e=dist_table({t:g['distribuicao'] for t,g in a['perdas'].items()})
    e+=dist_table({t:g['desfecho'] for t,g in a['perdas'].items()})
    e+=stats_table({f'{t} / {group} / {k.upper()}':s for t,g in a['perdas'].items() for group,values in g['perfis'].items() for k,s in values.items()})
    e+=stats_table({f'{t} / {group} / D origem':s for t,g in a['perdas'].items() for group,s in g['defasagem'].items()})
    e+=dist_table({f'{t} / {group} / fase':s for t,g in a['perdas'].items() for group,s in g['fases'].items()})
    e+=stats_table({f'{y} / {k.upper()}':s for y,g in annual.items() for k,s in g['indicadores'].items()})
    e+=table(['Preditor','Média desenvolvimento','Média teste','Diferença padronizada','Ausentes desenvolvimento','Ausentes teste'],[[k,*[v[x] for x in ('media_desenvolvimento','media_teste','diferenca_padronizada','ausentes_desenvolvimento','ausentes_teste')]] for k,v in m['distribuicao']['numericos'].items()])
    p11='; '.join(f"{t}: {g['distribuicao']['contagens']['nao_encontrados']}/{g['distribuicao']['denominador']} elegíveis sem correspondência futura" for t,g in a['perdas'].items())+'. Maior deslocamento padronizado absoluto entre coortes em '+max(m['distribuicao']['numericos'],key=lambda k:abs(m['distribuicao']['numericos'][k]['diferenca_padronizada'])).upper()+'.'
    phase_values = {k:v['media'] for k,v in a['ida_fase'][years[-1]].items() if v.get('media') is not None}
    low, high = min(phase_values, key=phase_values.get), max(phase_values, key=phase_values.get)
    p11 += f' Em {years[-1]}, as médias publicáveis de IDA variam de {phase_values[low]:.2f} na fase {low} a {phase_values[high]:.2f} na fase {high}, indicando heterogeneidade descritiva, sem comparação causal entre fases.'
    section(11,'Quais insights adicionais orientam coleta e monitoramento?','Perdas entre elegíveis da origem, perfis encontrados/não encontrados, cobertura anual, heterogeneidade por fase (pergunta 2) e distribuição das coortes oficiais.',e,p11,'Ausência de correspondência não prova evasão, sucesso ou fracasso. Mudanças de distribuição não demonstram a causa da queda de recall. Indicadores e composição podem ter mudado.','Registrar motivo de saída e calendário de avaliação; padronizar instrumentos e definições por fase; monitorar disponibilidade e perdas a cada ciclo. Revisar casos com a equipe e planejar validação prospectiva separada, sem ajustar retroativamente o modelo.',figs[9])
    text.append('## Matriz de síntese\n\n')
    text.append(table(['Pergunta','Evidência principal','Conclusão responsável','Limitação','Recomendação'],[[r[0],r[1], 'Evolução/associação observada; sem inferência causal.' if r[0]!='9' else 'Discriminação temporal não garante sensibilidade operacional.',r[3],r[4]] for r in matrix]))
    text.append('## Fontes e reprodução\n\n[Contrato metodológico](../docs/contrato_metodologico.md), [evidências documentais](../docs/evidencias_documentais.md), [coortes](relatorio_coortes_modelagem.md), [modelo oficial](relatorio_modelagem.md), [schema](../artifacts/schema_modelo.json) e [configuração congelada](../artifacts/configuracao_congelada.json). As métricas estruturadas registram hashes das fontes, entradas, código e saídas, com caminhos relativos.\n')
    return ''.join(text)
