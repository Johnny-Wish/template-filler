import re
import requests
from abc import ABC, abstractmethod


def compose(*ps):
    def inner(content):
        for p in ps:
            content = p.process(content)
        return content

    return inner


class PostProcessor(ABC):
    @abstractmethod
    def process(self, content: str) -> str:
        pass


class EnglishDialectPostProcessor(PostProcessor):
    URLs = dict(
        bre="https://raw.githubusercontent.com/hyperreality/"
            "American-British-English-Translator/master/data/british_spellings.json",
        ame="https://raw.githubusercontent.com/hyperreality/"
            "American-British-English-Translator/master/data/american_spellings.json",
    )

    def __init__(self, dialect):
        self.dialect = dialect
        d = requests.get(self.URLs[dialect.lower()]).json()
        # Flip the key and value
        self.d = {v: k for k, v in d.items()}
        d_cap = {k.capitalize(): v.capitalize() for k, v in self.d.items()}
        d_upper = {k.upper(): v.upper() for k, v in self.d.items()}
        self.d.update(d_cap)
        self.d.update(d_upper)
        self.regex = '|'.join(r'\b%s\b' % re.escape(s) for s in self.d)

    def _replace(self, match):
        return self.d[match.group(0)]

    def process(self, content: str) -> str:
        return re.sub(self.regex, self._replace, content)


class ApostrophePostProcessor(PostProcessor):
    styles = dict(curly="’", straight="'")
    reverse_styles = dict(straight="’", curly="'")

    @property
    def preference(self):
        return self.styles[self._pref]

    @property
    def other(self):
        return self.reverse_styles[self._pref]

    def __init__(self, preference):
        self._pref = preference

    def process(self, content):
        return content.replace(self.other, self.preference)
