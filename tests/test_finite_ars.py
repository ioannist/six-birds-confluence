from rewriteflat.finite_ars import FiniteARS


def test_diamond_properties():
    ars = FiniteARS(
        states=["A", "B", "C", "D"],
        edges=[("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")],
    )

    assert ars.reachable_from("A") == {"A", "B", "C", "D"}
    assert ars.reachable_from("B") == {"B", "D"}
    assert ars.is_normal_form("D")
    assert not ars.is_normal_form("A")
    assert ars.joinable("B", "C")
    assert ars.is_terminating()
    assert ars.is_locally_confluent()
    assert ars.is_confluent()
    assert ars.has_unique_reachable_normal_forms()
    assert ars.reachable_normal_forms("A") == {"D"}


def test_fork_properties():
    ars = FiniteARS(
        states=["A", "B", "C", "D"],
        edges=[("A", "B"), ("A", "C"), ("B", "D")],
    )

    assert ars.is_normal_form("C")
    assert ars.is_normal_form("D")
    assert not ars.joinable("B", "C")
    assert ars.is_terminating()
    assert not ars.is_locally_confluent()
    assert not ars.is_confluent()
    assert not ars.has_unique_reachable_normal_forms()
    assert ars.reachable_normal_forms("A") == {"C", "D"}


def test_cycle_is_not_terminating():
    ars = FiniteARS(states=["A", "B"], edges=[("A", "B"), ("B", "A")])
    assert not ars.is_terminating()
