# Takum-RVV — scaffold inicial

Projeto Integrador AOC/UFMG — 2026/02.

Este repositório é um **ponto de partida executável**, não uma implementação concluída do Takum-RVV.

## Decisão de escopo

O artigo preliminar do grupo descreve a variante **logarítmica (LNS)** do Takum. Este scaffold mantém essa escolha explícita. Não misture as equações da variante logarítmica com as da variante linear.

A referência formal principal para o codec é Hunhold, *Design and Implementation of a Takum Arithmetic Hardware Codec in VHDL*, arXiv:2408.10594. A definição distingue Takum logarítmico e linear. Antes de declarar T8/T16/T32 conformes, é necessário terminar a validação das regras de ghost bits e comparar com uma implementação de referência.

## O que já está implementado neste scaffold

- Estrutura modular Python.
- Tipos básicos e validação de largura.
- Decodificação da estrutura dos campos para larguras em que a partição `S|D|R|C|M` cabe sem ambiguidade.
- Representação interna de valor logarítmico.
- Interface inicial de ALU, simulador vetorial e benchmark.
- Testes iniciais e comandos de execução.

## O que NÃO está concluído

- Codificador Takum validado.
- Decodificação T8 para todos os regimes/ghost bits.
- Aritmética Takum arredondada corretamente para T8/T16/T32.
- Instruções Zvtakum integradas a um simulador RVV real.
- Referência Float128 e resultados experimentais finais.

As rotinas não concluídas lançam `NotImplementedError` intencionalmente. Não substitua isso por aproximações silenciosas: isso produziria resultados acadêmicos inválidos.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Testes

```bash
python -m pytest -q
```

## Próxima etapa recomendada

Validar, com a publicação formal e uma implementação de referência, a extensão da decodificação para T8 e os padrões especiais. Depois disso, implementar e testar o encoder antes da ALU.

## Estrutura

- `src/takum`: formato, decodificador e codificador.
- `src/arithmetic`: ALU.
- `src/vector`: abstração de registradores e instruções vetoriais.
- `src/benchmarks`: matriz-vetor e métricas.
- `experiments`: execução e gráficos.
- `tests`: testes unitários iniciais.
- `docs`: notas técnicas do projeto.
cat >> README.md <<'EOF'

---

# Experimental Evaluation

## 1. Overview

The project implements a software model of Takum arithmetic and a
simplified RISC-V Vector Extension (RVV) simulator.

The numerical evaluation compares the representation accuracy of:

- Takum T8
- Takum T16
- Takum T32
- IEEE 754 FP16
- IEEE 754 FP32

IEEE 754 Binary128 is used as the high-precision reference.

The current experiments evaluate numerical representation error.
They do not represent hardware execution time or actual RVV performance.

## 2. Running the Tests

Run the complete test suite from the project root:

```bash
PYTHONPATH=src python3 -m pytest tests/ -v