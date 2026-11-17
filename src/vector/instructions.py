from src.arithmetic.alu import TakumALU
from src.takum.encoder import encode
from src.takum.decoder import decode

class Zvtakum:
    """Implementação funcional de referência das instruções propostas.

    Não é um decoder de opcodes RVV nem uma implementação binária da ISA.
    Representa apenas a semântica das operações sobre listas de elementos.
    """
    def __init__(self, width: int):
        self.width = width
        self.alu = TakumALU(width)

    def _elementwise(self, a, b, operation):
        if len(a) != len(b):
            raise ValueError("Vetores com comprimentos diferentes")
        return [operation(x, y) for x, y in zip(a, b)]

    def vtadd_vv(self, a, b):
        return self._elementwise(a, b, self.alu.add)

    def vtsub_vv(self, a, b):
        return self._elementwise(a, b, self.alu.sub)

    def vtmul_vv(self, a, b):
        return self._elementwise(a, b, self.alu.mul)

    def vtdot_vv(self, a, b, accumulator=0):
        return self.alu.dot(a, b, accumulator)

    def vncvt_t_t(self, values, destination_width):
        if destination_width not in (8, 16, 32):
            raise ValueError("Largura de destino inválida")
        converted = []
        for raw in values:
            decoded = decode(raw, self.width)
            if decoded.value is None:
                raise NotImplementedError("Conversão de zero/NaR depende do encoder.")
            converted.append(encode(decoded.value, destination_width))
        return converted
