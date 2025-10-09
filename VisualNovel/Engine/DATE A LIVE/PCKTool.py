import argparse
from pathlib import Path
from typing import List

from DALLib.File.pck_file import PCKFile


def args_parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract PCK archives from a file or directory.")
    parser.add_argument(
        "input",
        help="Path to a .pck file or a directory that contains .pck files.",
    )
    parser.add_argument(
        "output",
        help="Directory where extracted files will be written.",
    )
    return parser.parse_args()


def _gather_archives(root: Path) -> List[Path]:
    archives: List[Path] = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".pck"]
    archives.sort()
    return archives


def _extract_archive(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with PCKFile() as archive:
        archive.load(str(source), keep_open=True)
        archive.extract_all_files(str(destination))


def _extract_from_directory(input_dir: Path, output_dir: Path) -> None:
    archives = _gather_archives(input_dir)
    if not archives:
        print(f"No .pck archives found in {input_dir}.")
        return

    for archive_path in archives:
        relative = archive_path.relative_to(input_dir)
        relative_destination = output_dir / relative.with_suffix("")
        print(f"Extracting {archive_path} -> {relative_destination}")
        _extract_archive(archive_path, relative_destination)


def _extract_from_file(input_file: Path, output_dir: Path) -> None:
    print(f"Extracting {input_file} -> {output_dir}")
    _extract_archive(input_file, output_dir)


if __name__ == "__main__":
    args = args_parse()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if output_path.exists() and not output_path.is_dir():
        raise NotADirectoryError(f"Output path must be a directory: {output_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    if input_path.is_dir():
        _extract_from_directory(input_path, output_path)
    else:
        _extract_from_file(input_path, output_path)
