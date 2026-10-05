# Object Oriented Design and Programming: e-Portfolio

## Declaration of AI use

I used an AI assistant while producing some of the artefacts in this portfolio, mainly to draft code tests (primarily helping me find edge cases), which I then ran, reviewed and edited. Every test result quoted below comes from a real run of the code in the repository folders named. I have treated AI output as a draft to be verified, and the reflection sections are my own account of what I learned. This statement is intended to follow the module's guidance on AI use.

## Artefact index

All artefacts are in the submitted e-portfolio folder.

- Assignments/ThreadSafeBanking.md: thread-safe banking assignment (graded 66%, Merit)
- Programming Exercises/Unit1.py, Unit2.py, Submissions/Unit3.py: OOP basics, SOLID shopping system, Factory Method
- Submissions/Unit9.md: ShopEase layered design
- Programming Exercises/Unit10/: secure e-learning platform (TDD, 137 tests, report in Unit10.md)
- Programming Exercises/Unit11/: dependency injection refactor (24 tests)
- Seminars/Seminar10.md: Strategy, Decorator, Visitor, Abstract Factory, Model Registry, Feature Store, mocking and AI-driven testing
- Seminars/Seminar12/: SupplyChainGuard capstone (code, 39 tests, slides)
- Discussions/: forum posts and peer responses for Units 4, 5, 7 and 8

---

# Part A: Portfolio

## Task 1: Key learning outcomes

### Secure coding practices

The module moved me from treating security as a feature to treating it as a property of the design. The clearest evidence is the e-learning platform (Unit10). Passwords are stored as salted scrypt hashes, sessions use random tokens of which only a SHA-256 digest is kept server side, every SQL statement is parameterised, and access is role based with deny by default. Two details taught me more than the headline controls. First, login throttling is keyed on client and email together, so one attacker cannot lock a legitimate user out of their own account. Second, authentication verifies against a dummy hash when an account does not exist, so response time does not reveal which emails are registered. The capstone applied the same thinking to a dependency scanner: size limits on input, API key checks through a dedicated authenticator, and fail-closed behaviour when an advisory source is unavailable, so a failed lookup is reported as UNVERIFIED rather than as safe.

### Advanced object-oriented principles

Unit 2 and ShopEase applied SOLID to a shopping domain, and the Unit 11 refactor applied the dependency inversion principle directly. The original UserManager created its own EmailService, so it could not be tested without sending email and could not switch to SMS. After refactoring, UserManager depends on a notification abstraction supplied from outside, and a small composition root wires the real objects together. The banking assignment applied encapsulation to concurrency: the account owns its lock, and lock ordering for transfers prevents deadlock (Goetz et al., 2006). Early in that work a plain Lock deadlocked on every transfer, because a method holding the lock called another method needing it. Switching to a re-entrant lock fixed it, and the failure taught me that thread safety has to be tested, not assumed.

### Design patterns for reusable, maintainable, flexible code

Over the module I used Factory Method (Unit 3), Abstract Factory, Builder, Adapter, Decorator, Facade, Strategy, Observer and Visitor (Gamma et al., 1994). The key lesson was choosing a pattern for the change it protects against, not for its own sake. Section 2.1 gives the detail.

### Advanced patterns and what they gave me

Strategy gave runtime behavioural flexibility: the capstone swaps scoring algorithms, including a model-backed one, without touching the scanner. Decorator gave separation of concerns: caching and audit logging wrap an advisory source without the source knowing. Visitor separated reporting algorithms from the result objects, so adding a new report format means adding a class, not editing the data. Abstract Factory gave scalability and extensibility: a whole family of authentication components can be swapped as one unit. Together these allow a system to grow by addition rather than modification, which is the open/closed principle in practice (Martin, 2017).

### AI-oriented patterns (conceptual awareness)

I met two architectural patterns from machine learning engineering. A Model Registry manages the lifecycle and versioning of models so that callers request a named model and version instead of constructing one. A Feature Store centralises feature computation so that training and serving use the same definitions, avoiding the skew that Sculley et al. (2015) identify as a source of hidden technical debt. I built small in-memory versions of both for Seminar 10 and the capstone, backed by a rule-based stand-in model. They are deliberately simple, but the interfaces are the point: a real model could replace the stand-in without any caller changing.

### Large-scale secure architecture

Unit 9 (ShopEase) and Unit 10 compared a layered modular monolith against microservices. I argued for layers with clear dependency direction (presentation, service, data access) as the right starting point, with seams where services could later be split, because distributed systems add operational and security cost that a small team may not need (Martin, 2017). I have not load tested any of this, which is an honest limit discussed in Part B.

### AI-adaptable and data-efficient design

