#!/usr/bin/env python3
import re, random, os, sys
import subprocess, pwd

created_usernames = set()

def GenerateUsername(username):
    print()
    username = re.sub(r"ö", "o", re.sub(r"å|ä", "a", username)) # Remove åäö

    # Removes anything but ASCII chars
    # Also removes anything within "" or ()
    username = re.sub(r"(\(.*\))|(\\\".*\\\")|[^A-z|\s|-]", "", username).strip().lower()
    
    # Select three first letters of first name and two first letters of last name and append three random digits
    nameList = username.split()
    print(nameList)
    if (len(nameList) < 2):
        return ""
    username = nameList[0][:3] + nameList[-1][:2] + str(random.randint(100, 999))
    return username

def GeneratePassword():
    return random.randint(111111111, 999999999)

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
        subprocess.run(["chpasswd"], input=f"{username}:{password}\n",
        text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Misslyckades att sätta lösenord för '{username}': {e}")
        return

    print(f"User {username} added with password {password}")

def LoadUsersFromFile(filename):
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            NewUser(line.strip())

LoadUsersFromFile(sys.argv[1])