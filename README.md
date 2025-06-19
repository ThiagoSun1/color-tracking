# Soccer Ball Tracker

A Raspberry Pi-based vision system that **tracks a soccer ball in real time** and records the session using an Arducam IMX519 camera and servo-controlled panning. Built entirely in Python, it uses two LFD-06 servo motors and a PCA9685 controller to physically follow the ball across the field.

---

## ⚽ Overview

This project captures video and automatically follows the **soccer ball** during games or training sessions. The system identifies the ball using color detection and moves the camera using servo motors to keep it in frame. Recordings are saved for later analysis.

---

## 🧠 Features

- 🎯 Tracks a moving soccer ball in real time using OpenCV
- 📷 Records the a soccer match or training session with the Arducam IMX519 and Picamera2
- 🔄 Dual LFD-06 servo motors (pan & tilt) controlled by PCA9685
- ⚙️ Runs entirely on a Raspberry Pi 4 or 5
- 🐍 Written in pure Python with no external apps or software needed

---

## 📦 Hardware Requirements

- Raspberry Pi 5 or 4 (Raspberry Pi OS 64-bit)
- Arducam IMX519 camera
- 2× LFD-06 servo motors
- PCA9685 16-channel PWM servo driver
- External 5–6V power supply for servos
- Tripod or camera mount (optional but useful)

---

## 🧰 Software Requirements

- Python 3.x (pre-installed on Raspberry Pi OS)
- The following Python libraries:

```bash
sudo apt update
sudo apt install python3-pip libcamera-dev -y

pip3 install numpy opencv-python picamera2 adafruit-circuitpython-servokit

sudo raspi-config
# Go to: Interface Options → Enable Camera

sudo raspi-config
# Go to: Interface Options → Enable I2C

# Clone the repository
git clone https://github.com/ThiagoSun1/soccer-ball-tracker.py/tree/main
cd pyPro

# Run the tracker
/usr/bin/python3 recording_track.py

```

## 📄 License

This project is licensed under the [MIT License](LICENSE).
