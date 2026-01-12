# 🏗️ PR Guard Architecture

This document provides a technical overview of how PR Guard is structured and how its components interact.

## 1. System Architecture
PR Guard follows a layered architecture connecting the CLI interface to AI agents and specialized tools.

```mermaid
graph TD
    User["User / GitHub Action"] --> CLI["CLI Layer (Typer)"]
    CLI --> Agent["Agent Layer (LangGraph)"]
    Agent --> Tools["Tools Layer (Git, FS)"]
    Agent --> LLM["LLM (OpenAI/Ollama)"]
    Tools --> Git["Local Git / GitHub CLI"]
    Tools --> FS["File System"]
    Agent --> Memory["In-Memory Checkpointer"]
```

---

## 2. Review Sequence Diagram
This diagram shows the flow of the `pr-guard review` command.

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as CLI (run_review)
    participant A as Review Agent
    participant T as Tools
    participant L as LLM

    U->>C: pr-guard review
    C->>A: init_review_agent()
    C->>A: agent.astream(user_input)
    loop Tool Loop
        A->>L: Decide Next Action
        L-->>A: Call Tool(git_diff)
        A->>T: _get_git_diff_between_branches()
        T-->>A: Diff String
    end
    A->>L: Generate Final Review
    L-->>A: GitHubPRReview (Structured)
    A-->>C: Streamed Chunks
    C->>U: Display Rich Report
```

---

## 3. Chat Loop Flowchart
The interactive chat uses a stateful loop for multi-turn conversations.

```mermaid
flowchart TD
    Start([Start Chat Loop]) --> Input[/Get User Input/]
    Input --> Exit{Input == 'exit'?}
    Exit -- Yes --> End([End Session])
    Exit -- No --> CMD{Is Command?}
    
    CMD -- Yes (e.g. 'tree') --> RunCMD[Execute CLI Function]
    RunCMD --> Input
    
    CMD -- No (Generic Text) --> Streaming[Start Live Stream]
    Streaming --> Agent[Call Chat Agent]
    Agent --> Update[Update Live Display]
    Update --> Finished{Stream Finished?}
    Finished -- No --> Agent
    Finished -- Yes --> Input
```

---

## 4. Connection Details
- **CLI to Agent**: Communicates via `astream` for real-time reporting.
- **Agent to Tools**: Tools are defined in `src/pr_guard/tools.py` and passed to the agent during initialization.
- **Environment**: Sensitive data (keys, tokens) are managed via `.env` and `src/pr_guard/config.py`.
