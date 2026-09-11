Team 11 image sorting script is contained in this directory

The goal of this script is to grab the 10 red circle (weak point of death star) and set them aside from the 90 dummy images.

Current Idea of script layout: 

- Get the main image sorting operation up and running, this should be the most difficult aspect.
- Have the script dump the correct images into Target.zip.
- Be able to pull images from ImageSorting/Images


Log:
- Created script
- Downloaded 100 random color images from https://github.com/IQAndreas/sample-images
- Used random number generator between 0 and 99 to choose which images have the circle added to them. (Resulted in the choice of images 1,2,8,9,39,42,44,50,57,98)

Requirements before running (For the Raspberry Pi, run in order):

This is mostly installations needed. (Just run these commands on command line)

- sudo apt update 
- sudo apt update
- sudo apt install -y libatlas-base-dev
- sudo apt install -y libjpeg-dev
- sudo apt install -y libopenjp2-7
- sudo apt install -y libtiff5
- (Possible need) sudo apt install -y libtiff6
(Confirming Installations)
- python3 --version
- pip3 --version
- python3 -m pip install opencv-python-headless numpy --break-system-packages