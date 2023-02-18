# pyidle

Idle Champions Automator for MacOS using Python

** Some of the newer changes to server calls has this breaking more often than it should

Install the requirements and run
```bash
sudo python3 idleautomate.py
```
or run with debug on (you probably want this for now)
```
sudo python3 idleautomate.py -d
```

- The UI leaks memory badly
- Automation assumes 4J Briv
- Currently no parsing of dict type
- Only opening of silver/gold implemented (the UI lies)
- Hiding may or may not work, and in multiscreen MacOS has weird behavior here
