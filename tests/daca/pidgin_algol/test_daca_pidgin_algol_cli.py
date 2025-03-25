from pathlib import Path

from daca.pidgin_algol.cli import main


def test_main(n_pow_n_file: Path, capsys):
    _ = capsys.readouterr()
    main(argv=[str(n_pow_n_file), "2"])
    captured = capsys.readouterr()
    assert int(captured.out.strip()) == 2**2


def test_main_verbose(n_pow_n_file: Path):
    main(
        argv=["--verbose", "--tokenize", "--parse", "--compile", str(n_pow_n_file), "2"]
    )


def test_main_no_verbose(n_pow_n_file: Path):
    main(argv=["--tokenize", "--parse", "--compile", str(n_pow_n_file), "2"])


def test_main_no_execute(n_pow_n_file: Path):
    main(argv=["--no-execute", str(n_pow_n_file)])
