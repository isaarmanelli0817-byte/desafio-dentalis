# Instruções e Regras do Projeto — Automação Dentalis

Este repositório contém a solução de automação de implantação de planos odontológicos da **Dentalis Saúde Bucal**, acompanhada de um harness de avaliação (`avaliar.py`) e um servidor MCP (`mcp_server.py`).

## Arquitetura do Sistema
- `main.py`: Servidor web em Python puro (`http.server`) que expõe a interface visual (`static/`) e as rotas REST (`/api/processar`, `/api/avaliar`, `/api/exemplos`, `/api/download-pdf`).
- `app/ai_service.py`: Comunicação com a API do Google Gemini (`gemini-3.5-flash-lite` com fallback para `gemini-3.8-flash`) usando Structured Outputs (`responseSchema`) e validador determinístico do Guia de Marca.
- `app/pdf_filler.py`: Preenchimento de campos AcroForms no template `ficha_implantacao_dental.pdf` via `pypdf`.
- `app/evaluator.py` e `avaliar.py`: Harness de avaliação automatizada que compara a saída do modelo com o gabarito das 5 mensagens em `data/mensagens_exemplo.json`.
- `mcp_server.py`: Servidor MCP (JSON-RPC 2.0 via `stdio`) que expõe a extração e o benchmark como ferramentas para agentes de IA.

## Regras de Negócio e Guardrails (Obrigatórios)
1. **Zero Alucinação:** Nunca inventar CNPJ, e-mail, plano, data de vigência ou dados de beneficiários. Campos ausentes devem retornar `null` e ser listados objetivamente em `pendencias`.
2. **Tabela de Planos Dentalis:**
   - `Essencial`: R$ 29,90/vida (referências como "plano mais barato" ou "mais econômico").
   - `Plus`: R$ 49,90/vida.
   - `Premium`: R$ 89,90/vida.
3. **Datas Relativas:** Calcular expressões como "primeiro dia do mês que vem" usando `data_recebimento` como referência, sempre no formato `DD/MM/AAAA`.
4. **Idioma:** Mensagens recebidas em outro idioma (ex.: inglês) devem ter a ficha extraída e os comunicados redigidos em **português do Brasil**.
5. **Guia de Marca nos Comunicados HTML:**
   - Assunto com no máximo 60 caracteres e zero emojis.
   - Máximo de 2 pontos de exclamação (`!`) no corpo.
   - Exatamente 1 botão/link de ação (`<a>` ou `<button>`).
   - Assinatura exata: `Equipe Dentalis`.
   - Rodapé obrigatório: `Dentalis Saúde Bucal - ANS nº 99.999-9`.
   - Paleta oficial: `#0B4F6C` (azul escuro), `#F2F7F9` (fundo claro) e `#20A39E` (verde-água).

## Fluxo de Validação (Harness)
Sempre que alterar prompts, schemas ou regras de extração, execute:
```bash
python avaliar.py