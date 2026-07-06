from __future__ import annotations

from pathlib import Path
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.archive_import_service import ArchiveImportService  # noqa: E402
from app.services.parse_service import ParseService  # noqa: E402


class FakeZipInfo:
    def __init__(self, filename: str, flag_bits: int = 0) -> None:
        self.filename = filename
        self.flag_bits = flag_bits


class ArchiveImportServiceTests(unittest.TestCase):
    def test_zip_name_decoder_recovers_gbk_encoded_chinese_name(self) -> None:
        raw_name = "奖学金材料.txt".encode("gbk")
        mojibake_name = raw_name.decode("cp437")
        info = FakeZipInfo(mojibake_name)

        self.assertEqual(ArchiveImportService()._decode_zip_name(info), "奖学金材料.txt")
        self.assertEqual(ParseService()._decode_zip_name(info), "奖学金材料.txt")

    def test_zip_name_decoder_keeps_utf8_flagged_name(self) -> None:
        info = FakeZipInfo("奖学金材料.txt", flag_bits=0x800)

        self.assertEqual(ArchiveImportService()._decode_zip_name(info), "奖学金材料.txt")
        self.assertEqual(ParseService()._decode_zip_name(info), "奖学金材料.txt")


if __name__ == "__main__":
    unittest.main()
