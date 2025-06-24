import unittest
import os
import json
import shutil
from tools.file_tools import read_file, list_files, new_file, edit_file
# Schemas are not strictly needed for tests if we pass dicts, but good for reference
# from tools.schemas import ReadFileInput, ListFilesInput, NewFileInput, EditFileInput

class TestFileTools(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for test files."""
        self.test_dir = "temp_test_dir_for_file_tools"
        # Clean up any potential leftovers from a previous failed run
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)

        self._original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self._original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_file(self, path, content=""):
        # Helper to create a file within the current test directory (self.test_dir)
        # Ensure parent dirs exist if path includes them
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    # --- Tests for read_file ---
    def test_read_file_existing(self):
        content = "Hello, world!\nThis is a test file."
        self._create_file("test_read.txt", content)
        input_data = {"path": "test_read.txt"}
        self.assertEqual(read_file(input_data), content)

    def test_read_file_non_existent(self):
        input_data = {"path": "non_existent_file.txt"}
        with self.assertRaises(FileNotFoundError):
            read_file(input_data)

    def test_read_file_unicode(self):
        content = "こんにちは世界\nUTF-8 test. 😊"
        self._create_file("test_unicode.txt", content)
        input_data = {"path": "test_unicode.txt"}
        self.assertEqual(read_file(input_data), content)

    # --- Tests for list_files ---
    def test_list_files_empty_directory(self):
        # Ensure directory is empty for this test
        for item in os.listdir("."): # Current dir is self.test_dir
            if os.path.isfile(item): os.remove(item)
            elif os.path.isdir(item): shutil.rmtree(item)

        input_data = {"path": "."}
        self.assertEqual(json.loads(list_files(input_data)), [])

    def test_list_files_with_content(self):
        self._create_file("file1.txt", "content1")
        self._create_file("file2.py", "content2")
        # os.makedirs("subdir1", exist_ok=True) # _create_file will make subdir1
        self._create_file("subdir1/file3.md", "content3")

        input_data_root = {"path": "."}
        expected_root_listing = sorted(["file1.txt", "file2.py", "subdir1/"])
        actual_root_listing = sorted(json.loads(list_files(input_data_root)))
        self.assertEqual(actual_root_listing, expected_root_listing)

        input_data_subdir = {"path": "subdir1"}
        expected_subdir_listing = sorted(["file3.md"])
        actual_subdir_listing = sorted(json.loads(list_files(input_data_subdir)))
        self.assertEqual(actual_subdir_listing, expected_subdir_listing)

    def test_list_files_non_existent_directory(self):
        input_data = {"path": "non_existent_dir"}
        with self.assertRaises(FileNotFoundError):
            list_files(input_data)

    def test_list_files_default_path(self):
        self._create_file("file_in_root.txt")
        input_data_none = {"path": None}
        self.assertEqual(sorted(json.loads(list_files(input_data_none))), sorted(["file_in_root.txt"]))
        os.remove("file_in_root.txt")

        self._create_file("file_for_dot_path.txt")
        input_data_dot = {"path": "."}
        self.assertEqual(sorted(json.loads(list_files(input_data_dot))), sorted(["file_for_dot_path.txt"]))
        os.remove("file_for_dot_path.txt")

    # --- Tests for new_file ---
    def test_new_file_create(self):
        content = "This is a new file.\nWith two lines."
        input_data = {"path": "newly_created.txt", "content": content}
        new_file(input_data)
        self.assertTrue(os.path.exists("newly_created.txt"))
        with open("newly_created.txt", 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), content)

    def test_new_file_overwrite(self):
        self._create_file("existing_to_overwrite.txt", "Old content.")
        new_content = "This is new content that overwrites."
        input_data = {"path": "existing_to_overwrite.txt", "content": new_content}
        new_file(input_data)
        with open("existing_to_overwrite.txt", 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), new_content)

    def test_new_file_create_parent_dirs(self):
        content = "File in new subdirectory."
        path = os.path.join("new_parent", "new_child", "file.txt")
        input_data = {"path": path, "content": content}
        new_file(input_data)
        self.assertTrue(os.path.exists(path))
        with open(path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), content)

    def test_new_file_empty_path(self):
        input_data = {"path": "", "content": "some content"}
        with self.assertRaisesRegex(ValueError, "File path cannot be empty for new_file."):
            new_file(input_data)

    # --- Tests for edit_file ---
    def test_edit_file_simple_replace(self):
        self._create_file("edit_me.txt", "Hello old world, old world!")
        input_data = {"path": "edit_me.txt", "old_str": "old", "new_str": "new"}
        edit_file(input_data)
        with open("edit_me.txt", 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), "Hello new world, old world!")

    def test_edit_file_old_str_not_found(self):
        self._create_file("edit_not_found.txt", "Hello world.")
        input_data = {"path": "edit_not_found.txt", "old_str": "missing", "new_str": "new"}
        with self.assertRaisesRegex(ValueError, "The string 'missing' was not found in the file 'edit_not_found.txt'."):
            edit_file(input_data)

    def test_edit_file_empty_old_str_prepends(self):
        self._create_file("edit_empty_old.txt", "world.")
        input_data = {"path": "edit_empty_old.txt", "old_str": "", "new_str": "Hello "}
        edit_file(input_data)
        with open("edit_empty_old.txt", 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), "Hello world.")

    def test_edit_file_non_existent_create_with_empty_old_str(self):
        path = "edit_create_new.txt"
        new_content = "Brand new content."
        input_data = {"path": path, "old_str": "", "new_str": new_content}
        edit_file(input_data)
        self.assertTrue(os.path.exists(path))
        with open(path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), new_content)

    def test_edit_file_non_existent_error_if_old_str_not_empty(self):
        input_data = {"path": "edit_non_existent_fail.txt", "old_str": "text", "new_str": "new"}
        with self.assertRaisesRegex(FileNotFoundError, "The file 'edit_non_existent_fail.txt' was not found."):
            edit_file(input_data)

    def test_edit_file_empty_path(self):
        input_data = {"path": "", "old_str": "a", "new_str": "b"}
        with self.assertRaisesRegex(ValueError, "File path cannot be empty."):
            edit_file(input_data)

    def test_edit_file_old_str_equals_new_str(self):
        self._create_file("edit_same_str.txt", "content")
        input_data = {"path": "edit_same_str.txt", "old_str": "a", "new_str": "a"}
        with self.assertRaisesRegex(ValueError, "old_str and new_str cannot be the same. No change would be made."):
            edit_file(input_data)

if __name__ == '__main__':
    unittest.main()
