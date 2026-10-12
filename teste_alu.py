"""Testes de t_add, t_sub, t_mul, t_dot e t_cvt.

Coloque na mesma pasta de split.py, takum.py e alu.py e rode:
    python test_alu.py
"""
import math
import random
import unittest

from takum import decode, encode
from alu import t_add, t_sub, t_mul, t_dot, t_cvt

NAR = {8: 0x80, 16: 0x8000, 32: 0x80000000}
OPS = {
    "add": (t_add, lambda x, y: x + y),
    "sub": (t_sub, lambda x, y: x - y),
    "mul": (t_mul, lambda x, y: x * y),
}


def padroes_aleatorios(n, qtd, seed):
    rnd = random.Random(seed)
    return [rnd.getrandbits(n) for _ in range(qtd) if True]


class TestAritmeticaBasica(unittest.TestCase):
    def test_valores_a_mao(self):
        for n in (8, 16, 32):
            e = lambda v: encode(v, n)
            d = lambda b: decode(b, n)
            self.assertEqual(d(t_add(e(1), e(2), n)), 3.0)
            self.assertEqual(d(t_sub(e(3), e(1), n)), 2.0)
            self.assertEqual(d(t_sub(e(1), e(1), n)), 0.0)
            self.assertEqual(d(t_mul(e(2), e(2), n)), 4.0)
            self.assertEqual(d(t_mul(e(0.5), e(4), n)), 2.0)
            self.assertEqual(d(t_mul(e(-2), e(3), n)), -6.0)

    def test_sub_nao_e_comutativa(self):
        for n in (8, 16, 32):
            um, dois = encode(1, n), encode(2, n)
            self.assertEqual(decode(t_sub(um, dois, n), n), -1.0)
            self.assertEqual(decode(t_sub(dois, um, n), n), 1.0)

    def test_comutatividade(self):
        for n in (8, 16, 32):
            for a, b in zip(padroes_aleatorios(n, 3000, 1), padroes_aleatorios(n, 3000, 2)):
                self.assertEqual(t_add(a, b, n), t_add(b, a, n))
                self.assertEqual(t_mul(a, b, n), t_mul(b, a, n))

    def test_identidades(self):
        for n in (8, 16, 32):
            um, zero = encode(1, n), 0
            for a in padroes_aleatorios(n, 3000, 3):
                if a == NAR[n]:
                    continue
                self.assertEqual(t_add(a, zero, n), a)
                self.assertEqual(t_mul(a, um, n), a)
                self.assertEqual(t_sub(a, a, n), 0)
                self.assertEqual(t_mul(a, zero, n), 0)

    def test_nar_propaga(self):
        for n in (8, 16, 32):
            nar, um = NAR[n], encode(1, n)
            for f in (t_add, t_sub, t_mul):
                self.assertEqual(f(nar, um, n), nar)
                self.assertEqual(f(um, nar, n), nar)
                self.assertEqual(f(nar, nar, n), nar)

    def test_saturacao_e_underflow(self):
        for n in (8, 16, 32):
            maximo = (1 << (n - 1)) - 1
            neg_max = (-maximo) & ((1 << n) - 1)
            self.assertEqual(t_mul(maximo, maximo, n), maximo)      # nunca NaR
            self.assertEqual(t_mul(maximo, neg_max, n), neg_max)
            self.assertEqual(t_add(maximo, maximo, n), maximo)
            self.assertEqual(t_sub(neg_max, maximo, n), neg_max)
            self.assertEqual(t_mul(1, 1, n), 1)                     # nunca zero

    def test_t8_exaustivo_contra_formula(self):
        """Todos os 65 536 pares de T8, nas três operações."""
        n = 8
        for nome, (f, op) in OPS.items():
            for a in range(256):
                for b in range(256):
                    if a == 0x80 or b == 0x80:
                        esperado = 0x80
                    else:
                        esperado = encode(op(decode(a, n), decode(b, n)), n)
                    self.assertEqual(f(a, b, n), esperado, (nome, a, b))

    def test_entrada_mascarada(self):
        self.assertEqual(t_add(0x140, 0x240, 8), t_add(0x40, 0x40, 8))


