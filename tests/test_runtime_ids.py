import re

from profilis.runtime.ids import span_id

HEX16 = re.compile(r"^[0-9a-f]{16}$")
TEST_ITERATIONS = 10_000


def test_span_id_format_and_nonzero() -> None:
    for _ in range(1000):
        s = span_id()
        assert HEX16.match(s), f"bad span id format: {s}"
        assert int(s, 16) != 0, "span id must be non-zero"


def test_span_id_uniqueness_reasonable() -> None:
    # 10k is a good balance for CI speed vs. collision probability
    ids = {span_id() for _ in range(TEST_ITERATIONS)}
    assert len(ids) == TEST_ITERATIONS
