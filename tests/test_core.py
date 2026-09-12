import tempfile
import unittest
from datetime import date
from pathlib import Path
from zipfile import ZipFile

from homework_memo.core import SUBJECTS, Exporter, Store, export_docx


class CoreTests(unittest.TestCase):
    def test_store_round_trip_is_utf8_and_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder))
            day = date(2026, 9, 12)
            value = {subject: f"完成{subject}\n第二行" for subject in SUBJECTS}
            store.save(day, value)
            self.assertEqual(store.load(day), value)

    def test_export_preserves_zip_members_and_writes_all_subjects(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            template = Path(__file__).parents[1] / "作业.docx"
            output = root / "作业.docx"
            value = {subject: f"任务-{subject}" for subject in SUBJECTS}
            export_docx(template, output, value, date(2026, 9, 12))
            self.assertTrue(output.exists())
            with ZipFile(output) as archive:
                xml = archive.read("word/document.xml").decode("utf-8")
                for subject in SUBJECTS:
                    self.assertIn(subject, xml)
                self.assertIn("任务-语文", xml)
                self.assertIn("word/styles.xml", archive.namelist())

    def test_export_rate_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            template = Path(__file__).parents[1] / "作业.docx"
            exporter = Exporter()
            value = {subject: "" for subject in SUBJECTS}
            exporter.export(template, root / "a.docx", value, date.today())
            with self.assertRaises(ValueError):
                exporter.export(template, root / "b.docx", value, date.today())


if __name__ == "__main__":
    unittest.main()

