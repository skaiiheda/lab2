"""Процессы и детерминированная симуляция обмена сообщениями."""

from dataclasses import dataclass
from .event import Event
from .lamport_clock import LamportClock
from .vector_clock import VectorClock


@dataclass
class Message:
    message_id: str
    sender: int
    receiver: int
    payload: str
    lamport_timestamp: int
    vector_clock: list[int]


class Process:
    def __init__(self, process_id: int, process_count: int) -> None:
        self.process_id = process_id
        self.lamport = LamportClock()
        self.vector = VectorClock(process_count)

    def internal(self) -> tuple[int, list[int]]:
        self.lamport.increment()
        self.vector.increment(self.process_id)
        return self.lamport.value, self.vector.values.copy()

    def send(self) -> tuple[int, list[int]]:
        # Отправка является событием, поэтому обе метки увеличиваются.
        return self.internal()

    def receive(self, lamport_timestamp: int, vector_clock: list[int]) -> tuple[int, list[int]]:
        self.lamport.update(lamport_timestamp)
        self.vector.update(vector_clock)
        self.vector.increment(self.process_id)
        return self.lamport.value, self.vector.values.copy()


class Simulation:
    """Симуляция событий; номера процессов начинаются с 0."""

    def __init__(self, process_count: int = 3) -> None:
        if process_count < 2:
            raise ValueError("Для симуляции нужны минимум два процесса")
        self.processes = [Process(i, process_count) for i in range(process_count)]
        self.events: list[Event] = []
        self._next_event_id = 1
        self._messages: dict[str, Message] = {}

    def _record(self, process_id: int, event_type: str, lamport: int,
                vector: list[int], description: str = "", target: int | None = None,
                message_id: str | None = None, conflict: bool = False) -> Event:
        event = Event(self._next_event_id, process_id, event_type, lamport, vector.copy(),
                      description, target, message_id, conflict)
        self._next_event_id += 1
        self.events.append(event)
        return event

    def internal(self, process_id: int, description: str = "Внутреннее событие",
                 conflict: bool = False) -> Event:
        p = self.processes[process_id]
        l, v = p.internal()
        return self._record(process_id, "INTERNAL", l, v, description, conflict=conflict)

    def send(self, sender: int, receiver: int, message_id: str,
             payload: str = "message") -> Event:
        if sender == receiver:
            raise ValueError("Отправитель и получатель должны различаться")
        if message_id in self._messages:
            raise ValueError(f"Сообщение {message_id!r} уже существует")
        p = self.processes[sender]
        l, v = p.send()
        self._messages[message_id] = Message(message_id, sender, receiver, payload, l, v.copy())
        return self._record(sender, "SEND", l, v, payload, receiver, message_id)

    def receive(self, message_id: str) -> Event:
        if message_id not in self._messages:
            raise KeyError(f"Неизвестное сообщение: {message_id}")
        message = self._messages[message_id]
        # Запрещаем повторное получение одного сообщения.
        if message.metadata_received if hasattr(message, "metadata_received") else False:
            raise ValueError("Сообщение уже получено")
        p = self.processes[message.receiver]
        l, v = p.receive(message.lamport_timestamp, message.vector_clock)
        event = self._record(message.receiver, "RECEIVE", l, v,
                             f"{message.payload} (от P{message.sender + 1})",
                             message.sender, message_id)
        # Удаляем сообщение из доступных к получению.
        del self._messages[message_id]
        return event

    def run_demo(self) -> list[Event]:
        """Детерминированный сценарий с пятью сообщениями и двумя конкурентными обновлениями."""
        # Эти две операции независимы: они моделируют конкурентные изменения x
        # и выделяются на диаграмме красным цветом.
        self.internal(0, "Конфликтное обновление x = 1 (P1)", conflict=True)
        self.internal(1, "Конфликтное обновление x = 0 (P2)", conflict=True)
        self.internal(0, "P1 начинает обработку")
        self.send(0, 1, "m1", "Запрос A")
        self.internal(1, "P2 выполняет локальную работу")
        self.receive("m1")
        self.send(1, 2, "m2", "Результат A")
        self.send(0, 2, "m3", "Независимый запрос")
        self.internal(2, "P3 выполняет локальную работу")
        self.receive("m2")
        self.send(2, 0, "m4", "Подтверждение")
        self.receive("m3")
        self.receive("m4")
        self.send(1, 0, "m5", "Дополнительное сообщение")
        self.receive("m5")
        return self.events
