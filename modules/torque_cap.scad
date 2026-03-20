// ==============================================================================
// MODULE: TORQUE-LOCK CAP (Hollow for Pipette)
// ==============================================================================

//TODO: Torque_Cap_Inner height needs to be consistent with maybe wall thickness

module Torque_Cap_Inner(access_hole=true) {
    // Dynamic Thread Length: Needs to cover enough neck to reach stability
    // neck_h is defined relative to stack.
    // Cap height should roughly match neck_clearance + engagement.

    // PETG Ring with Sine Teeth
    color("Silver")
    diff("remove")
    cyl(h=cap_inner_h, d=neck_od + 4, anchor=BOTTOM) {
        // Retention Flange at Bottom
        position(BOTTOM) cyl(d=neck_od + 6.4, h=cap_retention_h, rounding=1, anchor=BOTTOM);

        // Ratchet Teeth
        // Even with top, starting above retention
        position(BOTTOM) for(r=[0:(360/Torque_Teeth_Count):360]) {
            // Position teeth vertically at the perimeter
            zrot(r)
            translate([neck_od/2 + 2, 0, cap_retention_h])
            // zrot(180) // Point triangle outward
            cyl(h=cap_inner_h - cap_retention_h, r=tooth_height, $fn=3, anchor=BOTTOM);
        }

        // Threads
        tag("remove")
        position(BOTTOM) down(1)
        threaded_rod(d=neck_od+1, l=cap_inner_h, internal=true, pitch=cap_thread_pitch, anchor=BOTTOM);

        if(access_hole) {
           // Pipette Access Hole
           tag("remove")
           position(BOTTOM) down(1)
           cyl(h=cap_inner_h+10, d=25, anchor=BOTTOM);
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
   translate([0,0, cap_retention_h + Explode_Factor])
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
                translate([(neck_od + 20)/2, 0, slot_height/2])
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
                    // Offset Y to accommodate the horizontal tangential arm of 15mm
                    translate([neck_od/2 + 6, 15/2, slot_z])
                    cube([10, 22, slot_height], center=true);
                }
            }
        }

        // Additive Ribbing (Knurling)
        Cap_Ribs();

        // Additive Fingers (Attached to Side)
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
        // Horizontal arm slot is extended (up to ~30 degrees), so we skip more ribs.
        check = r % 60;
        // Ribs at 35, 40 are safe. The slot cuts through 0..30 roughly.
        // We also want to avoid Grip Indentations at 45.
        // So we only keep ribs at check == 35 or check == 40 to prevent floating ribs.
        if (check == 35 || check == 40) {
            rotate([0,0,r])
            translate([(neck_od + 20)/2, 0, cap_retention_h])
            cyl(h=cap_h-5, d=2, anchor=BOTTOM); // Stop before the rounded top
        }
    }
}

module Cap_Fingers() {
    slot_bottom = cap_retention_h + 1;
    slot_top = cap_h - 3;
    slot_height = slot_top - slot_bottom;
    slot_z = slot_bottom + slot_height/2;

    for(r=[0:60:360]) {
        rotate([0,0,r]) {
            // Finger attached at the wall
            // Positions:
            // Center Z = slot_z
            // Center Radius = neck_od/2 + 6
            translate([neck_od/2 + 6, 0, slot_z])
            Cap_Finger_Single(h=slot_height - 2);
        }
    }
}

module Cap_Finger_Single(h) {
    len = 15; // Based on historically discovered length for more flex

    // Finger Body (Horizontal/Tangential)
    // 3mm thick (Radial), 15mm long (Tangential), h height (Vertical)
    // Attached at base (Y=0 locally) pointing +Y
    cuboid([3, len, h], anchor=FRONT) {
        // Pawl for engagement
        // Positioned near the free end (BACK in local frame)
        // Local X- points World Inward
        position(BACK)
        translate([-1.5, 0, 0]) // On Inner Face (Local -X)
        rotate([0,90,0]) // Point along -X
        cyl(h=3, d=3, rounding2=1.5, anchor=TOP); // Pawl with rounded tip
    }
}
