# Cursor IDE Setup Guide for ProofHire/Agencity

This guide will help you set up Cursor IDE to work on the ProofHire/Agencity codebase.

## Quick Start (5 minutes)

### Step 1: Open the Project in Cursor

**Option A: Open as Workspace (Recommended)**
```bash
# In Terminal
open -a "Cursor" /Users/arjunvad/Desktop/proofhire/proofhire.code-workspace
```

**Option B: Open Folder**
1. Open Cursor
2. File → Open Folder
3. Select `/Users/arjunvad/Desktop/proofhire`

### Step 2: Install Recommended Extensions

When you open the project, Cursor will prompt to install recommended extensions. Click "Install All".

Or manually install:
- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Prettier** (esbenp.prettier-vscode)
- **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)
- **GitLens** (eamodio.gitlens)

### Step 3: Select Python Interpreter

1. Press `Cmd+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose: `./agencity/.venv/bin/python`

### Step 4: Verify Setup

Open a new terminal in Cursor (`Ctrl+`` `) and run:
```bash
cd agencity
source .venv/bin/activate
python -c "from app.config import settings; print('Setup OK!')"
```

---

## Project Structure

```
proofhire/
├── .cursorrules              # AI rules for Cursor (READ THIS!)
├── .vscode/                  # VS Code/Cursor settings
│   ├── settings.json         # Editor settings
│   ├── launch.json           # Debug configurations
│   ├── tasks.json            # Build tasks
│   └── extensions.json       # Recommended extensions
├── proofhire.code-workspace  # Workspace file
│
├── agencity/                 # Main intelligence platform
│   ├── app/                  # Python backend (FastAPI)
│   ├── web/                  # Next.js frontend
│   ├── scripts/              # Utility scripts
│   ├── tests/                # Test files
│   └── .env                  # Environment variables
│
├── backend/                  # ProofHire backend
├── runner/                   # Simulation runner
└── web/                      # ProofHire web app
```

---

## Running the Project

### Method 1: Using Tasks (Recommended)

Press `Cmd+Shift+P` → "Tasks: Run Task" → Select:

| Task | What it does |
|------|--------------|
| **Start Full Stack** | Starts both backend and frontend |
| **Start Backend** | Starts FastAPI on port 8001 |
| **Start Frontend** | Starts Next.js on port 3000 |
| **Run Tests** | Runs pytest |
| **Run Demo Script** | Runs the live demo |

### Method 2: Using Debug Panel

1. Click the Run & Debug icon (play button in sidebar)
2. Select a configuration:
   - **Agencity Backend (FastAPI)** - Debug the backend
   - **Agencity Frontend (Next.js)** - Debug the frontend
   - **Full Stack** - Run both together
3. Press F5 or click the green play button

### Method 3: Using Terminal

```bash
# Terminal 1: Backend
cd agencity
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001

# Terminal 2: Frontend
cd agencity/web
npm run dev
```

---

## Cursor AI Features

### Using .cursorrules

The `.cursorrules` file at the project root tells Cursor AI about the project. It includes:
- Project structure
- Coding standards
- Common patterns
- Key files to know about

**Cursor will automatically read this file when helping you.**

### Helpful Prompts for Cursor AI

```
"Explain how the master orchestrator works"
"Add a new API endpoint for X"
"Fix this bug in the curation engine"
"How do I add a new predictor to the prediction layer?"
"Search for all files that handle candidate scoring"
```

### Cursor Composer (Ctrl+I)

Use Composer for multi-file edits:
1. Press `Ctrl+I` (or `Cmd+I` on Mac)
2. Describe what you want to change
3. Cursor will suggest edits across multiple files

---

## Key Files to Know

### Backend (Python)

| File | Purpose |
|------|---------|
| `agencity/app/main.py` | FastAPI app entry point |
| `agencity/app/config.py` | Settings and env vars |
| `agencity/app/services/master_orchestrator.py` | Unified search entry |
| `agencity/app/services/reasoning/claude_engine.py` | Claude AI integration |
| `agencity/app/services/curation_engine.py` | Candidate curation |
| `agencity/app/api/routes/integration.py` | Pipeline APIs |

### Frontend (TypeScript/React)

| File | Purpose |
|------|---------|
| `agencity/web/src/app/dashboard/page.tsx` | Dashboard home |
| `agencity/web/src/app/dashboard/candidates/page.tsx` | Candidate curation UI |
| `agencity/web/src/app/dashboard/pipeline/page.tsx` | Pipeline view |
| `agencity/web/src/lib/api.ts` | API client |
| `agencity/web/src/components/` | Reusable components |

---

## Environment Variables

### Backend (.env)

Location: `agencity/.env`

Key variables:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
PINECONE_API_KEY=pcsk_...
```

### Frontend (.env.local)

Location: `agencity/web/.env.local`

```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## Debugging

### Python Backend

1. Set breakpoints by clicking left of line numbers
2. Select "Agencity Backend (FastAPI)" in Debug panel
3. Press F5
4. Backend will start with debugger attached

### Frontend

1. Add `debugger;` statement in code, or
2. Use Chrome DevTools (F12 in browser)

### API Testing

Use the built-in REST Client:
1. Create a `.http` file
2. Write requests:
```http
### Health Check
GET http://localhost:8001/health

### Get Pipeline
GET http://localhost:8001/api/pipeline/100b5ac1-1912-4970-a378-04d0169fd597
```
3. Click "Send Request" above each request

---

## Common Issues

### Python Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
1. Make sure you selected the right Python interpreter
2. Check PYTHONPATH includes the agencity folder
3. Run from within the agencity directory

### Port Already in Use

**Problem**: `Address already in use`

**Solution**:
```bash
# Find what's using the port
lsof -i :8001

# Kill it
kill -9 <PID>
```

### Frontend Can't Connect to Backend

**Problem**: Network errors in frontend

**Solution**:
1. Make sure backend is running on port 8001
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check browser console for CORS errors

---

## Keyboard Shortcuts (Cursor-specific)

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | AI edit inline |
| `Cmd+L` | Open AI chat |
| `Cmd+I` | Composer (multi-file edit) |
| `Cmd+Shift+P` | Command palette |
| `Cmd+P` | Quick file open |
| `Cmd+Shift+F` | Search across files |
| `F5` | Start debugging |
| `F12` | Go to definition |
| `Shift+F12` | Find all references |

---

## Next Steps

1. **Explore the codebase**: Start with `agencity/app/main.py` and trace through
2. **Run the demo**: Press `Cmd+Shift+P` → "Tasks: Run Task" → "Run Demo Script"
3. **Try the UI**: Open http://localhost:3000/dashboard
4. **Read the docs**: Check `agencity/docs/` for architecture details
5. **Ask Cursor AI**: Use the chat to ask questions about the codebase

---

## Need Help?

- **Project docs**: `agencity/docs/`
- **API docs**: http://localhost:8001/docs
- **Ask Cursor AI**: It knows the codebase from `.cursorrules`
