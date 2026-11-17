from src.takum.encoder import encode
from src.takum.decoder import decode
from src.takum.formats import TakumClass

class TakumALU:
    """Interface da ALU para palavras Takum logarítmicas.

    As operações em valores reais são executadas aqui apenas após a
    decodificação. A quantização de saída depende do encoder validado.
    """
    def __init__(self, width: int):
        if width not in (8, 16, 32):
            raise ValueError("width deve ser 8, 16 ou 32")
        self.width = width

    def _binary(self, a: int, b: int, op):
        da, db = decode(a, self.width), decode(b, self.width)
        if da.classification == TakumClass.NAR or db.classification == TakumClass.NAR:
            raise NotImplementedError("Propagação/codificação de NaR depende do encoder.")
        result = op(da.value, db.value)
        return encode(result, self.width)

    def add(self, a: int, b: int) -> int:
        return self._binary(a, b, lambda x, y: x + y)

    def sub(self, a: int, b: int) -> int:
        return self._binary(a, b, lambda x, y: x - y)

    def mul(self, a: int, b: int) -> int:
        return self._binary(a, b, lambda x, y: x * y)

    def dot(self, a: list[int], b: list[int], accumulator: int = 0) -> int:
        if len(a) != len(b):
            raise ValueError("Os vetores devem ter o mesmo tamanho.")
        acc = decode(accumulator, self.width).value
        for x, y in zip(a, b):
            dx, dy = decode(x, self.width), decode(y, self.width)
            if dx.value is None or dy.value is None:
                raise NotImplementedError("Tratamento de NaR/zero no dot ainda pendente.")
            acc += dx.value * dy.value
        return encode(acc, self.width)
