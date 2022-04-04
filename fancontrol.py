#
# fancontrol.py
#
import argparse
import lgpio
import logging
import logging.handlers
import os
import time


def configure_logging():
    """
    Configure the logging

    """

    LOGFILE = "/var/log/rpi-fan-control/rpi-fan-control.log"

    if not os.path.exists(os.path.dirname(LOGFILE)):
        os.makedirs(os.path.dirname(LOGFILE))
    
    logging.basicConfig(
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG,
        handlers=[
            logging.handlers.RotatingFileHandler(
                LOGFILE, 
                mode="a", 
                maxBytes=65536,
                backupCount=1,
            ),
            logging.StreamHandler()
        ]
    )


def get_temperature() -> float:
    """
    Get the CPU temperature

    Returns:
        The CPU temperature

    """
    filename = "/sys/class/thermal/thermal_zone0/temp"
    with open(filename) as infile:
        temperature = float(infile.read()) / 1000.0
        logging.info("Reading CPU temperature = %.1f %%" % temperature)
    return temperature


class Fan(object):
    """
    A class to control the fan speed

    """

    FREQ = 25

    def __init__(self, index: int, pin: int):
        """
        Initialise the fan

        Args:
            index: The GPIO board index
            pin: The GPIO pin

        """
        logging.info("Initialising rpi-fan-control")
        self.pin = pin
        self.h = lgpio.gpiochip_open(index)
        lgpio.gpio_claim_output(self.h, pin)

    def close(self):
        """
        Close the fan

        """
        if self.h is not None:
            logging.info("Exiting rpi-fan-control")
            lgpio.gpiochip_close(self.h)
            self.h = None

    def __enter__(self):
        """
        Enter the context manager

        """
        return self

    def __exit__(self, type, value, traceback):
        """
        Exit the context manager

        """
        self.close()

    def set(self, percent: float):
        """
        Set the fan speed

        Args:
            percent: The percentage speed of the fan

        """
        logging.info("Setting fan speed = %.1f %%" % percent)
        lgpio.tx_pwm(self.h, self.pin, self.FREQ, percent)


 
def control(fan: Fan, tmin: float, tmax: float, interval: int, epsilon: float):
    """
    Control the fan speed by monitoring the temperature

    Args:
        fan: The fan object
        tmin: The minimum temperature (C)
        tmax: The maximum temperature (C)
        interval: The time interval to check the temperature (s)
        epsilon: Set the fan speed if new speed exceed this absolute difference

    """
    previous_speed = 0
   
    while True:
        
        temperature = get_temperature() 

        m = 100.0 / (tmax - tmin)
        c = -m * tmin
        speed = min(max(m * temperature + c, 0.0), 100.0)
            
        if abs(speed - previous_speed) > epsilon:
            fan.set(speed)
            previous_speed = speed
        
        time.sleep(interval)


def run(
        index: int = 0, 
        pin: int = 14, 
        tmin: float = 50, 
        tmax: float = 75, 
        interval: int = 10, 
        epsilon: float = 1):
    """
    Run the fan control script

    Args:
        index: The GPIO board index
        pin: The GPIO pin
        tmin: The minimum temperature (C)
        tmax: The maximum temperature (C)
        interval: The time interval to check the temperature (s)
        epsilon: Set the fan speed if new speed exceed this absolute difference

    """
    with Fan(index, pin) as fan:
        control(fan, tmin, tmax, interval, epsilon)


if __name__ == '__main__':

    configure_logging()
    
    parser = argparse.ArgumentParser(description="Control the fan speed")
    
    parser.add_argument(
        "--pin",
        dest="pin",
        default=14,
        type=int,
        help="The GPIO pin to use to control the fan"
    )

    parser.add_argument(
        "--tmin",
        dest="tmin",
        default=50,
        type=float,
        help="The temperature at which the fan speed will be set to 0%"
    )
    
    parser.add_argument(
        "--tmax",
        dest="tmax",
        default=75,
        type=float,
        help="The temperature at which the fan speed will be set to 100%"
    )
    
    parser.add_argument(
        "--interval",
        dest="interval",
        default=10,
        type=float,
        help="The time interval after which to check the cpu temperature"
    )

    args = parser.parse_args()

    run(0, args.pin, args.tmin, args.tmax, args.interval)
