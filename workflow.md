```mermaid
graph TD
    subgraph "Part 1: Outline Generation (integrated_textbook_pipeline_chained.py)"
        A[User Input: Topic, Learning Goals] --> B{Execute Pipeline};
        
        B -- stage: toc / full --> C[1. Recommend Textbooks];
        C -- Top N Books --> D[2. Retrieve Tables of Contents];
        D -- TOCs --> E[Output: textbook_tocs.json];

        B -- stage: reconstruct / full --> F[3. Reconstruct Outline];
        E --> F;
        F -- Integrated Outline --> G[Output: integrated_pipeline.json];
    end

    subgraph "Part 2: Chapter Content Generation (generate_chapters_from_integrated_standalone.py)"
        G --> H{Start Chapter Generation};
        H --> I[1. Select Chapters to Generate];
        I --> J[2. Classify Subject (Theory/Tool)];
        J --> K[3. Generate Draft Content];
        K --> L{Review Content?};
        
        L -- Yes --> M[4. Review Drafts with LLM];
        M --> N{Auto-apply Fixes?};
        N -- Yes --> O[5. Propose & Apply Fixes];
        O --> P[6. Publish Final Content];
        
        L -- No --> P;
        N -- No --> P;

        P --> Q[Output: Markdown Files for Each Section];
        P --> R[7. Generate Final Report];
        R --> S[Output: Report.md];
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#d4f,stroke:#333,stroke-width:2px
    style Q fill:#9f9,stroke:#333,stroke-width:2px
    style S fill:#9f9,stroke:#333,stroke-width:2px
```
