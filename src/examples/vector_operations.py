
from src.takum import (
    encode,
    decode_to_float,
    vtadd_vv,
    vtsub_vv,
    vtmul_vv,
    vtdot_vv,
)


def encode_vector(values: list[float], width: int) -> list[int]:
    return [encode(value, width) for value in values]


def decode_vector(values: list[int], width: int) -> list[float]:
    return [
        decode_to_float(value, width)
        for value in values
    ]


def main():
    width = 16

    a = [1.0, 2.0, 3.0, 4.0]
    b = [5.0, 6.0, 7.0, 8.0]

    encoded_a = encode_vector(a, width)
    encoded_b = encode_vector(b, width)

    addition = vtadd_vv(encoded_a, encoded_b, width)
    subtraction = vtsub_vv(encoded_a, encoded_b, width)
    multiplication = vtmul_vv(encoded_a, encoded_b, width)
    dot_product = vtdot_vv(encoded_a, encoded_b, width)

    print("A:", a)
    print("B:", b)

    print("Soma:", decode_vector(addition, width))
    print("Subtração:", decode_vector(subtraction, width))
    print("Multiplicação:", decode_vector(multiplication, width))

    print(
        "Produto escalar:",
        decode_to_float(dot_product, width)
    )


if __name__ == "__main__":
    main()
