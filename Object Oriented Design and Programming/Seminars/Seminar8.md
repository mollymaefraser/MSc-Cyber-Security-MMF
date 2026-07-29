# Unit 8 Seminar

## Title: Refactoring and Code Smells

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

This seminar focuses on refactoring and code smells, two critical aspects of maintaining high-quality, readable, and maintainable code. Students will learn how to identify common code smells — indicators of poor design or implementation — and apply refactoring techniques to improve code quality.

The seminar includes a practical exercise where students refactor an existing codebase to eliminate code smells using object-oriented principles such as encapsulation, abstraction, and modularity.

---

## Seminar Tasks

### 1. Introduction to Code Smells

A **code smell** is a surface-level indicator in code that suggests a deeper design problem. Smells aren't bugs — the code still works — but they make software harder to read, test, and change, and they increase technical debt over time as small issues compound across a growing codebase.

| Code Smell | Description |
|---|---|
| **Long Method** | A method that is too long and does too much, mixing multiple responsibilities in one place. |
| **Large Class** | A class that has too many responsibilities, violating the Single Responsibility Principle. |
| **Duplicate Code** | Repeated code blocks that could be consolidated, making future changes error-prone (fixing a bug in one copy but not another). |
| **Primitive Obsession** | Overuse of primitive data types (strings, ints) instead of small, meaningful objects (e.g. passing a raw string for an email address instead of an `Email` value object). |
| **Feature Envy** | A method that is more interested in another class's data than its own, suggesting the method belongs on the other class instead. |

### 2. Refactoring Techniques

**Refactoring** is the process of improving the internal structure of code without changing its external behaviour — the same inputs should always produce the same outputs before and after.

| Technique | What It Does |
|---|---|
| **Extract Method** | Breaks down long methods into smaller, well-named, reusable methods. |
| **Extract Class** | Splits a large class into smaller, more focused classes, each with a single responsibility. |
| **Replace Conditional with Polymorphism** | Uses polymorphism (e.g. Strategy or subclassing) to replace complex if-elif chains. |
| **Introduce Parameter Object** | Groups related parameters into a single object, reducing long parameter lists and primitive obsession. |
| **Remove Duplicate Code** | Consolidates repeated code into a single method, class, or shared utility. |

### 3. Practical Exercise: Refactoring a Customer Management System

**Before refactoring** — a class showing Long Method, Duplicate Code, and Primitive Obsession:

```python
class CustomerManager:
    def __init__(self):
        self.customers = []

    def add_customer(self, name, email, phone, street, city, postcode):
        # Primitive obsession: address is passed as three loose strings
        # Long method: validation, formatting, and storage all mixed together
        if "@" not in email:
            raise ValueError("Invalid email")
        if len(phone) < 10:
            raise ValueError("Invalid phone number")

        formatted_address = f"{street}, {city}, {postcode}"
        self.customers.append({
            "name": name,
            "email": email,
            "phone": phone,
            "address": formatted_address
        })

    def print_customer_summary(self, name, email, phone, street, city, postcode):
        # Duplicate code: same validation logic repeated here
        if "@" not in email:
            raise ValueError("Invalid email")
        if len(phone) < 10:
            raise ValueError("Invalid phone number")

        formatted_address = f"{street}, {city}, {postcode}"
        print(f"{name} | {email} | {phone} | {formatted_address}")
```

**After refactoring** — applying Extract Class (for `Address`), Introduce Parameter Object, and Remove Duplicate Code:

```python
class Address:
    def __init__(self, street, city, postcode):
        self.street = street
        self.city = city
        self.postcode = postcode

    def __str__(self):
        return f"{self.street}, {self.city}, {self.postcode}"


class Customer:
    def __init__(self, name, email, phone, address: Address):
        self._validate_email(email)
        self._validate_phone(phone)
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address

    @staticmethod
    def _validate_email(email):
        if "@" not in email:
            raise ValueError("Invalid email")

    @staticmethod
    def _validate_phone(phone):
        if len(phone) < 10:
            raise ValueError("Invalid phone number")

    def summary(self):
        return f"{self.name} | {self.email} | {self.phone} | {self.address}"


class CustomerManager:
    def __init__(self):
        self.customers = []

    def add_customer(self, customer: Customer):
        self.customers.append(customer)

    def print_customer_summary(self, customer: Customer):
        print(customer.summary())
```

**What changed and why:**
- **Extract Class:** `Address` is now its own object rather than three loose primitive strings (fixes Primitive Obsession).
- **Introduce Parameter Object:** `Customer` groups `name`, `email`, `phone`, and `address` into a single cohesive object, so methods take one parameter instead of six.
- **Remove Duplicate Code:** validation logic lives once, inside `Customer`, instead of being copied into every method that needs it.
- **Extract Method:** validation is broken into small, named methods (`_validate_email`, `_validate_phone`) rather than being inlined repeatedly.
- `CustomerManager` is now smaller and more focused — it manages a collection of customers, while `Customer` is responsible for its own validity and presentation.

---

## Seminar Preparation

### 1. Review the Following Topics
- Code Smells: common types and how to detect them.
- Refactoring Techniques: key methods for improving code quality.

### 2. Set Up Your Development Environment
- Ensure you have a working Python or Java development environment.
- Install necessary tools (e.g., Python interpreter, Java Development Kit).

### 3. Prepare Questions
- Come prepared with questions or topics you find challenging (e.g., how to decide which refactoring technique to use, how to balance refactoring with deadlines).

### 4. Practice Basic Refactoring
- Write simple code snippets and practice refactoring them to improve readability and maintainability.