class TestDot(unittest.TestCase):
    def test_exemplo_a_mao(self):
        for n in (8, 16, 32):
            va = [encode(v, n) for v in (1, 2, 3, 4)]
            vb = [encode(v, n) for v in (0.5, 0.5, 2, 2)]
            self.assertEqual(t_dot(va, vb, n), encode(15.5, n))

    def test_vazio_e_um_elemento(self):
        self.assertEqual(t_dot([], [], 16), 0)
        self.assertEqual(t_dot([encode(3, 16)], [encode(2, 16)], 16), encode(6, 16))

    def test_nar_em_qualquer_posicao(self):
        for n in (8, 16, 32):
            um, nar = encode(1, n), NAR[n]
            self.assertEqual(t_dot([um, um, nar], [um, um, um], n), nar)
            self.assertEqual(t_dot([um, um, um], [um, nar, um], n), nar)

    def test_tamanhos_diferentes(self):
        with self.assertRaises(ValueError):
            t_dot([1, 2, 3], [1, 2], 8)

    def test_acumulador_largo(self):
        """O total é codificado UMA vez no final (não a cada soma)."""
        for n in (8, 16, 32):
            rnd = random.Random(11)
            for _ in range(300):
                tam = rnd.randint(1, 20)
                va = [rnd.getrandbits(n) for _ in range(tam)]
                vb = [rnd.getrandbits(n) for _ in range(tam)]
                if any(v == NAR[n] for v in va + vb):
                    continue
                total = sum(decode(a, n) * decode(b, n) for a, b in zip(va, vb))
                self.assertEqual(t_dot(va, vb, n), encode(total, n))

    def test_difere_de_somar_com_arredondamento_a_cada_passo(self):
        """Em T8, 1 + 0,0625 + 0,0625 ... mostra a vantagem do acumulador largo."""
        n = 8
        um = encode(1, n)
        pequeno = encode(0.0625, n)
        va = [um] + [pequeno] * 8
        vb = [um] * 9
        passo_a_passo = va[0]
        for v in va[1:]:
            passo_a_passo = t_add(passo_a_passo, v, n)
        self.assertNotEqual(t_dot(va, vb, n), passo_a_passo)


class TestCvt(unittest.TestCase):
    def test_alargar_e_exato(self):
        for n_from, n_to in ((8, 16), (8, 32), (16, 32)):
            n_padroes = 1 << n_from if n_from == 8 else 1 << 16
            for i in range(n_padroes):
                if i == NAR[n_from]:
                    continue
                novo = t_cvt(i, n_from, n_to)
                self.assertEqual(decode(novo, n_to), decode(i, n_from))
                self.assertEqual(t_cvt(novo, n_to, n_from), i)       # volta igual

    def test_estreitar_arredonda(self):
        for n_from, n_to in ((16, 8), (32, 16), (32, 8)):
            for i in padroes_aleatorios(n_from, 3000, 5):
                if i == NAR[n_from]:
                    continue
                self.assertEqual(t_cvt(i, n_from, n_to), encode(decode(i, n_from), n_to))

    def test_nar_e_zero(self):
        for n_from in (8, 16, 32):
            for n_to in (8, 16, 32):
                self.assertEqual(t_cvt(NAR[n_from], n_from, n_to), NAR[n_to])
                self.assertEqual(t_cvt(0, n_from, n_to), 0)

    def test_mesmo_formato(self):
        for i in padroes_aleatorios(16, 2000, 9):
            if i != NAR[16]:
                self.assertEqual(t_cvt(i, 16, 16), i)

    def test_exemplos(self):
        self.assertEqual(t_cvt(0x5740, 16, 8), encode(104.0, 8))
        self.assertEqual(t_cvt(0x40, 8, 16), 0x4000)
        self.assertEqual(t_cvt(0x4000, 16, 32), 0x40000000)

    def test_entrada_mascarada(self):
        self.assertEqual(t_cvt(0x180, 8, 16), NAR[16])


if __name__ == "__main__":
    unittest.main(verbosity=2)