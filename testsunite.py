#!/usr/bin/env python3
import os, sys, re, subprocess, pwd
from pathlib import Path
import pytest

SCT = Path(__file__).with_name("SCT.py")

USERNAME_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
EIGHT_RE = re.compile(r"^[a-z]{5}\d{3}$")

@pytest.fixture
def stub_env(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    logs = tmp_path / "logs"
    bindir.mkdir(); logs.mkdir()

    (bindir / "useradd").write_text(
        f"#!/bin/sh\necho \"$1\" >> \"{(logs/'useradd.log')}\"\n", encoding="utf-8"
    )
    (bindir / "chpasswd").write_text(
        f"#!/bin/sh\ncat - >> \"{(logs/'chpasswd.log')}\"\n", encoding="utf-8"
    )
    os.chmod(bindir / "useradd", 0o755)
    os.chmod(bindir / "chpasswd", 0o755)

    # Prepend our stub bin to PATH
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ.get('PATH','')}")
    return {"logs": logs}

def run_sct(names_text: str, env):
    """
    Run SCT.py as a subprocess with a temp names file.
    Return (proc, created_usernames, chpasswd_lines).
    """
    tmp = env["logs"].parent
    names_file = tmp / "names.txt"
    names_file.write_text(names_text, encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(SCT), str(names_file)],
        text=True, capture_output=True, env=os.environ.copy(),
    )

    users = []
    ua_log = env["logs"] / "useradd.log"
    if ua_log.exists():
        users = ua_log.read_text(encoding="utf-8").splitlines()

    cp_lines = []
    cp_log = env["logs"] / "chpasswd.log"
    if cp_log.exists():
        cp_lines = cp_log.read_text(encoding="utf-8").splitlines()

    return proc, users, cp_lines

def test_uniqueness_and_length(stub_env):
    proc, users, cp = run_sct("Ada Lovelace\nAda Lovelace\n", stub_env)
    assert proc.returncode == 0, proc.stderr
    assert len(users) == 2
    # Both unique, both 8 chars (5 letters + 3 digits), and useradd-safe
    assert users[0] != users[1]
    for u in users:
        assert EIGHT_RE.match(u), f"bad format: {u}"
        assert USERNAME_RE.match(u), f"useradd-incompatible: {u}"
    # Passwords set via chpasswd
    assert len(cp) == 2 and all(":" in line for line in cp)

def test_single_name_is_not_ignored(stub_env):
    proc, users, _ = run_sct("Cher\n", stub_env)
    assert proc.returncode == 0, proc.stderr
    assert len(users) == 1, "single-name input must still create a user"
    assert EIGHT_RE.match(users[0])

def test_tricky_name_cleaning(stub_env):
    proc, users, _ = run_sct('Åsa ("Sally") Öberg\n', stub_env)
    assert proc.returncode == 0, proc.stderr
    assert len(users) == 1
    # Should normalize å/ä/ö and strip quotes/parentheses → 'asaob'
    assert users[0].startswith("asaob")
    assert EIGHT_RE.match(users[0])

def test_uses_chpasswd_not_passwd(stub_env):
    proc, users, cp = run_sct("Grace Hopper\n", stub_env)
    assert proc.returncode == 0, proc.stderr
    assert len(users) == 1
    assert len(cp) == 1 and cp[0].startswith(users[0] + ":")

