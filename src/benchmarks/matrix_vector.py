def csr_matvec(values, col_indices, row_ptr, vector):
    """Multiplicação matriz-vetor em formato CSR.

    values[k] é A[row, col_indices[k]]; row_ptr delimita cada linha.
    Esta função opera sobre números Python comuns e serve como baseline
    estrutural. A versão Takum deve substituir a soma/produto pela ALU.
    """
    if len(row_ptr) == 0 or row_ptr[0] != 0:
        raise ValueError("row_ptr deve começar em zero")
    if row_ptr[-1] != len(values) or len(values) != len(col_indices):
        raise ValueError("Estrutura CSR inconsistente")
    if any(row_ptr[i] > row_ptr[i+1] for i in range(len(row_ptr)-1)):
        raise ValueError("row_ptr deve ser não decrescente")
    out = []
    for row in range(len(row_ptr)-1):
        acc = 0.0
        for k in range(row_ptr[row], row_ptr[row+1]):
            col = col_indices[k]
            if not 0 <= col < len(vector):
                raise ValueError("Índice de coluna fora do vetor")
            acc += values[k] * vector[col]
        out.append(acc)
    return out
