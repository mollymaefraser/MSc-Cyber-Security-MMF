(Apologies. My context here is limited as I could only respond to one peer, and only had one peer response.)

This discussion focused on the systemic limitations of the Common Vulnerability Scoring System (CVSS) and the necessity of transitioning toward more decision-oriented frameworks like Stakeholder-Specific Vulnerability Categorisation (SSVC). Through my initial post and subsequent engagement with a peer, it became evident that the primary critique of CVSS (as highlighted by Wunder et al. (2024)) is its inherent subjectivity and lack of organisational context.

A key theme that emerged from our exchange was the inter-rater inconsistency found in CVSS scoring. My initial post highlighted how metrics like "Scope" and "Attack Vector" are prone to human error and interpretation, a point my peer reinforced by noting that such inconsistencies directly undermine an organisation's ability to prioritise fixes (Wunder et al., 2024). We reached a consensus that while CVSS acts as a useful "thermometer" for technical severity, it fails as a "triage" tool because it does not account for the real-world risk environment (Allodi and Massacci, 2017).

In response to these failings, the discussion shifted toward preventative measures and alternative frameworks. I proposed that organisations could mitigate CVSS subjectivity by implementing internal scoring rubrics or "gold standards" tailored to their specific architecture. My peer and I both identified SSVC as the most viable successor to CVSS for prioritisation. We agreed that SSVC’s decision-tree model (Spring et al., 2021) is superior because it replaces a static numerical score with actionable outcomes (e.g., Immediate vs. Scheduled). This move from "technical severity" to "mission-driven risk" is essential for modern cybersecurity, ensuring that resources are allocated based on actual exposure rather than theoretical vulnerability.

In conclusion, the units and this discussion emphasise that technical scores are only one piece of the puzzle. Effective vulnerability management requires a blend of standardised metrics and context-specific logic to turn raw data into strategic action.

References
Allodi, L. and Massacci, F. (2017) ‘A Five-Year Study of Vulnerability Cost: Do Security Experts Have It Right?’, IEEE Transactions on Dependable and Secure Computing, 14(5), pp. 516–528.

Spring, J.M., Hatleback, E., Householder, A.D., Manion, A. and Shick, D. (2021) Prioritizing Vulnerability Response: A Stakeholder-Specific Vulnerability Categorization (Version 2.0). Software Engineering Institute, Carnegie Mellon University.

Wunder, J., Kurtz, A., Eichenmüller, C., Gassmann, F. and Benenson, Z. (2024) ‘Shedding Light on CVSS Scoring Inconsistencies: A User-Centric Study on Evaluating Widespread Security Vulnerabilities’, in 2024 IEEE Symposium on Security and Privacy (SP). San Francisco, CA, USA: IEEE, pp. 1102–1121.

