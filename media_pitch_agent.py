#!/usr/bin/env python3
"""
Media Pitch Agent
Monitors HARO (Help a Reporter Out) email digests and drafts media pitches on
behalf of a client, using the Anthropic API.

The shared instructions live in prompt/base.md; each client's details live in
profiles/<name>.md. The system prompt sent to Claude is base + the chosen profile,
so adding a new client is just one new profile file.

Usage:
    python media_pitch_agent.py <digest.txt> --profile <name>
    python media_pitch_agent.py samples/influxdata-haro-digest.txt --profile influxdata
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

import anthropic


ROOT = Path(__file__).parent
BASE_PROMPT_PATH = ROOT / "prompt" / "base.md"
PROFILES_DIR = ROOT / "profiles"
OUTPUTS_DIR = ROOT / "outputs"

MODEL = "claude-opus-4-8"


def load_system_prompt(profile_name: str) -> str:
    if not BASE_PROMPT_PATH.exists():
        raise FileNotFoundError(f"Base prompt not found at {BASE_PROMPT_PATH}")
    base = BASE_PROMPT_PATH.read_text(encoding="utf-8")

    profile_path = PROFILES_DIR / f"{profile_name}.md"
    if not profile_path.exists():
        available = ", ".join(sorted(p.stem for p in PROFILES_DIR.glob("*.md"))) or "none"
        raise FileNotFoundError(
            f"Profile '{profile_name}' not found at {profile_path}. "
            f"Available profiles: {available}"
        )
    profile = profile_path.read_text(encoding="utf-8")
    return f"{base}\n\n---\n\n{profile}"


def load_digest(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Digest file not found: {file_path}")
    return path.read_text(encoding="utf-8")


def save_output(content: str, profile_name: str) -> Path:
    OUTPUTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUTS_DIR / f"{profile_name}_pitches_{timestamp}.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def run_agent(digest_text: str, system_prompt: str) -> str:
    client = anthropic.Anthropic()

    user_message = f"""Please process the following HARO email digest. Extract all journalist queries, score each for relevance, and draft pitches for queries scoring 7 or higher.

HARO DIGEST:
{digest_text}"""

    print("Sending digest to Claude... (streaming)\n")
    print("=" * 60)

    full_response = ""

    with client.messages.stream(
        model=MODEL,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

    print("\n" + "=" * 60)
    return full_response


def main():
    parser = argparse.ArgumentParser(
        description="Media Pitch Agent — processes HARO digests and drafts pitches for a client"
    )
    parser.add_argument(
        "digest_file",
        help="Path to the HARO email digest text file",
    )
    parser.add_argument(
        "--profile",
        "-p",
        required=True,
        help="Client profile name (a file in profiles/ without the .md extension), e.g. influxdata",
    )
    args = parser.parse_args()

    try:
        system_prompt = load_system_prompt(args.profile)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        digest_text = load_digest(args.digest_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not digest_text.strip():
        print("Error: Digest file is empty.", file=sys.stderr)
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    try:
        result = run_agent(digest_text, system_prompt)
    except anthropic.AuthenticationError:
        print("\nError: Invalid API key. Check your ANTHROPIC_API_KEY.", file=sys.stderr)
        sys.exit(1)
    except anthropic.RateLimitError:
        print("\nError: Rate limit hit. Please wait and try again.", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIConnectionError:
        print("\nError: Could not connect to the Anthropic API. Check your internet connection.", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIStatusError as e:
        print(f"\nError: API returned status {e.status_code}: {e.message}", file=sys.stderr)
        sys.exit(1)

    try:
        output_path = save_output(result, args.profile)
        print(f"\nOutput saved to: {output_path}")
    except OSError as e:
        print(f"\nWarning: Could not save output file: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
