
import pytest

from takum import (
    CSRMatrix,
    spmv_reference,
    spmv_takum,
    decode_result,
)


def create_matrix():
    return CSRMatrix(
        values=[4.0, 5.0, 1.0, 3.0],
        col_indices=[0, 1, 0, 2],
        row_ptr=[0, 1, 2, 4],
        n_rows=3,
        n_cols=3,
    )


def test_csr_matrix_creation():
    matrix = create_matrix()

    assert matrix.n_rows == 3
    assert matrix.n_cols == 3
    assert matrix.nnz == 4


def test_csr_invalid_row_pointer():
    with pytest.raises(ValueError):
        CSRMatrix(
            values=[1.0],
            col_indices=[0],
            row_ptr=[0, 0],
            n_rows=2,
            n_cols=1,
        )


def test_spmv_reference():
    matrix = create_matrix()

    result = spmv_reference(
        matrix,
        [2.0, 3.0, 4.0],
    )

    assert result == [8.0, 15.0, 14.0]


def test_spmv_invalid_vector_size():
    matrix = create_matrix()

    with pytest.raises(ValueError):
        spmv_reference(matrix, [1.0, 2.0])


def test_spmv_takum():
    matrix = create_matrix()

    result, counters = spmv_takum(
        matrix,
        [2.0, 3.0, 4.0],
        16,
    )

    decoded = decode_result(result, 16)

    assert len(decoded) == 3
    assert counters["multiplications"] == 4
    assert counters["additions"] == 4
