// Vertical Cable Slot Definition
module Cable_Slot() {
    // Slot for ribbon cable passing down to the reader
    // Located against the wall of the hexagon
    translate([0, -27.5, 0])
        cube([13.5, 3.0, 200], center=true);
}

module Cable_Slot_2D() {
    translate([0, -27.5])
        square([13.5, 3.0], center=true);
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

// 1/8" NPT Tapping and Adapter Visualization
module npt_1_8_tapped_hole(h, internal=true) {
    // Standard 1/8" NPT: Major ~10.287mm, Pitch 27 TPI (0.9407mm)
    // Uses BOSL2's threading library. Note: NPT is tapered (1.7899 degrees),
    // but a straight tapped hole can work for shallow plastic threads.
    // The user requested a tapped hole design.
    threaded_rod(d=npt_1_8_thread_d, l=h, pitch=npt_1_8_thread_pitch, internal=internal, anchor=CENTER);
}

module npt_1_8_adapter_visual() {
    // Visual representation of Item 64774: 1/8" Tube ID x 1/8" NPT Natural Polypropylene Threaded Adapter
    // Dimensions approx: 1/2" hex body, 1/4" barb, overall length ~1" (25mm)
    color("White") {
        // Threaded section
        // Note: BOSL2 threaded_rod may not support 'taper' directly depending on version, so using a simple tapered cylinder for the visual if needed, or straight thread. We will use straight thread for visual simplicity.
        down(5) threaded_rod(d=npt_1_8_thread_d, l=10, pitch=npt_1_8_thread_pitch, anchor=BOTTOM);
        // Hex body
        down(5) cyl(h=5, d=13, $fn=6, anchor=TOP);
        // Barb
        down(10) cyl(h=10, d1=4, d2=5, anchor=TOP);
    }
}

// O_Ring_Inner: Seals Fluid Path to Potting Puck
module O_Ring_Inner() {
    // Standard Torus
    color("DeepSkyBlue")
    rotate_extrude($fn=g_fn)
    translate([oring_id/2 + oring_cs/2, 0, 0]) // ID + CS/2 = Center Radius
    circle(d=oring_cs, $fn=g_fn);
}
