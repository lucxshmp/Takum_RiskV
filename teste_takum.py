"""Testes de split_fields, decode e encode (T8, T16, T32).

Coloque este arquivo na mesma pasta de split.py e takum.py e rode:
    python test_takum.py            (ou: python -m unittest -v test_takum)

Se você colou split_fields dentro de takum.py, troque o import abaixo por:
    from takum import split_fields, decode, encode
"""
import bisect
import math
import random
import unittest

from takum import decode, encode, split_fields

NAR = {8: 0x80, 16: 0x8000, 32: 0x80000000}


def todos_padroes(n):
    """Todos os padrões válidos de T8/T16 (sem zero e sem NaR)."""
    return [i for i in range(1, 1 << n) if i != 1 << (n - 1)]


def tabela_oraculo(n):
    """Gabarito de força bruta: valores ordenados e seus padrões (T8/T16)."""
    itens = sorted((decode(i, n), i) for i in range(1 << n) if i != 1 << (n - 1))
    return [v for v, _ in itens], [b for _, b in itens]


def encode_oraculo(x, T):
    """Valor mais próximo na tabela; empate -> padrão par."""
    vals, bits = T
    k = bisect.bisect_left(vals, x)
    if k == 0:
        return bits[0]
    if k == len(vals):
        return bits[-1]
    lo, hi = vals[k - 1], vals[k]
    if lo == 0:
        return bits[k]
    if hi == 0:
        return bits[k - 1]
    if x - lo < hi - x:
        return bits[k - 1]
    if x - lo > hi - x:
        return bits[k]
    return bits[k - 1] if bits[k - 1] % 2 == 0 else bits[k]


class TestSplitFields(unittest.TestCase):
    def test_exemplos_a_mao(self):
        self.assertEqual(split_fields(0x5740, 16), (0, 1, 2, 2, 3, 320, 9))
        self.assertEqual(split_fields(0x56, 8), (0, 1, 2, 2, 3, 0, 5))
        self.assertEqual(split_fields(0x40, 8), (0, 1, 0, 0, 0, 0, 7))
        self.assertEqual(split_fields(0x40000000, 32), (0, 1, 0, 0, 0, 0, 27))

    def test_tamanhos_dos_campos(self):
        """p = max(n,12) - 5 - r e 0 <= r <= 7 para todo padrão."""
        for n in (8, 16):
            L = max(n, 12)
            for i in todos_padroes(n):
                S, D, R, r, C, F, p = split_fields(i, n)
                self.assertIn(S, (0, 1))
                self.assertIn(D, (0, 1))
                self.assertTrue(0 <= R <= 7)
                self.assertEqual(r, R if D else 7 - R)
                self.assertEqual(p, L - 5 - r)
                self.assertTrue(0 <= C < (1 << r) or r == 0 and C == 0)
                self.assertTrue(0 <= F < (1 << p))

    def test_entrada_mascarada(self):
        self.assertEqual(split_fields(0x15740, 16), split_fields(0x5740, 16))


class TestDecode(unittest.TestCase):
    def test_valores_conhecidos(self):
        self.assertEqual(decode(0x0000, 16), 0.0)
        self.assertEqual(decode(0x4000, 16), 1.0)
        self.assertEqual(decode(0x3800, 16), 0.5)
        self.assertEqual(decode(0x5740, 16), 104.0)
        self.assertEqual(decode(0xC000, 16), -1.0)
        self.assertEqual(decode(0x40, 8), 1.0)
        self.assertEqual(decode(0x56, 8), 64.0)
        self.assertEqual(decode(0x40000000, 32), 1.0)

    def test_nar(self):
        for n, nar in NAR.items():
            self.assertTrue(math.isnan(decode(nar, n)))

    def test_ordem_igual_ao_complemento_de_dois(self):
        """Lidos como inteiros com sinal, os padrões saem em ordem crescente."""
        for n in (8, 16):
            seq = sorted(
                (i - (1 << n) if i >= 1 << (n - 1) else i, decode(i, n))
                for i in range(1 << n) if i != 1 << (n - 1)
            )
            self.assertTrue(all(seq[k][1] < seq[k + 1][1] for k in range(len(seq) - 1)))

    def test_negacao_e_complemento_de_dois(self):
        for n in (8, 16):
            for i in range(1, 1 << (n - 1)):
                neg = (-i) & ((1 << n) - 1)
                self.assertEqual(decode(neg, n), -decode(i, n))

    def test_alcance_dinamico(self):
        self.assertAlmostEqual(decode(0x7F, 8) / 8.834235323891922e71, 1.0)
        self.assertAlmostEqual(decode(0x01, 8) / 1.131959884853339e-72, 1.0)
        self.assertAlmostEqual(decode(0x7FFF, 16) / 5.608679322432503e76, 1.0)
        self.assertAlmostEqual(decode(0x0001, 16) / 1.8351858179575695e-77, 1.0)


