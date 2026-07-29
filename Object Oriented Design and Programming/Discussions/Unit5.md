# Collaborative Discussion: Strategy Pattern Refactoring

**Unit:** Formative Collaborative Discussion (starts and ends in this unit week)
**Note:** Not assessed — informal tutor feedback only.

---

## Task

Analyse the provided code snippet and refactor it using the Strategy Pattern. The code represents a simple payment system that processes payments using different methods (e.g., Credit Card, PayPal).

### Original Code Snippet

```python
class PaymentProcessor:
    def process_payment(self, payment_type, amount):
        if payment_type == "credit_card":
            print(f"Processing credit card payment of ${amount}")
        elif payment_type == "paypal":
            print(f"Processing PayPal payment of ${amount}")
        elif payment_type == "bank_transfer":
            print(f"Processing bank transfer of ${amount}")
        else:
            raise ValueError("Invalid payment type")
```

---

## Discussion Guidelines

- Submit an initial post to the opening discussion tasks.
- Limit all posts to 300 words maximum, to encourage exchange of ideas.
- Contribute at least two follow-up posts engaging with peers.
- Discuss with peers the best refactoring techniques and finalise a clean, maintainable version of the code.

---

## 1. Problems in the Current Implementation

- **Violates OCP:** Adding a new payment method (e.g. Crypto) means editing `PaymentProcessor` directly, risking existing logic every time the system grows.
- **Tight coupling:** All payment logic lives inside one method, so `PaymentProcessor` knows the implementation details of every payment type — it isn't just orchestrating, it's doing the work itself.
- **Poor readability/maintainability:** The if-elif chain scales linearly with payment types; with a dozen methods this becomes a long, error-prone block that's hard to test in isolation.

---

## 2. How the Strategy Pattern Helps

The Strategy Pattern extracts each payment method into its own class implementing a shared interface. `PaymentProcessor` no longer contains payment logic — it just delegates to whichever strategy object it's given. This satisfies OCP (new strategies are added, not edited in), removes the coupling (each strategy is independently testable), and replaces the if-elif chain with simple delegation.

---

## 3. Refactored Code

```python
from abc import ABC, abstractmethod


# Step 1: Strategy interface
class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount):
        pass


# Step 2: Concrete strategies
class CreditCardPayment(PaymentStrategy):
    def pay(self, amount):
        print(f"Processing credit card payment of ${amount}")


class PayPalPayment(PaymentStrategy):
    def pay(self, amount):
        print(f"Processing PayPal payment of ${amount}")


class BankTransferPayment(PaymentStrategy):
    def pay(self, amount):
        print(f"Processing bank transfer of ${amount}")


# Step 3: Refactored context class
class PaymentProcessor:
    def __init__(self, strategy: PaymentStrategy):
        self.strategy = strategy

    def process_payment(self, amount):
        self.strategy.pay(amount)


# Step 4: Usage example
if __name__ == "__main__":
    processor = PaymentProcessor(CreditCardPayment())
    processor.process_payment(100)

    processor.strategy = PayPalPayment()
    processor.process_payment(50)

    processor.strategy = BankTransferPayment()
    processor.process_payment(200)
```

A new method like `CryptoPayment` is added as a new class implementing `PaymentStrategy` — `PaymentProcessor` never changes.

---

## 4. Benefits of Using the Strategy Pattern

- **Extensibility:** new payment methods slot in without touching existing, working code.
- **Testability:** each strategy can be unit tested in isolation, rather than through one large conditional method.
- **Runtime flexibility:** the strategy can be swapped on the same `PaymentProcessor` instance at runtime (as shown in the usage example), which the if-elif version can't offer as cleanly.
- **Readability:** `process_payment` is now a single line of delegation, regardless of how many payment types exist.
