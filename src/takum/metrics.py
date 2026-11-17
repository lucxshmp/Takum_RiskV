
import math
import struct

import mpmath as mp

from typing import Sequence

from .decoder import decode, decode_to_float
from .encoder import encode
from .formats import TakumClass


# ---------------------------------------------------------
# DECODIFICAÇÃO DE VETORES
# ---------------------------------------------------------

def decode_vector(
    vector: Sequence[int],
    width: int
) -> list[float]:
    """Decodifica um vetor Takum."""

    values = []

    for raw in vector:
        result = decode(raw, width)

        if result.classification == TakumClass.NAR:
            values.append(float("nan"))
        else:
            values.append(result.value)

    return values


# ---------------------------------------------------------
# MÉTRICAS TRADICIONAIS
# ---------------------------------------------------------

def mean_absolute_error(
    reference: Sequence[float],
    measured: Sequence[float]
) -> float:
    """Erro absoluto médio."""

    if len(reference) != len(measured):
        raise ValueError("Os vetores possuem tamanhos diferentes.")

    if not reference:
        return 0.0

    errors = [
        abs(float(x) - float(y))
        for x, y in zip(reference, measured)
    ]

    return sum(errors) / len(errors)


def root_mean_squared_error(
    reference: Sequence[float],
    measured: Sequence[float]
) -> float:
    """Raiz do erro quadrático médio."""

    if len(reference) != len(measured):
        raise ValueError("Os vetores possuem tamanhos diferentes.")

    if not reference:
        return 0.0

    squared_errors = [
        (float(x) - float(y)) ** 2
        for x, y in zip(reference, measured)
    ]

    return math.sqrt(sum(squared_errors) / len(squared_errors))


def maximum_absolute_error(
    reference: Sequence[float],
    measured: Sequence[float]
) -> float:
    """Maior erro absoluto observado."""

    if len(reference) != len(measured):
        raise ValueError("Os vetores possuem tamanhos diferentes.")

    if not reference:
        return 0.0

    return max(
        abs(float(x) - float(y))
        for x, y in zip(reference, measured)
    )


def mean_relative_error(
    reference: Sequence[float],
    measured: Sequence[float]
) -> float:
    """Erro relativo médio. Referências iguais a zero são ignoradas."""

    if len(reference) != len(measured):
        raise ValueError("Os vetores possuem tamanhos diferentes.")

    errors = []

    for x, y in zip(reference, measured):
        x = float(x)
        y = float(y)

        if x != 0:
            errors.append(abs(x - y) / abs(x))

    if not errors:
        return 0.0

    return sum(errors) / len(errors)


def calculate_metrics(
    reference: Sequence[float],
    measured: Sequence[float]
) -> dict[str, float]:
    """Calcula o conjunto tradicional de métricas."""

    return {
        "mae": mean_absolute_error(reference, measured),
        "rmse": root_mean_squared_error(reference, measured),
        "max_error": maximum_absolute_error(reference, measured),
        "mean_relative_error": mean_relative_error(
            reference,
            measured
        ),
    }


# ---------------------------------------------------------
# REFERÊNCIA DE ALTA PRECISÃO
# ---------------------------------------------------------

def high_precision_reference(
    values: Sequence[float],
    precision: int = 50
) -> list[mp.mpf]:
    """
    Converte os valores para mpmath com precisão arbitrária.

    precision representa a quantidade de dígitos decimais.
    Isso não implementa, por si só, o formato IEEE 754 binary128.
    """

    if precision < 1:
        raise ValueError("A precisão deve ser positiva.")

    with mp.workdps(precision):
        return [
            mp.mpf(str(value))
            for value in values
        ]


# ---------------------------------------------------------
# QUANTIZAÇÃO TAKUM
# ---------------------------------------------------------

def quantize_takum(
    values: Sequence[float],
    width: int
) -> list[float]:
    """Codifica e decodifica valores usando Takum T8, T16 ou T32."""

    result = []

    for value in values:
        encoded = encode(float(value), width)
        decoded = decode_to_float(encoded, width)
        result.append(decoded)

    return result


# ---------------------------------------------------------
# QUANTIZAÇÃO IEEE 754 FP16 E FP32
# ---------------------------------------------------------

def quantize_ieee(
    values: Sequence[float],
    width: int
) -> list[float]:
    """
    Simula a quantização IEEE 754 FP16 ou FP32.

    Utiliza a serialização binária nativa do Python.
    """

    formats = {
        16: "e",
        32: "f",
    }

    if width not in formats:
        raise ValueError("IEEE deve utilizar FP16 ou FP32.")

    ieee_format = formats[width]
    result = []

    for value in values:
        number = float(value)

        try:
            packed = struct.pack(ieee_format, number)
            decoded = struct.unpack(ieee_format, packed)[0]

        except OverflowError:
            decoded = math.copysign(float("inf"), number)

        result.append(decoded)

    return result


# ---------------------------------------------------------
# QUANTIZAÇÃO IEEE 754 FP8 E4M3FN
# ---------------------------------------------------------

