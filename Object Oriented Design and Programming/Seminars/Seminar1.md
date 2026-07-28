# Unit 1 Seminar

## Title: Introduction and Recap of Object-Oriented Programming

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

This seminar provides a comprehensive recap of Object-Oriented Programming (OOP) concepts, focusing on their application in large-scale and secure software design. Students will revisit key OOP principles such as inheritance, polymorphism, abstraction, and encapsulation, and explore how these concepts form the foundation for designing robust and maintainable software systems.

The seminar also includes a hands-on practical exercise to implement basic class hierarchies in Python, reinforcing the theoretical concepts covered.

---

## Seminar Tasks

### 1. Recap of Key OOP Concepts

| Concept | Description |
|---|---|
| **Inheritance** | How classes can inherit attributes and methods from other classes. |
| **Polymorphism** | How objects can take on multiple forms (e.g., method overriding). |
| **Abstraction** | How to hide complex implementation details and expose only essential features. |
| **Encapsulation** | How to bundle data and methods into a single unit and control access using access modifiers. |

### 2. Practical Exercise

Implement a basic class hierarchy in Python to demonstrate the application of OOP concepts.

**Example scenario:** Create a class hierarchy for a simple vehicle management system:

- `Vehicle` as a base class
- Subclasses: `Car`, `Bike`, and `Truck`

```python
class Vehicle:
    def __init__(self, brand, fuel_type):
        self.brand = brand
        self.fuel_type = fuel_type

    def describe(self):
        return f"{self.brand} vehicle running on {self.fuel_type}"


class Car(Vehicle):
    def __init__(self, brand, fuel_type, num_doors):
        super().__init__(brand, fuel_type)
        self.num_doors = num_doors


class Bike(Vehicle):
    def __init__(self, brand, fuel_type, has_gears):
        super().__init__(brand, fuel_type)
        self.has_gears = has_gears


class Truck(Vehicle):
    def __init__(self, brand, fuel_type, load_capacity):
        super().__init__(brand, fuel_type)
        self.load_capacity = load_capacity
```

This mirrors the structure covered in the wider OOP recap: each subclass inherits shared attributes from `Vehicle` via `super().__init__()`, while adding its own specific attributes — demonstrating inheritance directly, and setting up the foundation for polymorphism (e.g. overriding `describe()` per subclass), abstraction (hiding internal detail behind simple methods), and encapsulation (controlling access to attributes where needed).

---

## Seminar Preparation

### 1. Review the Following Topics
- Inheritance, polymorphism, abstraction, and encapsulation.
- Classes, objects, constructors, destructors, and access control.

### 2. Set Up Your Development Environment
- Ensure you have a working Python or Java development environment.
- Install necessary tools (e.g., Python interpreter, Java Development Kit).

### 3. Prepare Questions
- Come prepared with questions or topics you find challenging (e.g., polymorphism, access control).

### 4. Practice Basic OOP Concepts
- Write simple code snippets to practice creating classes, objects, and basic inheritance.
