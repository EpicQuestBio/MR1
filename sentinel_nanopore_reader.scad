// ==============================================================================
// SENTINEL NANOPORE READER - REV 11 (MASTER MERGE)
// Features: Torque-Lock Cap + Round Stack + Bottom Integration + Internal Layout
// ==============================================================================
include <BOSL2/std.scad>
include <BOSL2/threading.scad>

/* [Render Mode] */
// Select "Assembly" for 3D view, or a specific layer for export
Output_Mode = "Assembly"; // [Assembly, Plate_1_Base_DXF, Plate_2_Channel_DXF, Plate_3_Top_DXF, Gasket_Main_DXF, Housing_Pump_Case_STL, Housing_Pump_Lid_STL, Housing_Reader_Case_STL, Housing_Reader_Lid_STL, Torque_Cap_Outer_STL, Torque_Cap_Inner_STL, Pressure_Puck_STL, Bottom_Pusher_Plate_STL, PCB_DXF]

/* [View Settings] */
Explode_Factor = 0; // [0:1:100]
Cross_Section = false;

/* [Torque Mechanism Settings] */
// How "stiff" the torque fingers appear (visual only)
Torque_Stiffness = 1.2;
Torque_Teeth_Count = 24;

/* [Sealed Top Option] */
Sealed_Top_Mode = false; // [true, false]

/* [Dimensions - Round Cartridge] */
plate_diam = 60;
plate_thick = 4;
gasket_thick = 0.8;
screw_bcd = 50;
screw_hole = 3.2; //M3
m3_insert_hole = 4.2;

// Port Locations (Radius from center)
port_radius = 20; // Expanded for 1/4" NPT fittings
angle_fluid_in_bot = -30;
angle_fluid_in_top = 30;
angle_fluid_out_bot = 150;
angle_fluid_out_top = 210;

angle_elec_cis = 90;  // Top electrode (via)
angle_elec_trans = 270; // Bottom electrode (direct)

/* [Interposer Dimensions] */
i_width = 15;
i_length = 15;
i_thickness = 1;
chip_size = 4;
pad_length = 3;
num_pads = 4;
pad_pitch = 2;
pad_width = 1;

/* [Dimensions - Housing & Components] */
base_w = 110; // Slightly wider for components
base_l = 110;
// Reader Module (Top) Height
reader_h = 40;
// Pump Module (Bottom) Height
pump_h = 70;

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

// PCB 2D Projection
module PCB_2D() {
    difference() {
        square([pcb_w, pcb_l], center=true);

        // Mounting Holes
        for(mx = [-pcb_w/2 + 5, pcb_w/2 - 5], my = [-pcb_l/2 + 5, pcb_l/2 - 5]) {
            translate([mx, my]) circle(d=3);
        }

        // Central Pass-through
       // circle(d=40);

        // Port Pass-throughs
        for(a = [angle_fluid_in_top, angle_fluid_out_top, angle_fluid_in_bot, angle_fluid_out_bot, angle_elec_cis, angle_elec_trans]) {
            rotate([0,0,a]) translate([port_radius, 0]) circle(d=6);
        }

                        // Cutouts for Pass-throughs
                        // cylinder(h=10, d=40, center=true); // Center
                        // for(a = [angle_fluid_in_top, angle_fluid_out_top, angle_elec_cis, angle_elec_trans]) {
                        //     rotate([0,0,a]) translate([port_radius, 0, 0]) cylinder(h=10, d=6, center=true);
                        // }
        PogoPinHoles();
    }
}

// 1. THE DISPOSABLE INTERPOSER CARD
module Interposer() {
    color("White", 0.8) { // Acrylic/COC plastic appearance
        difference() {
            // Main Body
            translate([-i_width/2, -i_length/2, 0])
            cube([i_width, i_length, i_thickness]);

            // Pocket for Silicon Chip
            translate([-chip_size/2, -chip_size/2, i_thickness - 0.5])
            cube([chip_size, chip_size, 0.6]);
        }
    }

    // The Silicon Chip (The Pore)
    color("Dimgrey")
    translate([-chip_size/2 + 0.1, -chip_size/2 + 0.1, i_thickness - 0.5])
    cube([chip_size-0.2, chip_size-0.2, 0.5]);

