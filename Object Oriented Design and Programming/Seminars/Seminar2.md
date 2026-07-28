# Unit 2 Seminar

## Title: SOLID Principles of Object-Oriented Design

---

## Learning Outcomes

By the end of this seminar, students should be able to:

- Understand and implement secure coding practices in software development.
- Apply advanced object-oriented principles to solve complex software problems.
- Utilise design patterns to create reusable, maintainable, and flexible code.
- Design software architectures suitable for large-scale systems, ensuring security and robustness.
- Develop software solutions that are adaptable for AI models and efficient for data science tasks.

---

## General Overview

This seminar provides a detailed exploration of the SOLID principles of object-oriented design, which are essential for writing maintainable, scalable, and robust software systems. Students will learn about each of the five SOLID principles — Single Responsibility Principle (SRP), Open/Closed Principle (OCP), Liskov Substitution Principle (LSP), Interface Segregation Principle (ISP), and Dependency Inversion Principle (DIP) — and how to apply them in real-world systems.

The seminar includes a practical exercise where students refactor code to adhere to SOLID principles, reinforcing the theoretical concepts covered.

---

## Seminar Tasks

### 1. Introduction to SOLID Principles
- Overview of Object-Oriented Design.
- Importance of SOLID principles in software development.

### 2. Detailed Exploration of Each SOLID Principle

| Principle | Summary |
|---|---|
| **Single Responsibility Principle (SRP)** | A class should have only one reason to change — i.e. one job. |
| **Open/Closed Principle (OCP)** | Classes should be open for extension but closed for modification. |
| **Liskov Substitution Principle (LSP)** | Subclasses should be substitutable for their base class without breaking functionality. |
| **Interface Segregation Principle (ISP)** | Prefer several small, focused interfaces over one large, general-purpose one. |
| **Dependency Inversion Principle (DIP)** | High-level modules should depend on abstractions, not on low-level concrete implementations. |

### 3. Practical Exercise

Hands-on session where students refactor code to adhere to SOLID principles.

**Worked example: online shopping system**

Starting point — a poorly designed `Order` class that mixes cart management, total calculation, and payment processing in one place:

```python
class Order:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def calculate_total(self):
        return sum(item.price for item in self.items)

    def pay(self, payment_type):
        if payment_type == "credit":
            print("Processing credit card payment...")
        elif payment_type == "paypal":
            print("Processing PayPal payment...")
        # Adding a new payment method requires modifying this class.
```

**Issues:**
- Violates **SRP** — `Order` handles cart management *and* payment.
- Violates **OCP** — every new payment method means editing `pay()`.
- Violates **DIP** — `Order` is tightly coupled to specific payment types.

**Refactored solution:**

- `Order` — manages items and calculates totals only (**SRP**).
- `PaymentMethod` — an abstract base class defining `pay(amount)`, with concrete subclasses (`CreditCardPayment`, `PayPalPayment`, `CryptoPayment`) implementing it (**OCP**, **LSP**).
- `PaymentProcessor` — depends on the `PaymentMethod` abstraction rather than any concrete class, with the specific method injected at runtime (**DIP**).
- Interfaces stay small and focused, e.g. `PaymentMethod` only defines `pay()`, keeping unrelated behaviour (like refunds) in a separate interface (**ISP**).

This mirrors the same refactor covered in the seminar's practical exercise, and is a useful reference point when practising your own refactoring.

---

## Seminar Preparation

### 1. Review the Following Topics
- SOLID Principles: SRP, OCP, LSP, ISP, and DIP.
- Refactoring Techniques: how to refactor code to improve design.

### 2. Set Up Your Development Environment
- Ensure you have a working Python or Java development environment.
- Install necessary tools (e.g., Python interpreter, Java Development Kit).

### 3. Prepare Questions
- Come prepared with questions or topics you find challenging (e.g., how to balance SRP with performance, when to apply DIP).

### 4. Practice Basic Refactoring
- Write simple code snippets and practice refactoring them to improve readability and maintainability.
