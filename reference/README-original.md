# Vaga Certa — Case 2: Vagas & Carona

> Um motor de previsão de ocupação que responde **no dia um, com zero reportes** —
> porque parte do histórico oficial da DSI em vez de esperar a comunidade aparecer.

## Time

- Integrante 1 — curso/período
- Integrante 2 — curso/período
- Integrante 3 — curso/período
- Integrante 4 — curso/período

## O problema

Existem **dois apps de estacionamento já construídos por alunos da PUC**
([TemVaga](https://venture-projects.github.io/temvaga/) e
[Lota PUC](https://www.lotapuc.tech/estacionamento)). Os dois têm interface boa. Os
dois estavam **vazios** em 28/08/2026: `0 reportes hoje`, `—` de média,
*"sem registros salvos"*. São 100% crowdsourced — ninguém usa porque está vazio, e
está vazio porque ninguém usa. E nenhum dos dois usa o dado histórico que a PUC
entregou neste repositório.

Mas ao abrir o dado, a pergunta do case mudou de forma. **Não há superlotação
para resolver:**

| | O que o dado diz |
|---|---|
| **Carro** | Pico de **67–75% (piso) a 90–92% (teto)**. O rotativo nunca transborda. |
| **Bike** | **Impossível medir.** A capacidade instalada não está no dataset. Sem denominador não existe taxa de ocupação. |

O problema real é **a forma da curva de chegada**. O carro chega às **7h** para uma
aula que começa às **9h** — nos cinco dias, sem exceção. A mesma laje está a **90%
às 11h e a 25% às 16h**. A escassez é auto-infligida e temporal, não estrutural.

E a superlotação verdadeira está **fora do dataset**: 232 pessoas na fila de espera
da área interna, 454 cadastros pagos no Shopping da Gávea, 207 vagas perdidas desde
2023. O estacionamento não está cheio porque a demanda já foi racionada para fora.

## A solução

Um motor que cobre **os três ângulos que o case pede**, entregue num formato que os
apps existentes conseguem adotar com um `fetch` e nenhum backend novo.

### 1 · Previsão — *"vai ter vaga quando eu chegar?"*

Curva de ocupação por (dia da semana × hora) destilada dos 15 relatórios MBS32,
contra as 360 vagas reais do rotativo. Sai sempre como **faixa `[piso, teto]`**,
nunca número único — porque falta o relatório de uma cancela de entrada (ver
pegadinha 3).

**E responde a pergunta que o case faz de verdade: *qual o erro aceitável?***
Backtest no bicicletário (65 dias, 756 observações, 8h–19h):

| Preditor | MAE | Erro mediano | p90 |
|---|---|---|---|
| Só histórico (dia × hora) | 77,7 | **64%** | 177 |
| Histórico × nível dos 3 dias anteriores | 62,9 | 46% | 158 |
| Histórico + **1 reporte** da comunidade | 39,9 | **33%** | 90 |

**Reprovamos o nosso próprio prior ingênuo.** 64% de erro mediano é inconfiável.
Mas **um único reporte corta o erro pela metade** — e é isso que justifica
empiricamente o `fundir()` e a colaboração com os outros dois times: eles têm a
audiência e a coleta, nós temos o prior. Nenhum funciona sozinho, e agora isso é
número, não opinião.

### 2 · Carona — *"quem do meu bairro chega no mesmo horário?"*

Distribuição de bairro de `alunos.csv` cruzada com a curva de chegada → grupos por
bairro e carros removidos se agrupados de 3 em 3.

| Bairro | Alunos | Carros/pico manhã | Grupos de 3 | Pedalável |
|---|---|---|---|---|
| Barra da Tijuca | 300 | 52,0 | 17 | — |
| Copacabana | 151 | 26,2 | 8 | sim |
| Leblon | 138 | 23,9 | 7 | sim |
| Botafogo | 118 | 20,5 | 6 | sim |
| Gávea | 107 | 18,6 | 6 | sim |
| Ipanema | 96 | 16,7 | 5 | sim |

Tudo agregado. **Não coletamos nome, matrícula, e-mail nem WhatsApp** — ao
contrário do formulário de carona do TemVaga, que pede os quatro sem ter vínculo
formal com a PUC.

### 3 · Política — *"incentivar bike alivia? qual capacidade evitaria lotar?"*

- **Qual capacidade evitaria lotar:** as 360 vagas ainda bastam — **por 28 vagas**.
  O teto no pico é **332**. A PUC já perdeu **207** desde 2023; perder mais **28**
  estoura. Essa é a margem inteira do campus.
- **Incentivar bike alivia?** Alivia o carro, mas **não dá para prometer que a bike
  absorve**: a capacidade do bicicletário não está no dado, e a ocupação está
  subestimada (7,3% de saídas não registradas, e quem nunca teve saída lançada
  sequer virou linha). Máximo observado: 396 bicicletas — isso é **piso**, não
  capacidade.
- **Deslocar é a alavanca barata.** A tarde tem folga real: 25% de ocupação às 16h,
  e a grade confirma de onde vem o pico — 8.633 blocos de aula começam entre 7h e
  11h contra 4.089 entre 13h e 18h (**2,11×**).

### Decisão de produto que vale defender

O app **se recusa** a mandar o aluno chegar mais cedo. Para uma aula às 9h ele não
sugere 6h — *"chegue 3h antes"* é a patologia que o case denuncia, não a solução.
Quando antecipar é a única saída, ele declara o custo:
*"custa 1h de espera no campus antes da sua aula"*.

### O entregável é plugável — não é um terceiro app de reporte

```js
const base = await fetch('baseline.json').then(r => r.json());

prever(base, 'Terca', 9);
// { ocupacao_pct: {piso: 66.1, teto: 87.5}, prob_vaga_pct: 12.5, confianca: 'alta' }

fundir(prever(base, 'Terca', 9), [{ ocupacao_pct: 80, minutos_atras: 10 }]);
// prior + comunidade, com peso por quantidade e idade (meia-vida 30 min)

melhorHorario(base, 'Terca', 9);
// { na_hora: {hora:9, prob:12.5}, mais_cedo: {hora:6, prob:66.9, espera:3},
//   ganho_de_madrugar: 54.4, corrida: true }
```

### O achado que o app não esconde

Perguntamos ao dado se madrugar resolve. **Resolve.** Para uma aula às 9h numa
terça, chegar às 6h leva a chance de vaga de **12,5% para 66,9%**.

Seria confortável construir um app que diz "não precisa chegar cedo" — mas seria
fraudar o dado. O ponto é outro, e é mais forte: **é justamente por funcionar que
todo mundo faz**, e é por isso que o pico de chegada é às 7h para aulas que começam
às 9h. Ótimo individual e ótimo coletivo divergem.

A conclusão que sai daí é a tese do projeto: **nenhum app resolve isso mandando cada
aluno chegar mais cedo** — isso só acelera a corrida. Quem resolve é a instituição,
espalhando a chegada. O app mostra as duas opções lado a lado, com o preço de cada
uma em horas de vida, e nomeia a corrida em vez de participar dela.

## Como rodar

```bash
pip install -r requirements.txt
python motor.py
```

Requer **`pdftotext`** (Poppler) no PATH para ler os 15 relatórios — no Windows já
vem com o Git (`C:\Program Files\Git\mingw64\bin`).

Depois é só abrir **`app.html`** com duplo clique. **Sem servidor, sem internet,
sem CDN** — os dados vão embutidos no HTML de propósito (ver pegadinha 10).

| Arquivo | O que é |
|---|---|
| `motor.py` | lê PDFs + xlsx + bike + alunos, roda o backtest, gera tudo |
| `baseline.json` | ⭐ o prior (7,7 KB) — **é isto que os outros times adotam** |
| `previsao.js` | ⭐ `prever()` + `fundir()` + `melhorHorario()`, zero dependência |
| `app_template.html` | template da demo (o motor injeta os dados) |
| `app.html` | demo offline gerada |

## Dados usados

| Arquivo | Para quê |
|---|---|
| `estacionamento/*.pdf` (15) | **curva de ocupação do rotativo** — o README do case manda usar o PDF como referência |
| `estacionamento/FLUXO ...xlsx` | permanência, recorrência, separação visitante × conveniado |
| `estacionamento/capacidade_estacionamento.md` | 360 vagas; 207 perdidas; fila de 232 |
| `bicicletario/ocupacao_estimada.csv` | curva da bike **e o backtest** (65 dias) |
| `bicicletario/sessoes.csv` | saídas não registradas (7,3%) |
| `case1_oportunidades/alunos.csv` | distribuição de bairro para as rotas de carona |
| `case3_grade_horaria/turmas_horarios.csv` | de onde vem o pico: 2,11× mais aula de manhã |

### As pegadinhas — o que achamos e como tratamos

**1. A planilha soma TODAS as cancelas da PUC, não só o rotativo.** Comparar os
6.858 tickets com as 360 vagas dá 181% de ocupação — impossível. A curva do
rotativo vem dos PDFs; a planilha ficou para permanência e recorrência.

**2. O ticket `8932725` aparece 1.025 vezes** — 15% de todos os registros. Não é
carro estacionando, é acionamento de cancela (serviço/cortesia). Quem não separar
isso infla a ocupação em 15%.

**3. Faltam entradas no pacote de PDFs.** Há **um** relatório de cancela de entrada
e **dois** de saída. Em 17/08 saem **812** carros e entram **660** — **todo dia sai
mais carro do que entrou**, e o saldo cru fecha o dia em −152. Ninguém consegue
ocupação absoluta exata com esse pacote. Por isso o número sai como **faixa**: o
piso é o saldo cru; o teto reescala as entradas por `k = saídas/entradas`
(1,16–1,26) ancorando no fato de que o rotativo fecha às 23h e esvazia.
→ **Pedido concreto à DSI: o relatório da cancela de entrada que falta.**

**4. As três abas do xlsx têm o cabeçalho em posições diferentes** — e a aba
`21 de Agosto` tem 9 colunas contra 10 das outras. `header=0` quebra. Lemos
procurando a célula `ID`.

**5. Data/hora em serial do Excel na mesma planilha.** `pd.to_datetime` engole
`46252` como epoch de 1970 sem reclamar e gera **duração negativa em silêncio**.
O parser testa "é número?" **antes** de tentar interpretar como data.

**6. `Gavea` e `Gávea` são bairros diferentes no dado.** Gávea está partida em **4
grafias** (84 + 20 + 2 + 1 = 107). Sem normalizar acento, caixa e espaço em branco,
o grupo de carona nasce fragmentado. **325 grafias → 298 bairros.**

**7. Não existe placa.** A coluna `Placa` traz só o texto `Visualizar` (era link no
sistema de origem). Recorrência só via número de ticket.

**8. `turmas_horarios.csv` tem 74.381 linhas mas só 26.655 únicas** — 64% são
duplicatas exatas. Qualquer contagem sobre o arquivo cru vem inflada quase 3×.

**9. A capacidade do bicicletário não está no dado.** Nunca reportamos percentual
de ocupação da bike — só bicicletas absolutas. **Um erro que quase cometemos:**
396 é o máximo do *bicicletário*; dividir 396 por 360 (vagas de *carro*) dá "110%
de ocupação" e é a divisão de duas bases diferentes.

**10. `fetch()` a partir de `file://` é bloqueado por CORS.** Se a demo dependesse
de `fetch('baseline.json')`, abriria em branco na apresentação. Por isso o
`motor.py` embute JSON e JS inline no `app.html`. O `baseline.json` continua saindo
como arquivo separado — ele é o produto para os outros times, não a fonte da demo.

**Bônus não documentado no case:** tickets de uso único pagam **R$ 16,59** em média;
os recorrentes pagam **R$ 1,32**. Dá para separar visitante de conveniado **direto
da planilha** — o README do case afirma que só os PDFs permitiriam isso.

## Decisões e limitações

- **A semana medida (17–21/08/2026) é a primeira semana de aula de 2026.2** — é
  **teto** do semestre, não média.
- **São 5 dias úteis: uma segunda, uma terça.** Uma curva por dia da semana teria
  n=1. Por isso o dia entra como **fator de volume** medido (Sexta = 0,78) e não
  como curva própria — é o que a amostra sustenta.
- **O backtest é do bicicletário, não do carro.** O carro só tem 5 dias; a bike tem
  65. Assumimos que a estrutura do erro se parece entre os dois modais — é
  suposição, e está declarada.
- **Não convertemos bloco de aula em carro.** O Case 3 não traz matrícula de aluno
  em disciplina. A política é parametrizada em **% de chegadas**; a grade entra como
  evidência de que a tarde tem espaço.
- **A conversão bairro → carro assume** que a distribuição de bairro dos motoristas
  é a mesma dos alunos cadastrados. O ticket não tem vínculo com aluno, por design.
- **A lista de bairros "pedaláveis" é suposição do time**, feita no mapa — não há
  geocodificação no pacote de dados.
- **Períodos diferentes:** bicicletário é 2026.1 (mai–jul), estacionamento é 2026.2
  (ago). Comparamos a **forma** da curva, nunca os níveis.
- **Privacidade:** `alunos.csv` entra como distribuição populacional, nunca como
  identificação. Alinhado ao `USO-DOS-DADOS.md`.

## Próximos passos

1. **Pedir à DSI o relatório da cancela de entrada que falta.** É a única coisa que
   separa a faixa `[piso, teto]` de um número exato.
2. **Pedir à DSI a capacidade instalada do bicicletário.** Sem ela, "a bike alivia o
   estacionamento?" é irrespondível — e é uma das três perguntas do case.
3. **Oferecer o `baseline.json` aos times do TemVaga e do Lota PUC.** O backtest
   mostra que histórico sozinho erra 64% e que um reporte derruba para 33%: os três
   grupos resolvem juntos o que nenhum resolve sozinho.
4. Recalcular o prior com um semestre inteiro em vez de uma semana de pico, e ligar
   o `fundir()` a uma fonte real de reportes.
5. Fechar o laço com o Case 3: apontar **quais turmas** poderiam mudar de horário,
   checando `sala_id` e `professor_id` para não propor o impossível.

## Feito com

Claude · Python (pandas, openpyxl) · pdftotext (Poppler) · SVG na mão, sem
biblioteca de gráfico.

---

Projeto de alunos para o **Impact Lab · SIEng 2026** (PUC-Rio, 28/08/2026).
**Não é um serviço oficial da PUC-Rio.** Dados cedidos pela Diretoria de Sistemas de
Informação (DSI), já anonimizados. Propriedade intelectual conforme a Política de
Inovação da PUC-Rio (IE 01/2024).
