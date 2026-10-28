"""Helpers shared by the script tests."""
import contextlib
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")


def write(base, rel, text="x"):
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def run(script, cwd, *args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=cwd, capture_output=True, text=True)


def check_docs(d):
    return run("check_docs.py", d, d)


def copy_script(base, script):
    with open(os.path.join(SCRIPTS, script), encoding="utf-8") as f:
        write(base, f"scripts/{script}", f.read())
    return os.path.join(base, "scripts", script)


GOOD_README = "# Brand\n\nA useful description of this folder and its files.\n"
TAGS = "utm_source=github&utm_medium=public-resources&utm_campaign=brand"


def assets_module():
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)
    import generate_assets
    return generate_assets


@contextlib.contextmanager
def inside(d):
    """Run generate_assets functions, which write repo-relative paths, in a temp folder."""
    cwd = os.getcwd()
    os.chdir(d)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            yield
    finally:
        os.chdir(cwd)
