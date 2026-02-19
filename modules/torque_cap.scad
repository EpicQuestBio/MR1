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

module Torque_Cap_Assembly(access_hole=true) {
    Torque_Cap_Outer(access_hole=access_hole);
    // Raise inner cap to sit on retention lip
    // Lip height is effectively cap_retention_h (approx 2mm)
    // Inner flange height is cap_retention_h (2mm)
    // Inner starts at Z=0.
    // Outer cavity starts at Z=cap_retention_h - 0.5 (1.5mm)
    // To clear the lip (Z=1.5), Inner needs to be at Z >= 1.5.
    // I will use cap_retention_h (2.0) for safety/tolerance.
    translate([0,0, cap_retention_h])
    Torque_Cap_Inner(access_hole=access_hole);
}

module Torque_Cap_Outer(access_hole=true) {
    color("Orange") {
        diff("remove") {
            // Main Body with Rounded Top Edge
            // d = neck_od + 20
            // Rounding applied to both top and bottom edges (2mm)
            cyl(h=cap_h, d=neck_od + 20, rounding=2, anchor=BOTTOM);

            // Grip Indentations (12 recessed rounded slots)
            // Positioned at 15, 45, 75... to offset from the finger slots (0, 60...)
            // Cut depth controlled by radius offset
            for(r=[15:30:360]) {
                rotate([0,0,r])
                tag("remove")
                translate([(neck_od + 20)/2, 0, cap_h/2])
                // Vertical rounded indentation
                cylinder(h=cap_h+1, d=8, center=true);
            }

            // Retention Lip at Bottom (neck_od + 6)
            tag("remove")
            translate([0,0,-0.5]) cylinder(h=cap_retention_h + 1, d=neck_od + 5);

            // Main Clearance (neck_od + 8)
            // Stops before the ceiling to create a closed top
            tag("remove")
            translate([0,0,cap_retention_h-0.5])
            cylinder(h=cap_h - cap_top_thick - (cap_retention_h - 0.5), d=neck_od + 9);

            // Top Lid rim Access Hole
            if(access_hole) {
                 // Simplified: Just remove the hole
                 tag("remove")
                 translate([0,0,cap_h-cap_top_thick-1]) cylinder(h=cap_top_thick+2, d=25);
            }

            // Slots for Fingers
            // Wider slots to allow fingers to flex inward/outward
            // Positioned to align with fingers
            // FIX: Don't cut top rim (bridge) or bottom retention ring
            slot_bottom = cap_retention_h + 1;
            slot_top = cap_h - 3;
            slot_height = slot_top - slot_bottom;
            slot_z = slot_bottom + slot_height/2;

            for(r=[0:60:360]) {
                rotate([0,0,r]) {
                    tag("remove")
                    translate([neck_od/2 + 6, 0, slot_z])
                    cube([10, 12, slot_height], center=true);
                }
            }
        }

        // Additive Ribbing (Knurling)
        Cap_Ribs();

        // Additive Fingers (Attached to Top)
        Cap_Fingers();
    }
}

module Cap_Ribs() {
    // Vertical ribs around the perimeter
    // Perimeter D = neck_od + 20
    rib_count = 72; // Every 5 degrees
    for(r=[0:360/rib_count:360]) {
        // Exclude ribs that interfere with finger slots
        // Slots are at 0, 60, 120... (Multiples of 60)
        // Slot width ~10 degrees. We skip +/- 8 degrees to be safe.
        check = r % 60;
        if (check > 8 && check < 52) {
            rotate([0,0,r])
            translate([(neck_od + 20)/2, 0, 0])
            cyl(h=cap_h-5, d=2, anchor=BOTTOM); // Stop before the rounded top
        }
    }
}

module Cap_Fingers() {
    for(r=[0:60:360]) {
        rotate([0,0,r]) {
            // Finger attached at Top
            // Positions:
            // Top Z = cap_h (Base of cantilever)
            // Center Radius = neck_od/2 + 6
            translate([neck_od/2 + 6, 0, cap_h])
            rotate([0, 180, 0]) // Hang down
            Cap_Finger_Single();
        }
    }
}

module Cap_Finger_Single() {
    len = cap_h - (cap_retention_h + 1);

    // Finger Body (Thinner for flexibility)
    // 3mm thick (Radial), 8mm wide (Tangential)
    // Attached at base (which is Top of cap in world space)
    cuboid([3, 8, len], anchor=BOTTOM) {
        // Pawl for engagement
        // Positioned near the "Tip" (Local TOP)
        // Local X+ points World Inward (after rotation)
        position(TOP) down(5)
        translate([1.5, 0, 0]) // On Inner Face (Local +X)
        rotate([0,90,0]) // Point along +X
        cyl(h=3, d=3, rounding2=1.5, anchor=BOTTOM); // Pawl with rounded tip
    }
}
