# LANCE - Legal Action & Negotiation Command Engine

> A framework for managing legal disputes with the rigor of software engineering. Track evidence, enforce deadlines, escalate automatically, and build legal arguments from structured knowledge.

[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## What Is LANCE?

LANCE applies software engineering lifecycle discipline to legal disputes:

- **Evidence management** with SHA-256 integrity verification and chain of custody
- **Statute of limitations tracking** with jurisdiction-aware auto-calculation
- **Case state machine** with entry/exit criteria (like CI/CD gates)
- **Escalation engine** with rule-based triggers (no response → auto-draft next action)
- **Legal knowledge base** with embedded statutes, case law, and regulations
- **Damages calculator** with prejudgment interest computation
- **Attorney handoff** — one command generates a complete case package

## Philosophy

> "Never regress. Always escalate. Block on critical."

Inspired by [SPEAR](https://github.com/migueljnew-droid/spear-framework) (software engineering), LANCE ensures legal disputes only move forward. Every communication is logged, every deadline is tracked, every escalation is triggered automatically.

```
EVIDENCE ──► DEMAND ──► NEGOTIATION ──► REGULATORY ──► LITIGATION ──► RESOLUTION
    ▲                        │                │
    └────────────────────────┴────────────────┘  (can loop back for new evidence)
```

## Quick Start

### Installation

```bash
# Clone
git clone https://github.com/migueljnew-droid/lance.git
cd lance

# Install dependencies
pip install -r requirements.txt

# Initialize a new case
python -m engine.cli init --name "My Case" --jurisdiction CA
```

### Create a Case

```bash
# Initialize case structure
python -m engine.cli init \
  --name "Smith v. Acme Corp" \
  --type breach_of_contract \
  --jurisdiction CA

# Add evidence
python -m engine.cli evidence add \
  --file contract.pdf \
  --type contract \
  --description "Original agreement dated 2020-01-15"

# Check deadlines
python -m engine.cli deadlines

# View case status
python -m engine.cli status
```

### Claude Code Integration

LANCE ships as a Claude Code skill for AI-assisted legal work:

```bash
/lance status            # Case state, deadlines, pending actions
/lance deadlines         # All deadlines with countdown
/lance escalate          # What should happen next (rule-based)
/lance research [topic]  # Query knowledge base + web for law
/lance argue [claim]     # Build legal argument from evidence + law
/lance damages           # Calculate estimated recovery with interest
/lance audit             # Run financial audit on royalty data
/lance handoff           # Generate attorney package
/lance log [event]       # Record communication or event
```

## Architecture

```
lance/
├── knowledge/              # Legal Knowledge Base (YAML, queryable)
│   ├── statutes/           # Federal and state statutes
│   ├── regulations/        # Agency rules, consent decrees
│   ├── precedent/          # Case law organized by topic
│   └── templates/          # Letter and filing templates
├── engine/                 # Python engine
│   ├── cli.py              # Command-line interface
│   ├── case.py             # Case loader + state machine
│   ├── models.py           # Pydantic data models
│   ├── deadlines.py        # SOL + response deadline calculator
│   ├── evidence.py         # Hashing, chain of custody, manifest
│   ├── communications.py   # Communication tracker
│   ├── escalation.py       # Rule-based escalation engine
│   ├── damages.py          # Damages calculator with interest
│   ├── knowledge.py        # Knowledge base query engine
│   ├── arguments.py        # Legal argument builder
│   └── handoff.py          # Attorney handoff package generator
├── cases/                  # Active cases (one dir per case)
├── skill/                  # Claude Code skill definition
├── tests/                  # Test suite
├── docs/                   # Documentation
└── examples/               # Example case configurations
```

## Core Components

### Case State Machine

Every case moves through defined states with entry/exit criteria:

| State | Entry Criteria | Exit Criteria |
|-------|---------------|---------------|
| `evidence_gathering` | Case created, claim identified | Dossier complete, docs hashed, damages estimated |
| `demand` | Evidence complete | All demands sent, tracking recorded, deadlines set |
| `negotiation` | Respondent acknowledged | Settlement reached OR negotiation failed |
| `regulatory_filing` | Demand expired OR violation found | Complaints filed, confirmations received |
| `mediation` | Both parties agree | Complete (settled or failed) |
| `litigation` | Attorney retained, SOL verified | Judgment or settlement |
| `resolution` | Terms documented | Payment received, registrations corrected |

### Deadline Engine

Tracks two types of deadlines:
- **Response deadlines** — 30/60/90 day windows after sending demands
- **Statute of limitations** — jurisdiction-aware, with discovery rule and tolling support

Alerts at configurable intervals (365, 180, 90, 30, 14, 7, 3, 1 days before expiry).

### Evidence Chain

Every document gets:
- SHA-256 hash (proves integrity)
- Chain of custody entries (who held it, when, what action)
- Claim linkage (which legal claims this evidence supports)
- Metadata (type, date, source, custodian)

### Knowledge Base

Structured YAML files covering:
- **Federal statutes** — Copyright Act (17 USC), Music Modernization Act
- **State statutes** — California Civil Code, CCP, Business & Professions Code
- **Regulations** — ASCAP/BMI consent decrees, MLC rules, Copyright Office procedures
- **Case law** — Organized by topic with facts, holdings, and application notes
- **SOL reference** — By claim type and jurisdiction with tolling doctrines

### Escalation Rules

```yaml
rules:
  - trigger: "no_response"
    days: 30
    action: "draft_follow_up"
  - trigger: "no_response"
    days: 60
    action: "draft_regulatory_complaint"
  - trigger: "settlement_offered"
    action: "compare_against_damages_estimate"
  - trigger: "sol_approaching"
    days: 90
    action: "alert_retain_attorney"
```

### Damages Calculator

- Computes estimated damages from financial discrepancy data
- Applies jurisdiction-specific prejudgment interest rates
- Supports multiple claim types with different calculation methods
- Outputs court-ready damages summary

## Use Cases

LANCE is designed for:

- **Music publishing disputes** — royalty audits, share corrections, publisher accountability
- **Contract disputes** — breach, accounting, fiduciary duty claims
- **IP disputes** — copyright infringement, licensing disagreements
- **Employment disputes** — wage theft, misclassification, benefits claims
- **Consumer disputes** — warranty claims, fraud, unfair business practices
- **Any multi-party dispute** requiring deadline tracking, evidence management, and structured escalation

## Integration

### With Existing Audit Tools

LANCE includes `audit_bridge.py` to integrate with external audit tools (royalty auditors, financial analyzers). Feed audit findings directly into the damages calculator and evidence chain.

### With AI Assistants

The `/lance` Claude Code skill enables natural language interaction:
- "What's the statute of limitations for my fraud claim in California?"
- "Draft a follow-up letter to Warner — it's been 35 days with no response"
- "Build the legal argument for breach of fiduciary duty using evidence EV-001 through EV-005"

### With Legal Research

Knowledge base queries fall through to web search (Perplexity) when embedded knowledge doesn't cover a topic, ensuring you always have current case law.

## Disclaimer

LANCE is a case management and legal research assistance tool. It does NOT provide legal advice. Always consult a licensed attorney for legal decisions. The legal knowledge base is for reference and research purposes only.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

Built by [Louis Gold](https://github.com/migueljnew-droid) | Inspired by [SPEAR Framework](https://github.com/migueljnew-droid/spear-framework)
