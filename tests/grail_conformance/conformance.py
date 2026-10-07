#!/usr/bin/env python3
"""Compare the pinned Python Brainstem with CommunityRAPP in-process.

The grail runs unchanged in an isolated subprocess. CommunityRAPP is invoked
directly through azure.functions.HttpRequest objects. Both engines use the same
scripted fake OpenAI-compatible model and the same test agents.
"""
import hashlib
import importlib.util
import inspect
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
GRAIL = Path(os.path.expanduser(os.environ.get(
    "GRAIL_DIR",
    "~/.airaptr/kernel"
)))
DEFAULT_GRAIL_PY = Path("~/.airaptr/venv/bin/python").expanduser()
GRAIL_PY = os.environ.get(
    "GRAIL_PYTHON",
    str(DEFAULT_GRAIL_PY if DEFAULT_GRAIL_PY.exists() else Path(sys.executable))
)
MODEL = "gpt-4o"
SESSION_ID = "grail-conformance-session"


def chat_body(user_input, **extra):
    return {"user_input": user_input, "session_id": SESSION_ID, **extra}


# (name, method, path, body or raw bytes)
SCENARIOS = [
    ("health agents", "GET", "/health", None),
    ("echo", "POST", "/chat", chat_body("hello there")),
    ("trims input", "POST", "/chat", chat_body("   padded   ")),
    ("history counts", "POST", "/chat", chat_body(
        "third",
        conversation_history=[
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
        ],
    )),
    ("word stats agent", "POST", "/chat", chat_body(
        'CALL WordStats {"text": "one two three."}'
    )),
    ("python agent", "POST", "/chat", chat_body(
        'CALL Echo {"text": "loud"}'
    )),
    ("multiple tool calls", "POST", "/chat", chat_body("MULTI tools")),
    ("agent raises", "POST", "/chat", chat_body("CALL Boom {}")),
    ("unknown agent", "POST", "/chat", chat_body("CALL Nobody {}")),
    ("bad tool args", "POST", "/chat", chat_body("CALL Echo [1,2]")),
    ("tool rounds run out", "POST", "/chat", chat_body("LOOP forever")),
    ("tool fallback", "POST", "/chat", chat_body("FALLBACK empty")),
    ("missing input", "POST", "/chat", {}),
    ("blank input", "POST", "/chat", {"user_input": "   "}),
    ("input not a string", "POST", "/chat", {"user_input": 5}),
    ("body not an object", "POST", "/chat", [1, 2]),
    ("body not json", "POST", "/chat", b"not json"),
    ("history not a list", "POST", "/chat", {
        "user_input": "x",
        "conversation_history": "nope",
    }),
    ("history item not an object", "POST", "/chat", {
        "user_input": "x",
        "conversation_history": ["nope"],
    }),
    ("history bad role", "POST", "/chat", {
        "user_input": "x",
        "conversation_history": [{"role": "system", "content": "x"}],
    }),
    ("history bad content", "POST", "/chat", {
        "user_input": "x",
        "conversation_history": [{"role": "user", "content": 5}],
    }),
    ("input type checked first", "POST", "/chat", {
        "user_input": 5,
        "conversation_history": "nope",
    }),
    ("history checked before blank", "POST", "/chat", {
        "user_input": "   ",
        "conversation_history": "nope",
    }),
    ("version", "GET", "/version", None),
    ("not found", "GET", "/nope", None),
]


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait(port, path="/health", timeout=40):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(
                f"http://127.0.0.1:{port}{path}",
                timeout=2
            )
            return True
        except urllib.error.HTTPError:
            return True
        except Exception:
            time.sleep(0.2)
    return False


def decode_response(code, raw):
    try:
        return code, json.loads(raw)
    except (TypeError, ValueError):
        return code, {"_raw": raw[:120].decode(errors="replace")}


def call_http(port, method, path, body):
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            code, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        code, raw = error.code, error.read()
    return decode_response(code, raw)


