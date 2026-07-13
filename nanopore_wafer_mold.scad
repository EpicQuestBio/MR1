// ==============================================================================
// SENTINEL NANOPORE READER - 2-PART SILICONE MOLD FOR NANOPORE WAFER
// Generates a 3D printable compression mold to cast the hexagonal gasket
// with an embedded silicon square nanopore wafer.
// ==============================================================================

include <constants.scad>
include <modules/common.scad>

// Mold Plate Dimensions
mold_margin = 10;
mold_w = hex_diam + mold_margin * 2; // ~80mm
mold_l = hex_diam + mold_margin * 2; // ~80mm
mold_thick = 8.0;                    // Thickness of each mold half plate

// Alignment Bolt/Pin Settings
bolt_d = 3.2;         // M3 bolt/pin clearance
bolt_head_d = 6.0;    // M3 cap head diameter
bolt_head_depth = 3.0; // Recess depth for flush bolt heads
bolt_offset = mold_w/2 - 5; // Near the 4 corners

// Squeeze-out (overflow) channel dimensions
overflow_w = 2.0;
overflow_depth = 1.0;

module Wafer_Visual() {
    color("Dimgrey") {
        difference() {
            // Square wafer substrate
            cube([wafer_size, wafer_size, wafer_thick], center=true);

            // Central nanopore aperture (visual drill)
            cylinder(h=wafer_thick+1, d=0.5, center=true, $fn=16);
        }
    }
    // Nanopore itself (tiny black dot at the center)
    color("Black") sphere(d=0.2, $fn=8);
}

module Corner_Guides(wafer_s=wafer_size, guide_w=1.5, height) {
    difference() {
        // 4 outer blocks at the corners
        union() {
            for(s = [-1, 1], t = [-1, 1]) {
                translate([s * (wafer_s/2 + guide_w/2), t * (wafer_s/2 + guide_w/2), height/2])
                    cube([guide_w, guide_w, height], center=true);
            }
        }
        // Subtract the wafer space to make clean L-brackets
        translate([0, 0, height/2])
            cube([wafer_s, wafer_s, height + 1], center=true);
    }
}

// 1. BOTTOM MOLD HALF
module Nanopore_Wafer_Mold_Bottom(type="top") {
    h_plug = (gasket_thick - wafer_thick) / 2;
    h_guide = (gasket_thick + wafer_thick) / 2;

    // Determine active and passive ports based on gasket type
    active_in = (type=="bottom") ? angle_fluid_in_bot : angle_fluid_in_top;
    active_out = (type=="bottom") ? angle_fluid_out_bot : angle_fluid_out_top;
    pass_angles = (type=="bottom")
        ? [angle_fluid_in_top, angle_fluid_out_top]
        : [angle_fluid_in_bot, angle_fluid_out_bot];

    color("CadetBlue")
    difference() {
        // Main block
        translate([0, 0, mold_thick/2])
            cube([mold_w, mold_l, mold_thick], center=true);

        // A: Hexagonal Gasket Cavity
        translate([0, 0, mold_thick - gasket_thick]) {
            linear_extrude(gasket_thick + 1.0)
                circle(d=hex_diam, $fn=6);
        }

        // B: Finger Grip Cutout clearances (so the gasket finger tabs fit in the mold)
        translate([0, 0, mold_thick - gasket_thick]) {
            linear_extrude(gasket_thick + 1.0)
                Finger_Grip_Cutout_2D();
        }

        // C: Overflow/Squeeze-out Groove around the hex gasket cavity
        translate([0, 0, mold_thick - overflow_depth]) {
            difference() {
                linear_extrude(overflow_depth + 0.1)
                    circle(d=hex_diam + overflow_w*2, $fn=6);
                linear_extrude(overflow_depth + 0.2)
                    circle(d=hex_diam, $fn=6);
            }
        }

        // D: Alignment screw/bolt clearance holes in 4 corners
        for(x = [-bolt_offset, bolt_offset], y = [-bolt_offset, bolt_offset]) {
            translate([x, y, -0.5])
                cylinder(h=mold_thick + 1, d=bolt_d, $fn=32);
            // Nut / bolt head recess on bottom
            translate([x, y, -0.1])
                cylinder(h=bolt_head_depth, d=bolt_head_d, $fn=32);
        }
    }

    // Additive Features (Inside the hex cavity of the bottom mold)
    translate([0, 0, mold_thick - gasket_thick]) {
        // 1. Central cylindrical plug (protects nanopore underside)
        color("Gold")
        cylinder(h=h_plug, d=plug_diameter, $fn=32);

        // 2. Corner registration L-brackets to position the wafer
        color("DarkGoldenrod")
        Corner_Guides(wafer_s=wafer_size, guide_w=1.5, height=h_guide);

        // 3. Passive fluid port pins (through-holes in the cast silicone)
        color("Gold") {
            for(a = pass_angles) {
                rotate([0, 0, a]) translate([port_radius, 0, 0])
                    cylinder(h=gasket_thick, d=2.0, $fn=32);
            }
        }

        // 4. Active fluid port pins and raised flow channel bosses
        color("Gold") {
            // Inlet port pin + channel boss
            rotate([0, 0, active_in]) {
                translate([port_radius, 0, 0])
                    cylinder(h=gasket_thick, d=2.0, $fn=32);
                // Active flow channel boss (leads from port to center plug)
                hull() {
                    translate([port_radius, 0, gasket_thick/2])
                        cylinder(h=gasket_thick, d=1.2, center=true, $fn=16);
                    translate([0, 0, gasket_thick/2])
                        cylinder(h=gasket_thick, d=1.2, center=true, $fn=16);
                }
            }

            // Outlet port pin + channel boss
            rotate([0, 0, active_out]) {
                translate([port_radius, 0, 0])
                    cylinder(h=gasket_thick, d=2.0, $fn=32);
                // Active flow channel boss
                hull() {
                    translate([port_radius, 0, gasket_thick/2])
                        cylinder(h=gasket_thick, d=1.2, center=true, $fn=16);
                    translate([0, 0, gasket_thick/2])
                        cylinder(h=gasket_thick, d=1.2, center=true, $fn=16);
                }
            }
        }
    }
}

