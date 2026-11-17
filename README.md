# Takum-RVV

**Projeto Integrador — Arquitetura e Organização de Computadores (AOC/UFMG) — 2026/02**

Simulador funcional em Python da aritmética **Takum logarítmica** (T8, T16 e T32) e de uma extensão vetorial experimental para RISC-V, a **Zvtakum**. O projeto compara o erro numérico do Takum com FP8 (E4M3FN), FP16 e FP32, sempre usando Binary128 como referência, e executa uma multiplicação matriz–vetor esparsa (SpMV) em formato CSR.

> **Escopo.** Os resultados são de simulação em software. Os tempos medidos são de Python, e não de hardware; não há medição de ciclos, área ou energia. As instruções Zvtakum são uma proposta do grupo e não fazem parte da especificação RVV.

## Variante adotada

Usa-se a variante **logarítmica (LNS)** do Takum, conforme Hunhold, *Design and Implementation of a Takum Arithmetic Hardware Codec in VHDL* (arXiv:2408.10594). Não misture as equações das variantes logarítmica e linear. Para larguras menores que 12 bits (T8), a palavra é completada com *ghost bits* antes da extração dos campos.

### Limitação conhecida do decodificador

O decodificador calcula a magnitude como `exp(ℓ/e)`, enquanto a definição formal prevê `(√e)^ℓ = exp(ℓ/2)`. A estrutura dos campos (`S|D|R|C|M`) é a mesma, mas os valores **não coincidem bit a bit** com a referência de Hunhold. Os erros e a faixa dinâmica reportados referem-se ao codec como implementado. Além disso, o codificador arredonda para o valor mais próximo no domínio real e pode devolver zero, enquanto o codec de referência nunca converte um valor não nulo em zero.

## Estrutura

```text
src/takum/
  formats.py     tipos, larguras, classes (zero, NaR, finito)
  decoder.py     decodificador Takum LNS
  encoder.py     codificador (busca exaustiva, escolhida por ser simples de verificar)
  alu.py         soma, subtração, multiplicação e divisão (um arredondamento por operação)
  vector.py      vtadd.vv, vtsub.vv, vtmul.vv, vtdot.vv, vncvt.t.t
  simulator.py   VectorMachine: 32 registradores, VL <= 256, SEW em {8, 16, 32}, contador de instruções
  csr.py         matriz CSR e SpMV (referência Binary128 e versão Takum)
  metrics.py     métricas de erro e conversão para FP8/FP16/FP32/Binary128
  benchmark.py   benchmark das instruções vetoriais
src/examples/    exemplo de uso das instruções vetoriais
scripts/         experimentos e gráficos
results/         CSVs gerados e results/figures/
tests/           testes unitários
```

## Instruções Zvtakum

| Instrução | Operação | RVV equivalente |
|---|---|---|
| `vtadd.vv` | soma elemento a elemento | `vfadd.vv` |
| `vtsub.vv` | subtração elemento a elemento | `vfsub.vv` |
| `vtmul.vv` | multiplicação elemento a elemento | `vfmul.vv` |
| `vtdot.vv` | produto escalar, com acúmulo em Binary128 | `vfdot.*` |
| `vncvt.t.t` | redução de largura (por exemplo T16 → T8) | `vfncvt.*` |

O SEW escolhe o formato (8 → T8, 16 → T16, 32 → T32). Cada registrador lembra a largura do que guarda, e operações com larguras incompatíveis são recusadas.

## Instalação

```bash
git clone https://github.com/lucxshmp/Takum_RiskV.git
cd Takum_RiskV
python3 -m venv .venv
source .venv/bin/activate        # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Testes

O `pytest.ini` já configura `pythonpath = src`, então basta, a partir da raiz:

```bash
python -m pytest -q
```

## Experimentos

Todos os comandos rodam a partir da raiz e gravam em `results/`:

```bash
python scripts/run_format_comparison.py   # precisão: near_zero, moderate_values, random_magnitudes
python scripts/run_vector_benchmark.py    # benchmark vetorial (VL=8, T8/T16/T32)
python scripts/run_sparse_benchmark.py    # SpMV 128x128, 5% de densidade, semente 42
python scripts/plot_results.py            # gera results/figures/*.png (requer pandas)
```

Conjuntos de 1000 valores com semente fixa: `near_zero` (uniforme em ±1e-10, semente 42), `moderate_values` (uniforme em ±100, semente 43) e `random_magnitudes` (`m·10^k`, `k` inteiro em [-10, 10], semente 44). Se algum formato produz NaN ou infinito para uma amostra, ela é excluída de todos os formatos. No conjunto `random_magnitudes` isso remove as amostras com |x| > 448 (limite do FP8 E4M3FN), de modo que a comparação cobre cerca de 15 ordens de grandeza, e não as 21 do gerador.

### Erro relativo médio (referência Binary128)

| Formato | Próximos de zero | Moderados | Magnitudes variadas |
|---|---|---|---|
| Takum T8 | 4,9e-1 | 8,4e-2 | 2,3e-1 |
| Takum T16 | 2,7e-3 | 3,3e-4 | 9,8e-4 |
| Takum T32 | 4,0e-8 | 5,1e-9 | 1,5e-8 |
| FP8 E4M3FN | 1,0 | 2,3e-2 | 6,0e-1 |
| FP16 | 1,0 | 1,7e-4 | 2,8e-1 |
| FP32 | 2,1e-8 | 2,1e-8 | 2,1e-8 |

Para valores muito pequenos, FP8 e FP16 perdem toda a informação; para magnitudes moderadas, FP8 e FP16 têm menor erro que T8 e T16.

## Limitações

- O decodificador usa `exp(ℓ/e)` (ver acima), e os testes comparam com uma referência que usa as mesmas equações: eles mostram consistência interna, não equivalência com o VHDL de Hunhold.
- A ALU opera em ponto flutuante de 64 bits e arredonda ao final; não foi validada contra RTL.
- A SpMV foi avaliada só em Takum, acumula em Takum (não usa `vtdot.vv`) e não roda no `VectorMachine`.
- Uma única matriz (semente 42) e uma repetição no benchmark vetorial, sem barras de erro nos tempos.

## Referências

- L. Hunhold, *Design and Implementation of a Takum Arithmetic Hardware Codec in VHDL*, arXiv:2408.10594.
- L. Hunhold, *Beating Posits at Their Own Game: Takum Arithmetic*, CoNGA 2024.
- IEEE Std 754-2008, *IEEE Standard for Floating-Point Arithmetic*.
