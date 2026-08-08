// modules/elbow_adapter.scad

$fn = 100;

module Elbow_Adapter() {
    difference() {
        union() {
            // Main vertical shaft
            cylinder(d=4.0, h=20.2);

            // Lower collar
            translate([0, 0, 7.7])
            cylinder(d=5.2, h=2.0);

            // Middle flange
            translate([0, 0, 13.4])
            cylinder(d=10.0, h=2.0);

            // Horizontal tube (extends from X=0 to X=14.8)
            translate([0, 0, 20.2])
            rotate([0, 90, 0])
            cylinder(d=6.0, h=14.8);

            // Elbow outer corner (rounded base before chamfer)
            translate([0, 0, 20.2])
            sphere(d=6.0);

            // Luer Lock Lugs (ISO 80369-7 female)
            translate([14.8 - 1.5, 0, 20.2])
            rotate([0, 90, 0])
            intersection() {
                cylinder(d=7.83, h=1.5);
                translate([0, 0, 1.5/2])
                cube([8.0, 5.0, 2.0], center=true);
            }
        }

        // --- Inner Channels ---
        // Vertical Bore (ID 2.5)
        translate([0, 0, -1])
        cylinder(d=2.5, h=21.2);

        // Horizontal Bore (ID 4.0)
        translate([2.0, 0, 20.2])
        rotate([0, 90, 0])
        cylinder(d=4.0, h=14.8 - 7.5 - 2.0 + 0.01);

        // Luer taper (ID 3.82 to 4.27)
        translate([14.8 - 7.5, 0, 20.2])
        rotate([0, 90, 0])
        cylinder(d1=3.82, d2=4.27, h=7.5 + 0.01);

        // Loft between 4.0 and 2.5 ID
        hull() {
            translate([0, 0, 20.2])
            sphere(d=2.5);

            translate([2.0, 0, 20.2])
            rotate([0, 90, 0])
            cylinder(d=4.0, h=0.1);
        }

        // 45-degree chamfer on top-left outer corner
        translate([0, 0, 20.2])
        rotate([0, -45, 0])
        translate([-5, -5, 1.5])
        cube([10, 10, 10]);
    }
}
