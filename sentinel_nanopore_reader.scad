// ==============================================================================
// SENTINEL NANOPORE READER - REV 12 (Modular Split)
// Features: Torque-Lock Cap + Round Stack + Bottom Integration + Internal Layout
// ==============================================================================
include <BOSL2/std.scad>
include <BOSL2/threading.scad>

/* [Render Mode] */
// Select "Assembly" for 3D view, or a specific layer for export
Output_Mode = "Assembly"; // [Assembly, Plate_1_Base_DXF, Plate_2_Channel_DXF, Plate_3_Top_DXF, Gasket_Main_DXF, Housing_Pump_Case_STL, Housing_Pump_Lid_STL, Housing_Reader_Case_STL, Housing_Reader_Lid_STL, Torque_Cap_Outer_STL, Torque_Cap_Inner_STL, Pressure_Puck_STL, Bottom_Pusher_Plate_STL, PCB_DXF]

/* [View Settings] */
Explode_Factor = 100; // [0:1:100]
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

/* [Dimensions - Hexagonal Cartridge] */
hex_diam = 60; // Corner-to-corner diameter
hex_wall = 3;  // Minimum wall thickness for frames
pogo_y = -15;  // Y position of the pogo pin row
pogo_x_spacing = 5; // Spacing between pins

/* [Active Cartridge Settings] */
pcb_thick = 0.8;      // THIN RIGID FR4
carrier_thick = 2.6;  // Reduced height for thin PCB + components
opamp_h = 1.75;       // SOIC-8 Height
Show_Components = true;

/* [Internal Sealing & Potting] */
oring_id = 10;
oring_cs = 1.78;
Show_Potting = true;
Show_O_Rings = true;

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
fn_draft = 40;
fn_prod = 200;
g_fn = fn_draft;
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

// 2. THE RIGID ACTIVE PCB (Rev 19)
module PCB_Rigid_Active() {
    // 0.8mm FR4 Substrate
    pcb_w = 28; pcb_l = 38;

    difference() {
        // 0.8mm FR4 Substrate (Green)
        color("ForestGreen")
        translate([-pcb_w/2, -pcb_l/2, 0]) cube([pcb_w, pcb_l, pcb_thick]);

        // Chip Void
        cylinder(h=10, d=10, center=true);
    }

    // --- ACTIVE COMPONENTS (Top Side) ---
    if(Show_Components) {
        // LMP7721 OpAmp (The Critical Component)
        // Placed as close to the void as possible to minimize trace length
        translate([8, 6, pcb_thick]) {
            color("#333333") cube([5, 6, opamp_h]); // Body
            color("Silver") translate([-1, 0.5, 0]) cube([1, 5, 0.5]); // Pins
            color("Silver") translate([5, 0.5, 0]) cube([1, 5, 0.5]); // Pins
        }

        // Feedback Resistor (100M/1G)
        translate([8, -2, pcb_thick]) color("Blue") cube([3.2, 1.6, 0.6]);

        // Decoupling Caps (0.1uF)
        translate([12, 14, pcb_thick]) color("Brown") cube([1.6, 0.8, 0.6]);
    }

    // --- ELECTRODES (Silver Ribbons) ---
    // Solder pads + Ribbons leading into the void
    color("Silver") {
        // Top Ribbon (V+)
        translate([-4, 8, pcb_thick]) cube([2, 4, 0.1]); // Pad
        translate([-3, 5, pcb_thick]) cube([2, 3, 0.1]); // Trace
    }

    // --- INTERFACE PADS (Bottom Side) ---
    // These touch the Pogo Pins in the Base
    color("Gold") {
        for(i=[-2:2]) translate([i*5, -15, -0.01]) cube([3, 3, 0.05], center=true);
    }

    // Chip Mockup
    color("Silver") translate([0,0,pcb_thick/2]) cube([5,5,0.5], center=true);
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

// O_Ring_Inner: Seals Fluid Path to Potting Puck
module O_Ring_Inner() {
    // Standard Torus
    color("DeepSkyBlue")
    rotate_extrude($fn=g_fn)
    translate([oring_id/2 + oring_cs/2, 0, 0]) // ID + CS/2 = Center Radius
    circle(d=oring_cs, $fn=g_fn);
}

// L2_Hex: Carrier Frame (Hexagonal)
module Carrier_Frame_Hex() {
    // Replaces Plate_2_Channel
    // Holds PCB_Rigid_Active (28x38x0.8)

