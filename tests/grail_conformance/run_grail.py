"""Run the pinned grail, unchanged on disk, against the fake model. The only change is in memory, the way the grail's
own tests do it: the token-exchange URL points at the fake. The file's git blob hash is checked first.

    python run_grail.py <kernel_dir> <port> <fake_port>
"""
import hashlib
import os
import sys

kernel_dir, port, fake = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(os.path.join(kernel_dir, "brainstem.py"), "rb").read()
blob = hashlib.sha1(b"blob %d\0" % len(src) + src).hexdigest()
expected = os.environ.get("GRAIL_BLOB")
if expected and blob != expected:
    sys.exit(f"grail brainstem.py blob {blob} != pinned {expected}; refusing to test a changed kernel")
os.environ.update(PORT=port, GITHUB_TOKEN="ghu_fake", AGENTS_PATH=os.path.join(kernel_dir, "agents"))
sys.path.insert(0, kernel_dir)
os.chdir(kernel_dir)
import brainstem  # noqa: E402

brainstem.COPILOT_TOKEN_URL = f"http://127.0.0.1:{fake}/token"
brainstem.MODEL = os.environ.get("GRAIL_MODEL", "gpt-4o")
brainstem.VOICE_MODE = False
brainstem.app.run(
    host="127.0.0.1",
    port=int(port),
    debug=False,
    threaded=True,
    use_reloader=False,
)
