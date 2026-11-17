
import pytest

from takum import (
    encode,
    decode_to_float,
    vtadd_vv,
    vtsub_vv,
    vtmul_vv,
    vtdot_vv,
    vncvt_tt,
)


def encode_vector(values, width):
    return [encode(value, width) for value in values]


def decode_vector(values, width):
    return [decode_to_float(value, width) for value in values]


@pytest.mark.parametrize("width", [8, 16, 32])
def test_vector_addition(width):
    a = encode_vector([1.0, 2.0], width)
    b = encode_vector([3.0, 4.0], width)

    result = decode_vector(vtadd_vv(a, b, width), width)

    assert len(result) == 2


@pytest.mark.parametrize("width", [8, 16, 32])
def test_vector_subtraction(width):
    a = encode_vector([5.0, 6.0], width)
    b = encode_vector([2.0, 3.0], width)

    result = decode_vector(vtsub_vv(a, b, width), width)

    assert len(result) == 2


@pytest.mark.parametrize("width", [8, 16, 32])
def test_vector_multiplication(width):
    a = encode_vector([2.0, 3.0], width)
    b = encode_vector([4.0, 5.0], width)

    result = decode_vector(vtmul_vv(a, b, width), width)

    assert len(result) == 2


@pytest.mark.parametrize("width", [8, 16, 32])
def test_dot_product(width):
    a = encode_vector([1.0, 2.0, 3.0], width)
    b = encode_vector([4.0, 5.0, 6.0], width)

    result = vtdot_vv(a, b, width)

    assert decode_to_float(result, width) > 0


def test_vector_size_mismatch():
    a = encode_vector([1.0, 2.0], 16)
    b = encode_vector([3.0], 16)

    with pytest.raises(ValueError):
        vtadd_vv(a, b, 16)


def test_conversion_between_formats():
    source = encode_vector([1.0, 2.0, 3.0], 8)

    converted = vncvt_tt(
        source,
        source_width=8,
        destination_width=16,
    )

    assert len(converted) == 3
