from collections.abc import Generator, Iterable


def pairwise[T](s: Iterable[T]) -> Generator[tuple[T, T], None, None]:
    it = iter(s)
    yield from zip(it, it)
