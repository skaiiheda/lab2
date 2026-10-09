"""Запуск демонстрационного сценария задания."""

from pathlib import Path
from src.process import Simulation
from src.visualizer import print_event_tables, causal_relations, event_statistics, plot_timeline
from src.versioned_kv import VersionedKV


def conflict_demo() -> None:
    print("\nДЕМОНСТРАЦИЯ КОНФЛИКТА")
    for strategy in ("LWW", "MERGE"):
        store = VersionedKV(strategy)
        store.put("x", 0, [0, 0, 0])
        first = store.put("x", 1, [1, 0, 0])
        second = store.put("x", 0, [0, 1, 0])
        current = store.get("x")
        print(f"\nСтратегия: {strategy}")
        print(f"  Обновление P1: {first.value}, версия {first.vector_clock}, конфликт={first.conflict}")
        print(f"  Обновление P2: {second.value}, версия {second.vector_clock}, конфликт={second.conflict}")
        print(f"  Итог: x={current.value}, версия {current.vector_clock}")


def main() -> None:
    sim = Simulation(3)
    events = sim.run_demo()
    print_event_tables(events)
    pairs = causal_relations(events)
    stats = event_statistics(events)
    print("\nПРИЧИННО-СЛЕДСТВЕННЫЕ ПАРЫ (E1 -> E2)")
    print(", ".join(f"E{a} -> E{b}" for a, b in pairs) or "Нет")
    print("\nСТАТИСТИКА")
    for key, value in stats.items():
        print(f"{key}: {value}")
    chart = plot_timeline(events, Path("output") / "timeline.png")
    print(f"\nДиаграмма сохранена: {chart}")
    conflict_demo()


if __name__ == "__main__":
    main()