def quantize_ieee_fp8(
    values: Sequence[float]
) -> list[float]:
    """
    Simula IEEE 754 FP8 E4M3FN.

    Estrutura:
    - 1 bit de sinal;
    - 4 bits de expoente;
    - 3 bits de fração;
    - bias do expoente: 7;
    - menor subnormal positivo: 2**-9;
    - menor normal positivo: 2**-6;
    - maior valor finito: 448.

    O código 0x7F é reservado para NaN.
    Não existe representação de infinito.

    O arredondamento utiliza o valor representável mais próximo.
    Em caso de empate, escolhe o código com bit menos significativo
    igual a zero (ties to even).
    """

    # Gera todos os valores positivos finitos representáveis.
    # Cada elemento contém (código FP8, valor numérico).
    representable_values = []

    for exponent in range(16):
        for fraction in range(8):

            # E4M3FN reserva 0x7F para NaN.
            if exponent == 15 and fraction == 7:
                continue

            if exponent == 0:
                # Zero e números subnormais.
                number = fraction * (2 ** -9)
            else:
                # Números normais.
                number = (
                    1 + fraction / 8
                ) * (2 ** (exponent - 7))

            code = (exponent << 3) | fraction

            representable_values.append((code, number))

    result = []

    for value in values:
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            result.append(float("nan"))
            continue

        if number == 0:
            result.append(number)
            continue

        sign = -1.0 if number < 0 else 1.0
        absolute = abs(number)

        # Valores acima do maior finito não são representáveis.
        if absolute > 448:
            result.append(float("nan"))
            continue

        # Seleciona o valor representável mais próximo.
        # Em empate, prefere o código par.
        best_code, best_value = min(
            representable_values,
            key=lambda item: (
                abs(absolute - item[1]),
                item[0] & 1
            )
        )

        result.append(sign * best_value)

    return result


# ---------------------------------------------------------
# CÁLCULO DE PERCENTIS
# ---------------------------------------------------------

def _percentile(sorted_values, percentile):
    """Calcula percentil por interpolação linear."""

    if not sorted_values:
        return mp.mpf(0)

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = mp.mpf(len(sorted_values) - 1) * percentile / 100

    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)

    fraction = position - lower

    return (
        sorted_values[lower] * (1 - fraction)
        + sorted_values[upper] * fraction
    )


# ---------------------------------------------------------
# MÉTRICAS DE ALTA PRECISÃO
# ---------------------------------------------------------

def calculate_high_precision_metrics(
    reference: Sequence[mp.mpf],
    measured: Sequence[float]
) -> dict[str, float | int]:
    """
    Calcula métricas utilizando mpmath para os cálculos
    de erro e preservando a precisão da referência.
    """

    if len(reference) != len(measured):
        raise ValueError("Os vetores possuem tamanhos diferentes.")

    if not reference:
        return {
            "mae": 0.0,
            "rmse": 0.0,
            "max_error": 0.0,
            "mean_relative_error": 0.0,
            "median_relative_error": 0.0,
            "p95_relative_error": 0.0,
            "p99_relative_error": 0.0,
            "samples": 0,
            "relative_samples": 0,
        }

    with mp.workdps(50):

        absolute_errors = []
        relative_errors = []

        for ref, value in zip(reference, measured):

            ref = mp.mpf(ref)
            measured_value = mp.mpf(str(value))

            if not mp.isfinite(ref) or not mp.isfinite(measured_value):
                continue

            error = abs(ref - measured_value)

            absolute_errors.append(error)

            if ref != 0:
                relative_errors.append(error / abs(ref))

        if not absolute_errors:
            raise ValueError(
                "Não existem amostras finitas para comparar."
            )

        mae = mp.fsum(absolute_errors) / len(absolute_errors)

        mse = (
            mp.fsum(error ** 2 for error in absolute_errors)
            / len(absolute_errors)
        )

        rmse = mp.sqrt(mse)
        max_error = max(absolute_errors)

        relative_errors.sort()

        if relative_errors:

            mean_relative = (
                mp.fsum(relative_errors) / len(relative_errors)
            )

            median_relative = _percentile(relative_errors, 50)
            p95_relative = _percentile(relative_errors, 95)
            p99_relative = _percentile(relative_errors, 99)

        else:
            mean_relative = mp.mpf(0)
            median_relative = mp.mpf(0)
            p95_relative = mp.mpf(0)
            p99_relative = mp.mpf(0)

        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "max_error": float(max_error),
            "mean_relative_error": float(mean_relative),
            "median_relative_error": float(median_relative),
            "p95_relative_error": float(p95_relative),
            "p99_relative_error": float(p99_relative),
            "samples": len(absolute_errors),
            "relative_samples": len(relative_errors),
        }


# ---------------------------------------------------------
# COMPARAÇÃO ENTRE FORMATOS NUMÉRICOS
# ---------------------------------------------------------