class TestEncode(unittest.TestCase):
    def test_exemplos(self):
        self.assertEqual(encode(104.0, 16), 0x5740)
        self.assertEqual(encode(1.0, 32), 0x40000000)
        self.assertEqual(encode(-1.0, 8), 0xC0)
        self.assertEqual(encode(1.0, 8), 0x40)

    def test_especiais(self):
        for n, nar in NAR.items():
            self.assertEqual(encode(0.0, n), 0)
            self.assertEqual(encode(-0.0, n), 0)
            self.assertEqual(encode(math.nan, n), nar)
            self.assertEqual(encode(math.inf, n), nar)
            self.assertEqual(encode(-math.inf, n), nar)

    def test_saturacao(self):
        for n in (8, 16, 32):
            maximo = (1 << (n - 1)) - 1
            self.assertEqual(encode(1e300, n), maximo)
            self.assertEqual(encode(-1e300, n), (-maximo) & ((1 << n) - 1))
            self.assertEqual(encode(1e-300, n), 1)          # nunca vira zero
            self.assertEqual(encode(-1e-300, n), (1 << n) - 1)

    def test_ida_e_volta_t8_t16(self):
        for n in (8, 16):
            for i in todos_padroes(n):
                self.assertEqual(encode(decode(i, n), n), i, hex(i))

    def test_ida_e_volta_t32_aleatorio(self):
        rnd = random.Random(7)
        casos = [1, 2, 0x7FFFFFFF, 0x7FFFFFFE, 0x40000000, 0xC0000000, 0x80000001, 0xFFFFFFFF]
        casos += [rnd.getrandbits(32) for _ in range(100000)]
        for i in casos:
            if i in (0, 1 << 31):
                continue
            self.assertEqual(encode(decode(i, 32), 32), i, hex(i))

    def test_contra_oraculo_t8_t16(self):
        rnd = random.Random(1)
        for n in (8, 16):
            T = tabela_oraculo(n)
            for _ in range(50000):
                x = rnd.choice([1, -1]) * math.exp(rnd.uniform(-180, 180))
                self.assertEqual(encode(x, n), encode_oraculo(x, T), x)

    def test_empates_exatos(self):
        """Ponto médio entre dois vizinhos: deve ir para o padrão par."""
        for n in (8, 16):
            T = tabela_oraculo(n)
            vals = T[0]
            passo = max(1, len(vals) // 2000)
            for k in range(1, len(vals) - 1, passo):
                if vals[k] > 0 and vals[k + 1] > 0:
                    meio = (vals[k] + vals[k + 1]) / 2
                    self.assertEqual(encode(meio, n), encode_oraculo(meio, T), meio)

    def test_mais_proximo_t32(self):
        rnd = random.Random(3)
        for _ in range(30000):
            x = rnd.choice([1, -1]) * math.exp(rnd.uniform(-150, 150))
            p = encode(x, 32)
            vizinhos = [(p + d) & 0xFFFFFFFF for d in (-1, 0, 1)]
            vizinhos = [v for v in vizinhos if v != 1 << 31]
            melhor = min(abs(decode(v, 32) - x) for v in vizinhos)
            self.assertLessEqual(abs(decode(p, 32) - x), melhor, x)


if __name__ == "__main__":
    unittest.main(verbosity=2)