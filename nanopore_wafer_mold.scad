// ==============================================================================
// SENTINEL NANOPORE READER - 2-PART VERTICALLY-SPLIT SILICONE MOLD
// Generates a 3D printable vertically split compression mold to cast the
// hexagonal gasket with an embedded silicon square nanopore wafer,
// or a flat gasket without the nanopore (for the Fitted Amplifier Gasket).
//
// DESIGN FEATURES:
// 1. Vertically split along the X=0 plane. The seam is on the bottom resting surface.
// 2. Large open top reservoir to contain expanded foaming silicone during degassing.
// 3. Tapered injection sprue from the reservoir into the center-top of the cavity.
// 4. Proper air bleed/vent channels running from the upper corners of the hex cavity.
// 5. Symmetric round plugs clamping the wafer to protect the nanopore (when is_nanopore=true).
// 6. Configurable central square plug for flat gaskets without the nanopore.
// ==============================================================================

include <constants.scad>
include <modules/common.scad>
include <modules/cartridge.scad>

// Mold Plate Dimensions
mold_w = hex_diam + 20;  // ~80mm (Y direction)
mold_h = hex_diam + 30;  // ~90mm (Z direction)
mold_t = 15.0;           // Thickness of each mold half (X direction)

// Cavity position
cavity_z = mold_h / 2 - 10; // Positioned in lower-middle section

// Alignment Bolt/Pin Settings
bolt_d = 4.5;         // M4 clamp bolt clearance
bolt_head_d = 8.0;    // M4 cap head diameter
bolt_head_depth = 4.0; // Recess depth for clamp bolts
bolt_y_offset = mold_w/2 - 6;
bolt_z_offset = mold_h/2 - 6;

// Alignment Pins (Interlocks)
pin_d = 4.0;
pin_h = 5.0;

module Rounded_Mold_Block(t, w, h, r=4) {
    hull() {
        for(y = [-w/2 + r, w/2 - r]) {
            for(z = [-h/2 + r, h/2 - r]) {
                translate([0, y, z])
                    rotate([0, 90, 0])
                        cylinder(h=t, r=r, center=true, $fn=32);
            }
        }
    }
}

module Rounded_Reservoir_Block(t, w, h, r=2) {
    hull() {
        for(y = [-w/2 + r, w/2 - r]) {
            for(z = [-h/2 + r, h/2 - r]) {
                translate([0, y, z])
                    rotate([0, 90, 0])
                        cylinder(h=t, r=r, center=true, $fn=32);
            }
        }
    }
}

// Reservoir Dimensions
res_w = hex_diam - 10; // 50mm
res_d = 15.0;          // Depth of the reservoir (Z-axis cut from top)
res_t = mold_t - 3.0;  // Thickness of the reservoir cut in each half (X direction)

module Wafer_Visual() {
    color("Dimgrey") {
        difference() {
            // Square wafer substrate (oriented in Y-Z plane at X=0)
            cube([wafer_thick, wafer_size, wafer_size], center=true);

            // Central nanopore aperture
            rotate([0, 90, 0])
                cylinder(h=wafer_thick+1, d=0.5, center=true, $fn=16);
        }
    }
    // Nanopore itself
    color("Black") sphere(d=0.2, $fn=8);
}

module Corner_Guides_Vertical_Seam(wafer_s=wafer_size, guide_w=1.2, height) {
    // 2 Corner guides in Y-Z plane (top-left and bottom-right), extending in X direction.
    // This avoids overlapping with the active fluid channels at 30 and 210 degrees
    // while still fully registering the square wafer.
    difference() {
        union() {
            // Keep Quadrant II (s=-1, t=1) and Quadrant IV (s=1, t=-1)
            for(pair = [[-1, 1], [1, -1]]) {
                s = pair[0];
                t = pair[1];
                translate([height/2, s * wafer_s/2, t * wafer_s/2])
                    cube([height, guide_w, guide_w], center=true);
            }
        }
        // Subtract wafer space
        translate([height/2, 0, 0])
            cube([height + 1, wafer_s, wafer_s], center=true);
    }
}

