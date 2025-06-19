# pysec

FOSS endpoint security.

pysec offers the following components:

1. `pysec audit config`: A tool to check the security configuration of a system.
2. `pysec audit packages`: Get a list of all installed packages and CVEs related to them.


## Try it out!

```
git clone https://github.com/MartinThoma/pysec.git
pipx install -e .
```


## Supported platforms

At the moment only Ubuntu, but you can have a look at `oschecks/ubunut.py`.
Only some very basic checks need to be implemented for other platforms.


Simply copy the `ubuntu.py`, adjust the commands accordingly and make a pull request :-)