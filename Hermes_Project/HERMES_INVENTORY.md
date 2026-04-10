# Hermes Agent — Complete Skills & Tools Inventory
**Repository:** nranka79/ndr-hermes-agent  
**Generated:** 2026-04-01

---

## TABLE OF CONTENTS
1. [Tools Inventory](#tools-inventory)
2. [Skills Inventory](#skills-inventory)
3. [Custom Tools (Your Additions)](#custom-tools-your-additions)
4. [Invocation Patterns](#invocation-patterns)
5. [Prerequisites & Environment](#prerequisites--environment)

---

## TOOLS INVENTORY

### Core Tools (Alphabetical)

| Tool Name | Toolset | Invocation | Emoji | Async | Purpose |
|-----------|---------|-----------|-------|-------|---------|
| **browser_back** | browser | Use after navigation | ◀️ | No | Go back one page |
| **browser_click** | browser | Click on element | 👆 | No | Click UI elements by selector |
| **browser_close** | browser | Close browser | 🚪 | No | Shut down browser session |
| **browser_navigate** | browser | `browser_navigate(url)` | 🌐 | No | Load URL and take snapshot |
| **browser_press** | browser | Press keyboard key | ⌨️ | No | Emulate keyboard input (Enter, Tab, etc.) |
| **browser_scroll** | browser | Scroll within page | 📜 | No | Scroll up/down or to element |
| **browser_snapshot** | browser | Auto on navigate | 📸 | No | Full-page screenshot (JSON-formatted) |
| **browser_type** | browser | Type in input field | ⌨️ | No | Type text into focused field |
| **browser_vision** | browser | Analyze on-screen content | 👁️ | No | Vision model analysis of page |
| **clarify** | clarify | Ask user for input | ❓ | No | Blocking question with multiple choice |
| **cronjob** | cronjob | `cronjob(action, name, ...)` | ⏰ | No | Create/list/run scheduled tasks |
| **delegate_task** | delegation | Multi-agent routing | 🔀 | No | Spawn sub-agent for task |
| **execute_code** | code_execution | `execute_code(language, code)` | 🐍 | No | Run Python in sandbox |
| **google_workspace_manager** | google_workspace | `command: "SERVICE RESOURCE ACTION --flags"` | 📧 | No | Gmail, Drive, Sheets, Calendar, Contacts, Tasks, Admin |
| **ha_call_service** | homeassistant | Trigger HA automation | 🏠 | No | Call Home Assistant service |
| **ha_get_state** | homeassistant | Get current state | 🏠 | No | Read entity state (lights, temps, etc.) |
| **ha_list_entities** | homeassistant | List all HA devices | 🏠 | No | List available entities |
| **ha_list_services** | homeassistant | Get available services | 🏠 | No | List callable HA services |
| **honcho_conclude** | honcho | End session | 🔮 | No | Finalize profiling |
| **honcho_context** | honcho | Get context | 🔮 | No | Retrieve execution context |
| **honcho_profile** | honcho | Start profile | 🔮 | No | Profile code execution |
| **honcho_search** | honcho | Query database | 🔮 | No | Search honcho records |
| **image_generate** | image_gen | `image_generate(prompt, model)` | 🎨 | No | Text-to-image (FLUX, Stable Diffusion) |
| **memory** | memory | `memory(action, target, content)` | 🧠 | No | Add/update/remove/read memory entries |
| **mixture_of_agents** | moa | Route to specialized agents | 🧠 | **Yes** | Load-balance across agent specialists |
| **noun_learner** | google_workspace | After voice corrections | 📚 | No | Learn misspellings, update associations |
| **patch** | file | Apply code changes | 🔧 | No | Apply unified diff patches |
| **read_file** | file | `read_file(path)` | 📖 | No | Read file contents |
| **rl_check_status** | rl | Monitor training | 🧪 | **Yes** | Get run status |
| **rl_edit_config** | rl | Update parameters | 🧪 | **Yes** | Modify training config |
| **rl_get_current_config** | rl | View settings | 🧪 | **Yes** | Get active config |
| **rl_get_results** | rl | Retrieve metrics | 🧪 | **Yes** | Get run results |
| **rl_list_environments** | rl | Discover envs | 🧪 | **Yes** | List training environments |
| **rl_list_runs** | rl | History | 🧪 | **Yes** | List all training runs |
| **rl_select_environment** | rl | Choose env | 🧪 | **Yes** | Select env for training |
| **rl_start_training** | rl | Begin training | 🧪 | **Yes** | Start RL training run |
| **rl_stop_training** | rl | Halt training | 🧪 | **Yes** | Stop training run |
| **rl_test_inference** | rl | Test model | 🧪 | **Yes** | Test trained model |
| **search_files** | file | Find files/content | 🔎 | No | Recursive pattern search |
| **send_message** | messaging | Send to Slack, email, etc. | 📨 | No | Deliver messages to platforms |
| **session_search** | session_search | Query conversation history | 🔍 | No | Search past messages by topic |
| **skill_manage** | skills | Load/enable/customize | 📝 | No | Manage skill lifecycle |
| **skills_list** | skills | List all available | 📚 | No | Show available skills |
| **skill_view** | skills | Show skill details | 📚 | No | Get skill metadata |
| **terminal** | terminal | `terminal(command, env="local")` | 💻 | No | Execute shell (local/docker/ssh/modal) |
| **text_to_speech** | tts | Generate audio | 🔊 | No | Synthesize speech from text |
| **todo** | todo | Create tasks, get list | 📋 | No | Task management (create/complete/list) |
| **vision_analyze** | vision | Analyze image/screenshot | 👁️ | **Yes** | Vision model analysis |
| **web_extract** | web | Get article/page content | 📄 | **Yes** | Extract readable text from URL |
| **web_search** | web | `web_search(query)` | 🔍 | No | Web search (DuckDuckGo) |
| **write_file** | file | `write_file(path, content)` | ✍️ | No | Create/overwrite file |

---

## SKILLS INVENTORY

### Custom Skills (Your Repo Additions)

| Skill | Category | Path | Description | Invocation |
|-------|----------|------|-------------|-----------|
| **model-session-starter** | configuration | `skills/configuration/model-session-starter/` | Generate hermes command with specified model (MiniMax, Gemini, Nematron) | `hermes skills run model-session-starter -- MiniMax` |

### Standard Skills Available (Top 30 by Category)

#### Autonomous AI Agents
| Skill | Category | Description | Scripts |
|-------|----------|-------------|---------|
| claude-code | autonomous-ai-agents | Claude Code IDE integration | No |
| codex | autonomous-ai-agents | Code execution sandbox | No |
| hermes-agent-spawning | autonomous-ai-agents | Spawn sub-agents (v1.1.0) | No |
| opencode | autonomous-ai-agents | OpenCode integration | No |

#### Productivity
| Skill | Category | Description | Scripts |
|-------|----------|-------------|---------|
| linear | productivity | Linear issue tracking | No |
| notion | productivity | Notion API + database access | No |
| ocr-and-documents | productivity | Document OCR & parsing (v2.3.0) | **Yes** |
| powerpoint | productivity | Office automation | No |

#### Research & Data
| Skill | Category | Description | Scripts |
|-------|----------|-------------|---------|
| arxiv | research | ArXiv paper search & download | **Yes** |
| duckduckgo-search | research | Web search integration (v1.2.0) | **Yes** |

#### MLOps (71 total)
| Skill | Category | Description | Scripts |
|-------|----------|-------------|---------|
| serving-llms-vllm | mlops | vLLM inference server | No |
| stable-diffusion-image-generation | mlops | Stable Diffusion images | No |
| axolotl | mlops | LLM fine-tuning | No |
| qdrant-vector-search | mlops | Qdrant vector database | No |
| whisper | mlops | OpenAI Whisper STT | No |

#### Creative
| Skill | Category | Description | Scripts |
|-------|----------|-------------|---------|
| ascii-art | creative | ASCII art generation | No |
| excalidraw | creative | Diagram drawing | **Yes** |
| stable-diffusion-image-generation | creative | Image generation | No |

#### Google Workspace (100 vendor skills)
- gws-admin, gws-calendar, gws-chat, gws-classroom, gws-docs, gws-drive, gws-forms, gws-gmail, gws-meet, gws-sheets, gws-slides, gws-tasks

#### Security & DevOps
| Skill | Category | Description | Scripts |
|-------|----------|-------------|---------|
| github-code-review | github | Automated code review | No |
| github-pr-workflow | github | PR management automation | No |

#### Optional/Experimental (12)
- blackbox, solana, base (blockchain), blender-mcp (creative), agentmail (email), neuroskill-bci (health), openclaw-migration (migration), telephony (productivity), qmd (research), 1password, oss-forensics, sherlock (security)

---

## CUSTOM TOOLS (YOUR ADDITIONS)

### 1. **noun_resolver**
**File:** `tools/noun_resolver.py`  
**Status:** New (2026-04-01)  
**Purpose:** 3-tier contextual noun resolver for voice message correction  
**Invocation:** Automatic middleware (runs before agent sees text)  
**Features:**
- Tier 1: Thin name index (all 4,000 contacts) — O(1) lookup
- Tier 2: Hot record cache (top 15 by contact_score) — in-memory
- Tier 3: Live sheet fetch — single-row API call fallback
- Fuzzy matching via rapidfuzz
- Confidence thresholds: 0.92 (auto-replace), 0.75–0.91 (flag), <0.75 (skip)
- Session context (last 5 messages) for disambiguation

**When it runs:** Every message, especially voice  
**Depends on:** `DRAAS_CRED_FILE` → `/data/hermes/oauth-draas.json`  
**Returns:** `ResolveResult` with corrected_text, substitutions, needs_confirmation

---

### 2. **noun_learner_tool**
**File:** `tools/noun_learner_tool.py`  
**Status:** New (2026-04-01)  
**Toolset:** google_workspace  
**Registered Name:** `noun_learner`  
**Emoji:** 📚  
**Purpose:** Learn voice corrections and update spreadsheet associations  
**Actions (via `action` param):**
- **learn_correction** — Add misspelling to voice_misspellings column
- **update_associations** — Update associated_contacts, associated_projects, etc.
- **append_history** — Append timestamped summary to conversation_history
- **increment_score** — Bump contact_score for resolved contacts

**When to invoke:** After resolving a voice noun or user correction  
**Sheet:** `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g` (4 sheets)  
**Columns updated:**
- Contacts (CN: voice_misspellings, CO: contact_score, CG: conversation_history)
- Projects (C: voice_misspellings, D–F: associations, I: history)
- Land Proposals (C: voice_misspellings, F–G: associations, J: history)
- Entities (C: voice_misspellings, E–F: associations, H: history)

---

### 3. **google_workspace_manager**
**File:** `tools/google_workspace_power_tool.py` (ENHANCED)  
**Toolset:** google_workspace  
**Emoji:** 📧  
**Purpose:** Unified access to Google Workspace APIs  
**Recent updates (2026-04-01):**
- ✅ Calendar events **update** (full replace, preserves fields)
- ✅ Calendar events **patch** (partial update)
- ✅ Calendar events **delete**
- ✅ IST timezone support (`--timeZone Asia/Kolkata`)
- ✅ Event builder handles start/end/duration/timezone

**Account Support:**
- ndr@draas.com (PRIMARY, default)
- ndr@ahfl.in
- nishantranka@gmail.com

**Services & Commands:**
```
gmail messages list/get/send
gmail threads list
gmail labels list
drive files list/get/create/delete
drive about
sheets values get/update/append
sheets spreadsheets get/batchUpdate
calendar events list/get/create/update/patch/delete
calendar calendars list
contacts people list/get
tasks tasklists list
tasks tasks list/insert/update
admin users list/get
```

**Scopes Authorized:** 
✅ gmail.modify, drive, spreadsheets, calendar, contacts, tasks, admin

---

## INVOCATION PATTERNS

### Automatic (No Agent Call Needed)
| Tool | Trigger | When |
|------|---------|------|
| **noun_resolver** | Every message | Before agent processing |
| **browser_snapshot** | After navigate | Automatic screenshot |

### Agent-Triggered (Via Command/Request)
| Tool | Trigger Pattern | Example |
|------|-----------------|---------|
| **google_workspace_manager** | `"gmail messages list"` | `google_wo gmail messages list --params '{"maxResults":5}'` |
| **terminal** | `"run command"`, `"execute bash"` | `terminal(command="git status", env="local")` |
| **file tools** | `"read file"`, `"write to"`, `"search for"` | `read_file(path="/path/to/file")` |
| **browser tools** | `"navigate to"`, `"click on"`, `"type"` | `browser_navigate(url="https://example.com")` |
| **noun_learner** | `"learn correction"`, `"update association"` | After voice noun resolved |
| **memory** | `"remember"`, `"save to memory"` | `memory(action="add", target="project_notes", content="...")` |
| **todo** | `"create task"`, `"list my tasks"` | `todo(action="add", task="review PR")` |
| **send_message** | `"send to slack"`, `"email"` | `send_message(platform="slack", text="...")` |
| **web_search** | `"search for"`, `"look up"` | `web_search(query="latest news")` |
| **web_extract** | `"extract from"`, `"read article"` | `web_extract(url="...")` |
| **vision_analyze** | `"analyze image"`, `"describe screenshot"` | `vision_analyze(image="...")` |
| **image_generate** | `"generate image"`, `"create picture"` | `image_generate(prompt="...", model="flux")` |

---

## PREREQUISITES & ENVIRONMENT

### Required Environment Variables (OAuth + API Keys)

| Variable | Purpose | Account |
|----------|---------|---------|
| `DRAAS_OAUTH_REFRESH_TOKEN` | Google Workspace auth | ndr@draas.com |
| `DRAAS_OAUTH_CLIENT_ID` | OAuth client ID | ndr@draas.com |
| `DRAAS_OAUTH_CLIENT_SECRET` | OAuth secret (new: GOCSPX--tfz...) | ndr@draas.com |
| `GMAIL_OAUTH_REFRESH_TOKEN` | Gmail OAuth | nishantranka@gmail.com |
| `GMAIL_OAUTH_CLIENT_ID` | Gmail client ID | nishantranka@gmail.com |
| `GMAIL_OAUTH_CLIENT_SECRET` | Gmail secret | nishantranka@gmail.com |
| `AHFL_OAUTH_REFRESH_TOKEN` | AHFL workspace | ndr@ahfl.in |
| `AHFL_OAUTH_CLIENT_ID` | AHFL client ID | ndr@ahfl.in |
| `AHFL_OAUTH_CLIENT_SECRET` | AHFL secret | ndr@ahfl.in |
| `OPENROUTER_API_KEY` | OpenRouter LLM access | Model routing |
| `GOOGLE_AI_STUDIO_API_KEY` | Google AI Studio | Vision/Gemini |
| `HERMES_HOME` | Workspace root | `/data/hermes` (Railway) |
| `TERMINAL_ENV` | Shell execution env | "local", "docker", "ssh", "modal" |

### Spreadsheet Configuration

| Sheet | ID | Columns | Rows |
|-------|----|---------|----|
| **NDR DRAAS Google Contacts.csv** | 1196451362 | 94 (A–CO) | 4,193 |
| **projects** | 140719652 | 9 (A–I) | 1,000+ |
| **land_proposals** | 1966104697 | 10 (A–J) | 1,000+ |
| **entities** | 926880892 | 8 (A–H) | 1,000+ |

**Master Spreadsheet:** https://docs.google.com/spreadsheets/d/1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g

### Python Dependencies (New)

```
rapidfuzz>=3.0.0  # Fuzzy matching for noun resolver
google-auth>=2.0.0  # Google OAuth
google-api-python-client>=2.0.0  # Google Workspace API
```

### External Services

| Service | Purpose | Tool/Skill |
|---------|---------|-----------|
| **Google Workspace** | Email, Drive, Calendar, Sheets | google_workspace_manager, gws-* skills |
| **OpenRouter** | LLM routing (Gemini Flash Lite, etc.) | Model config |
| **Home Assistant** | Smart home automation | ha_* tools |
| **Railway.com** | Deployment platform | Hermes deployment |
| **GitHub** | Skill sync + repo | skill_manage, git tools |

---

## QUICK REFERENCE: COMMON OPERATIONS

### Email (Gmail)
```
gmail messages list --maxResults 10
gmail messages list --params '{"q":"from:ndr@draas.com"}'
gmail messages get --id MESSAGE_ID
gmail messages send --body '{"raw":"..."}'
```

### Calendar (with IST timezone)
```
calendar events list --calendarId primary
calendar events create --summary "Meeting" --start 2026-04-01T09:00:00+05:30 --timeZone Asia/Kolkata --duration 120
calendar events update --eventId ID --summary "New Title" --timeZone Asia/Kolkata
calendar events patch --eventId ID --start 2026-04-01T10:00:00+05:30
calendar events delete --eventId ID
```

### Drive
```
drive files list --params '{"q":"name contains \"report\""}'
drive files list --maxResults 20
drive files get --fileId ID
```

### Sheets
```
sheets values get --spreadsheetId SHEET_ID --range contacts!A:Z
sheets values update --spreadsheetId SHEET_ID --range Sheet1!A1:B1 --body '{"values":[["hello","world"]]}'
sheets values append --spreadsheetId SHEET_ID --range projects!A:I --body '{"values":[["NewProject","alias1","","contact1"]]}'
```

### Noun Learning (After Voice Correction)
```
noun_learner action=learn_correction sheet_type=contacts row=42 misspelling="drast"
noun_learner action=update_associations sheet_type=projects row=5 contacts="Anbu,Bharat"
noun_learner action=append_history sheet_type=projects row=5 summary="Discussed Q2 roadmap with team"
noun_learner action=increment_score row=42 amount=5
```

---

**Last Updated:** 2026-04-01  
**Repository:** nranka79/ndr-hermes-agent  
**Maintainer:** ndr@draas.com