// 1. LEFT MOLD HALF (X < 0)
module Nanopore_Wafer_Mold_Left(type="top", is_nanopore=true) {
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
        // Main block (rests on Z=0, split face at X=0)
        translate([-mold_t/2, 0, mold_h/2])
            Rounded_Mold_Block(mold_t, mold_w, mold_h, r=4);

        // A: Hexagonal Gasket Cavity (Left half, depth gasket_thick/2)
        translate([-gasket_thick/2, 0, cavity_z]) {
            rotate([0, 90, 0])
                linear_extrude(gasket_thick/2 + 0.1)
                    circle(d=primary_gasket_diam, $fn=6);
        }

        if (is_nanopore) {
            // Protrusion Pocket (depth PCB_Thickness, subtracted from X = -gasket_thick/2)
            translate([-gasket_thick/2 - PCB_Thickness/2, 0, cavity_z]) {
                cube([PCB_Thickness + 0.1, protrusion_size, protrusion_size], center=true);
            }
        }

        // B: Finger Grip Cutout clearances
        translate([-gasket_thick/2, 0, cavity_z]) {
            rotate([0, 90, 0])
                linear_extrude(gasket_thick/2 + 0.1)
                    Finger_Grip_Cutout_2D();
        }

        // C: Large Top Reservoir (Foam expansion chamber)
        translate([ 0.01, 0, mold_h - res_d/2 + 0.1])
            Rounded_Reservoir_Block(res_t, res_w, res_d + 0.2, r=2);

        // D: Tapered Injection sprue (half-cone cut)
        // From bottom of reservoir (Z = mold_h - res_d) down to top edge of hexagon (Z = cavity_z + 26.0)
        // Semi-cone tapering from d=6.0 at Z = mold_h - res_d down to d=3.0 at Z = cavity_z + 26.0
        translate([0.01, 0, 0]) {
            hull() {
                translate([0, 0, mold_h - res_d])
                    rotate([0, 90, 0]) cylinder(h=2.0, d=6.0, center=true, $fn=32);
                translate([0, 0, cavity_z + 26.0])
                    rotate([0, 90, 0]) cylinder(h=2.0, d=3.0, center=true, $fn=32);
            }
        }

        // E: Air Bleed / Vent Vents (Y = +/- 15, from Z = cavity_z + 26.0 up to mold_h)
        for(y_vent = [-15, 15]) {
            translate([-0.0001, y_vent, (mold_h + cavity_z + 2.0)/2])
                cube([1.5, 1.5, mold_h - (cavity_z + 26.0) + 0.2], center=true);
        }

        // F: Horizontal Clamping bolt holes
        for(y = [-bolt_y_offset, bolt_y_offset], z = [cavity_z - bolt_z_offset, cavity_z + bolt_z_offset]) {
            translate([-mold_t - 0.5, y, z])
                rotate([0, 90, 0]) cylinder(h=mold_t + 1.0, d=bolt_d, $fn=32);
            // Cap screw head counterbore
            translate([-mold_t - 0.1, y, z])
                rotate([0, 90, 0]) cylinder(h=bolt_head_depth, d=bolt_head_d, $fn=32);
        }

