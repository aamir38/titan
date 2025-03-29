"""
execution_orchestrator.py
Validates and routes signals to the executor
"""

from signal_age_filter import SignalAgeFilter
from redundant_signal_filter import RedundantSignalFilter
from execution_throttle_controller import ExecutionThrottleController
from mock_order_executor import MockOrderExecutor

class ExecutionOrchestrator:
    def __init__(self):
        self.age_filter = SignalAgeFilter()
        self.dup_filter = RedundantSignalFilter()
        self.throttle = ExecutionThrottleController()
        self.executor = MockOrderExecutor()

    def handle_signal(self, signal):
        if not self.age_filter.is_fresh(signal):
            return
        if self.dup_filter.is_duplicate(signal):
            return
        if not self.throttle.allow(signal['symbol']):
            return
        self.executor.execute(signal)
