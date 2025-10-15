from dataclasses import dataclass, field

from age_shared import Header, Instruction


@dataclass
class IR:
    header: Header
    instructions: list[Instruction]
    labels: set[int] = field(default_factory=set)

    def __post_init__(self):
        if not self.labels:
            self._calculate_labels()

    def _calculate_labels(self):
        from age_shared import is_control_flow, is_label_argument

        for instruction in self.instructions:
            if is_control_flow(instruction):
                for idx, arg in enumerate(instruction.arguments):
                    if is_label_argument(instruction, idx):
                        self.labels.add(arg.raw_data)
