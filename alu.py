import math
from takum import decode, encode


def t_add(a: int, b: int, n: int) -> int:
    """Soma dois takums de n bits e devolve o resultado como takum de n bits.

    Passos: (1) se um operando for NaR, o resultado é NaR; (2) decodifica
    os dois para float; (3) soma em float; (4) codifica o resultado,
    arredondando ao valor mais próximo (satura, nunca vira infinito).
    """
    nar = 1 << (n - 1)
    a &= (1 << n) - 1
    b &= (1 << n) - 1
    if a == nar or b == nar:                  # 1. NaR contamina o resultado
        return nar
    x = decode(a, n)                          # 2. bits -> float
    y = decode(b, n)
    return encode(x + y, n)                   # 3. soma  4. float -> bits


def t_sub(a: int, b: int, n: int) -> int:
    """Subtrai b de a (a - b), ambos takums de n bits, resultado em n bits.

    Mesmo esqueleto de t_add: trata NaR, decodifica, opera, codifica.
    """
    nar = 1 << (n - 1)
    a &= (1 << n) - 1
    b &= (1 << n) - 1
    if a == nar or b == nar:         # 1. NaR contamina o resultado
        return nar
    x = decode(a, n)                 # 2. bits -> float
    y = decode(b, n)
    return encode(x - y, n)          # 3. subtrai  4. float -> bits


def t_mul(a: int, b: int, n: int) -> int:
    """Multiplica dois takums de n bits e devolve o resultado em n bits.

    Mesmo esqueleto de t_add: trata NaR, decodifica, opera, codifica.
    Atenção à saturação: maior * maior deve dar o maior positivo, não NaR.
    """
    nar = 1 << (n - 1)
    a &= (1 << n) - 1
    b &= (1 << n) - 1
    if a == nar or b == nar:         # 1. NaR contamina o resultado
        return nar
    x = decode(a, n)                 # 2. bits -> float
    y = decode(b, n)
    return encode(x * y, n)          # 3. multiplica  4. float -> bits

def t_dot(va: list, vb: list, n: int) -> int:
    """Produto escalar de duas listas de takums de n bits.

    Soma os produtos va[i] * vb[i] em float (acumulador largo) e só no
    final codifica o total em n bits. Se qualquer elemento for NaR, o
    resultado é NaR. As listas devem ter o mesmo tamanho.
    """

    if len(va) != len(vb):
        raise ValueError("Erro, vetores de tamanhos diferentes")      # Não deixa dois vetores de tamanhos diferentes

    nar = 1 << (n - 1)
    mascara = (1 << n) - 1
    resultado = 0.0

    for i in range(len(va)):
        a = va[i] & mascara
        b = vb[i] & mascara

        if a == nar or b == nar:
            return nar                      # 1. NaR contamina o resultado

        x = decode(a, n)
        y = decode(b, n)

        resultado += x * y

    return encode(resultado, n)    


def t_cvt(bits: int, n_from: int, n_to: int) -> int:
    """Converte um takum de n_from bits para n_to bits (ex.: T16 -> T8).

    Decodifica com n_from e codifica com n_to. NaR continua NaR (com o
    padrão de NaR do formato novo) e zero continua zero.
    """

    nar_from = 1 << (n_from -1)
    nar_to = 1 << (n_to - 1)

    if bits == nar_from:
        return nar_to
    
    numero = decode(bits, n_from)
    numero_novo = encode(numero, n_to)
    return numero_novo