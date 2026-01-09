// PCB 2D Projection (Updated for Hex Amplifier)
module PCB_2D() {
    difference() {
        circle(d=hex_diam, $fn=6); // Hexagonal shape

        // Central Hole for Nanopore Carrier
        circle(d=carrier_diam);

        // Cable Slot (2D projection)
        translate([0, -26]) square([12, 5], center=true);

        // Port Pass-throughs
        for(a = [angle_fluid_in_top, angle_fluid_out_top, angle_fluid_in_bot, angle_fluid_out_bot, angle_elec_cis, angle_elec_trans]) {
            rotate([0,0,a]) translate([port_radius, 0]) circle(d=6);
        }
    }

    // Protruding Tabs (Into the hole)
    // Union-ed back in for the profile
    intersection() {
        circle(d=carrier_diam);
        union() {
             for(a=[0, 180]) rotate([0,0,a]) translate([carrier_diam/2, 0])
                square([5, 4], center=true);
        }
    }
}

// 4. NANOPORE CARRIER (Round Inner PCB)
module Nanopore_Carrier() {
    color("ForestGreen")
    difference() {
        cylinder(h=pcb_thin, d=carrier_diam);

        // Chip Aperture
        translate([0,0,-1]) cylinder(h=10, d=1.5);

        // Tab Slots (Cutouts for Amplifier Tabs)
        // Assume tabs at +/- 90 (Left/Right relative to rotated view?) or 0/180
        // We align with Amplifier tabs.
        for(a=[0, 180]) rotate([0,0,a]) translate([carrier_diam/2, 0, 0]) cube([4, 6, 10], center=true);
    }
    // Chip
    color("Black") translate([0,0,pcb_thin]) cube([3,3,0.3], center=true);
}
// 2. CHANNEL GASKET (The Microfluidics)
// ==============================================================================
module Channel_Gasket_Production() {
    color("Red", 0.8)
    difference() {
        // Gasket Body
        cylinder(h=gasket_thick, d=hex_diam, $fn=6);

        // THE FLUID CHANNEL
        // Defines the flow path from In -> Chip -> Out
        hull() {
            translate([0, 15, -1]) cylinder(h=5, d=5); // Input Area
            translate([0, -15, -1]) cylinder(h=5, d=5); // Output Area
            translate([0, 0, -1]) cylinder(h=5, d=8);   // Chip Chamber
        }

        // Bolt Holes (Must align perfectly)
        for(r=[0:60:360]) rotate([0,0,r])
            translate([screw_bcd/2, 0, -1]) cylinder(h=5, d=screw_hole);
    }
}

// ==============================================================================
// 3. FR4 INTERPOSER (The Chip Carrier)
// ==============================================================================
module FR4_Interposer_Production() {
    color("ForestGreen")
    difference() {
        // Standard 0.8mm FR4 Disk
        cylinder(h=pcb_thin, d=hex_diam, $fn=6);

        // Chip Aperture (Drill Hit)
        translate([0,0,-1]) cylinder(h=10, d=1.5);

        // Fluid Ports (Drill Hits)
      // Pass-throughs
        rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);

        // Bolt Holes
        for(r=[0:60:360]) rotate([0,0,r])
            translate([screw_bcd/2, 0, -1]) cylinder(h=10, d=screw_hole);
    }

    // Visual: The Chip glued on top
    if(Output_Mode == "Assembly")
        color("Black") translate([0,0,pcb_thick]) cube([5,5,0.3], center=true);
}

// 2. THE RIGID ACTIVE PCB (Rev 20 - Hex Amplifier + Round Carrier)
module PCB_Rigid_Active() {
    // 0.8mm FR4 Substrate (Hexagonal)

    difference() {
        color("ForestGreen")
        cylinder(h=pcb_thin, d=hex_diam, $fn=6);

        // Central Hole for Carrier
        translate([0,0,-1]) cylinder(h=10, d=carrier_diam);

        // Cable Slot
        Cable_Slot();
    }

    // Protruding Tabs (Into the hole)
    // Modeled as intersection with the hole area, attached to main body
    color("ForestGreen")
    intersection() {
        cylinder(h=pcb_thin, d=carrier_diam);
        union() {
             for(a=[0, 180]) rotate([0,0,a]) translate([carrier_diam/2, 0, pcb_thin/2])
                cube([5, 4, pcb_thin], center=true);
        }
    }

    // --- ACTIVE COMPONENTS (Top Side) ---
    if(Show_Components) {
        // LMP7721 OpAmp
        translate([15, 5, pcb_thin]) {
            color("#333333") cube([5, 6, opamp_h]); // Body
        }

        // JST Connector (Surface Mount, Right Angle)
        // Near the Cable Slot (Y=-26)
        translate([0, -19, pcb_thin]) {
            color("White") cube([12, 6, 5], center=true); // Body
             color("Silver") translate([0, -3.5, -2]) cube([12, 2, 1], center=true); // Pads
        }
    }

