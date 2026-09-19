from pathlib import Path
import os
import sys
import tempfile
import unittest


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sources import media_folder


class MediaFolderTests(unittest.TestCase):
    def test_generated_preview_is_not_used_as_a_source(self):
        original_path = media_folder.folder_path
        try:
            with tempfile.TemporaryDirectory() as temp_directory:
                media_folder.folder_path = temp_directory
                Path(temp_directory, 'art.JPG').touch()
                Path(temp_directory, 'latest.jpg').touch()
                Path(temp_directory, 'uploaded_files.json').touch()

                self.assertEqual(
                    media_folder.get_media_folder_images(),
                    [str(Path(temp_directory, 'art.JPG'))],
                )
        finally:
            media_folder.folder_path = original_path


if __name__ == '__main__':
    unittest.main()
