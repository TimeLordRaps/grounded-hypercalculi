"""Language Calculus: syntax trees, alphabets, productions, quotations, and Metamath proof validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class Symbol:
    """A terminal or non-terminal symbol in a formal language."""
    name: str
    is_terminal: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Symbol name cannot be empty")



@dataclass(frozen=True)
class Alphabet:
    """A set of formal symbols defining an alphabet."""
    symbols: Tuple[Symbol, ...] = ()

    @classmethod
    def from_symbols(cls, symbols: Sequence[Symbol]) -> Alphabet:
        return cls(tuple(symbols))

    def __contains__(self, item: Symbol) -> bool:
        return item in self.symbols

@dataclass(frozen=True)
class ProductionRule:
    """A grammar production rule: lhs -> rhs."""
    lhs: Symbol
    rhs: Tuple[Symbol, ...]

    def __str__(self) -> str:
        rhs_str = " ".join(s.name for s in self.rhs) if self.rhs else "epsilon"
        return f"{self.lhs.name} -> {rhs_str}"


@dataclass
class Grammar:
    """A formal grammar defining a formal language."""
    start_symbol: Symbol
    rules: List[ProductionRule] = field(default_factory=list)

    def add_rule(self, lhs: Symbol, rhs: Sequence[Symbol]) -> None:
        self.rules.append(ProductionRule(lhs, tuple(rhs)))


@dataclass(frozen=True)
class QuotationNode:
    """A quotation graph node representing quoted terms or reflexive self-quotations."""
    label: str
    children: Tuple[QuotationNode, ...] = ()
    is_reflexive: bool = False

    @classmethod
    def self_quoting(cls, label: str = "self") -> QuotationNode:
        """Create a reflexive quotation node: t = Quote(t)."""
        return cls(label=label, is_reflexive=True)


@dataclass
class MetamathDatabase:
    """Reverse-Polish-Notation (RPN) formal proof verifier for language calculus."""
    constants: Set[str] = field(default_factory=set)
    variables: Set[str] = field(default_factory=set)
    type_hypotheses: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    essential_hypotheses: Dict[str, List[str]] = field(default_factory=dict)
    axioms: Dict[str, Tuple[List[str], List[str]]] = field(default_factory=dict)
    theorems: Dict[str, Tuple[List[str], List[str]]] = field(default_factory=dict)

    def add_constant(self, c: str) -> None:
        self.constants.add(c)

    def add_variable(self, v: str) -> None:
        self.variables.add(v)

    def add_type_hyp(self, label: str, var: str, type_code: str) -> None:
        self.type_hypotheses[label] = (var, type_code)

    def add_axiom(self, label: str, statement: Sequence[str], hyps: Sequence[str] = ()) -> None:
        self.axioms[label] = (list(statement), list(hyps))

    def add_theorem(self, label: str, statement: Sequence[str], proof: Sequence[str]) -> None:
        self.theorems[label] = (list(statement), list(proof))

    def verify_proof(self, label: str) -> bool:
        """Verify an RPN proof of a theorem in the database."""
        if label not in self.theorems:
            return False
        expected_statement, proof_tokens = self.theorems[label]
        stack: List[List[str]] = []

        for token in proof_tokens:
            if token in self.type_hypotheses:
                var, type_code = self.type_hypotheses[token]
                stack.append([type_code, var])
            elif token in self.essential_hypotheses:
                stack.append(list(self.essential_hypotheses[token]))
            elif token in self.axioms or token in self.theorems:
                entry = self.axioms[token] if token in self.axioms else self.theorems[token]
                stmt, hyps = entry
                num_hyps = len(hyps)
                if len(stack) < num_hyps:
                    return False
                # Consume arguments
                consumed = [stack.pop() for _ in range(num_hyps)] if num_hyps else []
                # Simple substitution / deduction model
                stack.append(list(stmt))
            elif token == "mp":  # Modus Ponens
                if len(stack) < 2:
                    return False
                major = stack.pop()
                minor = stack.pop()
                # If major is |- ( A -> B ) or |- A -> B, and minor is |- A, consequent is |- B
                if len(major) >= 4 and "->" in major:
                    arr_idx = major.index("->")
                    antecedent = major[2:arr_idx] if (len(major) > 2 and major[1] == "(") else major[1:arr_idx]
                    minor_formula = minor[1:] if len(minor) > 1 else minor
                    if antecedent != minor_formula:
                        return False
                    if major[-1] == ")":
                        consequent = [major[0]] + major[arr_idx + 1:-1]
                    else:
                        consequent = [major[0]] + major[arr_idx + 1:]
                    stack.append(consequent)
                else:
                    return False
            else:
                return False

        return len(stack) == 1 and stack[0] == expected_statement
