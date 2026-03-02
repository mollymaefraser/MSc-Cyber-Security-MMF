### 1. Key Elements and Interdependencies in CPS
A comprehensive threat model for Industrial Cyber-Physical Systems (ICPS) must move beyond simple network diagrams to capture the "bridge" between the digital and physical worlds.

* **The Elements:**
* **Physical Assets:** Sensors, actuators, and machinery that interact with the environment.
* **Cyber Assets:** PLCs (Programmable Logic Controllers), HMIs (Human-Machine Interfaces), and edge/cloud servers.
* **Communication Links:** Industrial protocols (MQTT, OPC UA, Modbus) that facilitate data exchange.

* **The Interdependencies:**
* **Cyber-to-Physical:** How a command sent from a workstation translates into physical movement or heat.
* **Physical-to-Cyber:** How sensor data influences automated decision-making.

* **Why they are critical:** Standard IT threat models focus on Data Integrity. In ICPS, the focus shifts to Process Integrity. If a model fails to capture how a cyber-exploit impacts physical safety (e.g., overriding a pressure relief valve), the risk analysis will underestimate the "impact," potentially leading to catastrophic physical failure or loss of life.


### 2. Identifying Entry Points and Challenges
Threat modeling serves as a "blueprint" for an attacker’s potential path.

* **Identifying Entry Points:**
The paper emphasises the use of Data Flow Diagrams (DFDs) and Attack Trees. By mapping the flow of information from the corporate network down to the field level, security teams can pinpoint high-risk entry points like remote maintenance access, IIoT sensors, and legacy hardware that lack modern encryption.
* **The Challenges:**
* **Heterogeneity:** ICPS involve a mix of modern "Smart" devices and 20-year-old legacy systems that cannot be patched.
* **Real-time Constraints:** Security measures cannot introduce latency that disrupts physical synchronisation.
* **Complexity of Scale:** In Smart Manufacturing, the "attack surface" is massive because every component is interconnected, making it difficult to model every possible permutation of an attack.


### 3. Scenario-Specific Metrics and Prioritisation
In the era of smart manufacturing, you can't fix everything at once. Jbair et al. highlight that risk assessment must be contextual.

* **Scenario-Specific Metrics:**
Instead of using generic CVSS (Common Vulnerability Scoring System) scores, ICPS threat modeling uses metrics tailored to the industrial process. This includes:
* **Safety Impact:** Does this vulnerability risk human injury?
* **Operational Downtime:** How much will this cost the factory per hour?
* **Environmental Impact:** Could this cause a chemical leak?

* **Guiding Countermeasures:**
By mapping vulnerabilities to specific attack scenarios (e.g., a "Man-in-the-Middle" attack on a robotic arm), organisations can prioritise "choke points." If one countermeasure (like network segmentation) can mitigate five high-risk scenarios simultaneously, it becomes a high-priority investment. This ensures that security budgets are spent on mitigating the most "physical" risks rather than just "digital" annoyances.


### Comparison of IT vs. OT Threat Modeling

| Feature | IT Threat Modeling | ICPS/OT Threat Modeling |
| --- | --- | --- |
| **Primary Goal** | Protect Data (Confidentiality) | Protect Process (Availability/Safety) |
| **Impact Metric** | Data Breach / Financial Loss | Physical Damage / Safety Risk |
| **Life Cycle** | 3–5 years (High turnover) | 15–30 years (Legacy systems) |
| **Connectivity** | Standardised (TCP/IP) | Highly Diverse (Proprietary Protocols) |
