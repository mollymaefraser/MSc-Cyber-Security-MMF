Based on the frameworks discussed in the literature (specifically the resilience-driven framework by Adhillah et al. (2025) and the Business Continuity/Disaster Recovery (BCDR) strategies outlined by Kirvan (2025)), the following is a summary of applicable frameworks and recommendations for three distinct organisational contexts.

### **1. Applicable Frameworks by Organisation**

| Organisation | Recommended Framework(s) | Rationale |
| --- | --- | --- |
| **International Bank** | NIST CSF 2.0 & FFIEC | Banks require high-level compliance and robust risk management. The FFIEC (Federal Financial Institutions Examination Council) framework is industry-standard for financial stability, while NIST CSF 2.0 provides the "Identify, Protect, Detect, Respond, Recover" lifecycle essential for digital transactions. |
| **Large Hospital** | ISO 27001 & NIST 800-34 | Hospitals manage sensitive life-critical data. ISO 27001 provides a globally recognised Information Security Management System (ISMS), while NIST 800-34 focuses on contingency planning for IT systems that support patient care. |
| **Large Food Factory** | IEC 62443 & Adhillah et al. Resilience Framework | Food manufacturing relies on Operational Technology (OT). IEC 62443 focuses on Industrial Control Systems (ICS) security. The Adhillah et al. (2025) framework is vital here for its emphasis on "predictive" and "preemptive" capabilities to prevent physical production halts. |


### **2. Tests and Recommendations**

#### **International Bank**
* **Key Recommendations:**
* **Zero Trust Architecture:** Implement micro-segmentation so that a breach in one branch or department cannot escalate to the core banking system.
* **AI-Enhanced Detection:** Use the "Predictive" stage of the Adhillah framework to analyse transaction patterns and detect fraud or advanced persistent threats (APTs) in real-time.

* **Suggested Tests:**
* **Full-Scale Simulations:** Conduct unannounced "Red Team" exercises where ethical hackers attempt to breach the network to test the "Detect" and "Respond" functions.
* **RTO/RPO Audits:** Regularly test that the Recovery Time Objective (RTO) for customer-facing apps is near zero.

#### **Large Hospital**
* **Key Recommendations:**
* **Legacy System Protection:** Many hospitals use older medical devices. I recommend "virtual patching" and isolating these devices on separate network segments.
* **Culture of Security:** Adhillah et al. emphasize "Security Culture." Training should ensure staff do not bypass security for "speed of care" (e.g., shared passwords).

* **Suggested Tests:**
* **Functional Drills:** Practice "downtime procedures" where medical staff must operate using paper records while IT simulates a total system recovery.
* **Phishing Simulations:** Since hospitals are high-value targets for ransomware, monthly phishing tests for all staff are essential.

#### **Large Food Manufacturing Factory**

* **Key Recommendations:**
* **IT/OT Convergence:** Ensure the factory floor (OT) is not directly connected to the office (IT) network. Use the "Preemptive" measures from Adhillah to block threats before they reach PLC (Programmable Logic Controller) systems.
* **Supply Chain Resilience:** Following Kirvan’s advice, map all third-party dependencies (e.g., raw ingredient suppliers) to ensure a cyberattack on a vendor doesn't halt your production line.

* **Suggested Tests:**
* **Tabletop Exercises:** Bring managers together to walk through a "Ransomware on the Production Line" scenario.
* **Failover Testing:** Test the automated switch-over to backup power and data systems to ensure the physical manufacturing process (e.g., refrigeration) remains uninterrupted.


### **Module Wiki Post Structure**

#### **Section 1: FAQ (Frequently Asked Questions)**

* **Q: Why choose IEC 62443 for a food factory instead of just NIST?**
* *A: While NIST is excellent for data, IEC 62443 is specifically designed for the machinery and control systems (OT) found in factories, where safety and continuous physical output are more critical than data privacy.*


* **Q: What is the difference between RTO and RPO in a hospital setting?**
* *A: RTO (Recovery Time Objective) is how quickly you need the patient records back online. RPO (Recovery Point Objective) is how much data you can afford to lose (e.g., the last 5 minutes of vitals vs. the last 4 hours).*
