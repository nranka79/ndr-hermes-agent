# Council of Agents Pattern (Hermes Implementation)

## Concept (from Nishant)
- **Lead Council Coordinator** agent decomposes high-level task.
- Multiple specialist agents (research, critique, real-estate-expert, location-intelligence, creativity, legal, etc.) independently generate proposals/ideas.
- Coordinator facilitates **debate rounds**.
- Only proposals that reach **unanimity** (or very strong consensus) are promoted to the user.
- Final output is high-quality, vetted (used for video production ideas, copyright concepts, real estate strategies, etc.).

This prevents low-quality or contradictory outputs from reaching the user.

## Hermes Implementation (using existing tools)

### Core Skill Structure
Use `delegate_task` with one `role="orchestrator"` (the Council Coordinator) and multiple leaf agents.

**Coordinator Prompt Pattern:**
```
You are the Lead Council Coordinator.
Task: {user_goal}

1. Decompose into 3-5 specialist perspectives.
2. Spawn specialist agents with clear roles and context.
3. Collect proposals.
4. Run debate rounds: ask each agent to critique others' proposals.
5. Only advance proposals that achieve unanimity.
6. Present ONLY the unanimous best ideas to the user with clear rationale.
```

**Specialist Agent Context (example):**
- Real Estate Intelligence Agent
- Location/Geospatial Analyst
- Browser Research Specialist
- Competitive Analysis Critic
- Creative/Video Production Idea Generator

### Implementation Steps
1. Create new skill `council-of-agents` that wraps `delegate_task` with the above coordinator logic.
2. Use `gbrain` per specialist for long-term memory of their domain expertise.
3. Add consensus checker in the orchestrator (parse for phrases like "I agree", "unanimous", "all approve").
4. Combine with MoA 2.0 for the debate phase (multiple models critique simultaneously).
5. Output format: Only final unanimous recommendations + debate summary (for transparency).

### When to Use
- High-stakes real estate strategy
- Creative campaigns (video, copyright, marketing)
- Complex research where contradictory advice is harmful
- Any time user wants "only the best vetted ideas"

### Example Call
```python
delegate_task(
    goal="Develop 3 video production concepts for Ranka Oasis Phase 2 launch",
    context="Council mode: require unanimity among specialists before presenting",
    role="orchestrator",
    toolsets=["delegation", "terminal", "web"]
)
```

This pattern leverages Hermes' existing delegation, memory, and MoA capabilities. It turns Hermes into a structured "AI board of directors" for important decisions.

**Related:** autonomous-ai-agents, MoA section in main skill, real-estate-investor-research.
Submitted from 2026-07-10 learning session.
