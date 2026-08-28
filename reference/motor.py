# -*- coding: utf-8 -*-
"""
Vaga Certa - Case 2 (SIEng 2026 / PUC-Rio)
Motor de previsao de ocupacao: carro (15 PDFs MBS32) + bike (bicicletario).

Gera baseline.json (o prior plugavel) e app.html (demo offline).
Rode:  python motor.py
"""
import json, re, subprocess, sys, unicodedata
from pathlib import Path
import pandas as pd

CAP_CARRO = 360          # rotativo: 280 garagem + 80 laje (capacidade_estacionamento.md)
DIAS = {'17': 'Segunda', '18': 'Terca', '19': 'Quarta', '20': 'Quinta', '21': 'Sexta'}
ORDEM = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta']


def achar_dados():
    """Acha data/case2_vagas_carona esteja o script no repo ou solto."""
    aqui = Path(__file__).resolve().parent
    cands = [aqui / 'data' / 'case2_vagas_carona',
             aqui.parent.parent / 'data' / 'case2_vagas_carona',
             Path(r"C:\Users\Igor Peres\OneDrive - puc-rio.br\Claude\Projects"
                  r"\Impact Lab\SIEng\impact-lab-sieng2026\data\case2_vagas_carona")]
    for c in cands:
        if (c / 'estacionamento').is_dir():
            return c
    sys.exit('ERRO: nao achei data/case2_vagas_carona. Rode de dentro do repo.')


DADOS = achar_dados()
EST = DADOS / 'estacionamento'
BIKE = DADOS / 'bicicletario'
ALUNOS = DADOS.parent / 'case1_oportunidades' / 'alunos.csv'


# ---------------------------------------------------------------- PDFs (carro)
def linhas_pdf(pdf):
    """PEGADINHA: o relatorio e uma tabela de largura fixa. Sem -layout as colunas
    colam. Cada linha de hora vira 13 inteiros; interessa Total Entradas (indice
    10) e Total Saidas (indice 11)."""
    txt = subprocess.run(['pdftotext', '-layout', str(pdf), '-'],
                         capture_output=True).stdout.decode('latin-1')
    out = {}
    for ln in txt.splitlines():
        m = re.match(r'\s*(\d{2}):00 a \d{2}:59\s+(.*)$', ln)
        if m:
            out[int(m.group(1))] = [int(x) for x in re.findall(r'-?\d+', m.group(2))]
    return out


def curva_carro():
    """PEGADINHA: os 15 nomes de arquivo tem caixa e espacamento inconsistentes
    ('Saida ac06', 'SaidaAc06', 'Saida Ac06'). O que separa entrada de saida com
    seguranca e o parenteses no nome, nao o texto."""
    por_dia = {}
    for pdf in sorted(EST.glob('*.pdf')):
        d = re.match(r'(\d+) de [Aa]gosto', pdf.name).group(1)
        por_dia.setdefault(d, []).append(pdf)

    dias, det = {}, []
    for d in sorted(por_dia, key=int):
        ent, sai = [0] * 24, [0] * 24
        for pdf in por_dia[d]:
            r = linhas_pdf(pdf)
            if '(' in pdf.name:                       # relatorio de SAIDA
                for h, v in r.items():
                    sai[h] += v[11]
            else:                                     # relatorio de ENTRADA
                for h, v in r.items():
                    ent[h] = v[10]

        E, X = sum(ent), sum(sai)
        # PEGADINHA CENTRAL: sai mais carro do que entra, TODO dia. Falta o
        # relatorio de pelo menos uma cancela de entrada -> nao existe ocupacao
        # absoluta exata. Por isso o numero sai como faixa [piso, teto].
        k = X / E              # ancora: o rotativo fecha as 23h e esvazia

        def acumula(escala):
            c, o = 0, []
            for h in range(24):
                c += escala * ent[h] - sai[h]
                # sem o max() o piso vira negativo a tarde: e o deficit da cancela
                # que falta se acumulando, nao carro que sumiu.
                o.append(max(c, 0))
            return o

        piso = [round(x) for x in acumula(1)]
        teto = [round(x) for x in acumula(k)]
        nome = DIAS[d]
        dias[nome] = {'entradas': ent, 'saidas': sai, 'piso': piso, 'teto': teto,
                      'k': round(k, 3), 'total_entradas': E, 'total_saidas': X}
        det.append((nome, E, X, k, max(piso), piso.index(max(piso)),
                    max(teto), teto.index(max(teto)),
                    sum(ent[6:12]), sum(ent[13:19])))
    return dias, det


