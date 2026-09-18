"""The proof checker must refuse invalid proofs.

A verifier that accepts everything is worthless in a way that a verifier which
rejects too much is not, so these tests are almost entirely attacks. Each one
constructs a proof of a statement that does not follow, and requires False.

The `negative_control` tests reproduce the replaced logic directly, so the
defects stay legible after the source stops exhibiting them. Run as a whole
against the unfixed verifier, 17 of these 28 fail -- including
`test_an_axiom_cannot_be_applied_to_the_wrong_hypothesis`, which is the one that
matters: it returned True for a proof of falsity. The two citation-cycle tests
pass either way; the old code rejected cycles incidentally, by running out of
stack rather than by noticing them, and they are kept as regression guards
rather than offered as evidence.

The four defects pinned here:

- An axiom's declared hypotheses were popped and thrown away, so any argument
  discharged any hypothesis, and a proof of `|- F.` went through.
- Axiom entries are `(statement, hypothesis_labels)` and theorem entries are
  `(statement, proof_tokens)`; the citation branch unpacked both alike, so a
  theorem could be cited without its own proof ever being checked.
- Modus ponens split the major premise at the first `->` token rather than the
  one at paren depth zero.
- Essential hypotheses could not be declared through the public API at all.
"""

from __future__ import annotations

import pytest

from grounded_hypercalculi.language_calculus import MetamathDatabase

FALSITY = ["|-", "F."]


def _propositional_db() -> MetamathDatabase:
    """P and Q as wffs, with an axiom introducing an implication between them."""
    db = MetamathDatabase()
    for constant in ("|-", "wff", "(", ")", "->"):
        db.add_constant(constant)
    for variable in ("P", "Q"):
        db.add_variable(variable)
    db.add_type_hyp("wp", "P", "wff")
    db.add_type_hyp("wq", "Q", "wff")
    return db


# ============================================================================
# 1. Valid proofs still verify
# ============================================================================


def test_a_one_step_axiom_application_verifies() -> None:
    db = _propositional_db()
    db.add_axiom("ax-1", ["|-", "(", "P", "->", "P", ")"], hyps=["wp"])
    db.add_theorem("th-id", ["|-", "(", "P", "->", "P", ")"], ["wp", "ax-1"])
    assert db.verify_proof("th-id") is True


def test_modus_ponens_over_two_axioms_verifies() -> None:
    db = _propositional_db()
    db.add_axiom("ax-p", ["|-", "P"], hyps=["wp"])
    db.add_axiom("ax-imp", ["|-", "(", "P", "->", "Q", ")"], hyps=["wp", "wq"])
    db.add_theorem("th-q", ["|-", "Q"], ["wp", "ax-p", "wp", "wq", "ax-imp", "mp"])
    assert db.verify_proof("th-q") is True


def test_a_verified_theorem_may_be_cited_by_another() -> None:
    db = _propositional_db()
    db.add_axiom("ax-p", ["|-", "P"], hyps=["wp"])
    db.add_theorem("lemma", ["|-", "P"], ["wp", "ax-p"])
    db.add_theorem("uses-lemma", ["|-", "P"], ["lemma"])
    assert db.verify_proof("lemma") is True
    assert db.verify_proof("uses-lemma") is True


def test_modus_ponens_on_a_nested_implication_verifies() -> None:
    # |- ( ( A -> B ) -> C ) with |- ( A -> B ) gives |- C. Splitting the major
    # premise at the first '->' reads the inner connective and rejects this.
    db = MetamathDatabase()
    db.add_essential_hyp("maj", ["|-", "(", "(", "A", "->", "B", ")", "->", "C", ")"])
    db.add_essential_hyp("min", ["|-", "(", "A", "->", "B", ")"])
    db.add_theorem("nested", ["|-", "C"], ["min", "maj", "mp"])
    assert db.verify_proof("nested") is True


# ============================================================================
# 2. Hypotheses must actually be discharged
# ============================================================================


