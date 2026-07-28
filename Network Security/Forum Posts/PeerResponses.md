1.
Hi Ahmed,

I really enjoyed reading your analysis of the "fully digital enterprise." You made an excellent point regarding how digital transformation reshapes value creation while simultaneously expanding the attack surface.  

I particularly resonated with your mention of SMEs transitioning from "bricks and mortar". In my own recent practical audit of a web application (Supercar Showdown for our assignment), I observed exactly what you described: a legacy-style application struggling with modern security requirements like Anti-CSRF tokens and robust input validation. It’s easy for these organisations to adopt the "front-end" of a digital enterprise (like e-commerce) while neglecting the "back-end" security configurations that Doroiman and Sîrghi (2024) warn about.  

Your point about the digital divide and lack of specialised skills in SMEs is also crucial. Do you think that for these smaller enterprises, a "Cloud-First" approach (relying on the security of providers like Azure or AWS) is enough to bridge that skills gap, or does it simply introduce new risks like the "security misconfigurations" you mentioned? 

2.

Hi Asma,

I found your discussion on the dissolution of the boundary between IT and business strategy particularly insightful, especially your reference to van Gils and Proper (2018) regarding the "Achilles heel" of human behaviour. It’s a point that often gets lost in high-level technical discussions but is vital for operational resilience.

In my recent technical analysis of a web application for our first assignment , I saw firsthand how this "Achilles heel" manifests in the technical design. For instance, I identified CWE-79 (Cross-Site Scripting) and CWE-352 (CSRF) vulnerabilities that specifically rely on exploiting human interaction with a browser to execute unauthorised commands. While the enterprise might have a robust perimeter, as you noted, the human element, combined with a lack of input sanitisation, can bypass those external shields.

I was also interested in your point about supply chain vulnerabilities and third-party cascading risks. Given that many SMEs now rely on Cloudflare or Azure for their infrastructure (as I noted in my own audit), do you think this centralisation of services actually helps SMEs by "outsourcing" their security maturity, or does it simply create a more dangerous single point of failure if one of those major providers is compromised?



References

Doroiman, M.M. and Sîrghi, N. (2024) ‘The digital enterprise landscape: How DESI metrics shape economic growth in the EU’, Oradea Journal of Business and Economics, 9(2), pp. 36–46.

Kabanda, S., Tanner, M. and Kent, C. (2018) ‘Exploring SME cybersecurity practices in developing countries’, Journal of Organizational Computing and Electronic Commerce, 28(3), pp. 269–282.

MITRE (2026) CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting'). Available at: https://cwe.mitre.org/data/definitions/79.html.

MITRE (2026) CWE-352: Cross-Site Request Forgery (CSRF). Available at: https://cwe.mitre.org/data/definitions/352.html.

Van Gils, B. and Proper, H.A. (2018) ‘Enterprise Modelling in the Age of Digital Transformation’, in Buchmann, R.A., Karagiannis, D. and Kirikova, M. (eds.) The Practice of Enterprise Modeling. Cham: Springer, pp. 257–273.


