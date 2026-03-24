// ==============================================================================
// MODULES: CARTRIDGE LAYERS (Round + Bottom Ports)
// ==============================================================================

// PCB 2D Projection (Updated for Hex Amplifier)
module PCB_Amplifier_2D() {
   PCB_2D();
}

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
             for(a=[angle_fluid_in_top, angle_fluid_in_bot]) rotate([0,0,a]) translate([carrier_diam/2, 0])
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
        for(a=[angle_fluid_in_top, angle_fluid_in_bot]) rotate([0,0,a]) translate([carrier_diam/2, 0, 0]) cube([4, 6, 10], center=true);
    }
    // Chip
    color("Black") translate([0,0,pcb_thin]) cube([3,3,0.3], center=true);
}

module PCB_Nanopore_Carrier_2D() {
    projection(cut=false) Nanopore_Carrier();
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
            translate([0, 15, -1]) cylinder(h=gasket_thick+2, d=5); // Input Area
            translate([0, -15, -1]) cylinder(h=gasket_thick+2, d=5); // Output Area
            translate([0, 0, -1]) cylinder(h=gasket_thick+2, d=8);   // Chip Chamber
        }

        
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

        // Pass-throughs (To allow fluid flow through the stack)
        rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);
        rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);
        rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);
        rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);

        // Finger Grip Cutouts
        Finger_Grip_Cutout(height=20);
    }

    // Protruding Tabs (Into the hole)
    // Modeled as intersection with the hole area, attached to main body
    color("ForestGreen")
    intersection() {
        cylinder(h=pcb_thin, d=carrier_diam);
        union() {
             for(a=[angle_fluid_in_top, angle_fluid_in_bot]) rotate([0,0,a]) translate([carrier_diam/2, 0, pcb_thin/2])
                cube([5, 4, pcb_thin], center=true);
        }
    }

    // --- ACTIVE COMPONENTS (Top Side) ---
    if(Show_Components) {

        // --- NEW PADS (Top and Bottom) ---
        // Aligned with Liquid Ports closest to Amplifier (-30 and 210)
        // 2 Pads Top, 2 Pads Bottom

        pad_dist_inner = 12;
        pad_dist_outer = 17;

        // Top Pads (Gold + Silver Ribbon) - Aligned with Top In 
        rotate([0,0,angle_fluid_in_top]) {
            color("Gold") {
                translate([pad_dist_inner, 0, pcb_thin]) cube([2, 2, 0.1], center=true);
                translate([pad_dist_outer, 0, pcb_thin]) cube([2, 2, 0.1], center=true);
            }
            color("Silver") {
                translate([pad_dist_inner, 0, pcb_thin + 0.06]) cube([2, 0.8, 0.1], center=true);
                translate([pad_dist_outer, 0, pcb_thin + 0.06]) cube([2, 0.8, 0.1], center=true);
            }
        }

        // Bottom Pads (Gold + Silver Ribbon) - Aligned with Bot In 
        rotate([0,0,angle_fluid_in_bot]) {
            color("Gold") {
                translate([pad_dist_inner, 0, 0]) cube([2, 2, 0.1], center=true);
                translate([pad_dist_outer, 0, 0]) cube([2, 2, 0.1], center=true);
            }
            color("Silver") {
                translate([pad_dist_inner, 0, -0.06]) cube([2, 0.8, 0.1], center=true);
                translate([pad_dist_outer, 0, -0.06]) cube([2, 0.8, 0.1], center=true);
            }
        }

        // JST Connector (Surface Mount, Right Angle)
        // Moved Z to sit flush on TOP of PCB (pcb_thin + height/2)
        translate([0, -19, pcb_thin + 2.5]) {
            color("White") cube([12, 6, 5], center=true); // Body
            color("Silver") translate([0, -3.5, -2]) cube([12, 2, 1], center=true); // Pads
        }
        
        // --- COMPONENT PLACEMENT ---
        // Spaced out on the connector side (-Y)

        // LMP7721 OpAmp (Near Carrier)
        // Centered X/Y, Bottom at pcb_thin
        translate([0, -13, pcb_thin + opamp_h/2]) {
            color("#333333") cube([5, 6, opamp_h], center=true);
        }

        // V+ Rail Filtering (Left Side)
        translate([-10, -18, pcb_thin]) {
            color("Yellow") cube([3.2, 1.6, 1.5]);
            translate([0, 2, 0]) color("Brown") cube([1.6, 0.8, 0.6]);
        }

        // V- Rail Filtering (Right Side)
        translate([6, -18, pcb_thin]) {
            color("Yellow") cube([3.2, 1.6, 1.5]);
            translate([0, 2, 0]) color("Brown") cube([1.6, 0.8, 0.6]);
        }

        // Feedback Network
        translate([8, -24, pcb_thin]) color("Blue") cube([3.2, 1.6, 0.6]);
        
        // ESD Protection
        translate([-8, -24, pcb_thin]) color("Gold") cube([2,2,0.05]);
    }

    // --- ELECTRODES (Silver Ribbons) ---
    // On the Tabs
    color("Silver") {
        for(a=[[angle_fluid_in_top, angle_fluid_in_bot],[1,-1]]) rotate([0,0,a[0]]) translate([carrier_diam/2 - 1, 0, a[1]*pcb_thin])
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

        // Finger Grip Cutouts
        Finger_Grip_Cutout_2D();
    }
}


