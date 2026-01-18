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
        cuboid([base_w-2*wall, base_l-2*wall, pump_h+wall], anchor=BOTTOM);

        // Fluid Ports (Base Side Walls)
        // 2x Input (Left), 2x Output (Right)
        attach(LEFT) {
             for(y_pos = [-20, 20]) {
                 translate([0, y_pos, 0])
                 cyl(h=wall*3, d=20, anchor=CENTER) {
                    tag("remove") threaded_rod(d=13.7, l=20, pitch=1.411, internal=true, anchor=CENTER);
                 }
             }
        }
        attach(RIGHT) {
             for(y_pos = [-20, 20]) {
                 translate([0, y_pos, 0])
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
             rotate_extrude(angle=180, convexity=4)
             translate([25, 0, 0])
             circle(d=12);
        }

        // Connectivity (Back Wall)
        attach(BACK) {
            // DIN 5 MIDI (Panel Mount)
            tag("remove") translate([-25, 0, 0])
            cyl(h=wall*3, d=16, anchor=CENTER) ;

            // USB-C (Panel Mount Cutout)
            tag("remove") translate([0, 0, 0])
            cuboid([12, 6, wall*3], rounding=2, edges="Z", anchor=CENTER);

            // Barrel Jack (Panel Mount)
            tag("remove") translate([25, 0, 0])
            cyl(h=wall*3, d=12, anchor=CENTER) ;
        }

        // Lid Mounts
        for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 - wall*1.5), y * (base_l/2 - wall*1.5), 0])
                 position(BOTTOM) up(wall)
                 cyl(h=pump_h-wall, d=8, anchor=BOTTOM) {
                    tag("remove") position(TOP) down(10) cyl(h=15, d=3, anchor=BOTTOM);
                 }
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
    color("Silver")
    diff("remove")
    cuboid([base_w+2*wall, base_l+2*wall, wall], rounding=wall, edges="Z", anchor=BOTTOM) {

        // Male Interlock Lugs (Top Surface)
        // 4 corners, tapered squares or cylinders
        // UPDATED: Changed to Dimples for Threaded Sensor Enclosure Feet
        attach(TOP) {
            for(x = [-1, 1], y = [-1, 1]) {
                translate([x * (base_w/2 - feet_inset), y * (base_l/2 - feet_inset), 0])
                tag("remove") cyl(h=3, d=13, anchor=TOP); // Dimple/Recess
            }
        }

        // Mounting Holes
        tag("remove") {
            for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 - wall*1.5), y * (base_l/2 - wall*1.5), 0])
                 cyl(h=wall*3, d=3.5, center=true);
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
