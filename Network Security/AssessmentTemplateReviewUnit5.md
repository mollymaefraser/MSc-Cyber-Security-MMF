### **1. Does this template meet the NCSC stated requirement of preparing a baseline to use as a reference point for pen tests? If not, what changes/amendments would you make?**

**Analysis:** The PurpleSec penetration testing and vulnerability assessment templates provide an excellent operational baseline for general commercial entities, but they **do not fully meet** the strict, highly structured requirements set out by the UK NCSC (specifically within the NCSC CHECK framework guidelines).

The NCSC requires a security baseline to act as an immutable, reproducible "IT Health Check" reference point. This means a report must establish exactly what the system's intended "secure state" looks like, rather than just listing discovered flaws. The PurpleSec template operates primarily as a reactive vulnerability disclosure document rather than a proactive *architectural baseline reference tool*.

**Recommended Amendments/Changes to Achieve NCSC Compliance:**

* **Mandatory Scope Verification Matrix:** Add an explicit asset inventory table detailing every IP, hostname, subnet, and API endpoint in-scope, alongside their verified ownership metadata. The NCSC requires strict scope limits to prevent unauthorised scanning of shared public cloud architectures (like Microsoft Azure spaces).
* **Clear Classification of Safe Operating State:** Introduce a section that baselines the known good infrastructure configuration (e.g., specific allowed open ports, expected cryptographic TLS cipher suites, and permitted administrative access points).
* **Methodology and Tool Standardisation:** The template should explicitly reference standardised framework mappings like MITRE ATT&CK matrix techniques and NCSC-approved CREST standards rather than generalised descriptions of NMAP flags.


### **2. What are the two best lessons/examples presented in the report?**

* **Lesson 1: Inclusion of Explicit Proof-of-Concept (PoC) Evidence:** The template excels by requiring sanitised screenshots, raw proxy requests (such as a `GET` request intercept displaying stored XSS payloads like `<h1 onclick="alert(1)">test</h1>`), and exact steps to reproduce the flaw. This eliminates ambiguity for internal development teams, shifting the finding from a theoretical risk to irrefutable technical fact.
* **Lesson 2: Clear Categorisation of Finding Metadata:** Every identified vulnerability contains a structured breakdown detailing the Finding Title, Risk Score (Low/Med/High/Critical), Affected Systems/URLs, and Remediation Solution. This structured architecture bridges the gap between high-level risk management and engineering execution, making it easy to convert findings into actionable tickets.


### **3. What two things do you think are unnecessary or could be done more effectively?**

* **Improvement 1: Ineffective Risk Prioritisation (Missing Contextual Risk Scoring):** The template tends to rely solely on raw tool severity outputs (such as standard Nessus CVSS metrics). This can be done more effectively by introducing Contextual Asset Criticality. A "High" severity vulnerability on a isolated development server shouldn't have the same priority as a "Medium" vulnerability sitting on a live, public-facing user database server handling personal information. The prioritisation should weigh asset importance and data sensitivity alongside the raw bug score.
* **Improvement 2: Unnecessary Verbiage in Technical Phase Summaries:** The generic descriptions detailing how internet-level scanning operates via Nmap and Burp Suite add unnecessary fluff to an executive document. Instead of repeating textbook definitions of how Nmap works, this section could be replaced with a highly concise, dynamic Executive Timeline Graphic or an explicit attack-path narrative showing how an adversary could chain multiple low-level flaws together to compromise the network perimeter.


# **E-PORTFOLIO REFLECTION**

* **Did you have any issues or challenges with this activity?**
The main challenge was transitioning away from evaluating the template purely as a software developer and instead critically analysing it from the perspective of an auditor or compliance officer. Initially, the report looked complete because it successfully cataloged bugs. However, analysing it against the NCSC framework forced me to look for what was missing—specifically, the strict scope tracking and architectural reference baselines required by national standards.
* **How did you overcome them?**
I overcame this by shifting my focus back to our module’s core security frameworks (NIST CSF 2.0 and NCSC Baseline Security Controls). By evaluating the template through the lens of a security baseline standard, I isolated the structural gap between a standard commercial penetration test report and a formal public-sector regulatory audit template.
* **How will they affect your final report?**
This activity heavily shapes the design of my upcoming Unit 6 Vulnerability Audit report. It highlights that listing found vulnerabilities is only half the battle. To produce a professional advisory report, I must clearly define the target's testing constraints, explicitly outline perimeter architecture limitations (such as Cloudflare proxy layers), and ensure that my technical solutions provide a clear, prioritized remediation roadmap that aligns directly with international security standards.
