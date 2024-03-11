from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

MAX_HEADER_BYTES = 2048
CONTENT_PATH = Path("content")
NAVIGATION_PAGE_LAYOUT = "standard"
NAVIGATION_FILE_NAME = "__navigation.md"
NAVIGATION_INCLUDE_COMMAND = "{% include_relative __navigation.md %}"


@dataclass
class MdPage:
    path: Path

    @classmethod
    def make(cls, path: Path) -> Self | None:
        if (
            path.is_file()
            and path.suffix.lower() == ".md"
            and path.name != NAVIGATION_FILE_NAME
        ):
            return cls(path)
        return None

    @property
    def title(self) -> str:
        with self.path.open() as file:
            header: str = file.read(MAX_HEADER_BYTES)

        try:
            pre_header, header, post_header = header.split("---", maxsplit=2)
        except ValueError as ex:
            raise ValueError(
                f"The MD page must contain a valid YAML header: {self.path}"
            ) from ex

        if len(pre_header.strip()) != 0:
            raise ValueError(f"The MD page must begin with YAML header: {self.path}")
        if len(post_header.strip()) == 0:
            raise ValueError(f"Empty file: {self.path}")

        try:
            _, title_with_tail = header.split("title:", maxsplit=1)
        except ValueError as ex:
            raise ValueError(f"No title in MD page: {self.path}") from ex

        title, *_ = title_with_tail.split("\n", maxsplit=1)
        return title.strip()

    @property
    def is_index(self) -> bool:
        return self.path.stem.lower() == "index"

    def create_with_title(
        self, title: str, layout: str = NAVIGATION_PAGE_LAYOUT
    ) -> None:
        if self.path.exists():
            return

        lines = [
            "---",
            f"title: {title}",
            f"layout: {layout}",
            "---",
            "",
        ]
        content = "\n".join(lines)
        self.path.write_text(content)

    def append_navigation_include_command(self) -> None:
        lines = self.path.read_text().split("\n")
        if NAVIGATION_INCLUDE_COMMAND in lines:
            return
        with self.path.open("a") as file:
            file.write(f"\n\n\n{NAVIGATION_INCLUDE_COMMAND}")


@dataclass
class Directory:
    path: Path
    files: list[MdPage] = field(default_factory=list)
    directories: list[Self] = field(default_factory=list)

    @property
    def name(self) -> str:
        index = self.index
        if self.index is None:
            return self.path.name.replace("-", " ").capitalize()
        return index.title

    @classmethod
    def make_recursive(cls, path: Path) -> Self | None:
        if not path.is_dir():
            return None

        files: list[MdPage] = []
        directories: list[Directory] = []
        for entry in path.iterdir():
            file = MdPage.make(entry)
            if file is not None:
                files.append(file)
                continue
            directory = cls.make_recursive(entry)
            if directory is not None:
                directories.append(directory)

        files.sort(key=lambda file: file.path.name)
        directories.sort(key=lambda directory: directory.path.name)

        return cls(path, files, directories)

    @property
    def is_empty(self) -> bool:
        return len(self.files) == 0 and all(dir.is_empty for dir in self.directories)

    @property
    def has_index(self) -> bool:
        return self.index is not None

    @property
    def index(self) -> MdPage | None:
        for file in self.files:
            if file.is_index:
                return file
        return None

    def fill_indexes(self) -> None:
        index = MdPage(self.path / "index.md")
        if not self.has_index:
            index.create_with_title(self.path.name.capitalize())

        navigation_content = self.generate_navigation_md()
        (self.path / NAVIGATION_FILE_NAME).write_text(navigation_content)

        index.append_navigation_include_command()

        for directory in self.directories:
            directory.fill_indexes()

    def generate_pages_navigation(self) -> str | None:
        if len(self.files) == 0:
            return None

        pages = ["### Pages"]
        for file in self.files:
            if file.is_index:
                continue
            relative_path = file.path.relative_to(self.path)
            path_no_format = str(relative_path).replace(".md", "")
            page_line = f"- [{file.title}]({path_no_format})"
            pages.append(page_line)
        return "\n".join(pages) + "\n"

    def generate_folders_navigation(self) -> str | None:
        if len(self.directories) == 0:
            return None

        folders = ["### Folders"]
        for directory in self.directories:
            relative_path = directory.path.relative_to(self.path)
            path_no_format = str(relative_path).replace(".md", "")
            directory_line = f"- [{directory.name}]({path_no_format})"
            folders.append(directory_line)
        return "\n".join(folders) + "\n"

    def generate_navigation_md(self) -> str:
        table_of_contents: list[str] = []
        pages = self.generate_pages_navigation()
        folders = self.generate_folders_navigation()
        if pages is not None:
            table_of_contents.append(pages)
        if folders is not None:
            table_of_contents.append(folders)
        return "\n".join(table_of_contents)


class DirectoryStructure:
    def __init__(self, path: Path) -> None:
        self.root = Directory.make_recursive(path)

    def fill_indexes(self) -> None:
        self.root.fill_indexes()


def main() -> None:
    structure = DirectoryStructure(CONTENT_PATH)
    structure.fill_indexes()


if __name__ == "__main__":
    main()
