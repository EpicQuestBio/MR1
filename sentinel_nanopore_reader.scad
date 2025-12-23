// ==============================================================================
// SENTINEL NANOPORE READER - REV 11 (MASTER MERGE)
// Features: Torque-Lock Cap + Round Stack + Bottom Integration + Internal Layout
// ==============================================================================
include <BOSL2/std.scad>
include <BOSL2/threading.scad>

/* [Render Mode] */
// Select "Assembly" for 3D view, or a specific layer for export
Output_Mode = "Assembly"; // [Assembly, Plate_1_Base_DXF, Plate_2_Channel_DXF, Plate_3_Top_DXF, Gasket_Main_DXF, Housing_Base_STL, Torque_Cap_Outer_STL, Torque_Cap_Inner_STL, Pressure_Puck_STL]

/* [View Settings] */
Explode_Factor = 100; // [0:1:100]
Cross_Section = false;

/* [Torque Mechanism Settings] */
// How "stiff" the torque fingers appear (visual only)
Torque_Stiffness = 1.2;
Torque_Teeth_Count = 24;

/* [Dimensions - Round Cartridge] */
plate_diam = 60;
plate_thick = 4;
gasket_thick = 0.8;
screw_bcd = 50;
screw_hole = 3.2; //M3

// Port Locations (Radius from center)
port_radius = 12;
angle_fluid_in = 0;
angle_fluid_out = 180;
angle_elec_cis = 90;  // Top electrode (via)
angle_elec_trans = 270; // Bottom electrode (direct)

/* [Dimensions - Housing & Components] */
base_w = 110; // Slightly wider for components
base_l = 110;
base_h = 60;
neck_od = 90;
neck_id = 61;
neck_h = 45;
wall = 4;

// Internal Component Placeholders
pcb_w = 80; pcb_l = 60;
pump_w = 42; pump_l = 60;

/* [Global] */
$fn = 80;
epsilon = 0.01;

// ==============================================================================
// MODULES: CARTRIDGE LAYERS (Round + Bottom Ports)
// ==============================================================================

module BoltHoles() {
    for(r = [45:90:360]) {
        rotate([0,0,r]) translate([screw_bcd/2, 0]) circle(d=screw_hole);
    }
}

// L1: Base Plate (Interface)
module Plate_1_Base() {
    difference() {
        circle(d=plate_diam);
        BoltHoles();
        // Bottom Ports
        rotate([0,0,angle_fluid_in]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) circle(d=2);
        rotate([0,0,angle_elec_trans]) translate([port_radius, 0]) circle(d=2);
        // Trans-electrode trace
        hull() {
             rotate([0,0,angle_elec_trans]) translate([port_radius, 0]) circle(d=2);
             circle(d=2);
        }
        translate([plate_diam/2 - 3, 0]) circle(d=2); // Keying pin
    }
}

// G1: Main Gasket
module Gasket_Main() {
    difference() {
        circle(d=plate_diam);
        BoltHoles();
        circle(d=10); // Chip area
        // Pass-throughs
        rotate([0,0,angle_fluid_in]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) circle(d=2);
        translate([plate_diam/2 - 3, 0]) circle(d=2);
    }
}

// L2: Channel/Chip Layer
module Plate_2_Channel() {
    difference() {
        circle(d=plate_diam);
        BoltHoles();
        square([6,6], center=true); // Chip Pocket
        // Channels
        hull() {
            rotate([0,0,angle_fluid_in]) translate([port_radius, 0]) circle(d=4);
            translate([3,0]) circle(d=3);
        }
        hull() {
            rotate([0,0,angle_fluid_out]) translate([port_radius, 0]) circle(d=4);
            translate([-3,0]) circle(d=3);
        }
        rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) circle(d=2);
        translate([plate_diam/2 - 3, 0]) circle(d=2);
    }
}

// L3: Top Cap (Pipette Well)
module Plate_3_Top() {
    difference() {
        circle(d=plate_diam);
        BoltHoles();
        circle(d=6); // Sample Well
        // Cis-Electrode Termination
        hull() {
            rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) circle(d=2);
            translate([0, 5]) circle(d=2);
        }
        translate([plate_diam/2 - 3, 0]) circle(d=2);
    }
}

