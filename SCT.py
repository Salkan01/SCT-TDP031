#!/usr/bin/env python3
import os
import random
import re
import subprocess
import sys
from pathlib import Path

import pwd

created_usernames = set()


def _clean_name(raw_name: str) -> str:
    """Return a cleaned, lowercase version of ``raw_name``."""

    name = raw_name.lower()
    name = re.sub(r"å|ä", "a", name)
    name = re.sub(r"ö", "o", name)
    name = re.sub(r'(".*?"|\(.*?\))', " ", name)
    name = re.sub(r"[^A-Za-z\s-]", " ", name)
    name = re.sub(r"\s+", " ", name).strip().lower()
    return name


def GenerateUsername(raw_name):
    cleaned = _clean_name(raw_name)
    parts = cleaned.split()

    if len(parts) >= 2:
        letters = parts[0][:3] + parts[-1][:2]
    elif len(parts) == 1:
        letters = parts[0][:5]
    else:
        letters = "user"

    letters = letters[:5].ljust(5, "x")

    existing = {user.pw_name for user in pwd.getpwall()}
    existing.update(created_usernames)

    for i in range(1000):
        candidate = f"{letters}{i:03d}"
        if candidate not in existing:
            return candidate

    raise RuntimeError("No free username available")


def GeneratePassword():
    return str(random.randint(111111111, 999999999))


def _create_home_directory(username: str) -> None:
    """Best-effort attempt to create the user's home directory."""

    home_path = Path("/home") / username
    if home_path.exists():
        return

    try:
        subprocess.run(["mkhomedir_helper", username], check=False)
        return
    except FileNotFoundError:
        pass

    try:
        os.makedirs(home_path, exist_ok=True)
    except OSError:
        return


def NewUser(name):
    try:
        username = GenerateUsername(name)
    except Exception as e:
        print(f"Misslyckades att generera användarnamn för '{name}': {e}")
        return

    try:
        subprocess.run(["useradd", username], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Misslyckades att skapa '{username}': {e}")
        return

    created_usernames.add(username)
    password = GeneratePassword()

    try:
        subprocess.run(
            ["chpasswd"],
            input=f"{username}:{password}\n",
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Misslyckades att sätta lösenord för '{username}': {e}")
        return

    _create_home_directory(username)

    print(f"User {username} added with password {password}")


def LoadUsersFromFile(filename):
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if not name:
                continue
            NewUser(name)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file-with-names>")
        sys.exit(1)
    LoadUsersFromFile(sys.argv[1])
