// Test script for Pump Configuration
include <../constants.scad>
include <../modules/common.scad>
include <../modules/housing_pump.scad>

// Test Case 1: Default (Diitao)
translate([-150, 0, 0]) {
    color("Red") text("Diitao", halign="center");
    translate([0,0,20]) Housing_Pump_Case(pump_type="Diitao");
    translate([0,0,20]) Pump_Module_Assembly(pump_type="Diitao");
}

// Test Case 2: Blank
translate([0, 0, 0]) {
    color("Red") text("Blank", halign="center");
    translate([0,0,20]) Housing_Pump_Case(pump_type="Blank");
    translate([0,0,20]) Pump_Module_Assembly(pump_type="Blank");
}

// Test Case 3: Custom
translate([150, 0, 0]) {
    // Note: Custom dimensions are global, so we still need to set them globally if we want to change them.
    // However, since we can't change globals inside a scope in a way that affects modules defined outside,
    // we rely on the default values or would need to pass dimensions as params too.
    // For now, we accept the default custom dimensions defined in constants.scad (27.6, 31.7, 28.0)
    // or we can override them at the top level if this was the only test.
    // To properly test DIFFERENT custom dimensions in the same file, we'd need to parameterize dimensions too.
    // But testing the "Custom" type logic itself is sufficient here.

    color("Red") text("Custom", halign="center");
    translate([0,0,20]) Housing_Pump_Case(pump_type="Custom");
    translate([0,0,20]) Pump_Module_Assembly(pump_type="Custom");
}