# ------------------------------------------------------------- bike + backtest
def curva_bike():
    o = pd.read_csv(BIKE / 'ocupacao_estimada.csv')
    prior = o.groupby(['dia_semana', 'hora']).bicicletas_no_bicicletario.median()
    por_dia = {}
    for dia in ORDEM:
        if dia in prior.index.get_level_values(0):
            s = prior.loc[dia]
            por_dia[dia] = [int(s.get(h, 0)) for h in range(24)]
    picos = o.groupby('data').bicicletas_no_bicicletario.max()
    return por_dia, {'max_observado': int(o.bicicletas_no_bicicletario.max()),
                     'p90_picos_diarios': int(picos.quantile(.9)),
                     'mediana_picos_diarios': int(picos.median()),
                     'dias': int(picos.size)}


def backtest():
    """Responde a pergunta do case: 'qual o erro aceitavel para o aluno confiar?'
    Backtest honesto no bicicletario, que tem 65 dias (o carro so tem 5)."""
    o = pd.read_csv(BIKE / 'ocupacao_estimada.csv').sort_values(['data', 'hora'])
    o['data'] = pd.to_datetime(o.data)
    forma = o.groupby(['dia_semana', 'hora']).bicicletas_no_bicicletario.median().rename('prior')
    o = o.join(forma, on=['dia_semana', 'hora'])
    nivel = (o.groupby('data').bicicletas_no_bicicletario.mean()
             / o.groupby('data').prior.mean()).shift(1).rolling(3, min_periods=1).mean()
    o['nivel'] = o.data.map(nivel)
    o['fundido'] = o.prior * o.nivel
    o['reporte'] = o.groupby('data').bicicletas_no_bicicletario.shift(1)
    o['prior_mais_reporte'] = .5 * o.prior + .5 * o.reporte

    t = o[o.hora.between(8, 19)].dropna(subset=['nivel', 'reporte'])
    real = t.bicicletas_no_bicicletario

    def m(col):
        e = (real - t[col]).abs()
        return {'mae': round(float(e.mean()), 1),
                'erro_mediano_pct': int(round(float((e / real.clip(lower=1)).median()) * 100)),
                'p90': int(round(float(e.quantile(.9))))}

    return {'n_observacoes': int(len(t)), 'janela': '8h-19h', 'dias': 65,
            'so_historico': m('prior'),
            'historico_x_nivel': m('fundido'),
            'historico_mais_1_reporte': m('prior_mais_reporte')}


# ------------------------------------------------------------------- carona
def norm(s):
    """PEGADINHA: 'Gavea' e 'Gavea' (com acento) sao bairros diferentes no dado.
    325 grafias colapsam para 298 bairros. Gavea esta partida em 4 e soma 107."""
    s = str(s).strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


PEDALAVEL = {'gavea', 'jardim botanico', 'leblon', 'ipanema', 'lagoa', 'botafogo',
             'humaita', 'copacabana', 'laranjeiras', 'flamengo', 'sao conrado', 'urca'}


