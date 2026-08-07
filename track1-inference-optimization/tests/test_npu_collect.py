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
    def test_parses_two_devices_with_per_device_metrics(self):
        devices = parse_npu_smi(NPU_SMI_TWO_DEVICES)

        self.assertEqual(len(devices), 2)
        dev0, dev1 = devices
        # device_id is the chip index (unique per NPU), not the shared group id
        self.assertEqual(dev0["device_id"], "0")
        self.assertEqual(dev0["power"], "170.7")
        self.assertEqual(dev0["temp"], "49")
        self.assertEqual(dev0["aicore"], "0")
        self.assertEqual(dev0["hbm"], "51255")
        # Device 1: power unavailable ("-"), temp 51, aicore 0, hbm 45292
        self.assertEqual(dev1["device_id"], "1")
        self.assertEqual(dev1["power"], "")
        self.assertEqual(dev1["temp"], "51")
        self.assertEqual(dev1["aicore"], "0")
        self.assertEqual(dev1["hbm"], "45292")

    def test_empty_input_yields_no_devices(self):
        self.assertEqual(parse_npu_smi(""), [])

    def test_host_memory_returns_int_string(self):
        value = host_memory_kb()
        self.assertTrue(value == "" or int(value) > 0)


if __name__ == "__main__":
    unittest.main()
