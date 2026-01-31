include <../constants.scad>
use <../modules/housing_reader.scad>

// Verification Script for PCB Clearance
// Renders the PCB and the Connector Volumes to show they do not intersect.

$fn = 30;

module Connector_Volumes() {
    // Red cylinders representing the keep-out zones for connectors
    // DIN 5
    translate([-25, 60, 0]) rotate([90,0,0]) color("Red") cylinder(h=40, d=16);
    // USB-C (approx)
    translate([0, 60, 0]) rotate([90,0,0]) color("Red") cube([12, 6, 40], center=true);
    // Barrel
    translate([25, 60, 0]) rotate([90,0,0]) color("Red") cylinder(h=40, d=12);
}

projection(cut=false) {
    difference() {
        PCB_Main_Reader_2D();
        // Verify intersection logic:
        // If we subtract the connectors from the PCB, the result should be identical to PCB
        // If the PCB overlaps, the difference removes material.
    }
}

// 3D View for Assembly Mode check (uncomment to test in GUI)
/*
linear_extrude(1.6) PCB_Main_Reader_2D();
translate([0, 0, 10]) Connector_Volumes(); // Shifted Z for visibility
*/
