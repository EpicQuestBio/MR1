// ==============================================================================
// SENTINEL NANOPORE READER - REV 11 (MASTER MERGE)
// Features: Torque-Lock Cap + Round Stack + Bottom Integration + Internal Layout
// ==============================================================================
include <BOSL2/std.scad>
include <BOSL2/threading.scad>

/* [Render Mode] */
// Select "Assembly" for 3D view, or a specific layer for export
Output_Mode = "Assembly"; // [Assembly, Plate_1_Base_DXF, Plate_2_Channel_DXF, Plate_3_Top_DXF, Gasket_Main_DXF, Housing_Case_STL, Housing_Lid_STL, Torque_Cap_Outer_STL, Torque_Cap_Inner_STL, Pressure_Puck_STL, Bottom_Pusher_Plate_STL, PCB_DXF]

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
        circle(d=10); // Chip area
        // Pass-throughs
        rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);

        rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) circle(d=2);
        translate([plate_diam/2 - 3, 0]) circle(d=2);
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
        color("Red") linear_extrude(gasket_thick) Gasket_Main();

    // 3. Channel Plate + Interposer
    up(plate_thick + gasket_thick + Explode_Factor*2/4) {
        color("PowderBlue", 0.5) linear_extrude(plate_thick) Plate_2_Channel();
        // Interposer sits inside Plate 2
        // Pads need to face DOWN (towards PCB).
        // Original: pads at z=thickness.
        // Flipped: zrot(0) xrot(180) -> pads at z=-thickness (relative to center?).
        // Interposer module is 0..thickness.
        // translate([0,0,thickness]) rotate([180,0,0]) Interposer()?
        // If rotate 180 X, [x,y,z] -> [x, -y, -z].
        // 0..1 becomes 0..-1.
        // Translate up by 1 -> 1..0.
        // Correct position.
        // Y coordinates also flip. Original pads at +y. Now at -y.
        // Original: i_length/2 - pad_length - 2 = 7.5 - 3 - 2 = 2.5.
        // Flipped: -2.5.
        // But our holes are at +2.5.
        // So we need to rotate 180 Z as well? Or flip Y?
        // rotate([180, 0, 180])?
        // If rotate 180 X: y->-y.
        // If rotate 180 Z: -y->y.
        // So rotate([180, 0, 180]) restores Y to +y, but Z is inverted (pads down).
        translate([0,0,i_thickness]) rotate([180, 0, 180]) Interposer();
    }

    // 4. Gasket 2
    up(plate_thick*2 + gasket_thick + Explode_Factor*3/4)
        color("Red") linear_extrude(gasket_thick) Gasket_Main(pogo= true);

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
// MODULE: HOUSING SPLIT (Case + Lid)
// ==============================================================================