    // New dimensions
    // Thickness = 2.6mm (carrier_thick)
    // PCB Pocket = Through hole (PCB sits on bottom gasket)

    ins_w = 28;
    ins_l = 38;

    difference() {
        circle(d=hex_diam, $fn=6); // Corner-to-corner hex
      //  BoltHoles();

        // PCB Pocket (Through Hole)
        square([ins_w + 0.5, ins_l + 0.5], center=true);

        // Fluid Pass-throughs (Outside the PCB area)
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0]) circle(d=4);
    }
}

module PogoPinHoles() {
    // OLD Pogo Pin Access (Rev 12 Cluster)
    // translate([0, 3.5]) {
    //    for(px = [-3, -1, 1, 3]) translate([px, 0]) circle(d=1.5);
    // }

    // NEW Pogo Pin Access (Rev 18/Hex Linear)
    // 5 pins at pogo_y
    for(i=[-2:2]) {
         translate([i*pogo_x_spacing, pogo_y]) circle(d=3.2, $fn=g_fn); // Clearance for pogo head/shaft
    }
}

// L1: Base Plate (Interface) - Hexagonal Version
module Plate_1_Base_Hex() {
    difference() {
        circle(d=hex_diam, $fn=6);
       // BoltHoles();
        // All Ports are simple vertical pass-throughs or seats
        // Channels are now in the Gasket
        rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);
    }
}

