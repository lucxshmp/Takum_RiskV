class VectorRegisterFile:
    """Modelo funcional simples de registradores vetoriais.

    Guarda palavras Takum inteiras; a largura de cada elemento é definida
    na criação do banco.
    """
    def __init__(self, element_width: int, register_count: int = 32, vl: int = 0):
        if element_width not in (8, 16, 32):
            raise ValueError("element_width deve ser 8, 16 ou 32")
        if register_count <= 0 or vl < 0:
            raise ValueError("register_count deve ser positivo e vl não negativo")
        self.element_width = element_width
        self.register_count = register_count
        self.vl = vl
        self.mask = (1 << element_width) - 1
        self._registers = [[] for _ in range(register_count)]

    def write(self, index: int, values: list[int]):
        self._check_index(index)
        if self.vl and len(values) < self.vl:
            raise ValueError("Vetor menor que VL")
        if any(not isinstance(v, int) or v < 0 or v > self.mask for v in values):
            raise ValueError("Elemento não cabe na largura configurada")
        self._registers[index] = list(values[:self.vl or None])

    def read(self, index: int) -> list[int]:
        self._check_index(index)
        return list(self._registers[index])

    def _check_index(self, index: int):
        if not 0 <= index < self.register_count:
            raise IndexError("Índice de registrador inválido")
