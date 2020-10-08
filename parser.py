import re
import string
import warnings
from blob import Blob, Blank, Block
from blob import Article, Paragraph, Sentence, Atom
from blob import get_blank

SENTENCE_TAG = "__(sent_.*?)__"
PARAGRAPH_TAG = "__(para_.*?)__"
ANY_TAG = "__(.*?)__"


def nonempty_segments(s, sep):
    segments = s.split(sep)
    stripped_segments = [s.strip() for s in segments]
    return [s for s in stripped_segments if len(s) != 0]


def check_no_whitespace(s):
    if isinstance(s, (list, tuple)):
        for ss in s:
            check_no_whitespace(ss)

    for whs in string.whitespace:
        if whs in s:
            raise ValueError(f"whitespace {repr(whs)} found in {s}")


def check_no_linebreak(s):
    if isinstance(s, (list, tuple)):
        for ss in s:
            check_no_linebreak(ss)
    if "\n" in s:
        raise ValueError(f"linebreak found in {s}")


def placeholder_pad(s):
    check_no_whitespace(s)
    if s.startswith("__") and s.endswith("__"):
        warnings.warn(f"{s} seems to be already padded")
        return s
    return "__" + s + "__"


def placeholder_unpad(s):
    check_no_whitespace(s)
    if not (s.startswith("__") and s.endswith("__")):
        warnings.warn(f"{s} doesn't seems to be padded")
        return s
    return s[2:-2]


def split_sentences(s: str):
    trailing_dot = s.endswith(".")
    tags = re.findall(SENTENCE_TAG, s)
    for t in tags:
        old = placeholder_pad(t)
        new = old + "."
        s = s.replace(old, new)

    sentences = nonempty_segments(s, ".")
    sentences = [sent + "." if len(re.findall(SENTENCE_TAG, sent)) == 0 else sent for sent in sentences]
    if not trailing_dot and sentences[-1].endswith("."):
        sentences[-1] = sentences[-1][:-1]
    return sentences


class Parser:
    def parse_word(self, s):
        check_no_whitespace(s)
        tags = re.findall(ANY_TAG, s)
        if len(tags) == 0:
            return Atom(s)

        elif len(tags) == 1:
            padded = placeholder_pad(tags[0])
            blank = get_blank(tags[0])
            if padded == s:
                return blank
            else:
                seg1, seg2 = s.split(padded)
                return Block([Atom(seg1), blank, Atom(seg2)], atomic=False, separator="")
        else:
            raise ValueError(f"Multiple tags were found in the word '{s}': {tags}")

    def parse_sentence(self, s):
        check_no_linebreak(s)
        tags = re.findall(SENTENCE_TAG, s)
        check_no_whitespace(tags)

        if len(tags) == 0:
            words = nonempty_segments(s, " ")
            return Sentence([self.parse_word(w) for w in words], atomic=False)
        elif len(tags) == 1:
            padded = placeholder_pad(tags[0])
            if padded != s:
                raise ValueError(f"Bad use of sentence tag: tag={tags[0]}, sentence={s}")
            return get_blank(tags[0])
        else:
            raise ValueError(f"Multiple sentence tags were found in sentence '{s}': {tags}")

    def parse_paragraph(self, s):
        check_no_linebreak(s)
        tags = re.findall(PARAGRAPH_TAG, s)
        check_no_whitespace(tags)

        if len(tags) == 0:
            sentences = split_sentences(s)
            return Paragraph([self.parse_sentence(sent) for sent in sentences], atomic=False)
        elif len(tags) == 1:
            padded = placeholder_pad(tags[0])
            if padded != s:
                raise ValueError(f"Bad use of paragraph tag: tag={tags[0]}, paragraph={s}")
            return get_blank(tags[0])
        else:
            raise ValueError(f"Multiple paragraph tags were found in paragraph '{s}': {tags}")

    def parse_article(self, s):
        paragraphs = nonempty_segments(s, "\n")
        return Article([self.parse_paragraph(para) for para in paragraphs], atomic=False)

    def parse(self, s, ret_type="article"):
        if not isinstance(ret_type, str):
            raise ValueError(f"ret_type must be str, got {type(ret_type)}")
        ret_type = ret_type.lower()
        if ret_type == "article":
            return self.parse_article(s)
        elif ret_type == "paragraph":
            return self.parse_paragraph(s)
        elif ret_type == "sentence":
            return self.parse_sentence(s)
        elif ret_type in ["atom", "word"]:
            return self.parse_word(s)
        else:
            raise ValueError(f"Unknown ret_type: {ret_type}")

    def parse_by_tag(self, tag, s):
        if not isinstance(tag, str):
            raise ValueError(f"tag must be str, got {type(tag)}")
        if tag.startswith("art_"):
            return {tag: self.parse_article(s)}
        elif tag.startswith("para_"):
            return {tag: self.parse_paragraph(s)}
        elif tag.startswith("sent_"):
            return {tag: self.parse_sentence(s)}
        elif tag.startswith("tag_"):
            return {tag: self.parse_word(s)}

        return {tag: self.parse_word(s)}


if __name__ == '__main__':
    parser = Parser()
    # words = ["some", "word", "__first_name__", "__last_name__", "__last_name__.", "'__last_name__."]
    # for w in words:
    #     print(parser.parse_word(w).serialize(ignore_unfilled=True))
    #
    # print(parser.parse_sentence("I am writing for __first_name__.").serialize(ignore_unfilled=True))
    # print(parser.parse_sentence("I am writing for __first_name__ __last_name__.").serialize(ignore_unfilled=True))
    # print(parser.parse_sentence("__sent_overall__"))
    # print(parser.parse_sentence("__sent_overall__").serialize(ignore_unfilled=True))
    #
    # print(parser.parse_paragraph("""Hello, World. Hi, you. __sent_a__ Goodbye until next time."""))
    # print(parser.parse_article("""
    #     __date__
    #     To whom it may concern,
    #     I am writing this letter for __first_name__ __last_name__ to report __his__ academic performance in __project_name__.
    #     __para_project_description__
    #     __sent_overall__ __sent_assignment__ __sent_participation__ __sent_final__
    #     __para_individual__
    #     Sincerely,
    #     __sign__
    # """).serialize(ignore_unfilled=True))

    # paragraph = "__sent_a__ __sent_b__ __sent_c__ __sent_d__ __sent_e__ __sent_f__"
    # print(split_sentences(paragraph))
    # print(parser.parse_paragraph(paragraph))
    # print(parser.parse_paragraph(paragraph).serialize())
    #
    # paragraph = "To whom it may concern,"
    # print(split_sentences(paragraph))
    # print(parser.parse_paragraph(paragraph))
    # print(parser.parse_paragraph(paragraph).serialize())

    print(parser.parse("Hello World"))
