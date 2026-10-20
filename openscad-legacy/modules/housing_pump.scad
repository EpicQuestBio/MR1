// ==============================================================================
// MODULE: 12V PERISTALTIC PUMP (Diitao Style)
// ==============================================================================
module Peristaltic_Pump_12V() {
    // Dimensions based on Diitao/generic 12V dosing pump
    // Motor: ~27.6mm dia, 38mm length
    // Head: ~31.7mm dia, 20mm height
    // Total Height: ~58mm

    // Motor Body
    color("Silver") cylinder(h=38, d=27.6);

    // Pump Head
    translate([0,0,38]) {
        color("DodgerBlue") {
             difference() {
                cylinder(h=20, d=31.7);
                // Snap detents (visual)
                translate([0, 16, 10]) cube([10, 2, 10], center=true);
                translate([0, -16, 10]) cube([10, 2, 10], center=true);
             }
        }

        // Tubing Stubs (3mm ID x 5mm OD)
        // Usually exit sideways or top. Visualizing side exit.
        color("White", 0.5) {
            translate([12, 5, 10]) rotate([0, 90, 30]) cylinder(h=20, d=5); // In
            translate([12, -5, 10]) rotate([0, 90, -30]) cylinder(h=20, d=5); // Out
        }
    }
}

// ==============================================================================
// MODULE: PUMP VISUAL & CUTOUT HELPERS
// ==============================================================================

module Pump_Visual(type="Diitao") {
    if (type == "Diitao") {
        Peristaltic_Pump_12V();
    } else if (type == "Custom") {
        // Generic representation based on constants
        color("Silver") cylinder(h=38, d=pump_motor_d);
        translate([0,0,38]) {
             color("DodgerBlue") cylinder(h=20, d=pump_head_d);
        }
    } else if (type == "Blank") {
        // No pump visual
    }
}

module Pump_Mount_Cutout(type="Diitao") {
    if (type == "Diitao") {
        cylinder(h=10, d=28, center=true);
    } else if (type == "Custom") {
        cylinder(h=10, d=pump_mount_d, center=true);
    } else if (type == "Blank") {
        // No cutout
    }
}


// ==============================================================================
// MODULE: PUMP MODULE (Bottom Unit)
// ==============================================================================
module Housing_Pump_Case(pump_type=Pump_Type) {
    color("DimGray")
    diff("remove")
    cuboid([base_w+2*wall, base_l+2*wall, pump_h], rounding=wall, edges="Z", anchor=BOTTOM) {

        // Internal Bucket
        tag("remove") position(BOTTOM) up(wall)
        cuboid([base_w-2*wall, base_l-2*wall, pump_h], rounding=2, edges="Z", anchor=BOTTOM);

        // Fluid Ports (Base Side Walls)
        // 2x Input (Left), 2x Output (Right)
        attach(LEFT, overlap=0.1) {
             tag("add") for(x_pos = [-20, 20]) {
                 translate([x_pos, 0, 0])
                 cyl(h=wall*3, d=20, anchor=CENTER, $fn=32) {
                    tag("remove") threaded_rod(d=luer_thread_d, l=wall*5, pitch=luer_thread_pitch, internal=true, anchor=CENTER, $fn=30, spin=45);
                 }
             }
        }
        attach(RIGHT, overlap=0.1) {
             tag("add") for(x_pos = [-20, 20]) {
                 translate([x_pos, 0, 0])
                 cyl(h=wall*3, d=20, anchor=CENTER, $fn=32) {
                    tag("remove") threaded_rod(d=luer_thread_d, l=wall*5, pitch=luer_thread_pitch, internal=true, anchor=CENTER, $fn=30, spin=45);
                 }
             }
        }

        attach(FRONT, overlap=0.1) {
             // Coffee Mug Handle (D-Shaped)
             // Oriented vertically, sticking out Z (relative to attachment)
             // Designed for adult hand grasp (approx 40mm inner vertical, 30mm inner clearance)
             h_center = 26;
             stick_out = 36;
             tube_d = 12;

             // Explicit handle geometry to avoid path_sweep CGAL assertion violations
             // Recreate exact geometry with proper overlap and rounded corners
             corner_r = 12;
             z_start = -1;

             tag("add") union() {
                 // Vertical legs (from z_start up to start of corner curve)
                 translate([0, h_center, (stick_out - corner_r + z_start)/2])
                     cylinder(d=tube_d, h=stick_out - corner_r - z_start + 0.1, center=true);
                 translate([0, -h_center, (stick_out - corner_r + z_start)/2])
                     cylinder(d=tube_d, h=stick_out - corner_r - z_start + 0.1, center=true);

                 // Horizontal crossbar (between the corner curves)
                 translate([0, 0, stick_out])
                     rotate([90, 0, 0]) cylinder(d=tube_d, h=(h_center - corner_r)*2 + 0.1, center=true);

                 // Rounded corners using hull for absolute geometry safety
                 translate([0, h_center - corner_r, stick_out - corner_r])
                     hull() {
                         translate([0, corner_r, 0]) sphere(d=tube_d);
                         translate([0, 0, corner_r]) sphere(d=tube_d);
                     }

                 translate([0, -h_center + corner_r, stick_out - corner_r])
                     hull() {
                         translate([0, -corner_r, 0]) sphere(d=tube_d);
                         translate([0, 0, corner_r]) sphere(d=tube_d);
                     }
             }
        }

        // Connectivity (Back Wall)
        attach(BACK, overlap=0.1) {
            // USB-C 1 (Panel Mount Cutout)
            tag("remove") translate([-15, 0, 0])
            cuboid([12, 6, wall*10], rounding=2, edges="Z", anchor=CENTER);

            // USB-C 2 (Panel Mount Cutout)
            tag("remove") translate([15, 0, 0])
            cuboid([12, 6, wall*10], rounding=2, edges="Z", anchor=CENTER);
        }

        // Lid Mounts (In Wall Corners)
        tag("remove") {
             for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2), y * (base_l/2), 0])
                 cylinder(h=pump_h*3, d=3.2, center=true, $fn=16);
             }
        }

        // Knife Edge (Seal)
        attach(TOP, overlap=0.1) {
            // Updated to match Reader Module logic (base_w - 8)
            tag("add") {
                path_rect = rect([base_w - 8, base_l - 8], rounding=3);
                path_sweep(circle(r=seal_radius, $fn=16), path_rect, closed=true);
            }
        }
    }

    // Pump Mounting Plate (Swappable Insert)
    translate([0, 0, wall]) {
        // Simple plate on standoffs
        difference() {
            cube([base_w-5, base_l-5, 5], center=true); // Plate
            // Mounting for Pumps (Configurable)
             for(side = [-1, 1]) {
                translate([side * (base_w/4), 20, 0]) Pump_Mount_Cutout(type=pump_type);
             }
        }
    }
}

