from abc import ABC, abstractmethod
import math


# ============================================================
# Task 1: Basic Class Hierarchy (Inheritance)
# ============================================================

class Vehicle:
    def __init__(self, brand, fuel_type):
        self.brand = brand
        self.fuel_type = fuel_type


class Car(Vehicle):
    def __init__(self, brand, fuel_type, num_doors):
        super().__init__(brand, fuel_type)
        self.num_doors = num_doors

    def __str__(self):
        return f"Car(brand={self.brand}, fuel_type={self.fuel_type}, num_doors={self.num_doors})"


# ============================================================
# Task 2: Polymorphism with Methods
# ============================================================

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass


class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return math.pi * self.radius ** 2


class Rectangle(Shape):
    def __init__(self, length, width):
        self.length = length
        self.width = width

    def area(self):
        return self.length * self.width


# ============================================================
# Task 3: Encapsulation with Access Control
# ============================================================

class BankAccount:
    def __init__(self, balance=0):
        self.__balance = balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.__balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.__balance:
            raise ValueError("Insufficient funds.")
        self.__balance -= amount

    def get_balance(self):
        return self.__balance


# ============================================================
# Task 4: Abstraction with Base Class
# ============================================================

class Animal(ABC):
    @abstractmethod
    def make_sound(self):
        pass


class Dog(Animal):
    def make_sound(self):
        return "Woof!"


class Cat(Animal):
    def make_sound(self):
        return "Meow!"


# ============================================================
# Task 5: Constructor and Destructor
# ============================================================

class Person:
    def __init__(self, name):
        self.name = name

    def __del__(self):
        print(f"Goodbye, {self.name}!")


# ============================================================
# Demonstration / Tests
# ============================================================

if __name__ == "__main__":
    print("--- Task 1: Inheritance ---")
    my_car = Car("Toyota", "Petrol", 4)
    print(my_car)

    print("\n--- Task 2: Polymorphism ---")
    shapes = [Circle(5), Rectangle(4, 6)]
    for shape in shapes:
        print(f"{type(shape).__name__} area: {shape.area():.2f}")

    print("\n--- Task 3: Encapsulation ---")
    account = BankAccount(100)
    account.deposit(50)
    account.withdraw(30)
    print(f"Balance: {account.get_balance()}")
    try:
        account.withdraw(1000)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Task 4: Abstraction ---")
    animals = [Dog(), Cat()]
    for animal in animals:
        print(f"{type(animal).__name__} says: {animal.make_sound()}")

    print("\n--- Task 5: Constructor/Destructor ---")
    p = Person("Alice")
    print(f"Created: {p.name}")
    del p  # explicitly triggers __del__