def carona(chegadas_manha):
    a = pd.read_csv(ALUNOS)
    a['b'] = a.bairro.map(norm)
    vc = a.b.value_counts()
    tot = int(vc.sum())
    rotas = []
    for bairro, n in vc.head(12).items():
        # SUPOSICAO EXPLICITA: a distribuicao de bairro dos motoristas e a mesma
        # dos alunos cadastrados. O ticket nao tem vinculo com aluno (por design).
        carros = chegadas_manha * n / tot
        rotas.append({'bairro': bairro.title(), 'alunos': int(n),
                      'carros_pico_manha': round(carros, 1),
                      'grupos_de_3': int(carros // 3),
                      'pedalavel': bairro in PEDALAVEL})
    return rotas, {'bairros_crus': int(a.bairro.nunique()),
                   'bairros_normalizados': int(a.b.nunique()),
                   'alunos': tot}


# ------------------------------------------------------------------ planilha
def planilha():
    """A planilha soma TODAS as cancelas da PUC, nao so o rotativo -> serve para
    permanencia e recorrencia, NUNCA para ocupacao."""
    f = EST / 'FLUXO ESTACIONAMENTO PUC - 17 a 21 de Agosto.xlsx'
    if not f.exists():
        return None
    xl = pd.ExcelFile(f)
    quadros = []
    for aba in xl.sheet_names:
        cru = pd.read_excel(f, sheet_name=aba, header=None)
        # PEGADINHA: as 3 abas tem o cabecalho em linhas/colunas diferentes e a
        # aba '21 de Agosto' tem 9 colunas contra 10. header=0 quebra. Procuramos
        # a celula 'ID'.
        pos = None
        for i in range(min(6, len(cru))):
            for j, v in enumerate(cru.iloc[i]):
                if str(v).strip() == 'ID':
                    pos = (i, j)
                    break
            if pos:
                break
        if not pos:
            continue
        i, j = pos
        d = cru.iloc[i + 1:, j:].copy()
        d.columns = [str(c).strip() for c in cru.iloc[i, j:]]
        d = d[[c for c in d.columns if c and c != 'nan']]
        quadros.append(d)
    d = pd.concat(quadros, ignore_index=True)
    d = d[d.ID.notna()]

    rec = d.Ticket.value_counts()
    val = pd.to_numeric(d.Valor, errors='coerce')
    unico = rec[rec == 1].index
    return {'linhas': int(len(d)), 'tickets_distintos': int(d.Ticket.nunique()),
            'ticket_mais_frequente': str(rec.index[0]), 'aparicoes': int(rec.iloc[0]),
            'valor_medio_uso_unico': round(float(val[d.Ticket.isin(unico)].mean()), 2),
            'valor_medio_recorrente': round(float(val[~d.Ticket.isin(unico)].mean()), 2)}


# ---------------------------------------------------------------------- main
def main():
    print('Lendo 15 PDFs do MBS32...')
    dias, det = curva_carro()

    cab = ('dia'.ljust(9) + 'ent'.rjust(5) + 'sai'.rjust(5) + 'k'.rjust(6)
           + 'PISO'.rjust(6) + 'h'.rjust(3) + 'TETO'.rjust(6) + 'h'.rjust(3)
           + 'piso%'.rjust(7) + 'teto%'.rjust(7) + 'manha'.rjust(7)
           + 'tarde'.rjust(7) + 'raz'.rjust(6))
    print('\n' + cab)
    for n, E, X, k, pm, ph, tm, th, ma, ta in det:
        print(f'{n:<9}{E:>5}{X:>5}{k:>6.2f}{pm:>6}{ph:>3}{tm:>6}{th:>3}'
              f'{pm / CAP_CARRO * 100:>6.0f}%{tm / CAP_CARRO * 100:>6.0f}%'
              f'{ma:>7}{ta:>7}{ma / ta:>6.2f}')

    teto_max = max(max(v['teto']) for v in dias.values())
    margem = CAP_CARRO - teto_max
    print(f'\nCapacidade {CAP_CARRO} | teto no pico {teto_max} | MARGEM {margem} vagas '
          f'({margem / teto_max * 100:.1f}%)')
    print(f'A PUC perdeu 207 vagas desde 2023. Faltam {margem} para estourar.')

    mx = max(x['total_entradas'] for x in dias.values())
    vol = {n: round(d['total_entradas'] / mx, 2) for n, d in dias.items()}
    print('Fator de volume por dia:', vol)

    print('\nBicicletario...')
    bike, bike_cap = curva_bike()
    bt = backtest()
    print(f"  backtest {bt['n_observacoes']} obs | so historico "
          f"{bt['so_historico']['erro_mediano_pct']}% | +nivel "
          f"{bt['historico_x_nivel']['erro_mediano_pct']}% | +1 reporte "
          f"{bt['historico_mais_1_reporte']['erro_mediano_pct']}%")
    print(f"  capacidade instalada NAO esta no dado. max observado "
          f"{bike_cap['max_observado']} | p90 dos picos {bike_cap['p90_picos_diarios']}")

    chegadas = sum(sum(d['entradas'][6:12]) for d in dias.values()) / len(dias)
    rotas, binfo = carona(chegadas)
    print(f"\nCarona: {binfo['bairros_crus']} grafias -> "
          f"{binfo['bairros_normalizados']} bairros")
    for r in rotas[:6]:
        print(f"  {r['bairro']:<26}{r['alunos']:>5} alunos "
              f"{r['carros_pico_manha']:>6} carros {r['grupos_de_3']:>3} grupos "
              f"{'bike' if r['pedalavel'] else ''}")

    print('\nPlanilha (permanencia/recorrencia)...')
    pl = planilha()
    if pl:
        print(f"  {pl['linhas']} linhas, {pl['tickets_distintos']} tickets distintos")
        print(f"  ticket {pl['ticket_mais_frequente']} aparece {pl['aparicoes']}x "
              f"(acionamento de cancela, nao carro estacionando)")
        print(f"  uso unico R$ {pl['valor_medio_uso_unico']} x recorrente "
              f"R$ {pl['valor_medio_recorrente']}")

    base = {
        'meta': {'fonte': 'MBS32 Parking Manager + COBRA (bicicletario), DSI PUC-Rio',
                 'periodo_carro': '17-21/08/2026 (1a semana de aula de 2026.2)',
                 'periodo_bike': '04/05-31/07/2026 (2026.1)',
                 'capacidade_carro': CAP_CARRO,
                 'capacidade_bike': None,
                 'aviso': 'Semana de pico, nao media do semestre. A ocupacao do '
                          'carro e faixa [piso,teto]: falta o relatorio de uma '
                          'cancela de entrada.'},
        'carro': {n: {'piso': d['piso'], 'teto': d['teto'], 'entradas': d['entradas'],
                      'k_ancora': d['k']} for n, d in dias.items()},
        'bike': bike,
        'bike_capacidade': bike_cap,
        'fator_volume': vol,
        'backtest': bt,
        'carona': rotas,
        'bairros': binfo,
        'politica': {'teto_pico': teto_max, 'margem_vagas': margem,
                     'margem_pct': round(margem / teto_max * 100, 1),
                     'vagas_perdidas_2023_2025': 207,
                     'fila_area_interna': 232, 'cadastros_shopping_gavea': 454},
        'planilha': pl,
    }
    aqui = Path(__file__).resolve().parent
    out = aqui / 'baseline.json'
    out.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\nbaseline.json  {out.stat().st_size / 1024:.1f} KB')

    build_app(aqui, base)
    return base


def build_app(aqui, base):
    """Gera app.html com os dados EMBUTIDOS.

    PEGADINHA QUE MATA A DEMO: fetch('baseline.json') a partir de file:// e
    bloqueado por CORS no Chrome. Se o app dependesse de fetch, ele abriria em
    branco na hora da apresentacao. Por isso o JSON e o JS entram inline.
    O baseline.json continua saindo como arquivo separado - ele e o produto
    para os outros times, nao a fonte da demo."""
    tpl = (aqui / 'app_template.html').read_text(encoding='utf-8')
    js = (aqui / 'previsao.js').read_text(encoding='utf-8')
    html = tpl.replace('/*__BASELINE__*/null/*__END__*/',
                       json.dumps(base, ensure_ascii=False))
    html = html.replace('/*__PREVISAO__*/', js)
    dest = aqui / 'app.html'
    dest.write_text(html, encoding='utf-8')
    print(f'app.html       {dest.stat().st_size / 1024:.1f} KB  (offline, sem CDN)')


if __name__ == '__main__':
    main()
