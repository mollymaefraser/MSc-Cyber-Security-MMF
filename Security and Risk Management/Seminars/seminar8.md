### 1. Challenges in Modelling Social Engineering Threats
The primary challenge in modeling Social Engineering Threats (SETs) is the human element. Unlike technical vulnerabilities (like a bug in code), SE exploits human psychology, which is:
* Unpredictable: Responses vary based on individual personality, mood, and environment.
* Multidimensional: Threats often involve a mix of physical, social, and technical channels.
* Qualitative: "Trust" and "fear" are hard to measure with traditional binary security metrics.

The Study’s Approach:
To address this, the authors use a hybrid modeling approach. They break down complex human interactions into logical steps (Attack Trees) and then apply Markov Chains to account for the stochastic (random) nature of human decision-making over time.


### 2. Persuasion Principles and Modalities
The success of an SET rarely depends on a single message; it depends on how that message is delivered (modalities) and why it triggers a response (persuasion principles).
* Persuasion Principles: Based on Cialdini’s work (e.g., Authority, Urgency, Scarcity, Liking), these are the psychological levers used to bypass critical thinking.
* Modalities: These are the communication channels, such as email (phishing), phone (vishing), or physical presence (tailgating).

Importance of Systematic Analysis:
Analysing these systematically allows organisations to identify which specific "triggers" their employees are most vulnerable to. Instead of broad training, companies can tailor defenses based on the most statistically successful persuasion-modality combinations identified in the model.


### 3. Attack Trees vs. Markov Chain Models
The paper uses these two tools in tandem to quantify risk:

| Model | Role in the Study |
| :--- | :--- |
| Attack Tree | Used to decompose a high-level goal (e.g., "Steal Credentials") into sub-tasks. It helps identify all possible paths an attacker could take to achieve the Attack Occurrence Probability (AOP). |
| Markov Chain | Used to model the transitions between states of an attack. It accounts for the probability that a victim moves from "Receiving an email" to "Clicking a link." This determines the Attack Success Probability (ASP). |

By combining them, the study calculates the Total Success Probability, allowing security professionals to see not just *how* an attack happens, but how likely it is to reach completion.


### 4. Supporting Policy Frameworks
The findings of this study provide a "data-backed" foundation for organisational policy:
* Evidence-Based Training: Rather than generic "don't click links" posters, policies can mandate simulation training focused on the high-probability paths identified by the Markov model.
* Resource Allocation: If the model shows that "Urgency" via "Vishing" has the highest ASP, the IT policy can prioritise implementing specific voice-authentication technologies or stricter phone-handling protocols.
* Standardised Risk Assessment: It provides a mathematical framework that can be integrated into broader ISO/IEC 27001 risk management standards, making SE threats a formal part of the technical audit process.