        // G: Alignment Sockets (female)
        for(y = [-bolt_y_offset, bolt_y_offset]) {
            translate([-pin_h/2 + 0.1, y, cavity_z])
                rotate([0, 90, 0]) cylinder(h=pin_h, d=pin_d + 0.2, center=true, $fn=32);
        }
    }

    // Additive Features (Inside Left half cavity)
    translate([0, 0, cavity_z]) {
        if (is_nanopore) {
            // 1. Central cylindrical plug (protects nanopore left side, forming the channel leading to the recessed wafer)
            translate([-gasket_thick/2 - PCB_Thickness, 0, 0]) {
                rotate([0, 90, 0])
                    color("Gold") cylinder(h=wafer_recess, d=plug_diameter, $fn=32);
            }
            difference(){
                union(){
                    
                    // 3. Passive fluid port pins (generate holes in cast piece)
                    color("Gold") {
                        for(a = pass_angles) {
                            rotate([a, 0, 0]) translate([0, port_radius, 0])
                                rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                    cylinder(h=gasket_thick/2, d=2.0, $fn=32);
                        }
                    }
                    
                     // 4. Active fluid port pins and raised flow channel bosses
                    color("Gold") {
                        // Inlet port pin + channel boss
                        rotate([active_in, 0, 0]) {
                            translate([0, port_radius, 0])
                                rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                    cylinder(h=gasket_thick/2, d=2.0, $fn=32);

                            // Active channel boss (recessed in left mold to form channel in cast gasket)
                            hull() {
                                translate([0, port_radius, 0])
                                    rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                        cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                                translate([0, 0, 0])
                                    rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                        cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                            }
                        }

                        // Outlet port pin + channel boss
                        rotate([active_out, 0, 0]) {
                            translate([0, port_radius, 0])
                                rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                    cylinder(h=gasket_thick/2, d=2.0, $fn=32);

                            // Active channel boss
                            hull() {
                                translate([0, port_radius, 0])
                                    rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                        cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                                translate([0, 0, 0])
                                    rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                        cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                            }
                        }
                    }
                }
                
                
                // 1b. Wafer Pocket forming block (additive)
               # translate([-gasket_thick/2 - PCB_Thickness + wafer_recess + wafer_thick/2, 0, 0]) {
                    color("Gold") cube([wafer_thick, wafer_size, wafer_size], center=true);
                }

                // 2. Corner registration L-brackets to position the wafer
                // Centered at X = -gasket_thick/2 - PCB_Thickness + wafer_recess
                //translate([-gasket_thick/2 - PCB_Thickness + wafer_recess, 0, 0])
                //    Corner_Guides_Vertical_Seam(wafer_s=wafer_size, guide_w=1.2, height=h_guide);

               
            }
        } else {
            // Flat/Amplifier gasket mold: Central square plug to form the central square hole
            translate([-gasket_thick/4, 0, 0]) {
                color("Gold") cube([gasket_thick/2, wafer_hole_size, wafer_hole_size], center=true);
            }

            // Passive fluid port pins for pass-through top ports
            color("Gold") {
                for(a = pass_angles) {
                    rotate([a, 0, 0]) translate([0, port_radius, 0])
                        rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                            cylinder(h=gasket_thick/2, d=2.0, $fn=32);
                }
            }

            // Active fluid port pins and raised flow channel bosses for bottom ports
            color("Gold") {
                for (a = [active_in, active_out]) {
                    rotate([a, 0, 0]) {
                        // Port hole pin
                        translate([0, port_radius, 0])
                            rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                cylinder(h=gasket_thick/2, d=2.0, $fn=32);

                        // Active channel boss (recessed in left mold to form channel in cast gasket)
                        hull() {
                            translate([0, port_radius, 0])
                                rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                    cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                            translate([0, 0, 0])
                                rotate([0, 90, 0]) translate([0, 0, -gasket_thick/2])
                                    cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                        }
                    }
                }
            }
        }
    }
}

// 2. RIGHT MOLD HALF (X > 0)
// 2. RIGHT MOLD HALF (X > 0)
module Nanopore_Wafer_Mold_Right(type="top", is_nanopore=true) {
    h_plug = (gasket_thick - wafer_thick) / 2;

