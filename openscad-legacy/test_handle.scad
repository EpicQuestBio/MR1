include <constants.scad>
include <modules/common.scad>
include <modules/housing_pump.scad>

corner_r = 12;
z_start = -1;
h_center = 26;
stick_out = 36;
tube_d = 12;

union() {
    // Vertical legs (from z_start up to start of corner curve)
    translate([0, h_center, (stick_out - corner_r + z_start)/2])
        cylinder(d=tube_d, h=stick_out - corner_r - z_start + 0.1, center=true);
    translate([0, -h_center, (stick_out - corner_r + z_start)/2])
        cylinder(d=tube_d, h=stick_out - corner_r - z_start + 0.1, center=true);

    // Horizontal crossbar (between the corner curves)
    translate([0, 0, stick_out])
        rotate([90, 0, 0]) cylinder(d=tube_d, h=(h_center - corner_r)*2 + 0.1, center=true);

    // Rounded corners using sphere instead to be absolutely safe
    translate([0, h_center - corner_r, stick_out - corner_r])
        hull() {
            translate([0, corner_r, 0]) sphere(d=tube_d);
            translate([0, 0, corner_r]) sphere(d=tube_d);
            translate([0, corner_r, corner_r]) cube([tube_d, 0.1, 0.1], center=true); // Anchor to not make it fully spherical
        }
}
