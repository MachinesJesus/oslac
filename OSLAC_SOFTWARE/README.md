#The Steps to build OSLAC

* Step A.
Install Raspbian on Raspberry Pi.
 
* Step B.
Download all three packages: 
1. This repo @ https://github.com/MachinesJesus/oslac (MIT licence)
2. Pi WiFi Dash developed by Valmcc (at the cost of RER) @ https://github.com/valmcc/pi-wifi-dash (Note RER approved Pi WiFi Dash release under MIT licence).
3. Sunspec modbus by stoberblog (MIT licence) @ https://github.com/stoberblog/sunspec-modbus

* Step C. 
Install 1 on a Raspberry Pi and check working. 

* Step D. 
Copy the file 'OSLAC_control.py' into the downloaded directory (inside the folder) 'sunspec-modbus-master' obtained from 3.

* Step E.
Manually setup a static IP on your inverter. Check your inverter IP by going to IP "192.168.1.xxx" on a computer connected to your LAN. You should see the Inverters StartPage. Modbus TCP/IP access must also be enabled and the inverter connected to your WiFi.

* Step F.
Alter the 'configuration.py' within directory 'sunspec-modbus-master' to:
INVERTER_IP = "192.168.1.xxx"
MODBUS_PORT = 502  #not 7502

* Step G. 
Create cron-job on the Raspberry Pi to start 'OSLAC_control.py' around 60 seconds after the startup of the Raspberry Pi. Time should be allowed for the Pi WiFI Dash to start. 


This completes the (AS-IS) setup, feel free to contribute to this repo.  :D