    // Electrical Contact Pads (Gold plated)
    // Located at the "front" edge, away from the central fluid area
    color("Gold")
    translate([0, i_length/2 - pad_length - 2, i_thickness]) {
        start_x = -((num_pads-1)*pad_pitch)/2;
        for(i = [0:num_pads-1]) {
            translate([start_x + (i*pad_pitch) - pad_width/2, 0, 0])
            cube([pad_width, pad_length, 0.1]);
        }
    }
}

module BoltHoles() {
    for(r = [45:90:360]) {
        rotate([0,0,r]) translate([screw_bcd/2, 0]) circle(d=screw_hole);
    }
}

module PogoPinHoles() {
     // Pogo Pin Access
        translate([0, 2.5]) {
            for(px = [-3, -1, 1, 3]) translate([px, 0]) circle(d=1.5);
        }
}

// L1: Base Plate (Interface)
module Plate_1_Base() {
    difference() {
        circle(d=plate_diam);
        BoltHoles();
        // Bottom Flush Ports
        rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0]) circle(d=4);
        // Top Flush Ports (Pass-through)
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);

        rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) circle(d=2);
        rotate([0,0,angle_elec_trans]) translate([port_radius, 0]) circle(d=2);
        // Trans-electrode trace
        hull() {
             rotate([0,0,angle_elec_trans]) translate([port_radius, 0]) circle(d=2);
             circle(d=2);
        }
        translate([plate_diam/2 - 3, 0]) circle(d=2); // Keying pin

        // Pogo Pin Access
        PogoPinHoles();
    }
}

// G1:  Gasket with or without pogo pins
module Gasket_Main(pogo= false) {
    difference() {
        circle(d=plate_diam);
        BoltHoles();

        // Central Fluid Cavity (Restricted to isolate pins)
        // Covers chip (4x4) and channel ends, but stays away from pins at Y=2.5
        square([14, 4.2], center=true);

        // Pass-throughs
        rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);

        rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) circle(d=2);
        translate([plate_diam/2 - 3, 0]) circle(d=2);

        // Pogo Pin Penetration Holes
        if(pogo) PogoPinHoles();

    }
}

// L2: Channel/Chip Layer
module Plate_2_Channel() {
    difference() {
        circle(d=plate_diam);
        BoltHoles();
        square([i_width + 0.2, i_length + 0.2], center=true); // Interposer Pocket

        // Bottom Flush Channels (Connect Bottom Ports to Chip Pocket)
        hull() {
            rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0]) circle(d=4);
            translate([3,0]) circle(d=3);
        }
        hull() {
            rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0]) circle(d=4);
            translate([-3,0]) circle(d=3);
        }

        // Top Flush Ports (Pass-through to Plate 3)
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);

        rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) circle(d=2);
        translate([plate_diam/2 - 3, 0]) circle(d=2);
    }
}

// L3: Top Cap (Pipette Well)
module Plate_3_Top() {
    difference() {
        circle(d=plate_diam);
        BoltHoles();

        // Sample Well / Pipette Access
        // If Sealed_Top_Mode is true, we remove this hole to seal the chamber.
        if (!Sealed_Top_Mode) {
             circle(d=6);
        }

        // Top Flush Channels (Connect Top Ports to Sample Well)
        // Even if sealed, we need the fluid path to the center.
        hull() {
             rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
             translate([3, 0]) circle(d=3); // Connect to well
        }
        hull() {
             rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);
             translate([-3, 0]) circle(d=3); // Connect to well
        }

        // Cis-Electrode Termination
        hull() {
            rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) circle(d=2);
            translate([0, 5]) circle(d=2);
        }
        translate([plate_diam/2 - 3, 0]) circle(d=2);
    }
}

module Cartridge_Stack_3D() {
    // Stack using translations to ensure robustness with linear_extrude objects

    // 0. Bottom Pusher Plate (Under Base Plate)
    down( Explode_Factor/4) // 3mm thickness
        Bottom_Pusher_Plate();

    // 1. Base Plate
    color("PowderBlue", 0.5) linear_extrude(plate_thick) Plate_1_Base();

    // 2. Gasket 1
    up(plate_thick + Explode_Factor/4)
        color("Red") linear_extrude(gasket_thick) Gasket_Main(pogo=true);

