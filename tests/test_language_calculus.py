import pytest
from grounded_hypercalculi.language_calculus import (
    Alphabet,
    Grammar,
    MetamathDatabase,
    ProductionRule,
    QuotationNode,
    Symbol,
)


def test_symbols_and_grammar():
    s = Symbol("S", is_terminal=False)
    a = Symbol("a", is_terminal=True)
    b = Symbol("b", is_terminal=True)

    grammar = Grammar(start_symbol=s)
    grammar.add_rule(s, [a, s, b])
    grammar.add_rule(s, [])
    assert len(grammar.rules) == 2
    assert str(grammar.rules[0]) == "S -> a S b"


def test_quotation_graphs():
    reflexive = QuotationNode.self_quoting("omega_quote")
    assert reflexive.is_reflexive
    assert reflexive.label == "omega_quote"


def test_metamath_rpn_verifier():
    db = MetamathDatabase()
    db.add_constant("|-")
    db.add_constant("->")
    db.add_constant("wff")
    db.add_variable("P")
    db.add_type_hyp("wp", "P", "wff")
    db.add_axiom("ax-1", ["|-", "(", "P", "->", "P", ")"], hyps=["wp"])

    db.add_theorem("th-id", ["|-", "(", "P", "->", "P", ")"], ["wp", "ax-1"])
    assert db.verify_proof("th-id")


def test_metamath_modus_ponens_deduction():
    db = MetamathDatabase()
    db.add_constant("|-")
    db.add_constant("->")
    db.add_constant("wff")
    db.add_variable("P")
    db.add_variable("Q")
    db.add_type_hyp("wp", "P", "wff")
    db.add_type_hyp("wq", "Q", "wff")

    # Axiom 1: |- P
    db.add_axiom("ax-p", ["|-", "P"], hyps=["wp"])
    # Axiom 2: |- ( P -> Q )
    db.add_axiom("ax-imp", ["|-", "(", "P", "->", "Q", ")"], hyps=["wp", "wq"])

    # Theorem deriving |- Q via Modus Ponens
    db.add_theorem("th-q", ["|-", "Q"], ["wp", "ax-p", "wp", "wq", "ax-imp", "mp"])
    assert db.verify_proof("th-q")


def test_metamath_modus_ponens_mismatched_antecedent_fails():
    db = MetamathDatabase()
    db.add_constant("|-")
    db.add_constant("->")
    db.add_constant("wff")
    db.add_variable("P")
    db.add_variable("Q")
    db.add_variable("Z")
    db.add_type_hyp("wp", "P", "wff")
    db.add_type_hyp("wq", "Q", "wff")
    db.add_type_hyp("wz", "Z", "wff")

    # Axiom: |- Z
    db.add_axiom("ax-z", ["|-", "Z"], hyps=["wz"])
    # Axiom: |- ( P -> Q )
    db.add_axiom("ax-imp", ["|-", "(", "P", "->", "Q", ")"], hyps=["wp", "wq"])

    # Invalid proof attempting to derive |- Q from |- Z and |- ( P -> Q )
    db.add_theorem("th-bad", ["|-", "Q"], ["wz", "ax-z", "wp", "wq", "ax-imp", "mp"])
    assert not db.verify_proof("th-bad")