module Cartridge_Stack_3D() {
    color("PowderBlue", 0.5) linear_extrude(plate_thick) Plate_1_Base()
        attach(TOP, overlap=-Explode_Factor/4)
        color("Red") linear_extrude(gasket_thick) Gasket_Main()
            attach(TOP, overlap=-Explode_Factor/4)
            color("PowderBlue", 0.5) linear_extrude(plate_thick) Plate_2_Channel()
                attach(TOP, overlap=-Explode_Factor/4)
                color("Red") linear_extrude(gasket_thick) Gasket_Main()
                    attach(TOP, overlap=-Explode_Factor/4)
                    color("PowderBlue", 0.5) {
                        difference() {
                            linear_extrude(plate_thick*2) Plate_3_Top();
                            translate([0,0,2]) cylinder(h=plate_thick*2, d1=6, d2=14);
                        }
                    }
}

// ==============================================================================
// MODULE: PRESSURE PUCK (Pipette Access)
// ==============================================================================
module Pressure_Puck_3D() {
    color("#333333") {
        difference() {
            union() {
                cylinder(h=6, d=neck_id - 1);
                // Handle Tabs
                translate([0, 22, 0]) cylinder(h=6, d=8);
                translate([0, -22, 0]) cylinder(h=6, d=8);
            }
            // Center Hole for Pipette Access (Through-hole)
            translate([0,0,-1]) cylinder(h=20, d=16);
            // Underside recess to avoid crushing Top Plate features
            translate([0,0,-1]) difference() {
                cylinder(h=3, d=neck_id-4);
                cylinder(h=4, d=20); // Only press on center ring
            }
        }
    }
}

