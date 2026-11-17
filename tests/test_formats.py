
import pytest

from takum.formats import (
    TakumFormat,
    TakumClass,
    TakumValue,
    validate_width,
    mask_for_width,
    sign_mask,
)


@pytest.mark.parametrize("width", [8, 16, 32])
def test_supported_formats(width):
    validate_width(width)


@pytest.mark.parametrize("width", [8, 16, 32])
def test_mask_for_width(width):
    assert mask_for_width(width) == (1 << width) - 1


@pytest.mark.parametrize("width", [8, 16, 32])
def test_sign_mask(width):
    assert sign_mask(width) == 1 << (width - 1)


def test_invalid_width():
    with pytest.raises(ValueError):
        validate_width(64)


def test_takum_value_zero():
    value = TakumValue.zero()

    assert value.classification == TakumClass.ZERO
    assert value.value == 0.0


def test_takum_value_nar():
    value = TakumValue.nar()

    assert value.classification == TakumClass.NAR
    assert value.value is None


def test_takum_value_finite():
    value = TakumValue.finite(3.5)

    assert value.classification == TakumClass.FINITE
    assert value.value == 3.5


def test_float_conversion_of_nar():
    value = TakumValue.nar()

    with pytest.raises(ValueError):
        float(value)
