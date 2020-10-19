import re
from abc import abstractmethod
import warnings


class Checker:
    @abstractmethod
    def check(self, s: str):
        pass


TAG_RE = "__(.*?)__"
MALE_PRONOUNS = ['he', 'him', 'his', 'himself']
FEMALE_PRONOUNS = ['she', 'her', 'her', 'herself']


class PlaceholderChecker:
    def check(self, s: str):
        tags = re.findall(TAG_RE, s)
        if len(tags) != 0:
            raise ValueError(f"unresolved tags found: {tags}, {s}")

        i = s.find("_")
        underscore_occurences = []
        while i != -1:
            lower = max(0, i - 5)
            upper = min(i + 5 + 1, len(s))
            underscore_occurences.append(s[lower:upper])
            i = s.find("_", i + 1)

        if len(underscore_occurences) != 0:
            warnings.warn("resolved underscores: \n" + "\n".join(underscore_occurences))


class GenderChecker:
    def check(self, s):
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

            raise ValueError(f""" Both MALE and FEMALE pronouns found:
                Male pronoun count: {len(male_indices)}
                Female pronoun count: {len(female_indices)}
                Inferred gender is "{inferred_gender}" with confidence {confidence}

                Check these occurrences of the opposite gender:
                {windows(check_indices)}
            """)
        elif len(male_indices) == 0 and len(female_indices) == 0:
            warnings.warn("No gender pronouns found")
        else:
            if len(male_indices) > 0:
                print("Inferred Gender: M")
            else:
                print("Inferred Gender: F")


class NameChecker:
    def __init__(self, first_names, last_names):
        self.first_names = set(first_names)
        self.last_names = set(last_names)

    def check(self, s, target_first_name, target_last_name):
        s = re.sub('[^A-Za-z0-9 ]', ' ', s)
        s = s.split()
        old_s = " ".join(s)
        if target_first_name not in self.first_names:
            warnings.warn(f"Target first name not listed in {self.first_names}: \n {old_s}")
        if target_last_name not in self.last_names:
            warnings.warn(f"Target last name not listed in {self.last_names}: \n {old_s}")

        first_names = self.first_names - {target_first_name, target_last_name}
        last_names = self.last_names - {target_first_name, target_last_name}

        for fn, ln in zip(first_names, last_names):
            if fn in s:
                warnings.warn(f'Alien first name "{fn}" found: \n {old_s}')
            if ln in s:
                warnings.warn(f'Alien last name "{ln}" found: \n {old_s}')

        if not (target_first_name in s):
            warnings.warn(f"Target first name not found: \n {old_s}")
        if not (target_last_name in s):
            warnings.warn(f"Target last name not found: \n {old_s}")
