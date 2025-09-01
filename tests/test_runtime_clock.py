from profilis.runtime.clock import now_ns


def test_now_ns_monotonic_non_decreasing() -> None:
    last = now_ns()
    for _ in range(1000):
        cur = now_ns()
        assert cur >= last
        last = cur
