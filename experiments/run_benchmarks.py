"""Ponto de entrada para os experimentos.

A execução completa Takum será habilitada após encoder/ALU validados.
"""
from pathlib import Path
import json
import numpy as np
from src.benchmarks.matrix_vector import csr_matvec
from src.benchmarks.metrics import error_metrics

def main():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    cols = [0, 2, 1, 0, 2]
    row_ptr = [0, 2, 3, 5]
    x = [1.0, 2.0, 3.0]
    y = csr_matvec(values, cols, row_ptr, x)
    ref = np.asarray(y, dtype=np.longdouble).tolist()
    metrics = error_metrics(ref, y)
    output = {"baseline_float": y, "baseline_metrics": metrics,
              "note": "Takum/IEEE comparison awaits validated codec and ALU."}
    out = Path(__file__).parent / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "baseline.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
