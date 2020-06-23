# oslac - Open Source Load and Air-conditioning Controller
OSLAC provides a blueprint to build load controllers for any Modbus over WiFi System, with Raspberry Pi SBCs.

This project was developed with a LEAN development technique. The Fronius inverter was simply chosen due to the pre-existance of the stoberblog repo (Item 3 below). This allowed rapid prototyping. Most of the project time was spent on system design. This package is provided as-is under an MIT licence. It will need improvement and cloud integration to be deployed as a commercial load controller. However, it is a good base for beginning this task. 

MIT License:
This repository is offered under an MIT license see: LICENSE.md


The repo is structured as follows:

* OSLAC_PCB/outputs: These mask files can be sent direct to PCB manufacturers to have base boards built. 
* OSLAC PCB/fritzing_design: are the design files in Fritzing open source PCB software. 
* OSLAC PCB/BOM: has the full bill of materials to build the base board. 

* OSLAC_SOFTWARE: Includes the links to all software to build the AS-IS prototype, and a README.md of how to build the Raspberry Pi software.
