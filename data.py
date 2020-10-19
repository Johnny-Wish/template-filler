from blob import Blob, Atom


class AbstractData:
    def __init__(self, tag, value):
        self.tag = str(tag)
        self.value = value

    def eval(self):
        pass

    def to_dict(self):
        return {self.tag: self}


class AtomicData(AbstractData):
    def __init__(self, tag, value):
        super(AtomicData, self).__init__(tag, value)

    def eval(self):
        return Atom(str(self.value))


class SequenceData(AbstractData):
    def __init__(self, tag, value):
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"Unsupported sequence type {type(value)}")

        super(SequenceData, self).__init__(tag, value)

    def eval(self):
        return [Blob(str(v), atomic=True, separator=" ") for v in self.value]