The capstone's ScoringStrategy accepts any model through a registry, and ModelScoring clamps whatever the model returns to the range 0 to 1 and never trusts raw model output. Dependencies are parsed once into immutable value objects, and advisory lookups sit behind a caching decorator, which is the efficiency side of the same design.

### Linking each outcome to practical work

Utilising design patterns: the capstone (Sections 2.1 and 2.3) and Seminar 10 are the main evidence, supported by the Factory Method car exercise in Unit 3. Between them they show creational, structural and behavioural patterns, each used to absorb a specific kind of change. Designing architectures for large-scale systems with security and robustness: the ShopEase design (Unit 9) argues the layering and its dependency direction, and the e-learning platform (Unit 10) implements it with security controls and a six-cycle test-first record. Developing solutions adaptable for AI models and efficient for data tasks: the capstone's registry, feature store and model-backed scoring strategy, with the Seminar 10 mocking work showing how AI-dependent components are tested without a live model. Secure coding and advanced object-oriented principles run through all of these, with the banking assignment and the Unit 11 refactor as the sharpest individual examples.

---

## Task 2: Showcase of artefacts

### 2.1 Advanced design patterns (practical)

Strategy. Chosen because password rules, scoring algorithms and pricing rules all vary independently of the code that uses them. From the capstone:

```python
class ScoringStrategy(ABC):
    @abstractmethod
    def score(self, dep: Dependency, advisories: list) -> float:
        """Return a risk score between 0.0 and 1.0."""

class ModelScoring(ScoringStrategy):
    def score(self, dep, advisories):
        model = self._registry.get(self._name, self._version)
        value = model.predict(self._features.features_for(dep, advisories))
        return min(max(float(value), 0.0), 1.0)  # never trust a model output blindly
```

Maintainability improves because each algorithm is a small class. Extensibility improves because a new algorithm is a new class. Testability improves because each strategy is tested in isolation with plain inputs. The e-learning platform uses the same pattern for PasswordRule, so the policy can change without touching UserService.

Decorator. Chosen to add caching and audit logging to advisory sources without modifying them. Both decorators implement the same interface as the source they wrap, so they can be stacked in any order. This improves maintainability because cross-cutting behaviour lives in one place, and testability because each decorator is tested against a stub source. Seminar 10 applies the same idea to a signup service with logging and rate limiting.

Visitor. Chosen to separate reporting from the result objects. TextRenderer and JsonRenderer each visit every DependencyResult, and the Seminar 10 signup system has compliance and analytics visitors. New report formats do not change the data classes. The cost is that adding a new result type forces every visitor to change, which is the trade-off I weigh below.

Abstract Factory. Chosen in Seminar 10 so that a standard and an enterprise authentication family each create their own matching validator and hasher, preventing mismatched combinations. Switching the family is one decision at the composition root. The same shape supports switching AI service providers, since each provider's client, parser and cost model can come from one factory.

### 2.2 Testing: mocking and AI-driven testing

Mocking. In Seminar 10 a SignupService depends on a FraudScoringService. Tests replace it with Mock(spec=FraudScoringService), so no live model or API is involved, and the spec restricts calls to methods the real class actually has. create_autospec goes further and checks call signatures, which protects against a mock that silently drifts away from the real interface. I also used a hand-written stub where a mock's call tracking was irrelevant, following the distinctions in Meszaros (2007). In Unit 11 the refactored UserManager is tested with a mock notifier, so the tests check that the right message is requested without sending anything. Separate integration tests then check the real wiring.

AI-driven testing. I used an AI assistant for test-case generation and edge-case discovery. It suggested a very long password, non-ASCII characters and an empty client address for a rate limiter, and I kept those after review. It also suggested fuzzing the password with random byte sequences, which I did not add, because the form layer only ever passes a Python string and the test would not check anything real. That judgement is the point: the tool is fast at proposing cases, but deciding which cases matter in this system is an engineering decision. For regression support, the full suite in Unit10 runs in about a second, which makes it cheap to rerun after every refactor. I treat AI testing as support for object-oriented quality and not a substitute for judgement. A generated test that passes proves nothing until I know what it would fail on.

To check that the tests had teeth, I wrote a mutation check for the e-learning platform that deliberately breaks ten security behaviours and confirms the suite notices:

```
CAUGHT    Remove lockout check
CAUGHT    Keep sessions after password change
CAUGHT    Let anyone change roles
CAUGHT    Do not escape LIKE wildcards
SURVIVED  Skip dummy hash for unknown users (timing defence, not unit testable)

9 caught, 1 survived
```

The survivor is reported honestly: the timing defence cannot be observed reliably in a unit test. Branch coverage on the same code reports 100%, but the mutation result is the stronger evidence, since coverage only shows lines were run.

### 2.3 Case study and capstone highlights