    // --- ELECTRODES (Silver Ribbons) ---
    // On the Tabs
    color("Silver") {
        for(a=[0, 180]) rotate([0,0,a]) translate([carrier_diam/2 - 1, 0, pcb_thin])
             cube([3, 2, 0.2], center=true);
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

// L1: Base Plate (Interface) - Hexagonal Version
// 2D Projection for DXF
module Plate_1_Base_Hex() {
    projection(cut=false) Plate_1_Base_Hex_3D();
}

// L1: Base Plate (3D with Internal Channels)
module Plate_1_Base_Hex_3D() {
    difference() {
        linear_extrude(plate_thick) circle(d=hex_diam, $fn=6);

        // Cable Slot Pass-through
        Cable_Slot();

        // Pass-throughs (Top Fluid) - Simple Cylinders
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);

        // --- BOTTOM FLUID (TRANS LOOP) ---
        // 1. Inlet Port (-30) to Trans Loop Up-Via
        // Port Entry
        rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);

        // Channel: Port -> Up-Via (Left side of Trans Chamber)
        // Via A at Y=-10, X=-3
        hull() {
             rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0, plate_thick/2]) sphere(d=4);
             translate([-3, -10, plate_thick/2]) sphere(d=3);
        }
        // Vertical Up-Via A
        translate([-3, -10, 0]) cylinder(h=10, d=2);

        // 2. Trans Loop Down-Via -> Center
        // Vertical Down-Via B (Y=-10, X=3)
        translate([3, -10, 0]) cylinder(h=10, d=2);

        // Channel: Via B -> Center
        // Raise spheres so they cut a TRENCH (open top), not a TUNNEL.
        // Sphere Center Z should be at 'plate_thick' to cut depth = radius.
        // We use larger spheres or offset Z to control depth/width.

        hull() {
             // Via B is at Z=0..plate_thick.
             // Connect Via B to the Channel Start (Center)
             // Use a sphere at Z=plate_thick to ensure open connection
             translate([3, -10, plate_thick]) sphere(d=3); // Depth 1.5
             translate([0, 0, plate_thick]) sphere(d=3);   // Depth 1.5
        }

        // 3. "Sloped Roof" Channel: Center -> Outlet Port (150)
        // RISING FLOOR: Depth decreases from Center (1.5) to Outlet (0.5)
        // To achieve Depth 0.5 with Sphere R=1.5: Center Z = plate_thick + (1.5 - 0.5) = plate_thick + 1.0.

        // Outlet Port
        rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);

        hull() {
             // Center: Depth 1.5 (Z_floor = 2.5)
             translate([0, 0, plate_thick]) sphere(d=3);

             // Outlet: Depth 0.5 (Z_floor = 3.5)
             rotate([0,0,angle_fluid_out_bot])
             translate([port_radius, 0, plate_thick + 1.0]) sphere(d=3);
        }
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
    active_in = (type=="bottom") ? angle_fluid_in_bot : angle_fluid_in_top;
    active_out = (type=="bottom") ? angle_fluid_out_bot : angle_fluid_out_top;

    // Determine pass-through angles (the other pair)
    pass_angles = (type=="bottom")
        ? [angle_fluid_in_top, angle_fluid_out_top]
        : [angle_fluid_in_bot, angle_fluid_out_bot];

    difference() {
        circle(d=hex_diam, $fn=6);

        // Cable Slot
        Cable_Slot();

        // Pass-throughs
        for(a = pass_angles) {
            rotate([0,0,a]) translate([port_radius, 0]) circle(d=4);
        }

        // --- LOW DEAD VOLUME CHANNEL ---
        if (type == "bottom") {
             // Bottom: Split into Chip Hole and Trans Loop Hole
             // Hole 1: Under Chip (Central)
             circle(d=6);

             // Hole 2: Trans Loop (Over Trans Pads)
             // Isolates Trans fluid (Y=-10) from Chip fluid until routing happens in Plate 1
             hull() {
                 translate([-4, -10, 0]) circle(d=3);
                 translate([4, -10, 0]) circle(d=3);
             }
        } else {
            // Top: Large cutout for Amplifier Components + JST Connector
            // The gasket frames the PCB components.
            // Main Central Opening (Hex-ish or Large Circle)
            hull() {
                 circle(d=carrier_diam + 4); // Clear the carrier/pore area
                 translate([0, 10, 0]) circle(d=10); // Clear OpAmp area
                 translate([0, -18, 0]) circle(d=15); // Clear JST Connector area
            }

            // Connection from Inlet Port to Central Slot
            hull() {
                 rotate([0,0,active_in]) translate([port_radius, 0]) circle(d=4);
                 translate([5, 8, 0]) circle(d=4);
            }
            // Connection from Slot to Outlet Port
            hull() {
                 rotate([0,0,active_out]) translate([port_radius, 0]) circle(d=4);
                 translate([-5, 8, 0]) circle(d=4);
            }
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

        // Cable Slot (Clearance for connector body)
        Cable_Slot();

        // Sample Well / Pipette Access
        if (!Sealed_Top_Mode) {
             circle(d=6);
        }

        // LARGE COMPONENT CUTOUT (Frame Mode)
        // Cutout for Amplifier components and JST connector
        hull() {
             circle(d=carrier_diam + 2);
             translate([0, 10, 0]) circle(d=10); // OpAmp
             translate([0, -18, 0]) circle(d=14); // JST
        }

        // Vertical port holes.
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0]) circle(d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0]) circle(d=4);
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
        Bottom_Pusher_Plate(show_orings=true);

    // 1. Base Plate (Hex) - 4mm
    color("PowderBlue", 0.5) Plate_1_Base_Hex_3D();



    // 1.5. INNER O-RING (Bottom Seal)
    // if(Show_O_Rings)
    //      translate([0,0,stack_z + plate_thick_pp + 0.2+ //Explode_Factor*1/6]) O_Ring_Inner();

    // 2. Gasket 1 (Hex) - Bottom - 0.8mm
    up(plate_thick + Explode_Factor/6)
        color("Red") linear_extrude(gasket_thick) Gasket_Low_Dead_Volume(type="bottom");


    // 3. Nanopore Carrier + Amplifier Board
    up(plate_thick + gasket_thick + Explode_Factor*3/6) {
        // Round Nanopore Carrier (Center)
        Nanopore_Carrier();

        // Hexagonal Amplifier Board (Surrounding)
        PCB_Rigid_Active();
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
