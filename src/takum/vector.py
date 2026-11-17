
"""
Operações vetoriais para o formato Takum.

Implementação funcional em software das operações propostas:
    vtadd.vv  - soma elemento a elemento
    vtsub.vv  - subtração elemento a elemento
    vtmul.vv  - multiplicação elemento a elemento
    vtdot.vv  - produto escalar
    vncvt.t.t - conversão entre formatos Takum

Observação:
Este módulo simula as operações em Python. Não implementa instruções
de hardware RISC-V ou uma extensão RVV real.
"""
import mpmath as mp

from .metrics import quantize_binary128
from typing import Iterable, List, Optional

from .alu import takum_add, takum_sub, takum_mul
from .decoder import decode
from .encoder import encode
from .formats import TakumFormat


def _check_vector_sizes(a: Iterable[int], b: Iterable[int]) -> None:
    """Verifica se os vetores possuem o mesmo tamanho."""
    if len(a) != len(b):
        raise ValueError(
            f"Vetores com tamanhos diferentes: {len(a)} e {len(b)}"
        )


def vtadd_vv(
    a: List[int],
    b: List[int],
    fmt: TakumFormat
) -> List[int]:
    """Soma dois vetores elemento a elemento."""
    _check_vector_sizes(a, b)

    return [
        takum_add(x, y, fmt)
        for x, y in zip(a, b)
    ]


def vtsub_vv(
    a: List[int],
    b: List[int],
    fmt: TakumFormat
) -> List[int]:
    """Subtrai dois vetores elemento a elemento."""
    _check_vector_sizes(a, b)

    return [
        takum_sub(x, y, fmt)
        for x, y in zip(a, b)
    ]


def vtmul_vv(
    a: List[int],
    b: List[int],
    fmt: TakumFormat
) -> List[int]:
    """Multiplica dois vetores elemento a elemento."""
    _check_vector_sizes(a, b)

    return [
        takum_mul(x, y, fmt)
        for x, y in zip(a, b)
    ]


def vtdot_vv(
    a: List[int],
    b: List[int],
    fmt: TakumFormat
) -> int:
    """
    Calcula o produto escalar com acumulação em IEEE Binary128.

    Os elementos Takum são decodificados, multiplicados e
    acumulados com precisão de 113 bits.

    O resultado é convertido para Takum somente ao final.
    """
    _check_vector_sizes(a, b)

    accumulator = mp.mpf(0)

    with mp.workprec(256):

        for x, y in zip(a, b):
            value_x = decode(x, fmt).value
            value_y = decode(y, fmt).value

            if value_x is None or value_y is None:
                raise ValueError(
                    "Não é possível calcular o produto escalar "
                    "com elementos NaR."
                )

            # Multiplicação em precisão ampliada.
            product = mp.mpf(value_x) * mp.mpf(value_y)

            # Quantiza o produto para Binary128.
            product = quantize_binary128([product])[0]

            # Acumula e quantiza novamente para Binary128.
            accumulator = quantize_binary128(
                [accumulator + product]
            )[0]

    # Converte o resultado para o formato Takum de destino.
    return encode(float(accumulator), fmt)
def vncvt_tt(
    values: List[int],
    source_fmt: Optional[TakumFormat] = None,
    target_fmt: Optional[TakumFormat] = None,
    *,
    source_width: Optional[int] = None,
    destination_width: Optional[int] = None,
) -> List[int]:
    """
    Converte um vetor entre formatos Takum.

    Aceita larguras inteiras (8, 16, 32) ou objetos TakumFormat.
    """

    if source_width is not None or destination_width is not None:
        if source_fmt is not None or target_fmt is not None:
            raise ValueError("Use objetos ou larguras, não ambos.")

        source_fmt = source_width
        target_fmt = destination_width

    if source_fmt is None or target_fmt is None:
        raise ValueError("Informe os formatos de origem e destino.")

    # Extrai a largura caso tenha recebido um objeto TakumFormat.
    source_width_value = (
        source_fmt.value if isinstance(source_fmt, TakumFormat)
        else source_fmt
    )

    target_width_value = (
        target_fmt.value if isinstance(target_fmt, TakumFormat)
        else target_fmt
    )

    if source_width_value not in (8, 16, 32):
        raise ValueError("Formato de origem inválido.")

    if target_width_value not in (8, 16, 32):
        raise ValueError("Formato de destino inválido.")

    converted = []

    for raw_value in values:
        decoded = decode(raw_value, source_width_value)

        if decoded.value is None:
            converted.append(TakumFormat(target_width_value).nar)
        else:
            converted.append(
                encode(decoded.value, target_width_value)
            )

    return converted