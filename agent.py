import os
import json
import asyncio
import requests
import trafilatura
from openai import OpenAI
from dotenv import load_dotenv  
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL="openrouter/free"
MAX_HISTORY_TURNS = 20

ALPHAXIV_SERVER_PARAMS = StdioServerParameters(
    command = "npx",
    args=["-y", "mcp-remote", "https://api.alphaxiv.org/mcp/v1"]
)

def web_search(query: str) -> str:
    url = "https://google.serper.dev/search"
    payload = {"q": query}
    headers = {
        'X-API-KEY': os.environ.get("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = [item.get("snippet", "") for item in data.get("organic", [])[:4]]
        return json.dumps(results)
    except Exception as e:
        return f"Search tool failed: {str(e)}"
    
def web_fetch(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return "Failed to fetch webpage content."
        text = trafilatura.extract(downloaded)
        if not text:
            return "Failed to extract text from webpage."
        return text [:4000]
    except Exception as e:
        return f"Fetch tool failed: {str(e)}"
    
async def call_alphaxiv_mcp(tool_name: str, arguments: dict) -> str:
    try:
        async with stdio_client(ALPHAXIV_SERVER_PARAMS) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                if result and hasattr(result, 'content') and result.content:
                    return "".join([block.text for block in result.content if hasattr(block, 'text')])
                return "AlphaXiv server returned an empty protocol packet."
    except Exception as e:
        return f"Official MCP Server Communication Error: {str(e)}"
    
async def call_model_async(messages: list[dict], ui_log_callback) -> str:
    tools  = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search Google for live web information, current event and facts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": "Download and extract clean text from a specific destination URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type" : "string"
                        }
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_papers",
                "description": "Query the official AlphaXiv database for research papers, links and abstracts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_paper_details",
                "description": "Retrieve comprehensive comments, full text summaries, and community feedback for a target paper ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "paper_id": {
                            "type": "string"
                        }
                    },
                    "required": ["paper_id"]
                }
            }
        }
    ]
    for loop_step in range(5):
        response = client.chat.completions.create(
            model =MODEL,
            messages=messages,
            tools=tools
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content or "No answer payload returned."
        
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            ui_log_callback(f"[bold magenta] Protocol Invoking:[/bold magenta] [cyan]{name}[/cyan] -> {args}\n")

            if name == "web_search":
                result = web_search(args.get("query", ""))
            elif name == "web_fetch":
                result = web_fetch(args.get("url", ""))
            elif name in ["search_papers", "get_paper_details"]:
                result = await call_alphaxiv_mcp(name, args)
            else:
                result = f"Error: Tool name '{name}' matches no system manifest values."
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
    return "System Error: The agent hit an infinite operational tool loop limit."

def trim_history(messages: list[dict], max_turn: int) -> list[dict]:
    system_message = messages[0]
    chat_history = messages[1:]
    max_messages = max_turn*2
    if len(chat_history)> max_messages:
        chat_history = chat_history[-max_messages:]
    return [system_message] + chat_history

class ChatApp(App):
    TITLE = "Perplexity"
    CSS = """
    Screen {
        layout: vertical;
    }
    RichLog {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }
    Input {
        dock: bottom;
        height: 3;
    }
    """
    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear display"),
        Binding("ctrl+k", "clear_history", "Clear history"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.messages: list[dict] = [
            {"role": "system", "content": "You are a professional research agent. Always utilize provided tools to search for verified documents and facts before offering precise conclusions."}
        ]
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="log", wrap=True, markup=True, highlight=True)
        yield Input(placeholder="Ask for news, live web calculations, or academic paper lookups...")
        yield Footer()
        
    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold green]System Initialised Successfully.[/bold green] Native Async MCP Transport active.\n\n")
        self.query_one(Input).focus()
        
    def on_input_submitted(self, event: Input.Submitted)->None:
        user_text = event.value.strip()
        if not user_text:
            return
        event.input.clear()

        log = self.query_one('#log', RichLog)
        log.write(f"[bold cyan][You][/bold cyan] {user_text}\n")

        self.messages.append({"role": "user", "content": user_text})
        self.messages = trim_history(self.messages, MAX_HISTORY_TURNS)

        self.run_worker(self._get_response_async())
        
    async def _get_response_async(self)->None:
        log = self.query_one("#log", RichLog)
        log.write("[dim]Agent core thinking and synchronizing tools...[/dim]\n")
        try:
            response_text=  await call_model_async(self.messages, log.write)
            if not isinstance(response_text, str):
                response_text = str(response_text)
            self.messages.append({"role": "assistant", "content": response_text})
            log.write(f"[bold green][Agent][/bold green] {response_text}\n\n")
        except Exception as e:
            log.write(f"[bold red]Critical Core Loop Error:[/bold red] {str(e)}\n\n")

    def action_clear_display(self) -> None:
        self.query_one('#log', RichLog).clear()
        
    def action_clear_history(self) -> None:
        self.messages = [self.messages[0]]
        log = self.query_one("#log", RichLog)
        log.clear()
        log.write("[bold yellow]System context wiped. Conversation thread restarted.[/bold yellow]\n\n")

if __name__ == "__main__":
    ChatApp().run()