def test_an_axiom_cannot_be_applied_to_the_wrong_hypothesis() -> None:
    # The central attack. The axiom licenses |- F. only from |- A; the proof
    # offers |- B. Discarding the popped argument made this return True.
    db = MetamathDatabase()
    db.add_essential_hyp("needs_A", ["|-", "A"])
    db.add_essential_hyp("needs_B", ["|-", "B"])
    db.add_axiom("from_A_conclude_falsity", FALSITY, hyps=["needs_A"])
    db.add_theorem("bogus", FALSITY, ["needs_B", "from_A_conclude_falsity"])
    assert db.verify_proof("bogus") is False


def test_an_axiom_whose_hypothesis_label_is_unknown_is_refused() -> None:
    db = MetamathDatabase()
    db.add_essential_hyp("anything", ["|-", "irrelevant"])
    db.add_axiom("needs_one", FALSITY, hyps=["not_in_the_database"])
    db.add_theorem("bogus", FALSITY, ["anything", "needs_one"])
    assert db.verify_proof("bogus") is False


def test_hypotheses_must_be_supplied_in_the_declared_order() -> None:
    db = _propositional_db()
    db.add_axiom("ax-imp", ["|-", "(", "P", "->", "Q", ")"], hyps=["wp", "wq"])
    db.add_theorem("right-order", ["|-", "(", "P", "->", "Q", ")"], ["wp", "wq", "ax-imp"])
    db.add_theorem("wrong-order", ["|-", "(", "P", "->", "Q", ")"], ["wq", "wp", "ax-imp"])
    assert db.verify_proof("right-order") is True
    assert db.verify_proof("wrong-order") is False


def test_an_axiom_with_nothing_on_the_stack_is_refused() -> None:
    db = MetamathDatabase()
    db.add_essential_hyp("h", ["|-", "A"])
    db.add_axiom("needs_one", FALSITY, hyps=["h"])
    db.add_theorem("bogus", FALSITY, ["needs_one"])
    assert db.verify_proof("bogus") is False


def test_negative_control_the_discarded_argument_licensed_anything() -> None:
    # The replaced branch, reproduced: pop the arguments, ignore them, push the
    # conclusion. Any hypothesis is discharged by any argument.
    def legacy_step(stack: list[list[str]], statement: list[str], hyp_count: int) -> bool:
        if len(stack) < hyp_count:
            return False
        for _ in range(hyp_count):
            stack.pop()
        stack.append(list(statement))
        return True

    stack: list[list[str]] = [["|-", "B"]]
    assert legacy_step(stack, FALSITY, 1) is True
    assert stack == [FALSITY], "the old branch concluded falsity from an unrelated premise"


# ============================================================================
# 3. A cited theorem must itself be proved
# ============================================================================


def test_a_theorem_whose_proof_fails_cannot_be_cited() -> None:
    db = MetamathDatabase()
    db.add_type_hyp("tA", "A", "wff")
    db.add_theorem("unproved", FALSITY, ["a_token_that_does_not_exist"])
    db.add_theorem("cites_it", FALSITY, ["tA", "unproved"])
    assert db.verify_proof("unproved") is False
    assert db.verify_proof("cites_it") is False


def test_a_proof_that_cites_itself_is_refused() -> None:
    db = MetamathDatabase()
    db.add_theorem("self_referential", FALSITY, ["self_referential"])
    assert db.verify_proof("self_referential") is False


def test_a_cycle_of_citations_is_refused() -> None:
    db = MetamathDatabase()
    db.add_theorem("thm_a", FALSITY, ["thm_b"])
    db.add_theorem("thm_b", FALSITY, ["thm_c"])
    db.add_theorem("thm_c", FALSITY, ["thm_a"])
    for label in ("thm_a", "thm_b", "thm_c"):
        assert db.verify_proof(label) is False


def test_negative_control_a_theorems_proof_was_read_as_its_hypothesis_list() -> None:
    # Theorem entries are (statement, proof); axiom entries are (statement,
    # hyps). Unpacking both the same way made the citation pop len(proof) items
    # and push the statement, with the proof itself never run.
    db = MetamathDatabase()
    db.add_theorem("unproved", FALSITY, ["a_token_that_does_not_exist"])
    statement, second = db.theorems["unproved"]
    assert second == ["a_token_that_does_not_exist"], "the second element is the proof"
    assert len(second) == 1, "which the old branch would have counted as one hypothesis"