Scalable architecture. The capstone scanner is a Facade over parsers, advisory sources, scoring and reporting. A ParserFactory selects the parser for each manifest type, an Adapter wraps a legacy vulnerability feed, and Observers receive alerts. Each seam is a place where a new parser, feed or notifier can be added without editing existing classes. The e-learning platform uses repository classes behind its services, so storage could move from SQLite to a server database by changing one layer.

Robustness and reliability. The e-learning platform was built test first. Each of six red-green cycles has saved output of a failing run followed by a passing one. Writing tests first exposed two real defects: password verification crashed when the stored hash was missing, and a blocked login attempt was not being written to the audit log. Both were fixed with a failing test first. The capstone adds 39 tests, including failure paths such as an unreachable advisory source.

AI-readiness at design level. Models are reached only through an interface and a registry, features come from one store, outputs are clamped, and failures degrade to an explicit unverified state. The system can accept a real model later without changes to callers.

### 2.4 Critical commentary on artefacts

Banking assignment. The object was a thread-safe account and transfer. Techniques: encapsulation, a re-entrant lock owned by the account, and consistent lock ordering. The challenge was the self-deadlock described above. The tutor praised the work (66%) and asked for more references, diagrams, scalability and stress testing, logging and persistence, and a README. I address these points in my plan in Part B.

Capstone. Techniques: Facade, Factory, Adapter, Decorator, Strategy, Visitor, Observer, Builder. The main challenge was restraint. Eight patterns in one small system risks being a pattern catalogue rather than a design. I kept each only where I could name the change it absorbed, such as a new feed, report format or scoring approach. Pattern trade-offs: Visitor makes new reports easy but new result types costly; Decorator keeps classes small but deep stacks are harder to debug; Strategy adds a class per algorithm, which is wasteful for one fixed rule.

E-learning platform. Techniques: layered architecture, Strategy for password rules, repositories, TDD. Testing complexity came from time and concurrency. I injected a fake clock so session expiry and lockout tests never sleep, and lowered the scrypt cost parameter in tests so hashing did not dominate run time.

DI refactor. Technique: constructor injection with a composition root and a container. The challenge was abstraction versus over-engineering. A container is overkill for two classes, so I kept manual wiring as the default and showed the container as an option for growth (Seemann and van Deursen, 2019).

ShopEase. A design-level artefact where the lesson was drawing the dependency direction first, so that each layer knows only about the one beneath it.

Abstraction versus over-engineering. My working rule became: introduce an interface when there are, or are credibly about to be, two implementations, or when it is needed to replace a slow or non-deterministic dependency in a test. Otherwise keep the concrete class.

Scalability and stress testing. I have not yet measured how these systems behave under load. The in-memory session store and throttle in the e-learning platform would not survive more than one server process, so a shared store would be needed before scaling out. The capstone's caching decorator would need an expiry policy and size bound for long-running use. I record these as known limits, not as solved problems.

Collaboration. These artefacts were individual work. The collaborative element of the module was the discussion forum, where I posted on structural patterns, the Strategy pattern, insecure authentication and code smells, and replied to peers each unit. Those replies are in the Discussions folder and show me engaging with other people's designs critically, for example by questioning whether a Bridge example justified its extra abstraction.

---

# Part B: Reflection

## Task 3: Skill development

### Academic skills

Critical thinking and analysis. The most useful habit was asking what change a design decision protects against. The capstone could have used inheritance for scoring, but composition through Strategy let me swap algorithms at runtime, and I could explain why. The mutation check also changed how I judge tests: a high coverage figure is a claim, and a mutation run is evidence.

Ethics in AI-driven object-oriented design. Class hierarchies can bake in assumptions. If a risk model's inputs are chosen by an inheritance tree of feature classes, an unexamined feature can propagate bias into every subclass, and a Feature Store that is shared widely multiplies that effect. Transparency matters too: an object that returns only a score gives a reviewer nothing to challenge, so I designed results to carry the version of the model used and a verified flag, which supports explainability and auditability. Black-box coupling is the other risk. Because the model sits behind an interface and a registry, it can be swapped, inspected and tested against a stub, and the audit log records which decisions were made. Documenting models in the way proposed by Mitchell et al. (2019) is a natural next step. As a designer I am responsible for making these systems testable and traceable, because clean design is what makes later scrutiny possible.

Problem-solving. The deadlock in the banking work and the unhandled missing hash in the platform were both found by running code, not by reading it. Refactoring the UserManager showed that hard-to-test code is usually tightly coupled code (Fowler, 2018).

Research and self-study. I drew on Gamma et al. (1994) for pattern intent, Martin (2017) for architecture, Meszaros (2007) for test doubles and Sculley et al. (2015) for ML system design. Writing peer responses in the forums pushed me to read beyond the set material to support a point, for example on code smells and on Strategy versus conditional logic.

