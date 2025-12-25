Foundational
1. Conversation Memory & Persistence

Save/load chat history to JSON or SQLite
Summarize old context to stay within token limits
"Resume where we left off" across sessions

2. File Context Loader

/add file.py to inject file contents into context
Watch files for changes and auto-update context
Glob patterns: /add src/**/*.py

3. Tool Calling Framework

Define simple Python functions as callable tools
Let the LLM decide when to use them
Start with: calculator, date/time, shell commands


MCP Integration
4. MCP Client

Connect to any MCP server (fetch, filesystem, GitHub)
Dynamic tool discovery from server
Hot-swap servers without restarting

5. RAG with Local Docs

Embed and index your own markdown/code files
Semantic search before each query
"Chat with your codebase"


Productivity
6. Multi-Model Router

/model claude or /model gpt4 to switch mid-conversation
Auto-select model based on task type (code vs. creative)
Cost/token tracking per model

7. Output Modes

/output markdown → render rich terminal output
/output file → auto-save code blocks to files
/output clipboard → copy response directly


Agentic
8. Task Planner

Break complex requests into steps
Show plan before executing
Checkpoint/resume long-running tasks

9. Web Search + Grounding

Integrate search API (Serper, Tavily, or Brave)
Auto-search when LLM doesn't know something
Cite sources in responses

10. Agent Loops with Human Approval

ReAct pattern: think → act → observe → repeat
Pause before destructive actions (file writes, API calls)
/approve or /reject at each step


Suggested Build Order
PhaseFeaturesKey Learning11, 2, 3Tool calling basics24, 5MCP protocol, embeddings36, 7UX polish, multi-provider48, 9, 10Agentic patterns