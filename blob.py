import string
import warnings
from copy import deepcopy
from global_utils import capitalize


class Blob:
    def __init__(self, entries, atomic=False, separator=" "):
        if not isinstance(entries, (list, str)):
            raise ValueError(f"Argument entries must be either str or list, got {type(entries)}")

        if atomic:
            if isinstance(entries, list):
                raise ValueError(f'Atomic {self.__class__.__name__} has a list of sub-entries')
        else:
            if isinstance(entries, str):
                raise ValueError(f'Non-atomic {self.__class__.__name__} has str entry "{entries}"')
            for entry in entries:
                if not isinstance(entry, Blob):
                    raise ValueError(f"Non-atomic {self} has illegal sub-entry {entry} of type {type(entry)}")

        self.entries = entries
        self.atomic = atomic
        self.entry_separator = separator

    def fill_(self, d: dict):
        if self.atomic:
            return

        for entry in self.entries:
            if isinstance(entry, Blob):
                entry.fill_(d)

    def fill(self, d: dict):
        new = deepcopy(self)
        new.fill_(d)
        return new

    def serialize(self, ignore_unfilled=False) -> str:
        if not ignore_unfilled:
            if not self.is_filled:
                raise ValueError(f"{self} has not been fully filled, "
                                 f"check the following: \n{self.serialize(ignore_unfilled=True)}")

        if self.atomic:
            return self._pre_serialize(str(self.entries))
        else:
            entry_strings = [entry.serialize(ignore_unfilled=True) for entry in self.entries]
            entry_strings = [self._pre_serialize(s) for s in entry_strings]
            return self.entry_separator.join(entry_strings)

    def _pre_serialize(self, entry_str: str) -> str:
        return entry_str

    @property
    def is_filled(self):
        if self.atomic:
            return True
        for entry in self.entries:
            if not entry.is_filled:
                return False
        return True

    def append_entry(self, entry):
        if self.atomic:
            raise ValueError(f"cannot append entries to atomic instance {self}")

        if not isinstance(entry, Blob):
            raise ValueError(f"cannot append entry {entry} of type {type(entry)} to {self}")

        self.entries.append(entry)

    def list_unfilled_tags(self):
        if self.atomic:
            return []

        if isinstance(self, Blank) and len(self.entries) == 0:
            return [self.tag]

        tags = []
        for entry in self.entries:
            if isinstance(entry, Blank) and len(entry.entries) == 0:
                tags.append(entry.tag)
            tags += entry.list_unfilled_tags()

        return tags

    def eval(self):
        return self

    def __repr__(self):
        return f"<{self.__class__.__name__} with entries ({[repr(entry) for entry in self.entries]})>"


class Block(Blob):
    def cast_to(self, block_type, sep=None, copy=False):
        constructor = get_block_constructor(block_type)
        entries = deepcopy(self.entries) if copy else self.entries
        new = constructor(entries)
        if sep is not None:
            new.entry_separator = sep
        return new


class Article(Block):
    def __init__(self, entries, atomic=False):
        super(Article, self).__init__(entries, atomic=atomic, separator="\n")


class Paragraph(Block):
    def __init__(self, entries, atomic=False):
        super(Paragraph, self).__init__(entries, atomic=atomic, separator=" ")

    def _pre_serialize(self, entry_str: str) -> str:
        s = capitalize(entry_str.strip())
        if len(s) >= 1 and s[-1] in string.ascii_letters:
            warnings.warn(f'Sentence ends without a punctuation: "{entry_str}"')
        return s


class Sentence(Block):
    def __init__(self, entries, atomic=False):
        super(Sentence, self).__init__(entries, atomic=atomic, separator=" ")

    def _pre_serialize(self, entry_str: str) -> str:
        return entry_str.strip()


class Atom(Block):
    def __init__(self, entries):
        super(Atom, self).__init__(entries, atomic=True, separator=" ")

    def __repr__(self):
        return f"<{self.__class__.__name__} of {self.entries}>"


class Blank(Blob):
    def __init__(self, tag, separator="\n--blank-sperator--\n"):
        super(Blank, self).__init__(entries=[], atomic=False, separator=separator)
        self.tag = tag

    def fill_(self, d: dict):
        for tag in d:
            if tag == self.tag:
                self.append_entry(d[tag].eval())
        super(Blank, self).fill_(d)


