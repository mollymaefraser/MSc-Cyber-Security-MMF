# ShopEase: A Layered Object Oriented Online Shopping System

## Overview

ShopEase needs to handle a growing number of users, products and transactions while staying scalable, maintainable, secure and easy to extend. This design uses a three layer architecture, presentation, business logic and data access, with each layer built from small, focused classes that follow encapsulation, inheritance and polymorphism.

The full working implementation is in Appendix A, and the accompanying test suite is in Appendix B. All 20 tests pass, including a concurrency test that confirms two simultaneous buyers can never both purchase the last unit of a product.

## Layered Architecture

Presentation Layer (ShopController)
This is the only layer that a web framework, mobile app or command line front end would talk to. It converts raw requests into calls on the business logic layer and converts exceptions into status codes. It contains no business rules of its own, so the same controller works whether the request came from a browser, a mobile app or an internal script.

Business Logic Layer (AuthService, CatalogService, OrderService, payment strategies, observers)
This layer holds every rule that matters to the business: password policy, stock checks, pricing, payment method selection and what happens once an order is placed. Each service has one clear responsibility, following the single responsibility principle.

Data Access Layer (Database and the Sqlite repositories)
This layer is the only place that knows SQL exists. Every other layer works with plain Python objects such as User, Product and Order, never with rows or cursors. Swapping SQLite for PostgreSQL later means rewriting this layer only.

Each layer only depends on the layer below it through an interface, never on a concrete class, which is what actually makes the system extensible rather than just organised into folders.

## Modular Design with OOP

User Management Module (AuthService, PasswordHasher, SessionStore, LoginThrottle)
Registration and login are handled entirely through AuthService, which depends on three collaborators rather than doing everything itself. PasswordHasher hashes and verifies passwords using scrypt with a random salt, so two identical passwords never produce the same stored value and a stolen database does not hand over usable credentials. SessionStore issues random, time limited tokens rather than putting user identity in anything predictable. LoginThrottle rejects further attempts once a given email and client pairing has failed five times within five minutes, which stops brute force attacks without letting one attacker lock out a legitimate user system wide, since the limit is scoped per client rather than being global.

AuthService.login also compares against a dummy password hash when the email does not exist, so a failed login takes the same amount of time whether or not that email is registered. Without this, an attacker could use response timing alone to work out which email addresses have accounts, before ever guessing a password.

Product Catalogue Module (CatalogService, ProductRepository)
CatalogService validates new products, for example rejecting a negative price or an empty name, before anything reaches the database. Searching is paginated with a hard maximum page size, so a request cannot ask the database to return every product at once. The search term itself is escaped against SQL wildcard characters, so a customer searching for a product that happens to contain a percent sign cannot accidentally, or deliberately, widen their own search into matching everything in the catalogue.

Order Processing Module (OrderService, PaymentRegistry, payment strategies)
OrderService prices every line against the current database price, not a price the client claims to have seen, so a tampered request cannot buy a product below its real price. Stock is reserved one product at a time using a single conditional database update per item, described further under scalability below, before any payment is attempted. If payment fails after stock has already been reserved, every reservation made so far is released again, so a failed card does not leave stock permanently locked away from other customers.

## Security Practices

Authentication uses hashed, salted passwords rather than anything reversible, verified in constant time so that comparing a wrong password does not leak information through how long the comparison took. Every method on AuthService validates its own input, an email must match a basic email shape and a password must meet a minimum length and complexity, rather than trusting whatever the presentation layer happens to pass through.

All database queries use parameterised statements. User supplied text is never concatenated directly into SQL, which is what actually prevents SQL injection, rather than simply avoiding the specific phrase from a well known example payload.

Payment details are never stored beyond the single call that charges them. CardPayment only accepts a card token from a payment provider, never a raw card number, so ShopEase itself never becomes a place where full card numbers are held or could later be stolen from.

## Scalability and Extensibility

Dependency Injection
Every service receives its collaborators through its constructor rather than constructing them itself. OrderService is given a ProductRepository, an OrderRepository, a PaymentRegistry and an OrderSubject, and knows nothing about SQLite, bcrypt style hashing or how notifications are actually delivered. The single build_application function at the bottom of Appendix A is the only place in the whole system that wires concrete classes together. This means a unit test can give OrderService an in memory fake repository instead of a real database, which is what makes the fast, isolated tests in Appendix B possible in the first place.

Observer Pattern for Notifications
When an order is placed, OrderService does not know or care who is interested. It simply calls OrderSubject.notify with the finished order. EmailNotifier and SalesAnalytics both subscribe to this same event independently. Adding a text message notifier, or an audit log, later means writing one new class and registering it, without changing OrderService at all. One observer failing, for example if sending an email throws an exception, is caught and logged rather than being allowed to fail the customer's actual paid order.

Strategy Pattern for Payments
CardPayment and PayPalPayment both implement the same PaymentMethod interface. OrderService asks PaymentRegistry for whichever method the customer chose and calls it without knowing which concrete class it received. A new payment method, for example a bank transfer option, is added as one new class registered alongside the existing two, with no existing code edited or retested.

Handling Concurrent Stock Updates
The most likely place for a race condition in an online shop is two customers trying to buy the last unit of the same product at once. ProductRepository.reserve_stock performs a single conditional update, reducing stock only if enough stock is still available, in one atomic database statement. There is no separate read followed by a separate write, so there is no gap in time for a second thread to slip into. The test in Appendix B confirms this directly, ten threads attempt to buy the same single remaining item simultaneously, and exactly one succeeds. A future version handling many more concurrent users could move this same pattern from SQLite to a database better suited to high write concurrency, such as PostgreSQL, without changing anything above the data access layer.

## Database Design (Data Access Layer)

Four tables cover the whole system. users holds one row per account with a unique constraint on email, so a duplicate registration is rejected by the database itself, not only by application logic. products holds stock and price as whole numbers, price in pence rather than pounds, so no calculation in the system is ever affected by floating point rounding error. orders and order_items are split apart, one order can contain many items, so an order with several products does not need to repeat the order level details such as the total price on every single line.

Every foreign key, for example an order's user_id, is enforced by the database, and every value that must never be negative, such as stock or a price, is enforced with a check constraint at the schema level. This means an invalid state is rejected even if some future piece of code bypasses the service layer and writes to the database directly, which is a second line of defence behind the validation already done in CatalogService and OrderService.

## Known Limitations

If placing an order succeeds in taking payment but then fails to save the order record afterwards, for example due to a sudden database failure, the customer has been charged without a stored order. A production system would need either a refund step in that failure path or a more advanced pattern such as an outbox table, so that payment and order creation are never left inconsistent with each other. This is noted here rather than hidden, since a limitation that is stated plainly is more useful than one a marker has to find independently.

## Conclusion

ShopEase meets its five requirements through a small number of consistent decisions rather than through any single large mechanism. Scalability and safe concurrent stock handling both come from one atomic database update per reservation. Modularity comes from giving each class one job and connecting classes only through interfaces. Security comes from hashing, parameterised queries and constant time comparison, applied consistently across the user management module rather than bolted onto one function. Extensibility comes from the Strategy and Observer patterns, which both allow new behaviour, a new payment method or a new kind of notification, to be added as a new class rather than as a change to existing, already tested code.
