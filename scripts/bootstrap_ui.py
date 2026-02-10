# bootstrap_ui.py
"""
Creates a dark modern Electron + React + Tailwind UI for DocsAI.
Run from project root (next to 'docsai/' and 'profiles/'):
    python bootstrap_ui.py
Then:
    cd ui
    npm install
    npm run dev
"""

import os, textwrap, pathlib, subprocess, sys
ROOT = pathlib.Path.cwd()
UI = ROOT / "ui"

def w(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")

print("🛠  Creating DocsAI UI scaffold ...")

# ---------- package.json ----------
w(UI / "package.json", """
{
  "name": "docsai-ui",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "src/main/electron.ts",
  "scripts": {
    "dev": "concurrently \\"vite\\" \\"electron .\\"",
    "build": "vite build",
    "start": "electron ."
  },
  "dependencies": {
    "concurrently": "^9.0.0",
    "cross-env": "^7.0.3",
    "electron": "^30.0.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.18",
    "postcss": "^8.4.35",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.4.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0"
  }
}
""")

# ---------- vite.config.ts ----------
w(UI / "vite.config.ts", """
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  base: './'
})
""")

# ---------- tailwind + postcss ----------
w(UI / "tailwind.config.js", """
module.exports = {
  darkMode: 'class',
  content: ['./index.html','./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        base: '#0f172a',
        accent: '#14b8a6',
        panel: '#1e293b'
      },
      boxShadow: {
        glow: '0 0 12px 2px rgba(20,184,166,0.3)'
      }
    }
  },
  plugins: []
}
""")

w(UI / "postcss.config.js", """
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
""")

# ---------- index.html ----------
w(UI / "index.html", """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>DocsAI</title>
  </head>
  <body class="dark">
    <div id="root"></div>
    <script type="module" src="/src/renderer/main.tsx"></script>
  </body>
</html>
""")

# ---------- electron main ----------
w(UI / "src/main/electron.ts", """
import { app, BrowserWindow } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
let win: BrowserWindow | null = null

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 820,
    backgroundColor: '#0f172a',
    title: 'DocsAI',
    webPreferences: { nodeIntegration: true },
  })
  win.loadURL('http://localhost:5173')
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
""")

print("✅ Base config + Electron main created.")

# ---------- src/renderer base files ----------

RENDER = UI / "src/renderer"

# main entry point for React (Vite mount)
w(RENDER / "main.tsx", """
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""")

# global styles (Tailwind + dark modern base)
w(RENDER / "index.css", """
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body {
  @apply bg-base text-slate-200 font-sans;
}

button {
  @apply transition-all duration-150 ease-in-out;
}
""")

# main App layout
w(RENDER / "App.tsx", """
import Chat from './components/Chat'
import Dashboard from './components/Dashboard'
import ProfileSelect from './components/ProfileSelect'
import StatusBar from './components/StatusBar'
import { useState } from 'react'

export default function App() {
  const [tab, setTab] = useState<'chat'|'dashboard'>('chat')
  const [profile, setProfile] = useState('stripe')

  return (
    <div className="min-h-screen flex flex-col bg-base">
      <header className="flex items-center justify-between p-4 border-b border-slate-700">
        <h1 className="text-xl font-semibold text-accent tracking-wide">DocsAI</h1>
        <ProfileSelect value={profile} onChange={setProfile}/>
      </header>

      <nav className="flex gap-4 px-4 pt-3 text-sm text-slate-400">
        <button
          className={tab==='chat'?'text-accent':'hover:text-slate-200'}
          onClick={()=>setTab('chat')}
        >Chat</button>
        <button
          className={tab==='dashboard'?'text-accent':'hover:text-slate-200'}
          onClick={()=>setTab('dashboard')}
        >Dashboard</button>
      </nav>

      <main className="flex-1 p-4 overflow-auto">
        {tab==='chat' && <Chat profile={profile}/>}
        {tab==='dashboard' && <Dashboard profile={profile}/>}
      </main>

      <StatusBar profile={profile}/>
    </div>
  )
}
""")

# ---------- components ----------

COMP = RENDER / "components"

# Chat.tsx
w(COMP / "Chat.tsx", """
import { useState } from 'react'

export default function Chat({ profile }: {profile:string}) {
  const [question,setQuestion]=useState('')
  const [answer,setAnswer]=useState('')
  const [loading,setLoading]=useState(false)

  const ask = async ()=>{
    setLoading(true)
    setAnswer('')
    try{
      const res=await fetch(`http://localhost:8080/ask?q=${encodeURIComponent(question)}`)
      const data=await res.json()
      setAnswer(data.answer || JSON.stringify(data,null,2))
    }catch(e){setAnswer('Error contacting backend')}
    setLoading(false)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <textarea
        value={question}
        onChange={e=>setQuestion(e.target.value)}
        placeholder={`Ask the ${profile} docs...`}
        className="w-full h-32 p-3 bg-panel border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-accent shadow-glow"
      />
      <div className="flex justify-end">
        <button
          onClick={ask}
          disabled={loading}
          className="bg-accent text-slate-900 font-semibold px-6 py-2 rounded-md hover:brightness-110 disabled:opacity-50"
        >
          {loading?'Searching...':'Ask'}
        </button>
      </div>
      {answer && (
        <pre className="bg-panel p-4 rounded-md border border-slate-700 whitespace-pre-wrap text-slate-300">{answer}</pre>
      )}
    </div>
  )
}
""")

# Dashboard.tsx
w(COMP / "Dashboard.tsx", """
export default function Dashboard({ profile }: {profile:string}) {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-lg font-medium text-accent">Dashboard - {profile}</h2>
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="bg-panel p-4 rounded-lg border border-slate-700 shadow-glow">
          <h3 className="font-semibold mb-2 text-slate-100">Ingestion Stats</h3>
          <p className="text-sm text-slate-400">Pages indexed: TBD</p>
        </div>
        <div className="bg-panel p-4 rounded-lg border border-slate-700 shadow-glow">
          <h3 className="font-semibold mb-2 text-slate-100">Recent Questions</h3>
          <ul className="text-sm text-slate-400 list-disc list-inside space-y-1">
            <li>OAuth token refresh</li>
            <li>Webhook retries</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
""")

# ProfileSelect.tsx
w(COMP / "ProfileSelect.tsx", """
export default function ProfileSelect({ value, onChange }:{
  value:string, onChange:(v:string)=>void
}) {
  return (
    <select
      value={value}
      onChange={e=>onChange(e.target.value)}
      className="bg-panel border border-slate-700 rounded-md px-3 py-1 text-slate-200 focus:outline-none focus:border-accent"
    >
      <option value="stripe">Stripe</option>
      <option value="petstore">Petstore</option>
    </select>
  )
}
""")

# StatusBar.tsx
w(COMP / "StatusBar.tsx", """
export default function StatusBar({ profile }:{profile:string}) {
  return (
    <footer className="p-2 border-t border-slate-700 text-xs text-slate-500 text-center bg-panel">
      Connected to {profile} backend on port {profile==='stripe'?'8080':'8081'}
    </footer>
  )
}
""")

print("✅ React renderer + components created.")

# ---------- finalize & install ----------
print("📦 Writing final notes and attempting npm install...")

try:
    subprocess.run(["npm", "install"], cwd=UI, check=True, shell=True)
    print("✅ npm packages installed successfully.")
except Exception as e:
    print("⚠️ npm install skipped or failed — run manually:")
    print("    cd ui && npm install")
    print(e)

# ---------- final README in ui ----------
w(UI / "README_UI.md", """
# DocsAI UI

Dark modern Electron + React + Tailwind interface for DocsAI.

## Development

1.  Open a new terminal:
    ```bash
    cd ui
    npm run dev
    ```
    This starts Vite + Electron.  
    The app will open automatically once Vite serves at http://localhost:5173

2.  The UI connects to FastAPI backend on http://localhost:8080 by default.

## Structure

ui/
package.json
vite.config.ts
tailwind.config.js
src/
main/electron.ts
renderer/
App.tsx
components/
Chat.tsx
Dashboard.tsx
ProfileSelect.tsx
StatusBar.tsx
index.css
main.tsx


Modify the backend URL in `Chat.tsx` if you change ports.


print("\n🎉 DocsAI dark modern UI scaffold complete!")
print("Next steps:")
print(" 1. cd ui")
print(" 2. npm run dev")
print(" (Electron window will open)")
print("\nWhen you’re ready, connect the chat endpoint in FastAPI to your LLM retriever.")


---

✅ **How to use**

1. Save the entire three-part file as `bootstrap_ui.py` in your project root.  
2. Run:
   ```powershell
   python bootstrap_ui.py
    ```

    This creates the `ui/` folder with all necessary files.
""")