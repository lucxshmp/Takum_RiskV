
import pytest

from src.takum.simulator import VectorMachine


# Tolerância inicial para os testes com Takum T16.
TOLERANCE = 0.002


def test_vector_addition():
    machine = VectorMachine()
    machine.configure(vl=4, sew=16)

    machine.load_vector("v1", [1, 2, 3, 4])
    machine.load_vector("v2", [5, 6, 7, 8])

    machine.execute("vtadd.vv", "v3", "v1", "v2")

    result = machine.read_vector("v3")

    assert result == pytest.approx(
        [6, 8, 10, 12],
        rel=TOLERANCE
    )


def test_vector_subtraction():
    machine = VectorMachine()
    machine.configure(vl=3, sew=16)

    machine.load_vector("v1", [10, 20, 30])
    machine.load_vector("v2", [1, 2, 3])

    machine.execute("vtsub.vv", "v3", "v1", "v2")

    result = machine.read_vector("v3")

    assert result == pytest.approx(
        [9, 18, 27],
        rel=TOLERANCE
    )


def test_vector_multiplication():
    machine = VectorMachine()
    machine.configure(vl=3, sew=16)

    machine.load_vector("v1", [2, 3, 4])
    machine.load_vector("v2", [5, 6, 7])

    machine.execute("vtmul.vv", "v3", "v1", "v2")

    result = machine.read_vector("v3")

    assert result == pytest.approx(
        [10, 18, 28],
        rel=TOLERANCE
    )


def test_dot_product():
    machine = VectorMachine()
    machine.configure(vl=3, sew=16)

    machine.load_vector("v1", [1, 2, 3])
    machine.load_vector("v2", [4, 5, 6])

    machine.execute("vtdot.vv", "v3", "v1", "v2")

    result = machine.read_vector("v3")[0]

    assert result == pytest.approx(32, rel=TOLERANCE)


def test_narrowing_conversion():
    machine = VectorMachine()
    machine.configure(vl=3, sew=16)

    machine.load_vector("v1", [1.5, 2.5, 3.5])

    machine.execute(
        "vncvt.t.t",
        "v2",
        "v1",
        dst_sew=8
    )

    assert machine.sew == 16
    assert len(machine.read_raw("v2")) == 3


def test_instruction_count():
    machine = VectorMachine()
    machine.configure(vl=2, sew=16)

    machine.load_vector("v1", [1, 2])
    machine.load_vector("v2", [3, 4])

    machine.execute("vtadd.vv", "v3", "v1", "v2")
    machine.execute("vtmul.vv", "v4", "v1", "v2")

    stats = machine.get_statistics()

    assert stats["instructions_executed"] == 2
    assert stats["instruction_breakdown"]["vtadd.vv"] == 1
    assert stats["instruction_breakdown"]["vtmul.vv"] == 1


def test_narrowing_conversion_preserves_register_width():
    machine = VectorMachine()
    machine.configure(vl=3, sew=16)

    machine.load_vector("v1", [1.5, 2.5, 3.5])

    machine.execute(
        "vncvt.t.t",
        "v2",
        "v1",
        dst_sew=8
    )

    # O destino deve ser interpretado como T8.
    assert machine.vreg_sew["v2"] == 8

    # A largura do registrador original não deve mudar.
    assert machine.vreg_sew["v1"] == 16

    # A leitura deve utilizar a largura correta.
    assert machine.read_vector("v2") == pytest.approx(
        [1.5, 2.5, 3.5],
        rel=0.05
    )
