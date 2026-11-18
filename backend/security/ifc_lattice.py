"""Formal Information Flow Control (IFC) Lattice Model for AEGIS.

Grounds AEGIS in the mathematical foundations of security lattices (Denning 1976)
and Biba Integrity (Biba 1977) adapted for autonomous LLM agents.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Sequence

from backend.schemas.provenance import (
    Provenance,
    SensitivityLevel,
    SourceType,
    TrustLevel,
)


class SensitivityRank(IntEnum):
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2

    @classmethod
    def from_enum(cls, level: SensitivityLevel) -> SensitivityRank:
        mapping = {
            SensitivityLevel.PUBLIC: cls.PUBLIC,
            SensitivityLevel.INTERNAL: cls.INTERNAL,
            SensitivityLevel.CONFIDENTIAL: cls.CONFIDENTIAL,
        }
        return mapping[level]


class TrustRank(IntEnum):
    UNTRUSTED = 0
    REVIEWED = 1
    TRUSTED = 2

    @classmethod
    def from_enum(cls, level: TrustLevel) -> TrustRank:
        mapping = {
            TrustLevel.UNTRUSTED: cls.UNTRUSTED,
            TrustLevel.REVIEWED: cls.REVIEWED,
            TrustLevel.TRUSTED: cls.TRUSTED,
        }
        return mapping[level]


class IFCLattice:
    """Security Lattice enforcing Bell-LaPadula Confidentiality and Biba Integrity."""

    @staticmethod
    def join_sensitivity(a: SensitivityLevel, b: SensitivityLevel) -> SensitivityLevel:
        """Least Upper Bound (LUB) of sensitivity: max(rank(a), rank(b))."""
        rank_a = SensitivityRank.from_enum(a)
        rank_b = SensitivityRank.from_enum(b)
        max_rank = max(rank_a, rank_b)
        for level in SensitivityLevel:
            if SensitivityRank.from_enum(level) == max_rank:
                return level
        return SensitivityLevel.CONFIDENTIAL

    @staticmethod
    def meet_trust(a: TrustLevel, b: TrustLevel) -> TrustLevel:
        """Greatest Lower Bound (GLB) of integrity: min(rank(a), rank(b)).

        A chain is only as trusted as its least trusted link.
        """
        rank_a = TrustRank.from_enum(a)
        rank_b = TrustRank.from_enum(b)
        min_rank = min(rank_a, rank_b)
        for level in TrustLevel:
            if TrustRank.from_enum(level) == min_rank:
                return level
        return TrustLevel.UNTRUSTED

    @classmethod
    def propagate_provenance(
        cls,
        parents: Sequence[Provenance],
        derived_source_id: str,
        origin: str,
    ) -> Provenance:
        """Propagate taint and sensitivity through the lattice to derived outputs."""
        if not parents:
            return Provenance(
                source_id=derived_source_id,
                source_type=SourceType.AGENT_GENERATED,
                origin=origin,
                trust_level=TrustLevel.TRUSTED,
                sensitivity=SensitivityLevel.PUBLIC,
                contains_untrusted_instructions=False,
            )

        eff_sens = parents[0].sensitivity
        eff_trust = parents[0].trust_level
        has_untrusted_instr = parents[0].contains_untrusted_instructions

        for p in parents[1:]:
            eff_sens = cls.join_sensitivity(eff_sens, p.sensitivity)
            eff_trust = cls.meet_trust(eff_trust, p.trust_level)
            if p.contains_untrusted_instructions:
                has_untrusted_instr = True

        return Provenance(
            source_id=derived_source_id,
            source_type=SourceType.AGENT_GENERATED,
            origin=origin,
            trust_level=eff_trust,
            sensitivity=eff_sens,
            parent_source_ids=tuple(p.source_id for p in parents),
            contains_untrusted_instructions=has_untrusted_instr,
        )

    @classmethod
    def is_flow_permitted(
        cls,
        source_records: Sequence[Provenance] | None,
        destination_clearance: SensitivityLevel,
        requires_trusted_source: bool = True,
    ) -> tuple[bool, str]:
        """Check if information from source_records is mathematically permitted to flow.

        Rule 1: Sensitivity of every input must be <= destination clearance.
        Rule 2: If destination requires integrity (e.g. external broadcast), source must not be UNTRUSTED.
        """
        if not source_records:
            return True, "No source taint detected"

        dest_rank = SensitivityRank.from_enum(destination_clearance)

        for record in source_records:
            record_rank = SensitivityRank.from_enum(record.sensitivity)
            if record_rank > dest_rank:
                return (
                    False,
                    f"Flow violation: Source sensitivity ({record.sensitivity.value}) "
                    f"exceeds sink clearance ({destination_clearance.value})",
                )

            if requires_trusted_source and record.trust_level == TrustLevel.UNTRUSTED:
                return False, "Flow violation: Untrusted source cannot flow into sensitive sink"

            if record.contains_untrusted_instructions:
                return (
                    False,
                    "Flow violation: Source contains untrusted instructions (tainted lineage)",
                )

        return True, "Information flow permitted by lattice"
