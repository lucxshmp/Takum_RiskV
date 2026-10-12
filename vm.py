from alu import t_add, t_sub, t_mul, t_dot, t_cvt


class VM:
    """Simulador funcional das instruções vetoriais Zvtakum.

    Um "registrador vetorial" é uma lista de padrões de bits (int), todos
    com a mesma largura sew (8, 16 ou 32). Cada instrução aplica uma
    função da ALU a todos os elementos e registra que foi executada.
    """

    def __init__(self):
        """Cria a VM com o contador de instruções zerado.

        self.contador é um dicionário {nome da instrução: quantas vezes
        foi executada}. Ex.: {"vtadd.vv": 2, "vtmul.vv": 1}.
        """
        self.contador = {}

    def reset(self):
        """Zera o contador de instruções (volta ao estado inicial)."""
        self.contador = {}

    def _contar(self, nome):
        """Soma 1 ao contador da instrução 'nome' (cria a entrada se não existir)."""
        self.contador[nome] = self.contador.get(nome, 0) + 1

    def _checar_tamanhos(self, va, vb):
        """Levanta ValueError se va e vb tiverem tamanhos diferentes."""
        if len(va) != len(vb):
            raise ValueError("vetores de tamanhos diferentes")


    def vtadd_vv(self, va, vb, sew):
        """vtadd.vv: soma elemento a elemento, resultado[i] = va[i] + vb[i].

        Valida os tamanhos, conta a instrução (UMA vez, não por elemento)
        e devolve uma lista nova. Não altera va nem vb.
        """
        self._checar_tamanhos(va, vb)
        self._contar("vtadd.vv")
        return [t_add(a, b, sew) for a, b in zip(va, vb)]

    def vtsub_vv(self, va, vb, sew):
        """vtsub.vv: subtração elemento a elemento, resultado[i] = va[i] - vb[i].

        Mesmo esqueleto de vtadd_vv, usando t_sub.
        """
        self._checar_tamanhos(va, vb)
        self._contar("vtsub.vv")
        return [t_sub(a, b, sew) for a, b in zip(va, vb)]
        
    def vtmul_vv(self, va, vb, sew):
        """vtmul.vv: multiplicação elemento a elemento, resultado[i] = va[i] * vb[i].

        Mesmo esqueleto de vtadd_vv, usando t_mul.
        """
        self._checar_tamanhos(va, vb)
        self._contar("vtmul.vv")
        return [t_mul(a, b, sew) for a, b in zip(va, vb)]

    def vtdot_vv(self, va, vb, sew):
        """vtdot.vv: produto escalar de va e vb.

        Valida os tamanhos, conta a instrução e devolve UM número (padrão
        de bits em sew bits, não uma lista), usando t_dot.
        """
        self._checar_tamanhos(va, vb)
        self._contar("vtdot.vv")
        return t_dot(va, vb, sew)

    def vncvt_t_t(self, v, sew_from, sew_to):
        """vncvt.t.t: converte cada elemento de v para um formato mais estreito.

        Só estreita: se sew_to >= sew_from, levanta ValueError (e não conta
        a instrução). Devolve uma lista nova, usando t_cvt.
        """
        if sew_to >= sew_from:
            raise ValueError("vncvt estreita: sew_to deve ser menor que sew_from")
        self._contar("vncvt.t.t")
        return [t_cvt(x, sew_from, sew_to) for x in v]

    def total_instrucoes(self):
        """Devolve quantas instruções foram executadas no total (soma do contador)."""
        return sum(self.contador.values())