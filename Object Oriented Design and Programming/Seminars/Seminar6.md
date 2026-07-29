# Unit 6 Seminar

## Title: Concurrency and Parallelism in Object-Oriented Design

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

This seminar explores the concepts of concurrency and parallelism in object-oriented design, focusing on how to write thread-safe code in multi-threaded environments. Students will learn about threads, processes, and synchronisation mechanisms, as well as common concurrency issues such as race conditions and deadlocks.

The seminar includes a practical exercise to write thread-safe code in Python, reinforcing the theoretical concepts and providing hands-on experience.

---

## Seminar Tasks

### 1. Introduction to Concurrency and Parallelism

- **Concurrency:** managing multiple tasks at once (tasks may be interleaved on a single core, not necessarily running at the exact same instant).
- **Parallelism:** executing multiple tasks simultaneously (requires multiple cores/processors actually running work at the same time).
- **Threads vs. Processes:**

| | Threads | Processes |
|---|---|---|
| **Memory** | Share the same memory space | Have separate, isolated memory |
| **Overhead** | Lightweight to create/switch between | Heavier to create; more overhead |
| **Communication** | Easy (shared variables) but risks race conditions | Requires explicit IPC (pipes, queues, sockets) |
| **Use when** | Tasks are I/O-bound or need shared state | Tasks are CPU-bound and benefit from true parallel execution (bypassing the GIL in Python) |

### 2. Object-Oriented Approaches to Writing Thread-Safe Code

- **Encapsulation** helps thread safety by keeping shared state (e.g. a bank balance) private within a class, forcing all access through controlled methods rather than letting external code mutate it directly.
- **Abstraction** lets synchronisation details (locks, semaphores) be hidden behind simple method calls (e.g. `deposit()`, `withdraw()`), so callers don't need to manage locking themselves.
- **Synchronisation mechanisms:**
  - **Locks (mutexes):** ensure only one thread executes a critical section at a time.
  - **Semaphores:** allow a fixed number of threads to access a resource concurrently (a generalisation of a lock).
  - **Monitors:** a higher-level construct combining a lock with condition variables, often built into the language/class itself (Python's `threading.Lock` used inside a class approximates this).

### 3. Common Concurrency Issues

- **Race Conditions:** occur when multiple threads read and write shared data simultaneously without synchronisation, causing unpredictable or incorrect results (e.g. two threads both reading a balance of £100 before either writes back, causing one deposit to be lost).
- **Deadlocks:** occur when two or more threads each hold a resource the other needs, and both wait forever. Common causes include acquiring multiple locks in inconsistent orders across different threads.
- **Solutions:**
  - **Mutual exclusion:** use locks around critical sections so only one thread mutates shared state at a time.
  - **Deadlock prevention:** always acquire multiple locks in a consistent, agreed order; use timeouts on lock acquisition; minimise the number of locks held simultaneously.
  - **Thread-safe data structures:** use structures designed for concurrent access (e.g. `queue.Queue` in Python) rather than manually synchronising a plain list or dict.

### 4. Practical Exercise: Thread-Safe Bank Account

**Task:** Implement a simple multi-threaded bank account system where multiple threads perform concurrent deposits and withdrawals, using `threading.Lock` to prevent race conditions.

```python
import threading
import time


class BankAccount:
    def __init__(self, balance=0):
        self._balance = balance
        self._lock = threading.Lock()

    def deposit(self, amount):
        with self._lock:
            current = self._balance
            time.sleep(0.001)  # simulate processing delay to expose race conditions
            self._balance = current + amount

    def withdraw(self, amount):
        with self._lock:
            if amount > self._balance:
                print(f"Insufficient funds for withdrawal of £{amount}")
                return
            current = self._balance
            time.sleep(0.001)
            self._balance = current - amount

    def get_balance(self):
        with self._lock:
            return self._balance


def make_deposits(account, amount, times):
    for _ in range(times):
        account.deposit(amount)


def make_withdrawals(account, amount, times):
    for _ in range(times):
        account.withdraw(amount)


if __name__ == "__main__":
    account = BankAccount(balance=1000)

    threads = [
        threading.Thread(target=make_deposits, args=(account, 50, 10)),
        threading.Thread(target=make_deposits, args=(account, 20, 10)),
        threading.Thread(target=make_withdrawals, args=(account, 30, 10)),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"Final balance: £{account.get_balance()}")
    # Expected: 1000 + (50*10) + (20*10) - (30*10) = 1400
```

**Why this is thread-safe:**
- The `_balance` attribute is encapsulated (prefixed with `_`) and only ever modified inside `deposit()`/`withdraw()`, never accessed directly from outside the class.
- Each method wraps its read-modify-write sequence in `with self._lock:`, ensuring mutual exclusion — no two threads can execute the critical section at the same time.
- The artificial `time.sleep(0.001)` inside the critical section is included deliberately to widen the window where a race condition *would* occur if the lock were removed — useful for demonstrating the problem to students by commenting the lock out and observing an incorrect final balance.

---

## Seminar Preparation

### 1. Review the Following Topics
- Concurrency vs. Parallelism.
- Threads and processes.
- Synchronisation mechanisms (e.g., locks, semaphores).
- Race conditions and deadlocks.

### 2. Set Up Your Development Environment
- Ensure you have a working Python development environment.
- Install necessary libraries (e.g., the `threading` module, part of Python's standard library).

### 3. Prepare Questions
- Come prepared with questions or topics you find challenging (e.g., how to avoid deadlocks, when to use locks vs. semaphores).

### 4. Practice Basic Threading Concepts
- Write simple code snippets to practice creating and managing threads in Python.
