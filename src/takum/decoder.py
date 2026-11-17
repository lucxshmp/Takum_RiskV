
import math

from .formats import (
    TakumFields,
    TakumValue,
    mask_for_width,
    sign_mask,
    normalize_width,
)


def _validate_raw(raw: int, width: int) -> None:
    """Valida a representação binária recebida."""
    width = normalize_width(width)

    if not isinstance(raw, int):
        raise TypeError("A representação Takum deve ser um inteiro.")

    if raw < 0 or raw > mask_for_width(width):
        raise ValueError(
            f"O valor {raw} não cabe em {width} bits."
        )


def _expand_bits(raw: int, width: int) -> tuple[int, int]:
    """Acrescenta ghost bits à direita em formatos menores que 12 bits."""
    if width < 12:
        extra_bits = 12 - width
        return raw << extra_bits, 12

    return raw, width


def decode_fields(raw: int, width: int) -> TakumFields:
    """Extrai os campos S, D, R, C e M."""
    width = normalize_width(width)
    _validate_raw(raw, width)

    expanded, effective_width = _expand_bits(raw, width)

    sign = (expanded >> (effective_width - 1)) & 1
    direction = (expanded >> (effective_width - 2)) & 1

    regime_bits = (
        expanded >> (effective_width - 5)
    ) & 0b111

    regime = (
        7 - regime_bits
        if direction == 0
        else regime_bits
    )

    characteristic_width = regime
    fraction_width = effective_width - regime - 5

    if fraction_width < 0:
        raise ValueError("Largura de campos inválida.")

    fraction_mask = (1 << fraction_width) - 1
    fraction = expanded & fraction_mask

    characteristic = (
        expanded >> fraction_width
    ) & ((1 << characteristic_width) - 1)

    return TakumFields(
        sign=sign,
        direction=direction,
        regime=regime_bits,
        characteristic=characteristic,
        fraction=fraction,
        regime_width=3,
        characteristic_width=characteristic_width,
        fraction_width=fraction_width,
    )


def decode(raw: int, width: int) -> TakumValue:
    """Decodifica uma representação Takum."""
    width = normalize_width(width)
    _validate_raw(raw, width)

    if raw == 0:
        return TakumValue.zero()

    if raw == sign_mask(width):
        return TakumValue.nar()

    fields = decode_fields(raw, width)

    sign = fields.sign
    direction = fields.direction

    regime = (
        7 - fields.regime
        if direction == 0
        else fields.regime
    )

    characteristic_bits = fields.characteristic
    fraction_bits = fields.fraction

    if direction == 0:
        characteristic = (
            -(2 ** (regime + 1))
            + 1
            + characteristic_bits
        )
    else:
        characteristic = (
            2 ** regime - 1 + characteristic_bits
        )

    p = fields.fraction_width

    mantissa = (
        fraction_bits / (2 ** p)
        if p > 0
        else 0.0
    )

    sign_factor = -1 if sign else 1

    logarithmic_value = sign_factor * (
        characteristic + mantissa
    )

    try:
        magnitude = math.exp(
            logarithmic_value / math.e
        )
    except OverflowError:
        magnitude = math.inf

    return TakumValue.finite(sign_factor * magnitude)


def decode_to_float(raw: int, width: int) -> float:
    """Converte uma representação Takum diretamente para float."""
    result = decode(raw, width)

    if result.is_nar():
        raise ValueError("Não é possível converter NaR para float.")

    return float(result.value)
