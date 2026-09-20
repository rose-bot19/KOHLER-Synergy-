# KOHLER Synergy

**Adaptive Enterprise AI Agent**

KOHLER Synergy is a prototype enterprise AI layer that connects company knowledge, conversational context, tool-based actions, human approval, memory, auditability and modular prompts in one workflow.

## Core idea

Instead of behaving as a simple question-answering chatbot, Synergy follows an agent loop:

**Understand -> Retrieve -> Decide -> Act -> Verify -> Respond -> Remember**

The agent can decide when to search the enterprise knowledge base, check warranty information, create or retrieve support tickets, delegate complex work, or use memory. Higher-risk actions are gated by a human approval step.

## Demonstrated prototype workflows

### 1. Proactive support

Example:

> My name is Rose. I have a KOHLER Veil smart toilet and it is leaking.

Synergy can retrieve relevant support and warranty knowledge, provide troubleshooting guidance, suggest the next useful action, and create a support ticket when explicitly requested.

### 2. Conversational continuity

A conversation is persisted locally so that a browser reload does not automatically erase the chat. Users can also explicitly save conversations and create separate new conversations.

### 3. Enterprise action governance

Tools are classified through an action policy:

- Read-only actions can execute automatically.
- Low-risk actions can execute when requested.
- High-risk actions require human approval before execution.

The prototype includes mock enterprise connectors for actions such as email, customer-record updates and maintenance dispatch. These mocks demonstrate the workflow without connecting to real enterprise accounts.

### 4. Self-updating knowledge concept

Uploaded documents can be classified into the appropriate knowledge category and then approved before being stored and indexed. This is a knowledge-base update workflow, not model retraining.

## Architecture

```text
User
  |
  v
Streamlit UI
  |
  v
KOHLER Synergy Orchestrator
  |
  +--> Modular Prompt System
  +--> Knowledge Retrieval / ChromaDB
  +--> Tool Registry
  +--> Action Policy / Approval
  +--> Episodic Memory
  +--> Audit Log
  +--> Connectors
  |
  +--> LLM Provider
       +--> Gemini (primary prototype provider)
       +--> OpenRouter fallback layer (prototype integration)
```

## Project structure

```text
kohler-synergy/
├── app.py
├── agent.py
├── orchestrator.py
├── tools.py
├── connectors.py
├── knowledge_base.py
├── document_manager.py
├── memory.py
├── audit.py
├── action_policy.py
├── verification.py
├── guardrails.py
├── manager.py
├── workers.py
├── prompt_loader.py
├── prompts/
├── knowledge/
├── data/
├── tests/
├── requirements.txt
└── .env
```

## Stack

- Python
- Streamlit
- Gemini API
- OpenRouter-compatible provider layer
- ChromaDB for semantic retrieval
- JSON/JSONL prototype persistence
- Modular prompt architecture

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Create `.env` locally:

```env
GEMINI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
```

Run:

```bash
streamlit run app.py
```

## Prototype limitations

This repository uses synthetic/demo enterprise data and mock connectors for external enterprise systems. No real customer records, production databases, or external enterprise mailboxes are connected in the prototype.

## Demo

Recommended demo sequence:

1. Report a leaking KOHLER Veil smart toilet.
2. Show knowledge retrieval and troubleshooting guidance.
3. Ask about warranty.
4. Explicitly request a support ticket.
5. Show the created ticket ID.
6. Ask for the ticket number again to demonstrate conversational context.
7. Reload the page and show the persisted conversation.
8. Start a new chat to demonstrate conversation isolation.
9. Show a high-risk action stopping at the approval stage.

## note

Prompt files in `/prompts` contain the modular system instructions and workflow prompts used by Synergy. The submission prompt PDF is generated from those files so the documented prompt contents stay aligned with the repository.
