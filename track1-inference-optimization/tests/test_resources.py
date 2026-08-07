import json
import tempfile
import unittest
from pathlib import Path

from baseline.summarize_resources import summarize_csv


class ResourceSummaryTests(unittest.TestCase):
    def test_summarizes_peak_and_distribution_per_device(self):
        csv_content = (
            "timestamp,npu_aicore_pct,npu_hbm_mb,npu_power_w,npu_temp_c,host_used_kb\n"
            "2026-08-07T00:00:00.000Z,10;20,3115,170,48,1000\n"
            "2026-08-07T00:00:01.000Z,30;40,5000,180,52,2000\n"
            "2026-08-07T00:00:02.000Z,50;60,6000,190,55,3000\n"
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

        self.assertEqual(result["samples"], 3)
        aicore = result["summary"]["npu_aicore_pct"]
        self.assertEqual(aicore["status"], "ok")
        # Values flatten across devices: 10,20,30,40,50,60
        self.assertEqual(aicore["peak"], 60)
        self.assertEqual(aicore["count"], 6)
        hbm = result["summary"]["npu_hbm_mb"]
        self.assertEqual(hbm["peak"], 6000)
        host = result["summary"]["host_used_kb"]
        self.assertEqual(host["peak"], 3000)

    def test_missing_column_is_unavailable_not_zero(self):
        csv_content = (
            "timestamp,npu_aicore_pct,npu_hbm_mb\n"
            "2026-08-07T00:00:00.000Z,10,\n"
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

        self.assertEqual(result["summary"]["npu_hbm_mb"]["status"], "unavailable")
        # host_used_kb was never in the CSV
        self.assertEqual(
            result["summary"]["host_used_kb"]["status"], "unavailable"
        )
        # npu_power_w was never in the CSV
        self.assertEqual(
            result["summary"]["npu_power_w"]["status"], "unavailable"
        )

    def test_empty_file_is_unavailable(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("timestamp,npu_aicore_pct,npu_hbm_mb\n")
            path = Path(f.name)

        try:
            result = summarize_csv(path)
        finally:
            path.unlink()

        self.assertEqual(result["samples"], 0)
        self.assertEqual(
            result["summary"]["npu_aicore_pct"]["status"], "unavailable"
        )


if __name__ == "__main__":
    unittest.main()
