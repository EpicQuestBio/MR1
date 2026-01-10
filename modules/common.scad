// Vertical Cable Slot Definition
module Cable_Slot() {
    // Slot for JST cable passing down to the reader
    // Located at "Front" (Y negative, angle 270)
    translate([0, -26, 0])
        cube([12, 5, 200], center=true);
}

module BoltHoles() {
    for(r = [45:90:360]) {
        rotate([0,0,r]) translate([screw_bcd/2, 0]) circle(d=screw_hole);
    }
}

module PogoPinHoles() {
    // Pogo Pins removed for Single-Sided PCBA
    // Keeping module for compatibility but empty
}

// O_Ring_Inner: Seals Fluid Path to Potting Puck
module O_Ring_Inner() {
    // Standard Torus
    color("DeepSkyBlue")
    rotate_extrude($fn=g_fn)
    translate([oring_id/2 + oring_cs/2, 0, 0]) // ID + CS/2 = Center Radius
    circle(d=oring_cs, $fn=g_fn);
}
