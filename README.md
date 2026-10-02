# Media Pitch Agent

An AI agent that turns daily **HARO (Help a Reporter Out)** journalist-query
digests into ready-to-send media pitches — automatically scored for relevance
and drafted in each client's voice.

Built with the Anthropic API (Claude). One generic engine serves any number of
clients: each client is a single profile file, so onboarding a new company takes
minutes, not a rewrite.

> **Note:** The UET and InfluxData profiles are illustrative examples built
> entirely from public information. They do not represent real client engagements
> or any confidential data.

## What it does

For a given HARO digest, the agent:

1. **Extracts** every journalist query from the digest
2. **Scores** each query 1–10 for relevance to the client
3. **Drafts a pitch** (150–250 words, in the client's voice) for every query
   scoring 7 or higher
4. **Summarizes** the day: how many queries were reviewed, how many cleared the
   bar, and which pitches to send

This filters out the noise (a typical digest has dozens of queries, most
irrelevant) so the user only reviews and sends the handful worth pitching —
classic human-in-the-loop.

## How it's structured

```
media-pitch-agent/
├── media_pitch_agent.py      # the engine — client-agnostic
├── prompt/base.md            # shared instructions: role, scoring, output format
├── profiles/                 # one file per client
│   ├── uet.md                #   Universal Edge Technologies
│   └── influxdata.md         #   InfluxData
├── samples/                  # example HARO digests for testing
└── outputs/                  # generated pitches (git-ignored)
```

The system prompt sent to Claude is **`base.md` + the chosen profile**. The
engine never hard-codes a company — all client specifics (positioning, scoring
tiers, tone, differentiation) live in the profile, which is why adding a new
client is just one new `profiles/<name>.md` file.

## Usage

Requires Python 3 and an Anthropic API key.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-...        # Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-..."

python media_pitch_agent.py samples/influxdata-haro-digest.txt --profile influxdata
```

Output streams to the terminal and is saved to `outputs/<profile>_pitches_<timestamp>.md`.

## Add a new client

1. Copy an existing file in `profiles/` (e.g. `influxdata.md`)
2. Fill in the new company's profile, scoring tiers, and pitch specifics
3. Run with `--profile <new-name>`

## Notes

- The API key is read from the `ANTHROPIC_API_KEY` environment variable and is
  never stored in the repo.
- Pitches are **drafts for human review** — the agent recommends; a person sends.
