from backend.schemas.provenance import (
    Provenance,
    SensitivityLevel,
    SourceType,
    TrustLevel,
)
from backend.security.ifc_lattice import IFCLattice


def test_lattice_join_and_meet():
    # Join sensitivity: CONFIDENTIAL dominates PUBLIC
    joined = IFCLattice.join_sensitivity(
        SensitivityLevel.PUBLIC, SensitivityLevel.CONFIDENTIAL
    )
    assert joined == SensitivityLevel.CONFIDENTIAL

    # Meet trust: UNTRUSTED dominates TRUSTED (lowest integrity wins)
    met = IFCLattice.meet_trust(TrustLevel.TRUSTED, TrustLevel.UNTRUSTED)
    assert met == TrustLevel.UNTRUSTED


def test_lattice_propagation():
    parent1 = Provenance(
        source_id="src-001",
        source_type=SourceType.DOCUMENT,
        origin="doc1.txt",
        trust_level=TrustLevel.TRUSTED,
        sensitivity=SensitivityLevel.PUBLIC,
        contains_untrusted_instructions=False,
    )
    parent2 = Provenance(
        source_id="src-002",
        source_type=SourceType.DOCUMENT,
        origin="doc2.txt",
        trust_level=TrustLevel.UNTRUSTED,
        sensitivity=SensitivityLevel.CONFIDENTIAL,
        contains_untrusted_instructions=True,
    )

    child = IFCLattice.propagate_provenance(
        [parent1, parent2], "child-001", "AEGIS agent"
    )
    assert child.sensitivity == SensitivityLevel.CONFIDENTIAL
    assert child.trust_level == TrustLevel.UNTRUSTED
    assert child.contains_untrusted_instructions is True
    assert child.parent_source_ids == ("src-001", "src-002")


def test_flow_permitted_check():
    safe_rec = Provenance(
        source_id="src-safe",
        source_type=SourceType.DOCUMENT,
        origin="safe.txt",
        trust_level=TrustLevel.TRUSTED,
        sensitivity=SensitivityLevel.PUBLIC,
        contains_untrusted_instructions=False,
    )
    allowed, reason = IFCLattice.is_flow_permitted(
        [safe_rec], SensitivityLevel.PUBLIC
    )
    assert allowed is True

    unsafe_rec = Provenance(
        source_id="src-unsafe",
        source_type=SourceType.DOCUMENT,
        origin="unsafe.txt",
        trust_level=TrustLevel.UNTRUSTED,
        sensitivity=SensitivityLevel.CONFIDENTIAL,
        contains_untrusted_instructions=True,
    )
    allowed, reason = IFCLattice.is_flow_permitted(
        [unsafe_rec], SensitivityLevel.PUBLIC
    )
    assert allowed is False
    assert "Flow violation" in reason
