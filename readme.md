# Dice Detector Pi

This project uses a RaspberryPi 5 and a RaspberryPi Camera to identify each number shown by a set number of dice.

## Requirements
- opencv
- rich
- picamera2

## Setup
```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate.sh

sudo arp install libcamera-dev

pip install -r requirements.txt
pip install rpi-libcamera -Csetup-args="-Dversion=unknown"
```

## Run
```bash
python3 main.py
```

| Original | Processed & Matched |
|---|---|
| <img src="res/image.png"> | <img src="res/final_global_masked.jpg"> 