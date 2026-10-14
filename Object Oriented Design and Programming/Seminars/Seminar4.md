# Unit 4 Seminar

## Title: Design Patterns II: Structural Patterns

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

This seminar focuses on Structural Design Patterns, which are essential for organising classes and objects into larger, more flexible structures. Students will explore key structural patterns such as Adapter, Bridge, Composite, Decorator, Facade, Proxy, and Flyweight, and learn how these patterns enable modular and maintainable code.

The seminar includes a case study on the use of structural patterns in real-world applications (e.g., network security) and a practical exercise to implement the Decorator pattern in Python.

---

## Seminar Tasks

### 1. Purpose and Use Cases of Structural Patterns

| Pattern | Purpose | Typical Use Case |
|---|---|---|
| **Adapter** | Converts one interface into another that a client expects. | Integrating a legacy SOAP payment system with a modern REST API. |
| **Bridge** | Decouples an abstraction from its implementation so both can vary independently. | Remote controls (Basic, Advanced) operating different devices (TV, Radio). |
| **Composite** | Composes objects into tree structures, treating individual objects and compositions uniformly. | A file system where files and folders share the same interface. |
| **Decorator** | Adds behaviour to an object dynamically without altering its class. | Adding toppings/costs to a base coffee object at runtime. |
| **Facade** | Provides a simplified, unified interface to a complex subsystem. | A single `OrderFacade` hiding inventory, payment, and shipping subsystems. |
| **Proxy** | Provides a placeholder/surrogate to control access to another object. | Lazy-loading a large image, or adding access control to a sensitive resource. |
| **Flyweight** | Minimises memory use by sharing common state across many similar objects. | Rendering thousands of trees in a game, sharing texture/mesh data between instances. |

### 2. How Structural Patterns Enable Modular and Flexible Code

- They promote **modularity** by separating concerns; each class has a clear, narrow role (e.g. a `Device` only knows how to turn on/off; a `RemoteControl` only knows how to send commands).
- They promote **flexibility** by allowing behaviour or structure to change at runtime (Decorator, Proxy) or by allowing new implementations to be added without modifying existing code (Adapter, Bridge).
- They promote **reusability** by defining shared interfaces (e.g. `FileSystemComponent`, `PaymentGateway`) that let new concrete classes plug into existing client code untouched.
- In **large-scale systems**, they help manage complexity by hiding subsystem detail behind a single interface (Facade), avoiding class explosion from combinatorial subclassing (Bridge), and controlling access to expensive or sensitive resources (Proxy), all of which keep systems maintainable as they grow.
- In domains like **network security**, structural patterns are commonly used to wrap legacy or third-party components behind consistent, controlled interfaces (Adapter, Proxy), so that security checks, logging, or rate-limiting can be layered in without touching the underlying implementation.

### 3. Practical Exercise: Decorator Pattern

**Task:** Build a coffee shop application where toppings (milk, sugar, etc.) can be added dynamically to a base coffee object, with each topping adding its own cost and description.

```python
from abc import ABC, abstractmethod


# Component interface
class Coffee(ABC):
    @abstractmethod
    def cost(self):
        pass

    @abstractmethod
    def description(self):
        pass


# Concrete component
class SimpleCoffee(Coffee):
    def cost(self):
        return 2.50

    def description(self):
        return "Coffee"


# Base decorator
class CoffeeDecorator(Coffee):
    def __init__(self, coffee: Coffee):
        self._coffee = coffee

    def cost(self):
        return self._coffee.cost()

    def description(self):
        return self._coffee.description()


# Concrete decorators
class MilkDecorator(CoffeeDecorator):
    def cost(self):
        return self._coffee.cost() + 0.50

    def description(self):
        return self._coffee.description() + " + Milk"


class SugarDecorator(CoffeeDecorator):
    def cost(self):
        return self._coffee.cost() + 0.20

    def description(self):
        return self._coffee.description() + " + Sugar"


class WhippedCreamDecorator(CoffeeDecorator):
    def cost(self):
        return self._coffee.cost() + 0.75

    def description(self):
        return self._coffee.description() + " + Whipped Cream"


if __name__ == "__main__":
    order = SimpleCoffee()
    print(f"{order.description()}: £{order.cost():.2f}")

    order = MilkDecorator(order)
    order = SugarDecorator(order)
    print(f"{order.description()}: £{order.cost():.2f}")

    order = WhippedCreamDecorator(order)
    print(f"{order.description()}: £{order.cost():.2f}")
```

**Why this works as a Decorator example:**
- `SimpleCoffee` is the base component with a fixed cost and description.
- Each decorator (`MilkDecorator`, `SugarDecorator`, `WhippedCreamDecorator`) wraps a `Coffee` object and adds its own cost/description on top, without modifying `SimpleCoffee` itself.
- Decorators can be stacked in any combination and order at runtime, giving flexible, composable behaviour; this is the core benefit of the Decorator pattern over creating a rigid subclass for every topping combination (e.g. `CoffeeWithMilkAndSugar`).

---

## Seminar Preparation

### 1. Review the Following Topics
- Structural Design Patterns: Adapter, Bridge, Composite, Decorator, Facade, Proxy, Flyweight.
- Decorator Pattern: how it works and its use cases.

### 2. Set Up Your Development Environment
- Ensure you have a working Python or Java development environment.
- Install necessary tools (e.g., Python interpreter, Java Development Kit).

### 3. Prepare Questions
- Come prepared with questions or topics you find challenging (e.g., when to use the Bridge pattern vs. the Adapter pattern).

### 4. Practice Basic OOP Concepts
- Write simple code snippets to practice creating classes and objects, as structural patterns build on these fundamentals.

