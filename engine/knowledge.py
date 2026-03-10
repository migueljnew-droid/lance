"""Legal knowledge base query engine."""

from __future__ import annotations

from pathlib import Path

import yaml


class KnowledgeBase:
    """Queryable legal knowledge base backed by YAML files."""

    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = Path(knowledge_dir)
        self._cache: dict[str, dict] = {}

    def _load_category(self, category: str) -> list[dict]:
        """Load all YAML files in a category directory."""
        if category in self._cache:
            return self._cache[category]

        cat_dir = self.knowledge_dir / category
        if not cat_dir.exists():
            return []

        entries = []
        for yaml_file in sorted(cat_dir.glob("*.yaml")):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            if data:
                if isinstance(data, list):
                    entries.extend(data)
                else:
                    entries.append(data)
        self._cache[category] = entries
        return entries

    def query_statute(self, keyword: str, jurisdiction: str = None) -> list[dict]:
        """Search statutes by keyword and optional jurisdiction."""
        results = []
        statutes = self._load_category("statutes")
        keyword_lower = keyword.lower()
        for entry in statutes:
            if jurisdiction and entry.get("jurisdiction", "").upper() != jurisdiction.upper():
                continue
            if self._matches(entry, keyword_lower):
                results.append(entry)
        return results

    def query_precedent(self, keyword: str) -> list[dict]:
        """Search case law by keyword."""
        results = []
        precedents = self._load_category("precedent")
        keyword_lower = keyword.lower()
        for entry in precedents:
            if self._matches(entry, keyword_lower):
                results.append(entry)
        return results

    def query_regulation(self, keyword: str) -> list[dict]:
        """Search regulations by keyword."""
        results = []
        regulations = self._load_category("regulations")
        keyword_lower = keyword.lower()
        for entry in regulations:
            if self._matches(entry, keyword_lower):
                results.append(entry)
        return results

    def get_sol(self, claim_type: str, jurisdiction: str = "CA") -> dict | None:
        """Get statute of limitations for a claim type and jurisdiction."""
        statutes = self._load_category("statutes")
        for entry in statutes:
            if entry.get("jurisdiction", "").upper() != jurisdiction.upper():
                continue
            sol_table = entry.get("sol_table", [])
            for sol_entry in sol_table:
                if claim_type.lower() in sol_entry.get("claim_type", "").lower():
                    return sol_entry
        return None

    def get_template(self, template_name: str) -> dict | None:
        """Get a document template by name."""
        templates = self._load_category("templates")
        for tmpl in templates:
            if template_name.lower() in tmpl.get("name", "").lower():
                return tmpl
        return None

    def search(self, query: str, categories: list[str] = None) -> list[dict]:
        """Full-text search across all or specified categories."""
        cats = categories or ["statutes", "regulations", "precedent", "templates"]
        results = []
        query_lower = query.lower()
        for cat in cats:
            entries = self._load_category(cat)
            for entry in entries:
                if self._matches(entry, query_lower):
                    results.append({"category": cat, **entry})
        return results

    def list_categories(self) -> list[str]:
        """List available knowledge base categories."""
        if not self.knowledge_dir.exists():
            return []
        return [d.name for d in self.knowledge_dir.iterdir() if d.is_dir()]

    def stats(self) -> dict:
        """Get knowledge base statistics."""
        stats = {}
        for cat in self.list_categories():
            entries = self._load_category(cat)
            stats[cat] = len(entries)
        return stats

    @staticmethod
    def _matches(entry: dict, keyword: str) -> bool:
        """Check if any value in the entry contains the keyword."""
        for value in entry.values():
            if isinstance(value, str) and keyword in value.lower():
                return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and keyword in item.lower():
                        return True
                    elif isinstance(item, dict):
                        for v in item.values():
                            if isinstance(v, str) and keyword in v.lower():
                                return True
        return False