    // Determine active and passive ports based on gasket type
    active_in = (type=="bottom") ? angle_fluid_in_bot : angle_fluid_in_top;
    active_out = (type=="bottom") ? angle_fluid_out_bot : angle_fluid_out_top;
    pass_angles = (type=="bottom")
        ? [angle_fluid_in_top, angle_fluid_out_top]
        : [angle_fluid_in_bot, angle_fluid_out_bot];

    color("SteelBlue")
    difference() {
        // Main block
        translate([mold_t/2, 0, mold_h/2])
            Rounded_Mold_Block(mold_t, mold_w, mold_h, r=4);

        // A: Hexagonal Gasket Cavity (Right half, depth gasket_thick/2)
        translate([-0.001, 0, cavity_z]) {
            rotate([0, 90, 0])
                linear_extrude(gasket_thick/2 + 0.1)
                    circle(d=primary_gasket_diam, $fn=6);
        }

        // B: Finger Grip Cutout clearances
        translate([-0.001, 0, cavity_z]) {
            rotate([0, 90, 0])
                linear_extrude(gasket_thick/2 + 0.1)
                    Finger_Grip_Cutout_2D();
        }

        // C: Large Top Reservoir
        translate([0.01, 0, mold_h - res_d/2 + 0.1])
            Rounded_Reservoir_Block(res_t, res_w, res_d + 0.2, r=2);

        // D: Tapered Injection sprue (half-cone cut)
        translate([-0.001, 0, 0]) {
            hull() {
                translate([0, 0, mold_h - res_d])
                    rotate([0, 90, 0]) cylinder(h=2.0, d=6.0, center=true, $fn=32);
                translate([0, 0, cavity_z + 26.0])
                    rotate([0, 90, 0]) cylinder(h=2.0, d=3.0, center=true, $fn=32);
            }
        }

        // E: Air Bleed / Vent Vents
        for(y_vent = [-15, 15]) {
            translate([-0.001, y_vent, (mold_h + cavity_z + 2.0)/2])
                cube([1.5, 1.5, mold_h - (cavity_z + 26.0) + 0.2], center=true);
        }

        // F: Horizontal Clamping bolt holes
        for(y = [-bolt_y_offset, bolt_y_offset], z = [cavity_z - bolt_z_offset, cavity_z + bolt_z_offset]) {
            translate([-0.5, y, z])
                rotate([0, 90, 0]) cylinder(h=mold_t + 1.0, d=bolt_d, $fn=32);
            // Cap screw head counterbore / nut recess
            translate([mold_t - bolt_head_depth + 0.1, y, z])
                rotate([0, 90, 0]) cylinder(h=bolt_head_depth, d=bolt_head_d, $fn=32);
        }
    }