    // 3. Channel Plate + Interposer
    up(plate_thick + gasket_thick + Explode_Factor*2/4) {
        color("PowderBlue", 0.5) linear_extrude(plate_thick) Plate_2_Channel();
        // Interposer sits inside Plate 2
        // Pads need to face DOWN (towards PCB).
        // Rotate 180 around Y to flip pads to bottom.
        translate([0,0,i_thickness]) rotate([0, 180, 0]) Interposer();
    }

    // 4. Gasket 2
    up(plate_thick*2 + gasket_thick + Explode_Factor*3/4)
        color("Red") linear_extrude(gasket_thick) Gasket_Main(pogo=false);

    // 5. Top Plate
    up(plate_thick*2 + gasket_thick*2 + Explode_Factor)
        color("PowderBlue", 0.5)linear_extrude(plate_thick) Plate_3_Top(); 
        
    // 6. Puck
    up ( plate_thick*3 + gasket_thick*2 + Explode_Factor*2.3)
                Pressure_Puck_3D();
        
}

// ==============================================================================
// MODULE: BOTTOM PUSHER PLATE (TPU Seal)
// ==============================================================================
module Bottom_Pusher_Plate() {
    color("LightSlateGray")
    diff("remove")
    cyl(h=3, d=neck_id-0.5) { // Fits in neck
        tag("remove") {
            // Fluid Ports
            for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                zrot(a) translate([port_radius, 0, 0]) {
                    cyl(h=10, d=6, center=true); // Through hole
                    // O-Ring Seats (Top and Bottom)
                    position(TOP) torus(d_maj=8, d_min=1.5, anchor=CENTER);
                    position(BOTTOM) torus(d_maj=8, d_min=1.5, anchor=CENTER);
                }
            }
            // Electrode Ports
            for(a = [angle_elec_cis, angle_elec_trans]) {
                zrot(a) right(port_radius) cyl(h=10, d=4, center=true);
            }
            PogoPinHoles();
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
            
            
              //  #translate([0,0,2]) cylinder(h=plate_thick*2, d1=6, d2=14);
            
            // Center Hole for Pipette Access (Through-hole)
            translate([0,0,-1]) cylinder(h=20, d1=6, d2=16);
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
                 translate([0, y_pos, pump_h/2]) rotate([0,90,0])
                 cyl(h=wall*3, d=20, anchor=CENTER) {
                    tag("remove") threaded_rod(d=13.7, l=20, pitch=1.411, internal=true, anchor=CENTER);
                 }
             }
        }
        attach(RIGHT) {
             for(y_pos = [-20, 20]) {
                 translate([0, y_pos, pump_h/2]) rotate([0,90,0])
                 cyl(h=wall*3, d=20, anchor=CENTER) {
                    tag("remove") threaded_rod(d=13.7, l=20, pitch=1.411, internal=true, anchor=CENTER);
                 }
             }
        }

        // Connectivity (Back Wall)
        // DIN 5 MIDI (~16mm hole?) + Barrel Jack (8mm)
        attach(BACK) {
            // DIN 5
            translate([-20, 0, pump_h/2]) rotate([90,0,0])
            cyl(h=wall*3, d=16, anchor=CENTER) tag("remove");

            // Barrel Jack
            translate([20, 0, pump_h/2]) rotate([90,0,0])
            cyl(h=wall*3, d=8, anchor=CENTER) tag("remove");
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
        attach(TOP) {
            for(x = [-1, 1], y = [-1, 1]) {
                translate([x * (base_w/2 - 15), y * (base_l/2 - 15), 0])
                cuboid([10, 10, 5], rounding=2, edges="Z", anchor=BOTTOM);
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

// ==============================================================================
// MODULE: READER MODULE (Top Unit)
// ==============================================================================
module Housing_Case_Reader() {
    color("WhiteSmoke")
    diff("remove")
    cuboid([base_w+2*wall, base_l+2*wall, reader_h], rounding=wall, edges="Z", anchor=BOTTOM) {

        // Internal Bucket
        tag("remove") position(BOTTOM) up(wall)
        cuboid([base_w-2*wall, base_l-2*wall, reader_h+wall], anchor=BOTTOM);

        // Female Interlock Recesses (Bottom)
         attach(BOTTOM) {
            for(x = [-1, 1], y = [-1, 1]) {
                translate([x * (base_w/2 - 15), y * (base_l/2 - 15), 0])
                cuboid([10.5, 10.5, 6], rounding=2, edges="Z", anchor=BOTTOM) tag("remove");
            }
        }

        // Connectivity (Back Wall)
        attach(BACK) {
            // DIN 5
            translate([-20, 0, reader_h/2]) rotate([90,0,0])
            cyl(h=wall*3, d=16, anchor=CENTER) tag("remove");
            // Barrel Jack
            translate([20, 0, reader_h/2]) rotate([90,0,0])
            cyl(h=wall*3, d=8, anchor=CENTER) tag("remove");
        }

         // Lid Mounting Posts
        for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 - wall*1.5), y * (base_l/2 - wall*1.5), 0])
                 position(BOTTOM) up(wall)
                 cyl(h=reader_h-wall, d=8, anchor=BOTTOM) {
                    tag("remove") position(TOP) down(10) cyl(h=15, d=3, anchor=BOTTOM);
                 }
        }
    }
}

