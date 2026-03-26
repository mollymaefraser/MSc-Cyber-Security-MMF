Hi Elvira,

I found your analysis of the inter-rater inconsistency highlighted by Wunder et al. (2024) particularly insightful. Your point regarding the same professional potentially scoring the same vulnerability differently over time underscores the inherent subjectivity in CVSS, which is often masked by its numerical output. You rightly identified that metrics like Scope and User Interaction are often the primary culprits of this variance.

I also agree with your selection of Stakeholder-Specific Vulnerability Categorisation (SSVC). While CVSS acts as a "one-size-fits-all" thermometer, SSVC functions more like a triage protocol. To build on your point about decision-making, the use of a decision-tree model helps eliminate the "magic number" ambiguity that Howland (2023) criticises.

In terms of preventing the inconsistencies you mentioned, I believe organisations should implement scoring rubrics or "internal gold standards" for specific system architectures. By pre-defining what "Network" or "Physical" access looks like within the specific company infrastructure, firms can reduce the subjectivity of the Attack Vector metric. Additionally, integrating automated threat intelligence feeds to verify the "Exploit Status" (a key component of SSVC) can prevent reliance on outdated or subjective manual assessments (Spring et al., 2021).

Moving toward a context-aware model like SSVC not only improves consistency but ensures that resources are directed toward vulnerabilities that actually pose a credible threat to the organisation's mission.

References:

Howland, H. (2023) ‘CVSS: Ubiquitous and Broken’, Digital Threats: Research and Practice, 4(1). doi: 10.1145/3491263.

Spring, J.M., Hatleback, E., Householder, A.D., Manion, A. and Shick, D. (2021) Prioritizing Vulnerability Response: A Stakeholder-Specific Vulnerability Categorization (Version 2.0). Software Engineering Institute, Carnegie Mellon University.

Wunder, J., Kurtz, A., Eichenmüller, C., Gassmann, F. and Benenson, Z. (2024) ‘Shedding Light on CVSS Scoring Inconsistencies: A User-Centric Study on Evaluating Widespread Security Vulnerabilities’, in 2024 IEEE Symposium on Security and Privacy (SP). San Francisco, CA, USA: IEEE, pp. 1102–1121.
