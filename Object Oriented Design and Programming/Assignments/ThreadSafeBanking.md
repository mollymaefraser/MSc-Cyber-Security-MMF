Thread-Safe Banking System

Assignment: Designing and implementing a thread-safe banking system

1. Introduction

Concurrent access to shared financial data is a common source of subtle, hard-to-reproduce bugs: two threads reading a balance at the same instant, both computing an update from the same stale value, and one write silently overwriting the other. A race condition in a banking system does not merely crash the program: it can silently lose or duplicate money while every individual operation appears, in isolation, correct. This makes concurrency bugs especially dangerous here, since a system can pass casual manual testing and still corrupt data under production load, precisely because the failure only manifests when two operations genuinely overlap in time.

This assignment designs and implements a thread-safe BankAccount class supporting concurrent deposits, withdrawals, and transfers, alongside a TransactionSimulator that exercises the system under realistic concurrent load, and a test suite that validates correctness rather than merely assuming it. Throughout, the guiding principle is to encapsulate synchronisation inside the class, so client code calling deposit or withdraw never needs to reason about locking itself, since thread safety is a property of the object, not a discipline imposed on every caller (Silberschatz, Galvin and Gagne, 2018). This mirrors a broader theme from earlier in the module: encapsulation is not only about tidiness or readability, it is what makes certain correctness guarantees enforceable at all, since a caller cannot violate an invariant it has no way to directly access.

2. The BankAccount Class

Each BankAccount instance owns a private balance attribute and a dedicated lock, shown in full in Appendix A. Using one lock per account, rather than a single global lock shared across every account, is deliberate: a global lock would serialise all transactions system-wide, even ones touching unrelated accounts, destroying any benefit of using threads at all. A per-account lock instead only serialises operations on the same account, the actual source of contention.

Every method that reads or mutates the balance acquires the account's lock for the entire read-modify-write sequence, using Python's context manager syntax so the lock releases automatically even if an exception is raised mid-operation. This is what actually prevents race conditions: without the lock, two threads calling deposit concurrently could both read the same starting balance before either writes back, silently losing one deposit. The balance-reading method also acquires the lock, even though it only reads, since without this a reader could observe a partially updated balance mid-write.

The balance attribute is prefixed with an underscore to signal it is not part of the public interface, and access to it is restricted to methods that go through the lock. This applies the encapsulation principle covered earlier in the module: hiding shared mutable state behind controlled methods is not just good object-oriented practice, it is the mechanism that makes thread safety enforceable at all (Nesteruk, 2022, Part I; Lott and Phillips, 2021).

It is worth addressing a common misconception directly. Python's Global Interpreter Lock ensures only one thread executes Python bytecode at a time, which sometimes leads to the assumption that explicit locking is unnecessary in Python. This is incorrect: the Global Interpreter Lock only guarantees individual bytecode instructions are atomic, not that a multi-step operation such as incrementing the balance, involving a read, an addition, and a write, is atomic as a whole. The interpreter can switch threads between any of these steps, exactly the window in which a race condition occurs. The lock used here is therefore not redundant with the Global Interpreter Lock; it protects the logical operation, not the individual instruction (Python Software Foundation, 2026). This distinction between instruction-level and logical-level atomicity recurs across languages, not just Python, and is a central theme in Goetz et al. (2006).

3. Simulating Concurrent Transactions

The TransactionSimulator class, shown in full in Appendix B, models multiple users performing deposits and withdrawals on the same account concurrently, using one thread per simulated user, following the general pattern for spawning and joining worker threads in Beazley and Jones (2013). Each simulated user runs in its own thread, performing a mix of deposits and withdrawals against the same shared account. The simulator waits for every thread to finish, using each thread's join method, before considering the run complete. Without this, the program could report a balance before all transactions had finished, looking like a bug in the banking logic when it was really just a race in the test harness, not the system under test.

4. Deadlock Prevention: Transfers Between Accounts

A transfer is the one operation in this system that touches two accounts at once, which is exactly the situation deadlock thrives in. Picture two transfers running at once in opposite directions: one thread paying from account 1 into account 2, another paying from account 2 into account 1. If each thread simply claims the lock on whichever account it is paying out of first, both can succeed in claiming their first lock and then stall forever waiting on the second, since neither will ever release what it already holds (Silberschatz, Galvin and Gagne, 2018).

