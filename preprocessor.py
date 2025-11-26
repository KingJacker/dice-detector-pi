import cv2
import numpy as np

INPUT_PATH = "templates/5.jpg"
PROCESSED_PATH="templates/out"

x_offset = 100
y_offset = 200
radius_scale = 0.55

thresh_value = 200


def process(INPUT_PATH, PROCESSED_PATH):
	img = cv2.imread(INPUT_PATH)

	height, width, _ = img.shape
	center_x = (width // 2) +  x_offset
	center_y = (height // 2) + y_offset

	radius = int(min(width, height) * radius_scale)

	# Create a mask for the circular ROI
	mask = np.zeros(img.shape[:2], dtype="uint8")
	cv2.circle(mask, (center_x, center_y), radius, 255, -1) # Draw filled white circle

	masked_img = cv2.bitwise_and(img, img, mask=mask)

	# Preprocessing
	gray = cv2.cvtColor(masked_img, cv2.COLOR_BGR2GRAY)
	blurred = cv2.GaussianBlur(gray, (15, 15), 0)

	# Thresholding
	_, thresh = cv2.threshold(blurred, thresh_value, 255, cv2.THRESH_BINARY)

	# Morphological operations
	kernel_small = np.ones((3,3), np.uint8)
	kernel_medium = np.ones((5,5), np.uint8)

	eroded_thresh = cv2.erode(thresh, kernel_medium, iterations=1)
	dilated_thresh = cv2.dilate(eroded_thresh, kernel_medium, iterations=1) 
	final_thresh = cv2.morphologyEx(dilated_thresh, cv2.MORPH_CLOSE, kernel_small, iterations=1)

	cv2.imwrite(PROCESSED_PATH, final_thresh)