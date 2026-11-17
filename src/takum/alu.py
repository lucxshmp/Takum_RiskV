
from .decoder import decode
from .encoder import encode
from .formats import TakumClass


def _get_value(raw: int, width: int) -> float:
    """Converte uma palavra Takum em valor real."""
    result = decode(raw, width)

    if result.classification == TakumClass.NAR:
        raise ValueError("Operação com NaR.")

    return float(result.value)


def _check_result(value: float, width: int) -> int:
    """Codifica o resultado de uma operação."""
    return encode(value, width)


def takum_add(a: int, b: int, width: int) -> int:
    """Soma dois valores Takum."""
    x = _get_value(a, width)
    y = _get_value(b, width)

    return _check_result(x + y, width)


def takum_sub(a: int, b: int, width: int) -> int:
    """Subtrai dois valores Takum."""
    x = _get_value(a, width)
    y = _get_value(b, width)

    return _check_result(x - y, width)


def takum_mul(a: int, b: int, width: int) -> int:
    """Multiplica dois valores Takum."""
    x = _get_value(a, width)
    y = _get_value(b, width)

    return _check_result(x * y, width)


def takum_div(a: int, b: int, width: int) -> int:
    """Divide dois valores Takum."""
    x = _get_value(a, width)
    y = _get_value(b, width)

    if y == 0:
        raise ZeroDivisionError("Divisão por zero.")

    return _check_result(x / y, width)
