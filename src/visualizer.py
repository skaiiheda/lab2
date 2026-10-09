"""Табличный вывод и диаграмма пространства-времени."""

from pathlib import Path
from .event import Event


def print_event_tables(events: list[Event]) -> None:
    print("\nТАБЛИЦА СОБЫТИЙ")
    print(f"{'ID':>3} {'Процесс':<8} {'Тип':<8} {'Lamport':>7} {'Vector clock':<18} Описание")
    print("-" * 90)
    for e in events:
        print(f"{e.event_id:>3} {e.process_name:<8} {e.event_type:<8} "
              f"{e.lamport_timestamp:>7} {e.vector_string():<18} {e.description}")


def causal_relations(events: list[Event]) -> list[tuple[int, int]]:
    """Все упорядоченные пары событий e1 -> e2 по векторным часам."""
    from .vector_clock import happens_before
    return [(a.event_id, b.event_id) for a in events for b in events
            if a.event_id != b.event_id and happens_before(a.vector_clock, b.vector_clock)]


def event_statistics(events: list[Event]) -> dict[str, int]:
    from .vector_clock import happens_before
    total_pairs = len(events) * (len(events) - 1) // 2
    causal = sum(1 for i, a in enumerate(events) for b in events[i + 1:]
                 if happens_before(a.vector_clock, b.vector_clock) or happens_before(b.vector_clock, a.vector_clock))
    return {"events": len(events), "unordered_event_pairs": total_pairs,
            "causally_related_pairs": causal, "concurrent_pairs": total_pairs - causal}


def plot_timeline(events: list[Event], output_path: str | Path = "timeline.png") -> Path:
    """Сохранить диаграмму: линии процессов, точки событий, стрелки сообщений."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 5.8))
    process_count = max(e.process_id for e in events) + 1
    y_positions = {i: process_count - i for i in range(process_count)}
    colors = {"INTERNAL": "#3977b8", "SEND": "#27966f", "RECEIVE": "#d28b26"}
    by_message: dict[str, Event] = {}
    for e in events:
        if e.event_type == "SEND" and e.message_id:
            by_message[e.message_id] = e
    for pid, y in y_positions.items():
        ax.hlines(y, 0, max((e.lamport_timestamp for e in events), default=1) + 1,
                  color="#aab2bd", linewidth=1.2)
        ax.text(-0.25, y, f"P{pid + 1}", ha="right", va="center", fontweight="bold")
    for e in events:
        x, y = e.lamport_timestamp, y_positions[e.process_id]
        ax.scatter(x, y, s=100, color=("#d62728" if e.conflict else colors[e.event_type]),
                   edgecolors="black", linewidths=.5, zorder=3)
        ax.annotate(f"E{e.event_id}\n{e.event_type}\n{e.vector_string()}",
                    (x, y), xytext=(0, 12 if e.process_id % 2 == 0 else -42),
                    textcoords="offset points", ha="center", fontsize=7)
        if e.event_type == "RECEIVE" and e.message_id and e.message_id in by_message:
            send = by_message[e.message_id]
            ax.annotate("", xy=(x, y), xytext=(send.lamport_timestamp, y_positions[send.process_id]),
                        arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 1.1,
                                    "connectionstyle": "arc3,rad=0.08"})
            ax.text((x + send.lamport_timestamp) / 2,
                    (y + y_positions[send.process_id]) / 2 + .08,
                    e.message_id, fontsize=7, color="#444444")
    ax.set_xlabel("Логическая временная координата (Lamport timestamp)")
    ax.set_yticks([])
    ax.set_title("Диаграмма пространства-времени распределённой системы")
    ax.grid(axis="x", linestyle=":", alpha=.35)
    ax.set_xlim(-.8, max((e.lamport_timestamp for e in events), default=1) + 1.5)
    ax.set_ylim(.3, process_count + .7)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
