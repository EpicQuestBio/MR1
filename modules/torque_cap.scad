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
        position(BOTTOM) cyl(d=neck_od + 7, h=cap_retention_h, anchor=BOTTOM);

        // Ratchet Teeth
        // Even with top, starting above retention
        for(r=[0:(360/Torque_Teeth_Count):360]) {
            // Position teeth vertically at the perimeter
            zrot(r) position(RIGHT) up(cap_retention_h) cyl(h=cap_inner_h - cap_retention_h, r=tooth_height, $fn=3, anchor=BOTTOM);
        }

        // Threads
        tag("remove")
        position(BOTTOM) down(1)
        threaded_rod(d=neck_od+1, l=cap_inner_h+2, internal=true, pitch=cap_thread_pitch, anchor=BOTTOM);

        if(access_hole) {
           // Pipette Access Hole
           tag("remove")
           position(BOTTOM) down(1)
           cyl(h=cap_inner_h+10, d=22, anchor=BOTTOM);
        }
    }
}

module Torque_Cap_Outer(access_hole=true) {
    color("Orange") {
        difference() {
            cylinder(h=cap_h, d=neck_od + 20); // Outer Shell
            // Retention Lip at Bottom (neck_od + 6)
            translate([0,0,-1]) cylinder(h=cap_retention_h + 1, d=neck_od + 6);
            // Main Clearance (neck_od + 8)
            translate([0,0,cap_retention_h]) cylinder(h=cap_h, d=neck_od + 8);
        }
        // Top Lid rim
        if(access_hole) {
            translate([0,0,cap_h-cap_top_thick]) difference() {
                cylinder(h=cap_top_thick, d=neck_od + 20);
                translate([0,0,-1]) cylinder(h=cap_top_thick+2, d=25); // Pipette Access Hole
            }
        }

        // Spring Arms
        for(r=[0:60:360]) {
            rotate([0,0,r]) {
                translate([neck_od/2 + 6, 0, cap_h/2]) {
                    cube([4, 15, cap_h], center=true); // Arm
                    translate([-3, 6, 0]) cylinder(h=cap_h, d=3, center=true); // Pawl
                }
            }
        }
    }
}