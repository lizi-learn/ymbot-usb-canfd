import unittest
from unittest.mock import patch
from ymbot_usb_canfd.protocol import payload,frame,decode,LENGTHS
from ymbot_usb_canfd.hardware import select_device
from ymbot_usb_canfd.benchmark import run


class ProtocolTest(unittest.TestCase):
    def test_independent_known_vector(self):
        # Two big-endian integers: source=0, seq=1. Not built by the encoder.
        self.assertEqual(decode(b'b50080000000000000001',8),(0,1))
        self.assertEqual(frame(1,2,8,False),b't50180000000100000002\r')

    def test_all_fd_lengths_and_high_sequence(self):
        for size in LENGTHS[8:]:
            f=frame(1,0xFFFFFFFE,size)
            self.assertEqual(decode(f[:-1],size),(1,0xFFFFFFFE))

    def test_corruption_wrong_dlc_and_wrong_type(self):
        valid=frame(0,3,12)[:-1]
        for damaged in [valid[:-1]+b'0',b't'+valid[1:],valid[:4]+b'8'+valid[5:],valid+b'00']:
            with self.assertRaises(ValueError):
                decode(damaged,12)

    def test_refuses_ambiguous_usb_identity(self):
        rows=[{'serial':'same','kind':'slcan_fd'},{'serial':'same','kind':'slcan_fd'}]
        with patch('ymbot_usb_canfd.hardware.inventory',return_value=rows):
            with self.assertRaises(RuntimeError):select_device('same','slcan_fd')

    def test_no_hardware_on_invalid_test_request(self):
        with patch('ymbot_usb_canfd.benchmark.open_port') as open_port:
            for kwargs in [{'tx':'same','rx':'same'},{'tx':'a','rx':'b','duration':301},
                           {'tx':'a','rx':'b','mode':'classic','length':64}]:
                with self.assertRaises(ValueError):run(**kwargs)
            open_port.assert_not_called()


if __name__=='__main__':
    unittest.main()