// Reader Module Lid (Top Unit) - Thicker for side ports
module Housing_Lid_Reader() {
    lid_thick = 15; // Increased thickness for horizontal ports

    color("Gainsboro")
    diff("remove")
    cuboid([base_w+2*wall, base_l+2*wall, lid_thick], rounding=wall, edges="Z", anchor=BOTTOM) {

        // PCB Mounts (Underside)
        attach(BOTTOM) {
            translate([0,0,0]) {
                // 1mm Standoffs for PCB (80x60 centered)
                for(mx = [-pcb_w/2 + 5, pcb_w/2 - 5], my = [-pcb_l/2 + 5, pcb_l/2 - 5]) {
                    translate([mx, my, 0]) cyl(h=1, d=6, anchor=TOP) {
                        tag("remove") cyl(h=5, d=2.5, anchor=BOTTOM); // Mounting screw hole
                    }
                }
            }
        }

        // Pogo Pin Holes
        tag("remove")
        position(BOTTOM) up(lid_thick/2) {
             translate([0, 2.5, 0])
             for(px = [-3, -1, 1, 3]) {
                 translate([px, 0, 0]) cyl(h=lid_thick*3, d=1.2, center=true);
             }
        }

        // Neck Transition & Thread (On Top)
        attach(TOP, overlap=5) // Embed into plate
        difference(){
            cyl(h=10, d1=base_w-10, d2=neck_od, anchor=BOTTOM)
            attach(TOP)
            threaded_rod(d=neck_od, l=neck_h, pitch=20, anchor=BOTTOM);

        // Neck Bore
        // Starts at TOP (Lid Surface) and goes UP to clear the neck, preserving the shelf below.
        tag("remove")
        position(TOP) down(5)
        cyl(h=neck_h+20, d=neck_id, anchor=BOTTOM);
        }

        // Horizontal Fluid Ports (Exiting Side)
        // We need 4 ports: Top In/Out, Bot In/Out.
        // Let's bring them all out the LEFT side for loop connectivity to Pump Module below?
        // Or Split Left/Right.
        // User said: "Have them come out of the lid... These are the connections that go to the stack."
        // We will make 4 side ports.
        attach(LEFT) {
             for(i = [0:3]) {
                 // Spaced out along Y
                 translate([0, -30 + (i*20), lid_thick/2]) rotate([0,90,0])
                 cyl(h=wall*4, d=8, anchor=CENTER) { // Luer/Barb adapter hole
                    tag("remove") cyl(h=20, d=5, center=true); // 5mm through hole
                 }
             }
        }

        // Internal Routing Channels (Connecting Side Ports to Central Manifold)
        // This is complex CSG. For visualization, we just ensure the manifold holes go UP.
        // In reality, printed channels would turn 90 degrees.
        // We will make vertical holes at the Port Locations (radius 20) going DOWN.
        // And horizontal holes from the side meeting them?
        // For now, let's keep the vertical pass-throughs for the stack interface.

        tag("remove")
        position(CENTER) {
            // Fluid Ports (Pass-through to bottom for stack)
            for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                zrot(a) right(port_radius) cyl(h=lid_thick*3, d=4, center=true);
            }
            // Electrode Ports
            for(a = [angle_elec_cis, angle_elec_trans]) {
                zrot(a) right(port_radius) cyl(h=lid_thick*3, d=4, center=true);
            }
        }

