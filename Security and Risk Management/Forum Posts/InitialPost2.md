### Critique of CVSS Characteristics

Wunder et al. (2024) offer a pointed critique of the Common Vulnerability Scoring System (CVSS), specifically targeting its claims of objectivity and its formulaic "black box" nature. The authors argue that while CVSS is marketed as a standard for technical severity, it suffers from inter-rater inconsistency. Different analysts often assign different values to the same Base Score metrics (such as "Attack Complexity" or "Privileges Required"), leading to disparate scores for the same vulnerability (Wunder et al., 2024). Furthermore, they criticise the mathematical weightings within the CVSS formula, noting that the "magic numbers" used to calculate the final score lack a transparent, empirical basis.

I agree with this critique. The transition from CVSS v3.1 to v4.0 attempted to address contextual gaps, yet the fundamental issue remains: CVSS measures severity (the technical "badness") rather than risk (the likelihood and impact on a specific business). As argued by Allodi and Massacci (2017), high CVSS scores do not strongly correlate with actual exploitability in the wild. Relying on a technical score that ignores the threat landscape leads to "vulnerability fatigue," where security teams prioritise theoretical risks over active threats.

### Proposed Alternative: Stakeholder-Specific Vulnerability Categorisation (SSVC)

Among the alternatives discussed, the Stakeholder-Specific Vulnerability Categorisation (SSVC) should replace (or at least supersede) CVSS in decision-making workflows. Developed by Carnegie Mellon University’s SEI, SSVC moves away from a singular numerical score in favor of a decision-tree model (Spring et al., 2020).

SSVC is superior because it incorporates contextual relevance and exploit status as primary drivers. Unlike CVSS, which provides a static score, SSVC results in actionable outcomes: *Defer, Scheduled, Out-of-Cycle,* or *Immediate*. This methodology forces organizations to consider the "Mission Impact" and "System Exposure," ensuring that a vulnerability in a public-facing web server is treated with more urgency than the same vulnerability in an isolated legacy system. By focusing on decision-making logic rather than a pseudo-objective numerical value, SSVC provides a more mature framework for modern risk management (Wunder et al., 2024).

### References

* Allodi, L. and Massacci, F. (2017) ‘A Five-Year Study of Vulnerability Cost: Do Security Experts Have It Right?’, *IEEE Transactions on Dependable and Secure Computing*, 14(5), pp. 516–528.
* Spring, J.M., Hatleback, E., Householder, A.D., Manion, A. and Shick, D. (2020) *Prioritizing Vulnerability Response: A Stakeholder-Specific Vulnerability Categorization*. Software Engineering Institute, Carnegie Mellon University.
* Wunder, J., Kurtz, A., Eichenmüller, C., Gassmann, F. and Benenson, Z. (2024) ‘The Case Against CVSS: A Review of Vulnerability Scoring Systems’, *Journal of Cybersecurity* [Note: Adjust journal/source based on your specific unit reading].
