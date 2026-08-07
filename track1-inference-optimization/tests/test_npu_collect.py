import unittest

from baseline.npu_collect import host_memory_kb, parse_npu_smi

NPU_SMI_TWO_DEVICES = """\
+------------------------------------------------------------------------------------------------+
| npu-smi 25.5.1                   Version: 25.5.1                                               |
+---------------------------+---------------+----------------------------------------------------+
| NPU   Name                | Health        | Power(W)    Temp(C)           Hugepages-Usage(page)|
| Chip  Phy-ID              | Bus-Id        | AICore(%)   Memory-Usage(MB)  HBM-Usage(MB)        |
+===========================+===============+====================================================+
| 4     Ascend910           | OK            | 170.7       49                0    / 0             |
| 0     8                   | 0000:8D:00.0  | 0           0    / 0          51255/ 65536         |
+------------------------------------------------------------------------------------------------+
| 4     Ascend910           | OK            | -           51                0    / 0             |
| 1     9                   | 0000:8F:00.0  | 0           0    / 0          45292/ 65536         |
+===========================+===============+====================================================+
"""


class NpuSmiParserTests(unittest.TestCase):
    def test_parses_two_devices_with_multi_value_cells(self):
        result = parse_npu_smi(NPU_SMI_TWO_DEVICES)

        self.assertEqual(result["npu_aicore_pct"], "0;0")
        self.assertEqual(result["npu_hbm_mb"], "51255;45292")
        # Second device power is "-" (unavailable), first is 170.7
        self.assertEqual(result["npu_power_w"], "170.7;")
        self.assertEqual(result["npu_temp_c"], "49;51")

    def test_empty_input_yields_empty_metrics(self):
        result = parse_npu_smi("")
        self.assertEqual(result["npu_aicore_pct"], "")
        self.assertEqual(result["npu_hbm_mb"], "")
        self.assertEqual(result["npu_power_w"], "")
        self.assertEqual(result["npu_temp_c"], "")

    def test_aicore_and_hbm_extracted_with_memory_pairs(self):
        result = parse_npu_smi(NPU_SMI_TWO_DEVICES)
        # aicore must be the leading number, not the memory "0 / 0"
        aicore = result["npu_aicore_pct"]
        self.assertNotIn("/", aicore)

    def test_host_memory_returns_int_string(self):
        value = host_memory_kb()
        self.assertTrue(value == "" or int(value) > 0)


if __name__ == "__main__":
    unittest.main()
