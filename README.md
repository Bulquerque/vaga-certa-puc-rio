# Vaga Certa · Mobilidade PUC-Rio

MVP para o Impact Lab SIEng 2026: previsão transparente de ocupação do estacionamento rotativo e potencial de caronas por bairro.

## O que está aqui

- `/` — painel responsivo com cenário por dia, horário e modal (carro/bike).
- `reference/baseline.json` — prior agregado derivado dos dados anonimizados do case.
- `reference/motor.py` e `reference/previsao.js` — motor original do ZIP, preservado para rastreabilidade.
- `reference/offline-demo.html` — protótipo offline original.

## Decisões do MVP

O carro usa a capacidade conhecida de 360 vagas e mostra faixa piso–teto, porque o pacote de PDFs tem escopo incompleto entre cancelas. A planilha individual soma todas as cancelas e não é tratada como ocupação do rotativo. O bicicletário é exibido em volume absoluto porque sua capacidade instalada não está no dataset.

O matching real de caronas, login institucional, reservas, pagamentos, reputação e notificações são próximos passos: esta versão não finge oferecer backend ou autenticação.

## Rodar localmente

```bash
npm install
npm run dev
```

Build de produção: `npm run build`.

Dados cedidos pela DSI e anonimizados. Projeto acadêmico; não é um serviço oficial da PUC-Rio.
