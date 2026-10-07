"""Deterministic Copilot stand-in shared by the grail and CommunityRAPP.

Rules:
- CALL <Tool> <json> requests one tool.
- MULTI requests two tools in one assistant reply.
- LOOP requests tools for all three rounds, then completes without tools.
- FALLBACK requests tools for all three rounds, then returns an empty completion.
- After a normal tool result, the model returns RESULT: <last result>.
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1])


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/token"):
            return self._send({"token": "fake-copilot", "expires_at": int(time.time()) + 3600,
                               "endpoints": {"api": f"http://127.0.0.1:{PORT}"}})
        if self.path.startswith("/models"):
            return self._send({"data": [{"id": m, "name": m, "capabilities": {"type": "chat", "supports": {"tool_calls": True}},
                                         "model_picker_enabled": True} for m in ("gpt-4.1", "gpt-4o")]})
        self._send({"error": "not found"}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        msgs = body.get("messages", [])
        last = msgs[-1] if msgs else {}
        first_user = next((m.get("content") or "" for m in msgs if m.get("role") == "user"), "")
        if (
            first_user.startswith(("LOOP ", "FALLBACK "))
            and body.get("tools")
        ):
            msg = {"role": "assistant", "content": None, "tool_calls": [{"id": f"call_{len(msgs)}", "type": "function",
                   "function": {"name": "Echo", "arguments": '{"text": "again"}'}}]}
        elif first_user.startswith("FALLBACK "):
            msg = {"role": "assistant", "content": ""}
        elif last.get("role") == "tool":
            msg = {"role": "assistant", "content": "RESULT: " + str(last.get("content"))}
        else:
            text = next((m.get("content") or "" for m in reversed(msgs) if m.get("role") == "user"), "")
            if text.startswith("MULTI ") and body.get("tools"):
                msg = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_echo",
                            "type": "function",
                            "function": {
                                "name": "Echo",
                                "arguments": '{"text": "first"}',
                            },
                        },
                        {
                            "id": "call_stats",
                            "type": "function",
                            "function": {
                                "name": "WordStats",
                                "arguments": '{"text": "one two"}',
                            },
                        },
                    ],
                }
            elif text.startswith("CALL ") and body.get("tools"):
                _, name, args = (text.split(" ", 2) + ["{}"])[:3]
                msg = {"role": "assistant", "content": None,
                       "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": name, "arguments": args}}]}
            else:
                prior = sum(1 for m in msgs[:-1] if m.get("role") in ("user", "assistant"))
                msg = {"role": "assistant", "content": f"ECHO({prior}): {text}"}
        self._send({"model": body.get("model", "gpt-4.1"), "choices": [{"index": 0, "message": msg,
                    "finish_reason": "tool_calls" if msg.get("tool_calls") else "stop"}]})


ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
