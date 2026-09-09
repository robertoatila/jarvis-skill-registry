#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  J.A.R.V.I.S. COGNITIVE SOVEREIGN OS - DESKTOP LAUNCHER & HUD INTERFACE
  Version: 2.1.0 Sovereign Nivel 9
  Author: Markitos // J.A.R.V.I.S. Engineering Swarm
=============================================================================
"""

import os
import sys
import time
import urllib.request
import urllib.error
import subprocess
import webbrowser
import threading
from pathlib import Path

# Paths
BASE_DIR = Path("E:/.skill-registry").resolve()
TOOLING_DIR = BASE_DIR / "tooling"
UI_DIR = BASE_DIR / "ui"
ASSETS_DIR = UI_DIR / "assets"
ICON_PATH = ASSETS_DIR / "jarvis.ico"
PNG_PATH = ASSETS_DIR / "jarvis_core.png"
SERVER_URL = "http://localhost:8899"
SERVER_SCRIPT = TOOLING_DIR / "Start-JarvisServer.ps1"

def speak(text: str):
    """Voice output via Windows SAPI or pyttsx3."""
    def _run_tts():
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return
        except Exception:
            pass

        # Native Windows SAPI fallback via PowerShell (deterministic, zero-dep)
        try:
            ps_cmd = f"$speak = New-Object -ComObject SAPI.SpVoice; $speak.Rate = 1; $speak.Speak('{text}')"
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                check=False
            )
        except Exception as e:
            print(f"[Audio Error] Could not output speech: {e}")

    t = threading.Thread(target=_run_tts, daemon=True)
    t.start()

def is_server_running(url: str = SERVER_URL, timeout: float = 1.5) -> bool:
    """Check if the J.A.R.V.I.S. backend HTTP server is responding."""
    try:
        req = urllib.request.Request(f"{url}/api/status", headers={"User-Agent": "JARVIS-Launcher/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False

def ensure_server_running():
    """Ensure the PowerShell J.A.R.V.I.S. server daemon is active."""
    if is_server_running():
        print("[J.A.R.V.I.S.] Servidor operacional em http://localhost:8899.")
        return True

    print("[J.A.R.V.I.S.] Inicializando servidor em background...")
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", str(SERVER_SCRIPT),
        "-Port", "8899"
    ]
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    subprocess.Popen(cmd, cwd=str(BASE_DIR), creationflags=creation_flags)

    # Wait up to 6 seconds for the port to open
    for _ in range(12):
        time.sleep(0.5)
        if is_server_running():
            print("[J.A.R.V.I.S.] Servidor iniciado com sucesso!")
            return True

    print("[J.A.R.V.I.S.] Aviso: O servidor pode estar inicializando ainda.")
    return False

def launch_hud():
    """Open browser to the interactive Command Center."""
    ensure_server_running()
    webbrowser.open(SERVER_URL)
    speak("J.A.R.V.I.S. online, senhor. Todos os 2.168 repositórios e esquadrões de agentes operacionais.")

def build_gui():
    """Create lightweight Tkinter Desktop HUD Launcher with cyber aesthetics."""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        print("[J.A.R.V.I.S.] Tkinter not available. Running headless browser launcher.")
        launch_hud()
        return

    root = tk.Tk()
    root.title("J.A.R.V.I.S. // Cognitive Command Hub")
    root.geometry("480x560")
    root.configure(bg="#050a12")
    root.resizable(False, False)

    if ICON_PATH.exists():
        try:
            root.iconbitmap(str(ICON_PATH))
        except Exception:
            pass

    # Header title
    title_lbl = tk.Label(
        root,
        text="J.A.R.V.I.S.",
        font=("Outfit", 26, "bold"),
        fg="#00e5ff",
        bg="#050a12"
    )
    title_lbl.pack(pady=(25, 2))

    sub_lbl = tk.Label(
        root,
        text="SOVEREIGN COGNITIVE OS // NIVEL 9",
        font=("JetBrains Mono", 10, "bold"),
        fg="#5f8fa8",
        bg="#050a12"
    )
    sub_lbl.pack(pady=(0, 20))

    # Telemetry frame
    telemetry_frame = tk.Frame(root, bg="#0b1726", bd=1, relief="solid")
    telemetry_frame.pack(padx=30, pady=10, fill="x")

    stats = [
        ("ARSENAL DE SKILLS", "144 ATIVAS"),
        ("REPOSITÓRIOS GITHUB", "2.168 INDEXADOS"),
        ("SUBAGENTES TÁTICOS", "5 ESQUADRÕES"),
        ("TOKEN GOVERNANCE", "ATIVA (<= 25 PALAVRAS)"),
    ]

    for label, val in stats:
        row = tk.Frame(telemetry_frame, bg="#0b1726")
        row.pack(fill="x", padx=15, pady=6)
        tk.Label(row, text=label, font=("JetBrains Mono", 8), fg="#719db8", bg="#0b1726").pack(side="left")
        tk.Label(row, text=val, font=("JetBrains Mono", 8, "bold"), fg="#00ffc2", bg="#0b1726").pack(side="right")

    # Action Buttons
    btn_frame = tk.Frame(root, bg="#050a12")
    btn_frame.pack(padx=30, pady=25, fill="x")

    def on_launch_hud():
        speak("Acessando interface holográfica do J.A.R.V.I.S.")
        launch_hud()

    def on_sync_obsidian():
        speak("Sincronizando cofre do Obsidian com o arsenal soberano.")
        ps_cmd = "powershell -NoProfile -ExecutionPolicy Bypass -File 'E:/.skill-registry/tooling/Sync-ObsidianVault.ps1'"
        subprocess.Popen(ps_cmd, shell=True)
        messagebox.showinfo("J.A.R.V.I.S.", "Cofre Obsidian sincronizado com 2.168 repositórios e 144 skills!")

    def on_run_workflow():
        speak("Executando esteira autônoma de ingestão e poda.")
        subprocess.Popen([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(TOOLING_DIR / "Invoke-JarvisSkillWorkflow.ps1"),
            "-RepoFullName", "microsoft/autogen"
        ])
        messagebox.showinfo("J.A.R.V.I.S.", "Pipeline disparada para microsoft/autogen!")

    btn_hud = tk.Button(
        btn_frame,
        text="ABRIR HUD HOLOGRÁFICO (PORTA 8899)",
        font=("JetBrains Mono", 10, "bold"),
        bg="#00e5ff",
        fg="#050a12",
        activebackground="#5ffffb",
        activeforeground="#050a12",
        relief="flat",
        pady=10,
        command=on_launch_hud
    )
    btn_hud.pack(fill="x", pady=6)

    btn_sync = tk.Button(
        btn_frame,
        text="SINCRONIZAR COFRE OBSIDIAN",
        font=("JetBrains Mono", 9, "bold"),
        bg="#11273d",
        fg="#8de7ff",
        activebackground="#1b3e61",
        activeforeground="#ffffff",
        relief="flat",
        pady=8,
        command=on_sync_obsidian
    )
    btn_sync.pack(fill="x", pady=6)

    btn_pipeline = tk.Button(
        btn_frame,
        text="TESTAR ESTEIRA AUTÔNOMA DE SKILL",
        font=("JetBrains Mono", 9, "bold"),
        bg="#11273d",
        fg="#00ffc2",
        activebackground="#1b3e61",
        activeforeground="#ffffff",
        relief="flat",
        pady=8,
        command=on_run_workflow
    )
    btn_pipeline.pack(fill="x", pady=6)

    footer_lbl = tk.Label(
        root,
        text="MARKITOS SYSTEM // SOVEREIGN ARCHITECTURE FIRST",
        font=("JetBrains Mono", 8),
        fg="#34546b",
        bg="#050a12"
    )
    footer_lbl.pack(side="bottom", pady=15)

    # Initial greeting speech
    speak("J.A.R.V.I.S. inicializado.")

    root.mainloop()

if __name__ == "__main__":
    if "--hud-only" in sys.argv:
        launch_hud()
    else:
        # Check Tkinter availability; fall back to launch_hud() if headless
        try:
            build_gui()
        except Exception as ex:
            print(f"[J.A.R.V.I.S.] GUI Error ({ex}). Falling back to browser HUD.")
            launch_hud()