// L1: Base Plate (Interface) - Hexagonal Version
// 2D Projection for DXF
module Plate_1_Base_Hex() {
    projection(cut=false) Plate_1_Base_Hex_3D();
}

// L1: Base Plate (3D with Internal Channels) - BOSL2 Native
module Plate_1_Base_Hex_3D() {
    attachable(anchor=BOTTOM, d=hex_diam, l=plate_thick, $fn=6) {
        color("White", 0.4) // Acrylic
        diff("remove")
        cyl(h=plate_thick, d=hex_diam, $fn=6, anchor=BOTTOM) {

            // Cable Slot Pass-through
            tag("remove") Cable_Slot();

            // Pass-throughs - Simple Cylinders
            tag("remove") {
                rotate([0,0,angle_fluid_in_top]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);
                rotate([0,0,angle_fluid_out_top]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);
                rotate([0,0,angle_fluid_in_bot]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);
                rotate([0,0,angle_fluid_out_bot]) translate([port_radius, 0, -1]) cylinder(h=10, d=4);
            }
            
            // Finger Grip Cutouts
            tag("remove") Finger_Grip_Cutout(height=plate_thick*3);
        }
        children(); // Allow attachments
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
        // Cable Slot Pass-through
        tag("remove") Cable_Slot();
        // Pogo Pin Access
        PogoPinHoles();
    }
}

// G1:  Gasket with or without pogo pins
module Gasket_Main(pogo= false) {
    difference() {
        circle(d=plate_diam);
       // BoltHoles();
        // Cable Slot Pass-through
        tag("remove") Cable_Slot();
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

    // SQUISH COMPENSATION DIMENSIONS (50A Silicone)
    channel_w_laser = 1.2; // Desired 1.0mm
    port_d_laser = 2.0;    // Desired 1.5mm (Inlet) & Pass-throughs
    chamber_d = 6.5;       // Chip Size + 1.5mm
    fillet_r = 0.5;        // Anti-tear fillet radius

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
        tag("remove") Cable_Slot();


        // Pass-throughs (Inactive Ports)
        for(a = pass_angles) {
            rotate([0,0,a]) translate([port_radius, 0]) circle(d=port_d_laser);
        }

        // --- ACTIVE CHANNEL (Dogbone with Fillets) ---
        // 1. Center Chamber (d=6.5)
        // 2. Inlet/Outlet Paths (w=1.2)
        // 3. Port Bulbs (d=2.0)
        // 4. Fillets on internal corners (offset -0.5 then +0.5)

        offset(r=-fillet_r) offset(r=fillet_r) // Fillet convex corners of Void (Concave in Gasket)
        union() {
             // Center Chamber
             circle(d=chamber_d);

             // Inlet Path
             hull() {
                 circle(d=channel_w_laser); // At Center
                 rotate([0,0,active_in]) translate([port_radius, 0]) circle(d=channel_w_laser); // At Port
             }
             rotate([0,0,active_in]) translate([port_radius, 0]) circle(d=port_d_laser); // Port Bulb

             // Outlet Path
             hull() {
                 circle(d=channel_w_laser); // At Center
                 rotate([0,0,active_out]) translate([port_radius, 0]) circle(d=channel_w_laser); // At Port
             }
             rotate([0,0,active_out]) translate([port_radius, 0]) circle(d=port_d_laser); // Port Bulb
        }

        // Finger Grip Cutouts (Subtractive in 2D)
        Finger_Grip_Cutout_2D();
    }
}

