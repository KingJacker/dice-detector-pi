from matcher_optimized2_vis import matcher
from preprocessor import process
import os

IMAGE_FOLDER = "collected_images"
PROCESSED_FOLDER = "processed"
OUTPUT_FOLDER = "matched"

if __name__ == "__main__":
	image_paths = os.listdir(IMAGE_FOLDER) # get image paths
	print(image_paths)

	for i in range(len(image_paths)):
		

		image_path = f"{IMAGE_FOLDER}/{image_paths[i]}"
		processed_path = f"{PROCESSED_FOLDER}/processed_{i}.jpg"
		matched_path =  f"{OUTPUT_FOLDER}/matched_{i}.jpg"

		print(f"\nProcessing: {image_path}...")

		process(image_path, processed_path)	
		matcher(processed_path, matched_path)

		print(f"\n Done with {matched_path}")