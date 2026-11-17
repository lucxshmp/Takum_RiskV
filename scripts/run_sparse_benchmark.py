
import csv
import math
import random
import sys
from pathlib import Path

import mpmath as mp

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from takum.csr import CSRMatrix, spmv_takum, decode_result
from takum.metrics import calculate_high_precision_metrics
from takum.metrics import quantize_binary128


SEED = 42
N = 128
DENSITY = 0.05
WIDTHS = [8, 16, 32]

OUTPUT_DIR = PROJECT_ROOT / "results"
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_sparse_matrix(n, density, seed):
    rng = random.Random(seed)

    values = []
    col_indices = []
    row_ptr = [0]

    for row in range(n):
        for col in range(n):
            if rng.random() < density:
                values.append(rng.uniform(-10.0, 10.0))
                col_indices.append(col)

        row_ptr.append(len(values))

    return CSRMatrix(
        values=values,
        col_indices=col_indices,
        row_ptr=row_ptr,
        n_rows=n,
        n_cols=n,
    )


def binary128_spmv(matrix, vector):
    matrix_values = quantize_binary128(matrix.values)
    vector_values = quantize_binary128(vector)

    result = []

    with mp.workprec(256):
        for row in range(matrix.n_rows):
            accumulator = mp.mpf(0)

            start = matrix.row_ptr[row]
            end = matrix.row_ptr[row + 1]

            for index in range(start, end):
                col = matrix.col_indices[index]

                product = quantize_binary128([
                    matrix_values[index] * vector_values[col]
                ])[0]

                accumulator = quantize_binary128([
                    accumulator + product
                ])[0]

            result.append(accumulator)

    return result


def save_results(matrix, reference, vector):
    summary_path = OUTPUT_DIR / "sparse_spmv_summary.csv"
    errors_path = OUTPUT_DIR / "sparse_spmv_errors.csv"

    summary_rows = []
    error_rows = []

    for width in WIDTHS:
        encoded_result, counters = spmv_takum(
            matrix,
            vector,
            width,
        )

        decoded_result = decode_result(encoded_result, width)

        metrics = calculate_high_precision_metrics(
            reference,
            decoded_result,
        )

        summary_rows.append({
            "format": f"Takum T{width}",
            "matrix_rows": matrix.n_rows,
            "matrix_cols": matrix.n_cols,
            "nonzero_elements": matrix.nnz,
            "density": DENSITY,
            "multiplications": counters["multiplications"],
            "additions": counters["additions"],
            **metrics,
        })

        for row, (ref, measured) in enumerate(
            zip(reference, decoded_result)
        ):
            finite = (
                mp.isfinite(ref)
                and math.isfinite(measured)
            )

            if finite:
                absolute_error = abs(ref - mp.mpf(str(measured)))
                relative_error = (
                    absolute_error / abs(ref)
                    if ref != 0 else None
                )
            else:
                absolute_error = None
                relative_error = None

            error_rows.append({
                "format": f"Takum T{width}",
                "row": row,
                "reference_binary128": str(ref),
                "takum_result": measured,
                "absolute_error": (
                    str(absolute_error)
                    if absolute_error is not None else ""
                ),
                "relative_error": (
                    str(relative_error)
                    if relative_error is not None else ""
                ),
            })

    with summary_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=summary_rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    with errors_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=error_rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(error_rows)

    print("\nResultados:")
    for row in summary_rows:
        print(
            f"{row['format']}: "
            f"MAE={row['mae']:.8e}, "
            f"RMSE={row['rmse']:.8e}, "
            f"erro relativo médio="
            f"{row['mean_relative_error']:.8e}"
        )

    print(f"\nArquivos gerados:")
    print(summary_path)
    print(errors_path)


def main():
    rng = random.Random(SEED)

    matrix = generate_sparse_matrix(
        N,
        DENSITY,
        SEED,
    )

    vector = [
        rng.uniform(-1.0, 1.0)
        for _ in range(N)
    ]

    print("Experimento de multiplicação matriz-vetor esparsa")
    print(f"Dimensões: {N} x {N}")
    print(f"Densidade: {DENSITY}")
    print(f"Elementos não nulos: {matrix.nnz}")

    reference = binary128_spmv(matrix, vector)

    save_results(matrix, reference, vector)


if __name__ == "__main__":
    main()
