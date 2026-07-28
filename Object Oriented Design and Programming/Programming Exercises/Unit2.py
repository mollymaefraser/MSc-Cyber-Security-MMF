"""
Online Shopping System: SOLID Principles Refactoring Exercise
================================================================

This file demonstrates the progression from a poorly designed system to one
that adheres to the SOLID principles.

Part 1: The original poorly designed code (as given).
Part 2: The refactored version, applying SRP, OCP, LSP, ISP, and DIP.
"""

from abc import ABC, abstractmethod


# ============================================================
# PART 1: ORIGINAL POORLY DESIGNED CODE
# ============================================================
#
# Problems:
# 1. SRP violation: Order handles cart management, total calculation,
#    AND payment processing all in one class.
# 2. OCP violation: adding a new payment method means editing the
#    pay() method's if/elif chain directly.
# 3. DIP violation: Order is tightly coupled to specific payment
#    types instead of depending on an abstraction.

class OrderOriginal:
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


# ============================================================
# PART 2: REFACTORED CODE (SOLID PRINCIPLES)
# ============================================================

# ------------------------------------------------------------
# Supporting class: a simple Product/Item
# ------------------------------------------------------------
class Item:
    def __init__(self, name, price):
        self.name = name
        self.price = price


# ------------------------------------------------------------
# Single Responsibility Principle (SRP)
# ------------------------------------------------------------
# Order now has exactly one job: manage the cart and calculate totals.
# It no longer knows anything about payments.

class Order:
    def __init__(self):
        self.items = []
        self.discount_percent = 0

    def add_item(self, item):
        self.items.append(item)

    def apply_discount(self, percent):
        self.discount_percent = percent

    def calculate_total(self):
        subtotal = sum(item.price for item in self.items)
        discount_amount = subtotal * (self.discount_percent / 100)
        return subtotal - discount_amount


# ------------------------------------------------------------
# Open/Closed Principle (OCP) + Dependency Inversion Principle (DIP)
# ------------------------------------------------------------
# PaymentMethod is an abstraction. New payment types can be ADDED by
# creating new subclasses, without ever modifying existing code.
# High-level code (Order/PaymentProcessor) depends on this abstraction,
# not on concrete payment classes.

class PaymentMethod(ABC):
    @abstractmethod
    def pay(self, amount):
        """Process a payment of the given amount."""
        pass


class CreditCardPayment(PaymentMethod):
    def pay(self, amount):
        print(f"Processing credit card payment of £{amount:.2f}...")


class PayPalPayment(PaymentMethod):
    def pay(self, amount):
        print(f"Processing PayPal payment of £{amount:.2f}...")


class CryptoPayment(PaymentMethod):
    """
    New payment method added WITHOUT touching any existing class.
    This demonstrates OCP (open for extension, closed for modification)
    and LSP (this can be used anywhere a PaymentMethod is expected,
    without breaking anything).
    """
    def pay(self, amount):
        print(f"Processing crypto payment of £{amount:.2f}...")


# ------------------------------------------------------------
# Interface Segregation Principle (ISP)
# ------------------------------------------------------------
# PaymentMethod only defines pay() -- the one method every payment type
# actually needs. We do NOT bundle in unrelated methods like
# refund() or generate_invoice(), which would force every subclass to
# implement things it may not need. If refund functionality is required,
# it should live in its own separate interface, e.g.:
#
# class Refundable(ABC):
#     @abstractmethod
#     def refund(self, amount):
#         pass
#
# Only payment methods that actually support refunds would implement it.


# ------------------------------------------------------------
# Dependency Inversion Principle (DIP)
# ------------------------------------------------------------
# PaymentProcessor is a high-level class. It depends on the PaymentMethod
# abstraction, not on any concrete payment class. The specific payment
# method is "injected" at runtime.

class PaymentProcessor:
    def __init__(self, payment_method: PaymentMethod):
        self.payment_method = payment_method

    def process_payment(self, amount):
        self.payment_method.pay(amount)


# ============================================================
# Demonstration
# ============================================================

if __name__ == "__main__":
    print("=== Original (poorly designed) code ===")
    old_order = OrderOriginal()
    old_order.add_item(Item("Keyboard", 45.00))
    old_order.add_item(Item("Mouse", 20.00))
    print(f"Total: £{old_order.calculate_total():.2f}")
    old_order.pay("credit")

    print("\n=== Refactored (SOLID) code ===")
    order = Order()
    order.add_item(Item("Keyboard", 45.00))
    order.add_item(Item("Mouse", 20.00))
    order.apply_discount(10)  # 10% discount
    total = order.calculate_total()
    print(f"Total after discount: £{total:.2f}")

    # Order/PaymentProcessor don't care which payment method is used.
    for method in [CreditCardPayment(), PayPalPayment(), CryptoPayment()]:
        processor = PaymentProcessor(method)
        processor.process_payment(total)
