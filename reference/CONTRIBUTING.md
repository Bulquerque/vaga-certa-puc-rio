# Como participar

Projeto de equipe para o Case 2 (SIEng 2026 / PUC-Rio). Sem build, sem backend —
tudo roda abrindo os arquivos direto no navegador ou com Python puro.

## Rodar localmente

- **App / protótipo:** abra `app.html` no navegador (duplo clique). Estado da demo
  (reservas, check-ins, caronas) fica no `localStorage` do próprio navegador.
- **Motor de previsão (Python):**
  ```bash
  pip install -r requirements.txt
  python motor.py
  ```
- **Motor no navegador (JS):** `previsao.js` + `baseline.json` — ver exemplo no
  cabeçalho de `previsao.js`.

## Fluxo de contribuição

1. Crie uma branch a partir da `main`:
   ```bash
   git checkout -b sua-feature
   ```
2. Faça as mudanças e um commit descritivo.
3. `git push -u origin sua-feature` e abra um Pull Request.
4. Pelo menos 1 review de outro integrante antes do merge.

## Combinados

- `baseline.json` é o único dado versionado — é **agregado por bairro/hora**, sem
  identificação. **Nunca** commitar planilhas brutas, `alunos.csv`, nomes,
  matrículas ou telefones (ver `.gitignore`).
- Um arquivo por responsabilidade; manter o estilo dos arquivos existentes
  (comentários no mesmo tom, sem dependências novas sem combinar).