// 2. TOP MOLD HALF
module Nanopore_Wafer_Mold_Top(type="top") {
    h_plug = (gasket_thick - wafer_thick) / 2;

    color("SteelBlue")
    difference() {
        // Main block (inverted orientation for assembly/printing)
        translate([0, 0, mold_thick/2])
            cube([mold_w, mold_l, mold_thick], center=true);

        // Alignment bolt/pin clearance holes
        for(x = [-bolt_offset, bolt_offset], y = [-bolt_offset, bolt_offset]) {
            translate([x, y, -0.5])
                cylinder(h=mold_thick + 1, d=bolt_d, $fn=32);
            // Nut / bolt head recess on top side
            translate([x, y, mold_thick - bolt_head_depth + 0.1])
                cylinder(h=bolt_head_depth, d=bolt_head_d, $fn=32);
        }
    }

    // Additive Features (Facing downwards relative to the mating surface at Z=0)
    // 1. Central cylindrical plug (protects nanopore top side)
    translate([0, 0, 0]) {
        color("Gold")
        mirror([0, 0, 1]) // Extends downwards into cavity
            cylinder(h=h_plug, d=plug_diameter, $fn=32);
    }
}

// 3. MOLD ASSEMBLY VISUALIZATION
module Nanopore_Wafer_Mold_Assembly(explode=0, show_gasket=true) {
    h_plug = (gasket_thick - wafer_thick) / 2;

    // Bottom Mold sits at its default coordinate system
    Nanopore_Wafer_Mold_Bottom(type="top");

    // The Silicon Nanopore Wafer sits inside the cavity
    // Centered vertically relative to the gasket:
    // gasket bottom is at Z = mold_thick
    // wafer center is at Z = mold_thick + gasket_thick/2
    translate([0, 0, mold_thick + gasket_thick/2 + explode * 0.5])
        Wafer_Visual();

    // The cured silicone gasket itself (visualized in transparent red)
    if (show_gasket) {
        translate([0, 0, mold_thick + explode * 0.25]) {
            color("Red", 0.5) {
                difference() {
                    // Main gasket shape
                    linear_extrude(gasket_thick)
                        circle(d=hex_diam, $fn=6);

                    // Subtract finger grip cutouts
                    linear_extrude(gasket_thick + 1.0)
                        Finger_Grip_Cutout_2D();

                    // Subtract the embedded wafer pocket
                    translate([0, 0, (gasket_thick - wafer_thick)/2 - 0.05])
                        cube([wafer_size + 0.1, wafer_size + 0.1, wafer_thick + 0.1], center=true);

                    // Central protected nanopore opening
                    translate([0, 0, -0.5])
                        cylinder(h=gasket_thick + 1.0, d=plug_diameter, $fn=32);

                    // Port holes and channel paths molded into the silicone
                    // (They are formed by the raised bosses, so we subtract them here for visualization)
                    for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                        rotate([0, 0, a]) translate([port_radius, 0, -0.5])
                            cylinder(h=gasket_thick + 1.0, d=2.0, $fn=32);
                    }

                    // Channel paths (subtracted to show flow path in cast piece)
                    for(a = [angle_fluid_in_top, angle_fluid_out_top]) {
                        rotate([0, 0, a]) {
                            hull() {
                                translate([port_radius, 0, gasket_thick/2])
                                    cylinder(h=gasket_thick+0.1, d=1.2, center=true, $fn=16);
                                translate([0, 0, gasket_thick/2])
                                    cylinder(h=gasket_thick+0.1, d=1.2, center=true, $fn=16);
                            }
                        }
                    }
                }
            }
        }
    }

    // Top Mold sits on top of the bottom mold, meeting at the mating plane
    // Bottom mold top face is at Z = mold_thick
    // We translate top mold by mold_thick, flip it, and add explode offset.
    translate([0, 0, mold_thick + gasket_thick + explode])
        rotate([180, 0, 0])
            Nanopore_Wafer_Mold_Top(type="top");
}

// Default Rendering
if (Output_Mode == "Assembly" && !is_undef($preview)) {
    // Standard visualization
    Nanopore_Wafer_Mold_Assembly(explode=Explode_Factor * 0.4, show_gasket=true);
} else {
    // Support exporting individual components
    if (Output_Mode == "Gasket_Mold_Bottom_STL") {
        Nanopore_Wafer_Mold_Bottom(type="top");
    } else if (Output_Mode == "Gasket_Mold_Top_STL") {
        Nanopore_Wafer_Mold_Top(type="top");
    }
}
