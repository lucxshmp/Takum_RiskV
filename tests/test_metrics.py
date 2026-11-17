
import pytest
from decimal import Decimal
import mpmath as mp

from src.takum.metrics import (
    decode_vector,
    mean_absolute_error,
    root_mean_squared_error,
    maximum_absolute_error,
    mean_relative_error,
    calculate_metrics,
    high_precision_reference,
    quantize_takum,
    quantize_ieee,
    calculate_high_precision_metrics,
    compare_numeric_formats,
    quantize_binary128,
)


# ---------------------------------------------------------
# TESTES ORIGINAIS
# ---------------------------------------------------------

def test_mean_absolute_error():
    reference = [1.0, 2.0, 3.0]
    measured = [1.1, 1.9, 3.2]

    assert mean_absolute_error(reference, measured) == pytest.approx(0.1333333)


def test_rmse():
    reference = [1.0, 2.0, 3.0]
    measured = [1.1, 1.9, 3.2]

    assert root_mean_squared_error(reference, measured) == pytest.approx(0.1414213)


def test_maximum_absolute_error():
    reference = [1.0, 2.0, 3.0]
    measured = [1.1, 1.9, 3.2]

    assert maximum_absolute_error(reference, measured) == pytest.approx(0.2)


def test_mean_relative_error():
    reference = [1.0, 2.0, 4.0]
    measured = [1.1, 2.2, 4.0]

    assert mean_relative_error(reference, measured) == pytest.approx(0.0666666667)


def test_calculate_metrics():
    reference = [1.0, 2.0, 3.0]
    measured = [1.1, 1.9, 3.2]

    metrics = calculate_metrics(reference, measured)

    assert "mae" in metrics
    assert "rmse" in metrics
    assert "max_error" in metrics
    assert "mean_relative_error" in metrics


def test_metric_size_mismatch():
    with pytest.raises(ValueError):
        mean_absolute_error([1, 2], [1])


# ---------------------------------------------------------
# TESTES DE REFERÊNCIA DE ALTA PRECISÃO
# ---------------------------------------------------------

def test_high_precision_reference():
    values = [1.5, 2.5, 3.5]

    reference = high_precision_reference(values)

    assert reference[0] == Decimal("1.5")
    assert reference[1] == Decimal("2.5")
    assert reference[2] == Decimal("3.5")


def test_high_precision_reference_precision_validation():
    with pytest.raises(ValueError):
        high_precision_reference([1.0], precision=0)


# ---------------------------------------------------------
# TESTES DE QUANTIZAÇÃO TAKUM
# ---------------------------------------------------------

def test_takum_quantization():
    values = [1.0, 2.0, 3.0]

    result = quantize_takum(values, 16)

    assert len(result) == 3
    assert result[0] == pytest.approx(1.0, rel=0.002)


@pytest.mark.parametrize("width", [8, 16, 32])
def test_takum_quantization_supported_widths(width):
    values = [0.5, 1.0, 2.0]

    result = quantize_takum(values, width)

    assert len(result) == len(values)


# ---------------------------------------------------------
# TESTES DE QUANTIZAÇÃO IEEE 754
# ---------------------------------------------------------

def test_ieee_fp16_quantization():
    values = [1.0, 2.0, 3.0]

    result = quantize_ieee(values, 16)

    assert result == pytest.approx(values)


def test_ieee_fp32_quantization():
    values = [1.0, 2.0, 3.0]

    result = quantize_ieee(values, 32)

    assert result == pytest.approx(values)


def test_ieee_invalid_width():
    with pytest.raises(ValueError):
        quantize_ieee([1.0], 8)


# ---------------------------------------------------------
# TESTES DE MÉTRICAS DE ALTA PRECISÃO
# ---------------------------------------------------------

def test_high_precision_metrics():
    reference = high_precision_reference([1.0, 2.0, 3.0])
    measured = [1.0, 2.1, 3.0]

    metrics = calculate_high_precision_metrics(reference, measured)

    assert metrics["samples"] == 3
    assert metrics["mae"] == pytest.approx(0.1 / 3)
    assert metrics["max_error"] == pytest.approx(0.1)


def test_high_precision_metrics_percentiles():
    reference = high_precision_reference([1, 2, 3, 4, 5])
    measured = [1.1, 2.2, 3.3, 4.4, 5.5]

    metrics = calculate_high_precision_metrics(reference, measured)

    assert metrics["median_relative_error"] > 0
    assert metrics["p95_relative_error"] > 0
    assert metrics["p99_relative_error"] > 0


def test_high_precision_metrics_empty_vectors():
    metrics = calculate_high_precision_metrics([], [])

    assert metrics["samples"] == 0
    assert metrics["mae"] == 0.0


def test_high_precision_metrics_size_mismatch():
    reference = high_precision_reference([1, 2])

    with pytest.raises(ValueError):
        calculate_high_precision_metrics(reference, [1.0])


# ---------------------------------------------------------
# TESTES DE COMPARAÇÃO ENTRE FORMATOS
# ---------------------------------------------------------

def test_compare_numeric_formats():
    values = [0.1, 1.0, 10.0]

    results = compare_numeric_formats(values)

    assert "Takum T8" in results
    assert "Takum T16" in results
    assert "Takum T32" in results
    assert "IEEE FP8 E4M3FN" in results
    assert "IEEE FP16" in results
    assert "IEEE FP32" in results

    for metrics in results.values():
        assert metrics["samples"] == len(values)
        assert metrics["mae"] >= 0
        assert metrics["rmse"] >= 0


def test_compare_numeric_formats_custom_widths():
    values = [1.0, 2.0, 3.0]

    results = compare_numeric_formats(
        values,
        takum_widths=(8, 16),
        ieee_widths=(32,),
        include_fp8=False,
    )

    assert len(results) == 3
    assert "Takum T8" in results
    assert "Takum T16" in results
    assert "IEEE FP32" in results


# ---------------------------------------------------------
# TESTE DE DECODIFICAÇÃO DE VETOR
# ---------------------------------------------------------

def test_decode_vector():
    from src.takum.encoder import encode

    values = [1.0, 2.0, 3.0]

    encoded = [
        encode(value, 16)
        for value in values
    ]

    decoded = decode_vector(encoded, 16)

    assert decoded == pytest.approx(values, rel=0.002)


# ---------------------------------------------------------
# TESTES IEEE BINARY128
# ---------------------------------------------------------

def test_binary128_basic_values():
    values = [1.0, -2.5, 0.0]

    result = quantize_binary128(values)

    assert result[0] == 1
    assert result[1] == -mp.mpf("2.5")
    assert result[2] == 0


def test_binary128_precision():
    with mp.workprec(256):
        values = [mp.mpf("1.1")]

        result = quantize_binary128(values)

        error = abs(result[0] - mp.mpf("1.1"))

        assert result[0] != mp.mpf("1.1")
        assert error < mp.mpf("1e-33")


def test_binary128_subnormal():
    with mp.workprec(256):
        smallest = mp.ldexp(mp.mpf(1), -16494)

        result = quantize_binary128([smallest])

        assert result[0] == smallest


def test_binary128_overflow():
    with mp.workprec(256):
        value = mp.ldexp(mp.mpf(1), 16384)

        result = quantize_binary128([value])

        assert mp.isinf(result[0])
