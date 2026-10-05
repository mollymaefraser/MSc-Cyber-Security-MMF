from capstone import *

advisories = [
    Advisory("badlib", "1.0.0", Severity.CRITICAL, "Remote code execution"),
    Advisory("midlib", "2.1.0", Severity.MEDIUM, "Information disclosure"),
]
auth = ApiKeyAuthenticator()
key = auth.issue_key()
log = []
scanner = build_default_scanner(advisories, log, auth)
report = scanner.scan(key, "requirements", "safelib==3.0.0\nmidlib==2.1.0\nbadlib==1.0.0\n")
renderer = TextRenderer()
report.accept(renderer)
print("\n".join(renderer.lines))
