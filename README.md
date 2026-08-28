# Vaga Certa · Mobilidade PUC-Rio

MVP para o Impact Lab SIEng 2026: previsão transparente de ocupação do estacionamento rotativo e potencial de caronas por bairro.

## O que está aqui

- `/` — painel responsivo com cenário por dia, horário e modal (carro/bike), acessibilidade básica e leitura textual da curva.
- Caronas — busca por bairro, dia, chegada e quantidade de passageiros; matching explicável; ofertas sintéticas verificadas; vagas; ponto público; desvio; recorrência; cálculo de custo; reserva demonstrativa; validação de formulário; estado vazio e aviso de risco do estacionamento.
- Oferta de vaga — publicação local de rota única ou semanal, prévia de custo, política de divisão e ponto de encontro.
- Persistência — ofertas e reservas de demonstração são salvas no `localStorage` deste navegador para que o fluxo sobreviva a um refresh.
- `reference/baseline.json` — prior agregado derivado dos dados anonimizados do case.
- `reference/motor.py` e `reference/previsao.js` — motor original do ZIP, preservado para rastreabilidade.
- `reference/offline-demo.html` — protótipo offline original.

## Decisões do MVP

O carro usa a capacidade conhecida de 360 vagas e mostra faixa piso–teto, porque o pacote de PDFs tem escopo incompleto entre cancelas. A planilha individual soma todas as cancelas e não é tratada como ocupação do rotativo. O bicicletário é exibido em volume absoluto porque sua capacidade instalada não está no dataset.

O módulo de caronas é deliberadamente um MVP local: a reserva é uma simulação de dispositivo, e as ofertas seed são sintéticas. Não há login institucional, backend compartilhado, transação atômica, aceite remoto do motorista, pagamento, reputação, notificações, moderação ou garantia de segurança pessoal. O próximo passo de produção é um backend com identidade PUC-Rio, autorização server-side, ocorrências por data, aceite/cancelamento, lock transacional de vagas e controles de privacidade. A verificação visual “institucional” das ofertas seed é apenas um sinal de demonstração e não é uma comprovação real.

## Rodar localmente

```bash
npm install
npm run dev
```

Build de produção: `npm run build`.

Dados cedidos pela DSI e anonimizados. Projeto acadêmico; não é um serviço oficial da PUC-Rio.
