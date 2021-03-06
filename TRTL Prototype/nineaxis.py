"""Module to retrieve 9-axis data for parsing and enjoyment.

IMPORTANT:
    Make sure the write time for the arduino code properly syncs up with the
    read time of the python code. If they aren't in sync then you will get the
    wrong data!

The 9-axis is most accurate when each individual sensor is calibrated. The
calibration is outputted as an integer from 0 to 3, where 0 is not calibrated
and 3 is fully calibrated. To calibrate each sensor, perform the following:
    SYS:
        The system fusion will calibrate when everything else is calibrated.
        Calibrate the other sensors and it will calibrate momentarily.
    GYRO:
        The gyroscope will calibrate easily, just rest it on a flat surface for
        a short time, it's quick.
    ACCEL:
        Rotate the 9-axis at 45° angles and hold it for a few seconds each
        increment and it will calibrate.
    MAG:
        Move the 9-axis in a figure-eight/infinity motion and it will
        calibrate.
"""

import serial
import time


class NineAxis:
    """9-Axis Absolute Orientation class.

    NineAxis reads from the serial port a comma delimited string
    in the following format:
        x, y, z, sys_cal, gyro_cal, accel_cal, mag_cal
    """

    def __init__(self, port, baud=9600):
        """Constructor method, initialize with port and baudrate."""
        self.ser = serial.Serial(port, baud)
        time.sleep(5)
        self.ser.reset_input_buffer()
        # Split out the escape characters and the byte formatter
        self.refresh()

    def refresh(self):
        """Read from serial and format."""
        self.info = self.read_nineaxis()
        try:
            self.info = [float(x) for x in self.info]
        except ValueError:
            self.info = [0, 0, 0, 0, 0, 0, 0]
        (self.x, self.y, self.z, self.sys_cal, self.gyro_cal,
         self.accel_cal, self.mag_cal) = self.info

    def read_nineaxis(self):
        """Return a list of strings read from the serial.

        It slices out the control characters at the beginning and end of the
        string and splits it by commas.
        """
        return str(self.ser.readline())[2:-5].split(',')