# ============================================================================
# 4. Modus ponens
# ============================================================================


def test_modus_ponens_requires_the_minor_to_be_the_antecedent() -> None:
    db = MetamathDatabase()
    db.add_essential_hyp("maj", ["|-", "(", "A", "->", "B", ")"])
    db.add_essential_hyp("min", ["|-", "X"])
    db.add_theorem("mismatch", ["|-", "B"], ["min", "maj", "mp"])
    assert db.verify_proof("mismatch") is False


def test_modus_ponens_does_not_produce_an_unbalanced_formula() -> None:
    # From |- ( A -> B ) -> C and |- A, splitting at the first '->' yielded
    # '|- B ) -> C'. The major premise is not a parenthesised implication and is
    # now rejected outright.
    db = MetamathDatabase()
    db.add_essential_hyp("maj", ["|-", "(", "A", "->", "B", ")", "->", "C"])
    db.add_essential_hyp("min", ["|-", "A"])
    db.add_theorem("malformed", ["|-", "B", ")", "->", "C"], ["min", "maj", "mp"])
    assert db.verify_proof("malformed") is False


@pytest.mark.parametrize(
    "major",
    [
        ["|-", "A", "->", "B"],                          # unparenthesised
        ["|-", "(", "A", "and", "B", ")"],               # no implication
        ["|-", "(", "->", "B", ")"],                     # empty antecedent
        ["|-", "(", "A", "->", ")"],                     # empty consequent
        ["|-", "(", "A", "->", "B", "->", "C", ")"],     # two top-level arrows
        ["|-", "(", "(", "A", "->", "B", ")"],           # unbalanced, opens too many
        ["|-", "(", ")", "A", "->", "B", ")"],           # unbalanced, closes too early
    ],
)
def test_modus_ponens_refuses_a_major_premise_that_is_not_one_implication(major) -> None:
    db = MetamathDatabase()
    db.add_essential_hyp("maj", major)
    db.add_essential_hyp("min", ["|-", "A"])
    db.add_theorem("attempt", ["|-", "B"], ["min", "maj", "mp"])
    assert db.verify_proof("attempt") is False


def test_modus_ponens_with_too_few_premises_is_refused() -> None:
    db = MetamathDatabase()
    db.add_essential_hyp("only", ["|-", "(", "A", "->", "B", ")"])
    db.add_theorem("short", ["|-", "B"], ["only", "mp"])
    assert db.verify_proof("short") is False


def test_negative_control_the_first_arrow_split_reads_the_inner_connective() -> None:
    major = ["|-", "(", "(", "A", "->", "B", ")", "->", "C", ")"]
    first_arrow = major.index("->")
    assert first_arrow == 4, "the first '->' is the one inside the nested antecedent"
    legacy_antecedent = major[2:first_arrow]
    assert legacy_antecedent == ["(", "A"], "which is not a formula"


# ============================================================================
# 5. Housekeeping the checker must still do
# ============================================================================


def test_an_unknown_token_is_refused() -> None:
    db = MetamathDatabase()
    db.add_theorem("bogus", FALSITY, ["no_such_token"])
    assert db.verify_proof("bogus") is False


def test_a_proof_of_an_unknown_label_is_refused() -> None:
    assert MetamathDatabase().verify_proof("never_declared") is False


def test_residue_left_on_the_stack_is_refused() -> None:
    # Two independent results and a claim to have proved one of them: the proof
    # did not reduce to its statement.
    db = _propositional_db()
    db.add_theorem("residue", ["wff", "P"], ["wp", "wq"])
    assert db.verify_proof("residue") is False


def test_the_conclusion_must_be_the_claimed_statement() -> None:
    db = _propositional_db()
    db.add_axiom("ax-p", ["|-", "P"], hyps=["wp"])
    db.add_theorem("claims-q", ["|-", "Q"], ["wp", "ax-p"])
    assert db.verify_proof("claims-q") is False


def test_essential_hypotheses_are_reachable_from_the_public_api() -> None:
    db = MetamathDatabase()
    db.add_essential_hyp("h", ["|-", "A"])
    assert db.essential_hypotheses["h"] == ["|-", "A"]
