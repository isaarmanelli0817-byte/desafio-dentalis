# Dentalis Saúde Bucal — Automação de Implantação com IA

Solução desenvolvida para automatizar o fluxo de implantação de novos contratos empresariais da **Dentalis Saúde Bucal**, transformando mensagens não estruturadas enviadas pelo RH em:
1. **Ficha de Implantação oficial (`ficha_implantacao_dental.pdf`)** preenchida automaticamente via campos AcroForms.
2. **Duas opções de comunicado em HTML** prontas para disparo aos colaboradores, validadas programaticamente contra o Guia de Marca da Dentalis.
3. **Painel Web interativo** com benchmark automatizado de acertos sobre os 5 cenários de exemplo.

---

## Arquitetura e Decisões Técnicas

* **Backend & Servidor Web (`main.py`):** Construído com Python puro (`http.server.ThreadingHTTPServer`) para garantir execução imediata em qualquer ambiente Windows/Linux sem bloqueios de DLLs nativas ou dependências pesadas.
* **Motor de IA (`app/ai_service.py`):** Integração direta com a API do Google Gemini (`gemini-3.5-flash-lite` com fallback resiliente para `gemini-3.8-flash` e retentativas automáticas) utilizando **Structured Outputs (`responseSchema`)** para garantir retorno JSON determinístico.
* **Preenchimento de PDF (`app/pdf_filler.py`):** Manipulação direta de formulários AcroForms com `pypdf`, preservando a aparência visual dos campos (`NeedAppearances`) e mapeando dinamicamente até 10 beneficiários (Titulares e Dependentes).
* **Validador de Guia de Marca (`validar_comunicado`):** Auditoria automática via Regex e parsing de texto que verifica 7 regras obrigatórias antes de liberar os comunicados:
  1. Assunto com até 60 caracteres;
  2. Ausência de emojis no assunto;
  3. Máximo de 2 pontos de exclamação (`!`) no corpo;
  4. Exatamente 1 botão de ação (`<a>` ou `<button>`);
  5. Assinatura exata `Equipe Dentalis`;
  6. Rodapé obrigatório `Dentalis Saúde Bucal - ANS nº 99.999-9`;
  7. Aplicação da paleta oficial (`#0B4F6C`, `#F2F7F9`, `#20A39E`).
* **Avaliador de Precisão (`app/evaluator.py`):** Compara campo a campo a extração da IA contra o gabarito esperado das 5 mensagens de exemplo (`data/mensagens_exemplo.json`).

---

## Regras de Negócio Aplicadas

* **Tabela de Planos Dentalis:** Mapeamento automático de valores e referências comerciais (*Essencial — R$ 29,90*, *Plus — R$ 49,90*, *Premium — R$ 89,90*), identificando solicitações indiretas como *"plano mais barato"*.
* **Cálculo de Datas Relativas:** Conversão de expressões como *"primeiro dia do mês que vem"* ou *"dia 1º"* para `DD/MM/AAAA` a partir da data de recebimento da mensagem.
* **Zero Alucinação & Gestão de Pendências:** Campos ausentes (CNPJ, e-mail, plano indefinido ou dados de dependentes não enviados) permanecem `null` e são listados objetivamente no campo **Pendências** da ficha.
* **Suporte Multilíngue:** Mensagens recebidas em inglês (ex.: *Northwind Logistics Brasil*) têm seus dados traduzidos para português na ficha e os comunicados gerados em português do Brasil.

---

## Resultados do Benchmark (Evolução Iterativa)

Durante o desenvolvimento, o prompt de sistema foi calibrado a partir da análise de erros da primeira rodada:
* **Iteração 1 (Média Geral: 88,0%):** O modelo extraiu 100% dos dados cadastrais, mas gerou observações genéricas em cenários sem ressalvas e manteve os comunicados da Mensagem 04 em inglês (reprovando a checagem do rodapé ANS).
* **Iteração 2 (Média Geral: 98,0%):** Após restringir o preenchimento de `pendencias`/`observacoes` a critérios objetivos e fixar português do Brasil nos comunicados, todas as 5 mensagens passaram na auditoria de marca:

| Cenário | Acertos | Taxa de Acerto | Guia de Marca |
| :--- | :---: | :---: | :---: |
| **Msg 01 — Alvorada Engenharia** | 10/10 | 100,0% | Aprovado |
| **Msg 02 — Construtora Horizonte** | 10/10 | 100,0% | Aprovado |
| **Msg 03 — Grupo Lume Educação** | 10/10 | 100,0% | Aprovado |
| **Msg 04 — Northwind Logistics Brasil** | 10/10 | 100,0% | Aprovado |
| **Msg 05 — Padaria Pão de Minas** | 9/10 | 90,0% | Aprovado |
| **Média Geral** | **49/50** | **98,0%** | **100% Aprovado** |

Os arquivos gerados para cada mensagem (PDF preenchido, JSON extraído e as 2 opções de e-mail HTML) encontram-se salvos na pasta `resultados_exemplo/`.

---

## Como Executar Localmente

1. **Clone o repositório e acesse a pasta:**

       git clone <url-do-seu-repositorio>
       cd desafio-dentalis

2. **Crie e ative o ambiente virtual:**

       python -m venv .venv
       # Windows (PowerShell):
       .venv\Scripts\Activate.ps1

3. **Instale as dependências:**

       pip install -r requirements.txt

4. **Configure a chave da API:**
   Copie `.env.example` para `.env` e insira sua chave `GEMINI_API_KEY`.

5. **Inicie a interface web:**

       python main.py

   Acesse `http://127.0.0.1:8000` no navegador.

6. *(Opcional)* **Reexecute a avaliação das 5 mensagens via terminal:**

       python avaliar.py---

## Uso por Agentes de IA (MCP & Contexto de Projeto)

Este repositório inclui:
- **Regras e Contexto para Agentes (`GEMINI.md` e `CLAUDE.md`):** Documentam as regras de negócio da Dentalis, padrões de saída, regras do Guia de Marca e o fluxo do harness de avaliação (`avaliar.py`).
- **Servidor MCP (`mcp_server.py`):** Expõe a solução via **Model Context Protocol (JSON-RPC 2.0 sobre `stdio`)** com duas ferramentas prontas para agentes:
  - `processar_implantacao_dentalis`: extrai dados de mensagens do RH, preenche o PDF oficial e retorna os comunicados validados.
  - `executar_benchmark_dentalis`: roda o harness de avaliação nos 5 cenários e devolve a acurácia.

Exemplo de configuração para clientes MCP (como Claude Desktop ou Cursor):

```json
{
  "mcpServers": {
    "dentalis-implantacao": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}---

### Passo 5: Subir esses 4 arquivos no GitHub
Como você está enviando direto pelo site do GitHub:
1. Abra o seu repositório `desafio-dentalis` no navegador.
2. Clique em **Add file** $\rightarrow$ **Upload files**.
3. Arraste os 4 arquivos atualizados (`GEMINI.md`, `CLAUDE.md`, `mcp_server.py` e `README.md`) e clique em **Commit changes**.