// ==============================================================================
// MODULE: TORQUE-LOCK CAP (Hollow for Pipette)
// ==============================================================================
module Torque_Cap_Inner() {
    color("Silver")
    diff("remove")
    cyl(h=20, d=neck_od + 4, anchor=BOTTOM) {
        // Ratchet Teeth
        for(r=[0:(360/Torque_Teeth_Count):360]) {
            zrot(r) attach(RIGHT, overlap=1.5) cyl(h=20, d=3, $fn=3);
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

// ==============================================================================
// MODULE: HOUSING (Integrated Internal Mounts)
// ==============================================================================
module Housing_3D() {
    color("WhiteSmoke")
    diff("remove")
    cuboid([base_w+2*wall, base_l+2*wall, base_h+wall/2], rounding=wall, edges="Z", anchor=BOTTOM) {

        // Neck Transition & Thread
        attach(TOP, overlap=wall/2)
        cyl(h=10, d1=base_w-10, d2=neck_od, anchor=BOTTOM)
            attach(TOP)
            threaded_rod(d=neck_od, l=neck_h, pitch=20, anchor=BOTTOM);

        // Internal Cavity
        tag("remove")
        position(BOTTOM) up(wall)
        cuboid([base_w-2*wall, base_l-2*wall, base_h+neck_h], anchor=BOTTOM);

        // Neck Bore
        tag("remove")
        position(TOP) down(5)
        cyl(h=neck_h+20, d=neck_id, anchor=BOTTOM);

        // Interface Shelf Openings (Top of base_h)
        tag("remove")
        position(TOP) down(wall/2) {
            cyl(h=10, d=40, center=true); // Center opening
            for(a = [angle_fluid_in, angle_fluid_out, angle_elec_cis, angle_elec_trans]) {
                zrot(a) right(port_radius) down(5) cyl(h=20, d=6, center=true);
            }
        }

        // Access Ports
        tag("remove") {
            attach(FRONT, overlap=10) up(20) cyl(h=20, d=15);
            attach(RIGHT, overlap=10) up(30) cyl(h=20, d=10);
        }

        // --- INTERNAL COMPONENT MOUNTS ---

        // 1. Pump Mount
        // Position relative to center of floor
        position(BOTTOM) up(wall) translate([base_w/2 - pump_w - 5, base_l/2 - pump_l - 5, 0]) {
             difference() {
                 cube([pump_w+5, pump_w+5, 10]); // Bracket Base
                 translate([2.5, 2.5, -1]) cube([pump_w, pump_w, 12]); // Motor cutout
            }
            // Screw holes for NEMA17 (31mm spacing)
            translate([2.5 + (pump_w-31)/2, 2.5 + (pump_w-31)/2, 0]) cylinder(h=5, d=3);
            translate([2.5 + (pump_w-31)/2 + 31, 2.5 + (pump_w-31)/2, 0]) cylinder(h=5, d=3);
        }

        // 2. PCB Mount
        position(BOTTOM) up(wall) translate([-base_w/2 + 10, -base_l/2 + 10, 0]) {
             cylinder(h=5, d=6); // Standoff 1
             translate([pcb_w-5, 0, 0]) cylinder(h=5, d=6);
             translate([0, pcb_l-5, 0]) cylinder(h=5, d=6);
             translate([pcb_w-5, pcb_l-5, 0]) cylinder(h=5, d=6);
        }
    }
}

// ==============================================================================
// MAIN RENDER LOGIC
// ==============================================================================

if (Output_Mode == "Assembly") {

    difference() {
        union() {
            Housing_3D();

            // Internals (Visual Only)
            if(!Cross_Section) {
                // PCB
                color("Green") translate([-base_w/2 + 10, -base_l/2 + 10, wall+5- Explode_Factor]) cube([pcb_w, pcb_l, 1.6]);
                // Pump
                color("Silver") translate([base_w/2 - pump_w - 2.5, base_l/2 - pump_l - 2.5, wall- Explode_Factor]) cube([pump_w, pump_w, 40]);

                // Routing Lines (Visual)
                color("DeepSkyBlue") {
                    rotate([0,0,angle_fluid_in]) translate([port_radius, 0, 20]) cylinder(h=40, d=3);
                    rotate([0,0,angle_fluid_out]) translate([port_radius, 0, 20]) cylinder(h=40, d=3);
                }
            }

            // Stack
            translate([0,0, base_h + Explode_Factor]) Cartridge_Stack_3D();

            // Puck
            translate([0,0, base_h + (plate_thick*4 + gasket_thick*2) + Explode_Factor*2.3])
                Pressure_Puck_3D();

            // Torque Cap (Inner + Outer)
            translate([0,0, base_h + neck_h - 15 + Explode_Factor*2.5]) {
                 Torque_Cap_Inner();
                 translate([0,0,-2]) Torque_Cap_Outer();
            }
        }

        if(Cross_Section) {
            translate([0, -100, -10]) cube([200, 200, 300]);
        }
    }

    // Labels
    if (Explode_Factor > 0) {
        color("Black") {
            translate([0, -base_l/2 - 20, 0]) text("Rev 11: Master Integration", halign="center");
            translate([0, 0, base_h + neck_h + Explode_Factor*2.5 + 30]) text("Torque-Lock Cap (Hollow)", halign="center");
        }
    }

// --- DXF / STL EXPORTS ---
} else if (Output_Mode == "Plate_1_Base_DXF") {
    projection(cut=false) Plate_1_Base();
} else if (Output_Mode == "Plate_2_Channel_DXF") {
    projection(cut=false) Plate_2_Channel();
} else if (Output_Mode == "Plate_3_Top_DXF") {
    projection(cut=false) Plate_3_Top();
} else if (Output_Mode == "Gasket_Main_DXF") {
    projection(cut=false) Gasket_Main();
} else if (Output_Mode == "Housing_Base_STL") {
    Housing_3D();
} else if (Output_Mode == "Torque_Cap_Outer_STL") {
    Torque_Cap_Outer();
} else if (Output_Mode == "Torque_Cap_Inner_STL") {
    Torque_Cap_Inner();
} else if (Output_Mode == "Pressure_Puck_STL") {
    Pressure_Puck_3D();
}