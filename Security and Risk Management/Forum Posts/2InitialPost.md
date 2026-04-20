### Critique of CVSS Characteristics

Wunder et al. (2024) offer a pointed critique of the Common Vulnerability Scoring System (CVSS), specifically targeting its claims of objectivity and its formulaic "black box" nature. The authors argue that while CVSS is marketed as a standard for technical severity, it suffers from significant inter-rater inconsistency. Their study revealed that different analysts often assign different values to the same Base Score metrics—such as "Attack Vector" or "Scope"—leading to disparate scores for identical vulnerabilities (Wunder et al., 2024). Furthermore, they criticise the mathematical weightings within the CVSS formula, noting that the "magic numbers" used to calculate the final score lack a transparent, empirical basis and often fail to reflect the actual risk perceived by security professionals.

I agree with this critique. While the transition to CVSS v4.0 attempted to address contextual gaps, the fundamental issue remains: CVSS measures severity (the technical potential for harm) rather than risk (the likelihood and actual impact on a specific business). As argued by Allodi and Massacci (2017), high CVSS scores do not strongly correlate with actual exploitability in the wild. Relying on a technical score that ignores the threat landscape leads to "vulnerability fatigue," where security teams prioritise theoretical risks over active threats simply because of a high numerical value.

### Proposed Alternative: Stakeholder-Specific Vulnerability Categorisation (SSVC)

Among the alternatives discussed, the Stakeholder-Specific Vulnerability Categorisation (SSVC) should replace (or at least supersede) CVSS in decision-making workflows. Developed by Carnegie Mellon University’s SEI, SSVC moves away from a singular numerical score in favor of a decision-tree model (Spring et al., 2020).

SSVC is superior because it incorporates contextual relevance and exploit status as primary drivers. Unlike CVSS, which provides a static score, SSVC results in actionable outcomes: *Defer, Scheduled, Out-of-Cycle,* or *Immediate*. This methodology forces organisations to consider "Mission Impact" and "System Exposure," ensuring that a vulnerability in a public-facing web server is treated with more urgency than the same vulnerability in an isolated legacy system. By focusing on qualitative decision-making logic rather than a pseudo-objective numerical value, SSVC provides a more mature framework for modern risk management (Wunder et al., 2024).

### References

* Allodi, L. and Massacci, F. (2017) ‘A Five-Year Study of Vulnerability Cost: Do Security Experts Have It Right?’, *IEEE Transactions on Dependable and Secure Computing*, 14(5), pp. 516–528.
* Spring, J.M., Hatleback, E., Householder, A.D., Manion, A. and Shick, D. (2020) *Prioritizing Vulnerability Response: A Stakeholder-Specific Vulnerability Categorization*. Software Engineering Institute, Carnegie Mellon University.
* Wunder, J., Kurtz, A., Eichenmüller, C., Gassmann, F. and Benenson, Z. (2024) ‘Shedding Light on CVSS Scoring Inconsistencies: A User-Centric Study on Evaluating Widespread Security Vulnerabilities’, in *2024 IEEE Symposium on Security and Privacy (SP)*. San Francisco, CA, USA: IEEE, pp. 1102–1121. doi: 10.1109/SP54263.2024.00058.
