import time
import ephem
import serial
import nmea

#Constants
initial_az = 180
initial_alt = 90
min_elevation = 10.0
sleep_time = 1.0
unwind_threshold = 180
sleep_on_unwind = 45.0

default_lat = '-88.787'
default_lon = '41.355'

mount_port = '/dev/ttyUSB0'
arduino_port = '/dev/ttyACM0'

class SerialTester:
    def write(self,line):
        print(line)

    def read(self, num):
        return

class Antenna:
    azimuth = initial_az
    altitude = initial_alt
    parked = True

    def set_position(self, az, alt):
        self.azimuth = az
        self.altitude = alt
        az_int = round(az)
        alt_int = round(alt)
        ser.write(":Sz " + str(az_int) + "*00:00#")
        ser.write(":Sa +" + str(alt_int) + "*00:00#")
        ser.write(":MS#")
        ser.read(64)

    def park(self):
        if (self.parked):
            print('Antenna Parked')
        else:
            print('Parking Antenna')
            self.set_position(initial_az, initial_alt)
            self.parked = True

    def move(self, az, alt):
        if (self.parked):
            self.parked = False
                # Unwrap Cable if Azimuth will cross through True North
                # In the above case, Set Azimuth to 180 Degrees, then pick up
                # normal tracking
                # Then sleep 45 seconds to give the positioner time to
                # reposition
        if ((self.azimuth - az) > unwind_threshold):
            self.set_position(initial_az, self.altitude)
            print('Repositioning to unwrap cable')
            time.sleep(sleep_on_unwind)
        else:
            print('Tracking Mode')
            self.set_position(az, alt)

def reset():
    obs = ephem.Observer()
    #Set LAT/LON Coordinates to IMSA's location
    obs.date = ephem.now()
    obs.lon = default_lon
    obs.lat = default_lat
    obs.elevation = 0.0
    return obs

def update(nmea):
    obs = ephem.Observer()
    try:
        if nmea.is_fixed() and nmea.checksum():
            datetime = nmea.get_date() + " " + nmea.get_time()
            obs.date = datetime
            obs.lat = str(nmea.get_lat())
            obs.lon = str(nmea.get_lon())
            true_heading = nmea.get_magnetic_heading() + nmea.get_magnetic_var()
            return obs, true_heading
        else:
            print("GPS Fix Not Found: using default location...")
            return reset(), 0.0
    except:
        print("GPS Fix Not Found: using default location...")
        return reset(), 0.0


def setup_serial(port, baud):
    # Set Serial Port - USB0
    ser = serial.Serial(port, baud, timeout=1)
    print("Current Port Used is " + ser.name)
    return ser
    #return SerialTester()

def setup_satellite():
    # Read in TLE for target satellite ICO F2
    icof2 = ephem.readtle('ICO F2',
               '1 26857U 01026A   16172.60175106 -.00000043  00000-0  00000+0 0  9997',
               '2 26857 044.9783   5.1953 0013193 227.2968 127.4685 03.92441898218058')
    return icof2

def to_degrees(radians):
    return radians / ephem.degree

def get_sat_position(icof2, home):
    icof2.compute(home)
    icof2_az = to_degrees(icof2.az)
    icof2_alt = to_degrees(icof2.alt)
    print('Current Satellite Location: Azimuth %3.2f deg, \
    Altitude %3.2f deg' % (icof2_az, icof2_alt))
    return icof2_az, icof2_alt

def read_nmea(port):
    port.flushInput()
    port.readline()
    try:
        line = port.readline().decode("ascii").replace('\r', '').replace('\n', '')
    except:
        line = ""
    return line

def nmea_tester(sentence):
    mes = nmea.nmea(sentence)
    print("Checksum: ")
    print(mes.checksum())
    print("Reformatted Date & Time: ")
    print(mes.get_date())
    print(mes.get_time())
    print("Lat, Lon: ")
    print(str(mes.get_lat()) + ", " + str(mes.get_lon()))
    print("Heading, MagVar")
    print(str(mes.get_magnetic_heading()) + ", " + str(mes.get_magnetic_var()))

def arduino_tester():
    ard = setup_serial(arduino_port, 115200)
    icof2 = setup_satellite()
    while True:
        try:
            line = read_nmea(ard)
            home = reset()
            home, heading = update(nmea.nmea(line))
            print(home.lat)
            print(home.lon)
            print(home.date)
        except:
            break

#Tests NMEA parser
#sentence = "$GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*62,131.76"
#nmea_tester(sentence)


#Tests Arduino Reader -> observer interface
#arduino_tester()

#Test serial comms to
home = reset()
ser = SerialTester()
ard = setup_serial(arduino_port, 115200)
icof2 = setup_satellite()
antenna = Antenna()
heading = 0.0
counter = time.time()
while True:
    mes = nmea.nmea(read_nmea(ard))
    # home.date = "2016-06-28 12:00:00"

        # Operate the antenna if the satellite's elevation is greater than 10
        # degrees
        # If the elevation IS above 10 degrees and the antenna is parked, then
        # unlatch the park_latch variable
    if time.time()-counter >= sleep_time:
        home, heading = update(mes)
        icof2_az, icof2_alt = get_sat_position(icof2, home)
        if (icof2_alt >= min_elevation):
            antenna.move(icof2_az - heading, icof2_alt)
        else:
            antenna.park()
        counter = time.time()
