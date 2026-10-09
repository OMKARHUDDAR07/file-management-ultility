"""
FILE MANAGEMENT UTILITY  (Skyrovix Virtual Internship - Task 3)
================================================================
Menu-driven command-line tool built with Python modules
(pathlib, shutil, logging, collections, unittest).

FEATURES
  - Python modules ........ pathlib, shutil, logging, collections, unittest
  - Input validation ...... empty / non-existent paths, invalid names, confirmations
  - Data processing ....... search, organize by extension, folder summary
  - Error handling ........ PermissionError, FileExistsError, FileNotFoundError, OSError
                            (all logged to file_manager.log)

WORKFLOW
  1. Show menu  ->  2. Validate user input  ->  3. Process the operation
  ->  4. Handle errors  ->  5. Log result and return to menu

HOW TO RUN
  Utility :  python file_management_utility.py
  Tests   :  python file_management_utility.py --test
"""

import logging
import shutil
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

logging.basicConfig(
    filename="file_manager.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


# ======================= INPUT VALIDATION =======================
def get_path(prompt, must_exist=True):
    """Ask for a path; re-ask until it is valid."""
    while True:
        raw = input(prompt).strip().strip('"')
        if not raw:
            print("  Input cannot be empty.")
            continue
        path = Path(raw).expanduser()
        if must_exist and not path.exists():
            print(f"  '{path}' does not exist. Try again.")
            continue
        return path


def confirm(message):
    return input(f"{message} (y/n): ").strip().lower() == "y"


# ======================= CORE OPERATIONS =======================
def list_files(folder):
    items = sorted(folder.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    if not items:
        print("  (empty folder)")
    for p in items:
        kind = "DIR " if p.is_dir() else "FILE"
        size = f"{p.stat().st_size:>10,} B" if p.is_file() else ""
        print(f"  [{kind}] {p.name:<40} {size}")
    return items


def create_folder(path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_item(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst / src.name)
    else:
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def move_item(src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst / src.name))


def rename_item(src, new_name):
    if any(c in new_name for c in '\\/:*?"<>|'):
        raise ValueError("New name contains invalid characters.")
    target = src.with_name(new_name)
    if target.exists():
        raise FileExistsError(f"'{new_name}' already exists.")
    src.rename(target)
    return target


def delete_item(path):
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def search_files(folder, keyword):
    keyword = keyword.lower()
    return [p for p in folder.rglob("*") if keyword in p.name.lower()]


def organize_by_extension(folder):
    """Move files into sub-folders named after their extension."""
    moved = 0
    for p in list(folder.iterdir()):
        if p.is_file():
            ext = p.suffix.lower().lstrip(".") or "no_extension"
            move_item(p, folder / ext)
            moved += 1
    return moved


def folder_summary(folder):
    counts, total = defaultdict(int), 0
    for p in folder.rglob("*"):
        if p.is_file():
            counts[p.suffix.lower() or "no_extension"] += 1
            total += p.stat().st_size
    return dict(counts), total


# ======================= MENU HANDLERS =======================
def run_action(func):
    """Run a menu action, catching and logging common errors."""
    try:
        func()
    except PermissionError:
        print("  Permission denied.")
        logging.error("PermissionError in %s", func.__name__)
    except FileExistsError as e:
        print(f"  Already exists: {e}")
        logging.error("FileExistsError: %s", e)
    except FileNotFoundError as e:
        print(f"  Not found: {e}")
        logging.error("FileNotFoundError: %s", e)
    except (ValueError, shutil.Error, OSError) as e:
        print(f"  Error: {e}")
        logging.error("%s: %s", type(e).__name__, e)


def do_list():
    list_files(get_path("Folder path: "))


def do_create():
    p = create_folder(get_path("New folder path: ", must_exist=False))
    print(f"  Created: {p}")
    logging.info("Created folder %s", p)


def do_copy():
    src = get_path("Source file/folder: ")
    dst = get_path("Destination folder: ", must_exist=False)
    copy_item(src, dst)
    print("  Copied.")
    logging.info("Copied %s -> %s", src, dst)


def do_move():
    src = get_path("Source file/folder: ")
    dst = get_path("Destination folder: ", must_exist=False)
    move_item(src, dst)
    print("  Moved.")
    logging.info("Moved %s -> %s", src, dst)


def do_rename():
    src = get_path("File/folder to rename: ")
    new = input("New name: ").strip()
    target = rename_item(src, new)
    print(f"  Renamed to {target.name}")
    logging.info("Renamed %s -> %s", src, target)


def do_delete():
    path = get_path("File/folder to delete: ")
    if confirm(f"  Delete '{path}' permanently?"):
        delete_item(path)
        print("  Deleted.")
        logging.info("Deleted %s", path)
    else:
        print("  Cancelled.")


def do_search():
    folder = get_path("Folder to search in: ")
    keyword = input("Keyword: ").strip()
    if not keyword:
        raise ValueError("Keyword cannot be empty.")
    results = search_files(folder, keyword)
    print(f"  {len(results)} match(es):")
    for r in results:
        print("   ", r)


def do_organize():
    folder = get_path("Folder to organize: ")
    if confirm("  Move files into extension-based sub-folders?"):
        n = organize_by_extension(folder)
        print(f"  Organized {n} file(s).")
        logging.info("Organized %s (%d files)", folder, n)


def do_summary():
    counts, total = folder_summary(get_path("Folder path: "))
    for ext, n in sorted(counts.items()):
        print(f"  {ext:<15} {n} file(s)")
    print(f"  Total size: {total / 1024:.2f} KB")


MENU = {
    "1": ("List files", do_list),
    "2": ("Create folder", do_create),
    "3": ("Copy", do_copy),
    "4": ("Move", do_move),
    "5": ("Rename", do_rename),
    "6": ("Delete", do_delete),
    "7": ("Search", do_search),
    "8": ("Organize by extension", do_organize),
    "9": ("Folder summary", do_summary),
    "0": ("Exit", None),
}


def main():
    print("=== File Management Utility ===")
    while True:
        print()
        for key, (label, _) in MENU.items():
            print(f"  {key}. {label}")
        choice = input("Choose an option: ").strip()
        if choice not in MENU:
            print("  Invalid choice. Enter a number from the menu.")
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            run_action(MENU[choice][1])


# ======================= TESTING =======================
class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "a.txt").write_text("hello")
        (self.root / "b.py").write_text("print(1)")

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_folder(self):
        self.assertTrue(create_folder(self.root / "new" / "sub").is_dir())

    def test_copy_and_move(self):
        copy_item(self.root / "a.txt", self.root / "copy")
        self.assertTrue((self.root / "copy" / "a.txt").exists())
        move_item(self.root / "b.py", self.root / "moved")
        self.assertTrue((self.root / "moved" / "b.py").exists())
        self.assertFalse((self.root / "b.py").exists())

    def test_rename(self):
        self.assertTrue(rename_item(self.root / "a.txt", "c.txt").exists())

    def test_rename_invalid_name(self):
        with self.assertRaises(ValueError):
            rename_item(self.root / "a.txt", "bad/name.txt")

    def test_rename_existing(self):
        with self.assertRaises(FileExistsError):
            rename_item(self.root / "a.txt", "b.py")

    def test_delete(self):
        delete_item(self.root / "a.txt")
        self.assertFalse((self.root / "a.txt").exists())

    def test_delete_missing(self):
        with self.assertRaises(FileNotFoundError):
            delete_item(self.root / "nope.txt")

    def test_search(self):
        self.assertEqual(len(search_files(self.root, "a.t")), 1)

    def test_organize(self):
        self.assertEqual(organize_by_extension(self.root), 2)
        self.assertTrue((self.root / "txt" / "a.txt").exists())
        self.assertTrue((self.root / "py" / "b.py").exists())

    def test_summary(self):
        counts, total = folder_summary(self.root)
        self.assertEqual(counts[".txt"], 1)
        self.assertGreater(total, 0)


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.argv.remove("--test")
        unittest.main(verbosity=2)
    else:
        main()