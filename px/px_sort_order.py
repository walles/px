import enum


class SortOrder(enum.Enum):
    CPU = 1
    MEMORY = 2
    CUMULATIVE_CPU = 3

    def next(self):
        if self == SortOrder.CPU:
            return SortOrder.MEMORY
        if self == SortOrder.MEMORY:
            return SortOrder.CUMULATIVE_CPU
        return SortOrder.CPU
