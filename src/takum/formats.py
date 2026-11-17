
from dataclasses import dataclass
from enum import Enum


class TakumFormat(Enum):
    T8 = 8
    T16 = 16
    T32 = 32

    @property
    def width(self) -> int:
        return self.value


class TakumClass(Enum):
    ZERO = "zero"
    NAR = "nar"
    FINITE = "finite"


@dataclass(frozen=True)
class TakumFields:
    """
    Campos extraídos de uma representação Takum.

    sign:
        Bit de sinal S.

    direction:
        Bit de direção D.

    regime:
        Campo bruto R.

    characteristic:
        Campo C.

    fraction:
        Campo M.
    """
    sign: int
    direction: int
    regime: int
    characteristic: int
    fraction: int

    regime_width: int
    characteristic_width: int
    fraction_width: int


@dataclass(frozen=True)
class TakumValue:
    """
    Representação de um valor Takum decodificado.
    """
    classification: TakumClass
    value: float | None = None

    @staticmethod
    def zero() -> "TakumValue":
        return TakumValue(TakumClass.ZERO, 0.0)

    @staticmethod
    def nar() -> "TakumValue":
        return TakumValue(TakumClass.NAR, None)

    @staticmethod
    def finite(value: float) -> "TakumValue":
        return TakumValue(TakumClass.FINITE, float(value))

    def is_zero(self) -> bool:
        return self.classification == TakumClass.ZERO

    def is_nar(self) -> bool:
        return self.classification == TakumClass.NAR

    def is_finite(self) -> bool:
        return self.classification == TakumClass.FINITE

    def __float__(self) -> float:
        if self.is_nar():
            raise ValueError("NaR não pode ser convertido para float.")

        return float(self.value)


def validate_width(width: int) -> None:
    """
    Verifica se a largura corresponde a um formato suportado.
    """
    if width not in (8, 16, 32):
        raise ValueError(
            f"Largura inválida: {width}. "
            "Os formatos suportados são T8, T16 e T32."
        )


def mask_for_width(width: int) -> int:
    """
    Retorna uma máscara com 'width' bits ligados.
    """
    validate_width(width)
    return (1 << width) - 1


def sign_mask(width: int) -> int:
    """
    Retorna a máscara do bit mais significativo.
    """
    validate_width(width)
    return 1 << (width - 1)


def normalize_width(width: int | TakumFormat) -> int:
    """Converte um formato Takum ou uma largura para inteiro."""
    if isinstance(width, TakumFormat):
        width = width.value

    validate_width(width)
    return width

