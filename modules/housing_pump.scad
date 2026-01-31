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
// MODULE: PUMP MODULE (Bottom Unit)
// ==============================================================================
module Housing_Pump_Case() {
    color("DimGray")
    diff("remove")
    cuboid([base_w+2*wall, base_l+2*wall, pump_h], rounding=wall, edges="Z", anchor=BOTTOM) {

        // Internal Bucket
        tag("remove") position(BOTTOM) up(wall)
        cuboid([base_w-2*wall, base_l-2*wall, pump_h+wall], rounding=2, edges="Z", anchor=BOTTOM);

        // Fluid Ports (Base Side Walls)
        // 2x Input (Left), 2x Output (Right)
        attach(LEFT) {
             for(x_pos = [-20, 20]) {
                 translate([x_pos, 0, 0])
                 cyl(h=wall*3, d=20, anchor=CENTER) {
                    tag("remove") threaded_rod(d=13.7, l=20, pitch=1.411, internal=true, anchor=CENTER);
                 }
             }
        }
        attach(RIGHT) {
             for(x_pos = [-20, 20]) {
                 translate([x_pos, 0, 0])
                 cyl(h=wall*3, d=20, anchor=CENTER) {
                    tag("remove") threaded_rod(d=13.7, l=20, pitch=1.411, internal=true, anchor=CENTER);
                 }
             }
        }

        attach(FRONT) {
             // Coffee Mug Handle
             // Oriented vertically, sticking out Z
             translate([0, 0, -2])
             rotate([90, 0, 90])
             intersection() {
                 rotate_extrude(convexity=4)
                 translate([25, 0, 0])
                 circle(d=12);

                 // Cut half to simulate angle=180 but safer geometry
                 // Covers Y positive (angle 0 to 180)
                 translate([0, 50, 0])
                 cube([100, 100, 100], center=true);
             }
        }

        // Connectivity (Back Wall)
        attach(BACK) {
            // DIN 5 MIDI (Panel Mount)
            tag("remove") translate([-25, 0, 0])
            cyl(h=wall*10, d=16, anchor=CENTER) ;

            // USB-C (Panel Mount Cutout)
            tag("remove") translate([0, 0, 0])
            cuboid([12, 6, wall*10], rounding=2, edges="Z", anchor=CENTER);

            // Barrel Jack (Panel Mount)
            tag("remove") translate([25, 0, 0])
            cyl(h=wall*10, d=12, anchor=CENTER) ;
        }

        // Lid Mounts (In Wall Corners)
        tag("remove") {
             for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 + 2), y * (base_l/2 + 2), 0])
                 cylinder(h=pump_h*3, d=3.2, center=true);
             }
        }

        // Knife Edge (Seal)
        attach(TOP) {
            // Updated to match Reader Module logic (base_w - 8)
            path_rect = rect([base_w - 8, base_l - 8], rounding=3);
            path_sweep(circle(r=seal_radius), path_rect, closed=true);
        }
    }

    // Pump Mounting Plate (Swappable Insert)
    translate([0, 0, wall]) {
        // Simple plate on standoffs
        difference() {
            cube([base_w-5, base_l-5, 5], center=true); // Plate
            // Mounting for 2x Diitao Pumps
             for(side = [-1, 1]) {
                translate([side * (base_w/4), 20, 0]) cylinder(h=10, d=28, center=true);
             }
        }
    }
}

module Housing_Pump_Lid() {
    lid_thick = wall; // Thin lid

    color("Silver")
    union() {
        diff("remove")
        cuboid([base_w+2*wall, base_l+2*wall, lid_thick], rounding=wall, edges="Z", anchor=BOTTOM) {

            // Male Interlock Lugs (Top Surface)
            // UPDATED: Changed to Dimples for Threaded Sensor Enclosure Feet
            attach(TOP) {
                for(x = [-1, 1], y = [-1, 1]) {
                    translate([x * (base_w/2 - feet_inset), y * (base_l/2 - feet_inset), 0])
                    tag("remove") cyl(h=3, d=13, anchor=TOP); // Dimple/Recess
                }
            }

            // Mounting Holes (In Corners)
            tag("remove") {
                for(x = [-1, 1], y = [-1, 1]) {
                     translate([x * (base_w/2 + 2), y * (base_l/2 + 2), 0])
                     cylinder(h=lid_thick*3, d=3.5, center=true);

                     // Counterbore?
                     translate([x * (base_w/2 + 2), y * (base_l/2 + 2), 0])
                     position(TOP) down(2) cylinder(h=4, d=6, anchor=BOTTOM);
                }
            }

            // O-Ring Groove
             tag("remove") position(BOTTOM) {
                 path_rect = rect([base_w - 8, base_l - 8], rounding=3);
                 down(0.01) // Ensure cut
                 path_sweep(circle(d=seal_cs+0.2), path_rect, closed=true);
             }
        }

        // Indexing Lip (Bottom of Lid)
        // Note: Pump Lid is `anchor=BOTTOM`. It sits at z=0 to z=wall.
        // We need the lip to stick DOWN from z=0.
        translate([0,0,0]) {
            difference() {
                 cuboid([base_w - 2*wall - 0.4, base_l - 2*wall - 0.4, seal_lip_h], rounding=2, edges="Z", anchor=TOP);
                 up(0.01) // ensure manifold
                 cuboid([base_w - 2*wall - 0.4 - 3, base_l - 2*wall - 0.4 - 3, seal_lip_h + 0.1], rounding=2, edges="Z", anchor=TOP);
            }
        }
    }
}

// 1. Pump Module Assembly
module Pump_Module_Assembly() {
    Housing_Pump_Case();
    translate([0,0,pump_h + Explode_Factor/2]) Housing_Pump_Lid();

    // Internal Components
    if(!Cross_Section) {
         // Pumps (Visual)
        for(side = [-1, 1]) {
             translate([side * (base_w/4), 20, wall+5]) // On plate (wall+5)
             Peristaltic_Pump_12V();
        }
    }
}
