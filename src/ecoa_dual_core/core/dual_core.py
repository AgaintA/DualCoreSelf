from __future__ import annotations

from .gate import WriteGate
from .interpreter import SelfModelInterpreter
from .self_state import SelfStateCore
from .types import InterpreterState, MethodResult, ResidualEvent, SelfLedger, StepAudit


class DualCoreSystem:
    def __init__(self, dual_core_config: dict[str, float], gate_config: dict[str, float]) -> None:
        self.interpreter = SelfModelInterpreter(dual_core_config, gate_config)
        self.gate = WriteGate(gate_config)
        self.self_state_core = SelfStateCore()
        self.reset()

    def reset(self) -> None:
        self.state = InterpreterState()
        self.ledger = SelfLedger()
        self.audit: list[StepAudit] = []
        self.ledger_history: list[SelfLedger] = [SelfLedger()]
        self.write_steps: list[int] = []
        self.committed_classes: list[str] = []

    def step(self, event: ResidualEvent) -> None:
        self.state = self.interpreter.step(self.state, event)
        gate_open, gate_reason = self.gate.evaluate(self.state)

        if gate_open:
            self.ledger = self.self_state_core.apply(self.ledger, self.state, event)
            self.state.cooldown_remaining = self.gate.cooldown_steps
            self.write_steps.append(event.t)
            self.committed_classes.append(self.state.top_hypothesis)

        self.ledger_history.append(
            SelfLedger(
                health=self.ledger.health,
                deformation=self.ledger.deformation,
                calibration=self.ledger.calibration,
                version=self.ledger.version,
            )
        )
        self.audit.append(
            StepAudit(
                t=event.t,
                regime=event.true_regime.value,
                residual=event.residual,
                residual_norm=event.residual_norm,
                mode=self.state.mode.value,
                top_hypothesis=self.state.top_hypothesis,
                confidence=self.state.confidence,
                gate_open=gate_open,
                gate_reason=gate_reason,
                ledger=self.ledger.as_tuple(),
                note=self.state.last_reason,
            )
        )

    def run(self, events: list[ResidualEvent], seed: int) -> MethodResult:
        self.reset()
        for event in events:
            self.step(event)

        return MethodResult(
            method_name="Proposed Dual-Core mechanism",
            regime=events[0].true_regime.value,
            seed=seed,
            onset_step=events[0].onset_step,
            ledger_history=self.ledger_history,
            audit=self.audit,
            write_steps=self.write_steps,
            committed_classes=self.committed_classes,
        )
