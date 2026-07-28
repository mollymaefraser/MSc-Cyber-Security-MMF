# Cyberattack Investigation Report

This report analyses six prevalent cyberattack vectors, exploring their historical origins, technical execution, and the layered defense mechanisms required to mitigate them in modern digital environments.


## 1. Phishing
Origin & History
Phishing first emerged in the mid-1990s, notably targeting America Online (AOL) users to steal credentials. A landmark case was the 2016 Democratic National Committee (DNC) email leak, where a spear-phishing campaign led to the compromise of sensitive political data (Toledano, 2024).

How the Attack Works
Phishing exploits the "human element" via social engineering. Attackers masquerade as a trusted entity (banks, IT support) through email or SMS to trick users into clicking malicious links or downloading attachments. It exploits vulnerabilities in human psychology and the lack of robust email authentication.

Best Practice Mitigation Strategies
*   Multi-Factor Authentication (MFA): Ensures that even if credentials are stolen, the attacker cannot gain access without a second factor.
*   Security Awareness Training: Educating employees to recognise suspicious URLs and "urgent" linguistic triggers.

Modern Protection Tools & Techniques
*   AI-Enhanced Email Filtering: Tools like Darktrace or Mimecast use AI to detect linguistic anomalies that bypass traditional filters.
*   DMARC/SPF/DKIM: Standard protocols used to verify sender identity and prevent domain spoofing.


## 2. SQL Injection (SQLi)
Origin & History
SQLi was first documented in 1998 by Jeff Forristal. One of the most significant incidents occurred in 2008 when Heartland Payment Systems suffered a breach via SQLi, leading to the theft of over 130 million credit card numbers.

How the Attack Works
Attackers insert malicious SQL code into input fields (like login forms). If the application does not properly sanitise inputs, the database executes the malicious command, allowing unauthorised data access or deletion. It exploits poorly coded web applications that lack input validation.

Best Practice Mitigation Strategies
*   Prepared Statements (Parameterised Queries): Forces the database to treat input as data rather than executable code.
*   Principle of Least Privilege: Ensuring the database user account has the minimum permissions necessary.

Modern Protection Tools & Techniques
*   Web Application Firewalls (WAF): Solutions like Cloudflare or Akamai filter out known SQLi patterns at the network edge.
*   DAST/SAST Tools: Automated scanners (e.g., Burp Suite, Snyk) that identify code vulnerabilities during the development lifecycle.


## 3. Ransomware
Origin & History
The first known ransomware was the 1989 "AIDS Trojan," distributed via floppy disks. However, modern ransomware exploded with WannaCry (2017), which utilised the EternalBlue exploit to encrypt hundreds of thousands of computers globally, including the UK’s NHS (Toledano, 2024).

How the Attack Works
Ransomware encrypts a victim's files and demands payment (usually in cryptocurrency) for the decryption key. It typically enters a network via phishing or RDP (Remote Desktop Protocol) vulnerabilities.

Best Practice Mitigation Strategies
*   Offline Backups (3-2-1 Rule): Maintaining backups that are not connected to the primary network to prevent them from being encrypted.
*   Patch Management: Regularly updating software to close vulnerabilities (like EternalBlue) used for propagation.

Modern Protection Tools & Techniques
*   Endpoint Detection and Response (EDR): Tools like CrowdStrike use behavioral analysis to kill processes that begin mass-encrypting files.
*   Zero Trust Architecture: Segmenting networks so an infection in one area cannot "move laterally" to critical servers.


## 4. Denial-of-Service (DoS / DDoS)
Origin & History
Early DoS attacks appeared in the late 80s, but the 2016 Dyn attack remains a watershed moment. It used the Mirai botnet—comprised of compromised IoT devices—to take down major sites like Twitter and Netflix by overwhelming DNS servers.

How the Attack Works
An attacker floods a server or network with excessive traffic, consuming its bandwidth or CPU resources until it crashes. It exploits the finite capacity of network resources and the lack of authentication in protocols like UDP.

Best Practice Mitigation Strategies
*   Rate Limiting: Restricting the number of requests a single IP can make within a specific timeframe.
*   Redundancy and Load Balancing: Distributing traffic across multiple servers to prevent a single point of failure.

Modern Protection Tools & Techniques
*   Anycast Network Routing: Distributing the attack traffic across a global network of "scrubbing centers" (e.g., AWS Shield).
*   Intrusion Prevention Systems (IPS): Hardware or software that identifies and blocks traffic patterns associated with flood attacks.


## 5. Man-in-the-Middle (MitM)
Origin & History
MitM attacks are as old as telecommunications, but in the cyber realm, they became prominent with the rise of unencrypted Wi-Fi. A notable modern example involved the Equifax mobile app (2017), which failed to properly validate SSL certificates, potentially allowing MitM interceptions.

How the Attack Works
The attacker secretly relays and possibly alters communications between two parties who believe they are directly communicating. This is often achieved via ARP spoofing or DNS hijacking. It exploits a lack of mutual authentication and encryption.

Best Practice Mitigation Strategies
*   Use of HTTPS/TLS: Ensuring all data in transit is encrypted so that even if intercepted, it cannot be read.
*   VPN Usage: Creating an encrypted tunnel for data, especially when using public or untrusted networks.

Modern Protection Tools & Techniques
*   HSTS (HTTP Strict Transport Security): A policy mechanism that forces browsers to only communicate with websites using secure HTTPS connections.
*   Certificate Pinning: An advanced technique where an application is hardcoded to trust only a specific SSL certificate.


## 6. Cross-Site Scripting (XSS)
Origin & History
XSS was identified by Microsoft engineers in late 1999. The Samy Worm (2005) is the most famous incident; it exploited XSS on MySpace to add over a million friends to the creator's profile in just 20 hours, demonstrating the viral potential of the attack.

How the Attack Works
Attackers inject malicious scripts into trusted websites. When a victim visits the site, the script executes in their browser, potentially stealing session cookies or redirecting users. It exploits the browser's trust in the content delivered by the server.

Best Practice Mitigation Strategies
*   Output Encoding: Converting special characters (like `<` and `>`) into a safe, non-executable format before rendering them in the browser.
*   Input Validation: Restricting the types of data users can submit to forms.

Modern Protection Tools & Techniques
*   Content Security Policy (CSP): A modern security layer that tells the browser which sources of scripts are trusted, effectively blocking unauthorised malicious scripts.
*   Automatic Context-Aware Encoding: Modern web frameworks (like React or Angular) have built-in protections that automatically encode data to prevent XSS.

### References
Antelada Toledano, S. (2024) *Critical Infrastructure Security: Cybersecurity Lessons Learned from Real-World Breaches*. 1st edn. Birmingham: Packt Publishing.