class Slot(Blank):
    def append_entry(self, entries):
        if isinstance(entries, (list, tuple)):
            for entry in entries:
                super(Slot, self).append_entry(entry)
        else:
            super(Slot, self).append_entry(entries)

    def __repr__(self):
        return f"<{self.__class__.__name__} with tag={self.tag} and entries={self.entries}>"


class ParagraphSlot(Slot):
    def __init__(self, tag):
        super(ParagraphSlot, self).__init__(tag, separator="\n")


class SentenceSlot(Slot):
    def __init__(self, tag):
        super(SentenceSlot, self).__init__(tag, separator=" ")


class Placeholder(Blank):
    def __init__(self, tag):
        super(Placeholder, self).__init__(tag=tag, separator=" ")
        self._filled = False

    def append_entry(self, entry):
        super(Placeholder, self).append_entry(entry)
        self._filled = True

    def serialize(self, ignore_unfilled=False):
        if self.is_filled:
            return self._pre_serialize(self.entries[0].serialize())
        if ignore_unfilled:
            return f"<Unfilled Tag `{self.tag}`>"

    @property
    def is_filled(self):
        return self._filled

    def __repr__(self):
        repr = f"{self.__class__.__name__} with tag={self.tag}"
        if self.is_filled:
            return repr + f" entry={self.entries}"
        else:
            return repr + " unfilled"

    def __str__(self):
        if self.is_filled:
            return str(self.entries[0])
        else:
            return f"<Unfilled placeholder with tag {self.tag}>"


class CapitalizedPlaceholder(Placeholder):
    def _pre_serialize(self, entry_str: str) -> str:
        return " ".join([capitalize(s) for s in entry_str.split()])


class LastNamePlaceholder(CapitalizedPlaceholder):
    def __init__(self):
        super(LastNamePlaceholder, self).__init__("last_name")


class FirstNamePlaceholder(CapitalizedPlaceholder):
    def __init__(self):
        super(FirstNamePlaceholder, self).__init__("first_name")


class DatePlaceholder(CapitalizedPlaceholder):
    def __init__(self):
        super(DatePlaceholder, self).__init__("date")


class ProjectNamePlaceholder(Placeholder):
    def __init__(self):
        super(ProjectNamePlaceholder, self).__init__("project_name")


class PronounPlaceholder(Placeholder):
    pass


class HePlaceholder(Placeholder):
    def __init__(self):
        super(HePlaceholder, self).__init__('he')


class HisPlaceholder(Placeholder):
    def __init__(self):
        super(HisPlaceholder, self).__init__('his')


class HimPlaceholder(Placeholder):
    def __init__(self):
        super(HimPlaceholder, self).__init__('him')


class HimselfPlaceholder(Placeholder):
    def __init__(self):
        super(HimselfPlaceholder, self).__init__('himself')


class GroupIdPlaceholder(Placeholder):
    def __init__(self):
        super(GroupIdPlaceholder, self).__init__('gid')


class SignaturePlaceholder(Placeholder):
    def __init__(self):
        super(SignaturePlaceholder, self).__init__('signature')


class TaggedPlaceholder(Placeholder):
    pass


def get_blank(tag):
    if tag == "first_name":
        return FirstNamePlaceholder()
    elif tag == "last_name":
        return LastNamePlaceholder()
    elif tag == "date":
        return DatePlaceholder()
    elif tag == "he":
        return HePlaceholder()
    elif tag == "him":
        return HimPlaceholder()
    elif tag == "his":
        return HisPlaceholder()
    elif tag == "himself":
        return HimselfPlaceholder()
    elif tag == "project_name":
        return ProjectNamePlaceholder()
    elif tag == "gid":
        return GroupIdPlaceholder()
    elif tag == "signature":
        return SignaturePlaceholder()
    elif tag == "program_description":
        return ParagraphSlot(tag=tag)
    elif tag.startswith("para_"):
        return ParagraphSlot(tag=tag)
    elif tag.startswith("sent_"):
        return SentenceSlot(tag=tag)
    else:
        return TaggedPlaceholder(tag=tag)


def get_block_constructor(block_type: str = None):
    if block_type is None:
        return Block
    if not isinstance(block_type, str):
        raise ValueError(f"block_type must be str or None, got {type(block_type)}")
    block_type = block_type.lower()
    if block_type == "block":
        return Block
    elif block_type == "article":
        return Article
    elif block_type == "paragraph":
        return Paragraph
    elif block_type == "sentence":
        return Sentence
    elif block_type == "atom":
        return Atom
    else:
        raise ValueError(f"Unknown block type: {block_type}")
