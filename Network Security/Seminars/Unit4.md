# **Seminar Preparation: Data Breach Case Study Analysis**

### **Selected Case:** The Equifax Data Breach (2017)

#### **1. What types of data were affected?**

The breach exposed the highly sensitive Personally Identifiable Information (PII) of approximately 147 million individuals. The compromised data fields included:

* Full names and Social Security Numbers (SSNs).
* Dates of birth and physical residential addresses.
* Driver’s license numbers.
* Credit card numbers (for roughly 209,000 consumers).

#### **2. What happened?**

The initial entry vector was an unpatched, known remote code execution (RCE) vulnerability in the Apache Struts web framework (CVE-2017-5638). Equifax’s security team was notified of the patch requirement in March 2017 but failed to apply it to their legacy dispute portal. Attackers scanned and identified this vulnerability, gained access to the system environment, and spent over 140 days systematically exfiltrating data packets completely undetected. The traffic went unnoticed because Equifax had let an internal network traffic encryption monitoring certificate expire ten months prior, blinding their intrusion detection systems (IDS).

#### **3. Who was responsible?**

* **External Actors:** Sophisticated, state-sponsored threat actors (subsequently indicted by the US Department of Justice as members of the Chinese military).
* **Internal Failures:** Systemic corporate governance oversight failures. The ultimate professional accountability fell upon the Chief Executive Officer (CEO), Chief Information Officer (CIO), and Chief Information Security Officer (CISO), all of whom resigned or retired shortly after the public disclosure.

#### **4. Were any escalation(s) stopped - how?**

Yes, multiple critical internal communications and escalations broke down:

* The US Department of Homeland Security (DHS) sent out a patch alert for the Apache Struts flaw on March 8, 2017. Internal IT management distributed the patch directive via email on March 9, but the system administrators responsible for the portal failed to implement it.
* Subsequent automated internal vulnerability scans failed to flag the unpatched portal due to misconfigured scanning parameters, creating a false sense of security and stopping any further operational escalation.

#### **5. Was the Business Continuity Plan instigated?**

No, a traditional Disaster Recovery or Business Continuity Plan (BCP) designed to maintain business availability during downtime was not actively initiated because the live production systems remained operational throughout the breach. Instead, the firm moved into a delayed Incident Response (IR) and crisis management phase once the compromise was discovered on July 29, 2017.

#### **6. Was the ICO notified?**

Yes. Because Equifax is a global credit bureau handling data for international residents, the breach impacted approximately 15 million citizens in the United Kingdom. Equifax notified the Information Commissioner’s Office (ICO). Since the breach occurred just prior to the enforcement of the modern GDPR framework, the ICO fined Equifax the maximum allowable penalty under the UK Data Protection Act 1998, which was £500,000.

#### **7. Were affected individuals notified?**

Yes, but the notification process was severely flawed and heavily criticised. Discovery occurred in late July 2017, but public notification was delayed until September 7, 2017 (nearly six weeks later). Equifax directed worried consumers to a hastily constructed, unsecure dedicated website (`equifaxsecurity2017.com`) that looked like a phishing page, and initially required users to waive their rights to class-action lawsuits in order to check if their data was stolen.

#### **8. What were the social, legal and ethical implications of the decisions made?**

* **Social Implications:** Severe erosion of public trust. Unlike standard consumer businesses, credit bureaus collect consumer data involuntarily; individuals could not opt-out of having Equifax hold their PII, creating widespread societal anger over the lack of data sovereignty.
* **Legal Implications:** Massive global litigation. Equifax eventually agreed to a global regulatory settlement of at least $575 million with the US Federal Trade Commission (FTC), the Consumer Financial Protection Bureau (CFPB), and multiple states, alongside the landmark maximum fine from the UK ICO.
* **Ethical Implications:** Prior to public disclosure, three high-level Equifax executives sold stock worth nearly $1.8 million. While an independent review stated they did not know of the breach at the time, it raised massive ethical and professional conflict-of-interest concerns regarding transparency and insider trading.

#### **9. If you had been the ISM for the organisation you selected, what mitigations would you have put in place to stop any reoccurrences?**

If tasked as the Information Security Manager (ISM), I would enforce a strict Defense-in-Depth strategic architecture:

1. **Automated Vulnerability and Patch Lifecycle Management:** Establish strict SLAs where any critical-rated CVE (such as Apache Struts RCE) must be patched or mitigated within 48 to 72 hours, backed by automated enforcement tools rather than manual email reliance.
2. **Certificate Lifecycle Automation:** Implement automated monitoring and deployment tools (such as Venafi or Let's Encrypt) to ensure SSL/TLS certificates used for deep packet inspection never expire silently, preserving continuous network monitoring visibility.
3. **Strict Least-Privilege Segmentation:** Isolate web application portals from the core backend database infrastructure, ensuring that even if a front-end server is breached, attackers cannot cross-segment to query the entire customer database.

### **References:**

* **Swinhoe, D. (2020)** *The 15 Biggest Data Breaches of the 21st Century*. CSO Online.
* **UK Information Commissioner's Office (ICO) (2018)** *Monetary Penalty Notice: Equifax Ltd*. available at: [https://ico.org.uk](https://ico.org.uk).
* **US Government Accountability Office (GAO) (2018)** *Data Protection: Actions Taken by Equifax and Federal Agencies after the 2017 Breach*. GAO-18-559. Washington, D.C.