// L1: Base Plate (Interface) - Round Legacy
module Plate_1_Base() {
    difference() {
        circle(d=plate_diam);
        //BoltHoles();
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
       // BoltHoles();

        // Central Fluid Cavity (Restricted to isolate pins)
        // Covers chip (4x4) and channel ends, but stays away from pins at Y=2.5
        square([4.2, 4.2], center=true);

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

// Gasket Low Dead Volume (Replaces Gasket_Hex)
module Gasket_Low_Dead_Volume(type="bottom") {
    // type: "bottom" or "top"

    // Determine angles based on type
    // Bottom: In=-30, Out=150. Top: In=30, Out=210.
    active_in = (type=="bottom") ? angle_fluid_in_bot : angle_fluid_in_top;
    active_out = (type=="bottom") ? angle_fluid_out_bot : angle_fluid_out_top;

    // Determine pass-through angles (the other pair)
    pass_angles = (type=="bottom")
        ? [angle_fluid_in_top, angle_fluid_out_top]
        : [angle_fluid_in_bot, angle_fluid_out_bot];

    // Slot Connection Points (Y coordinates)
    // Bottom In (Y~-10) -> Connect to South Slot End (-8)
    // Top In (Y~10) -> Connect to North Slot End (8)
    slot_y_in = (type=="bottom") ? -8 : 8;

    // Bottom Out (Y~10) -> Connect to North Slot End (8)
    // Top Out (Y~-10) -> Connect to South Slot End (-8)
    slot_y_out = (type=="bottom") ? 8 : -8;

    difference() {
        circle(d=hex_diam, $fn=6);
      //  BoltHoles();

        // Pass-throughs
        for(a = pass_angles) {
            rotate([0,0,a]) translate([port_radius, 0]) circle(d=4);
        }

        // --- LOW DEAD VOLUME CHANNEL ---
        // 1. Central "Race Track" Slot over Chip & Ribbons
        hull() {
             translate([0, -8, 0]) circle(d=8);
             translate([0, 8, 0]) circle(d=8);
        }

        // 2. Connection from Inlet Port to Slot
        hull() {
             rotate([0,0,active_in]) translate([port_radius, 0]) circle(d=4);
             translate([0, slot_y_in, 0]) circle(d=4);
        }

        // 3. Connection from Slot to Outlet Port
        hull() {
             rotate([0,0,active_out]) translate([port_radius, 0]) circle(d=4);
             translate([0, slot_y_out, 0]) circle(d=4);
        }

        // Pogo Pin Penetration Holes (Only for Top Gasket)
        if(type == "top") {
             PogoPinHoles();
        }
    }
}

// G1_Hex: Gasket (Hexagonal) - Legacy
module Gasket_Hex(pogo=false) {
   Gasket_Low_Dead_Volume(type = pogo ? "top" : "bottom");
}

// L2: Channel/Chip Layer
module Plate_2_Channel() {
    difference() {
        circle(d=plate_diam);
      //  BoltHoles();
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

// L3_Hex: Top Cap (Hexagonal)
module Plate_3_Top_Hex() {
    difference() {
        circle(d=hex_diam, $fn=6);
        //BoltHoles();

        // Sample Well / Pipette Access
        // Used to access the central Gasket Channel from above
        if (!Sealed_Top_Mode) {
             circle(d=6);
        }

        // Channels are now in the Gasket.
        // We just need vertical port holes.
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);

        // Pogo Pin Access (Top-Down)
        PogoPinHoles();
    }
}

// L3: Top Cap (Pipette Well)
module Plate_3_Top() {
    difference() {
        circle(d=plate_diam);
      //  BoltHoles();

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
    // UPDATED FOR REV 19 RIGID ACTIVE CARTRIDGE

    plate_thick_pp = 3;
    stack_z = -3;

    // 0. Bottom Pusher Plate (Under Base Plate)
    down( Explode_Factor/4) // 3mm thickness
        Bottom_Pusher_Plate();
        
    // 1. Base Plate (Hex) - 4mm
    color("PowderBlue", 0.5) linear_extrude(plate_thick) Plate_1_Base_Hex();
    
    // 1.5. INNER O-RING (Bottom Seal)
    if(Show_O_Rings)
        translate([0,0,stack_z + plate_thick_pp + 0.2+ Explode_Factor*1/6]) O_Ring_Inner();
        
    // 2. Gasket 1 (Hex) - Bottom - 0.8mm
    up(plate_thick + Explode_Factor/6)
        color("Red") linear_extrude(gasket_thick) Gasket_Low_Dead_Volume(type="bottom");

    // 3. Carrier Frame (Hex) + PCB Rigid Active
    // Carrier height reduced to 2.6mm
    up(plate_thick + gasket_thick + Explode_Factor*3/6) {
        color("PowderBlue", 0.5) linear_extrude(carrier_thick) Carrier_Frame_Hex();

        // PCB Sits inside, flush with bottom
        translate([0,0,0]) PCB_Rigid_Active();
    }

    // 4. Gasket 2 (Hex) - Top - 0.8mm
    up(plate_thick + gasket_thick + carrier_thick + Explode_Factor*4/6)
        color("Red") linear_extrude(gasket_thick) Gasket_Low_Dead_Volume(type="top");

    // 5. Top Plate (Hex) - 4mm
    up(plate_thick + gasket_thick + carrier_thick + gasket_thick + Explode_Factor)
        color("PowderBlue", 0.5)linear_extrude(plate_thick) Plate_3_Top_Hex();
        
    // 6. Puck
    up ( plate_thick*2 + gasket_thick*2 + carrier_thick + Explode_Factor*1.2)
                Pressure_Puck_3D();
        
}

// ==============================================================================
// MODULE: BOTTOM PUSHER PLATE (TPU Seal)
// ==============================================================================
module Bottom_Pusher_Plate(show_orings=Show_O_Rings) {
    // Dimensions
    pp_h = 3;
    port_d = 6;

    // O-Ring Dimensions (Port Seals)
    // Seat: d_maj=8, d_min=1.5 (CS)
    or_cs = 1.5;
    or_maj = 8.0;

    union() {
        color("LightSlateGray")
        diff("remove")
        cyl(h=pp_h, d=hex_diam, $fn=6) { // Fits in HEX neck

            // Fluid Ports (4x)
            for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                zrot(a) translate([port_radius, 0, 0]) {

                    // 1. Through Hole
                    tag("remove") cyl(h=pp_h + 1, d=port_d, center=true, $fn=g_fn);

                    // 2. O-Ring Seats (Subtractive)
                    tag("remove") {
                        position(TOP) torus(d_maj=or_maj, d_min=or_cs, anchor=CENTER, $fn=g_fn);
                        position(BOTTOM) torus(d_maj=or_maj, d_min=or_cs, anchor=CENTER, $fn=g_fn);
                    }
                }
            }

            // Pogo Pin Clearance
            tag("remove") linear_extrude(10, center= true) PogoPinHoles();
        }

        // 3. O-Rings (Additive, Visual)
        if (show_orings) {
            for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                zrot(a) translate([port_radius, 0, 0]) {
                    // Top O-Ring
                    translate([0,0, pp_h/2])
                        color("DeepSkyBlue")
                        torus(d_maj=or_maj, d_min=or_cs, anchor=CENTER, $fn=g_fn);

                    // Bottom O-Ring
                    translate([0,0, -pp_h/2])
                        color("DeepSkyBlue")
                        torus(d_maj=or_maj, d_min=or_cs, anchor=CENTER, $fn=g_fn);
                }
            }
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

                // EXTENSION RING for Thinner Stack (Rev 19)
                // Stack lost ~1.4mm. We add a ring to push down further.
                translate([0,0,-1.4]) cylinder(h=1.4, d=neck_id - 1);
            }
            
            // Center Hole for Pipette Access (Through-hole)
            translate([0,0,-5]) cylinder(h=20, d1=6, d2=16);
            // Underside recess to avoid crushing Top Plate features
            translate([0,0,-5]) difference() {
                cylinder(h=3 + 4 + 1.4, d=neck_id-4); // Increased clear depth
                cylinder(h=10, d=20); // Only press on center ring
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

        // Connectivity (Back Wall)
        // DIN 5 MIDI (~16mm hole?) + Barrel Jack (8mm)
        #attach(BACK) {
            // DIN 5
            tag("remove") translate([-20, 0, pump_h/2]) rotate([90,0,0])
            cyl(h=wall*3, d=16, anchor=CENTER) ;

            // Barrel Jack
            tag("remove") translate([20, 0, pump_h/2]) rotate([90,0,0])
            cyl(h=wall*3, d=8, anchor=CENTER) ;
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
                 tag("remove") translate([x * (base_w/2 - 15), y * (base_l/2 - 15), 0])
                 tag("remove") cuboid([10.5, 10.5, 6], rounding=2, edges="Z", anchor=BOTTOM);
            }
        }

        // Connectivity (Back Wall)
        attach(BACK) {
            // DIN 5
            tag("remove") translate([-20, 0, reader_h/2]) rotate([90,0,0])
            cyl(h=wall*3, d=16, anchor=CENTER) ;
            // Barrel Jack
            tag("remove") translate([20, 0, reader_h/2]) rotate([90,0,0])
            cyl(h=wall*3, d=8, anchor=CENTER) ;
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
    lid_thick = 25; // Increased thickness for horizontal ports
    ceiling_thick = 10; // Thickness of the top solid section for channels

    color("Gainsboro")
    union() {
        // 1. Shell with Cuts
        diff("remove")
        cuboid([base_w+2*wall, base_l+2*wall, lid_thick], rounding=wall, edges="Z", anchor=TOP) {

            // Internal Bucket (Now starts lower to leave ceiling room)
            tag("remove") position(TOP) down(ceiling_thick)
            cuboid([base_w-2*wall, base_l-2*wall, lid_thick - ceiling_thick + wall], anchor=TOP);

            // Pogo Pin Holes
            tag("remove")
            position(BOTTOM) down(lid_thick/2)
            linear_extrude(lid_thick*3)PogoPinHoles();

            // Neck Transition & Thread (On Top)
            attach(TOP, overlap=5) // Embed into plate
            {
                cyl(h=10, d1=base_w-10, d2=neck_od, anchor=BOTTOM)
                attach(TOP)
                threaded_rod(d=neck_od, l=neck_h, pitch=20, anchor=BOTTOM);

                // Neck Bore (Hexagonal Socket)
                // Starts at TOP (Lid Surface) and goes UP to clear the neck, preserving the shelf below.
                // Replaces cyl(d=neck_id) with hex prism(d=hex_diam + clearance)
                tag("remove")
                position(TOP)
                cyl(h=neck_h+20, d=hex_diam + 1.0, $fn=6, anchor=BOTTOM); // +1mm clearance
            }

            // Internal Fluid Routing Channels
            // Connects Side Ports (Left) to Top Ports (Center Manifold)
            tag("remove") {
                 cd = 4; // Channel diameter
                 port_z = -ceiling_thick/2; // Z height of horizontal channels (mid-ceiling)
                 side_x = -(base_w/2 + wall + 2); // Start slightly outside Left face

                 // Waypoints for jogs (Parametric)
                 // Jog happens near the wall to start the cross-over
                 jog_start_x = side_x + 9; // ~ -50
                 jog_end_x = jog_start_x + 5; // ~ -45
                 jog_y_offset = 6; // Shift 6mm closer to center (from +/-10 to +/-4)

                 // Target coordinates on Top Surface (R=20)
                 t1_x = port_radius * cos(angle_fluid_out_top); // ~ -17.3
                 t1_y = port_radius * sin(angle_fluid_out_top); // ~ -10

                 t2_x = port_radius * cos(angle_fluid_in_bot);  // ~ 17.3
                 t2_y = port_radius * sin(angle_fluid_in_bot);  // ~ -10

                 t3_x = port_radius * cos(angle_fluid_in_top);  // ~ 17.3
                 t3_y = port_radius * sin(angle_fluid_in_top);  // ~ 10

                 t4_x = port_radius * cos(angle_fluid_out_bot); // ~ -17.3
                 t4_y = port_radius * sin(angle_fluid_out_bot); // ~ 10

                 // Path 1: Side Y=-30 -> Out Top (t1)
                 // Short path, no conflicts
                 hull() {
                     translate([side_x, -30, port_z]) sphere(d=cd);
                     translate([t1_x, -30, port_z]) sphere(d=cd);
                 }
                 hull() {
                     translate([t1_x, -30, port_z]) sphere(d=cd);
                     translate([t1_x, t1_y, port_z]) sphere(d=cd);
                 }
                 hull() {
                     translate([t1_x, t1_y, port_z]) sphere(d=cd);
                     translate([t1_x, t1_y, 0.1]) cylinder(h=0.1, d=cd); // Up to surface
                 }
                 // Side Port Entry (Counterbore)
                 translate([side_x, -30, port_z]) rotate([0,90,0]) cylinder(h=10, d=8, anchor=BOTTOM);


                 // Path 2: Side Y=-10 -> In Bot (t2)
                 // Crosses center. Jogs to Y=-4 to avoid intersecting Path 1 vertical shaft at Y=-10
                 hull() {
                     translate([side_x, -10, port_z]) sphere(d=cd);
                     translate([jog_start_x, -10, port_z]) sphere(d=cd);
                 }
                 hull() {
                     translate([jog_start_x, -10, port_z]) sphere(d=cd);
                     translate([jog_end_x, -10 + jog_y_offset, port_z]) sphere(d=cd); // Jog In (to -4)
                 }
                 hull() {
                     translate([jog_end_x, -10 + jog_y_offset, port_z]) sphere(d=cd);
                     translate([t2_x, -10 + jog_y_offset, port_z]) sphere(d=cd); // Run across
                 }
                 hull() {
                     translate([t2_x, -10 + jog_y_offset, port_z]) sphere(d=cd);
                     translate([t2_x, t2_y, port_z]) sphere(d=cd); // Jog Back
                 }
                 hull() {
                     translate([t2_x, t2_y, port_z]) sphere(d=cd);
                     translate([t2_x, t2_y, 0.1]) cylinder(h=0.1, d=cd);
                 }
                 translate([side_x, -10, port_z]) rotate([0,90,0]) cylinder(h=10, d=8, anchor=BOTTOM);


                 // Path 3: Side Y=10 -> In Top (t3)
                 // Crosses center. Jogs to Y=4 to avoid intersecting Path 4 vertical shaft at Y=10
                 hull() {
                     translate([side_x, 10, port_z]) sphere(d=cd);
                     translate([jog_start_x, 10, port_z]) sphere(d=cd);
                 }
                 hull() {
                     translate([jog_start_x, 10, port_z]) sphere(d=cd);
                     translate([jog_end_x, 10 - jog_y_offset, port_z]) sphere(d=cd); // Jog In (to 4)
                 }
                 hull() {
                     translate([jog_end_x, 10 - jog_y_offset, port_z]) sphere(d=cd);
                     translate([t3_x, 10 - jog_y_offset, port_z]) sphere(d=cd); // Run across
                 }
                 hull() {
                     translate([t3_x, 10 - jog_y_offset, port_z]) sphere(d=cd);
                     translate([t3_x, t3_y, port_z]) sphere(d=cd); // Jog Back
                 }
                 hull() {
                     translate([t3_x, t3_y, port_z]) sphere(d=cd);
                     translate([t3_x, t3_y, 0.1]) cylinder(h=0.1, d=cd);
                 }
                 translate([side_x, 10, port_z]) rotate([0,90,0]) cylinder(h=10, d=8, anchor=BOTTOM);


                 // Path 4: Side Y=30 -> Out Bot (t4)
                 // Short path
                 hull() {
                     translate([side_x, 30, port_z]) sphere(d=cd);
                     translate([t4_x, 30, port_z]) sphere(d=cd);
                 }
                 hull() {
                     translate([t4_x, 30, port_z]) sphere(d=cd);
                     translate([t4_x, t4_y, port_z]) sphere(d=cd);
                 }
                 hull() {
                     translate([t4_x, t4_y, port_z]) sphere(d=cd);
                     translate([t4_x, t4_y, 0.1]) cylinder(h=0.1, d=cd);
                 }
                 translate([side_x, 30, port_z]) rotate([0,90,0]) cylinder(h=10, d=8, anchor=BOTTOM);
            }

            // Electrode Ports (Still pass-through?)
            // If internal routing is for fluids only, electrodes might need their own paths or pass-throughs.
            // Assuming electrodes still pass through from bottom for now.
             tag("remove")
             position(CENTER) {
                for(a = [angle_elec_cis, angle_elec_trans]) {
                    zrot(a) right(port_radius) cyl(h=lid_thick*3, d=4, center=true);
                }
             }
        }

        // 2. Additive Features (Preserved from Bucket Cut)

        // PCB Mounts (Underside)
        // Positioned relative to TOP anchor of main block.
        // attach(BOTTOM) puts it at [0,0,-lid_thick] facing down (Z+ -> World Z-).
        translate([0,0,-lid_thick]) rotate([180,0,0]) {
            translate([0,0,0]) {
                // 1mm Standoffs for PCB (80x60 centered)
                for(mx = [-pcb_w/2 + 5, pcb_w/2 - 5], my = [-pcb_l/2 + 5, pcb_l/2 - 5]) {
                    translate([mx, my, 0])
                    diff("remove") // Ensure local screw hole removal
                    cyl(h=1, d=6, anchor=TOP) {
                        tag("remove") cyl(h=5, d=2.5, anchor=BOTTOM); // Mounting screw hole
                    }
                }
            }
        }

        // Mounting Holes (Corners)
        // Positioned relative to parent origin (TOP surface).
        // We shift them down by lid_thick/2 so they sit within the lid volume (0 to -lid_thick)
        // instead of protruding out the top.
        for(x = [-1, 1], y = [-1, 1]) {
             translate([x * (base_w/2 - wall*1), y * (base_l/2 - wall*1), -lid_thick/2])
             diff("remove")
             union() {
                 cyl(h=lid_thick, d=wall*2.5, center=true);
                 tag("remove") cyl(h=lid_thick*3, d=3.5, center=true);
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
    translate([0,0,reader_h + Explode_Factor*0.4]) Housing_Lid_Reader();

    // Stack & Cap on top of Lid
    translate([0,0, reader_h + 15 + Explode_Factor]) { // 15 is lid thick
        Cartridge_Stack_3D();
         // Torque Cap (Inner + Outer)
        translate([0,0, neck_h - 15 + Explode_Factor*1.5]) {
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
                        translate([55+30, 20, pump_h + wall + reader_h - 5]) sphere(d=4); // Up to new port Z (-5 from top)
                    }
                    hull() {
                        translate([55+30, 20, pump_h + wall + reader_h - 5]) sphere(d=4);
                         translate([-55-10, 20, pump_h + wall + reader_h - 5]) sphere(d=4); // Over to Left
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
    projection(cut=false) Plate_1_Base_Hex();
} else if (Output_Mode == "Plate_2_Channel_DXF") {
    // Legacy name for Carrier Frame
    projection(cut=false) Carrier_Frame_Hex();
} else if (Output_Mode == "Plate_3_Top_DXF") {
    projection(cut=false) Plate_3_Top_Hex();
} else if (Output_Mode == "Gasket_Main_DXF") {
    // Export Top version by default or union? Usually individual.
    // Let's assume Top since it has more holes (conservative) or just Bottom.
    // User can change the call or we can add a mode.
    projection(cut=false) Gasket_Low_Dead_Volume(type="top");
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
    Bottom_Pusher_Plate(show_orings=false);
} else if (Output_Mode == "PCB_DXF") {
    projection(cut=false) PCB_2D();
}
