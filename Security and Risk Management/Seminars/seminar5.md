### **Case Study: Bank Details Sent via WhatsApp (Financial Sector)**

### **1. What is the specific aspect of GDPR that your case study addresses?**
This case addresses Article 5(1)(f) of the GDPR, which outlines the principle of "Integrity and Confidentiality." Under this principle, personal data must be processed in a manner that ensures appropriate security, including protection against unauthorised or unlawful processing and against accidental loss, destruction, or damage, using appropriate technical or organisational measures. Specifically, it highlights:
* **Unauthorised Disclosure:** Sending sensitive financial information (IBAN and BIC) via an unapproved, non-secure personal messaging platform.
* **Human Error:** The failure of an employee to follow established data-handling protocols.
* **Accuracy (Article 5(1)(d)):** The employee accidentally sent the details of the *wrong* customer to the requester.


### **2. How was it resolved?**
The issue was resolved through a **mandatory breach notification** and subsequent investigation by the DPC.
* **Self-Reporting:** The financial institution notified the DPC once the error was discovered.
* **Containment:** The organisation reached out to the unintended recipient to request the deletion of the message/image.
* **Corrective Action:** The DPC noted that while the organisation had "approved practices" in place, they were not strictly enforced. The bank was required to update its staff training modules and reinforce the prohibition of using personal devices/unauthorised apps for transmitting customer data.
* **Outcome:** The DPC typically issues a **reprimand** in such cases if it is a first-time human error, but they mandated a formal review of the company's technical and organisational security measures to ensure compliance with the "Accountability" principle.


### **3. If this was your organisation, what steps would you take as an Information Security Manager to mitigate the issue?**
As an Information Security Manager, I would implement a multi-layered mitigation strategy focusing on People, Process, and Technology:
**A. Technical Measures (Preventative)**
* **Mobile Device Management (MDM):** Implement MDM software on all company-issued devices to block the installation of unapproved messaging apps (like WhatsApp) for business use.
* **Data Loss Prevention (DLP):** Deploy DLP tools that scan outgoing communications for patterns like IBANs or BIC codes and block them if they are being sent via unauthorised channels.
* **Secure Portal:** Transition all customer data requests to a secure, encrypted "Customer Portal" where users log in to view their details, eliminating the need for staff to "send" data manually.

**B. Process & Policy (Organisational)**
* **Clean Desk & Device Policy:** Strictly forbid the use of personal mobile phones in areas where sensitive customer data is handled.
* **Standard Operating Procedures (SOPs):** Create a rigid "Verification Workflow" where any disclosure of financial data must be double-checked by a second staff member (Four-Eyes Principle) before being sent.

**C. Training & Culture (People)**
* **Role-Based GDPR Training:** Conduct specific training for front-line staff on the dangers of "convenience-based" security shortcuts. I would use this specific case study as a "lesson learned" to show how a small "favor" for a known customer can lead to a legal breach.
* **Sanction Policy:** Clearly communicate the internal disciplinary consequences for bypassing security protocols to act as a deterrent.
