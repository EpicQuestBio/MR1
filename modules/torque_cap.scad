// ==============================================================================
// MODULE: TORQUE-LOCK CAP (Hollow for Pipette)
// ==============================================================================
module Torque_Cap_Inner() {
    color("Silver")
    diff("remove")
    cyl(h=20, d=neck_od + 4, anchor=BOTTOM) {
        // Ratchet Teeth
        for(r=[0:(360/Torque_Teeth_Count):360]) {
            // Position teeth vertically at the perimeter
            zrot(r) position(RIGHT) cyl(h=20, d=3, $fn=3, anchor=CENTER);
        }

        // Threads
        tag("remove")
        position(BOTTOM) down(1)
        threaded_rod(d=neck_od+1, l=22, internal=true, pitch=20, anchor=BOTTOM);

        // Pipette Access Hole
        tag("remove")
        position(BOTTOM) down(1)
        cyl(h=30, d=22, anchor=BOTTOM);
    }
}

module Torque_Cap_Outer() {
    color("Orange") {
        difference() {
            cylinder(h=25, d=neck_od + 20); // Outer Shell
            translate([0,0,-1]) cylinder(h=27, d=neck_od + 8); // Clearance for Inner
        }
        // Top Lid rim
        translate([0,0,20]) difference() {
            cylinder(h=5, d=neck_od + 20);
            translate([0,0,-1]) cylinder(h=7, d=25); // Pipette Access Hole
        }

        // Spring Arms
        for(r=[0:60:360]) {
            rotate([0,0,r]) {
                translate([neck_od/2 + 6, 0, 10]) {
                    cube([4, 15, 18], center=true); // Arm
                    translate([-3, 6, 0]) cylinder(h=18, d=3, center=true); // Pawl
                }
            }
        }
    }
}
