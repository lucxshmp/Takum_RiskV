"""Testes da VM (vtadd.vv, vtsub.vv, vtmul.vv, vtdot.vv, vncvt.t.t).

Coloque na mesma pasta de split.py, takum.py, alu.py e vm.py e rode:
    python test_vm.py
"""
import random
import unittest

from takum import decode, encode
from alu import t_add, t_sub, t_mul, t_dot, t_cvt
from vm import VM

NAR = {8: 0x80, 16: 0x8000, 32: 0x80000000}


def vetor(valores, n):
    return [encode(v, n) for v in valores]


def valores(v, n):
    return [decode(x, n) for x in v]


class TestInstrucoesVetoriais(unittest.TestCase):
    def setUp(self):
        self.vm = VM()

    def test_vtadd_vtsub_vtmul_a_mao(self):
        for n in (8, 16, 32):
            va = vetor([1, 2, 3, 4], n)
            vb = vetor([0.5, 0.5, 2, 2], n)
            self.assertEqual(valores(self.vm.vtadd_vv(va, vb, n), n), [1.5, 2.5, 5, 6])
            self.assertEqual(valores(self.vm.vtsub_vv(va, vb, n), n), [0.5, 1.5, 1, 2])
            self.assertEqual(valores(self.vm.vtmul_vv(va, vb, n), n), [0.5, 1, 6, 8])

    def test_igual_a_alu_elemento_a_elemento(self):
        rnd = random.Random(4)
        for n in (8, 16, 32):
            va = [rnd.getrandbits(n) for _ in range(40)]
            vb = [rnd.getrandbits(n) for _ in range(40)]
            self.assertEqual(self.vm.vtadd_vv(va, vb, n), [t_add(a, b, n) for a, b in zip(va, vb)])
            self.assertEqual(self.vm.vtsub_vv(va, vb, n), [t_sub(a, b, n) for a, b in zip(va, vb)])
            self.assertEqual(self.vm.vtmul_vv(va, vb, n), [t_mul(a, b, n) for a, b in zip(va, vb)])

    def test_nao_altera_as_entradas(self):
        va, vb = vetor([1, 2], 16), vetor([3, 4], 16)
        copia_a, copia_b = list(va), list(vb)
        self.vm.vtadd_vv(va, vb, 16)
        self.assertEqual((va, vb), (copia_a, copia_b))

    def test_vetor_vazio(self):
        self.assertEqual(self.vm.vtadd_vv([], [], 8), [])
        self.assertEqual(self.vm.vtdot_vv([], [], 8), 0)
        self.assertEqual(self.vm.vncvt_t_t([], 16, 8), [])

    def test_nar_so_afeta_o_elemento(self):
        n = 16
        va = [encode(1, n), NAR[n], encode(3, n)]
        vb = [encode(1, n)] * 3
        r = self.vm.vtadd_vv(va, vb, n)
        self.assertEqual(r[1], NAR[n])
        self.assertEqual(decode(r[0], n), 2.0)
        self.assertEqual(decode(r[2], n), 4.0)

    def test_tamanhos_diferentes(self):
        for nome in ("vtadd_vv", "vtsub_vv", "vtmul_vv", "vtdot_vv"):
            with self.assertRaises(ValueError):
                getattr(self.vm, nome)([1, 2, 3], [1, 2], 8)

    def test_vtdot(self):
        for n in (8, 16, 32):
            va = vetor([1, 2, 3, 4], n)
            vb = vetor([0.5, 0.5, 2, 2], n)
            r = self.vm.vtdot_vv(va, vb, n)
            self.assertIsInstance(r, int)                 # um escalar, não lista
            self.assertEqual(r, t_dot(va, vb, n))
            self.assertEqual(r, encode(15.5, n))          # em T8 vira 16 (arredonda)

    def test_vncvt(self):
        for n_from, n_to in ((16, 8), (32, 16), (32, 8)):
            rnd = random.Random(8)
            v = [rnd.getrandbits(n_from) for _ in range(50)]
            self.assertEqual(self.vm.vncvt_t_t(v, n_from, n_to),
                             [t_cvt(x, n_from, n_to) for x in v])
        self.assertEqual(self.vm.vncvt_t_t([0x5740], 16, 8), [encode(104.0, 8)])

    def test_vncvt_so_estreita(self):
        with self.assertRaises(ValueError):
            self.vm.vncvt_t_t([0x40], 8, 16)
        with self.assertRaises(ValueError):
            self.vm.vncvt_t_t([0x40], 8, 8)


class TestContador(unittest.TestCase):
    def test_conta_por_instrucao(self):
        vm = VM()
        v = vetor([1, 2], 8)
        vm.vtadd_vv(v, v, 8)
        vm.vtadd_vv(v, v, 8)
        vm.vtmul_vv(v, v, 8)
        vm.vtdot_vv(v, v, 8)
        vm.vncvt_t_t(vetor([1], 16), 16, 8)
        self.assertEqual(vm.contador, {"vtadd.vv": 2, "vtmul.vv": 1,
                                       "vtdot.vv": 1, "vncvt.t.t": 1})
        self.assertEqual(vm.total_instrucoes(), 5)

    def test_conta_instrucao_e_nao_elementos(self):
        vm = VM()
        v = vetor(list(range(1, 33)), 8)
        vm.vtadd_vv(v, v, 8)
        self.assertEqual(vm.contador["vtadd.vv"], 1)

    def test_reset(self):
        vm = VM()
        v = vetor([1], 8)
        vm.vtadd_vv(v, v, 8)
        vm.reset()
        self.assertEqual(vm.contador, {})
        self.assertEqual(vm.total_instrucoes(), 0)

    def test_instrucao_com_erro_nao_conta(self):
        vm = VM()
        with self.assertRaises(ValueError):
            vm.vtadd_vv([1, 2], [1], 8)
        self.assertEqual(vm.total_instrucoes(), 0)

    def test_vms_independentes(self):
        a, b = VM(), VM()
        v = vetor([1], 8)
        a.vtadd_vv(v, v, 8)
        self.assertEqual(b.contador, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)