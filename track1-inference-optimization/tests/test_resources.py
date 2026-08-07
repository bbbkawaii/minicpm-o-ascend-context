import tempfile
import unittest
from pathlib import Path

from baseline.summarize_resources import summarize_csv


class ResourceSummaryTests(unittest.TestCase):
    CSV_HEADER = "timestamp,device_id,npu_aicore_pct,npu_hbm_mb,npu_power_w,npu_temp_c,host_used_kb\n"

    def test_per_device_aggregation(self):
        csv_content = self.CSV_HEADER + (
            "2026-08-07T00:00:00.000Z,0,10,3115,170,48,1000\n"
            "2026-08-07T00:00:00.000Z,1,20,45292,180,51,1000\n"
            "2026-08-07T00:00:01.000Z,0,30,5000,175,50,2000\n"
            "2026-08-07T00:00:01.000Z,1,40,45292,190,52,2000\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            path = Path(f.name)

        try:
            result = summarize_csv(path)
        finally:
            path.unlink()

        self.assertEqual(result["samples"], 4)
        dev0 = result["devices"]["0"]["metrics"]
        dev1 = result["devices"]["1"]["metrics"]
        # Device 0: aicore 10,30 -> peak 30
        self.assertEqual(dev0["npu_aicore_pct"]["peak"], 30)
        self.assertEqual(dev0["npu_hbm_mb"]["peak"], 5000)
        # Device 1: aicore 20,40 -> peak 40 (NOT mixed with device 0)
        self.assertEqual(dev1["npu_aicore_pct"]["peak"], 40)
        self.assertEqual(dev1["npu_hbm_mb"]["peak"], 45292)
        # Host memory aggregated across all rows
        self.assertEqual(result["host_used_kb"]["peak"], 2000)

    def test_missing_column_is_unavailable_not_zero(self):
        csv_content = (
            "timestamp,device_id,npu_aicore_pct,npu_hbm_mb\n"
            "2026-08-07T00:00:00.000Z,0,10,\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            path = Path(f.name)

        try:
            result = summarize_csv(path)
        finally:
            path.unlink()

        dev0 = result["devices"]["0"]["metrics"]
        self.assertEqual(dev0["npu_hbm_mb"]["status"], "unavailable")
        self.assertEqual(dev0["npu_power_w"]["status"], "unavailable")
        self.assertEqual(result["host_used_kb"]["status"], "unavailable")

    def test_empty_file_is_unavailable(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(self.CSV_HEADER)
            path = Path(f.name)

        try:
            result = summarize_csv(path)
        finally:
            path.unlink()

        self.assertEqual(result["samples"], 0)
        self.assertEqual(result["devices"], {})
        self.assertEqual(result["host_used_kb"]["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