// Lid for the pump case - solid top face (no center pass-through hole)
module Housing_Pump_Lid() {
    lid_thick = pump_lid_thick; // Thicker lid to clear foot dimples
    local_seal_lip_h = 5; // Increased from 2.5 to 5.0 for better engagement

    color("Silver")
    union() {
        diff("remove")
        cuboid([base_w+2*wall, base_l+2*wall, lid_thick], rounding=wall, edges="Z", anchor=BOTTOM) {

            // Male Interlock Lugs (Top Surface)
            // UPDATED: Changed to Dimples for Threaded Sensor Enclosure Feet
            attach(TOP) {
         tag("remove") {
            for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 - feet_inset), y * (base_l/2 - feet_inset), 0])
                 // Truncated sphere pointing down (4mm depth for clearance)
                 // Added +0.2 to height and Z-offset to prevent boolean artifacts at the top surface
                 down(0) intersection() {
                     sphere(d=13.5);
                     translate([0, 0, -4/2 + 0.2/2]) cube([15, 15, 4 + 0.2], center=true);
                 }
            }
        }
        }
            // Mounting Holes (In Corners)
            tag("remove") {
                for(x = [-1, 1], y = [-1, 1]) {
                     translate([x * (base_w/2), y * (base_l/2), 0])
                     cylinder(h=lid_thick*3, d=3.5, center=true);

                     // Counterbore?
                     translate([x * (base_w/2), y * (base_l/2), 0])
                     position(TOP) down(2) cylinder(h=4, d=6, anchor=BOTTOM);
                }
            }

            // O-Ring Groove
             tag("remove") position(BOTTOM) {
                 path_rect = rect([base_w - 8, base_l - 8], rounding=3);
                 down(0.01) // Ensure cut
                 path_sweep(circle(d=seal_cs+0.2, $fn=16), path_rect, closed=true);
             }
        }

        // Indexing Lip (Bottom of Lid)
        // Note: Pump Lid is `anchor=BOTTOM`. It sits at z=0 to z=wall.
        // We need the lip to stick DOWN from z=0.
        translate([0,0,0]) {
            difference() {
                 cuboid([base_w - 2*wall - 0.4, base_l - 2*wall - 0.4, local_seal_lip_h], rounding=2, edges="Z", anchor=TOP);
                 up(0.01) // ensure manifold
                 cuboid([base_w - 2*wall - 0.4 - 3, base_l - 2*wall - 0.4 - 3, local_seal_lip_h + 0.1], rounding=2, edges="Z", anchor=TOP);
            }
        }
    }
}

// 1. Pump Module Assembly
module Pump_Module_Assembly(pump_type=Pump_Type) {
    Housing_Pump_Case(pump_type=pump_type);
    translate([0,0,pump_h + Explode_Factor/2]) Housing_Pump_Lid();

    // Internal Components
    if(!Cross_Section) {
         // Pumps (Visual)
        for(side = [-1, 1]) {
             translate([side * (base_w/4), 20, wall+5]) // On plate (wall+5)
             Pump_Visual(type=pump_type);
        }
    }
}
