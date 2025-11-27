from picamera2 import Picamera2
from led import LED
import time

IMAGE_FOLDER = "collected_images"


def shoot(path="my_picture.jpg"):
	picam2.start(show_preview=False)
	time.sleep(0.2) # Give the camera time to adjust exposure/white balance

	filepath = image_folder+path
	picam2.capture_file(filepath)
	picam2.stop()




try: 
	myhandler = 4 # led handler chip
	led1 = LED(14, myhandler)
	led2 = LED(15, myhandler)

	picam2 = Picamera2()
	camera_config = picam2.create_still_configuration(main={"size": (3280, 2464)})
	picam2.configure(camera_config)

	for i in range(20):
		print(f"Taking image: {i}")

		led1.on()
		led2.on()

		picam2.start(show_preview=False)
		time.sleep(2)
		picam2.capture_file(f"{IMAGE_FOLDER}/image_{i}.jpg")

		led1.off()
		led2.off()

		time.sleep(5)

except Exception as e:
	print(f"Error: {e}")

finally:
	picam2.stop()
	led1.off()
	led2.off()
	led1.free()
	led2.free()
	print("Cleanup done.")