module Housing_Case() {
    color("WhiteSmoke")
    union() {
        // Main Hollow Box (Open Top)
        diff("remove")
        cuboid([base_w+2*wall, base_l+2*wall, base_h], rounding=wall, edges="Z", anchor=BOTTOM) {

            // Internal Cavity (Bucket)
            tag("remove")
            position(BOTTOM) up(wall)
            cuboid([base_w-2*wall, base_l-2*wall, base_h+wall], anchor=BOTTOM); // Go up through top

            // Access Ports
            tag("remove") {
                // USB/Power Ports
                attach(FRONT, overlap=10) up(20) cyl(h=20, d=15);
                attach(RIGHT, overlap=10) up(30) cyl(h=20, d=10);
            }

            // External Fluid Ports (4x 1/4" NPT Threaded Holes)
            // Left Wall
            attach(LEFT) {
                for(y_pos = [-20, 20]) {
                    translate([0, y_pos, 30])
                    rotate([0, 90, 0])
                    cyl(h=wall*3, d=20, anchor=CENTER) {
                        tag("remove")
                        threaded_rod(d=13.7, l=20, pitch=1.411, internal=true, anchor=CENTER);
                    }
                }
            }
            // Right Wall (Additional ports if needed, or keeping it clean)
            // User asked for ports on outer shell. Putting 2 on Left, 2 on Right?
            // Or all 4 on one side? Spacing is better if distributed or all on Back/Sides.
            // Let's put 2 on LEFT, 2 on BACK to avoid the USB port on RIGHT/FRONT.

            attach(BACK) {
                for(x_pos = [-30, 30]) {
                    translate([x_pos, 0, 30])
                    rotate([90, 0, 0])
                    cyl(h=wall*3, d=20, anchor=CENTER) {
                        tag("remove")
                        threaded_rod(d=13.7, l=20, pitch=1.411, internal=true, anchor=CENTER);
                    }
                }
            }

            // Feet
            attach(BOTTOM) {
                for(x = [-1, 1], y = [-1, 1]) {
                    translate([x * (base_w/2 - 10), y * (base_l/2 - 10), 0])
                    cyl(h=5, d=10, anchor=TOP) {
                        tag("remove") attach(BOTTOM, overlap=8) cyl(h=8, d=m3_insert_hole, anchor=BOTTOM);
                    }
                }
            }

            // Lid Mounting Posts
            for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 - wall*1.5), y * (base_l/2 - wall*1.5), 0])
                 position(BOTTOM) up(wall)
                 cyl(h=base_h-wall, d=8, anchor=BOTTOM) {
                    tag("remove") position(TOP) down(10) cyl(h=15, d=3, anchor=BOTTOM); // Screw hole
                 }
            }
        }

        // 1. Pump Mounts (On Floor)
        // Two 12V Peristaltic Pumps (27.6mm dia motor)
        // Positioned symmetrically
        for(side = [-1, 1]) {
            translate([side * (base_w/4), -base_l/2 + 25, wall]) {
                // Pump socket
                difference() {
                    cylinder(h=15, d=34); // Socket Wall
                    translate([0,0,-1]) cylinder(h=17, d=28); // Motor clearance (27.6 + tolerance)

                    // Wire/Vent cutout
                    translate([0, -10, 5]) cube([10, 20, 20], center=true);
                }
            }
        }
    }
}

module Housing_Lid() {
    color("Gainsboro")
    diff("remove")
    cuboid([base_w+2*wall, base_l+2*wall, wall], rounding=wall, edges="Z", anchor=BOTTOM) {

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
        // Pads at y = 2.5 (approx). Width 6mm centered.
        // We need corresponding holes in the Lid.
        tag("remove")
        position(CENTER) {
             translate([0, 2.5, 0]) // Position under pads
             // pad_pitch = 2. num_pads=4.
             // start_x = -3. x = -3, -1, 1, 3.
             for(px = [-3, -1, 1, 3]) {
                 translate([px, 0, 0]) cyl(h=wall*3, d=1.2, center=true);
             }
        }

        // Neck Transition & Thread
        attach(TOP, overlap=wall/2) // Embed into plate
        difference(){
        cyl(h=10, d1=base_w-10, d2=neck_od, anchor=BOTTOM)
            attach(TOP)
            threaded_rod(d=neck_od, l=neck_h, pitch=20, anchor=BOTTOM);

        // Neck Bore
        //tag("remove")
        position(TOP) down(5)
        cyl(h=neck_h+20, d=neck_id, anchor=BOTTOM);
        }
        // Bosses for 1/4" NPT Fittings (Underside)
        attach(BOTTOM) {
            for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                zrot(a) translate([port_radius, 0, 0])
                cyl(h=12, d=22, anchor=BOTTOM) {
                    // 1/4" NPT Thread (Approximate: Tapered hole + thread)
                    // NPT 1/4" OD is ~13.7mm at large end. Pitch 18TPI ~1.4mm.
                    tag("remove")
                    threaded_rod(d=13.7, l=21, pitch=1.411, internal=true);
                }
            }
        }