This implementation avoids that outcome by refusing to let the direction of a transfer decide the locking order. In the transfer function shown in full in Appendix C, the two accounts involved are sorted by account number before either lock is touched, so whichever has the lower number is always locked first, regardless of whether it is the source or the destination of that particular transfer. Because every thread follows this same rule, two threads transferring between the same pair of accounts can never end up wanting each other's lock at the same time, since one is always first in the queue for both. This is the lock-ordering technique described by Downey (2016), applied here to a single pair of accounts rather than the more general case of arbitrarily many shared resources.

One consequence of this design is worth being explicit about. The withdraw and deposit methods each take out a lock on the account they are modifying, and transfer also holds that same lock for the whole operation before calling either method. An ordinary lock does not allow the thread already holding it to acquire it again, which would mean a thread locking itself out midway through its own transfer, the moment withdraw or deposit tried to take a lock the surrounding call already held. For this reason, the lock used throughout BankAccount is re-entrant rather than plain: the same thread may acquire it repeatedly, only becoming free once released the same number of times, keeping the outer locking in transfer compatible with the inner locking inside withdraw and deposit.

5. Testing and Validation

Correctness under concurrency cannot be verified by inspection alone, since race conditions are often intermittent and may not appear in a single manual run. Testing under deliberately high load to increase the likelihood a latent defect surfaces is a well-established strategy for exposing intermittent faults of this kind (Myers, Sandler and Badgett, 2011). The test suite in Appendix D uses Python's unittest module and runs a high volume of concurrent transactions to make any race condition statistically likely to surface if the locking were removed.

The first test deliberately uses a high transaction count, ten threads each performing one thousand deposits, since race conditions caused by removing the lock would likely be masked at low volumes, where threads rarely overlap. At this volume, an unsynchronised version reliably produces a final balance below the expected total, giving a clear pass or fail signal. The transfer test checks an invariant rather than an exact value: combined balance across both accounts must remain constant regardless of how many transfers occur, a stronger check than either account's balance alone, since it would catch bugs where money is duplicated or destroyed, not just miscounted.

6. Conclusion

This system meets the assignment's requirements by encapsulating a lock inside each BankAccount instance to eliminate race conditions on individual account operations, using consistent lock ordering in transfer to eliminate deadlocks between accounts, and validating both properties with concurrency-heavy automated tests rather than manual inspection. The design favours a per-account lock over a single global lock, since the latter would serialise every transaction system-wide and defeat the purpose of using threads at all: a small but meaningful example of a synchronisation strategy that can be technically correct while still a poor choice if it ignores performance under realistic load.

The design choice to use a re-entrant lock, rather than a plain one, illustrates a broader lesson: thread safety is rarely solved once and forgotten, but requires each new operation to be checked against the locking strategy already in place. A method that is individually correct in isolation, such as withdraw, can still deadlock once composed with another locking operation, such as transfer, unless the underlying lock is chosen with that composition in mind. Future extensions, such as an audit log or periodic interest, would each need the same question asked: does this new operation acquire locks in an order, and of a type, consistent with everything else that touches shared state? Treating that as a standing design constraint, rather than a one-off fix, is what would keep the system correct as it grows.

References

Beazley, D. and Jones, B. K. (2013) Python Cookbook. 3rd edn. Sebastopol, CA: O'Reilly Media.

Downey, A. B. (2016) The Little Book of Semaphores. 2nd edn. Needham, MA: Green Tea Press.

Goetz, B., Peierls, T., Bloch, J., Bowbeer, J., Holmes, D. and Lea, D. (2006) Java Concurrency in Practice. Boston, MA: Addison-Wesley.

Lott, S. F. and Phillips, D. (2021) Python Object-Oriented Programming: Build Robust and Maintainable Object-Oriented Python Applications and Libraries. 4th edn. Birmingham: Packt Publishing.

Myers, G. J., Sandler, C. and Badgett, T. (2011) The Art of Software Testing. 3rd edn. Hoboken, NJ: Wiley.

Nesteruk, D. (2022) Design Patterns in Modern C++20: Reusable Approaches for Object-Oriented Software Design. 2nd edn. California: Apress.

Silberschatz, A., Galvin, P. B. and Gagne, G. (2018) Operating System Concepts. 10th edn. Hoboken, NJ: Wiley.

Python Software Foundation (2026) threading: Thread-based parallelism. Available at: https://docs.python.org/3/library/threading.html (Accessed: 1 September 2026).

Appendix A: The BankAccount Class

