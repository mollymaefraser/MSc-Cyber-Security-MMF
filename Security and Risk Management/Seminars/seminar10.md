### 1. Cloud Vendor Lock-In Issues and Mitigations
In his 2024 research, Aashish Kumar identifies that vendor lock-in occurs when an organisation becomes too reliant on a specific cloud service provider (CSP), making migration prohibitively expensive or technically impossible.

#### Main Issues Identified:
* Technical Lock-In: Reliance on proprietary APIs, unique software architectures, or specialised infrastructure that only works within one vendor’s ecosystem.
* Data Lock-In (Data Gravity): The accumulation of massive datasets in a specific cloud makes moving that data elsewhere difficult due to high egress fees and the complexity of transferring large volumes of data.
* Service & Certification Lock-In: Dependency on specific SaaS stacks or proprietary services (like specialised AI tools or databases) that do not have direct equivalents in other clouds.
* Economic/Contractual Lock-In: High implementation fees, "walled garden" pricing models, and long-term contracts that penalise early exit or switching.

#### Mitigation Strategies:
* Adopting Open Standards: Use vendor-agnostic technologies and open-source software to ensure that applications can be ported across different environments.
* Containerisation (Docker/Kubernetes): Decoupling applications from the underlying infrastructure so they can run on any CSP without code changes.
* Multi-Cloud & Hybrid Strategies: Distributing workloads across multiple providers to maintain bargaining power and avoid a single point of failure.
* Exit Strategy Planning: Negotiating "right to exit" clauses in contracts and maintaining updated documentation on how to migrate data and services before a crisis occurs.


### 2. Security Concerns and Mitigations
Corbari et al. (2024), writing in The Cyber Defense Review, focus on security from an operational and "Mission Thread" perspective, highlighting how complexity and miscommunication create security gaps in modern environments.

#### Main Security Concerns:
* The Communication Gap: A disconnect between mission commanders (who focus on operational goals) and cyber defenders (who focus on technical assets). This leads to a lack of shared understanding regarding what needs the most protection.
* Asset-Based vs. Mission-Based Security: Traditional security often focuses on protecting individual servers or assets rather than the end-to-end "thread" of a critical mission. If a non-critical asset is compromised but it lies on a critical mission path, the entire operation fails.
* Adversary Pre-positioning: The threat of adversaries embedding themselves in infrastructure long before a conflict, waiting to disrupt "force projection" or critical services.
* Complexity and Intangibility: The rapid proliferation of digital systems makes it difficult for planners to see the full attack surface, often resulting in "black box" security where leaders don't fully trust or understand their defense posture.

#### Mitigation Strategies:
* Mission Thread Analysis (MTA): Implementing a framework that maps out every step of a mission (the "thread") and identifies the specific technical data pathways (Mission Engineering Threads) required for success.
* Integrated Defensive Cyberspace Operations (DCO): Aligning technical cyber teams with operational planners so that defense resources are prioritised based on mission criticality rather than just generic compliance.
* Cyber Resilience: Shifting from just trying to "prevent" attacks to ensuring the mission can continue even while under fire. This involves identifying critical dependencies and ensuring they are defended.
* Standardised Terminology: Establishing a common framework (as proposed by Corbari et al.) to ensure all stakeholders—from Congress to network operators—speak the same language regarding risk and requirements.
