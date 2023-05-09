#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Laser Display Parser

This script performs number detection from the screen of Keyence LK-G82
measurement laser. It is assumed that the camera is facing the screen
directly and from a distance of approximately 10-20 cm.

This script requires the cv2 and numpy libraries to be installed within
the Python environment used for running this script.

The script writes the detected reading into a text file located in the
same directory as the script. The text file is named in the following
pattern: "results_YYYY-MM-DD HH:MM:SS.SSSSSS.txt"

The script uses a STREAM_MODE variable to process either the camera
stream or a single input image. Single image mode is useful for testing
and for setting up thresholding parameters. Mode can be set with command
line parameter "stream" or "test" (default is stream). GUI parameters
are saved in gui_values.txt and are updated in the file if they have been
changed during script runtime and the program is closed by pressing "q".

This file can also be imported as a module and contains
the following functions:

    * init_camera - initialises and sets up camera object
    * init_gui - sets up GUI for interactive parameter control
    * get_digits_lookup - returns a look-up dictionary for matching
		7-segment LED patterns to their corresponding numbers
    * main - the main function of the script
"""

import cv2
import numpy as np
import os
import sys
import time
from copy import deepcopy
from datetime import datetime

# Path of script
SCRIPT_PATH = os.path.dirname(__file__)
print(f"Reading script from path: {SCRIPT_PATH}\n")


def init_camera(camera_id:int=0) -> cv2.VideoCapture:
	""" Initialises and sets up camera object

	Args:
		camera_id (int): Identifier of camera device (usually ranges
			from 0 to 4), depends on system setup (default is 0)
	
	Returns:
		camera: a cv2.VideoCapture object that enables interfacing with
			camera hardware
	"""

	camera = cv2.VideoCapture(camera_id)
	# Disable automatic exposure correction
	camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
	# Disable automatic white balance correction
	camera.set(cv2.CAP_PROP_AUTO_WB, 0)
	# Disable auto-focus, set initial manual focus value
	camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
	focus = 28  # min: 0, max: 255, increment later multiplied with 5
	camera.set(cv2.CAP_PROP_FOCUS, focus)
	# Set buffer size to 1 to always have the newest frame
	camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

	return camera


def init_gui(win_name:str) -> None:
	""" Initialises and sets up the GUI with trackbars for interactively
		changing parameters during runtime

	Args:
		win_name (str): Name of the GUI window
	
	Returns:
		None
	"""
	# Setup thresholding ranges from GUI values text file
	with open(os.path.join(SCRIPT_PATH, "gui_values.txt"), "r") as gui_file:
		values = [int(row.strip()) for row in gui_file]

	lh = values[0] # low hue
	ls = values[1] # low saturation
	lv = values[2] # low value
	hh = values[3] # high hue
	hs = values[4] # high saturation
	hv = values[5] # high value
	focus = values[6] # initial focus value

	cv2.namedWindow(win_name, cv2.WINDOW_AUTOSIZE)
	# Setup trackbars for changing thresholding ranges
	cv2.createTrackbar("low_H", win_name, lh, 179, lambda x: None)
	cv2.createTrackbar("low_S", win_name, ls, 255, lambda x: None)
	cv2.createTrackbar("low_V", win_name, lv, 255, lambda x: None)
	cv2.createTrackbar("high_H", win_name, hh, 179, lambda x: None)
	cv2.createTrackbar("high_S", win_name, hs, 255, lambda x: None)
	cv2.createTrackbar("high_V", win_name, hv, 255, lambda x: None)
	cv2.createTrackbar("focus", win_name, focus, 255//5, lambda x: None)


def get_digits_lookup() -> dict:
	""" Defines a look-up dictionary for getting numbers by their
		corresponding 7-segment LED patterns

	Args:
		None

	Returns:
		DIGITS_LOOKUP: a dictionary where keys are segment patterns
			and values are their corresponding numbers
	"""

	# Dictionary of 7-segment LED segments corresponding to numbers
	DIGITS_LOOKUP = {
		(1, 1, 1, 0, 1, 1, 1): "0",
		(0, 0, 1, 0, 0, 1, 0): "1",
		(1, 0, 1, 1, 1, 0, 1): "2",
		(1, 0, 1, 1, 0, 1, 1): "3",
		(0, 1, 1, 1, 0, 1, 0): "4",
		(1, 1, 0, 1, 0, 1, 1): "5",
		(1, 1, 0, 1, 1, 1, 1): "6",
		(1, 0, 1, 0, 0, 1, 0): "7",
		(1, 1, 1, 1, 1, 1, 1): "8",
		(1, 1, 1, 1, 0, 1, 1): "9",
		(0, 0, 0, 1, 0, 0, 0): "-"
	}
	return DIGITS_LOOKUP


def main():
	print("Welcome to Laser Display Parser!\nPress 'q' to exit.")
	time.sleep(2)

	# Setup
	gui_window = "Image"
	init_gui(gui_window)
	DIGITS_LOOKUP = get_digits_lookup()

	# Set mode to camera stream (True) or single example image (False)
	if len(sys.argv) == 2 and sys.argv[1] == "test":
		STREAM_MODE = False
	else:
		STREAM_MODE = True

	if STREAM_MODE:
		camera = init_camera(0)
	else:
		orig_image = cv2.imread(os.path.join(SCRIPT_PATH, "display_example.png")) # Load test image

	# Initialise timer for maintaining constant frequency
	prev_image_time = time.time()
	# Open text file for detection results with a unique name
	results = open(os.path.join(SCRIPT_PATH, f"results_{datetime.now()}.txt"), "w")

	while True:
		# Set focus, can only be changed in increments of 5
		if STREAM_MODE: camera.set(cv2.CAP_PROP_FOCUS, cv2.getTrackbarPos("focus", gui_window) * 5)

		if time.time() >= prev_image_time + 1: # Operate at 1 Hz
			prev_image_time = time.time() # Restart timer
			
			if STREAM_MODE:
				# Read newest frame from camera
				_, rgb_image = camera.read()
			else:
				rgb_image = deepcopy(orig_image)

			# Convert image to HSV colour space to aid colour detection
			image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2HSV)

			# Threshold image based user-defined HSV channel ranges
			thres = cv2.inRange(image, (cv2.getTrackbarPos("low_H", gui_window), cv2.getTrackbarPos("low_S", gui_window), cv2.getTrackbarPos("low_V", gui_window)), (cv2.getTrackbarPos("high_H", gui_window), cv2.getTrackbarPos("high_S", gui_window), cv2.getTrackbarPos("high_V", gui_window)))
			cv2.imshow(gui_window, thres)

			# Find display-ROI for laser display
			roi = np.nonzero(thres)

			if len(roi[0]) > 0:
				# Take area between white pixels' min-max coordinates
				thres = thres[min(roi[0]):max(roi[0]), min(roi[1]):max(roi[1])]
				# Remove upper area that only contains indicator LED
				thres = thres[thres.shape[0]//4:]

			# Perform morphology on display-ROI for improved detection
			kernel = np.ones((2,2), np.uint8)
			thres = cv2.morphologyEx(thres, cv2.MORPH_CLOSE, kernel)
			cv2.imshow("ROI", thres)

			# Setup for dividing display into digits
			digit_width_weights = np.array([15, 32, 35, 33, 34, 35])
			one_row_len = thres.shape[1]
			mult = one_row_len / sum(digit_width_weights)
			space = one_row_len // 25
			digit_widths = (digit_width_weights * mult).astype(int)

			# Divide display into digit-ROI's
			digits = []
			for i in range(6):
				start_i = sum(digit_widths[:i])
				if i != 0: start_i += space * 2
				end_i = sum(digit_widths[:i+1]) + space
				digits.append(thres[:, start_i:end_i])
			
			laser_reading = []
			# Loop over each of the digits
			for _, digit in enumerate(digits):
				
				h, w = digit.shape # height, width
				
				# Define the coordinates of the ROI's for all 7 segments
				s = digit.shape[1] // 3 # size of segment-ROI in pixels
				segments = [
					((s, 0), (w - s, s+1)),	# top
					((0, s), (s, h//2 - s+1)), # top-left
					((w - s-1, s), (w, h//2 - s+1)), # top-right
					((s, h//2 - s//2), (w-s, h//2 + s//2 + 1)), # center
					((0, h//2 + s), (s, h - s)), # bottom-left
					((w - s-1, h//2 + s), (w, h - s)), # bottom-right
					((s, h - s-1), (w-s, h)) # bottom
				]

				# List for keeping track of segments that are on
				on_segments = [0] * len(segments)

				# Take segment-ROI's
				for (i, ((start_x, start_y), (end_x, end_y))) in enumerate(segments):
					# Take segment-ROI
					segROI = digit[start_y:end_y, start_x:end_x]
					# Count number of white pixels in the segment-ROI
					white_count = cv2.countNonZero(segROI)
					# Calculate segment area
					area = (end_x - start_x) * (end_y - start_y)
					
					# If the total number of non-zero pixels exceeds 30%
					# of segment-ROI, mark the segment as "on"
					if white_count / float(area) > 0.30:
						on_segments[i] = 1

				# Find digit that matches the pattern of "on" segments
				if tuple(on_segments) in DIGITS_LOOKUP:
					num = DIGITS_LOOKUP[tuple(on_segments)]	
				else:
					num = None

				laser_reading.append(num)

			# Applicable if reading was positive and had no starting -
			if laser_reading[0] == None: laser_reading.pop(0)
			# Combine the result into a number
			# if all digits were read successfully
			if None not in laser_reading:
				laser_reading = int(''.join(laser_reading)) / 10000
			else:
				laser_reading = None
			
			print(f"laser reading: {laser_reading}")

			# Write the laser reading to file
			results.write(str(laser_reading)+"\n")
			
		if (cv2.waitKey(1) & 0xFF) == ord('q'):
			results.close()
			# Write GUI trackbar values into file
			with open(os.path.join(SCRIPT_PATH, "gui_values.txt"), "w") as gui_file:
				gui_file.write(str(cv2.getTrackbarPos("low_H", gui_window)) + "\n")
				gui_file.write(str(cv2.getTrackbarPos("low_S", gui_window)) + "\n")
				gui_file.write(str(cv2.getTrackbarPos("low_V", gui_window)) + "\n")

				gui_file.write(str(cv2.getTrackbarPos("high_H", gui_window)) + "\n")
				gui_file.write(str(cv2.getTrackbarPos("high_S", gui_window)) + "\n")
				gui_file.write(str(cv2.getTrackbarPos("high_V", gui_window)) + "\n")

				gui_file.write(str(cv2.getTrackbarPos("focus", gui_window)))

			break


if __name__ == "__main__":
	main()