        // Mounting Holes (Corners)
        tag("remove") {
            for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 - wall*1.5), y * (base_l/2 - wall*1.5), 0])
                 cyl(h=lid_thick*3, d=3.5, center=true);
            }
        }
    }
}

// 1. Pump Module Assembly
module Pump_Module_Assembly() {
    Housing_Pump_Case();
    translate([0,0,pump_h + Explode_Factor]) Housing_Pump_Lid();

    // Internal Components
    if(!Cross_Section) {
         // Pumps (Visual)
        for(side = [-1, 1]) {
             translate([side * (base_w/4), 20, wall+5]) // On plate (wall+5)
             Peristaltic_Pump_12V();
        }
    }
}

// 2. Reader Module Assembly
module Reader_Module_Assembly() {
    Housing_Case_Reader();
    translate([0,0,reader_h + Explode_Factor]) Housing_Lid_Reader();

    // Stack & Cap on top of Lid
    translate([0,0, reader_h + 15 + Explode_Factor]) { // 15 is lid thick
        Cartridge_Stack_3D();
         // Torque Cap (Inner + Outer)
        translate([0,0, neck_h - 15 + Explode_Factor*2.5]) {
             Torque_Cap_Inner();
             translate([0,0,-2]) Torque_Cap_Outer();
        }
    }

    // PCB (Attached to Lid Underside)
    // Lid bottom is at z = reader_h
    // Standoffs 1mm down. PCB top at reader_h - 1.
    translate([0,0, reader_h - 1 - 1.6]) {
        color("Green") linear_extrude(1.6)PCB_2D();
    }
}


// ==============================================================================
// MAIN RENDER LOGIC
// ==============================================================================

if (Output_Mode == "Assembly") {

    difference() {
        union() {
            // Bottom Unit: Pump Module
            Pump_Module_Assembly();

            // Top Unit: Reader Module
            // Sits on top of Pump Module (Height pump_h + lid_wall)
            translate([0,0, pump_h + wall + Explode_Factor]) {
                Reader_Module_Assembly();
            }

            // External Tubing Loops (Visual)
            // Connecting Pump Module Side Ports -> Reader Module Side Ports
            if(!Cross_Section) {
                color("DeepSkyBlue") {
                    // Pump Out (Right Side) -> Reader In (Left Side)
                    // Visual loop around back
                    hull() {
                        translate([55+10, 20, pump_h/2]) sphere(d=4); // Pump Out
                        translate([55+30, 20, pump_h/2]) sphere(d=4); // Loop out
                    }
                     hull() {
                        translate([55+30, 20, pump_h/2]) sphere(d=4);
                        translate([55+30, 20, pump_h + reader_h + 15/2]) sphere(d=4); // Up
                    }
                    hull() {
                        translate([55+30, 20, pump_h + reader_h + 15/2]) sphere(d=4);
                         translate([-55-10, 20, pump_h + reader_h + 15/2]) sphere(d=4); // Over to Left
                    }
                }
            }
        }

        if(Cross_Section) {
            translate([0, -100, -10]) cube([200, 200, 300]);
        }
    }

    // Labels
    if (Explode_Factor > 0) {
        color("Black") {
            translate([0, -base_l/2 - 20, 0]) text("Rev 12: Modular Split", halign="center");
            translate([0, 0, pump_h + reader_h + neck_h + Explode_Factor*2.5 + 30]) text("Torque-Lock Cap", halign="center");
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
} else if (Output_Mode == "Housing_Pump_Case_STL") {
    Housing_Pump_Case();
} else if (Output_Mode == "Housing_Pump_Lid_STL") {
    Housing_Pump_Lid();
} else if (Output_Mode == "Housing_Reader_Case_STL") {
    Housing_Case_Reader();
} else if (Output_Mode == "Housing_Reader_Lid_STL") {
    Housing_Lid_Reader();
} else if (Output_Mode == "Torque_Cap_Outer_STL") {
    Torque_Cap_Outer();
} else if (Output_Mode == "Torque_Cap_Inner_STL") {
    Torque_Cap_Inner();
} else if (Output_Mode == "Pressure_Puck_STL") {
    Pressure_Puck_3D();
} else if (Output_Mode == "Bottom_Pusher_Plate_STL") {
    Bottom_Pusher_Plate();
} else if (Output_Mode == "PCB_DXF") {
    projection(cut=false) PCB_2D();
}
