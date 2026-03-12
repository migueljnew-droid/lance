<div align="center">

<br />

<picture>
  <img src="assets/banner.svg" alt="LANCE Framework" width="100%" />
</picture>

<br /><br />

<img src="https://img.shields.io/badge/LANCE-LEGAL%20COMMAND%20ENGINE-000000?style=for-the-badge&labelColor=8b0000&color=000000" alt="LANCE" />

<br /><br />

<img src="https://img.shields.io/badge/case%20states-7-cc2222?style=flat-square" alt="7 Case States" />&nbsp;
<img src="https://img.shields.io/badge/knowledge%20base-statutes%20%2B%20case%20law-cc2222?style=flat-square" alt="Knowledge Base" />&nbsp;
<img src="https://img.shields.io/badge/evidence-SHA--256%20verified-cc2222?style=flat-square" alt="SHA-256 Verified" />&nbsp;
<img src="https://img.shields.io/badge/python-3.10+-cc2222?style=flat-square" alt="Python 3.10+" />&nbsp;
<img src="https://img.shields.io/badge/license-MIT-cc2222?style=flat-square" alt="MIT License" />

<br /><br />

**A framework for managing legal disputes with software engineering rigor.**<br />
Track evidence. Enforce deadlines. Escalate automatically. Build arguments from structured knowledge.

</div>

<br />

---

<br />

## What Is LANCE?

LANCE applies software engineering lifecycle discipline to legal disputes:

> **Evidence management** with SHA-256 integrity verification and chain of custody
>
> **Statute of limitations tracking** with jurisdiction-aware auto-calculation
>
> **Case state machine** with entry/exit criteria (like CI/CD gates)
>
> **Escalation engine** with rule-based triggers (no response → auto-draft next action)
>
> **Legal knowledge base** with embedded statutes, case law, and regulations
>
> **Damages calculator** with prejudgment interest computation
>
> **Attorney handoff** — one command generates a complete case package

<br />

## Philosophy

<div align="center">

> *"Never regress. Always escalate. Block on critical."*

Inspired by [SPEAR](https://github.com/migueljnew-droid/spear-framework) — legal disputes only move forward.

</div>

```
EVIDENCE ──> DEMAND ──> NEGOTIATION ──> REGULATORY ──> LITIGATION ──> RESOLUTION
    ^                        |                |
    └────────────────────────┴────────────────┘  (loops back for new evidence)
```

<br />

## Quick Start

```bash
# Clone
git clone https://github.com/migueljnew-droid/lance.git
cd lance

# Install dependencies
pip install -r requirements.txt

# Initialize a new case
python -m engine.cli init --name "My Case" --jurisdiction CA
```

```bash
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

<br />

## Case State Machine

Every case moves through defined states with entry/exit criteria:

<table>
<tr><th>State</th><th>Entry Criteria</th><th>Exit Criteria</th></tr>
<tr>
<td><img src="https://img.shields.io/badge/-Evidence%20Gathering-444444?style=flat-square" /></td>
<td>Case created, claim identified</td>
<td>Dossier complete, docs hashed, damages estimated</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/-Demand-663333?style=flat-square" /></td>
<td>Evidence complete</td>
<td>All demands sent, tracking recorded, deadlines set</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/-Negotiation-884422?style=flat-square" /></td>
<td>Respondent acknowledged</td>
<td>Settlement reached OR negotiation failed</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/-Regulatory%20Filing-885522?style=flat-square" /></td>
<td>Demand expired OR violation found</td>
<td>Complaints filed, confirmations received</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/-Mediation-886622?style=flat-square" /></td>
<td>Both parties agree</td>
<td>Settled or failed</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/-Litigation-993333?style=flat-square" /></td>
<td>Attorney retained, SOL verified</td>
<td>Judgment or settlement</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/-Resolution-228822?style=flat-square" /></td>
<td>Terms documented</td>
<td>Payment received, registrations corrected</td>
</tr>
</table>

<br />

## Claude Code Integration

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

<br />

## Core Components

<details>
<summary><b>Deadline Engine</b></summary>
<br />

Tracks two types of deadlines:
- **Response deadlines** — 30/60/90 day windows after sending demands
- **Statute of limitations** — jurisdiction-aware, with discovery rule and tolling support

Alerts at configurable intervals (365, 180, 90, 30, 14, 7, 3, 1 days before expiry).

</details>

<details>
<summary><b>Evidence Chain</b></summary>
<br />

Every document gets:
- **SHA-256 hash** — proves integrity
- **Chain of custody entries** — who held it, when, what action
- **Claim linkage** — which legal claims this evidence supports
- **Metadata** — type, date, source, custodian

</details>

<details>
<summary><b>Knowledge Base</b></summary>
<br />

Structured YAML files covering:
- **Federal statutes** — Copyright Act (17 USC), Music Modernization Act
- **State statutes** — California Civil Code, CCP, Business & Professions Code
- **Regulations** — ASCAP/BMI consent decrees, MLC rules, Copyright Office procedures
- **Case law** — Organized by topic with facts, holdings, and application notes
- **SOL reference** — By claim type and jurisdiction with tolling doctrines

</details>

<details>
<summary><b>Escalation Rules</b></summary>
<br />

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

</details>

<details>
<summary><b>Damages Calculator</b></summary>
<br />

- Computes estimated damages from financial discrepancy data
- Applies jurisdiction-specific prejudgment interest rates
- Supports multiple claim types with different calculation methods
- Outputs court-ready damages summary

</details>

<br />

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
│   ├── escalation.py       # Rule-based escalation engine
│   ├── damages.py          # Damages calculator with interest
│   ├── knowledge.py        # Knowledge base query engine
│   ├── arguments.py        # Legal argument builder
│   └── handoff.py          # Attorney handoff package generator
├── cases/                  # Active cases (one dir per case)
├── skill/                  # Claude Code skill definition
├── tests/                  # Test suite
└── examples/               # Example case configurations
```

<br />

## Use Cases

<table>
<tr><td width="40">&#127925;</td><td><b>Music publishing disputes</b> — royalty audits, share corrections, publisher accountability</td></tr>
<tr><td>&#128221;</td><td><b>Contract disputes</b> — breach, accounting, fiduciary duty claims</td></tr>
<tr><td>&#169;</td><td><b>IP disputes</b> — copyright infringement, licensing disagreements</td></tr>
<tr><td>&#128188;</td><td><b>Employment disputes</b> — wage theft, misclassification, benefits claims</td></tr>
<tr><td>&#128722;</td><td><b>Consumer disputes</b> — warranty claims, fraud, unfair business practices</td></tr>
</table>

<br />

## Disclaimer

> LANCE is a case management and legal research assistance tool. It does **NOT** provide legal advice. Always consult a licensed attorney for legal decisions. The legal knowledge base is for reference and research purposes only.

<br />

## License

MIT License. See [LICENSE](LICENSE) for details.

<br />

---

<div align="center">

**Built by [Miguel Jiminez](https://github.com/migueljnew-droid)**&nbsp;&nbsp;·&nbsp;&nbsp;Inspired by [SPEAR Framework](https://github.com/migueljnew-droid/spear-framework)

<br />

<img src="https://img.shields.io/github/stars/migueljnew-droid/lance?style=social" alt="Stars" />&nbsp;&nbsp;
<img src="https://img.shields.io/github/forks/migueljnew-droid/lance?style=social" alt="Forks" />

</div>
