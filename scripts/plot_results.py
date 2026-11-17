import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

datasets = {
    "near_zero": "Próximos de zero",
    "moderate_values": "Valores moderados",
    "random_magnitudes": "Magnitudes variadas",
}

# Carrega os três conjuntos de resultados.
frames = []

for filename, label in datasets.items():
    file_path = RESULTS_DIR / f"{filename}.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    df = pd.read_csv(file_path)
    df["dataset_label"] = label
    frames.append(df)

data = pd.concat(frames, ignore_index=True)

# Define a ordem dos formatos.
format_order = [
    "Takum T8",
    "Takum T16",
    "Takum T32",
    "IEEE FP8 E4M3FN",
    "IEEE FP16",
    "IEEE FP32",
]
dataset_order = list(datasets.values())

# Gráfico 1: erro relativo médio.
pivot = data.pivot(
    index="format",
    columns="dataset_label",
    values="mean_relative_error",
).reindex(format_order)

pivot[dataset_order].plot(
    kind="bar",
    figsize=(12, 6),
    logy=True,
)

plt.title("Erro relativo médio por formato")
plt.ylabel("Erro relativo médio (escala logarítmica)")
plt.xlabel("Formato")
plt.xticks(rotation=0)
plt.legend(title="Conjunto de dados")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(FIGURES_DIR / "erro_relativo_medio.png", dpi=300)
plt.close()


# Gráfico 2: percentil 95 do erro relativo.
pivot = data.pivot(
    index="format",
    columns="dataset_label",
    values="p95_relative_error",
).reindex(format_order)

pivot[dataset_order].plot(
    kind="bar",
    figsize=(12, 6),
    logy=True,
)

plt.title("Percentil 95 do erro relativo por formato")
plt.ylabel("Erro relativo P95 (escala logarítmica)")
plt.xlabel("Formato")
plt.xticks(rotation=0)
plt.legend(title="Conjunto de dados")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(FIGURES_DIR / "erro_relativo_p95.png", dpi=300)
plt.close()


# Gráfico 3: MAE e RMSE por formato e conjunto.
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

for metric, axis, title in [
    ("mae", axes[0], "Erro absoluto médio (MAE)"),
    ("rmse", axes[1], "Raiz do erro quadrático médio (RMSE)"),
]:
    pivot = data.pivot(
        index="format",
        columns="dataset_label",
        values=metric,
    ).reindex(format_order)

    pivot[dataset_order].plot(
        kind="bar",
        ax=axis,
        logy=True,
    )

    axis.set_title(title)
    axis.set_ylabel("Erro absoluto (escala logarítmica)")
    axis.set_xlabel("Formato")
    axis.tick_params(axis="x", rotation=0)
    axis.grid(axis="y", alpha=0.3)

axes[1].legend(title="Conjunto de dados")
axes[0].get_legend().remove()

plt.suptitle("Comparação dos erros absolutos — referência Binary128")
plt.tight_layout()
plt.savefig(FIGURES_DIR / "erros_absolutos.png", dpi=300)
plt.close()


# Gráfico 4: erros da multiplicação matriz-vetor esparsa.
sparse_file = RESULTS_DIR / "sparse_spmv_summary.csv"

if not sparse_file.exists():
    raise FileNotFoundError(f"Arquivo não encontrado: {sparse_file}")

sparse_data = pd.read_csv(sparse_file)

sparse_order = ["Takum T8", "Takum T16", "Takum T32"]
sparse_data = (
    sparse_data.set_index("format")
    .reindex(sparse_order)
)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

sparse_data[["mae", "rmse"]].plot(
    kind="bar",
    ax=axes[0],
    logy=True,
)

axes[0].set_title("Erros absolutos — SpMV")
axes[0].set_ylabel("Erro (escala logarítmica)")
axes[0].set_xlabel("Formato")
axes[0].tick_params(axis="x", rotation=0)
axes[0].grid(axis="y", alpha=0.3)

sparse_data[["mean_relative_error"]].plot(
    kind="bar",
    ax=axes[1],
    logy=True,
    legend=False,
)

axes[1].set_title("Erro relativo médio — SpMV")
axes[1].set_ylabel("Erro relativo (escala logarítmica)")
axes[1].set_xlabel("Formato")
axes[1].tick_params(axis="x", rotation=0)
axes[1].grid(axis="y", alpha=0.3)

plt.suptitle("Avaliação da multiplicação matriz-vetor esparsa")
plt.tight_layout()
plt.savefig(
    FIGURES_DIR / "sparse_spmv_erros.png",
    dpi=300,
)
plt.close()


print("Gráficos gerados com sucesso:")
for filename in [
    "erro_relativo_medio.png",
    "erro_relativo_p95.png",
    "erros_absolutos.png",
]:
    print(FIGURES_DIR / filename)