    // Additive Features (Inside Right half cavity)
    translate([0, 0, cavity_z]) {
        if (is_nanopore) {
            // 1. Central cylindrical plug (protects nanopore right side)
            // Extends from right cavity floor (X = gasket_thick/2) down to wafer right face (X = -gasket_thick/2 - PCB_Thickness + wafer_recess + wafer_thick)
            translate([-gasket_thick/2 - PCB_Thickness + wafer_recess + wafer_thick, 0, 0]) {
                rotate([0, 90, 0])
                    color("Gold") cylinder(h=gasket_thick + PCB_Thickness - wafer_recess - wafer_thick, d=plug_diameter, $fn=32);
            }

            // 2. Passive fluid port pins
            color("Gold") {
                for(a = pass_angles) {
                    rotate([a, 0, 0]) translate([0, port_radius, 0])
                        rotate([0, 90, 0])
                            cylinder(h=gasket_thick/2, d=2.0, $fn=32);
                }
            }

            // 3. Active fluid port pins and raised flow channel bosses
            color("Gold") {
                // Inlet port pin + channel boss
                rotate([active_in, 0, 0]) {
                    translate([0, port_radius, 0])
                        rotate([0, 90, 0])
                            cylinder(h=gasket_thick/2, d=2.0, $fn=32);

                    // Active channel boss
                    hull() {
                        translate([0, port_radius, 0])
                            rotate([0, 90, 0])
                                cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                        translate([0, 0, 0])
                            rotate([0, 90, 0])
                                cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                    }
                }

                // Outlet port pin + channel boss
                rotate([active_out, 0, 0]) {
                    translate([0, port_radius, 0])
                        rotate([0, 90, 0])
                            cylinder(h=gasket_thick/2, d=2.0, $fn=32);

                    // Active channel boss
                    hull() {
                        translate([0, port_radius, 0])
                            rotate([0, 90, 0])
                                cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                        translate([0, 0, 0])
                            rotate([0, 90, 0])
                                cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                    }
                }
            }
        } else {
            // Flat/Amplifier gasket mold: central square plug from meeting surface (X = 0) to cavity floor (X = gasket_thick/2)
            translate([gasket_thick/4, 0, 0]) {
                color("Gold") cube([gasket_thick/2, wafer_hole_size, wafer_hole_size], center=true);
            }

            // Passive fluid port pins for pass-through top ports
            color("Gold") {
                for(a = pass_angles) {
                    rotate([a, 0, 0]) translate([0, port_radius, 0])
                        rotate([0, 90, 0])
                            cylinder(h=gasket_thick/2, d=2.0, $fn=32);
                }
            }

            // Active fluid port pins and raised flow channel bosses for bottom ports
            color("Gold") {
                for (a = [active_in, active_out]) {
                    rotate([a, 0, 0]) {
                        // Port hole pin
                        translate([0, port_radius, 0])
                            rotate([0, 90, 0])
                                cylinder(h=gasket_thick/2, d=2.0, $fn=32);

                        // Active channel boss
                        hull() {
                            translate([0, port_radius, 0])
                                rotate([0, 90, 0])
                                    cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                            translate([0, 0, 0])
                                rotate([0, 90, 0])
                                    cylinder(h=gasket_thick/2, d=1.2, $fn=16);
                        }
                    }
                }
            }
        }

        // 4. Alignment Pins (male) protruding from meeting surface (X = 0)
        for(y = [-bolt_y_offset, bolt_y_offset]) {
            translate([0, y, 0])
                rotate([0, -90, 0])
                    color("Gold") cylinder(h=pin_h - 0.2, d=pin_d, $fn=32);
        }
    }
}

// 3. MOLD ASSEMBLY VISUALIZATION
module Nanopore_Wafer_Mold_Assembly(explode=0, show_gasket=true, is_nanopore=true) {
    local_type = is_nanopore ? "top" : "bottom";
    // Left Mold Half
    translate([-explode, 0, 0])
        Nanopore_Wafer_Mold_Left(type=local_type, is_nanopore=is_nanopore);

    // Silicon Square Wafer sits at its new offset position
    if (is_nanopore) {
        translate([-gasket_thick/2 - PCB_Thickness + wafer_recess + wafer_thick/2, 0, cavity_z])
            Wafer_Visual();
    }

