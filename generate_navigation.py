from pathlib import Path

CONTENT_PATH = Path("content")


def is_markdown(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".md"


def get_title(path: Path) -> str:
    with path.open() as file:
        first = file.readline().strip()
        if first != "---":
            raise ValueError(f"Bad MD file format: {path}")
        while True:
            line = file.readline().strip()
            if line == "" or line == "---":
                raise ValueError(f"No title found in: {path}")
            if line.startswith("title:"):
                return line.replace("title:", "").strip()


def generate_html_file_info(path: Path) -> str:
    html_path_no_extension = path.parent / path.stem
    title = get_title(path)
    return f'<li><a href="{html_path_no_extension}">{title}</a></li>'


def generate_html_folder_info(directory: Path) -> str:
    items = [f"<li><p>{directory.name.capitalize()}</p><ul>"]
    for path in directory.iterdir():
        if is_markdown(path):
            items.append(generate_html_file_info(path))
        if path.is_dir():
            items.append(generate_html_folder_info(path))
    items.append("</ul></li>")
    return "".join(items)


def generate_html_navigation(content_directory: Path) -> str:
    items: list[str] = []
    for path in content_directory.iterdir():
        if is_markdown(path):
            items.append(generate_html_file_info(path))
        if path.is_dir():
            items.append(generate_html_folder_info(path))

    comment = "<!-- Auto-generated from folder structure -->"
    header = f"<h2>{content_directory.name.capitalize()}</h2>"
    joined = "".join(items)
    content = f"<ul>{joined}</ul>"
    return header + content


def main() -> None:
    result = generate_html_navigation(CONTENT_PATH)
    Path("_includes/navigation.html").write_text(result)


if __name__ == "__main__":
    main()
