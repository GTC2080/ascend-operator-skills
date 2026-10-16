import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import source_manifest as checker


class SourceManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'source'
        self.root.mkdir()
        (self.root / 'kernel.cpp').write_text('original source')
        self.manifest = self.root.parent / 'source.json'
        checker.create(self.root, self.manifest)

    def test_exact_tree_passes(self):
        self.assertTrue(checker.verify(self.root, self.manifest)['matches'])

    def test_changed_file_fails(self):
        (self.root / 'kernel.cpp').write_text('changed source')
        self.assertEqual(checker.verify(self.root, self.manifest)['changed'], ['kernel.cpp'])

    def test_missing_file_fails(self):
        (self.root / 'extra.cpp').write_text('extra')
        checker.create(self.root, self.root.parent / 'two-files.json')
        (self.root / 'kernel.cpp').unlink()
        self.assertEqual(checker.verify(self.root, self.root.parent / 'two-files.json')['missing'], ['kernel.cpp'])

    def test_extra_file_fails(self):
        (self.root / 'extra.cpp').write_text('extra')
        self.assertEqual(checker.verify(self.root, self.manifest)['extra'], ['extra.cpp'])

    def test_symlink_rejected(self):
        try:
            (self.root / 'alias').symlink_to(self.root / 'kernel.cpp')
        except (OSError, NotImplementedError):
            self.skipTest('symlink unavailable on this host')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            checker.verify(self.root, self.manifest)

    def test_manifest_inside_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            checker.create(self.root, self.root / 'self.json')

    def test_no_overwrite(self):
        with self.assertRaises(FileExistsError):
            checker.create(self.root, self.manifest)

    def test_unsafe_path_rejected(self):
        d = json.loads(self.manifest.read_text())
        d['files']['../outside'] = d['files'].pop('kernel.cpp')
        self.manifest.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            checker.verify(self.root, self.manifest)

    def test_absolute_and_drive_paths_rejected(self):
        for name in ('', '.', '/absolute', 'C:/outside', 'a/../../outside', 'a\\outside'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                checker.relative_name(name)


if __name__ == '__main__':
    unittest.main()
