# Empório da Música — Celeste, AI Customer Service Agent

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![LLM](https://img.shields.io/badge/LLM-DeepSeek-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 🇺🇸 English

### Overview

**Celeste** is the AI customer-service agent for **Empório da Música**, a fictional musical instrument store in Campo Grande/MS, Brazil. She answers customers via a chat interface in **Portuguese or English** — the customer picks their language at the start, and Celeste switches mid-conversation if needed.

Celeste decides on her own when to query the product catalog (CSV), when to check order status, and when to retrieve store policies (PDF) — always grounding answers on real data instead of hallucinating.

*Celeste é a agente de IA de atendimento da **Empório da Música**, loja fictícia de instrumentos musicais em Campo Grande/MS. Ela responde em **português ou inglês** — o cliente escolhe o idioma no início e a Celeste troca no meio da conversa se precisar. Ela decide sozinha quando consultar catálogo (CSV), status de pedido e políticas (PDF), sempre ancorando respostas em dados reais.*

### Architecture

```
┌──────────┐     ┌─────────────────┐     ┌──────────────────┐
│  User    │────▶│ Agent (Celeste) │────▶│  Tool dispatcher │
│  (CLI)   │◀────│  DeepSeek Flash │◀────│  (function call) │
└──────────┘     └─────────────────┘     └────────┬─────────┘
                                                  │
              ┌───────────────────────────────────┼──────────────────────┐
              ▼                                   ▼                      ▼
      ┌───────────────┐                  ┌───────────────┐      ┌────────────────┐
      │  catalog.py   │                  │   orders.py   │      │  policies.py   │
      │  (CSV)        │                  │   (CSV)       │      │  (PDF + TF-IDF)│
      └───────────────┘                  └───────────────┘      └────────────────┘
```

Celeste is an LLM (DeepSeek Flash) with **native function calling**. She receives the user message and decides which tool to call (or none). The tools are plain Python functions that read CSVs (via pandas) or query a TF-IDF index over the policy PDF. The LLM never sees raw data — only tool outputs, which drastically reduces hallucination.

*Celeste é um LLM (DeepSeek Flash) com **function calling nativo**. Ela recebe a mensagem e decide qual tool chamar (ou nenhuma). As tools são funções Python puras que leem CSVs (pandas) ou consultam um índice TF-IDF sobre o PDF. O LLM nunca vê os dados brutos — só o resultado da tool, o que reduz drasticamente a alucinação.*

### Setup & Run

**Requirements:** Python 3.11+, a DeepSeek API key.

```bash
# 1. Clone
git clone <repo-url>
cd emporio-musica-agent

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# edit .env and set DEEPSEEK_API_KEY

# 4. Run
python main.py

# 5. (optional) run tests
python -m pytest tests/ -v
```

*Requisitos: Python 3.11+ e uma chave da API DeepSeek. Copie `.env.example` para `.env` e preencha a chave. Rode `python main.py` para o chat e `python -m pytest tests/ -v` para os 12 testes offline (não consomem API).*

### Technical Decisions

**LLM provider — DeepSeek Flash.** Chosen for cost (very cheap per token), OpenAI-compatible API (official `openai` SDK works unchanged), and native function-calling support. Swapping to OpenAI or Gemini is a 2-line change in `src/config.py`.

**Framework — plain Python + `openai` SDK.** No LangChain/LangGraph. For an agent with 6 tools and a single-turn loop, a framework adds indirection without benefit. Plain function calling is easier to reason about, debug, and defend.

**Data access — pandas in memory.** The CSVs are small (< 100 rows each), so loading them once into a DataFrame is simpler and faster than SQLite/Postgres. Cached at module level.

**RAG over policies — TF-IDF + cosine similarity.** The PDF has ~10 sections with clear headings. Chunking respects section boundaries and TF-IDF with bigrams captures phrases like "direito de arrependimento". No external embedding API needed — the stack is self-contained and free. Trade-off: TF-IDF is lexical, so it misses pure semantic paraphrases.

**Bilingual UX.** The customer picks PT or EN before the conversation starts. This choice is baked into the system prompt, and the agent also switches mid-conversation if the customer does. The welcome message is hardcoded (no LLM dependency), so it works even if the API is down.

**Prompt strategy.** The system prompt (`src/prompts.py`) maps each tool to a category of question and cites the store manual (sections 7.1–7.3) as the source of truth for tone and accuracy. This prevents the LLM from guessing prices or inventing deadlines. Out-of-scope handling is also explicit.

*Decisões em PT:*

**Provedor — DeepSeek Flash.** Custo baixo, API compatível com OpenAI (SDK oficial funciona sem mudança), function calling nativo. Trocar para OpenAI/Gemini é mudar 2 linhas em `src/config.py`.

**Framework — Python puro + SDK `openai`.** Sem LangChain/LangGraph. Para 6 tools e loop de turno único, framework adiciona indireção sem benefício.

**Dados — pandas em memória.** CSVs pequenos (< 100 linhas) → carregar uma vez em DataFrame é mais simples e rápido que SQLite/Postgres. Cache no módulo.

**RAG — TF-IDF + cosseno.** O PDF tem ~10 seções com títulos claros. Chunking respeita os limites de seção e o TF-IDF com bigramas captura expressões como "direito de arrependimento". Sem API externa — stack autocontido e gratuito. Trade-off: TF-IDF é lexical, perde paráfrases semânticas.

**UX bilíngue.** O cliente escolhe PT ou EN antes da conversa. A escolha vai pro system prompt, e o agente também troca no meio se o cliente trocar. A saudação é hardcoded (sem LLM), então funciona mesmo se a API cair.

**Prompt.** O system prompt mapeia cada tool a uma categoria de pergunta e cita o manual (seções 7.1–7.3) como fonte de verdade pra tom e precisão. Evita que o LLM invente preço ou prazo. Tratamento fora de escopo é explícito.

### Known Limitations

- **TF-IDF is lexical, not semantic.** Paraphrases with no lexical overlap may miss. Mitigation: `top_k=3` + bigrams. Production would use embeddings.
- **No conversation persistence.** Refreshing the CLI loses history. Would need SQLite/Redis.
- **No customer authentication.** The agent accepts an order ID without verifying ownership. Must be gated by login/OTP in production.
- **Tool loop capped at 5 rounds.** Prevents infinite loops but limits complex multi-step reasoning.
- **No streaming.** CLI waits for full response. Production UI would stream tokens.
- **Promotions only attached inside `search_products`.** A dedicated "list active promotions" tool isn't implemented.
- **PDF chunking depends on layout.** If the manual is re-rendered, the regex may need adjustment.

*Com mais tempo: (1) embeddings para RAG semântico; (2) tool dedicada de promoções; (3) persistência em SQLite; (4) autenticação por OTP; (5) streaming; (6) deploy FastAPI + frontend; (7) avaliação automatizada com LLM-as-judge.*

### AI-Assisted Development

I used an AI assistant throughout the project. The assistant helped draft code skeletons, review tool schemas, and reason about prompt structure. All technical decisions (framework choice, TF-IDF over embeddings, CSV over DB, bilingual UX) were made and justified by me, and every file was read and validated before commit. The offline tests were generated with assistant help and confirmed locally. I did not use a one-shot approach — each commit corresponds to a real step in the build, as visible in the git history.

*Usei um assistente de IA ao longo do projeto. O assistente ajudou a rascunhar esqueletos, revisar schemas e pensar no prompt. Todas as decisões técnicas (framework, TF-IDF em vez de embeddings, CSV em vez de banco, UX bilíngue) foram minhas e justificadas. Cada arquivo foi lido e validado antes do commit. Os testes offline foram gerados com ajuda do assistente e confirmados localmente. Não usei one-shot — cada commit corresponde a um passo real, visível no histórico do git.*

### Interaction Examples

See [`examples/`](./examples/) for 5 scenarios: catalog search, store info, price lookup, **return policy (non-trivial)**, and **out-of-scope request**.

---

## 🇧🇷 Português

### Visão Geral

**Celeste** é a agente de IA de atendimento da **Empório da Música**. Responde em **português ou inglês** (o cliente escolhe no início e ela troca no meio se precisar). Decide sozinha quando consultar catálogo/pedidos/políticas e nunca inventa preço, estoque ou prazo.

### Arquitetura

LLM (DeepSeek Flash) com **function calling nativo**. A Celeste recebe a mensagem e decide qual tool chamar (ou nenhuma). As tools são funções Python puras que leem CSVs (pandas) ou consultam um índice TF-IDF sobre o PDF. O LLM nunca vê os dados brutos — só o resultado da tool, o que reduz alucinação.

### Como Rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # preencha DEEPSEEK_API_KEY
python main.py
python -m pytest tests/ -v   # 12 testes offline
```

### Decisões Técnicas

Ver seção em inglês acima. Resumo: DeepSeek Flash (custo + compatibilidade OpenAI + function calling nativo); Python puro + SDK `openai` (sem framework); pandas em memória (CSVs pequenos); TF-IDF + cosseno para RAG (sem embeddings externos); UX bilíngue com escolha explícita; prompt que mapeia tools a categorias e cita o manual como fonte de verdade.

### Limitações Conhecidas

TF-IDF é lexical (perde paráfrases semânticas); sem persistência de conversa; sem autenticação de cliente; loop de tool limitado a 5 rounds; sem streaming; tool de promoções dedicada não implementada; chunking depende do layout do PDF.

Com mais tempo: embeddings para RAG, tool de promoções, persistência em SQLite, autenticação por OTP, streaming, deploy FastAPI, avaliação automatizada.

### Uso de Assistentes de IA

Usei um assistente (esta conversa) para rascunhar esqueletos, revisar schemas e pensar no prompt. Todas as decisões técnicas foram minhas e justificadas. Cada arquivo foi lido e validado antes do commit. Não usei one-shot; o trabalho foi incremental, visível no histórico do git.

### Exemplos de Interação

Ver [`examples/`](./examples/) — 5 cenários.

---

## 📄 License / Licença

MIT.