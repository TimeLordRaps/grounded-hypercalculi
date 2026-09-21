"""Language Calculus: syntax trees, alphabets, productions, quotations, and proof checking.

``MetamathDatabase`` checks Reverse-Polish-Notation proofs over a *fragment* of
Metamath, not the language. It has constants, variables, floating and essential
hypotheses, axioms, theorems and modus ponens. It does **not** have
substitution, disjoint-variable conditions, frame-derived mandatory hypothesis
ordering, or compressed proofs. Hypotheses are matched literally, so an axiom
stated over ``P`` applies only to arguments that literally mention ``P``.

That makes it incomplete against real Metamath databases, which is the direction
a proof checker can afford to be wrong in. It is not permitted to be wrong in
the other: see ``verify_proof`` for the four defects that let it certify ``|- F.``
and ``tests/test_proof_verifier_soundness.py`` for the attacks that pin them.
"""

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

    @property
    def non_terminals(self) -> frozenset[Symbol]:
        """Set of all non-terminal symbols appearing in the grammar."""
        nts: set[Symbol] = {self.start_symbol}
        for r in self.rules:
            nts.add(r.lhs)
            for s in r.rhs:
                if not s.is_terminal:
                    nts.add(s)
        return frozenset(nts)

    @property
    def terminals(self) -> frozenset[Symbol]:
        """Set of all terminal symbols appearing in grammar production rules."""
        ts: set[Symbol] = set()
        for r in self.rules:
            for s in r.rhs:
                if s.is_terminal:
                    ts.add(s)
        return frozenset(ts)

    def derive(self, max_depth: int = 5) -> set[tuple[Symbol, ...]]:
        """Generate all terminal sentences derivable within max_depth steps.

        Uses breadth-first search over leftmost sentential forms.
        """
        if max_depth < 0:
            raise ValueError("max_depth must be nonnegative")
        sentences: set[tuple[Symbol, ...]] = set()
        frontier: set[tuple[Symbol, ...]] = {(self.start_symbol,)}
        visited: set[tuple[Symbol, ...]] = set()

        for _ in range(max_depth + 1):
            next_frontier: set[tuple[Symbol, ...]] = set()
            for form in frontier:
                if form in visited:
                    continue
                visited.add(form)

                if all(s.is_terminal for s in form):
                    sentences.add(form)
                    continue

                # Expand first non-terminal (leftmost derivation)
                for i, sym in enumerate(form):
                    if not sym.is_terminal:
                        for rule in self.rules:
                            if rule.lhs == sym:
                                new_form = form[:i] + rule.rhs + form[i + 1:]
                                if new_form not in visited:
                                    next_frontier.add(new_form)
                        break
            frontier = next_frontier
            if not frontier:
                break

        return sentences

    def derives_sentence(
        self,
        sentence: Sequence[Symbol],
        max_depth: int = 10,
    ) -> bool:
        """Decide whether a terminal sentence is derivable within max_depth steps."""
        target = tuple(sentence)
        if any(not s.is_terminal for s in target):
            raise ValueError("Target sentence must contain only terminal symbols")
        return target in self.derive(max_depth=max_depth)



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

    def add_essential_hyp(self, label: str, statement: Sequence[str]) -> None:
        """Declare an essential hypothesis, the logical premise of an axiom."""
        self.essential_hypotheses[label] = list(statement)

    def _hypothesis_statement(self, label: str) -> Optional[List[str]]:
        """The statement a hypothesis label stands for, or None if it has none."""
        if label in self.type_hypotheses:
            var, type_code = self.type_hypotheses[label]
            return [type_code, var]
        if label in self.essential_hypotheses:
            return list(self.essential_hypotheses[label])
        return None

    def verify_proof(self, label: str) -> bool:
        """Whether the RPN proof recorded for ``label`` establishes its statement.

        Proof tokens are read left to right against a stack. A hypothesis label
        pushes the statement it stands for. An axiom label pops one entry per
        declared hypothesis, requires each to match, and pushes the axiom's
        statement. A theorem label pushes that theorem's statement only once
        that theorem's own proof has been verified. ``mp`` applies modus ponens.
        The proof succeeds when it ends with exactly the claimed statement on the
        stack, and nothing else.

        Hypotheses are matched **exactly**, not up to substitution. Metamath
        proper unifies an axiom's hypotheses with the arguments by substituting
        for variables, and this does not: an axiom stated over ``P`` applies only
        to arguments literally mentioning ``P``. That rejects valid proofs, which
        is a limitation of this verifier and is the direction it is safe to be
        wrong in. It accepts no step whose hypotheses were not supplied.

        That was not previously true. The popped arguments were discarded
        without comparison, so an axiom reading "from |- A conclude |- F." could
        be applied to |- B, and this method returned True for a proof of
        falsity. Unsoundness in a proof checker is the whole of the thing it is
        for, so these are rejections, not stricter warnings.

        Returns:
            True only if every step is licensed. False for any unknown token,
            unmatched hypothesis, stack underflow, circular citation, or
            residue left on the stack.
        """
        return self._verify(label, in_progress=frozenset())

    def _verify(self, label: str, in_progress: frozenset) -> bool:
        if label not in self.theorems:
            return False
        if label in in_progress:
            # A proof that cites itself, directly or through a chain, establishes
            # nothing. Detect it rather than recurse until the stack gives out.
            return False
        expected_statement, proof_tokens = self.theorems[label]
        nested = in_progress | {label}
        stack: List[List[str]] = []

        for token in proof_tokens:
            hypothesis = self._hypothesis_statement(token)
            if hypothesis is not None:
                stack.append(hypothesis)
            elif token in self.axioms:
                statement, hypothesis_labels = self.axioms[token]
                if len(stack) < len(hypothesis_labels):
                    return False
                # popped comes off top-first; the proof pushes the hypotheses in
                # the order the axiom declares them, so reverse to compare.
                popped = [stack.pop() for _ in range(len(hypothesis_labels))]
                supplied = list(reversed(popped))
                for hypothesis_label, argument in zip(hypothesis_labels, supplied):
                    required = self._hypothesis_statement(hypothesis_label)
                    if required is None or required != argument:
                        return False
                stack.append(list(statement))
            elif token in self.theorems:
                # A cited theorem carries a proof, not a hypothesis list. It may
                # be used only once that proof checks out.
                if not self._verify(token, nested):
                    return False
                stack.append(list(self.theorems[token][0]))
            elif token == "mp":
                consequent = self._modus_ponens(stack)
                if consequent is None:
                    return False
                stack.append(consequent)
            else:
                return False

        return len(stack) == 1 and stack[0] == expected_statement

    @staticmethod
    def _modus_ponens(stack: List[List[str]]) -> Optional[List[str]]:
        """Pop a minor and major premise and return the consequent, or None.

        The major premise must be a parenthesised implication ``|- ( A -> B )``.
        It is split at the ``->`` sitting at paren depth zero, which is the
        connective the formula is an implication *of*; splitting at the first
        ``->`` token instead reads the inner connective of ``( ( A -> B ) -> C )``
        and yields ``B ) -> C``, a token sequence that is not a formula.
        """
        if len(stack) < 2:
            return None
        major = stack.pop()
        minor = stack.pop()
        if len(major) < 5 or major[1] != "(" or major[-1] != ")":
            return None

        body = major[2:-1]
        depth = 0
        split_at = None
        for index, tok in enumerate(body):
            if tok == "(":
                depth += 1
            elif tok == ")":
                depth -= 1
                if depth < 0:
                    return None  # unbalanced
            elif tok == "->" and depth == 0:
                if split_at is not None:
                    return None  # ambiguous: two top-level arrows, not one formula
                split_at = index
        if depth != 0 or split_at is None:
            return None

        antecedent = body[:split_at]
        consequent = body[split_at + 1:]
        if not antecedent or not consequent:
            return None
        if minor[1:] != antecedent:
            return None
        return [major[0]] + consequent