// BOSL2 3D Gasket Wrapper
module Gasket_Low_Dead_Volume_3D(type="bottom") {
    // Wrapper using attachable directly
    // This separates the attachment logic from the geometry generation (diff)
    // and prevents children() from being processed multiple times by diff().
    attachable(anchor=BOTTOM, d=hex_diam, l=gasket_thick, $fn=6) {
        color("Red")
        diff("remove")
        cyl(h=gasket_thick, d=hex_diam, $fn=6, anchor=BOTTOM) {
            tag("remove")
            position(BOTTOM)
            linear_extrude(gasket_thick+0.2) // Extrude slightly more for cut
            difference() {
                square([hex_diam*2, hex_diam*2], center=true); // Inverse mask
                Gasket_Low_Dead_Volume(type=type); // The actual gasket shape
            }
        }
        children();
    }
}

// Wrapper for PCB Layer to support BOSL2 attachments
module PCB_Active_Stack_3D() {
    // Structural Spacer using attachable directly
    // This defines the attachment geometry (Hex Cylinder, h=carrier_thick)
    // but only renders the inner children (PCB components).
    // This prevents a solid block from obscuring the PCB.
    attachable(anchor=BOTTOM, d=hex_diam, l=carrier_thick, $fn=6) {
        PCB_Active_Stack_Parts();
        children();
    }
}

