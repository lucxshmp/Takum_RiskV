import math

def split_fields(bits: int, n: int) -> tuple:
    """Separa um takum de n bits nos campos S, D, R, r, C, F e p.

    Layout (bit mais significativo à esquerda):

        | S | D |  R  |   C   |      F      |
        | 1 | 1 |  3  |   r   |  L - 5 - r  |
    
    - S: sinal (0 = positivo, 1 = negativo)
    - D: direção (1 = valor >= 1, 0 = valor < 1)
    - R: regime, 3 bits (0 a 7); diz quantos bits tem C
    - r: número de bits de C. Se D == 1, r = R; se D == 0, r = 7 - R
    - C: característica (parte do expoente), r bits
    - F: fração, p bits (o valor da fração é F / 2**p)
    - p: número de bits de F

    Para n < 12 (caso do T8) o padrão é completado com zeros à direita
    até 12 bits, porque C pode ter até 7 bits e não caberia. Esses zeros
    valem como bits implícitos de C e F. Por isso p é medido sobre L bits.

    Args:
        bits: padrão de bits como inteiro (ex.: 0x5740).
        n: largura do formato (8, 16 ou 32).

    Returns:
        (S, D, R, r, C, F, p), todos inteiros.

    Atenção: não trata zero (todos os bits 0) nem NaR (só o bit mais
    alto em 1). Quem chama deve tratar esses dois casos antes.
    """
    # 1. Garante que só os n bits de baixo são usados.
    bits &= (1 << n) - 1

    # 2. Completa com zeros à direita até 12 bits, se necessário.
    #    L é a largura "efetiva" usada em todas as posições abaixo.
    L = max(n, 12)
    b = bits << (L - n)          # para n >= 12, L - n = 0 e nada muda

    # 3. Campos fixos: padrão (b >> posição) & máscara.
    S = (b >> (L - 1)) & 0b1     # bit mais alto
    D = (b >> (L - 2)) & 0b1     # segundo bit
    R = (b >> (L - 5)) & 0b111   # 3 bits seguintes

    # 4. r depende de D e R, então vem antes de C e F.
    r = R if D == 1 else 7 - R

    # 5. Campos variáveis: C tem r bits, F ocupa o resto.
    p = L - 5 - r                # bits de F (sempre >= 0, pois L >= 12)
    C = (b >> p) & ((1 << r) - 1)
    F = b & ((1 << p) - 1)

    return S, D, R, r, C, F, p

def decode(bits: int, n: int) -> float:
    """Converte um takum linear de n bits (8, 16 ou 32) em float.

    Passos:
    1. zero e NaR são casos especiais (tratados antes de tudo);
    2. split_fields separa S, D, R, r, C, F, p;
    3. c (característica) depende de D;
      4. valor = (1 - 3*S + f) * 2**((-1)**S * (c + S)),  com f = F / 2**p.

    Retorna 0.0 para o padrão todo zero e math.nan para NaR
    (só o bit mais alto em 1).
    """
    bits &= (1 << n) - 1
    if bits == 0:
        return 0.0
    if bits == 1 << (n - 1):
        return math.nan                       # NaR

    S, D, R, r, C, F, p = split_fields(bits, n)

    # Característica: D = 1 -> c >= 0 ; D = 0 -> c < 0
    if D == 1:
        c = (1 << r) - 1 + C
    else:
        c = -(1 << (r + 1)) + 1 + C

    f = F / (1 << p)                          # fração em [0, 1), exata em float
    expoente = (c + S) * (-1) ** S
    return math.ldexp(1 - 3 * S + f, expoente)   # (1-3S+f) * 2**expoente


def _encode_positivo(a: float, n: int) -> int:
    """Codifica a > 0 (finito) como padrão de n bits com S = 0.

    Arredonda para o valor representável mais próximo (empate: padrão par)
    e satura: nunca produz zero, NaR nem overflow.
    """
    PADRAO_MAX = (1 << (n - 1)) - 1           # maior positivo: 0111...1
    PADRAO_MIN = 1                            # menor positivo: 000...01

    # 1. a = (1 + f) * 2**c, com M inteiro de 53 bits: 1 + f = M / 2**52
    m, e = math.frexp(a)                      # a = m * 2**e, m em [0.5, 1)
    M = int(m * (1 << 53))                    # exato
    c = e - 1
    if c > 254:
        return PADRAO_MAX                     # c máximo do formato é 254
    if c < -255:
        return PADRAO_MIN                     # c mínimo do formato é -255

    # 2. Inverso do passo "c a partir de D, r, C": acha D, r, C e R.
    if c >= 0:
        D = 1
        r = (c + 1).bit_length() - 1          # floor(log2(c + 1))
        C = c - ((1 << r) - 1)
        R = r
    else:
        D = 0
        r = (-c).bit_length() - 1             # floor(log2(-c))
        C = c + (1 << (r + 1)) - 1
        R = 7 - r

    # 3. Monta o padrão em L bits (L = max(n, 12)) com a fração truncada,
    #    em aritmética de inteiros para não perder bits.
    L = max(n, 12)
    p = L - 5 - r                             # bits de F nessa largura
    prefixo = (((D << 3) | R) << r) | C       # D, R, C colados (sem S)
    # valor "contínuo" do padrão = prefixo*2**p + f*2**p, f = (M - 2**52)/2**52
    N = (prefixo << (p + 52)) + ((M - (1 << 52)) << p)
    # joga fora os L-n bits extras (T8) e os 52 bits de precisão
    inferior = N >> (52 + L - n)              # padrão truncado (piso)
    superior = inferior + 1

    # 4. Escolhe o mais próximo em valor; empate -> padrão par.
    if inferior == 0:
        return PADRAO_MIN
    if superior > PADRAO_MAX:
        return PADRAO_MAX
    d_inf = a - decode(inferior, n)
    d_sup = decode(superior, n) - a
    if d_inf < d_sup:
        return inferior
    if d_sup < d_inf:
        return superior
    return inferior if inferior % 2 == 0 else superior


def encode(x: float, n: int) -> int:
    """Converte um float em takum linear de n bits (8, 16 ou 32).

    - nan e infinitos viram NaR;
    - 0.0 vira 0;
    - fora do alcance satura (nunca vira infinito nem zero);
    - negativos: o padrão é o complemento de dois do padrão do positivo.
    """
    if math.isnan(x) or math.isinf(x):
        return 1 << (n - 1)                   # NaR
    if x == 0:
        return 0
    pos = _encode_positivo(abs(x), n)
    if x < 0:
        return (-pos) & ((1 << n) - 1)        # complemento de dois
    return pos
