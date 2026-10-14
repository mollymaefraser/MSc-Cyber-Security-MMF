"""Deliberately breaks key security rules, one at a time, and checks the test suite notices.

Each mutation edits a source file, runs the whole suite, then restores the file.
Run from the project root: python3 mutation_check.py
"""

import pathlib
import subprocess

MUTATIONS = [
    ("elearn/users.py", "            self._throttle.check(key)  # checked first, so a locked out client costs no hashing work\n",
     "            pass\n", "Remove lockout check"),
    ("elearn/users.py", "        self._sessions.revoke_all_for_user(user_id)  # old sessions may belong to an attacker\n",
     "", "Keep sessions after password change"),
    ("elearn/users.py", "        require_role(actor, Role.ADMIN)\n", "", "Let anyone change roles"),
    ("elearn/users.py", "            if entry is None or entry[1] <= self._clock():", "            if entry is None:",
     "Sessions never expire"),
    ("elearn/users.py", "        stored = found[1] if found else self._dummy_hash",
     "        stored = found[1] if found else 'scrypt$1024$00$00'",
     "Skip dummy hash for unknown users (timing defence, not unit testable)"),
    ("elearn/enrolment.py", 'if taken >= row["capacity"]:', 'if taken > row["capacity"]:', "Off-by-one on capacity"),
    ("elearn/courses.py", "if course is None or not (course.published or self.can_manage(actor, course)):",
     "if course is None:", "Show drafts to everyone"),
    ("elearn/courses.py", 'replace("%", "\\\\%")', 'replace("%", "%")', "Do not escape LIKE wildcards"),
    ("elearn/controller.py", 'return Response(500, {"error": "Internal server error"})',
     'return Response(500, {"error": str(exc)})', "Leak internal error text"),
    ("elearn/security.py", "if user.role not in roles:", "if False:", "Disable require_role"),
]


def main() -> None:
    caught = survived = 0
    for path, old, new, label in MUTATIONS:
        target = pathlib.Path(path)
        original = target.read_text()
        if old not in original:
            print(f"SKIPPED (pattern not found): {label}")
            continue
        target.write_text(original.replace(old, new, 1))
        try:
            result = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                                    capture_output=True, text=True, timeout=120)
        finally:
            target.write_text(original)
        if result.returncode != 0:
            caught += 1
            print(f"CAUGHT    {label}")
        else:
            survived += 1
            print(f"SURVIVED  {label}")
    print(f"\n{caught} caught, {survived} survived")


if __name__ == "__main__":
    main()