    // The cured silicone gasket itself
    if (show_gasket) {
        translate([0, 0, cavity_z]) {
            color("Red", 0.5) {
                rotate([0, 90, 0]) {
                    difference() {
                        if (is_nanopore) {
                            union() {
                                // Main gasket shape
                                cylinder(h=gasket_thick, d=primary_gasket_diam, center=true, $fn=6);

                                // Protrusion
                                translate([0, 0, -gasket_thick/2 - PCB_Thickness/2])
                                    cube([protrusion_size, protrusion_size, PCB_Thickness], center=true);
                            }
                        } else {
                            // Main gasket shape (flat, no protrusion)
                            cylinder(h=gasket_thick, d=primary_gasket_diam, center=true, $fn=6);
                        }

                        // Finger grip cutouts
                        Finger_Grip_Cutout(height=gasket_thick + 10.0);

                        if (is_nanopore) {
                            // Wafer pocket cutout
                            translate([0, 0, -gasket_thick/2 - PCB_Thickness + wafer_recess + wafer_thick/2])
                                cube([wafer_size + 0.1, wafer_size + 0.1, wafer_thick + 0.1], center=true);

                            // Central protected round aperture
                            cylinder(h=gasket_thick + PCB_Thickness * 2 + 2.0, d=plug_diameter, center=true, $fn=32);

                            // Ports
                            for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                                rotate([0, 0, a]) translate([port_radius, 0, 0])
                                    cylinder(h=gasket_thick + 2.0, d=2.0, center=true, $fn=32);
                            }
                            
                            // Active ports & molded flow channels
                            for (a = [angle_fluid_in_top, angle_fluid_out_top]) {
                                rotate([0, 0, a]) {
                                    // Port hole
                                    translate([port_radius, 0, 0])
                                        cylinder(h=gasket_thick + 2.0, d=2.0, center=true, $fn=32);
                                    // Flow channel
                                    hull() {
                                        translate([port_radius, 0, 0])
                                            cylinder(h=gasket_thick + 0.1, d=1.2, center=true, $fn=16);
                                        translate([0, 0, 0])
                                            cylinder(h=gasket_thick + 0.1, d=1.2, center=true, $fn=16);
                                    }
                                }
                            }
                            
                            
                        } else {
                            // Central square hole
                            cube([wafer_hole_size, wafer_hole_size, gasket_thick + 2.0], center=true);

                            // Passive ports (simple pass-throughs)
                            for(a = [angle_fluid_in_top, angle_fluid_out_top]) {
                                rotate([0, 0, a]) translate([port_radius, 0, 0])
                                    cylinder(h=gasket_thick + 2.0, d=2.0, center=true, $fn=32);
                            }

                            // Active ports & molded flow channels
                            for (a = [angle_fluid_in_bot, angle_fluid_out_bot]) {
                                rotate([0, 0, a]) {
                                    // Port hole
                                    translate([port_radius, 0, 0])
                                        cylinder(h=gasket_thick + 2.0, d=2.0, center=true, $fn=32);
                                    // Flow channel
                                    hull() {
                                        translate([port_radius, 0, 0])
                                            cylinder(h=gasket_thick + 0.1, d=1.2, center=true, $fn=16);
                                        translate([0, 0, 0])
                                            cylinder(h=gasket_thick + 0.1, d=1.2, center=true, $fn=16);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Right Mold Half
    translate([explode, 0, 0])
        Nanopore_Wafer_Mold_Right(type=local_type, is_nanopore=is_nanopore);
}

// 4. MULTI-MOLD ASSEMBLY VISUALIZATION FOR ENHANCED TESTING & DOCUMENTATION
module Multi_Mold_Visualizer() {
    exp_factor = (Mold_Visualization_Mode == "mated") ? 0 : (Explode_Factor * 0.4);

    if (Mold_Visualization_Mode == "nanopore_only") {
        Nanopore_Wafer_Mold_Assembly(explode=exp_factor, show_gasket=true, is_nanopore=true);
    } else if (Mold_Visualization_Mode == "amplifier_only") {
        Nanopore_Wafer_Mold_Assembly(explode=exp_factor, show_gasket=true, is_nanopore=false);
    } else if (Mold_Visualization_Mode == "gaskets_only") {
        // Just show the two resultant gaskets side-by-side, rotated nicely to see details
        translate([0, -35, cavity_z]) {
            rotate([0, -20, 0]) { // tilt to see details
                // Nanopore gasket
                color("Red") {
                    difference() {
                        union() {
                            cylinder(h=gasket_thick, d=primary_gasket_diam, center=true, $fn=6);
                            translate([0, 0, -gasket_thick/2 - PCB_Thickness/2])
                                cube([protrusion_size, protrusion_size, PCB_Thickness], center=true);
                        }
                        Finger_Grip_Cutout(height=gasket_thick + 10.0);
                        translate([0, 0, -gasket_thick/2 - PCB_Thickness + wafer_recess + wafer_thick/2])
                            cube([wafer_size + 0.1, wafer_size + 0.1, wafer_thick + 0.1], center=true);
                        cylinder(h=gasket_thick + PCB_Thickness * 2 + 2.0, d=plug_diameter, center=true, $fn=32);
                        for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                            rotate([0, 0, a]) translate([port_radius, 0, 0])
                                cylinder(h=gasket_thick + 2.0, d=2.0, center=true, $fn=32);
                        }
                    }
                }
                // Embed the wafer
                translate([0, 0, -gasket_thick/2 - PCB_Thickness + wafer_recess + wafer_thick/2])
                    Wafer_Visual();
            }
        }

        translate([0, 35, cavity_z]) {
            rotate([0, -20, 0]) {
                // Amplifier Gasket
                color("Red") {
                    difference() {
                        cylinder(h=gasket_thick, d=primary_gasket_diam, center=true, $fn=6);
                        Finger_Grip_Cutout(height=gasket_thick + 10.0);
                        cube([wafer_hole_size, wafer_hole_size, gasket_thick + 2.0], center=true);

                        // Passive ports
                        for(a = [angle_fluid_in_top, angle_fluid_out_top]) {
                            rotate([0, 0, a]) translate([port_radius, 0, 0])
                                cylinder(h=gasket_thick + 2.0, d=2.0, center=true, $fn=32);
                        }

                        // Active ports & molded flow channels
                        for (a = [angle_fluid_in_bot, angle_fluid_out_bot]) {
                            rotate([0, 0, a]) {
                                translate([port_radius, 0, 0])
                                    cylinder(h=gasket_thick + 2.0, d=2.0, center=true, $fn=32);
                                hull() {
                                    translate([port_radius, 0, 0])
                                        cylinder(h=gasket_thick + 0.1, d=1.2, center=true, $fn=16);
                                    translate([0, 0, 0])
                                        cylinder(h=gasket_thick + 0.1, d=1.2, center=true, $fn=16);
                                }
                            }
                        }
                    }
                }
            }
        }
    } else {
        // default: "separated" or "mated" showing both molds side-by-side
        translate([0, -mold_w/2 - 15, 0]) {
            Nanopore_Wafer_Mold_Assembly(explode=exp_factor, show_gasket=true, is_nanopore=true);
        }
        translate([0, mold_w/2 + 15, 0]) {
            Nanopore_Wafer_Mold_Assembly(explode=exp_factor, show_gasket=true, is_nanopore=false);
        }
    }
}

// Default Rendering
if (Output_Mode == "Assembly" && !is_undef($preview)) {
    // Stand-alone rendering of both molds / gaskets
    Multi_Mold_Visualizer();
} else {
    // Support exporting individual components
    if (Output_Mode == "Gasket_Mold_Bottom_STL") {
        translate([0, 0, mold_t/2]) rotate([0, -90, 0])
        Nanopore_Wafer_Mold_Left(type="top", is_nanopore=true);
    } else if (Output_Mode == "Gasket_Mold_Top_STL") {
        translate([0, 0, mold_t/2]) rotate([0, 90, 0])
        Nanopore_Wafer_Mold_Right(type="top", is_nanopore=true);
    } else if (Output_Mode == "Amplifier_Gasket_Mold_Left_STL") {
        translate([0, 0, mold_t/2]) rotate([0, -90, 0])
        Nanopore_Wafer_Mold_Left(type="bottom", is_nanopore=false);
    } else if (Output_Mode == "Amplifier_Gasket_Mold_Right_STL") {
        translate([0, 0, mold_t/2]) rotate([0, 90, 0])
        Nanopore_Wafer_Mold_Right(type="bottom", is_nanopore=false);
    }
}
