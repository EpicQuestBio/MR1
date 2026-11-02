include <constants.scad>
include <modules/common.scad>
include <modules/cartridge.scad>

// Test Script to verify Gasket geometry
// We render both Top and Bottom types side-by-side

module Test_Render() {
    translate([-40, 0, 0]) {
        color("Red") text("Top", halign="center");
        translate([0,0,0]) Gasket_Low_Dead_Volume(type="top");
    }

    translate([40, 0, 0]) {
        color("Blue") text("Bottom", halign="center");
        translate([0,0,0]) Gasket_Low_Dead_Volume(type="bottom");
    }
}

Test_Render();
