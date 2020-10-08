from copy import deepcopy
from blob import Blob, Atom, Sentence, Paragraph, Article
from blob import ParagraphSlot, TaggedPlaceholder, FirstNamePlaceholder
from data import AtomicData, SequenceData

b1 = Sentence(
    entries=[
        Atom(entries="This is a"),
        Atom(entries="   "),
        Atom(entries="sentence"),
    ], atomic=False
)

b2 = Paragraph(
    entries=[
        Sentence(entries="Here is another paragraph.", atomic=True),
        Sentence(entries="There're several sentences in this paragraph.", atomic=True),
        Sentence(entries="including this one, which has not been capitalized", atomic=True),
    ], atomic=False
)

b3 = Paragraph(
    entries=[
        Sentence(entries="What is your name? ", atomic=True),
        FirstNamePlaceholder(),
        Sentence(entries="Here is a question for ya:", atomic=True),
        Sentence(entries="3 * 5 + 1 =", atomic=True),
        TaggedPlaceholder(tag="answer1"),
    ], atomic=False
)

b4 = Blob(
    entries=[
        Blob(entries="What are your", atomic=True, separator=" "),
        Blob(entries="favourite numbers?", atomic=True, separator=" "),
        ParagraphSlot(tag="favnum"),
    ], atomic=False, separator=" "
)


def test_blob():
    x = Blob(entries=[b1, b2], separator="\n-----This is the division between two paragraphs-----\n")
    print(x.serialize())


def test_placeholder():
    data1 = AtomicData("answer1", 16)
    data2 = AtomicData("answer1", "18")
    name_data = AtomicData("first_name", "shuheng")
    b4 = deepcopy(b3)
    x = Article(entries=[b1, b2, b3, b4])
    y1 = x.fill(data1.to_dict()).fill(name_data.to_dict())
    y2 = x.fill(data2.to_dict()).fill(name_data.to_dict())
    print(x.is_filled, y1.is_filled, y2.is_filled)
    print(y1.serialize())
    print(y2.serialize())
    print(x.serialize(ignore_unfilled=True))
    # print(x.serialize())


def test_slot():
    data1 = SequenceData("favnum", ["123"])
    data2 = SequenceData("favnum", [])
    data3 = SequenceData("favnum", [456, 789, 101])
    x = Blob(entries=[b1, b2, b4], separator="\n")
    y = x.fill(data1.to_dict())
    y = y.fill(data2.to_dict())
    y = y.fill(data3.to_dict())
    print(x.is_filled, y.is_filled)
    print(x.serialize())
    print(y.serialize())

    x1 = Blob(entries=[b1, b2, b3, b4], separator="\n")
    x2 = Blob(entries=[b1, b2, b3, b4], separator="\n")
    z = Blob([x1, x2])
    print(x1.list_unfilled_tags(), x1.is_filled)
    print(z.list_unfilled_tags(), x2.is_filled)


def test_blob_cast():
    x = Article(entries=[b1, b2])
    print(x.serialize())
    y = x.cast_to("paragraph")
    print(y.serialize())


if __name__ == '__main__':
    test_blob()
    test_placeholder()
    test_slot()
    test_blob_cast()
