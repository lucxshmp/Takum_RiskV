
import math
import pytest

from takum import (
    encode,
    decode,
    decode_to_float,
    TakumClass,
    sign_mask,
)


def reference_decode(raw: int, width: int):
    """
    Decodificador independente baseado diretamente
    nas equações da definição matemática de Takum.
    """

    if raw == 0:
        return 0.0

    if raw == (1 << (width - 1)):
        return None

    extra_bits = max(0, 12 - width)
    effective_width = width + extra_bits

    expanded = raw << extra_bits

    sign = (expanded >> (effective_width - 1)) & 1
    direction = (expanded >> (effective_width - 2)) & 1

    regime_bits = (
        expanded >> (effective_width - 5)
    ) & 0b111

    if direction == 0:
        regime = 7 - regime_bits
    else:
        regime = regime_bits

    characteristic_width = regime
    mantissa_width = effective_width - regime - 5

    mantissa_mask = (1 << mantissa_width) - 1
    characteristic_mask = (1 << characteristic_width) - 1

    mantissa_bits = expanded & mantissa_mask

    characteristic_bits = (
        expanded >> mantissa_width
    ) & characteristic_mask

    if direction == 0:
        characteristic = (
            -(2 ** (regime + 1))
            + 1
            + characteristic_bits
        )
    else:
        characteristic = (
            2 ** regime
            - 1
            + characteristic_bits
        )

    mantissa = mantissa_bits / (2 ** mantissa_width)

    sign_factor = -1 if sign else 1

    logarithmic_value = sign_factor * (
        characteristic + mantissa
    )

    return sign_factor * math.exp(
        logarithmic_value / math.e
    )


@pytest.mark.parametrize("width", [8, 16, 32])
def test_zero_encoding(width):
    assert encode(0.0, width) == 0

    result = decode(0, width)

    assert result.classification == TakumClass.ZERO
    assert result.value == 0.0


@pytest.mark.parametrize("width", [8, 16, 32])
def test_nan_encoding(width):
    raw = encode(float("nan"), width)

    assert raw == sign_mask(width)

    result = decode(raw, width)

    assert result.classification == TakumClass.NAR


@pytest.mark.parametrize("width", [8, 16, 32])
@pytest.mark.parametrize(
    "value",
    [1.0, -1.0, 2.0, -2.0, 0.5, -0.5]
)
def test_encode_decode_finite(width, value):
    raw = encode(value, width)
    decoded = decode_to_float(raw, width)

    assert math.isfinite(decoded)
    assert decoded != 0.0
    assert (decoded > 0) == (value > 0)


@pytest.mark.parametrize("width", [8, 16, 32])
def test_encode_rejects_infinity(width):
    with pytest.raises(OverflowError):
        encode(float("inf"), width)

    with pytest.raises(OverflowError):
        encode(float("-inf"), width)


def test_decode_rejects_invalid_raw():
    with pytest.raises(ValueError):
        decode(256, 8)


def test_decode_rejects_negative_raw():
    with pytest.raises(ValueError):
        decode(-1, 8)


def test_decode_nar_to_float():
    with pytest.raises(ValueError):
        decode_to_float(sign_mask(16), 16)


def test_all_t8_patterns_match_reference():
    """
    Testa todas as 256 representações possíveis de T8.
    """
    for raw in range(1 << 8):
        expected = reference_decode(raw, 8)
        result = decode(raw, 8)

        if expected is None:
            assert result.classification == TakumClass.NAR

        elif expected == 0.0:
            assert result.classification == TakumClass.ZERO

        else:
            assert result.classification == TakumClass.FINITE

            assert math.isclose(
                result.value,
                expected,
                rel_tol=1e-12,
                abs_tol=1e-12,
            )


@pytest.mark.parametrize("width", [16, 32])
@pytest.mark.parametrize(
    "raw",
    [
        1,
        2,
        3,
        15,
        31,
        127,
        255,
        1024,
        4096,
        16384,
    ],
)
def test_selected_patterns_match_reference(width, raw):
    result = decode(raw, width)
    expected = reference_decode(raw, width)

    assert expected is not None
    assert result.classification == TakumClass.FINITE

    assert math.isclose(
        result.value,
        expected,
        rel_tol=1e-12,
        abs_tol=1e-12,
    )


@pytest.mark.parametrize("width", [8, 16, 32])
@pytest.mark.parametrize(
    "raw",
    [
        1,
        3,
        15,
        31,
        63,
        127,
    ],
)
def test_decode_encode_selected_patterns(width, raw):
    """
    Verifica se a codificação recupera representações
    selecionadas após decodificá-las.
    """
    raw &= (1 << width) - 1

    result = decode(raw, width)

    if result.classification == TakumClass.FINITE:
        encoded = encode(result.value, width)

        decoded_again = decode(encoded, width)

        assert decoded_again.classification == TakumClass.FINITE

        assert math.isclose(
            decoded_again.value,
            result.value,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )


def test_t8_encoder_selects_nearest_representable_value():
    """
    Compara o encoder com uma busca exaustiva independente
    sobre todas as representações finitas de T8.
    """

    representable_values = []

    for raw in range(256):
        value = reference_decode(raw, 8)

        if value is not None and value != 0.0:
            representable_values.append(value)

    test_values = [
        0.1,
        0.3,
        0.5,
        0.9,
        1.1,
        2.0,
        3.0,
        10.0,
        100.0,
        -0.1,
        -0.5,
        -1.1,
        -3.0,
        -10.0,
    ]

    for value in test_values:
        raw = encode(value, 8)
        actual = decode_to_float(raw, 8)

        minimum_error = min(
            abs(candidate - value)
            for candidate in representable_values
        )

        actual_error = abs(actual - value)

        assert actual_error <= minimum_error + 1e-12
