#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_sovereign_binaries.py // J.A.R.V.I.S. Autonomous Tool Deployer
Deploys portable sovereign CLI binaries into Drive D: hangar (D:\Program Files\jarvis-arsenal\binaries).
"""

import io
import os
import sys
import zipfile
import subprocess
import urllib.request
from pathlib import Path

TARGET_DIR = Path(r"D:\Program Files\jarvis-arsenal\binaries")
TARGET_DIR.mkdir(parents=True, exist_ok=True)

TOOLS = [
    {
        "name": "ripgrep",
        "binary_name": "rg.exe",
        "url": "https://github.com/BurntSushi/ripgrep/releases/download/15.2.0/ripgrep-15.2.0-x86_64-pc-windows-msvc.zip",
        "exe_match": "rg.exe",
    },
    {
        "name": "aria2",
        "binary_name": "aria2c.exe",
        "url": "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip",
        "exe_match": "aria2c.exe",
    }
]

def install_tool(tool: dict) -> bool:
    dest = TARGET_DIR / tool["binary_name"]
    print(f"[*] Instalando {tool['name']} -> {dest}...")
    try:
        req = urllib.request.Request(tool["url"], headers={"User-Agent": "JARVIS-Deployer/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        print(f"    Download concluído ({len(data) / (1024*1024):.2f} MB). Extraindo...")
        
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for entry in zf.namelist():
                if entry.endswith(tool["exe_match"]):
                    content = zf.read(entry)
                    dest.write_bytes(content)
                    print(f"[OK] {tool['binary_name']} instalado com sucesso ({len(content)} bytes)!")
                    break
        
        # Test verification
        res = subprocess.run([str(dest), "--version"], capture_output=True, text=True, check=False)
        print(f"    Verificação: {res.stdout.splitlines()[0] if res.stdout else 'Sem saída'}")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao instalar {tool['name']}: {e}")
        return False

def main():
    print("=" * 65)
    print(" J.A.R.V.I.S. SOVEREIGN BINARIES INSTALLER // DRIVE D: HANGAR")
    print("=" * 65)
    success_count = 0
    for t in TOOLS:
        if install_tool(t):
            success_count += 1
    print("=" * 65)
    print(f"Instalação finalizada: {success_count}/{len(TOOLS)} ferramentas operacionais!")
    print(f"Caminho: {TARGET_DIR}")
    print("=" * 65)

if __name__ == "__main__":
    main()