```python
import threading


class InsufficientFundsError(Exception):
    """Raised when a withdrawal or transfer would take a balance below zero."""


class BankAccount:
    """A single bank account that can be used safely by multiple threads at once."""

    def __init__(self, account_number, initial_balance=0):
        if initial_balance < 0:
            raise ValueError("initial_balance cannot be negative")
        self.account_number = account_number
        self._balance = initial_balance
        self._lock = threading.RLock()

    def _check_positive_amount(self, amount, action):
        if amount <= 0:
            raise ValueError(f"{action} amount must be greater than zero")

    def deposit(self, amount):
        self._check_positive_amount(amount, "Deposit")
        with self._lock:
            self._balance += amount

    def withdraw(self, amount):
        self._check_positive_amount(amount, "Withdrawal")
        with self._lock:
            if amount > self._balance:
                shortfall = amount - self._balance
                raise InsufficientFundsError(
                    f"Account {self.account_number} is short by £{shortfall} "
                    f"for this withdrawal (balance: £{self._balance})"
                )
            self._balance -= amount

    def get_balance(self):
        with self._lock:
            return self._balance
```

Appendix B: The TransactionSimulator Class

```python
import random
import threading
import time


class TransactionSimulator:
    """Drives concurrent, randomised deposit and withdrawal activity against one account."""

    MIN_TRANSACTION_AMOUNT = 1
    MAX_TRANSACTION_AMOUNT = 50
    SIMULATED_LATENCY_SECONDS = 0.001

    def __init__(self, account: BankAccount):
        self.account = account

    def _perform_random_transaction(self):
        amount = random.randint(self.MIN_TRANSACTION_AMOUNT, self.MAX_TRANSACTION_AMOUNT)
        action = random.choice(["deposit", "withdraw"])

        if action == "deposit":
            self.account.deposit(amount)
        else:
            try:
                self.account.withdraw(amount)
            except InsufficientFundsError:
                pass  # a declined withdrawal under contention is expected, not a bug

        time.sleep(self.SIMULATED_LATENCY_SECONDS)

    def simulate_user(self, user_id, num_transactions=10):
        for _ in range(num_transactions):
            self._perform_random_transaction()

    def run(self, num_users=5, num_transactions=10):
        user_threads = [
            threading.Thread(target=self.simulate_user, args=(uid, num_transactions))
            for uid in range(num_users)
        ]
        for thread in user_threads:
            thread.start()
        for thread in user_threads:
            thread.join()
```

Appendix C: The transfer Function

```python
def transfer(source: BankAccount, destination: BankAccount, amount):
    """Move funds between two accounts, locking both in a fixed order to avoid deadlock."""
    lower_account, higher_account = sorted(
        (source, destination), key=lambda account: account.account_number
    )

    with lower_account._lock, higher_account._lock:
        source.withdraw(amount)
        destination.deposit(amount)
```

Appendix D: Test Suite

```python
import threading
import unittest


class TestBankAccount(unittest.TestCase):
    DEPOSIT_THREAD_COUNT = 10
    DEPOSITS_PER_THREAD = 1000

    def test_many_concurrent_deposits_add_up_correctly(self):
        account = BankAccount("ACC001", initial_balance=0)

        def repeated_deposits():
            for _ in range(self.DEPOSITS_PER_THREAD):
                account.deposit(1)

        workers = [
            threading.Thread(target=repeated_deposits)
            for _ in range(self.DEPOSIT_THREAD_COUNT)
        ]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()

        expected_total = self.DEPOSIT_THREAD_COUNT * self.DEPOSITS_PER_THREAD
        self.assertEqual(account.get_balance(), expected_total)

    def test_withdrawal_beyond_balance_is_rejected(self):
        account = BankAccount("ACC002", initial_balance=10)
        with self.assertRaises(InsufficientFundsError):
            account.withdraw(50)

    def test_combined_balance_is_unchanged_by_concurrent_transfers(self):
        account_a = BankAccount("ACC003", initial_balance=500)
        account_b = BankAccount("ACC004", initial_balance=500)
        starting_total = account_a.get_balance() + account_b.get_balance()

        def shuffle_funds_back_and_forth():
            for _ in range(100):
                transfer(account_a, account_b, 5)
                transfer(account_b, account_a, 5)

        workers = [
            threading.Thread(target=shuffle_funds_back_and_forth) for _ in range(4)
        ]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()

        ending_total = account_a.get_balance() + account_b.get_balance()
        self.assertEqual(starting_total, ending_total)


if __name__ == "__main__":
    unittest.main()
```
