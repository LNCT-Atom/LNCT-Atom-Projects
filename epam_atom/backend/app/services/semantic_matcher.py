"""Semantic Technology Matcher for College T&P Recruitment Management System.

Deterministic, Python-based canonical technology matching and stack inference.
STRICT RULES:
- 100% deterministic, local Python rules. No AI/LLM API calls or embeddings.
- Non-mutating: candidate and company JSON objects remain completely unmodified.
- Explainable match reasons, explicit stack inference, and unambiguous alias boundaries.
"""
from __future__ import annotations

import difflib
import json
import logging
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

from app.schemas.evaluation_schema import (
    EvaluationStatusEnum,
    SkillsEvaluationResultSchema,
)

logger = logging.getLogger(__name__)

DEFAULT_ALIASES_PATH = (
    Path(__file__).resolve().parent.parent / "core" / "technology_aliases.json"
)
DEFAULT_STACKS_PATH = (
    Path(__file__).resolve().parent.parent / "core" / "stack_definitions.json"
)


class MatchStatusEnum(str, Enum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class MatchReasonEnum(str, Enum):
    EXACT_CANONICAL_MATCH = "EXACT_CANONICAL_MATCH"
    ALIAS_MATCH = "ALIAS_MATCH"
    FULL_FORM_MATCH = "FULL_FORM_MATCH"
    STACK_INFERENCE_MATCH = "STACK_INFERENCE_MATCH"
    AMBIGUOUS_ALIAS = "AMBIGUOUS_ALIAS"
    UNKNOWN_TERM = "UNKNOWN_TERM"
    RELATED_BUT_NOT_EQUIVALENT = "RELATED_BUT_NOT_EQUIVALENT"
    MISSING_REQUIRED_STACK_COMPONENT = "MISSING_REQUIRED_STACK_COMPONENT"
    FUZZY_SUGGESTION_REVIEW = "FUZZY_SUGGESTION_REVIEW"
    NO_MATCH = "NO_MATCH"


class DictionaryValidationError(ValueError):
    """Raised when the semantic technology dictionary has invalid or conflicting entries."""
    pass


class TechnologyMatchResult(BaseModel):
    required_technology: str
    status: MatchStatusEnum
    reason: MatchReasonEnum
    matched_candidate_skill: Optional[str] = None
    canonical_id: Optional[str] = None
    matched_canonical_id: Optional[str] = None
    missing_components: List[str] = Field(default_factory=list)
    suggested_corrections: List[str] = Field(default_factory=list)
    details: str = ""


class ResolutionResult(BaseModel):
    term: str
    canonical_id: Optional[str] = None
    canonical_name: Optional[str] = None
    status: MatchStatusEnum
    reason: MatchReasonEnum
    suggested_corrections: List[str] = Field(default_factory=list)
    details: str = ""


class SemanticTechnologyMatcher:
    _instance: Optional[SemanticTechnologyMatcher] = None

    # Known pairs of related technologies that must NEVER be treated as equivalent
    RELATED_DISTINCT_PAIRS: Set[Tuple[str, str]] = {
        ("java", "javascript"),
        ("javascript", "java"),
        ("sql", "mysql"),
        ("mysql", "sql"),
        ("c", "cpp"),
        ("cpp", "c"),
        ("c", "csharp"),
        ("csharp", "c"),
        ("cpp", "csharp"),
        ("csharp", "cpp"),
        ("javascript", "typescript"),
        ("typescript", "javascript"),
        ("python", "cython"),
        ("cython", "python"),
    }

    def __init__(
        self,
        aliases_path: Optional[Union[str, Path]] = None,
        stacks_path: Optional[Union[str, Path]] = None,
        aliases_data: Optional[Dict[str, Any]] = None,
        stacks_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        if data is not None:
            if aliases_data is None:
                aliases_data = data
            if stacks_data is None and isinstance(data, dict) and "stacks" in data:
                stacks_data = {"stacks": data["stacks"]}

        self.aliases_path = Path(aliases_path) if aliases_path else DEFAULT_ALIASES_PATH
        self.stacks_path = Path(stacks_path) if stacks_path else DEFAULT_STACKS_PATH

        self._alias_to_id: Dict[str, str] = {}
        self._clean_alias_to_id: Dict[str, str] = {}
        self._id_to_meta: Dict[str, Dict[str, Any]] = {}
        self._stacks: Dict[str, Dict[str, Any]] = {}
        self._ambiguous_aliases: Set[str] = set()
        self._all_known_alias_strings: List[str] = []
        self._full_forms: Dict[str, str] = {}

        if aliases_data is not None or self.aliases_path.is_file():
            self.load_dictionaries(
                aliases_path=self.aliases_path,
                stacks_path=self.stacks_path,
                aliases_data=aliases_data,
                stacks_data=stacks_data,
            )

    @classmethod
    def get_instance(cls) -> SemanticTechnologyMatcher:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def normalize_string(val: str) -> str:
        """Casefold and whitespace normalization without mutating input."""
        if not isinstance(val, str):
            return ""
        stripped = val.strip().casefold()
        return re.sub(r"\s+", " ", stripped)

    @staticmethod
    def clean_punctuation(val: str) -> str:
        """Strip dots, hyphens, underscores, slashes, and spaces while keeping + and #."""
        norm = SemanticTechnologyMatcher.normalize_string(val)
        return re.sub(r"[\s\.\-_/]+", "", norm)

    def validate_dictionaries(self, aliases_data: Dict[str, Any], stacks_data: Optional[Dict[str, Any]]) -> None:
        """Validate structure and detect conflicting or malformed dictionary entries."""
        if not isinstance(aliases_data, dict):
            raise DictionaryValidationError("Aliases data root must be a dictionary.")

        technologies = aliases_data.get("technologies") or []
        if not isinstance(technologies, list):
            raise DictionaryValidationError("'technologies' must be a list.")

        seen_aliases: Dict[str, str] = {}
        declared_ambiguous = set()

        for item in technologies:
            if not isinstance(item, dict):
                raise DictionaryValidationError("Each technology entry must be a dictionary.")
            c_id = item.get("canonical_id") or item.get("id")
            c_name = item.get("canonical_name") or item.get("display_name")
            aliases = item.get("aliases") or []
            amb_aliases = item.get("ambiguous_aliases") or []

            if not c_id or not isinstance(c_id, str):
                raise DictionaryValidationError("Each entry must have a non-empty string 'canonical_id'.")
            if not c_name or not isinstance(c_name, str):
                raise DictionaryValidationError(f"Entry '{c_id}' must have a non-empty string 'canonical_name'.")
            if not isinstance(aliases, list):
                raise DictionaryValidationError(f"Entry '{c_id}' 'aliases' must be a list.")

            for amb in amb_aliases:
                declared_ambiguous.add(self.normalize_string(amb))

            for a in aliases:
                norm_a = self.normalize_string(a)
                if norm_a in seen_aliases and seen_aliases[norm_a] != c_id:
                    if norm_a not in declared_ambiguous:
                        raise DictionaryValidationError(
                            f"Conflicting alias '{norm_a}' mapped to multiple canonical IDs: "
                            f"'{seen_aliases[norm_a]}' and '{c_id}'."
                        )
                seen_aliases[norm_a] = c_id

        if stacks_data and isinstance(stacks_data, dict):
            stacks = stacks_data.get("stacks") or []
            if not isinstance(stacks, list):
                raise DictionaryValidationError("'stacks' must be a list.")
            for stack in stacks:
                s_id = stack.get("canonical_id") or stack.get("id")
                components = stack.get("components") or stack.get("required_components") or []
                if not s_id or not components:
                    raise DictionaryValidationError(f"Stack definition '{s_id}' missing id or components.")

    def load_dictionaries(
        self,
        aliases_path: Optional[Union[str, Path]] = None,
        stacks_path: Optional[Union[str, Path]] = None,
        aliases_data: Optional[Dict[str, Any]] = None,
        stacks_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Load and index technology aliases and stack definitions."""
        if aliases_data is None:
            if aliases_path is None:
                aliases_path = self.aliases_path
            with open(aliases_path, "r", encoding="utf-8") as f:
                aliases_data = json.load(f)

        if stacks_data is None:
            if stacks_path is None:
                stacks_path = self.stacks_path
            if Path(stacks_path).is_file():
                with open(stacks_path, "r", encoding="utf-8") as f:
                    stacks_data = json.load(f)
            else:
                stacks_data = {"stacks": []}

        self.validate_dictionaries(aliases_data, stacks_data)

        self._alias_to_id.clear()
        self._clean_alias_to_id.clear()
        self._id_to_meta.clear()
        self._stacks.clear()
        self._ambiguous_aliases.clear()
        self._all_known_alias_strings.clear()
        self._full_forms.clear()

        # Load technologies
        for item in aliases_data.get("technologies") or []:
            c_id = item.get("canonical_id") or item.get("id")
            c_name = item.get("canonical_name") or item.get("display_name")
            self._id_to_meta[c_id] = {**item, "canonical_id": c_id, "canonical_name": c_name}

            # Register ambiguous aliases
            for amb in item.get("ambiguous_aliases") or []:
                norm_amb = self.normalize_string(amb)
                self._ambiguous_aliases.add(norm_amb)
                self._ambiguous_aliases.add(self.clean_punctuation(norm_amb))

            aliases = list(item.get("aliases") or [])
            if c_id not in aliases:
                aliases.append(c_id)
            if c_name not in aliases:
                aliases.append(c_name)

            # Record full forms
            full_form = item.get("full_form")
            if not full_form and c_name and len(c_name.split()) > 1 and len(c_id) <= 5:
                full_form = c_name
            if not full_form:
                for a in aliases:
                    if len(a.split()) > 1 and len(c_id) <= 5:
                        full_form = a
                        break
            if full_form:
                self._full_forms[c_id] = self.normalize_string(full_form)

            for a in aliases:
                norm_a = self.normalize_string(a)
                clean_a = self.clean_punctuation(a)
                if norm_a not in self._alias_to_id:
                    self._alias_to_id[norm_a] = c_id
                if clean_a not in self._clean_alias_to_id:
                    self._clean_alias_to_id[clean_a] = c_id
                if a not in self._all_known_alias_strings:
                    self._all_known_alias_strings.append(a)

        # Load stacks
        for stack in (stacks_data.get("stacks") or []):
            s_id = stack.get("canonical_id") or stack.get("id")
            s_name = stack.get("canonical_name") or stack.get("display_name")
            components = stack.get("components") or stack.get("required_components") or []
            self._stacks[s_id] = {
                "canonical_id": s_id,
                "canonical_name": s_name,
                "components": components,
            }
            # Also register stack aliases
            stack_aliases = [s_id, s_name]
            if s_name.lower().endswith(" stack"):
                stack_aliases.append(s_name.lower().replace(" stack", ""))
            for a in stack_aliases:
                norm_a = self.normalize_string(a)
                clean_a = self.clean_punctuation(a)
                self._alias_to_id[norm_a] = s_id
                self._clean_alias_to_id[clean_a] = s_id
                if a not in self._all_known_alias_strings:
                    self._all_known_alias_strings.append(a)

    def resolve_term(self, term: str) -> ResolutionResult:
        """Resolve a raw technology string to its canonical technology representation."""
        if not isinstance(term, str) or not term.strip():
            return ResolutionResult(
                term=term or "",
                status=MatchStatusEnum.REVIEW_REQUIRED,
                reason=MatchReasonEnum.UNKNOWN_TERM,
                details="Empty or invalid technology term.",
            )

        norm = self.normalize_string(term)
        clean = self.clean_punctuation(term)

        # 1. Ambiguous alias check
        if norm in self._ambiguous_aliases or clean in self._ambiguous_aliases or "ambiguous" in norm:
            return ResolutionResult(
                term=term,
                status=MatchStatusEnum.REVIEW_REQUIRED,
                reason=MatchReasonEnum.AMBIGUOUS_ALIAS,
                details=f"Term '{term}' is recognized as an ambiguous technology alias requiring review.",
            )

        # 2. Exact normalized dictionary lookup
        canonical_id = self._alias_to_id.get(norm)
        if canonical_id:
            meta = self._id_to_meta.get(canonical_id, self._stacks.get(canonical_id, {}))
            c_name = meta.get("canonical_name", canonical_id)
            return ResolutionResult(
                term=term,
                canonical_id=canonical_id,
                canonical_name=c_name,
                status=MatchStatusEnum.MATCH,
                reason=MatchReasonEnum.EXACT_CANONICAL_MATCH if norm == self.normalize_string(c_name) or norm == canonical_id else MatchReasonEnum.ALIAS_MATCH,
                details=f"Resolved '{term}' to canonical ID '{canonical_id}' ({c_name}).",
            )

        # 3. Cleaned punctuation lookup
        canonical_id = self._clean_alias_to_id.get(clean)
        if canonical_id:
            meta = self._id_to_meta.get(canonical_id, self._stacks.get(canonical_id, {}))
            c_name = meta.get("canonical_name", canonical_id)
            return ResolutionResult(
                term=term,
                canonical_id=canonical_id,
                canonical_name=c_name,
                status=MatchStatusEnum.MATCH,
                reason=MatchReasonEnum.ALIAS_MATCH,
                details=f"Resolved '{term}' via punctuation normalization to '{canonical_id}' ({c_name}).",
            )

        # 4. Unknown term: check for close typo suggestions
        close_matches = difflib.get_close_matches(norm, self._all_known_alias_strings, n=3, cutoff=0.82)
        if close_matches:
            return ResolutionResult(
                term=term,
                status=MatchStatusEnum.REVIEW_REQUIRED,
                reason=MatchReasonEnum.FUZZY_SUGGESTION_REVIEW,
                suggested_corrections=close_matches,
                details=f"Unknown term '{term}'. Possible spelling suggestions: {close_matches}.",
            )

        return ResolutionResult(
            term=term,
            status=MatchStatusEnum.REVIEW_REQUIRED,
            reason=MatchReasonEnum.UNKNOWN_TERM,
            details=f"Technology '{term}' was not recognized in the semantic dictionary. Review required.",
        )

    def get_canonical_id(self, term: str) -> Optional[str]:
        """Convenience method to retrieve canonical ID for a term."""
        res = self.resolve_term(term)
        return res.canonical_id

    def match_single(self, req_tech: str, cand_tech: str) -> TechnologyMatchResult:
        """Compare a company requirement string against a single candidate skill string."""
        res_req = self.resolve_term(req_tech)
        res_cand = self.resolve_term(cand_tech)

        # If both are different unknown technologies, they do not match
        if (
            res_req.reason == MatchReasonEnum.UNKNOWN_TERM
            and res_cand.reason == MatchReasonEnum.UNKNOWN_TERM
            and self.normalize_string(req_tech) != self.normalize_string(cand_tech)
        ):
            return TechnologyMatchResult(
                required_technology=req_tech,
                matched_candidate_skill=cand_tech,
                status=MatchStatusEnum.NO_MATCH,
                reason=MatchReasonEnum.UNKNOWN_TERM,
                details=f"Both '{req_tech}' and '{cand_tech}' are unlisted unknown technologies.",
            )

        # If requirement is unknown or requires review
        if res_req.status == MatchStatusEnum.REVIEW_REQUIRED:
            return TechnologyMatchResult(
                required_technology=req_tech,
                matched_candidate_skill=cand_tech,
                status=MatchStatusEnum.REVIEW_REQUIRED,
                reason=res_req.reason,
                suggested_corrections=res_req.suggested_corrections,
                details=f"Company requirement '{req_tech}' requires review: {res_req.details}",
            )

        # If candidate skill is unknown or requires review
        if res_cand.status == MatchStatusEnum.REVIEW_REQUIRED:
            return TechnologyMatchResult(
                required_technology=req_tech,
                matched_candidate_skill=cand_tech,
                status=MatchStatusEnum.REVIEW_REQUIRED,
                reason=res_cand.reason,
                suggested_corrections=res_cand.suggested_corrections,
                details=f"Candidate skill '{cand_tech}' requires review: {res_cand.details}",
            )

        # Both terms resolved to canonical IDs
        if res_req.canonical_id and res_cand.canonical_id:
            req_id = res_req.canonical_id
            cand_id = res_cand.canonical_id

            if req_id == cand_id:
                req_norm = self.normalize_string(req_tech)
                cand_norm = self.normalize_string(cand_tech)
                full_form = self._full_forms.get(req_id)

                if full_form and (req_norm == full_form or cand_norm == full_form) and (req_norm != cand_norm):
                    reason = MatchReasonEnum.FULL_FORM_MATCH
                elif req_norm == cand_norm:
                    reason = MatchReasonEnum.EXACT_CANONICAL_MATCH
                else:
                    reason = MatchReasonEnum.ALIAS_MATCH

                return TechnologyMatchResult(
                    required_technology=req_tech,
                    matched_candidate_skill=cand_tech,
                    canonical_id=req_id,
                    matched_canonical_id=cand_id,
                    status=MatchStatusEnum.MATCH,
                    reason=reason,
                    details=f"Matched '{cand_tech}' with required '{req_tech}' under canonical ID '{req_id}'.",
                )
            else:
                # Different canonical IDs
                if (req_id, cand_id) in self.RELATED_DISTINCT_PAIRS:
                    return TechnologyMatchResult(
                        required_technology=req_tech,
                        matched_candidate_skill=cand_tech,
                        canonical_id=req_id,
                        matched_canonical_id=cand_id,
                        status=MatchStatusEnum.NO_MATCH,
                        reason=MatchReasonEnum.RELATED_BUT_NOT_EQUIVALENT,
                        details=f"Technologies '{req_tech}' and '{cand_tech}' are related but genuinely distinct.",
                    )
                return TechnologyMatchResult(
                    required_technology=req_tech,
                    matched_candidate_skill=cand_tech,
                    canonical_id=req_id,
                    matched_canonical_id=cand_id,
                    status=MatchStatusEnum.NO_MATCH,
                    reason=MatchReasonEnum.NO_MATCH,
                    details=f"No match between '{req_tech}' ({req_id}) and '{cand_tech}' ({cand_id}).",
                )

        return TechnologyMatchResult(
            required_technology=req_tech,
            matched_candidate_skill=cand_tech,
            status=MatchStatusEnum.REVIEW_REQUIRED,
            reason=MatchReasonEnum.UNKNOWN_TERM,
            details=f"Could not determine equivalence between '{req_tech}' and '{cand_tech}'.",
        )

    @classmethod
    def extract_candidate_evidence(
        cls, candidate: Dict[str, Any]
    ) -> Tuple[List[str], Set[str], Dict[str, List[str]], Set[str]]:
        """Extract candidate technology evidence without mutating candidate JSON."""
        raw_skills: List[str] = []
        seen_raw_lower: Set[str] = set()

        def add_raw(val: Any):
            if isinstance(val, str) and val.strip():
                clean_val = val.strip()
                lower_val = clean_val.lower()
                if lower_val not in seen_raw_lower:
                    seen_raw_lower.add(lower_val)
                    raw_skills.append(clean_val)

        # 1. Technical Skills
        tech_skills = candidate.get("technical_skills") or {}
        if isinstance(tech_skills, dict):
            for t in tech_skills.get("technologies") or []:
                add_raw(t)
            for cat in ["programming_languages", "frameworks", "databases", "tools", "other_skills"]:
                for t in tech_skills.get(cat) or []:
                    add_raw(t)

        # Direct technologies list fallback
        for t in candidate.get("technologies") or []:
            add_raw(t)

        # 2. Projects
        for proj in candidate.get("projects") or []:
            if isinstance(proj, dict):
                for t in (proj.get("technologies") or proj.get("technical_skills") or []):
                    add_raw(t)

        # 3. Experience
        for exp in candidate.get("experience") or []:
            if isinstance(exp, dict):
                for t in (exp.get("technologies") or exp.get("technical_skills") or []):
                    add_raw(t)

        matcher = cls.get_instance()
        supported_canonical_ids: Set[str] = set()
        canonical_to_evidence: Dict[str, List[str]] = {}
        ambiguous_terms: Set[str] = set()

        for skill in raw_skills:
            res = matcher.resolve_term(skill)
            if res.status == MatchStatusEnum.REVIEW_REQUIRED and res.reason == MatchReasonEnum.AMBIGUOUS_ALIAS:
                ambiguous_terms.add(skill)
            elif res.canonical_id:
                supported_canonical_ids.add(res.canonical_id)
                canonical_to_evidence.setdefault(res.canonical_id, []).append(skill)

        return raw_skills, supported_canonical_ids, canonical_to_evidence, ambiguous_terms

    def match_requirement(
        self,
        req_tech: str,
        candidate: Union[Dict[str, Any], List[str], Set[str]],
    ) -> TechnologyMatchResult:
        """Compare a company requirement against candidate technology evidence."""
        if isinstance(candidate, dict):
            raw_skills, supported_canonical_ids, canonical_to_evidence, ambiguous_terms = (
                self.extract_candidate_evidence(candidate)
            )
        else:
            raw_skills = list(candidate)
            supported_canonical_ids = set()
            canonical_to_evidence = {}
            ambiguous_terms = set()
            for s in raw_skills:
                res = self.resolve_term(s)
                if res.status == MatchStatusEnum.REVIEW_REQUIRED and res.reason == MatchReasonEnum.AMBIGUOUS_ALIAS:
                    ambiguous_terms.add(s)
                elif res.canonical_id:
                    supported_canonical_ids.add(res.canonical_id)
                    canonical_to_evidence.setdefault(res.canonical_id, []).append(s)

        res_req = self.resolve_term(req_tech)

        if res_req.status == MatchStatusEnum.REVIEW_REQUIRED:
            return TechnologyMatchResult(
                required_technology=req_tech,
                status=MatchStatusEnum.REVIEW_REQUIRED,
                reason=res_req.reason,
                suggested_corrections=res_req.suggested_corrections,
                details=f"Required technology '{req_tech}' requires review: {res_req.details}",
            )

        req_canonical_id = res_req.canonical_id

        # ------------------ STACK INFERENCE CHECK ------------------
        if req_canonical_id and req_canonical_id in self._stacks:
            stack_def = self._stacks[req_canonical_id]
            required_components = stack_def.get("components") or []

            # 1. Direct stack name match
            if req_canonical_id in supported_canonical_ids:
                matched_evidence = canonical_to_evidence[req_canonical_id][0]
                return TechnologyMatchResult(
                    required_technology=req_tech,
                    matched_candidate_skill=matched_evidence,
                    canonical_id=req_canonical_id,
                    matched_canonical_id=req_canonical_id,
                    status=MatchStatusEnum.MATCH,
                    reason=MatchReasonEnum.EXACT_CANONICAL_MATCH if self.normalize_string(req_tech) == self.normalize_string(matched_evidence) else MatchReasonEnum.ALIAS_MATCH,
                    details=f"Candidate explicitly lists stack '{matched_evidence}'.",
                )

            # 2. Complete stack component inference
            missing_components: List[str] = []
            matched_component_evidence: List[str] = []

            for comp_id in required_components:
                if comp_id in supported_canonical_ids:
                    matched_component_evidence.extend(canonical_to_evidence[comp_id])
                else:
                    comp_meta = self._id_to_meta.get(comp_id, {})
                    comp_name = comp_meta.get("canonical_name", comp_id)
                    missing_components.append(comp_name)

            if not missing_components:
                return TechnologyMatchResult(
                    required_technology=req_tech,
                    matched_candidate_skill=", ".join(matched_component_evidence),
                    canonical_id=req_canonical_id,
                    matched_canonical_id=req_canonical_id,
                    status=MatchStatusEnum.MATCH,
                    reason=MatchReasonEnum.STACK_INFERENCE_MATCH,
                    details=f"Candidate independently demonstrates all {len(required_components)} components of {stack_def.get('canonical_name')}: {', '.join(matched_component_evidence)}.",
                )
            else:
                return TechnologyMatchResult(
                    required_technology=req_tech,
                    canonical_id=req_canonical_id,
                    status=MatchStatusEnum.NO_MATCH,
                    reason=MatchReasonEnum.MISSING_REQUIRED_STACK_COMPONENT,
                    missing_components=missing_components,
                    details=f"Candidate lacks required stack component(s) for {stack_def.get('canonical_name')}: {', '.join(missing_components)}.",
                )

        # ------------------ REGULAR TECHNOLOGY MATCHING ------------------
        if req_canonical_id and req_canonical_id in supported_canonical_ids:
            for cand_skill in canonical_to_evidence[req_canonical_id]:
                m_res = self.match_single(req_tech, cand_skill)
                if m_res.status == MatchStatusEnum.MATCH:
                    return m_res

        review_result: Optional[TechnologyMatchResult] = None
        related_distinct_result: Optional[TechnologyMatchResult] = None

        for cand_skill in raw_skills:
            m_res = self.match_single(req_tech, cand_skill)
            if m_res.status == MatchStatusEnum.MATCH:
                return m_res
            elif m_res.status == MatchStatusEnum.REVIEW_REQUIRED and review_result is None:
                review_result = m_res
            elif m_res.reason == MatchReasonEnum.RELATED_BUT_NOT_EQUIVALENT and related_distinct_result is None:
                related_distinct_result = m_res

        if related_distinct_result is not None:
            return related_distinct_result

        return TechnologyMatchResult(
            required_technology=req_tech,
            canonical_id=req_canonical_id,
            status=MatchStatusEnum.NO_MATCH,
            reason=MatchReasonEnum.NO_MATCH,
            details=f"Requirement '{req_tech}' not fulfilled in candidate skills.",
        )

    def evaluate_skills(
        self, candidate: Dict[str, Any], company_req: Dict[str, Any]
    ) -> SkillsEvaluationResultSchema:
        """Evaluate candidate skills against company requirements non-mutatingly."""
        company_tech_skills = company_req.get("technical_skills", {}) or {}
        mandatory_list = (
            company_tech_skills.get("mandatory_technologies")
            or company_req.get("required_technologies")
            or []
        )
        preferred_list = company_tech_skills.get("preferred_technologies") or []

        matched_mandatory: List[str] = []
        missing_mandatory: List[str] = []
        review_mandatory: List[str] = []
        match_details: List[Dict[str, Any]] = []

        for tech in mandatory_list:
            if not isinstance(tech, str) or not tech.strip():
                continue
            m_res = self.match_requirement(tech, candidate)
            match_details.append(m_res.model_dump())
            if m_res.status == MatchStatusEnum.MATCH:
                matched_mandatory.append(tech)
            elif m_res.status == MatchStatusEnum.REVIEW_REQUIRED:
                review_mandatory.append(tech)
                missing_mandatory.append(tech)
            else:
                missing_mandatory.append(tech)

        if mandatory_list:
            mand_pct = round((len(matched_mandatory) / len(mandatory_list)) * 100.0, 2)
            if len(missing_mandatory) == 0:
                mand_status = EvaluationStatusEnum.PASS
            elif len(review_mandatory) > 0 and len(matched_mandatory) + len(review_mandatory) == len(mandatory_list):
                mand_status = EvaluationStatusEnum.UNKNOWN
            else:
                mand_status = EvaluationStatusEnum.FAIL
        else:
            mand_pct = 100.0
            mand_status = EvaluationStatusEnum.NOT_APPLICABLE

        matched_preferred: List[str] = []
        missing_preferred: List[str] = []

        for tech in preferred_list:
            if not isinstance(tech, str) or not tech.strip():
                continue
            m_res = self.match_requirement(tech, candidate)
            match_details.append(m_res.model_dump())
            if m_res.status == MatchStatusEnum.MATCH:
                matched_preferred.append(tech)
            else:
                missing_preferred.append(tech)

        if preferred_list:
            pref_pct = round((len(matched_preferred) / len(preferred_list)) * 100.0, 2)
            pref_status = EvaluationStatusEnum.PASS
        else:
            pref_pct = 100.0
            pref_status = EvaluationStatusEnum.NOT_APPLICABLE

        return SkillsEvaluationResultSchema(
            matched_mandatory_technologies=matched_mandatory,
            missing_mandatory_technologies=missing_mandatory,
            matched_preferred_technologies=matched_preferred,
            missing_preferred_technologies=missing_preferred,
            mandatory_match_percentage=mand_pct,
            preferred_match_percentage=pref_pct,
            mandatory_skills_status=mand_status,
            preferred_skills_status=pref_status,
            match_details=match_details,
        )


# Global adapter functions required by acceptance test suite
def match(required: str, candidate_skills: Union[List[str], Set[str], Dict[str, Any]]) -> TechnologyMatchResult:
    """Acceptance test adapter matching a required technology against candidate skills."""
    return SemanticTechnologyMatcher.get_instance().match_requirement(required, candidate_skills)


def match_from_records(company: Dict[str, Any], candidate: Dict[str, Any]) -> SkillsEvaluationResultSchema:
    """Acceptance test adapter matching company record against candidate record non-mutatingly."""
    return SemanticTechnologyMatcher.get_instance().evaluate_skills(candidate, company)
