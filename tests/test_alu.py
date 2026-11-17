
import pytest

from takum import (
    encode,
    decode_to_float,
    takum_add,
    takum_sub,
    takum_mul,
    takum_div,
)


@pytest.mark.parametrize("width", [8, 16, 32])
def test_addition(width):
    a = encode(2.0, width)
    b = encode(3.0, width)

    result = takum_add(a, b, width)

    assert decode_to_float(result, width) > 0


@pytest.mark.parametrize("width", [8, 16, 32])
def test_subtraction(width):
    a = encode(5.0, width)
    b = encode(2.0, width)

    result = takum_sub(a, b, width)

    assert decode_to_float(result, width) > 0


@pytest.mark.parametrize("width", [8, 16, 32])
def test_multiplication(width):
    a = encode(2.0, width)
    b = encode(3.0, width)

    result = takum_mul(a, b, width)

    assert decode_to_float(result, width) > 0


@pytest.mark.parametrize("width", [8, 16, 32])
def test_division(width):
    a = encode(6.0, width)
    b = encode(2.0, width)

    result = takum_div(a, b, width)

    assert decode_to_float(result, width) > 0


def test_division_by_zero():
    a = encode(2.0, 16)
    zero = encode(0.0, 16)

    with pytest.raises(ZeroDivisionError):
        takum_div(a, zero, 16)
