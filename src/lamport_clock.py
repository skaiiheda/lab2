"""Реализация логических часов Лэмпорта."""

class LamportClock:
    """Логические часы одного процесса."""

    def __init__(self, initial: int = 0) -> None:
        if initial < 0:
            raise ValueError("Начальное значение часов не может быть отрицательным")
        self.value = initial

    def increment(self) -> int:
        """Увеличить часы при внутреннем событии или отправке сообщения."""
        self.value += 1
        return self.value

    def update(self, received_timestamp: int) -> int:
        """Обновить часы при получении сообщения: max(local, received) + 1."""
        if received_timestamp < 0:
            raise ValueError("Полученная метка не может быть отрицательной")
        self.value = max(self.value, received_timestamp) + 1
        return self.value

    def __repr__(self) -> str:
        return f"LamportClock({self.value})"
