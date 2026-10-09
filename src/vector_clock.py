"""Реализация векторных часов и отношения happens-before."""

from collections.abc import Sequence


class VectorClock:
    """Векторные часы для фиксированного числа процессов."""

    def __init__(self, process_count: int, values: Sequence[int] | None = None) -> None:
        if process_count < 1:
            raise ValueError("Число процессов должно быть положительным")
        if values is None:
            self.values = [0] * process_count
        else:
            if len(values) != process_count:
                raise ValueError("Длина вектора должна совпадать с числом процессов")
            if any(v < 0 for v in values):
                raise ValueError("Значения вектора не могут быть отрицательными")
            self.values = list(values)

    def increment(self, process_id: int) -> list[int]:
        """Увеличить компоненту процесса; process_id задаётся с нуля."""
        if not 0 <= process_id < len(self.values):
            raise IndexError("Некорректный идентификатор процесса")
        self.values[process_id] += 1
        return self.values

    def update(self, received_vector: Sequence[int]) -> list[int]:
        """Покомпонентный максимум с полученным вектором."""
        if len(received_vector) != len(self.values):
            raise ValueError("Размер полученного вектора не совпадает")
        if any(v < 0 for v in received_vector):
            raise ValueError("Значения вектора не могут быть отрицательными")
        self.values = [max(a, b) for a, b in zip(self.values, received_vector)]
        return self.values

    def copy(self) -> "VectorClock":
        return VectorClock(len(self.values), self.values)

    def __repr__(self) -> str:
        return f"VectorClock({self.values})"


def happens_before(v1: Sequence[int], v2: Sequence[int]) -> bool:
    """True, если v1 строго предшествует v2 по покомпонентному порядку."""
    if len(v1) != len(v2):
        raise ValueError("Сравниваемые векторы должны иметь одинаковую длину")
    return all(a <= b for a, b in zip(v1, v2)) and any(a < b for a, b in zip(v1, v2))


def compare_vectors(v1: Sequence[int], v2: Sequence[int]) -> str:
    """Возвращает BEFORE, AFTER, EQUAL или CONCURRENT."""
    if happens_before(v1, v2):
        return "BEFORE"
    if happens_before(v2, v1):
        return "AFTER"
    if list(v1) == list(v2):
        return "EQUAL"
    return "CONCURRENT"
