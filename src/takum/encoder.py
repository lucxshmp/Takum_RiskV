
import math

from .formats import (
    TakumClass,
    TakumValue,
    mask_for_width,
    sign_mask,
    normalize_width,
)


def _pack_fields(
    sign: int,
    direction: int,
    regime_bits: int,
    characteristic: int,
    fraction: int,
    fraction_width: int,
    effective_width: int,
) -> int:
    """Empacota os campos na representação binária Takum."""
    result = sign << (effective_width - 1)
    result |= direction << (effective_width - 2)
    result |= regime_bits << (effective_width - 5)
    result |= characteristic << fraction_width
    result |= fraction
    return result


def _candidate_encodings(value: float, width: int):
    """
    Gera candidatos válidos próximos do valor desejado.

    A fração é quantizada considerando os bits fantasma
    utilizados nos formatos com menos de 12 bits.
    """
    extra_bits = max(0, 12 - width)
    effective_width = width + extra_bits

    sign = 1 if value < 0 else 0
    sign_factor = -1 if sign else 1

    target_internal = sign_factor * math.e * math.log(abs(value))

    for regime in range(8):
        characteristic_width = regime
        fraction_width = effective_width - regime - 5

        if fraction_width < 0:
            continue

        # Quantidade de bits efetivamente disponíveis na fração.
        effective_fraction_bits = max(0, fraction_width - extra_bits)
        fraction_scale = 1 << effective_fraction_bits

        max_fraction_units = fraction_scale - 1

        for direction in (0, 1):
            if direction == 0:
                regime_bits = 7 - regime
                characteristic_base = -(2 ** (regime + 1)) + 1
            else:
                regime_bits = regime
                characteristic_base = 2 ** regime - 1

            max_characteristic = (1 << characteristic_width) - 1

            for characteristic_bits in range(max_characteristic + 1):
                characteristic = (
                    characteristic_base + characteristic_bits
                )

                fraction_target = (
                    target_internal - characteristic
                ) * fraction_scale

                # Avalia os dois vizinhos da fração ideal.
                lower = math.floor(fraction_target)
                upper = math.ceil(fraction_target)

                for fraction_units in {lower, upper, 0, max_fraction_units}:
                    fraction_units = min(
                        max(fraction_units, 0),
                        max_fraction_units,
                    )

                    fraction = fraction_units << extra_bits

                    raw_expanded = _pack_fields(
                        sign=sign,
                        direction=direction,
                        regime_bits=regime_bits,
                        characteristic=characteristic_bits,
                        fraction=fraction,
                        fraction_width=fraction_width,
                        effective_width=effective_width,
                    )

                    raw = raw_expanded >> extra_bits
                    raw &= mask_for_width(width)

                    # Zero e NaR são representações reservadas.
                    if raw == 0 or raw == sign_mask(width):
                        continue

                    yield raw


def encode(value: float, width: int) -> int:
    """
    Codifica um número real em Takum T8, T16 ou T32.

    Escolhe a representação finita com menor erro absoluto
    no domínio real.
    """
    width = normalize_width(width)

    if not isinstance(value, (int, float)):
        raise TypeError("O valor a codificar deve ser numérico.")

    value = float(value)

    if math.isnan(value):
        return sign_mask(width)

    if value == 0.0:
        return 0

    if math.isinf(value):
        raise OverflowError("Infinito não pode ser codificado em Takum.")

    from .decoder import decode_to_float

    candidates = set(_candidate_encodings(value, width))

    # Zero também pode ser o valor representável mais próximo.
    best_raw = 0
    best_error = abs(value)

    for raw in candidates:
        decoded = decode_to_float(raw, width)
        error = abs(decoded - value)

        if error < best_error:
            best_error = error
            best_raw = raw

    return best_raw


def encode_value(value: TakumValue, width: int) -> int:
    """Codifica um objeto TakumValue."""
    width = normalize_width(width)

    if value.classification == TakumClass.ZERO:
        return 0

    if value.classification == TakumClass.NAR:
        return sign_mask(width)

    if value.classification == TakumClass.FINITE:
        return encode(value.value, width)

    raise ValueError("Classificação Takum desconhecida.")