def compare_numeric_formats(
    values: Sequence[float],
    takum_widths=(8, 16, 32),
    ieee_widths=(16, 32),
    include_fp8=True,
) -> dict:
    """
    Compara Takum e IEEE 754 utilizando Binary128 como referência.

    Formatos avaliados por padrão:
    - Takum T8, T16 e T32;
    - IEEE FP8 E4M3FN;
    - IEEE FP16;
    - IEEE FP32.

    Todos os formatos são avaliados sobre o mesmo conjunto
    de amostras finitas, garantindo uma comparação justa.

    Amostras que geram NaN ou infinito em qualquer formato
    são excluídas de todas as comparações.
    """

    reference = quantize_binary128(
        high_precision_reference(values, precision=50)
    )

    measured_formats = {}

    # Quantização Takum.
    for width in takum_widths:
        name = f"Takum T{width}"
        measured_formats[name] = quantize_takum(values, width)

    # Quantização IEEE FP16 e FP32.
    for width in ieee_widths:
        name = f"IEEE FP{width}"
        measured_formats[name] = quantize_ieee(values, width)

    # Quantização IEEE FP8 E4M3FN.
    if include_fp8:
        measured_formats["IEEE FP8 E4M3FN"] = quantize_ieee_fp8(values)

    # Identifica as amostras válidas em todos os formatos.
    valid_indices = []

    for i, ref in enumerate(reference):

        if not mp.isfinite(ref):
            continue

        all_finite = all(
            math.isfinite(float(measured[i]))
            for measured in measured_formats.values()
        )

        if all_finite:
            valid_indices.append(i)

    if not valid_indices:
        raise ValueError(
            "Não existem amostras finitas comuns a todos os formatos."
        )

    # Aplica exatamente o mesmo subconjunto a todos os formatos.
    common_reference = [
        reference[i] for i in valid_indices
    ]

    results = {}

    for name, measured in measured_formats.items():

        common_measured = [
            measured[i] for i in valid_indices
        ]

        metrics = calculate_high_precision_metrics(
            common_reference,
            common_measured
        )

        metrics["input_samples"] = len(values)
        metrics["excluded_samples"] = (
            len(values) - len(valid_indices)
        )

        results[name] = metrics

    return results


# ---------------------------------------------------------
# ARREDONDAMENTO BINARY128
# ---------------------------------------------------------

def _round_binary_ties_to_even(value):
    """Arredonda um valor positivo para o inteiro mais próximo, com empate par."""

    lower = mp.floor(value)
    fraction = value - lower

    if fraction < mp.mpf("0.5"):
        return int(lower)

    if fraction > mp.mpf("0.5"):
        return int(lower + 1)

    # Empate: escolhe o inteiro par.
    if int(lower) % 2 == 0:
        return int(lower)

    return int(lower + 1)


# ---------------------------------------------------------
# QUANTIZAÇÃO IEEE 754 BINARY128
# ---------------------------------------------------------

def quantize_binary128(
    values: Sequence[float]
) -> list[mp.mpf]:
    """
    Quantiza valores para IEEE 754 binary128.

    Parâmetros do formato:
    - Precisão: 113 bits;
    - Expoente: 15 bits;
    - Bias: 16383;
    - Expoente normal mínimo: -16382;
    - Expoente normal máximo: 16383;
    - Menor subnormal positivo: 2**-16494.

    O arredondamento utilizado é round to nearest, ties to even.

    Retorna valores mp.mpf que representam os valores
    binary128 quantizados.
    """

    precision = 256
    exponent_bias = 16383
    fraction_bits = 112

    min_normal_exponent = -16382
    max_normal_exponent = 16383
    min_subnormal_exponent = -16494

    result = []

    with mp.workprec(precision):

        for value in values:

            number = mp.mpf(value)

            if mp.isnan(number):
                result.append(mp.nan)
                continue

            if mp.isinf(number):
                result.append(number)
                continue

            if number == 0:
                result.append(mp.mpf(0))
                continue

            sign = -1 if number < 0 else 1
            absolute = abs(number)

            mantissa, exponent = mp.frexp(absolute)

            unbiased_exponent = exponent - 1

            # Overflow para infinito.
            if unbiased_exponent > max_normal_exponent:
                result.append(mp.inf * sign)
                continue

            # Números subnormais.
            if unbiased_exponent < min_normal_exponent:

                scaled = mp.ldexp(
                    absolute,
                    -min_subnormal_exponent
                )

                significand = _round_binary_ties_to_even(scaled)

                if significand == 0:
                    result.append(mp.mpf(0))
                    continue

                quantized = mp.ldexp(
                    mp.mpf(significand),
                    min_subnormal_exponent
                )

                result.append(sign * quantized)
                continue

            # Números normais.
            significand = _round_binary_ties_to_even(
                mp.ldexp(mantissa, fraction_bits + 1)
            )

            # Arredondamento pode gerar carry no expoente.
            if significand == 2 ** (fraction_bits + 1):
                significand >>= 1
                unbiased_exponent += 1

            # Verifica overflow após arredondamento.
            if unbiased_exponent > max_normal_exponent:
                result.append(mp.inf * sign)
                continue

            quantized = mp.ldexp(
                mp.mpf(significand),
                unbiased_exponent - fraction_bits
            )

            result.append(sign * quantized)

    return result