module PCB_Active_Stack_Parts() {
    // Carrier moves up in exploded view
    translate([0, 0, Explode_Factor/3]) Nanopore_Carrier();
    PCB_Rigid_Active();
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

// L3_Hex: Top Cap (Hexagonal) - 3D BOSL2 Native
module Plate_3_Top_Hex() {
    attachable(anchor=BOTTOM, d=hex_diam, l=plate_thick, $fn=6) {
        color("White", 0.4) // Acrylic
        diff("remove")
        cyl(h=plate_thick, d=hex_diam, $fn=6, anchor=BOTTOM) {

            tag("remove") union() {
                // Cable Slot (Clearance for connector body)
                Cable_Slot();

                // Sample Well / Pipette Access
                if (!Sealed_Top_Mode) {
                    cylinder(h=plate_thick*3, d=6, center=true);
                }

                // Fluid Ports (Top In/Out) - Ensure connectivity
                for(a=[angle_fluid_in_top, angle_fluid_out_top])
                    rotate([0,0,a]) translate([port_radius, 0]) cylinder(h=plate_thick*3, d=4, center=true);

                // COMPONENT CUTOUTS (Frame Mode)
                // Updated to avoid cutting the central seal area (d ~ 10mm)
                linear_extrude(plate_thick*3, center=true)
                union() {
                    // Top Wing (OpAmp 1)
                    translate([14, 4]) square([7, 8]); // OpAmp 1 with clearance

                    // Bottom Wing (JST, OpAmp 2, Filters, Cable Slot)
                    // JST/ESD/CableSlot Area (X[-7, 7], Y[-29, -15])
                    translate([-7, -29]) square([14, 14]);
                    // OpAmp 2 Area (X[4, 11], Y[-21, -13])
                    translate([4, -21]) square([7, 8]);
                    // Filters Area (X[-1, 14.2], Y[-28, -22])
                    translate([-1, -28]) square([15.2, 6]);
                }

                // Electrode Access
                rotate([0,0,angle_elec_cis]) translate([port_radius, 0]) cylinder(h=20, d=2, center=true);

                // Keying Pin
                translate([plate_diam/2 - 3, 0]) cylinder(h=20, d=2, center=true);

                // Finger Grip Cutouts
                Finger_Grip_Cutout(height=plate_thick*3);
            }
        }
        children(); // Allow attachments
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
    // Stack using BOSL2 Attachments for robust relative positioning

    // 0. Bottom Pusher Plate (Base)
    Bottom_Pusher_Plate(show_orings=true)

        // 1. Attach Plate 1 Base (Acrylic)
        attach(TOP)
        up(Explode_Factor/5) // Visual gap
        Plate_1_Base_Hex_3D()

            // 2. Attach Bottom Gasket
            attach(TOP)
            up(Explode_Factor/5)
            Gasket_Low_Dead_Volume_3D(type="bottom")

                // 3. Attach PCB + Carrier
                attach(TOP)
                up(Explode_Factor/5)
                PCB_Active_Stack_3D()

                    // 4. Attach Top Gasket
                    attach(TOP)
                    up(Explode_Factor/5)
                    Gasket_Low_Dead_Volume_3D(type="top")

                        // 5. Attach Top Plate
                        attach(TOP)
                        up(Explode_Factor/5)
                        Plate_3_Top_Hex()

                            // 6. Attach Puck
                            attach(TOP)
                            up(Explode_Factor/5)
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

    // Converted to BOSL2 cyl root
    // We wrap in attachable to separate the geometry color from the children attachments
    attachable(anchor=BOTTOM, d=hex_diam, l=pp_h, $fn=6) {
        color("LightSlateGray")
        diff("remove")
        cyl(h=pp_h, d=hex_diam, $fn=6, anchor=BOTTOM) { // Fits in HEX neck

            // Fluid Ports (4x)
        tag("remove")
        for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
            zrot(a) translate([port_radius, 0, 0]) {

                // 1. Through Hole
                cyl(h=pp_h + 1, d=port_d, center=true, $fn=g_fn);

                // 2. O-Ring Seats (Subtractive)
                position(TOP) torus(d_maj=or_maj, d_min=or_cs, anchor=CENTER, $fn=g_fn);
                position(BOTTOM) torus(d_maj=or_maj, d_min=or_cs, anchor=CENTER, $fn=g_fn);
            }
        }

            // Pogo Pin Clearance
            tag("remove") linear_extrude(10, center= true) PogoPinHoles();

            // Finger Grip Cutouts
            tag("remove") Finger_Grip_Cutout(height=pp_h*3);

            // 3. O-Rings (Additive, Attached)
            // These are separate objects, not subtracted. We attach them.
            if (show_orings) {
                for(a = [angle_fluid_in_bot, angle_fluid_in_top, angle_fluid_out_bot, angle_fluid_out_top]) {
                    attach(TOP)
                    zrot(a) translate([port_radius, 0, 0])
                    color("DeepSkyBlue") torus(d_maj=or_maj, d_min=or_cs, anchor=CENTER, $fn=g_fn);

                    attach(BOTTOM)
                    zrot(a) translate([port_radius, 0, 0])
                    color("DeepSkyBlue") torus(d_maj=or_maj, d_min=or_cs, anchor=CENTER, $fn=g_fn);
                }
            }
        }
        children(); // Allow attachments
    }
}

// ==============================================================================
// MODULE: PRESSURE PUCK (Pipette Access)
// ==============================================================================
module Finger_Grip_Cutout(height=10) {
     // Side notches for finger grip
     // Placed at X = +/- 30 (Hex Corners) to avoid internal components
     translate([30, 0, 0]) cylinder(h=height, d=10, center=true);
     translate([-30, 0, 0]) cylinder(h=height, d=10, center=true);
}

module Finger_Grip_Cutout_2D() {
     translate([30, 0]) circle(d=10);
     translate([-30, 0]) circle(d=10);
}

module Pressure_Puck_3D() {
    // Revised Puck with Recessed Cups (Subtractive)
    // Removed Additive Handle Tabs
    attachable(anchor=BOTTOM, size=[neck_id, neck_id, 6]) {
        color("#333333") {
            difference() {
                // Main Body
                cylinder(h=6, d=neck_id - 1);

                // Center Hole for Pipette Access (Through-hole)
                translate([0,0,-5]) cylinder(h=20, d1=6, d2=16);

                // Underside recess
                translate([0,0,-5]) difference() {
                    cylinder(h=3 + 4 + 1.4, d=neck_id-4);
                    cylinder(h=10, d=20);
                }

                // New Recessed Cups (Finger Grip)
                translate([0,0,3]) Finger_Grip_Cutout(height=20);
            }
        }
        children();
    }
}

// PCB Solid Hex (No Fluid Ports) for Lid Mounting
module PCB_Solid_Hex() {
    difference() {
        circle(d=hex_diam, $fn=6); // Hexagonal shape

        // Central Hole for Nanopore Carrier
        circle(d=carrier_diam);

        // Cable Slot (2D projection)
        translate([0, -26]) square([12, 5], center=true);
    }

    // Protruding Tabs (Into the hole)
    intersection() {
        circle(d=carrier_diam);
        union() {
             for(a=[0, 180]) rotate([0,0,a]) translate([carrier_diam/2, 0])
                square([5, 4], center=true);
        }
    }
}
