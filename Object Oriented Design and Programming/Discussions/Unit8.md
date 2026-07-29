# Collaborative Discussion: Identifying Code Smells and Refactoring

**Unit:** Formative Collaborative Discussion (starts and ends in this unit week)
**Note:** Not assessed — informal tutor feedback only.

---

## Task

Analyse the provided code snippet and identify areas where refactoring can improve code maintainability and readability.

### Original Code Snippet

```python
def calculate_total_price(items):
    total = 0
    for item in items:
        if item['type'] == 'book':
            total += item['price'] * 0.9  # 10% discount for books
        elif item['type'] == 'electronics':
            total += item['price'] * 0.8  # 20% discount for electronics
        else:
            total += item['price']
    return total
```

---

## Discussion Guidelines

- Submit an initial post to the opening discussion tasks.
- Limit all posts to 300 words maximum, to encourage exchange of ideas.
- Contribute at least two follow-up posts engaging with peers.
- Discuss with peers the best refactoring techniques and finalise a clean, maintainable version of the code.

---

## 1. Code Smells Identified

**Magic Numbers:** `0.9` and `0.8` are hardcoded directly into the calculation with only a trailing comment to explain them. There's no single place to update if the book discount changes from 10% to 15% — you'd have to find and edit the literal inside the function, and if the same discount value were used elsewhere in the codebase, you'd have to update it in multiple places consistently.

**Long Method with Conditional Logic:** `calculate_total_price()` mixes iteration, discount rule selection, and calculation all in one function. Every new item type (e.g. "clothing", "toys") means adding another `elif` branch, so the function's complexity grows unbounded and it becomes harder to read, test, and reason about as the business adds more categories.

---

## 2. Refactored Code

### Option 1 — Named Constants (Simpler Approach)

```python
BOOK_DISCOUNT = 0.9        # 10% off books
ELECTRONICS_DISCOUNT = 0.8  # 20% off electronics
NO_DISCOUNT = 1.0

def calculate_total_price(items):
    total = 0
    for item in items:
        if item['type'] == 'book':
            total += item['price'] * BOOK_DISCOUNT
        elif item['type'] == 'electronics':
            total += item['price'] * ELECTRONICS_DISCOUNT
        else:
            total += item['price'] * NO_DISCOUNT
    return total
```

This fixes the magic numbers but the conditional chain — and its scaling problem — remains.

### Option 2 — Strategy Pattern (More Scalable)

```python
from abc import ABC, abstractmethod


class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, price):
        pass


class BookDiscount(DiscountStrategy):
    def apply(self, price):
        return price * 0.9


class ElectronicsDiscount(DiscountStrategy):
    def apply(self, price):
        return price * 0.8


class NoDiscount(DiscountStrategy):
    def apply(self, price):
        return price


DISCOUNT_STRATEGIES = {
    'book': BookDiscount(),
    'electronics': ElectronicsDiscount(),
}


def calculate_total_price(items):
    total = 0
    for item in items:
        strategy = DISCOUNT_STRATEGIES.get(item['type'], NoDiscount())
        total += strategy.apply(item['price'])
    return total
```

Adding a new discount rule (e.g. `ClothingDiscount`) means adding a class and a dictionary entry — `calculate_total_price()` itself never changes again.

