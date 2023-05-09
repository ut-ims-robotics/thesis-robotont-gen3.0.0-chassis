# Laser Display Parser

This script performs number detection from the screen of a Keyence LK-G82 measurement laser.
The script can be operate both on continuous camera stream and on single images.
An example image named `display_example.png` has been provided for testing purposes.

## Usage

To run the script in either stream or test mode, run it from command line with

```bash
$ ./laser_digit_detector.py stream
#or
$ ./laser_digit_detector.py test
```

The script uses OpenCV and NumPy, which have to be installed in the Python environment used for running the script.
The required Python packages are listed in the `requirements.txt` file which can be used to install the packages with the Terminal command `python3 -m pip install -r requirements.txt`.
