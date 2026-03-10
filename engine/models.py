"""Pydantic models for LANCE case data structures."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──


class CaseState(str, Enum):
    EVIDENCE_GATHERING = "evidence_gathering"
    DEMAND = "demand"
    NEGOTIATION = "negotiation"
    REGULATORY_FILING = "regulatory_filing"
    MEDIATION = "mediation"
    LITIGATION = "litigation"
    RESOLUTION = "resolution"
    CLOSED = "closed"


class ClaimType(str, Enum):
    BREACH_OF_CONTRACT = "breach_of_contract"
    BREACH_OF_FIDUCIARY_DUTY = "breach_of_fiduciary_duty"
    FRAUD = "fraud"
    ACCOUNTING = "accounting"
    COPYRIGHT_INFRINGEMENT = "copyright_infringement"
    UNFAIR_BUSINESS_PRACTICES = "unfair_business_practices"
    UNJUST_ENRICHMENT = "unjust_enrichment"
    DECLARATORY_JUDGMENT = "declaratory_judgment"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class EvidenceType(str, Enum):
    CONTRACT = "contract"
    ROYALTY_STATEMENT = "royalty_statement"
    CORRESPONDENCE = "correspondence"
    FINANCIAL_RECORD = "financial_record"
    REGISTRATION = "registration"
    SCREENSHOT = "screenshot"
    AUDIO_VIDEO = "audio_video"
    EXPERT_REPORT = "expert_report"
    COURT_FILING = "court_filing"
    OTHER = "other"


class CommMethod(str, Enum):
    CERTIFIED_MAIL = "certified_mail"
    EMAIL = "email"
    PHONE = "phone"
    IN_PERSON = "in_person"
    PORTAL = "portal"
    FAX = "fax"
    PROCESS_SERVER = "process_server"


class CommStatus(str, Enum):
    DRAFTED = "drafted"
    SENT = "sent"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    RESPONDED = "responded"
    IGNORED = "ignored"
    RETURNED = "returned"


class DeadlineType(str, Enum):
    RESPONSE = "response_deadline"
    SOL = "statute_of_limitations"
    FILING = "filing_deadline"
    HEARING = "hearing_date"
    DISCOVERY = "discovery_deadline"
    CUSTOM = "custom"


class DeadlineStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    APPROACHING = "approaching"
    URGENT = "urgent"
    EXPIRED = "expired"
    COMPLETED = "completed"
    WAIVED = "waived"


# ── Core Models ──


class Party(BaseModel):
    """A party to the dispute (claimant, respondent, third party)."""
    id: str
    name: str
    role: str
    entity: Optional[str] = None
    aka: Optional[list[str]] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    counsel: Optional[str] = None
    ipi: Optional[str] = None  # Music-specific: IPI/CAE number
    notes: Optional[str] = None


class Jurisdiction(BaseModel):
    """Jurisdiction and venue information."""
    primary_state: str = Field(description="Primary state (e.g., 'CA')")
    federal: bool = False
    governing_law: str = Field(description="Which state's law governs")
    venue: Optional[str] = None
    notes: Optional[str] = None


class Claim(BaseModel):
    """A legal claim in the dispute."""
    id: str
    type: ClaimType
    description: str
    statute: Optional[str] = None
    sol_years: Optional[float] = None
    accrual_date: Optional[date] = None
    discovery_date: Optional[date] = None
    sol_expiry: Optional[date] = None
    tolling_basis: Optional[str] = None
    estimated_damages: Optional[float] = None
    notes: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)


class ContractTerms(BaseModel):
    """Key terms of the underlying contract."""
    type: str
    date_signed: Optional[date] = None
    deal_id: Optional[str] = None
    key_terms: list[str] = Field(default_factory=list)
    audit_clause: Optional[str] = None
    objection_period_days: Optional[int] = None
    term: Optional[str] = None
    governing_law: Optional[str] = None
    notes: Optional[str] = None


# ── Evidence Models ──


class CustodyEntry(BaseModel):
    """A chain of custody entry for evidence."""
    date: date
    holder: str
    action: str
    notes: Optional[str] = None


class EvidenceItem(BaseModel):
    """A piece of evidence in the case."""
    id: str
    title: str
    filename: str
    type: EvidenceType
    date_created: Optional[date] = None
    date_obtained: Optional[date] = None
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    source: Optional[str] = None
    custodian: Optional[str] = None
    description: Optional[str] = None
    relevance: list[str] = Field(default_factory=list, description="Claim IDs")
    chain_of_custody: list[CustodyEntry] = Field(default_factory=list)

    def compute_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of the evidence file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        self.sha256 = h.hexdigest()
        return self.sha256


class EvidenceManifest(BaseModel):
    """Registry of all evidence items."""
    version: int = 1
    case_id: str
    evidence: list[EvidenceItem] = Field(default_factory=list)


# ── Communication Models ──


class Communication(BaseModel):
    """A communication sent or received."""
    id: str
    direction: str = Field(description="'outbound' or 'inbound'")
    date: date
    counterparty_id: str
    method: CommMethod
    status: CommStatus = CommStatus.DRAFTED
    subject: Optional[str] = None
    summary: str
    documents: list[str] = Field(default_factory=list)
    tracking_number: Optional[str] = None
    response_deadline: Optional[date] = None
    response_received: Optional[date] = None
    notes: Optional[str] = None


# ── Deadline Models ──


class EscalationAction(BaseModel):
    """Action to take when a deadline expires."""
    action: str
    escalation_rule: Optional[str] = None
    description: Optional[str] = None


class Deadline(BaseModel):
    """A tracked deadline."""
    id: str
    type: DeadlineType
    description: str
    claim_id: Optional[str] = None
    trigger_date: date
    trigger_event: Optional[str] = None
    days: int
    due_date: date
    alert_days_before: list[int] = Field(default_factory=lambda: [30, 14, 7, 3, 1])
    status: DeadlineStatus = DeadlineStatus.PENDING
    on_expiry: Optional[EscalationAction] = None
    notes: Optional[str] = None

    @property
    def days_remaining(self) -> int:
        return (self.due_date - date.today()).days


# ── Event Log Models ──


class Event(BaseModel):
    """An event in the case timeline (append-only log)."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    type: str
    actor: str
    description: str
    metadata: dict = Field(default_factory=dict)


# ── Escalation Rule Models ──


class EscalationRule(BaseModel):
    """A rule that triggers escalation."""
    id: str
    name: str
    trigger: str
    counterparty_id: Optional[str] = None
    days: Optional[int] = None
    condition: Optional[str] = None
    action: str
    action_description: str
    priority: int = 1


# ── Damages Models ──


class DamagesEstimate(BaseModel):
    """Estimated damages for a claim."""
    claim_id: str
    principal: float
    interest_rate: float = 0.10  # CA default: 10% per annum
    interest_start_date: Optional[date] = None
    accrued_interest: float = 0.0
    total_with_interest: float = 0.0
    calculation_method: Optional[str] = None
    notes: Optional[str] = None


# ── Master Case Model ──


class Case(BaseModel):
    """The master case file."""
    id: str
    title: str
    type: str
    state: CaseState = CaseState.EVIDENCE_GATHERING
    priority: str = "high"
    jurisdiction: Jurisdiction
    claimant: Party
    respondents: list[Party] = Field(default_factory=list)
    third_parties: list[Party] = Field(default_factory=list)
    contract: Optional[ContractTerms] = None
    claims: list[Claim] = Field(default_factory=list)
    created: date = Field(default_factory=date.today)
    updated: date = Field(default_factory=date.today)
    notes: Optional[str] = None
