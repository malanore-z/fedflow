"""
Units APIs
===========
some apis for units convert.
"""
__all__ = [
    "Units",
    "ByteUnits"
]

import abc


class Units(object):

    """
    The basic class of all units
    """

    @classmethod
    @abc.abstractmethod
    def convert(cls, _from, _to, _value):
        """
        convert value from unit '_from' to unit '_to'

        :param _from: the instance of ``Units``
        :param _to: the instance of ``Units``
        :param _value: a number value
        :return: a number value
        """
        pass

    @classmethod
    @abc.abstractmethod
    def parse(cls, s: str):
        """
        parse str value

        :param s: value
        :return: a tuple consist of value and units, (value, units)
        """
        pass

    @abc.abstractmethod
    def to_string(self, _value=None) -> str:
        """
        Get a str value

        :param _value: a number value
        :return: a str value
        """
        pass

    def __repr__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string()

    def from_units(self, _from, _value):
        return Units.convert(_from, self, _value)

    def to_units(self, _to, _value):
        return Units.convert(self, _to, _value)


class ByteUnits(Units):

    """
    An units class used for handling byte convert
    """

    PREFIX_SEQUENCE = "-KMGTPEZY"

    def __init__(self, prefix, is_binary, is_byte):
        super(ByteUnits, self).__init__()
        self.prefix = prefix
        self.is_binary = is_binary
        self.is_byte = is_byte

    @classmethod
    def convert(cls, _from, _to, _value):
        if _from.is_binary != _to.is_binary or _from.is_byte != _to.is_byte:
            raise ValueError("_from and _to must have the same units format.")
        dist = _to.prefix - _from.prefix
        co = 1024 if _from.is_binary else 1000
        while dist != 0:
            if dist < 0:
                _value = _value * co
                dist += 1
            else:
                _value = _value / co
                dist -= 1
        return _value

    @classmethod
    def parse(cls, s: str):
        """
        parse a str to a tuple ``(int_value, units)``

        :param s:
        :return:
        """
        if s is None:
            raise ValueError("s cannot be None")
        s = s.strip()
        if s == "":
            return 0, ByteUnits(0, 0, 0)
        value = 0
        units = ByteUnits(0, 0, 0)

        pos = 1
        if s[-pos] == 'b':
            units.is_byte = 0
        elif s[-pos] == 'B':
            units.is_byte = 1
        else:
            raise ValueError("Illegal unit: %s" % s)
        pos += 1
        if pos > len(s):
            return value, units

        if s[-pos] == "i":
            units.is_binary = 1
            pos += 1
        else:
            units.is_binary = 0
        if pos > len(s):
            raise ValueError("Illegal unit: %s" % s)

        prefix = ByteUnits.PREFIX_SEQUENCE.find(s[-pos])
        if prefix >= 0:
            units.prefix = prefix
            pos += 1

        if units.prefix == 0 and units.is_binary == 1:
            raise ValueError("Illegal unit: %s" % s)

        if pos > len(s):
            return value, units

        value_s = s[:-(pos-1)]
        try:
            value = int(value_s)
        except:
            try:
                value = float(value_s)
            except:
                pass

        return value, units

    def to_string(self, _value=None) -> str:
        units_str = "%s%s%s" % (
            ByteUnits.PREFIX_SEQUENCE[self.prefix],
            "i" if self.is_binary else "-",
            "B" if self.is_byte else "b"
        )
        units_str = units_str.replace("-", "")
        if _value is None:
            return units_str
        else:
            return str(_value) + units_str


for prefix in range(len(ByteUnits.PREFIX_SEQUENCE)):
    for is_binary in range(2):
        for is_byte in range(2):
            units = ByteUnits(prefix, is_binary, is_byte)
            setattr(ByteUnits, units.__repr__(), units)
