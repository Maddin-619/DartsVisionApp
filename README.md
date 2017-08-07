# DartsVisionApp

This app serves to digitize the steel darts sport. You get the advantages from the e-darts with the steel darts. The app is based on the fact that the darts are recognized by a camera and the points are evaluated automatically. This eliminates the annoying calculation and note the points.<br />
The system hardware is a raspberry pi with a raspberry pi camera. This is located above the dartboard on the ceiling. This software is designed for such a system.

## Description

Core element of the app is the python programm. It is responsable for the darts reconginizion via the camera. It sends the scored points over AMQP middleware to the NodeJs web app.
DartsVisionApp is a web application based on the MEAN stack. It is the user interface. Connecting to the website via Smartphone makes it possible to create players and starts a darts match.

## Requirements
### Hardware

* Raspberry Pi (3)
* Raspberry Pi camera
* [Raspberry case](https://www.rasppishop.de/Nwazet-Pi-Kamera-Gehaeuse-inkl-Linse-und-Wandhalterung-fuer-Raspberry)
* 2 x Dart Board (lights to avoid shadows sometihing like [that](https://www.cht-cottbus.de/philips-linear-led-deckenleuchte-850863116-800lm-weiss.htm?gclid=Cj0KCQjwn6DMBRC0ARIsAHZtCePsOh2S4pL3mSAbM0IRDXYz1-5qu3X60cCUfqp1aZKlXWfRga2CGb0aAgnGEALw_wcB))
* [Relais for Dart Board lights](https://www.amazon.de/gp/product/B00ALNJN72/ref=oh_aui_detailpage_o05_s00?ie=UTF8&psc=1) (install instructions [here](https://www.amazon.de/gp/customer-reviews/R2335YTB9VL42P/ref=cm_cr_getr_d_rvw_ttl?ie=UTF8&ASIN=B00ALNJN72))

### Software

* Linux OS on the Raspberry Pi (Debian, Ubuntu, ...)
* Python 3
* Open CV for Python 3
* NodeJS
* Mongodb
* RabbitMQ

## Install
1. Set up Raspberry Pi with OS and connect it to your local network.

2. Install Python 3
```sh
sudo apt-get install python3 
```

3. Install Open CV with instructions form [here](http://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/)

4. Install NodeJS from [https://nodejs.org](#https://nodejs.org).

5. Install Mongodb:
```sh
sudo apt-get -y install mongodb
```

6. Install RabbitMQ
```sh
sudo apt-get install rabbitmq-server
```

7. Build the project:
```sh
npm install
```

8. Run the server:
```sh
npm start
```

9. Connect with your smartphone via browser:
```sh
raspberrypi:3000
```

## Operation manual

The root page gives an overview about the created players. Here you can create/delete players and look into the statistics. By clicking new game you can create a new game. Select the players and chose the game mode and click on create. Now the game starts. The arrow indicates the players turn. 
When pulling out the darts from the board is recognized that the next player is on the row. If no dart has hit the disk then the hand must once through the aperture of the camera.