#!/usr/bin/env python3
"""Render the public J.A.R.V.I.S. demo from captured runtime evidence.

This renderer does not invent runtime facts. Every technical value shown in the
video is read from demo_capture.py or quickstart_verifier.py output. ffmpeg is
used only as a media encoder.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

WIDTH = 1920
HEIGHT = 1080
DURATION_SECONDS = 82
GIF_START_SECONDS = 22
GIF_DURATION_SECONDS = 14


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _ass_time(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}.00"


def _ass_escape(value: object) -> str:
    text = str(value)
    text = text.replace("\\", r"\\")
    text = text.replace("{", r"\{").replace("}", r"\}")
    text = text.replace("\n", r"\N")
    return text


def _event(start: int, end: int, title: str, lines: list[str], *, fixture: bool = False) -> str:
    label = "DETERMINISTIC LOCAL FIXTURE — REAL RUNTIME RECEIPTS" if fixture else "REAL RUNTIME / CI CAPTURE"
    body = [f"{{\\b1\\fs46}}{_ass_escape(title)}{{\\b0\\fs34}}", ""]
    body.extend(_ass_escape(line) for line in lines)
    body.extend(["", f"{{\\fs24}}{_ass_escape(label)}"])
    return (
        f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Demo,,0,0,0,,"
        + r"\N".join(body)
    )


def build_ass(demo: dict[str, Any], quickstart: dict[str, Any]) -> str:
    benchmark = demo["context_benchmark"]
    inference = demo["inference"]
    skill = demo["skill"]
    local = demo["local_execution"]
    routing = inference["routing"]
    governor = inference["governor"]
    exec_receipt = inference["execution_receipt"]
    verify_receipt = inference["verification_receipt"]
    quick_launch = quickstart["checks"]["launch"]

    scenes = [
        _event(
            0,
            2,
            "CAN YOUR AGENT PROVE IT WORKED?",
            [
                "J.A.R.V.I.S. — inspectable context, routing, execution and verification.",
            ],
        ),
        _event(
            2,
            12,
            "START FROM ZERO",
            [
                "python jarvis.py --doctor",
                "python jarvis.py --no-browser",
                f"commit  {demo['commit_sha']}",
                f"doctor  {demo['doctor']['status']}",
                f"HUD     HTTP {quick_launch['http_status']} at 127.0.0.1",
                "provider key required: false",
            ],
        ),
        _event(
            12,
            22,
            "ONE BOUNDED MISSION",
            [
                "Use explicit repository evidence.",
                "Admit only context that fits the byte budget.",
                "Route to an eligible local backend.",
                "Accept only after independent verification.",
                f"capability: {skill['requested_capability']}",
            ],
            fixture=True,
        ),
        _event(
            22,
            38,
            "DECISION RECEIPTS — NOT CHAIN-OF-THOUGHT",
            [
                f"CONTEXT   {benchmark['bounded_serialized_bytes']} B admitted / {benchmark['budget_bytes']} B budget",
                f"CONTEXT   {len(benchmark['sources_loaded'])} loaded / {len(benchmark['sources_omitted'])} omitted sources",
                f"SKILL     {skill['selected_skill']}",
                f"MODEL     {routing['selected_candidate']}",
                f"AUTHORITY R0 read-only / local-only / network denied",
                f"GOVERNOR  {governor['action']} ({governor['reason_code']})",
            ],
            fixture=True,
        ),
        _event(
            38,
            54,
            "EXECUTION IS NOT VERIFICATION",
            [
                f"EXECUTION adapter={exec_receipt['adapter']}",
                f"EXECUTION invocation_occurred={str(exec_receipt['invocation_occurred']).lower()}",
                f"EVIDENCE  {', '.join(verify_receipt['evidence_ids'])}",
                f"VERIFY    {verify_receipt['verification_state']}",
                f"OUTCOME   {inference['status']} / {inference['reason']}",
                "The verifier is a separate receipt linked to the execution receipt.",
            ],
            fixture=True,
        ),
        _event(
            54,
            68,
            "A REAL LOCAL ADAPTER, VERIFIED SEPARATELY",
            [
                f"TOOL      {local['execution_receipt']['adapter']}",
                f"EXECUTION {local['execution_receipt']['execution_state']}",
                f"VERIFY    {local['verification_receipt']['verification_state']}",
                f"EVIDENCE  {len(local['verification_receipt']['evidence_ids'])} verification item(s)",
                "No external side effect. No provider credential.",
            ],
        ),
        _event(
            68,
            78,
            "RESOURCE RECEIPT — ONLY MEASURED CLAIMS",
            [
                f"context naive:    {benchmark['naive_serialized_bytes']} B",
                f"context admitted: {benchmark['bounded_serialized_bytes']} B",
                f"context rejected: {benchmark['bytes_not_admitted']} B",
                f"token estimate:   {benchmark['token_estimate']}",
                (
                    "inference tokens: "
                    f"{exec_receipt['resource_usage']['tokens']['value']} "
                    f"({exec_receipt['resource_usage']['tokens']['status']})"
                ),
                (
                    "inference cost:   "
                    f"{exec_receipt['resource_usage']['cost_usd']['status']}"
                ),
            ],
            fixture=True,
        ),
        _event(
            78,
            82,
            "EXECUTE LESS BLINDLY. VERIFY MORE.",
            [
                "github.com/robertoatila/jarvis-skill-registry",
                "python jarvis.py",
                "Try the quickstart. Break the assumptions. Contribute evidence.",
            ],
        ),
    ]

    return """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Demo,DejaVu Sans Mono,34,&H00F5F7FA,&H000000FF,&H00111827,&H90070B14,0,0,0,0,100,100,0,0,3,3,0,7,120,120,110,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
