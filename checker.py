import re
from abc import abstractmethod


class Checker:
    def __init__(self, summarizers=None):
        if summarizers is None:
            self.summarizers = []
        else:
            self.summarizers = list(summarizers)

    def append_summarizer(self, s):
        self.summarizers.append(s)

    def update_summary(self, which, msg):
        for s in self.summarizers:
            s.register(self, which, msg)

    @abstractmethod
    def check(self, filename, s: str):
        pass


TAG_RE = "__(.*?)__"
MALE_PRONOUNS = ['he', 'him', 'his', 'himself']
FEMALE_PRONOUNS = ['she', 'her', 'her', 'herself']


class CheckSummarizer:
    def __init__(self):
        self.check_class_names = []
        self.which = []
        self.messages = []

    def register(self, checker, which, msg):
        self.check_class_names.append(checker.__class__.__name__)
        self.which.append(str(which))
        self.messages.append(str(msg))

    def get_summaries(self):
        if len(self.check_class_names) == 0:
            return None

        return [f"{c}: in {w}: {m}" for c, w, m in zip(self.check_class_names, self.which, self.messages)]


class PlaceholderChecker(Checker):
    def check(self, filename, s: str):
        tags = re.findall(TAG_RE, s)
        if len(tags) != 0:
            self.update_summary(filename, f"unresolved tags found: {tags}, {s}")

        i = s.find("_")
        underscore_occurences = []
        while i != -1:
            lower = max(0, i - 5)
            upper = min(i + 5 + 1, len(s))
            underscore_occurences.append(s[lower:upper])
            i = s.find("_", i + 1)

        if len(underscore_occurences) != 0:
            self.update_summary(filename, "resolved underscores: \n" + "\n".join(underscore_occurences))


class GenderChecker(Checker):
    def check(self, filename, s):
        s = re.sub('[^A-Za-z0-9 ]', ' ', s)
        s = s.lower().split()
        male_indices = [i for i, w in enumerate(s) if w in MALE_PRONOUNS]
        female_indices = [i for i, w in enumerate(s) if w in FEMALE_PRONOUNS]

        def window(i, half_size=3):
            lower = max(0, i - half_size)
            upper = min(i + half_size + 1, len(s))
            return " ".join(s[lower: upper])

        def windows(indices, half_size=3):
            return "\n".join(window(i, half_size=half_size) for i in indices)

        if len(male_indices) != 0 and len(female_indices) != 0:
            if len(male_indices) > len(female_indices):
                inferred_gender = "MALE"
                check_indices = female_indices
                confidence = len(male_indices) / (len(male_indices) + len(female_indices))
            else:
                inferred_gender = "FEMALE"
                check_indices = male_indices
                confidence = len(female_indices) / (len(male_indices) + len(female_indices))

            self.update_summary(
                filename,
                f""" Both MALE and FEMALE pronouns found:
                Male pronoun count: {len(male_indices)}
                Female pronoun count: {len(female_indices)}
                Inferred gender is "{inferred_gender}" with confidence {confidence}

                Check these occurrences of the opposite gender:
                {windows(check_indices)}"""
            )
        elif len(male_indices) == 0 and len(female_indices) == 0:
            self.update_summary(filename, "No gender pronouns found")
        else:
            if len(male_indices) > 0:
                print("Inferred Gender: M")
            else:
                print("Inferred Gender: F")


class NameChecker(Checker):
    def __init__(self, first_names, last_names, summarizers=None):
        super(NameChecker, self).__init__(summarizers=summarizers)
        self.first_names = set(first_names)
        self.last_names = set(last_names)

    def check(self, filename, s, target_first_name, target_last_name):
        s = re.sub('[^A-Za-z0-9 ]', ' ', s)
        s = s.split()
        old_s = " ".join(s)
        if target_first_name not in self.first_names:
            self.update_summary(filename, f"Target first name not listed in {self.first_names}: \n {old_s}")
        if target_last_name not in self.last_names:
            self.update_summary(filename, f"Target last name not listed in {self.last_names}: \n {old_s}")

        first_names = self.first_names - {target_first_name, target_last_name}
        last_names = self.last_names - {target_first_name, target_last_name}

        for fn, ln in zip(first_names, last_names):
            if fn in s:
                self.update_summary(filename, f'Alien first name "{fn}" found: \n {old_s}')
            if ln in s:
                self.update_summary(filename, f'Alien last name "{ln}" found: \n {old_s}')

        if not (target_first_name in s):
            self.update_summary(filename, f"Target first name not found: \n {old_s}")
        if not (target_last_name in s):
            self.update_summary(filename, f"Target last name not found: \n {old_s}")


class ApostropheChecker(Checker):
    STRAIGHT = "'"
    CURLY = "’"

    def __init__(self, preference=None, summarizers=None):
        super().__init__(summarizers=summarizers)
        if preference not in (None, "straight", "curly"):
            raise ValueError("preference must be None, 'straight' or 'curly'")
        self.preference = preference

    @property
    def other_style(self):
        if not preference:
            raise ValueError("No preference is set")
        return self.STRAIGHT if self.preference == 'curly' else self.CURLY

    def check(self, filename, s):
        if not self.preference:
            if self.STRAIGHT in s and self.CURLY in s:
                self.update_summary(filename, "Both straight and curly apostrophes are found")
        elif self.other_style in s:
            self.update_summary(
                filename,
                f"Apostrophe preference is set to {self.preference} but {self.other_style} is found"
            )
