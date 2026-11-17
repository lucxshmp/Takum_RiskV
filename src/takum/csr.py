
from dataclasses import dataclass

from .alu import takum_add, takum_mul
from .decoder import decode
from .encoder import encode
from .formats import TakumClass, validate_width


@dataclass
class CSRMatrix:
    """
    Representação de uma matriz esparsa no formato CSR.
    """

    values: list[float]
    col_indices: list[int]
    row_ptr: list[int]
    n_rows: int
    n_cols: int

    def __post_init__(self):
        if self.n_rows < 0 or self.n_cols < 0:
            raise ValueError("Dimensões da matriz inválidas.")

        if len(self.values) != len(self.col_indices):
            raise ValueError(
                "values e col_indices devem possuir o mesmo tamanho."
            )

        if len(self.row_ptr) != self.n_rows + 1:
            raise ValueError(
                "row_ptr deve possuir n_rows + 1 elementos."
            )

        if not self.row_ptr or self.row_ptr[0] != 0:
            raise ValueError("row_ptr deve começar em zero.")

        if self.row_ptr[-1] != len(self.values):
            raise ValueError(
                "O último elemento de row_ptr deve indicar "
                "o total de elementos não nulos."
            )

        if any(
            self.row_ptr[i] > self.row_ptr[i + 1]
            for i in range(self.n_rows)
        ):
            raise ValueError("row_ptr deve ser não decrescente.")

        if any(
            col < 0 or col >= self.n_cols
            for col in self.col_indices
        ):
            raise ValueError("Índice de coluna fora dos limites.")

        for row in range(self.n_rows):
            start = self.row_ptr[row]
            end = self.row_ptr[row + 1]

            columns = self.col_indices[start:end]

            if columns != sorted(columns):
                raise ValueError(
                    f"Índices da linha {row} não estão ordenados."
                )

            if len(columns) != len(set(columns)):
                raise ValueError(
                    f"Existem colunas duplicadas na linha {row}."
                )

    @property
    def nnz(self) -> int:
        """Quantidade de elementos não nulos."""
        return len(self.values)


def spmv_reference(
    matrix: CSRMatrix,
    vector: list[float]
) -> list[float]:
    """
    Multiplicação matriz-vetor usando aritmética Python.

    y = A * x
    """
    if len(vector) != matrix.n_cols:
        raise ValueError(
            "O tamanho do vetor não corresponde "
            "ao número de colunas da matriz."
        )

    result = []

    for row in range(matrix.n_rows):
        accumulator = 0.0

        start = matrix.row_ptr[row]
        end = matrix.row_ptr[row + 1]

        for index in range(start, end):
            column = matrix.col_indices[index]

            accumulator += (
                matrix.values[index] * vector[column]
            )

        result.append(accumulator)

    return result


def spmv_takum(
    matrix: CSRMatrix,
    vector: list[float],
    width: int
) -> tuple[list[int], dict[str, int]]:
    """
    Multiplicação matriz-vetor usando operações Takum.

    Cada elemento da matriz e do vetor é codificado no formato
    escolhido. A multiplicação e a acumulação são realizadas
    por meio das operações da ALU Takum.

    Retorna:
        vetor de saída codificado;
        contadores de operações.
    """
    validate_width(width)

    if len(vector) != matrix.n_cols:
        raise ValueError(
            "O tamanho do vetor não corresponde "
            "ao número de colunas da matriz."
        )

    encoded_vector = [
        encode(value, width)
        for value in vector
    ]

    result = []

    counters = {
        "multiplications": 0,
        "additions": 0,
        "nonzero_elements": matrix.nnz,
    }

    zero = encode(0.0, width)

    for row in range(matrix.n_rows):
        accumulator = zero

        start = matrix.row_ptr[row]
        end = matrix.row_ptr[row + 1]

        for index in range(start, end):
            column = matrix.col_indices[index]

            encoded_matrix_value = encode(
                matrix.values[index],
                width
            )

            product = takum_mul(
                encoded_matrix_value,
                encoded_vector[column],
                width
            )

            accumulator = takum_add(
                accumulator,
                product,
                width
            )

            counters["multiplications"] += 1
            counters["additions"] += 1

        result.append(accumulator)

    return result, counters


def decode_result(
    vector: list[int],
    width: int
) -> list[float]:
    """Converte um vetor Takum para números reais."""
    decoded = []

    for raw in vector:
        value = decode(raw, width)

        if value.classification == TakumClass.NAR:
            decoded.append(float("nan"))
        else:
            decoded.append(value.value)

    return decoded
