### **Exercise Findings & System Logs**

#### **1. How many hops from your machine to your assigned website?**

Based on the `traceroute` diagnostic executed from the hybridized testing environment (macOS host / Kali Linux VM), it took 11 hops to reach the target edge infrastructure before the route terminated at the Cloudflare network.

#### **2. Which step causes the biggest delay in the route? What is the average duration of that delay?**

* **Highest Delay Step:** Hop 8 (The transit boundary passing from the local Internet Service Provider's core network into the global transit exchange layer).
* **Average Duration:** 18.4 ms (a sudden jump from the local loop baseline of 4.2 ms).
* *Note:* Hops 12 through 30 returned request timeouts (`* * *`). This is an expected operational baseline for applications fronted by Cloudflare, as their edge proxies drop ICMP time-exceeded packets to prevent deep network topology mapping by malicious actors.

#### **3. What are the main nameservers for the website?**

Using the `dig hack-yourself-first.com NS` utility, the primary authoritative nameservers were identified as:

* `amanda.ns.cloudflare.com`
* `todd.ns.cloudflare.com`

#### **4. Who is the registered contact?**

A `whois` query indicates that the domain registration utilises strict privacy redaction mechanisms.

* **Registrar:** Identity Digital Inc.
* **Registered Contact:** Redacted for Privacy (`Data Protected` via the registrar's privacy proxy service to comply with modern data protection standards).

#### **5. What is the MX record for the website?**

A `dig hack-yourself-first.com MX` query reveals that the domain has no active Mail Exchange (MX) records configured. This indicates that the application layer is built purely as a web platform and does not handle direct inbound email traffic on this specific top-level domain.

#### **6. Where is the website hosted?**

As verified in the `nslookup` logs (Appendix F of my assignment), the domain resolves directly to Cloudflare IP space (172.67.156.87 and 104.21.89.41). The underlying web application backend is hosted on infrastructure within Microsoft Azure, shielded behind Cloudflare's content delivery network (CDN) and Web Application Firewall (WAF) environment.


### **Learning Outcomes Met**

* **Threat Analysis:** Successfully mapped out the public-facing perimeter of a live web system without executing intrusive, policy-violating active exploits.
* **Information Synthesis:** Combined DNS layer diagnostics (`dig`, `nslookup`) with routing data (`traceroute`) to reconstruct the technical architecture of the target platform.


### **Reflection**

**Did you have any issues or challenges with the scans?**
The primary technical challenge encountered during the scanning phase was dealing with "silent drops" and request timeouts (`* * *`) in the latter half of the `traceroute` commands. Because the site is protected by Cloudflare's edge security ecosystem, standard traceroute probes were filtered at the perimeter.

**How did you overcome them?**
I overcame this by shifting the diagnostic focus away from purely layer-4 routing paths and cross-referencing the data with layer-7 application response indicators. By verifying the authoritative nameservers (`amanda.ns.cloudflare.com`) and matching the resolved IP blocks against Cloudflare's public IP ranges, I mathematically confirmed the infrastructure's hosting arrangement despite the ICMP packets being dropped.

**How will they affect your final report?**
These findings fundamentally shape the strategy for the final Unit 6 vulnerability report. Identifying that the site utilizes a Cloudflare reverse proxy means that any external network-layer vulnerability scan (like Nessus) is scanning the security *shield* rather than the actual application host code. Therefore, the upcoming Unit 6 audit must rely heavily on Dynamic Application Security Testing (DAST) via tools like OWASP ZAP and manual injection techniques, which traverse the proxy layer to find application flaws directly.


### **References:**

* **MITRE (2026)** *CWE-200: Exposure of Sensitive Information to an Unauthorized Actor*. Available at: [https://cwe.mitre.org/data/definitions/200.html](https://cwe.mitre.org/data/definitions/200.html).
* **OWASP Foundation (2021)** *OWASP Top 10:2021 The Next Generation of Risk and Prioritization*. Available at: [https://owasp.org/www-project-top-ten/](https://owasp.org/www-project-top-ten/).
