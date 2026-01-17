"""Funciones auxiliares y utilidades."""
import random


def weighted_sample_without_replacement(items, weights, k):
    """Selección ponderada sin reemplazo."""
    if k >= len(items):
        return items
    selected = []
    remaining_items = items[:]
    remaining_weights = weights[:]
    for _ in range(k):
        if not remaining_items:
            break
        chosen = random.choices(remaining_items, weights=remaining_weights, k=1)[0]
        selected.append(chosen)
        idx = remaining_items.index(chosen)
        remaining_items.pop(idx)
        remaining_weights.pop(idx)
    return selected
