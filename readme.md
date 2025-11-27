# Dice Detector Pi

This project uses a RaspberryPi 5 and a RaspberryPi Camera to identify each number shown by a set number of dice.

## Requirements
- opencv
- rich
- picamera2
- libcamera-dev

## Setup
```bash
git clone https://github.com/KingJacker/dice-detector-pi.git
cd dice-detector-pi

python3 -m venv --system-site-packages venv
source venv/bin/activate.sh

sudo arp install libcamera-dev

pip install -r requirements.txt
pip install rpi-libcamera -Csetup-args="-Dversion=unknown"
```

## Run
```bash
source venv/bin/activate.sh
python3 main.py
```

Find the resulting processed image in `matcher-output/final_global_masked.jpg`.

## Demo
In the Folder `scripts` you can find scripts that work independently of the camera. 20 pictures of dice were taken and processed.
- Input images: `scripts/collected_images`
- Preprocessed images: `scripts/processed`
- Matched images: `scripts/matched`

View the results here [demo.md](demo.md)

### Example
| Original | Processed & Matched |
|---|---|
| <img src="res/image.png"> | <img src="res/final_global_masked.jpg"> 

## Performance

Preprocessing is very fast: < 1 second

Matching takes about 30 seconds and is very dependent on search parameters. The downscaling of the image imporves the search speed significantly.