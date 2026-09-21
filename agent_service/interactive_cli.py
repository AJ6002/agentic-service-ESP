r"""
Interactive Test Terminal for ESP APM Agent Service (Slice 2).

Directly connects to the live FastAPI /query endpoint (port 8091)
and streams real NDJSON frames:
- AdvisoryFrame (XAI Diagnostic Assessment, Hypotheses, Recommendations, Citations)
- VisualFrame (Active UI Cards chosen by Visualization Planner)
- StatusFrame (Data source health and gateway progress)
- ClarificationFrame (HITL pause for ambiguous slots or missing evidence)
- TextDeltaFrame (Narrative stream)
- DoneFrame (Turn completion status)

Zero stubbed values — 100% synchronized with live backend contracts.

Usage:
  1. Ensure the agent service is running:
     .\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8091
  2. In another terminal, run this CLI:
     .\.venv\Scripts\python.exe interactive_cli.py
"""

import json
import sys
import uuid
import httpx

SERVICE_URL = "http://127.0.0.1:8091"

# Terminal ANSI color helpers
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner(clarify_on_insufficient: bool):
    mode_str = f"{RED}STRICT (Pause on missing evidence){RESET}" if clarify_on_insufficient else f"{GREEN}PARTIAL (Proceed with partial evidence & notes){RESET}"
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}         ESP APM Agent Service — Interactive Test CLI (Slice 2)       {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print("Commands:")
    print(f"  {YELLOW}/new{RESET}      — Reset and start a fresh session")
    print(f"  {YELLOW}/strict{RESET}   — Enable pause on insufficient evidence")
    print(f"  {YELLOW}/partial{RESET}  — Allow diagnosis with partial evidence & status notes")
    print(f"  {YELLOW}/health{RESET}   — Check backend server status")
    print(f"  {YELLOW}/exit{RESET}     — Quit")
    print(f"Mode: {mode_str}")
    print("----------------------------------------------------------------------\n")


def check_health(client: httpx.Client) -> bool:
    try:
        resp = client.get(f"{SERVICE_URL}/health", timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            print(f"{GREEN}[Server Online]{RESET} status={data.get('status')} service={data.get('service')} slice={data.get('slice', 2)}")
            return True
        else:
            print(f"{RED}[Server Error]{RESET} HTTP {resp.status_code}")
            return False
    except Exception:
        print(f"{RED}[Server Offline]{RESET} Could not connect to {SERVICE_URL}.")
        print("Please start the backend with:")
        print(f"  {YELLOW}.\\.venv\\Scripts\\uvicorn app.main:app --host 127.0.0.1 --port 8091{RESET}")
        return False


def render_advisory_frame(frame: dict):
    advisory = frame.get("advisory", {})
    if not advisory or not isinstance(advisory, dict):
        return

    assessment = advisory.get("assessment")
    hypotheses = advisory.get("hypotheses", [])
    recommendation = advisory.get("recommendation")
    verification_steps = advisory.get("verification_steps", [])
    confidence = advisory.get("confidence")
    source_refs = frame.get("source_refs") or advisory.get("cited_evidence_ids", [])

    print(f"\n{BOLD}{MAGENTA}╔════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{MAGENTA}║                     XAI DIAGNOSTIC ADVISORY                        ║{RESET}")
    print(f"{BOLD}{MAGENTA}╚════════════════════════════════════════════════════════════════════╝{RESET}")

    if confidence is not None:
        try:
            conf_pct = float(confidence) * 100
            conf_color = GREEN if conf_pct >= 85 else (YELLOW if conf_pct >= 60 else RED)
            print(f" {BOLD}Confidence:{RESET} {conf_color}{conf_pct:.1f}%{RESET}")
        except (ValueError, TypeError):
            print(f" {BOLD}Confidence:{RESET} {confidence}")

    if assessment:
        print(f"\n {BOLD}{CYAN}▶ ASSESSMENT:{RESET}\n   {assessment}")

    if hypotheses:
        print(f"\n {BOLD}{YELLOW}▶ HYPOTHESES:{RESET}")
        for i, h in enumerate(hypotheses, start=1):
            print(f"   [{i}] {h}")

    if recommendation:
        print(f"\n {BOLD}{GREEN}▶ RECOMMENDATION:{RESET}\n   {recommendation}")

    if verification_steps:
        print(f"\n {BOLD}{BLUE}▶ VERIFICATION STEPS:{RESET}")
        for s in verification_steps:
            print(f"   • {s}")

    if source_refs:
        print(f"\n {BOLD}{DIM}▶ CITED EVIDENCE PROVENANCE:{RESET} {DIM}{', '.join(source_refs)}{RESET}")

    print(f"{BOLD}{MAGENTA}──────────────────────────────────────────────────────────────────────{RESET}\n")


def render_visual_frame(frame: dict):
    viz = frame.get("visualization", {})
    if not viz or not isinstance(viz, dict):
        return

    card_ids = viz.get("card_ids") or viz.get("cards", [])
    if not card_ids:
        return

    evidence_ids = viz.get("evidence_ids", [])
    print(f"{BOLD}{CYAN}[ACTIVE UI CARDS]:{RESET} ", end="")
    for cid in card_ids:
        print(f"{BOLD}[{cid}]{RESET} ", end="")
    print()
    if evidence_ids:
        print(f"{DIM}  Supporting Evidence: {', '.join(evidence_ids)}{RESET}")
    print()


def main():
    clarify_on_insufficient = False
    print_banner(clarify_on_insufficient)

    session_id = f"cli-session-{uuid.uuid4().hex[:6]}"
    pending_options: list[str] = []

    with httpx.Client(timeout=60.0) as client:
        check_health(client)
        print(f"\n{BOLD}Active Session ID:{RESET} {CYAN}{session_id}{RESET}\n")

        while True:
            try:
                user_input = input(f"{BOLD}{GREEN}You > {RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                sys.exit(0)

            if not user_input:
                continue

            if user_input.lower() in ("/exit", "exit", "quit"):
                print("Goodbye.")
                sys.exit(0)

            if user_input.lower() == "/new":
                session_id = f"cli-session-{uuid.uuid4().hex[:6]}"
                pending_options = []
                print(f"\n{YELLOW}[Session Reset]{RESET} New Session ID: {CYAN}{session_id}{RESET}\n")
                continue

            if user_input.lower() == "/strict":
                clarify_on_insufficient = True
                print(f"\n{YELLOW}[Mode Changed]{RESET} {RED}STRICT mode enabled{RESET} (will pause for clarification if required evidence is missing).\n")
                continue

            if user_input.lower() == "/partial":
                clarify_on_insufficient = False
                print(f"\n{YELLOW}[Mode Changed]{RESET} {GREEN}PARTIAL mode enabled{RESET} (will proceed with partial evidence and surface status notes).\n")
                continue

            if user_input.lower() == "/health":
                check_health(client)
                print()
                continue

            # If user picked a number from presented options (e.g. "1" -> "Proceed with partial evidence")
            if pending_options and user_input.isdigit():
                idx = int(user_input) - 1
                if 0 <= idx < len(pending_options):
                    user_input = pending_options[idx]
                    print(f"  {YELLOW}Selected option: {user_input}{RESET}")

            # Send real query to backend /query endpoint with streaming NDJSON
            payload = {
                "session_id": session_id,
                "message": user_input,
                "clarify_on_insufficient": clarify_on_insufficient,
            }

            try:
                with client.stream("POST", f"{SERVICE_URL}/query", json=payload) as resp:
                    if resp.status_code != 200:
                        print(f"{RED}[API Error {resp.status_code}]{RESET} {resp.read().decode('utf-8')}\n")
                        continue

                    pending_options = []
                    text_started = False
                    advisory_rendered = False

                    for line in resp.iter_lines():
                        if not line or not line.strip():
                            continue

                        try:
                            frame = json.loads(line)
                        except Exception:
                            continue

                        frame_type = frame.get("type")

                        # 1. Status Frame (Gateway progress / data source health)
                        if frame_type == "status":
                            stage = frame.get("stage", "")
                            msg = frame.get("message", "")
                            stage_prefix = f"[{stage.upper()}] " if stage else ""
                            print(f"{YELLOW}[STATUS] {stage_prefix}{msg}{RESET}")

                        # 2. Advisory Frame (Real XAI Diagnostic output)
                        elif frame_type == "advisory":
                            render_advisory_frame(frame)
                            advisory_rendered = True

                        # 3. Visual Frame (Active UI Cards selection)
                        elif frame_type == "visual":
                            render_visual_frame(frame)

                        # 4. Clarification Halt
                        elif frame_type == "clarification":
                            question = frame.get("question", "Please clarify:")
                            slot = frame.get("slot")
                            opts = frame.get("options", [])
                            pending_options = opts

                            print(f"\n{BOLD}{YELLOW}Agent [PAUSED]:{RESET} {question}")
                            if opts:
                                for i, opt in enumerate(opts, start=1):
                                    print(f"  {CYAN}[{i}]{RESET} {opt}")
                                print(f"  {DIM}(Type the number or enter custom text){RESET}")
                            print()

                        # 5. Text Delta (Answer narrative stream)
                        elif frame_type == "text_delta":
                            delta = frame.get("delta", "")
                            # If advisory was already rendered in full structure, supplemental delta is printed cleanly
                            if not text_started:
                                prefix = f"\n{BOLD}{CYAN}Diagnostic Narrative:{RESET}\n" if advisory_rendered else f"\n{BOLD}{CYAN}Agent:{RESET} "
                                print(prefix, end="", flush=True)
                                text_started = True
                            print(delta, end="", flush=True)

                        # 6. Error Frame
                        elif frame_type == "error":
                            code = frame.get("code", "ERROR")
                            msg = frame.get("message", "")
                            print(f"\n{RED}[ERROR {code}]{RESET} {msg}\n")

                        # 7. Done Frame
                        elif frame_type == "done":
                            status = frame.get("status")
                            if text_started:
                                print("\n")
                            if status == "PAUSED":
                                pass
                            elif status == "OK":
                                pass
                            else:
                                print(f"{YELLOW}[Turn Finished: {status}]{RESET}\n")

            except httpx.ConnectError:
                print(f"{RED}[Connection Failed]{RESET} Could not connect to {SERVICE_URL}. Is the uvicorn server running?\n")
            except Exception as ex:
                print(f"{RED}[Request Error]{RESET} {ex}\n")


if __name__ == "__main__":
    main()
