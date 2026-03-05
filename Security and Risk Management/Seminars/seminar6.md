### **1. Applicable Standards for Pampered Pets**
| Standard | Applicability to Pampered Pets |
| --- | --- |
| **GDPR (ICO)** | High. Currently, they handle local customer emails and orders. Post-transformation, they will process international data. They must protect "Personal Data" (names, addresses, pet details) of EU/UK citizens. |
| **PCI-DSS** | Critical. They currently take payments in-store (likely via a card terminal). Digitalisation means online payments, putting their "Wireless Gateway" and website directly in scope for PCI-DSS compliance. |
| **Appendix D/G (Risk)** | Essential. Since they are using an "old, networked computer" and a shared wireless hub for staff smartphones, they currently violate basic HMG cybersecurity hygiene. |
| **HIPAA** | Low/None. Unless "Pampered Pets" begins offering veterinary insurance or medical services involving US-regulated health data, HIPAA is likely not applicable. |


### **2. Evaluation & Verification**
**The "Old Computer" & Shared Hub Problem:**
The current setup is a major security hole. Harry’s old computer likely lacks modern security patches, and the staff using the same Wi-Fi for personal apps creates a "bridge" for malware to jump to the sales computer.

**How to check if standards are being met:**
* **Vulnerability Assessment:** Use a tool to scan the "old networked computer" for unpatched vulnerabilities (a key requirement of HMG Guidelines).
* **PCI-DSS SAQ-A:** Since they are moving online, I would check if their web developer is using an "iFrame" or "Redirect" for payments. If the card numbers ever touch Pampered Pets' own server, the compliance cost skyrockets.
* **Data Audit:** Review how Alice and Cathy store the email orders. If they are sitting in an unencrypted inbox on a shared computer, they are failing GDPR "Integrity and Confidentiality" requirements.


### **3. Recommendations for the Digital Transformation**
1. **Network Segmentation (Immediate):** Split the wireless hub into three separate VLANs: one for the Front Desk/Payments, one for Warehouse/Admin, and a "Guest" one for Staff Smartphones. This aligns with Appendix D controls.
2. **Hardware Lifecycle Management:** Replace Harry’s "old, networked computer." Under HMG Cybersecurity Guidelines, unsupported operating systems (like Windows 7 or older) are a critical failure.
3. **Cloud-Based ERP:** Instead of a local spreadsheet, move to a secure cloud platform (like Shopify or Xero). This shifts the burden of physical security and high-level encryption to the service provider.
4. **Supply Chain Risk Assessment:** If they move to an international supply chain (to save 24%), they lose the "10-minute drive" resilience. They must implement Third-Party Risk Management to ensure international vendors also comply with data standards.


### **4. Addressing the Assumptions**
* **Assumption 1 (Payment Method):** I assume that with Orla’s funding, the business will use a reputable payment processor (like Stripe) rather than trying to build their own payment database.
* **Assumption 2 (Data Sensitivity):** I assume "Pampered Pets" does not store clinical veterinary records, which would require higher data protection tiers similar to those found in the HIPAA or ISO 27001 frameworks.
* **Assumption 3 (The "Orla" Factor):** I assume that Orla’s "international reach" includes the EU. If it includes the USA, they must also look into CCPA (California Consumer Privacy Act) in addition to GDPR.
