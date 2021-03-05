import serial
import sys
import argparse
from io import BytesIO
from PIL import Image
from enum import IntEnum, auto

SERIAL_PORT_NAME: str = "/dev/ttyUSB0"  # Default value

class BytePosition(IntEnum):
    """
    See send_start_byte docstring for more details
    """
    SAVE = 0
    ZIPPED = auto()
    SET_RR = auto()
    RESERVED_FOR_FUTURE_USE_1 = auto()
    RESERVED_FOR_FUTURE_USE_2 = auto()
    RESERVED_FOR_FUTURE_USE_3 = auto()
    START = auto()
    CLEAR = auto()

class ProtocolHandler:
    def __init__(self, serial_port: serial.Serial) -> None:
        """
        Initializator
        :param serial.Serial serial_port: Open and active serial port over which send the data
        :return: Nothing
        :rtype: None
        """
        self.serial_port: serial.Serial = serial_port
    
    def __send_start_byte(self, clear: bool = False, start: bool = False, set_rr: bool = False, zipped: bool = False, save: bool = False) -> None:
        """
        Compose and send protocol's start byte. Parameters are sorted from the one with the highest priority to the one with the lowest priority
        :param bool clear: Clear embedded device's frame buffer. Highest priority, mutual exclusion. If it is equal to True no payload expected
        :param bool start: Start or stop animation on the embedded device. When equals to True the animation starts (no payload expected, but you can set refresh-rate), otherwise the payload is added to the frame buffer
        :param bool set_rr: Set refresh-rate. Mutual exclusion. If equals to True 1 byte of payload expected; the payload must represent the refresh rate as ms(/portTICK_MS)
        :param bool zipped: If True the embedded device will unzip the frame
        :param bool save: Does the frame belong to an animation? If True the frame is saved in the frame buffer, otherwise is displayed immediately
        """
        sb: int = 0x00 \
                | ((0x01 << int(BytePosition.CLEAR)) if clear else 0x00) \
                | ((0x01 << int(BytePosition.START)) if start else 0x00) \
                | ((0x01 << int(BytePosition.SET_RR)) if set_rr else 0x00) \
                | ((0x01 << int(BytePosition.ZIPPED)) if zipped else 0x00) \
                | ((0x01 << int(BytePosition.SAVE)) if save else 0x00)
        start_byte: bytes = bytes([sb])
        # print(start_byte)
        self.serial_port.write(start_byte)

    def __send_stop_byte(self) -> None:
        """
        Send protocol's stop byte: 0x00
        """
        pass

    def __check_ack(self) -> bool:
        pass

    def send_bitmap(self, buf: bytes) -> None:
        """
        Send a series of bytes to the embedded device. Store these bytes and save them into the frame buffer
        :param bytes buf: bytes of which the bitmap image is made up of
        """
        self.__send_start_byte(zipped = True, save = True)
        assert self.__check_ack()
        self.serial_port.write(buf)
        self.__send_stop_byte()
        assert self.__check_ack()

    def set_refresh_rate(self, rr: int) -> None:
        """
        Set animation's refresh rate
        :param int rr: Refresh Rate value in milliseconds (later divided by portTICK_MS on the ESP32 MCU)
        """
        self.__send_start_byte(set_rr = True)
        assert self.__check_ack()
        self.serial_port.write(byte([rr]))
        self.__send_stop_byte()
        assert self.__check_ack()

    def start(self) -> None:
        """
        Start animation
        """
        self.__send_start_byte(start = True)
        assert self.__check_ack()
        self.__send_stop_byte()
        assert self.__check_ack()

    def clear(self) -> None:
        """
        Clear embedded device's frame buffer
        """
        self.__send_start_byte(clear = True)
        assert self.__check_ack()
        self.__send_stop_byte()
        assert self.__check_ack()


def main(serial_port_name: str, show: bool) -> None:
    stdin_img_bytes = BytesIO(sys.stdin.buffer.read())
    if show:
        im = Image.open(stdin_img_bytes)
        im.show()
    with serial.Serial(port=serial_port_name, baudrate=115200, bytesize=8, parity='N', stopbits=1) as serial_port:
        handler: ProtocolHandler = ProtocolHandler(serial_port)
        # handler.send(stdin_img_bytes.getvalue())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help='Serial port name', type=str, default=SERIAL_PORT_NAME)
    parser.add_argument('-s', '--show', help='Show piped image', default=False, action='store_true')
    args = parser.parse_args()
    main(args.port, args.show)

