"""LANCE Command-Line Interface."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from . import __version__
from .case import CaseManager
from .communications import CommunicationTracker
from .damages import DamagesCalculator
from .deadlines import DeadlineEngine
from .escalation import EscalationEngine
from .evidence import EvidenceManager, EvidenceType
from .handoff import HandoffGenerator
from .knowledge import KnowledgeBase
from .models import Case, CaseState, Jurisdiction, Party


def main():
    parser = argparse.ArgumentParser(
        prog="lance",
        description="LANCE — Legal Action & Negotiation Command Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  init          Initialize a new case
  status        Show case status
  deadlines     Show all deadlines with countdown
  escalate      Evaluate escalation rules and recommend actions
  evidence      Manage evidence (add, verify, list)
  comms         Manage communications (log, list, awaiting)
  damages       Calculate estimated damages with interest
  search        Search legal knowledge base
  handoff       Generate attorney handoff package
  transition    Transition case to new state

Examples:
  lance init --name "Smith v. Acme" --jurisdiction CA
  lance status --case-dir ./cases/smith_v_acme
  lance deadlines
  lance escalate
  lance evidence add --file contract.pdf --type contract --title "Original Agreement"
  lance evidence verify
  lance damages --principal 30000 --start 2015-01-01
  lance search "statute of limitations fraud california"
  lance handoff
        """,
    )
    parser.add_argument("--version", action="version", version=f"LANCE v{__version__}")
    parser.add_argument("--case-dir", default=".", help="Path to case directory")

    subparsers = parser.add_subparsers(dest="command")

    # ── init ──
    init_parser = subparsers.add_parser("init", help="Initialize a new case")
    init_parser.add_argument("--name", required=True, help="Case name/title")
    init_parser.add_argument("--type", default="general", help="Case type")
    init_parser.add_argument("--jurisdiction", default="CA", help="Primary jurisdiction")
    init_parser.add_argument("--claimant", default="", help="Claimant name")
    init_parser.add_argument("--output", default=".", help="Output directory")

    # ── status ──
    subparsers.add_parser("status", help="Show case status")

    # ── deadlines ──
    subparsers.add_parser("deadlines", help="Show all deadlines")

    # ── escalate ──
    subparsers.add_parser("escalate", help="Evaluate escalation rules")

    # ── evidence ──
    ev_parser = subparsers.add_parser("evidence", help="Manage evidence")
    ev_sub = ev_parser.add_subparsers(dest="evidence_command")

    ev_add = ev_sub.add_parser("add", help="Add evidence file")
    ev_add.add_argument("--file", required=True, help="Path to evidence file")
    ev_add.add_argument("--title", required=True, help="Evidence title")
    ev_add.add_argument("--type", required=True, choices=[e.value for e in EvidenceType])
    ev_add.add_argument("--description", default="", help="Description")
    ev_add.add_argument("--custodian", default="", help="Custodian name")
    ev_add.add_argument("--claims", nargs="+", default=[], help="Related claim IDs")

    ev_sub.add_parser("verify", help="Verify evidence integrity")
    ev_sub.add_parser("list", help="List all evidence")

    # ── comms ──
    comms_parser = subparsers.add_parser("comms", help="Manage communications")
    comms_sub = comms_parser.add_subparsers(dest="comms_command")
    comms_sub.add_parser("list", help="List all communications")
    comms_sub.add_parser("awaiting", help="Show communications awaiting response")

    # ── damages ──
    dmg_parser = subparsers.add_parser("damages", help="Calculate damages")
    dmg_parser.add_argument("--principal", type=float, required=True, help="Underpayment amount")
    dmg_parser.add_argument("--start", required=True, help="Underpayment start date (YYYY-MM-DD)")
    dmg_parser.add_argument("--claim-id", default="CLM-001", help="Claim ID")
    dmg_parser.add_argument("--rate", type=float, help="Override interest rate")
    dmg_parser.add_argument("--jurisdiction", default="CA", help="Jurisdiction for interest rate")

    # ── search ──
    search_parser = subparsers.add_parser("search", help="Search knowledge base")
    search_parser.add_argument("query", nargs="+", help="Search query")
    search_parser.add_argument("--category", help="Limit to category (statutes, precedent, regulations)")

    # ── handoff ──
    ho_parser = subparsers.add_parser("handoff", help="Generate attorney handoff package")
    ho_parser.add_argument("--output", help="Output directory")

    # ── transition ──
    tr_parser = subparsers.add_parser("transition", help="Transition case state")
    tr_parser.add_argument("--to", required=True, choices=[s.value for s in CaseState])
    tr_parser.add_argument("--reason", default="", help="Reason for transition")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    case_dir = Path(args.case_dir).resolve()

    try:
        if args.command == "init":
            _cmd_init(args, case_dir)
        elif args.command == "status":
            _cmd_status(case_dir)
        elif args.command == "deadlines":
            _cmd_deadlines(case_dir)
        elif args.command == "escalate":
            _cmd_escalate(case_dir)
        elif args.command == "evidence":
            _cmd_evidence(args, case_dir)
        elif args.command == "comms":
            _cmd_comms(args, case_dir)
        elif args.command == "damages":
            _cmd_damages(args, case_dir)
        elif args.command == "search":
            _cmd_search(args, case_dir)
        elif args.command == "handoff":
            _cmd_handoff(args, case_dir)
        elif args.command == "transition":
            _cmd_transition(args, case_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_init(args, case_dir):
    output = Path(args.output).resolve()
    case = Case(
        id=f"CASE-{date.today().strftime('%Y%m%d')}",
        title=args.name,
        type=args.type,
        jurisdiction=Jurisdiction(
            primary_state=args.jurisdiction,
            governing_law=args.jurisdiction,
        ),
        claimant=Party(
            id="claimant",
            name=args.claimant or "TBD",
            role="claimant",
        ),
    )
    mgr = CaseManager.init_case(output, case)
    print(f"Case initialized: {mgr.case.title}")
    print(f"  ID: {mgr.case.id}")
    print(f"  State: {mgr.case.state.value}")
    print(f"  Directory: {output}")


def _cmd_status(case_dir):
    mgr = CaseManager(case_dir)
    summary = mgr.status_summary()
    print(f"{'='*60}")
    print(f"  LANCE — Case Status")
    print(f"{'='*60}")
    print(f"  Case:   {summary['title']}")
    print(f"  ID:     {summary['case_id']}")
    print(f"  State:  {summary['state']} — {summary['state_description']}")
    print(f"  Claims: {summary['claims_count']}")
    print(f"  Events: {summary['total_events']}")
    print(f"  Last:   {summary['last_event']}")
    print(f"{'='*60}")
    print(f"  Exit criteria for current state:")
    for criterion in summary["exit_criteria"]:
        print(f"    [ ] {criterion}")
    print(f"  Allowed transitions: {', '.join(summary['allowed_transitions'])}")


def _cmd_deadlines(case_dir):
    engine = DeadlineEngine(case_dir)
    report = engine.check_deadlines()
    print(f"{'='*60}")
    print(f"  DEADLINES — as of {report['as_of']}")
    print(f"{'='*60}")
    for category in ["expired", "urgent", "approaching", "active"]:
        items = report.get(category, [])
        if items:
            print(f"\n  [{category.upper()}]")
            for dl in items:
                days = dl["days_remaining"]
                marker = f"{days} days" if days >= 0 else f"{abs(days)} days OVERDUE"
                print(f"    {dl['id']}: {dl['description']}")
                print(f"           Due: {dl['due_date']} ({marker})")
    if not any(report.get(c) for c in ["expired", "urgent", "approaching", "active"]):
        print("  No active deadlines.")


def _cmd_escalate(case_dir):
    comms = CommunicationTracker(case_dir)
    deadlines = DeadlineEngine(case_dir)
    engine = EscalationEngine(case_dir)
    triggered = engine.evaluate(comms, deadlines)
    print(f"{'='*60}")
    print(f"  ESCALATION EVALUATION")
    print(f"{'='*60}")
    if not triggered:
        print("  No escalation actions triggered.")
    else:
        for t in triggered:
            print(f"\n  [{t['priority']}] {t['rule_name']}")
            print(f"      Action: {t['action']}")
            print(f"      {t['description']}")
            ctx = t.get("context", {})
            if "days_overdue" in ctx:
                print(f"      Overdue: {ctx['days_overdue']} days")
            if "counterparty" in ctx:
                print(f"      Party: {ctx['counterparty']}")


def _cmd_evidence(args, case_dir):
    mgr = EvidenceManager(case_dir)
    if args.evidence_command == "add":
        item = mgr.add_evidence(
            file_path=Path(args.file),
            title=args.title,
            evidence_type=EvidenceType(args.type),
            description=args.description,
            custodian=args.custodian,
            claim_ids=args.claims,
        )
        print(f"Evidence added: {item.id} — {item.title}")
        print(f"  SHA-256: {item.sha256}")
        print(f"  File: {item.filename}")
    elif args.evidence_command == "verify":
        results = mgr.verify_integrity()
        print(f"Evidence Integrity Check:")
        for r in results:
            status = r["status"]
            icon = "+" if status == "VERIFIED" else "!" if status == "MISSING" else "X"
            print(f"  [{icon}] {r['id']}: {r['title']} — {status}")
    elif args.evidence_command == "list":
        summary = mgr.summary()
        print(f"Evidence: {summary['total_items']} items")
        for item in mgr.manifest.evidence:
            print(f"  {item.id}: {item.title} ({item.type.value})")
    else:
        print("Use: lance evidence {add|verify|list}")


def _cmd_comms(args, case_dir):
    tracker = CommunicationTracker(case_dir)
    if args.comms_command == "awaiting":
        awaiting = tracker.get_awaiting_response()
        if not awaiting:
            print("No communications awaiting response.")
        else:
            for a in awaiting:
                status = "OVERDUE" if a["overdue"] else "waiting"
                print(f"  {a['id']}: [{status}] {a['summary']}")
                print(f"         Sent: {a['sent_date']} via {a['method']}")
                print(f"         Deadline: {a['response_deadline']} ({a['days_waiting']} days)")
    elif args.comms_command == "list":
        summary = tracker.summary()
        print(f"Communications: {summary['total']} total ({summary['outbound']} out, {summary['inbound']} in)")
        for comm in tracker.communications:
            direction = "->" if comm.direction == "outbound" else "<-"
            print(f"  {comm.id} {direction} {comm.counterparty_id}: {comm.summary} [{comm.status.value}]")
    else:
        print("Use: lance comms {list|awaiting}")


def _cmd_damages(args, case_dir):
    calc = DamagesCalculator(jurisdiction=args.jurisdiction)
    start = date.fromisoformat(args.start)
    estimate = calc.calculate(
        claim_id=args.claim_id,
        principal=args.principal,
        underpayment_start=start,
        custom_rate=args.rate,
    )
    print(f"{'='*60}")
    print(f"  DAMAGES ESTIMATE")
    print(f"{'='*60}")
    print(f"  Principal:       ${estimate.principal:>12,.2f}")
    print(f"  Interest Rate:   {estimate.interest_rate*100:.1f}% per annum")
    print(f"  Interest Period: {start} to {date.today()}")
    print(f"  Accrued Interest:${estimate.accrued_interest:>12,.2f}")
    print(f"  {'─'*40}")
    print(f"  TOTAL:           ${estimate.total_with_interest:>12,.2f}")
    print(f"{'='*60}")
    print(f"  Method: {estimate.calculation_method}")


def _cmd_search(args, case_dir):
    # Try to find knowledge base relative to lance install
    kb_paths = [
        case_dir / "knowledge",
        Path(__file__).parent.parent / "knowledge",
    ]
    kb_dir = None
    for p in kb_paths:
        if p.exists():
            kb_dir = p
            break

    if kb_dir is None:
        print("Knowledge base not found. Expected at ./knowledge/ or ../knowledge/")
        sys.exit(1)

    kb = KnowledgeBase(kb_dir)
    query = " ".join(args.query)
    categories = [args.category] if args.category else None
    results = kb.search(query, categories)

    if not results:
        print(f"No results for: {query}")
    else:
        print(f"Found {len(results)} results for: {query}\n")
        for r in results[:10]:
            cat = r.pop("category", "unknown")
            print(f"  [{cat}] {r.get('title', r.get('name', r.get('citation', 'Untitled')))}")
            if "statute" in r:
                print(f"         Statute: {r['statute']}")
            if "holding" in r:
                print(f"         {r['holding'][:120]}...")
            print()


def _cmd_handoff(args, case_dir):
    gen = HandoffGenerator(case_dir)
    output = Path(args.output) if args.output else None
    package_dir = gen.generate(output)
    print(f"Attorney handoff package generated:")
    print(f"  {package_dir}")
    for f in sorted(package_dir.rglob("*")):
        if f.is_file():
            print(f"  └ {f.relative_to(package_dir)}")


def _cmd_transition(args, case_dir):
    mgr = CaseManager(case_dir)
    target = CaseState(args.to)
    event = mgr.transition(target, reason=args.reason)
    print(f"State transitioned: {event.description}")


if __name__ == "__main__":
    main()