### Employability skills

Time management. The module's tasks were a mixture of short seminars and large pieces (the banking assignment, the e-learning case study and the capstone). Splitting large work into small verified steps, as TDD does, also helped planning, because each step had a visible finish. The capstone in particular was easier once the design was settled and the work became a series of small additions.

Communication and literacy. The banking assignment went through plagiarism-check feedback, with a first Turnitin similarity of 21% and a later 14% after I rewrote passages in my own words and referenced properly. That taught me how closely referencing and originality are linked. Forum posts taught me to make one clear claim and support it, and peer responses taught me to add something new instead of agreeing.

Resilience and interpersonal skills. I have a professional background as a software engineer, so some concepts were familiar, but formal pattern vocabulary and security reasoning were not. The 66% on the banking assignment, with feedback about missing diagrams and stress testing, was a useful reminder that working code is not the same as a well-evidenced submission. In the forums, discussion with peers showed me alternative views, such as when a pattern is worth its extra classes.

## Task 4: Professional Development Plan

### Reflective model

I use Kolb's learning cycle (Kolb, 1984), with Bloom's Revised Taxonomy (Anderson and Krathwohl, 2001) to judge my level, and Gibbs' cycle (Gibbs, 1988) for the main critical incident.

Concrete experience: the banking transfer deadlocked. Reflective observation: I assumed the lock was safe because each method looked correct alone. Abstract conceptualisation: re-entrancy and lock ordering explain the failure. Active experimentation: an RLock, then tests for concurrent transfers. In Gibbs' terms, the feeling was frustration, the evaluation was that tests should have come first, and my action plan was test-first development, which I then applied in the e-learning platform.

On Bloom's taxonomy, I can apply and analyse patterns confidently. I am at the evaluate level on testing, as the mutation work shows, and I am only starting to create at scale, because I have not yet built a system under real load.

### Strengths

- Test-first discipline and evidence-based claims, shown by the red and green output and the mutation check.
- Security reasoning at design level.
- Reasoning about when a pattern is worth its cost.

### Areas for improvement

- Scalability, stress testing and persistence, as the tutor feedback and my own review both indicate.
- Diagrams and structured documentation, such as UML for each design and a README for each project.
- Referencing breadth, using more primary and academic sources.
- Practical experience with real ML tooling, since my Model Registry and Feature Store are conceptual.

### Goals and actions

AI-aware software architecture. Over the next six months, replace the stand-in model in the capstone with a real model served through the registry and measure latency. Reading: Sculley et al. (2015) in full, then a book on machine learning system design. Certification to consider: a cloud architecture associate certificate.

Advanced testing strategies for intelligent systems. Add property-based testing and load tests to the platform and capstone, and record results. Reading: Meszaros (2007) on test doubles at scale.

Ethical software engineering in AI-integrated applications. Write a model card for the capstone's risk model, following Mitchell et al. (2019).

Success measures: a load-tested version of one artefact with a README and UML diagrams, one real model integrated, and one model card published in the repository.

---

# References

Anderson, L.W. and Krathwohl, D.R. (eds.) (2001) A taxonomy for learning, teaching, and assessing: a revision of Bloom's taxonomy of educational objectives. New York: Longman.

Fowler, M. (2018) Refactoring: improving the design of existing code. 2nd edn. Boston: Addison-Wesley.

Gamma, E., Helm, R., Johnson, R. and Vlissides, J. (1994) Design patterns: elements of reusable object-oriented software. Reading, MA: Addison-Wesley.

Gibbs, G. (1988) Learning by doing: a guide to teaching and learning methods. Oxford: Further Education Unit, Oxford Polytechnic.

Goetz, B., Peierls, T., Bloch, J., Bowbeer, J., Holmes, D. and Lea, D. (2006) Java concurrency in practice. Upper Saddle River, NJ: Addison-Wesley.

Kolb, D.A. (1984) Experiential learning: experience as the source of learning and development. Englewood Cliffs, NJ: Prentice Hall.

Martin, R.C. (2017) Clean architecture: a craftsman's guide to software structure and design. Boston: Pearson.

Meszaros, G. (2007) xUnit test patterns: refactoring test code. Upper Saddle River, NJ: Addison-Wesley.

Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I.D. and Gebru, T. (2019) 'Model cards for model reporting', Proceedings of the Conference on Fairness, Accountability, and Transparency, pp. 220-229.

Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J.-F. and Dennison, D. (2015) 'Hidden technical debt in machine learning systems', Advances in Neural Information Processing Systems, 28.

Seemann, M. and van Deursen, S. (2019) Dependency injection principles, practices, and patterns. Shelter Island, NY: Manning.
