# Design and production files

## Folder structure

There are separate folders for every file type.
The folders contain the following file types:

* step: STEP files for 3D CAD models editable with most CAD programs;
* stl: STL files for geometry data readable by most slicer software;
* 3mf: 3MF files for 3D-printer configuration and detail groupings;
* gcode: G-code files for printing the chassis parts with optimised parameters with a Prusa MK3S+ 3D printer.

## Part naming

**STEP and STL files**

The parts are divided into four modules:

* frame module
* motor module
* camera module
* computer module

The part files are named as follows:

`module_[submodule_]part.extension`

For example, the STEP file for the front part of the top plate of the frame module is named `frame_top_front.STEP`.


**3MF and G-code files**

The parts are divided into printgroups for optimised 3D printing.
The groupings contain the following parts:

![Robotont gen3.0.0 printgroups](https://github.com/ut-ims-robotics/thesis-robotont-gen3.0.0-chassis/blob/main/images/printgroups.png "Robotont gen3.0.0 printgroups")
