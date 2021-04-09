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
        self.d = requests.get(self.URLs[dialect.lower()]).json()
        self.dialect = dialect

    def process(self, content: str) -> str:
        for new, old in self.d.items():
            content = content.replace(old, new)
            content = content.replace(old.capitalize(), new.capitalize())
            content = content.replace(old.upper(), new.upper())
        return content


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
