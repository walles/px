import enum


class SortOrder(enum.Enum):
    CPU = 1
    MEMORY = 2
    AGGREGATED_CPU = 3

    def next(self):
        if self == SortOrder.CPU:
            return SortOrder.MEMORY
        if self == SortOrder.MEMORY:
            return SortOrder.AGGREGATED_CPU
        return SortOrder.CPU
