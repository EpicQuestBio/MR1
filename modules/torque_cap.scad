// ==============================================================================
// MODULE: TORQUE-LOCK CAP (Hollow for Pipette)
// ==============================================================================
module Torque_Cap_Inner(access_hole=true) {
    // Dynamic Thread Length: Needs to cover enough neck to reach stability
    // neck_h is defined relative to stack.
    // Cap height should roughly match neck_clearance + engagement.

    // PETG Ring with Sine Teeth
    color("Silver")
    diff("remove")
    cyl(h=cap_inner_h, d=neck_od + 4, anchor=BOTTOM) {
        // Retention Flange at Bottom
        position(BOTTOM) cyl(d=neck_od + 8, h=cap_retention_h, anchor=BOTTOM);

        // Ratchet Teeth
        // Even with top, starting above retention
        for(r=[0:(360/Torque_Teeth_Count):360]) {
            // Position teeth vertically at the perimeter
            zrot(r)
            translate([neck_od/2 + 2, 0, cap_retention_h])
            // zrot(180) // Point triangle outward
            cyl(h=cap_inner_h - cap_retention_h, r=tooth_height, $fn=3, anchor=BOTTOM);
        }

        // Threads
        tag("remove")
        position(BOTTOM) down(1)
        threaded_rod(d=neck_od+1, l=cap_inner_h+2, internal=true, pitch=cap_thread_pitch, anchor=BOTTOM);

        if(access_hole) {
           // Pipette Access Hole
           tag("remove")
           position(BOTTOM) down(1)
           cyl(h=cap_inner_h+10, d=neck_id/10, anchor=BOTTOM);
        }
    }
}

module Torque_Cap_Outer(access_hole=true) {
    color("Orange") {
        diff("remove") {
            cylinder(h=cap_h, d=neck_od + 20); // Outer Shell
            // Retention Lip at Bottom (neck_od + 6)
            tag("remove")
            translate([0,0,-0.5]) cylinder(h=cap_retention_h + 1, d=neck_od + 5);
            // Main Clearance (neck_od + 8)
            tag("remove")
            translate([0,0,cap_retention_h-0.5]) cylinder(h=cap_h+1, d=neck_od + 9);
        }
        // Top Lid rim
        if(access_hole) {
            tag("remove")
            translate([0,0,cap_h-cap_top_thick]) difference() {
                cylinder(h=cap_top_thick, d=neck_od + 20);
                translate([0,0,-0.5]) cylinder(h=cap_top_thick+1, d=25); // Pipette Access Hole
            }
        }

        // Spring Arms
        for(r=[0:60:360]) {
            rotate([0,0,r]) {
                // Cutout slot for flex
                tag("remove")
                translate([neck_od/2 + 6, 0, cap_h/2])
                cube([6, 18, cap_h+2], center=true);

                // Arm Body
                translate([neck_od/2 + 6, 0, cap_retention_h + 1]) {
                     // Arm Base - shift up by retention + 1mm clearance
                     // Height is remainder
                     up((cap_h - (cap_retention_h+1))/2)
                     cube([4, 15, cap_h - (cap_retention_h+1)], center=true); // Arm

                     // Pawl - shift up
                     up((cap_h - (cap_retention_h+1))/2)
                     translate([-3, 6, 0])
                     cylinder(h=cap_h - (cap_retention_h+1), d=3, center=true); // Pawl
                }
            }
        }
    }
}