        // Pass-throughs (Through Lid)
        tag("remove")
        position(CENTER) {
            // Fluid Ports (Small pass-throughs aligning with threads)
            for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                zrot(a) right(port_radius) cyl(h=wall*5, d=8, center=true);
            }
            // Electrode Ports
            for(a = [angle_elec_cis, angle_elec_trans]) {
                zrot(a) right(port_radius) cyl(h=wall*5, d=4, center=true);
            }
        }

        // Mounting Holes (Corners)
        tag("remove") {
            for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 - wall*1.5), y * (base_l/2 - wall*1.5), 0])
                 cyl(h=wall*3, d=3.5, center=true);
            }
        }
    }
}

module Housing_3D() {
    Housing_Case();
    translate([0,0,base_h+ Explode_Factor*0.4]) Housing_Lid();
}

// ==============================================================================
// MAIN RENDER LOGIC
// ==============================================================================

if (Output_Mode == "Assembly") {

    difference() {
        union() {
          #  Housing_3D();

            // Internals (Visual Only)
            if(!Cross_Section) {
                // PCB (Attached to Lid Standoffs)
                // Lid is at base_h. Standoffs are 1mm down.
                // PCB top surface is at base_h - 1. PCB thickness 1.6.
                // PCB is centered.
                translate([0,0, base_h - 1 - 1.6]) {
                    difference() {
                        color("Green") 
                        linear_extrude(1.6)PCB_2D();
                        
                    }
                    // Visual Pogo Pins
                    color("Gold")
                    translate([0, 2.5, 1.6/2]) { // On top surface
                         for(px = [-3, -1, 1, 3]) translate([px, 0, 0]) cylinder(h=10, d=1);
                    }
                }

                // Pumps (Visual)
                for(side = [-1, 1]) {
                     translate([side * (base_w/4), -base_l/2 + 25, wall - Explode_Factor])
                     Peristaltic_Pump_12V();
                }

                // Routing Lines (Visual)
                // Tubing: External Ports -> Pumps -> Lid Ports
                color("DeepSkyBlue") {
                    // Left Pump (Side -1) -> Left Wall Ports
                    // Path: Wall (-55) -> Pump In -> Pump Out -> Lid (-30 deg)

                    // Simple schematic lines
                    // External In -> Pump
                    hull() {
                        translate([-55, -20, 30]) sphere(d=4);
                        translate([-(base_w/4) + 12, -base_l/2 + 25 + 5, wall + 38 + 10]) sphere(d=4);
                    }

                    // Pump -> Lid Port (Inlet Bottom -30)
                    hull() {
                        translate([-(base_w/4) + 12, -base_l/2 + 25 - 5, wall + 38 + 10]) sphere(d=4);
                        rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0, base_h]) sphere(d=4);
                    }

                    // Right Pump (Side 1) -> Back Wall Ports?
                    // Let's route Right Pump to Top Inlet (30)
                    // External In -> Pump
                     hull() {
                        translate([-30, 55, 30]) sphere(d=4); // Back Port
                        translate([(base_w/4) + 12, -base_l/2 + 25 + 5, wall + 38 + 10]) sphere(d=4);
                    }

                    // Pump -> Lid Port (Inlet Top 30)
                    hull() {
                        translate([(base_w/4) + 12, -base_l/2 + 25 - 5, wall + 38 + 10]) sphere(d=4);
                        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0, base_h]) sphere(d=4);
                    }

                    // Outlets (Direct to Waste Ports)
                    // Outlet Bot (150) -> Left Wall 2
                    hull() {
                         rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0, base_h]) sphere(d=4);
                         translate([-55, 20, 30]) sphere(d=4);
                    }
                    // Outlet Top (210) -> Back Wall 2
                    hull() {
                         rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0, base_h]) sphere(d=4);
                         translate([30, 55, 30]) sphere(d=4);
                    }
                }
            }

            // Stack
            translate([0,0, base_h + wall + Explode_Factor]) Cartridge_Stack_3D();



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
} else if (Output_Mode == "Housing_Case_STL") {
    Housing_Case();
} else if (Output_Mode == "Housing_Lid_STL") {
    Housing_Lid();
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
