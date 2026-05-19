# **PART 1: WIKI CONTRIBUTION**

## **Section 1: Results Compilation**

**Contributor:** Molly Fraser

**Target Website:** hack-yourself-first.com (Supercar Showdown)

**Testing Environment:** Kali Linux Virtual Machine (via UTM on macOS host)

* **What Operating System does the website utilise?** The backend target infrastructure is hosted on Windows Server (indicated by specific ASP.NET and IIS ecosystem footprints). However, the public-facing OS is masked by Cloudflare’s customised Linux-based edge architecture.
* **What web server software is it running?** Active header fingerprinting and sAP scans disclosed that the origin server runs Microsoft-IIS/10.0 (or a legacy equivalent handling ASP.NET execution pipelines).
* **Is it running a CMS (WordPress, Drupal, etc.)?** No. Automated enumeration and spidering confirm this is a custom-built, legacy ASP.NET application (`.aspx` routing structures) rather than a standardised Content Management System.
* **What protection does it have (CDN, Proxy, Firewall)?** The site implements a robust layer-7 external security posture utilising Cloudflare CDN/Reverse Proxy and a Web Application Firewall (WAF). This drops ICMP packets and intercepts aggressive layer-4 scans.
* **Where is it hosted?** The primary domain public IP mapping resolves to Cloudflare's network layer (172.67.156.87 and 104.21.89.41**), with the backend application code operating inside the Microsoft Azure cloud ecosystem.
* **Does it have any open ports? Which did you expect to be open?** Nmap port mapping showed that only ports 80 (HTTP) and 443 (HTTPS) are exposed to the public internet, which is the expected secure baseline configuration for an e-commerce/web platform to facilitate standard TLS/SSL traffic.
* **Does the site have any known vulnerabilities?** Yes, several critical application-layer vulnerabilities were validated:
* **Stored/Reflected Injection Flaws (CWE-79 & CWE-89):** Input fields accept raw database syntax and JavaScript payloads without sanitisation.
* **Broken Access Control (CWE-352):** Form actions (such as account registration) do not utilise unique Anti-CSRF cryptographic tokens.
* **Security Misconfiguration (CWE-200):** Leakage of explicit infrastructure version components in HTTP response fields.


* **What versions of software is it using? Are these patched so that they are up to date?** The site leaks exposure of ASP.NET version 4.0.30319. Additionally, front-end scanning flagged an outdated, unpatched version of the client-side jQuery library, leaving the application layer vulnerable to known public exploits.


## **Section 2: Wiki FAQ Input**

**Q: I ran an aggressive Nmap scan or OS detection flag (`-O`), but the output only shows Cloudflare or fails completely. How do I get past this to fingerprint the real origin server?**

**A (Molly Fraser):** This happens because Cloudflare acts as a reverse proxy, meaning your Kali tools are scanning Cloudflare's edge servers rather than the actual host where the website sits. To bypass this limitations silently, look at Layer-7 Header Disclosure instead of Layer-4 TCP/IP stacks. When running an automated baseline tool (like OWASP ZAP) or inspecting the web headers directly via your browser's Developer Tools, you will notice the application returns specific parameters such as `X-AspNet-Version: 4.0.30319` and `Server: Microsoft-IIS/10.0`. This tells us the backend architecture is Microsoft-based, even though Nmap insists the IP points to Cloudflare!

---

# **PART 2: PORTFOLIO REFLECTION**

**Did you have any issues or challenges with the scans?** The defining challenge during this collaborative task was traversing the external shielding of the target. Initially, active port scanning and aggressive infrastructure scans using Nessus or Nmap yielded limited, highly generic metrics because Cloudflare’s Web Application Firewall (WAF) aggressively filters, rate-limits, and alters incoming probes to disguise the underlying environment.

**How did you overcome them?** I overcame this obstacle by pivoting from infrastructure-centric network exploration (Layer 3/4) to dynamic application security testing (Layer 7). Instead of depending blindly on Nmap to deduce the OS environment, I utilised OWASP ZAP to execute contextual web queries. By meticulously inspecting the HTTP response headers leaked by the verbose server configurations, I isolated explicit technical footprints (`X-Powered-By: ASP.NET`) that clearly confirmed the server's backend properties without having to strip away the proxy's network shield.

**How will they affect your final report?** These challenges significantly enhance the strategic design of my final vulnerability report. They demonstrate that network-level defenses alone are completely insufficient if the application layer code itself is poorly configured. This experience highlights the critical need to structure recommendations into two tiers: immediate server-level hardening (such as disabling verbose disclosure headers) and systemic source-code adjustments (such as sanitising input variables and embedding Anti-CSRF tokens into forms). This insight ensures my final assessment balances perimeter network controls with deep secure-coding lifecycles.
