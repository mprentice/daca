from pathlib import Path

from daca.ram.cli import main


def test_ram_main(n_pow_n_file: Path, capsys):
    _ = capsys.readouterr()
    main(argv=[str(n_pow_n_file), "2"])
    captured = capsys.readouterr()
    assert int(captured.out.strip()) == 2**2
    main(argv=["--tokenize", "--no-execute", str(n_pow_n_file)])
    main(argv=["--parse", "--no-execute", str(n_pow_n_file)])
    main(argv=["--tokenize", "--parse", str(n_pow_n_file), "2"])
    main(argv=["--verbose", "--tokenize", "--parse", str(n_pow_n_file), "2"])
