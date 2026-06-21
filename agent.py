import os
import sys
import json
import uuid
import argparse
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

import tools.web as web
import tools.files as files
import tools.papers as papers

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "google/gemma-2-9b-it:free"
MAX_ITERATIONS = 10
SESSIONS_DIR = ".agent/sessions"
WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))

def build_system_prompt() -> str:
    prompt = "You are a Research Desk, a helpful research assistant."
    if os.path.exists("AGENTS.md"):
        with open("AGENTS.md", "r", encoding="utf-8") as f:
            prompt += f"\n\n{f.read()}"
    return prompt

def generate_title(first_user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": f"Generate a short 3-5 word title for this prompt: {first_user_message}. Reply ONLY with the title."}],
            max_tokens=15
        )
        return response.choices[0].message.content.strip(' "')
    except:
        return "Untitled Session"

def save_session(session_id: str, messages: list, title: str = "Untitled") -> None:
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            title = existing_data.get("title", title)
    else:
        if len(messages) >= 2 and messages[1].get("role") == "user":
            title = generate_title(messages[1]["content"])

    data = {
        "id": session_id, 
        "title": title, 
        "created_at": now, 
        "updated_at": now, 
        "messages": messages
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_session(session_id: str) -> dict:
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

TOOLS = [
    {"type": "function", "function": {"name": "web_search", "description": "Search Google for live web information.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "Download text from a specific URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "paper_search", "description": "Search HuggingFace for ML/CS academic papers.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "read_paper", "description": "Read the markdown content of an academic paper by ID.", "parameters": {"type": "object", "properties": {"paper_id": {"type": "string"}}, "required": ["paper_id"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a file with line numbers appended.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "start_line": {"type": "integer"}, "read_lines": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Create a new file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Surgically edit a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "operation": {"type": "string", "enum": ["replace", "delete", "append"]}, "start_line": {"type": "integer"}, "end_line": {"type": "integer"}, "content": {"type": "string"}}, "required": ["path", "operation", "start_line"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files in the workspace.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}}, "required": ["path"]}}}
]

class Agent:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or uuid.uuid4().hex[:8]
        session_data = load_session(self.session_id)
        
        if session_data:
            self.messages = session_data.get("messages", [])
        else:
            self.messages = [{"role": "system", "content": build_system_prompt()}]

    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        save_session(self.session_id, self.messages)
        return self._run_loop()

    def run_once(self, prompt: str) -> str:
        return self.chat(prompt)

    def _run_loop(self) -> str:
        for _ in range(MAX_ITERATIONS):
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS
            )
            
            assistant_msg = response.choices[0].message
            self.messages.append(assistant_msg)
            save_session(self.session_id, self.messages)

            if assistant_msg.tool_calls:
                for tool_call in assistant_msg.tool_calls:
                    self._emit("tool_call", name=tool_call.function.name, args=tool_call.function.arguments)
                    tool_output = self.dispatch(tool_call)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": tool_output
                    })
                save_session(self.session_id, self.messages)
                continue
            else:
                return assistant_msg.content or ""
                
        return "System Error: Max iterations reached."

    def dispatch(self, tool_call) -> str:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        try:
            if name == "web_search": res = web.web_search(**args)
            elif name == "web_fetch": res = web.web_fetch(**args)
            elif name == "paper_search": res = papers.paper_search(**args)
            elif name == "read_paper": res = papers.read_paper(**args)
            elif name == "read_file": res = files.read_file(**args)
            elif name == "write_file": res = files.write_file(**args)
            elif name == "edit_file": res = files.edit_file(**args)
            elif name == "list_files": res = files.list_files(**args)
            else: res = {"error": f"Unknown tool: {name}"}
        except Exception as e:
            res = {"error": str(e)}
            
        return json.dumps(res) if not isinstance(res, str) else res

    def _emit(self, event: str, **data) -> None:
        pass 

class REPLAgent(Agent):
    def run(self) -> None:
        print(f"Research Desk [Session {self.session_id}] - /quit to exit")
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
                
            if not user_input or user_input in ("/quit", "/exit"):
                break
                
            if user_input == "/sessions":
                print("\n--- Saved Sessions ---")
                if os.path.exists(SESSIONS_DIR):
                    for f in os.listdir(SESSIONS_DIR):
                        if f.endswith(".json"):
                            sid = f.replace(".json", "")
                            data = load_session(sid)
                            title = data.get("title", "Untitled")
                            print(f"{sid} | {title}")
                print("----------------------")
                continue
                
            if user_input.startswith("/resume "):
                new_id = user_input.split(" ")[1]
                self.session_id = new_id
                session_data = load_session(self.session_id)
                self.messages = session_data.get("messages", []) if session_data else [{"role": "system", "content": build_system_prompt()}]
                print(f"[System] Switched to session {new_id}")
                continue
                
            print("\n" + self.chat(user_input))

    def _emit(self, event: str, **data) -> None:
        if event == "tool_call":
            print(f"  \033[95m[tool] {data.get('name')}\033[0m", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="AI Research Agent")
    parser.add_argument("prompt", nargs="?", help="One-shot prompt to run")
    parser.add_argument("--tui", action="store_true", help="Run in Textual UI mode")
    parser.add_argument("--session", type=str, help="Resume a specific session ID")
    
    args = parser.parse_args()

    if args.tui:
        import tui 
        tui.TUIAgent(session_id=args.session).run()
    elif args.prompt:
        agent = REPLAgent(session_id=args.session)
        print(agent.run_once(args.prompt))
    else:
        agent = REPLAgent(session_id=args.session)
        agent.run()

if __name__ == "__main__":
    main()