# Deep Research Pipeline in Azure AI Foundry

This document illustrates how the **Deep Research pipeline** works in Azure AI Foundry.  
It includes visualizations showing:  

1. **Detailed Flow (flowchart)** – full breakdown of stages and decisions.  

We'll use the example query:  
**"What is the impact of recent AI regulations on the financial sector?"**

---

## 1. Detailed Flow

**Example walkthrough:**  

- The user submits the query: *"What is the impact of recent AI regulations on the financial sector?"*  
- GPT-4o clarifies: identifies that this refers to regulations such as the EU AI Act (2023–2024) and U.S. SEC guidelines, and scopes the task to focus on their impact on banks, investment firms, and compliance costs.  
- Bing grounding is invoked to fetch recent articles, whitepapers, and regulatory summaries.  
- o3-deep-research ingests all sources, compares viewpoints (e.g., on compliance costs vs. innovation), resolves contradictions, and produces a structured report.  
- The report cites EU Commission press releases, financial industry analyses, and regulatory documents.  
- Optional compliance scanning ensures no sensitive or disallowed content leaks.  
- The formatted report is delivered back to the user or integrated into an internal workflow (e.g., a compliance dashboard).  

```mermaid
flowchart TD
  %% Lanes
  subgraph U[User]
    UQ[User submits query]
    UClarify[User adds context]
    URecv[Receives final report]
  end

  subgraph A[Agent Orchestrator]
    direction TB

    subgraph G4[GPT-4o Scoping]
      G4_in[Parse intent]
      G4_scope[Clarify and scope task]
      G4_need{Clarification needed?}
      G4_plan[Produce research plan]
    end

    subgraph BG[Bing Grounding]
      BG_q[Make search queries]
      BG_call[Call Bing Search]
      BG_results[Collect ranked sources]
    end

    subgraph O3[o3-deep-research]
      O3_ingest[Ingest query plan and sources]
      O3_reason[Analyze and synthesize]
      O3_gap{Info gaps?}
      O3_tool[Request more sources]
      O3_struct[Assemble outputs with citations]
    end

    subgraph MOD[Compliance]
      MOD_scan[Moderation checks]
    end
  end

  subgraph D[Delivery]
    D_fmt[Format output]
    D_hooks[Optional post processing]
  end

  %% Main flow
  UQ --> G4_in --> G4_scope --> G4_need
  G4_need -- yes --> UClarify --> G4_scope
  G4_need -- no --> G4_plan --> BG_q --> BG_call --> BG_results --> O3_ingest --> O3_reason --> O3_gap

  %% Iterative grounding loop
  O3_gap -- yes --> O3_tool --> BG_call --> BG_results --> O3_ingest
  O3_gap -- no --> O3_struct --> MOD_scan --> D_fmt --> D_hooks --> URecv

```

## 2. Simplified & Chronological Flow

This section merges the Simple User Flow and the Chronological Sequence.
It shows both:

A linear high-level flow of how data moves.

A time-ordered sequence of interactions between User, GPT-4o, Bing, and o3-deep-research.

## 2.1 Simple User Flow

Example walkthrough:

- User asks: “What is the impact of recent AI regulations on the financial sector?”

- GPT-4o clarifies that this refers to EU AI Act and SEC rules.

- Bing grounding retrieves fresh sources from government and industry reports.

- o3-deep-research synthesizes the findings into a polished report with citations.

- The user receives a final answer referencing specific regulations and industry impact.

```mermaid
flowchart LR
  UQ[User query] --> G4[GPT-4o scope]
  G4 --> BG[Bing grounding]
  BG --> O3[o3-deep-research]
  O3 --> UR[Final answer]

```

## 2.2 Chronological Sequence

Example walkthrough:

- The user asks: “What is the impact of recent AI regulations on the financial sector?”

- GPT-4o clarifies, deciding to focus on EU AI Act and SEC guidelines.

- Bing grounding fetches official EU docs and industry analyses.

- o3-deep-research compares sources, notes conflicting views (e.g., on compliance cost), and may request additional SEC documents.

- The model produces a report with citations to EU and SEC sources.

- The user receives the final structured answer.

```mermaid
sequenceDiagram
  participant User
  participant GPT4o as GPT-4o
  participant Bing as Bing Grounding
  participant O3 as o3-deep-research
  participant Out as Delivery

  autonumber

  User->>GPT4o: Submit query
  GPT4o-->>User: Ask clarification (optional)
  User->>GPT4o: Provide details (if needed)
  GPT4o->>Bing: Send search queries
  Bing-->>GPT4o: Return sources
  GPT4o->>O3: Pass scoped query and sources
  Note over O3: Multi step reasoning and synthesis
  O3->>Bing: Request additional info (optional)
  Bing-->>O3: Provide supplemental sources
  O3->>Out: Produce report with citations
  Out-->>User: Deliver final answer

```


## Summary
This detailed flowchart shows the complete Deep Research pipeline in Azure AI Foundry, illustrating how user queries are processed through multiple AI agents to produce comprehensive, well-sourced research reports. The pipeline ensures accuracy through iterative grounding and maintains compliance through optional safety scanning.
