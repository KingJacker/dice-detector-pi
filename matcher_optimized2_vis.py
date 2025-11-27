import cv2 as cv
from rich.progress import Progress
import os
import numpy as np

# --- CONFIGURATION ---
IMAGE_PATH = "input.jpg"
TEMPLATE_FOLDER = "templates/white_filled"
DEBUG_FOLDER = "matcher-output/debug_maps"
OUTPUT_PATH = "matcher-output/final_global_masked.jpg"

RESIZE_FACTOR = 0.2
SCALES = np.linspace(0.8, 1.2, 5) 
ROTATIONS = np.linspace(-90, 90, 16)
SCORE_THRESHOLD = 0.60
OVERLAP_THRESHOLD = 0.2 
MAX_DICE = 6 

# Ensure debug folder exists
os.makedirs(DEBUG_FOLDER, exist_ok=True)

def get_rotated_template(image, angle):
	h, w = image.shape[:2]
	center = (w // 2, h // 2)
	M = cv.getRotationMatrix2D(center, angle, 1.0)
	rotated = cv.warpAffine(image, M, (w, h), borderMode=cv.BORDER_CONSTANT, borderValue=(0,0,0))
	return rotated

def save_heatmap_visualization(heatmap, die_number):
	norm_map = cv.normalize(heatmap, None, 0, 255, cv.NORM_MINMAX, cv.CV_8U)
	color_map = cv.applyColorMap(norm_map, cv.COLORMAP_JET)
	cv.imwrite(f"{DEBUG_FOLDER}/heatmap_die_{die_number}.jpg", color_map)

def draw_candidate_cloud(img, candidates):
	accumulator = np.zeros(img.shape, dtype=np.uint16)
	
	step_color = (20, 20, 0) 
	
	scratch = np.zeros(img.shape, dtype=np.uint8)
	for cand in candidates:
		scratch.fill(0)
		
		x, y = cand["center"]
		w, h = cand["box_size"]
		angle = cand["angle"]
		
		center_x = x + w // 2
		center_y = y + h // 2
		rect = ((center_x, center_y), (w, h), -angle)
		box = cv.boxPoints(rect)
		box = np.int32(box)
		
		cv.fillPoly(scratch, [box], step_color)
		
		accumulator += scratch

	heatmap = np.clip(accumulator, 0, 255).astype(np.uint8)
	
	final_vis = cv.addWeighted(img, 0.6, heatmap, 1.0, 0)
	
	cv.imwrite(f"{DEBUG_FOLDER}/debug_00_all_candidates_cloud.jpg", final_vis)
	print(f"Saved Additive Cloud to {DEBUG_FOLDER}/debug_00_all_candidates_cloud.jpg")

def collect_all_candidates(img, templates, scales, rotations_deg, score_threshold):
	candidates = []
	
	small_img = cv.resize(img, None, fx=RESIZE_FACTOR, fy=RESIZE_FACTOR, interpolation=cv.INTER_AREA)
	h_small, w_small = small_img.shape[:2]
	
	total_steps = len(templates) * len(scales) * len(rotations_deg)

	print(f"\nScanning Image (Resolution factor: {RESIZE_FACTOR})...")

	with Progress() as progress:
		task = progress.add_task("Scanning...", total=total_steps)

		for i, template in enumerate(templates):
			template_number = i + 1
			small_template_base = cv.resize(template, None, fx=RESIZE_FACTOR, fy=RESIZE_FACTOR, interpolation=cv.INTER_AREA)

			composite_heatmap = np.zeros((h_small, w_small), dtype=np.float32)

			for scale in scales:
				if scale != 1:
					current_template = cv.resize(small_template_base, None, fx=scale, fy=scale)
				else:
					current_template = small_template_base

				for angle in rotations_deg:
					rotated_tmpl = get_rotated_template(current_template, angle)
					
					res = cv.matchTemplate(small_img, rotated_tmpl, cv.TM_CCOEFF_NORMED) 
					
					# VISUALIZATION: Update composite heatmap with max values found so far
					# Note: matchTemplate output is smaller than input by (w_templ-1, h_templ-1)
					# We pad it to match size for simple visualization overlay
					h_res, w_res = res.shape
					padded_res = np.zeros((h_small, w_small), dtype=np.float32)
					padded_res[:h_res, :w_res] = res
					
					# Keep the maximum pixel value found at every coordinate
					composite_heatmap = np.maximum(composite_heatmap, padded_res)

					# --- Standard Collection Logic ---
					locs = np.where(res >= score_threshold)
					if len(locs[0]) > 0:
						for pt in zip(*locs[::-1]): 
							score = res[pt[1], pt[0]]
							true_x = int(pt[0] / RESIZE_FACTOR)
							true_y = int(pt[1] / RESIZE_FACTOR)
							
							h_orig, w_orig = template.shape[:2]
							box_w = int(w_orig * scale)
							box_h = int(h_orig * scale)

							candidates.append({
								"score": score,
								"center": (true_x, true_y), 
								"box_size": (box_w, box_h),
								"angle": angle,
								"scale": scale,
								"die_number": template_number,
							})

					progress.update(task, advance=1)
			
			# Save the composite heatmap for this number
			save_heatmap_visualization(composite_heatmap, template_number)

	return candidates

def apply_global_masking(candidates, img):
	"""
	Sorts by score and fills a global occupancy mask.
	Saves debug images for every step.
	"""
	img_shape = img.shape
	candidates.sort(key=lambda x: x["score"], reverse=True)
	
	final_matches = []
	occupancy_mask = np.zeros((img_shape[0], img_shape[1]), dtype=np.uint8)
	
	# Visualization: Copy original image to draw steps on
	debug_step_img = img.copy()

	print(f"\nProcessing {len(candidates)} potential candidates with Global Masking...")
	
	step_count = 0

	for cand in candidates:
		score = cand["score"]
		x, y = cand["center"]
		w, h = cand["box_size"]
		angle = cand["angle"]
		
		center_x = x + w // 2
		center_y = y + h // 2
		
		candidate_mask = np.zeros_like(occupancy_mask)
		rect = ((center_x, center_y), (w, h), -angle)
		box = cv.boxPoints(rect)
		box = np.int32(box)
		
		cv.fillPoly(candidate_mask, [box], 255)
		
		overlap = cv.bitwise_and(occupancy_mask, candidate_mask)
		overlap_pixels = cv.countNonZero(overlap)
		candidate_area = cv.countNonZero(candidate_mask)
		if candidate_area == 0: continue 
		
		overlap_ratio = overlap_pixels / candidate_area
		
		if overlap_ratio < OVERLAP_THRESHOLD:
			final_matches.append(cand)
			cv.fillPoly(occupancy_mask, [box], 255)
			
			# --- VISUALIZATION: Save the "Accepted" Step ---
			step_count += 1
			# Draw green box
			cv.drawContours(debug_step_img, [box], 0, (0, 255, 0), 3)
			# Draw label
			cv.putText(debug_step_img, str(cand['die_number']), (center_x, center_y), 
					   cv.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
			
			# cv.imwrite(f"{DEBUG_FOLDER}/debug_step_{step_count:02d}_found_die_{cand['die_number']}.jpg", debug_step_img)
			print(f"Accepted Die {cand['die_number']} (Score: {score:.2f})")
			
			if len(final_matches) >= MAX_DICE:
				break
	
	# Save final mask
	cv.imwrite(f"{DEBUG_FOLDER}/debug_99_final_mask.jpg", occupancy_mask)
	return final_matches

def draw_results(img, matches):
	out_img = img.copy()
	counts = np.zeros(MAX_DICE+1, dtype=int)
	
	for m in matches:
		die_num = m["die_number"]
		x, y = m["center"]
		w, h = m["box_size"]
		angle = m["angle"]
		
		center_x = x + w // 2
		center_y = y + h // 2
		
		rect = ((center_x, center_y), (w, h), -angle)
		box = cv.boxPoints(rect)
		box = np.int32(box)

		cv.drawContours(out_img, [box], 0, (0, 255, 0), 4)
		cv.putText(out_img, str(die_num), (center_x - 25, center_y + 20), cv.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 8)
		
		counts[die_num] += 1
		
	return out_img, counts

def load_templates(template_folder):
	print("\nLoading Templates...")
	if not os.path.exists(template_folder):
		print(f"Error: Template folder {template_folder} does not exist.")
		return []
	files = sorted(os.listdir(template_folder)) 
	templates = []
	for file in files:
		if file.lower().endswith(('.png', '.jpg', '.jpeg')):
			# print(f"Loaded: {file}")
			img = cv.imread(os.path.join(template_folder, file))
			templates.append(img)
	return templates


# funciton to import
def matcher(IMAGE_PATH):
	img = cv.imread(IMAGE_PATH)

	if img is None:
		print(f"Error loading image: {IMAGE_PATH}")
	else:
		templates = load_templates(TEMPLATE_FOLDER)
		if not templates:
			return

		# 1. Collect candidates + Save Heatmaps
		candidates = collect_all_candidates(img, templates, SCALES, ROTATIONS, SCORE_THRESHOLD)

		# 2. Visualize the "Cloud" of all detections
		# draw_candidate_cloud(img, candidates)

		# 3. Filter using Global Occupancy Mask + Save Step-by-Step
		final_matches = apply_global_masking(candidates, img)

		# 4. Draw Final Results
		out_img, counts = draw_results(img, final_matches)

		print("\nFinal Counts:")
		for i in range(1, MAX_DICE+1):
			print(f"{i} Eyes: {counts[i]}")

		cv.imwrite(OUTPUT_PATH, out_img)
		print(f"\nProcessing Complete.")


# --- MAIN EXECUTION ---

def main():
	img = cv.imread(IMAGE_PATH)

	if img is None:
		print(f"Error loading image: {IMAGE_PATH}")
	else:
		templates = load_templates(TEMPLATE_FOLDER)
		if not templates:
			return

		# 1. Collect candidates + Save Heatmaps
		candidates = collect_all_candidates(img, templates, SCALES, ROTATIONS, SCORE_THRESHOLD)

		# 2. Visualize the "Cloud" of all detections
		draw_candidate_cloud(img, candidates)

		# 3. Filter using Global Occupancy Mask + Save Step-by-Step
		final_matches = apply_global_masking(candidates, img)

		# 4. Draw Final Results
		out_img, counts = draw_results(img, final_matches)

		print("\nFinal Counts:")
		for i in range(1, MAX_DICE+1):
			print(f"{i} Eyes: {counts[i]}")

		cv.imwrite(OUTPUT_PATH, out_img)
		print(f"\nProcessing Complete.")
		print(f"1. Check '{DEBUG_FOLDER}' to see Heatmaps, Candidate Cloud, and Step-by-Step detection.")
		print(f"2. Final result saved to '{OUTPUT_PATH}'")

if __name__ == "__main__":
	main()