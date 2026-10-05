# Secure E-Learning Platform

Developed and tested on Python 3.11, standard library only (coverage is optional).

Run the tests:      python3 -m unittest discover -s tests -t . -v
Run the demo:       python3 demo.py
Coverage:           python3 -m coverage run --branch --source=elearn -m unittest discover -s tests -t . && python3 -m coverage report -m
Mutation check:     python3 mutation_check.py

The report is Unit10.md. Raw terminal output behind each figure is in evidence/.