""" + "\n".join(scenes) + "\n"


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed: "
            + " ".join(command)
            + "\n"
            + (completed.stdout or "")
            + "\n"
            + (completed.stderr or "")
        )


def render_video(*, hero: Path, hud: Path, ass: Path, mp4: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to render demo assets")
    mp4.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[hero];"
        f"[1:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[hud];"
        "[hero][hud]concat=n=2:v=1:a=0,"
        f"ass={ass.as_posix()}[out]"
    )
    _run([
        ffmpeg,
        "-y",
        "-loop",
        "1",
        "-t",
        "2",
        "-i",
        str(hero),
        "-loop",
        "1",
        "-t",
        str(DURATION_SECONDS - 2),
        "-i",
        str(hud),
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-t",
        str(DURATION_SECONDS),
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "24",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(mp4),
    ])


def render_gif(*, mp4: Path, gif: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to render demo assets")
    gif.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        "fps=8,scale=960:-1:flags=lanczos,split[s0][s1];"
        "[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer"
    )
    _run([
        ffmpeg,
        "-y",
        "-ss",
        str(GIF_START_SECONDS),
        "-t",
        str(GIF_DURATION_SECONDS),
        "-i",
        str(mp4),
        "-filter_complex",
        filter_complex,
        "-loop",
        "0",
        str(gif),
    ])


def write_evidence_markdown(
    *,
    path: Path,
    demo: dict[str, Any],
    quickstart: dict[str, Any],
    mp4: Path,
    gif: Path,
) -> None:
    benchmark = demo["context_benchmark"]
    launch = quickstart["checks"]["launch"]
    inference = demo["inference"]
    content = f"""# J.A.R.V.I.S. 90-Second Demo Evidence

This page records the exact evidence used to render the public demo assets. The
video and GIF are generated from real local runtime/CI outputs; the inference
backend shown in the decision sequence is explicitly a deterministic local
fixture and is not presented as a live provider.

## Capture identity

- Demo: `{demo['demo']}`
- Exact source commit: `{demo['commit_sha']}`
- Claim boundary: {demo['claim_boundary']}
- Provider key required: **no**
- Live provider used: **no**

## Public quickstart

- `python jarvis.py --doctor`: **{demo['doctor']['status']}**
- Local HUD: **HTTP {launch['http_status']}**
- HUD URL used by verifier: `{launch['url']}`

## Structured runtime evidence

- Context benchmark: **{benchmark['naive_serialized_bytes']} B naive → {benchmark['bounded_serialized_bytes']} B admitted**, budget {benchmark['budget_bytes']} B.
- Context token estimate: **{benchmark['token_estimate']}** — no byte→token conversion is claimed.
- Skill resolver selected: `{demo['skill']['selected_skill']}`.
- Model router selected: `{inference['routing']['selected_candidate']}`.
- Governor action: `{inference['governor']['action']}`.
- Inference execution receipt: `invocation_occurred={str(inference['execution_receipt']['invocation_occurred']).lower()}`.
- Inference verification receipt: **{inference['verification_receipt']['verification_state']}**.
- Local adapter: `{demo['local_execution']['execution_receipt']['adapter']}`.
- Local verification: **{demo['local_execution']['verification_receipt']['verification_state']}**.

## Media outputs

- 82-second 1920×1080 MP4: [{mp4.name}](../assets/{mp4.name})
- {GIF_DURATION_SECONDS}-second README/social loop: [{gif.name}](../assets/{gif.name})

The rendered captions contain structured receipts and measured evidence only.
They do not expose or claim private chain-of-thought.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render J.A.R.V.I.S. public demo media.")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--quickstart", type=Path, required=True)
    parser.add_argument("--hero", type=Path, required=True)
    parser.add_argument("--hud", type=Path, required=True)
    parser.add_argument("--ass-output", type=Path, required=True)
    parser.add_argument("--mp4-output", type=Path, required=True)
    parser.add_argument("--gif-output", type=Path, required=True)
    parser.add_argument("--evidence-md-output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        demo = _read_json(args.evidence)
        quickstart = _read_json(args.quickstart)
        if demo.get("status") != "PASS":
            raise ValueError("demo evidence is not PASS")
        if quickstart.get("status") != "PASS":
            raise ValueError("quickstart evidence is not PASS")
        if quickstart["checks"]["launch"].get("http_status") != 200:
            raise ValueError("HUD was not observed at HTTP 200")
        args.ass_output.parent.mkdir(parents=True, exist_ok=True)
        args.ass_output.write_text(build_ass(demo, quickstart), encoding="utf-8")
        render_video(
            hero=args.hero,
            hud=args.hud,
            ass=args.ass_output,
            mp4=args.mp4_output,
        )
        render_gif(mp4=args.mp4_output, gif=args.gif_output)
        write_evidence_markdown(
            path=args.evidence_md_output,
            demo=demo,
            quickstart=quickstart,
            mp4=args.mp4_output,
            gif=args.gif_output,
        )
    except Exception as exc:
        print(f"DEMO_RENDER_FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
