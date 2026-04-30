### Vulnerability Audit Baseline: hack-yourself-first.com

Target Description: A live web application designed to demonstrate common security risks to developers. It mimics a supercar gallery and showroom.

| Vulnerability Category | Potential/Identified Flaw | Reference (CVE/OWASP) | Technical Impact |
| :--- | :--- | :--- | :--- |
| Injection | SQL Injection (SQLi) via search bars or URL parameters (e.g., `?MakeId=1`). | OWASP A03:2021 | Allows unauthorised database access, enabling attackers to dump user credentials and "supercar" data. |
| Cross-Site Scripting (XSS) | Reflected XSS in search results or profile fields. | OWASP A03:2021 | Attackers can inject malicious scripts to steal session cookies or hijack user accounts. |
| Broken Access Control | Insecure Direct Object References (IDOR). | OWASP A01:2021 | Changing a numeric ID in the URL allows a user to view another user's private profile or "garage." |
| Cryptographic Failures | Lack of HSTS or sensitive data sent over HTTP. | OWASP A02:2021 | Credentials can be intercepted via Man-in-the-Middle (MitM) attacks if the transport layer isn't secure. |
| Security Misconfiguration | Verbose error messages revealing server stack info. | OWASP A05:2021 | Discloses ASP.NET versions or database structure, aiding attackers in crafting specific exploits. |
| Authentication Failures | Weak password policies and lack of brute-force protection. | OWASP A07:2021 | Simplifies account takeover via credential stuffing or dictionary attacks. |

Audit Methodology: 
1. National Vulnerability Database (NVD): Searched for "ASafaWeb" (Hunt’s previous tool used for this site) and general ASP.NET vulnerabilities.
2. Literature Search: Reviewed Troy Hunt’s Hack Yourself First course documentation which outlines the intentional flaws integrated into the site.
3. Audit Baseline: Cross-referenced findings with the OWASP Top 10 (2021/2024 updates) to categorise risks.


### Reflection (For E-Portfolio)

Did you have any issues or challenges with the literature search/audit on software sites and the national vulnerabilities database?
One primary challenge was that since hack-yourself-first.com is a training tool, it does not have a single "CVE" code assigned to the site as a whole. Vulnerabilities are usually logged in the NVD for specific software versions (e.g., Windows Server 2019), but not for custom-coded "lab" websites. This made it difficult to find a single official "report" on the National Vulnerabilities Database.

How did you overcome them?
I overcame this by shifting the search strategy from "site-specific CVEs" to "vulnerability patterns." Instead of searching for the URL in the NVD, I searched for the technology stack it uses (ASP.NET) and used the author's own academic/training literature (Troy Hunt’s blog and Pluralsight course) to verify the specific flaws he intentionally built. I then mapped these manually to the OWASP Top 10 categories to create a professional baseline.

How will they affect your final report?
These findings will provide the technical "evidence" section of my final report. By having a baseline of vulnerabilities, I can now recommend specific mitigation strategies (like parameterised queries for SQLi or Content Security Policies for XSS). It has taught me that vulnerability auditing is not just about automated tools; it requires synthesising information from multiple qualitative sources (blogs, manuals) alongside quantitative databases (NVD).
