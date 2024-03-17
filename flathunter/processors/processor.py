"""Abstract class defining the 'Processor' interface"""
from typing import Dict

class Processor:
    """Proves the given listing."""

    def process_expose(self, expose: Dict) -> Dict:
        """Mutate the expose. Should be implemented in the subclass"""
        return expose

    def process_exposes(self, exposes):
        """Apply the processor to every expose in the sequence"""
        return map(self.process_expose, exposes)
