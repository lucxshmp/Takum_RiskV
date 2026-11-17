
from collections import Counter

from .formats import normalize_width
from .encoder import encode
from .decoder import decode_to_float
from .vector import (
    vtadd_vv,
    vtsub_vv,
    vtmul_vv,
    vtdot_vv,
    vncvt_tt,
)


class VectorMachine:
    """Simulador funcional da extensão vetorial Zvtakum."""

    def __init__(self, num_registers=32, max_vl=256):
        self.num_registers = num_registers
        self.max_vl = max_vl

        self.vregs = {
            f"v{i}": [] for i in range(num_registers)
        }

        self.vreg_sew = {
            f"v{i}": None for i in range(num_registers)
        }

        self.vl = 0
        self.sew = 16

        self.instret = 0
        self.instruction_count = Counter()

    def configure(self, vl, sew):
        sew = normalize_width(sew)

        if not isinstance(vl, int) or vl < 0:
            raise ValueError("VL deve ser um inteiro não negativo.")

        if vl > self.max_vl:
            raise ValueError("VL excede o limite da máquina.")

        self.vl = vl
        self.sew = sew

    def _validate_register(self, register):
        if register not in self.vregs:
            raise ValueError(f"Registrador inválido: {register}")

    def _validate_vector(self, register, expected_sew=None):
        self._validate_register(register)

        if len(self.vregs[register]) < self.vl:
            raise ValueError(
                f"Registrador {register} não possui dados suficientes."
            )

        actual_sew = self.vreg_sew[register]

        if expected_sew is not None and actual_sew != expected_sew:
            raise ValueError(
                f"Registrador {register} possui largura T{actual_sew}, "
                f"mas a operação exige T{expected_sew}."
            )

    def load_vector(self, register, values):
        self._validate_register(register)

        if len(values) < self.vl:
            raise ValueError("O vetor possui menos elementos que VL.")

        self.vregs[register] = [
            encode(float(value), self.sew)
            for value in values[:self.vl]
        ]

        self.vreg_sew[register] = self.sew

    def load_raw(self, register, values):
        self._validate_register(register)

        if len(values) < self.vl:
            raise ValueError("O vetor possui menos elementos que VL.")

        mask = (1 << self.sew) - 1

        self.vregs[register] = [
            int(value) & mask
            for value in values[:self.vl]
        ]

        self.vreg_sew[register] = self.sew

    def read_vector(self, register):
        self._validate_register(register)

        width = self.vreg_sew[register]

        if width is None:
            raise ValueError(
                f"Registrador {register} ainda não foi carregado."
            )

        return [
            decode_to_float(value, width)
            for value in self.vregs[register]
        ]

    def read_raw(self, register):
        self._validate_register(register)
        return self.vregs[register].copy()

    def _count_instruction(self, instruction):
        self.instret += 1
        self.instruction_count[instruction] += 1

    def execute(self, instruction, vd, vs1, vs2=None, dst_sew=None):
        self._validate_register(vd)
        self._validate_vector(vs1)

        if instruction == "vncvt.t.t":
            if dst_sew is None:
                raise ValueError("Informe dst_sew para realizar a conversão.")

            source_sew = self.vreg_sew[vs1]
            dst_sew = normalize_width(dst_sew)

            if dst_sew >= source_sew:
                raise ValueError(
                    "A conversão deve reduzir a largura dos elementos."
                )

            self.vregs[vd] = vncvt_tt(
                self.vregs[vs1][:self.vl],
                source_width=source_sew,
                destination_width=dst_sew,
            )

            self.vreg_sew[vd] = dst_sew
            self._count_instruction(instruction)

            return self.read_vector(vd)

        if vs2 is None:
            raise ValueError(
                f"A instrução {instruction} exige dois operandos."
            )

        self._validate_vector(vs1, self.sew)
        self._validate_vector(vs2, self.sew)

        a = self.vregs[vs1][:self.vl]
        b = self.vregs[vs2][:self.vl]

        if instruction == "vtadd.vv":
            results = vtadd_vv(a, b, self.sew)

        elif instruction == "vtsub.vv":
            results = vtsub_vv(a, b, self.sew)

        elif instruction == "vtmul.vv":
            results = vtmul_vv(a, b, self.sew)

        elif instruction == "vtdot.vv":
            results = [vtdot_vv(a, b, self.sew)]

        else:
            raise ValueError(f"Instrução não suportada: {instruction}")

        self.vregs[vd] = results
        self.vreg_sew[vd] = self.sew

        self._count_instruction(instruction)

        return self.read_vector(vd)

    def get_statistics(self):
        return {
            "instructions_executed": self.instret,
            "instruction_breakdown": dict(self.instruction_count),
            "vl": self.vl,
            "sew": self.sew,
        }

    def reset_statistics(self):
        self.instret = 0
        self.instruction_count.clear()