def load_test_agents():
    fixture = HERE / "agents" / "echo_agent.py"
    spec = importlib.util.spec_from_file_location(
        "grail_conformance_agents",
        fixture
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    agents = {}
    for _, candidate in inspect.getmembers(module, inspect.isclass):
        if (
            candidate.__module__ == module.__name__
            and candidate.__name__ != "BasicAgent"
            and hasattr(candidate, "perform")
        ):
            instance = candidate()
            agents[instance.name] = instance
    return agents


class Tier2Adapter:
    def __init__(self, fake_port, work):
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = MODEL
        os.environ["VOICE_MODE"] = "false"
        os.environ["USE_CLOUD_STORAGE"] = "false"
        for name in (
            "WEBSITE_INSTANCE_ID",
            "WEBSITE_SITE_NAME",
            "APPSETTING_WEBSITE_SITE_NAME",
            "AZURE_STORAGE_ACCOUNT_NAME",
            "AZURE_FILES_SHARE_NAME",
        ):
            os.environ.pop(name, None)

        from openai import OpenAI
        import function_app

        self.func = __import__("azure.functions", fromlist=["functions"])
        self.app = function_app
        self.client = OpenAI(
            api_key="fake",
            base_url=f"http://127.0.0.1:{fake_port}/v1",
        )
        self.agents = load_test_agents()

        function_app._openai_client = self.client
        function_app._openai_client_created_at = time.time()
        function_app._llm_backend = "azure"
        function_app._copilot_model = None
        function_app._get_openai_client = lambda: self.client
        function_app._get_cached_agents = (
            lambda force_refresh=False: self.agents.copy()
        )
        function_app.get_storage_manager = lambda: object()

    @staticmethod
    def invoke(handler, request):
        if hasattr(handler, "_function"):
            handler = handler._function.get_user_function()
        return handler(request)

    def call(self, method, path, body):
        raw_body = b""
        if body is not None:
            raw_body = (
                body if isinstance(body, bytes)
                else json.dumps(body).encode()
            )
        request = self.func.HttpRequest(
            method=method,
            url=f"http://localhost/api{path}",
            headers={"Content-Type": "application/json"},
            params={},
            route_params={},
            body=raw_body,
        )

        if path == "/health" and method == "GET":
            response = self.invoke(self.app.health_check, request)
        elif path == "/version" and method == "GET":
            response = self.invoke(self.app.version, request)
        elif path == "/chat" and method == "POST":
            response = self.invoke(self.app.chat, request)
        else:
            return 404, {"error": "not found"}

        return decode_response(response.status_code or 200, response.get_body())


def contract_view(name, code, body):
    if name == "health agents":
        return {
            "code": code,
            "status": body.get("status"),
            "agents": sorted(body.get("agents", [])),
        }
    if name == "version":
        return {
            "code": code,
            "has_version": isinstance(body.get("version"), str),
        }
    if name == "not found":
        return {"code": code}
    if code == 200:
        return {
            "code": code,
            "keys": sorted(body),
            "response": body.get("response"),
            "session_id": body.get("session_id"),
            "agent_logs": body.get("agent_logs"),
            "voice_mode": body.get("voice_mode"),
            "model": body.get("model"),
            "requested_model": body.get("requested_model"),
            **(
                {"voice_response": body.get("voice_response")}
                if "voice_response" in body else {}
            ),
        }
    return {
        "code": code,
        "keys": sorted(body),
        "error": body.get("error"),
    }


def git_blob(data):
    return hashlib.sha1(
        b"blob %d\0" % len(data) + data
    ).hexdigest()


def prepare_grail(work):
    if not (GRAIL / "brainstem.py").is_file():
        raise RuntimeError(f"grail not found at {GRAIL}")

    grail = work / "grail"
    shutil.copytree(
        GRAIL,
        grail,
        ignore=shutil.ignore_patterns(
            "agents",
            ".brainstem_model",
            ".copilot_*",
            ".env",
            ".git",
            "__pycache__",
            "tests",
        ),
    )
    agents = grail / "agents"
    agents.mkdir()
    shutil.copy(GRAIL / "agents" / "basic_agent.py", agents)
    for fixture in (HERE / "agents").glob("*_agent.py"):
        shutil.copy(fixture, agents)
    return grail


def read_log(path):
    try:
        return path.read_text(errors="replace")[-4000:]
    except OSError:
        return "(log unavailable)"


def stop_process(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main():
    work = Path(tempfile.mkdtemp(prefix="grail-conformance-"))
    fake_port, grail_port = free_port(), free_port()
    fake_log = work / "fake.log"
    grail_log = work / "grail.log"
    processes = []
    log_handles = []

    try:
        grail = prepare_grail(work)
        source = (GRAIL / "brainstem.py").read_bytes()
        grail_blob = git_blob(source)

        fake_handle = fake_log.open("w")
        grail_handle = grail_log.open("w")
        log_handles.extend((fake_handle, grail_handle))

        processes.append(subprocess.Popen(
            [sys.executable, str(HERE / "fake_model.py"), str(fake_port)],
            stdout=fake_handle,
            stderr=subprocess.STDOUT,
        ))
        if not wait(fake_port, path="/models", timeout=10):
            raise RuntimeError(
                "fake model did not start:\n" + read_log(fake_log)
            )

        env = dict(
            os.environ,
            HOME=str(work / "home"),
            GITHUB_TOKEN="ghu_fake",
            GITHUB_MODEL=MODEL,
            VOICE_MODE="false",
            GRAIL_BLOB=grail_blob,
            GRAIL_MODEL=MODEL,
        )
        processes.append(subprocess.Popen(
            [
                GRAIL_PY,
                str(HERE / "run_grail.py"),
                str(grail),
                str(grail_port),
                str(fake_port),
            ],
            env=env,
            stdout=grail_handle,
            stderr=subprocess.STDOUT,
        ))
        if not wait(grail_port):
            raise RuntimeError(
                "grail did not start:\n" + read_log(grail_log)
            )

        tier2 = Tier2Adapter(fake_port, work)
        rows = []
        differences = 0
        for name, method, path, body in SCENARIOS:
            grail_result = contract_view(
                name,
                *call_http(grail_port, method, path, body)
            )
            tier2_result = contract_view(
                name,
                *tier2.call(method, path, body)
            )
            same = grail_result == tier2_result
            differences += not same
            rows.append({
                "scenario": name,
                "same": same,
                "grail": grail_result,
                "tier2": tier2_result,
            })
            print(
                ("  same  " if same else "  DIFF  ")
                + name
                + (
                    ""
                    if same
                    else (
                        f"\n          grail: {grail_result}"
                        f"\n          tier2: {tier2_result}"
                    )
                )
            )

        report = {
            "grail_blob": grail_blob,
            "scenarios": rows,
            "identical": len(SCENARIOS) - differences,
            "total": len(SCENARIOS),
        }
        (HERE / "report.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(
            f"\n{len(SCENARIOS) - differences} of "
            f"{len(SCENARIOS)} scenarios identical"
        )
        return 1 if differences else 0
    except Exception as error:
        print(f"conformance failed: {error}", file=sys.stderr)
        return 2
    finally:
        for process in reversed(processes):
            stop_process(process)
        for handle in log_handles:
            handle.close()
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
