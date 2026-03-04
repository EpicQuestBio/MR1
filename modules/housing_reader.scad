// ==============================================================================
// MODULE: READER MODULE (Top Unit)
// ==============================================================================
module Housing_Case_Reader() {
    color("WhiteSmoke")
    diff("remove")
    cuboid([base_w+2*wall, base_l+2*wall, wall], rounding=wall, edges="Z", anchor=BOTTOM) {

        // Feet / Sensor Enclosures (Bottom)
        // Female Interlocks (Holes) matching Pump Lid Dimples
         tag("add") {
            for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 - feet_inset), y * (base_l/2 - feet_inset), 0])
                 // Truncated sphere pointing down (3.5mm depth)
                 // Added +0.1 to height and Z-offset to prevent boolean artifacts when joining
                 down(0) intersection() {
                     sphere(d=13);
                     translate([0, 0, -3.5/2 + 0.1/2]) cube([15, 15, 3.5 + 0.1], center=true);
                 }
            }
        }

         // Lid Mounting Holes (In Wall Corners)
         // Wall center is base_w/2.
         // With thicker wall, we put holes in the corners.
         tag("remove") {
             for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2), y * (base_l/2), 0])
                 cylinder(h=wall*3, d=3.2, center=true);
             }
        }

        // Knife Edge (Seal)
        // Attached to Top Surface
        attach(TOP) {
            // Seal path centered inside the screws
            // Screws at +/- (base_w/2) (Radius 55)
            // Wall Inner Edge at +/- (base_w/2 - 5) (Radius 50)
            // Seal at +/- (base_w/2 - 4) (Radius 51) -> Size [base_w - 8, base_l - 8]
            path_rect = rect([base_w - 8, base_l - 8], rounding=3);
            path_sweep(circle(r=seal_radius), path_rect, closed=true);
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

            // Cable Slot through the Lid
            tag("remove") Cable_Slot();

            // Internal Bucket (Now starts lower to leave ceiling room)
            tag("remove") position(TOP) down(ceiling_thick)
            cuboid([base_w-2*wall, base_l-2*wall, lid_thick - ceiling_thick + wall], rounding=2, edges="Z", anchor=TOP);

            // Pogo Pin Holes
            tag("remove")
            position(BOTTOM) down(lid_thick/2)
            linear_extrude(lid_thick*3)PogoPinHoles();

            // Neck Transition & Thread (On Top)
            attach(TOP, overlap=5) // Embed into plate
            {
                cyl(h=10, d1=base_w-10, d2=neck_od, anchor=BOTTOM)
                attach(TOP)
                threaded_rod(d=neck_od, l=neck_h, pitch=cap_thread_pitch, anchor=BOTTOM);

                // Neck Bore (Hexagonal Socket)
                // Starts at TOP (Lid Surface) and goes UP to clear the neck, preserving the shelf below.
                tag("remove")
                position(TOP)
                cyl(h=neck_h+20, d=hex_diam + 1.0, $fn=6, anchor=BOTTOM); // +1mm clearance
            }

            // Internal Fluid Routing Channels
            // Connects Side Ports (Split 2-Left / 2-Right) to Top Ports (Center Manifold)
            // Ports aligned to Y = +/- 20 to match Pump Case
            tag("remove") {
                 cd = 4; // Channel diameter
                 port_z = -ceiling_thick/2; // Z height of horizontal channels (mid-ceiling)
                 side_x_left = -(base_w/2 + wall + 2); // Start slightly outside Left face
                 side_x_right = (base_w/2 + wall + 2); // Start slightly outside Right face

                 // Target coordinates on Top Surface (R=20)
                 t1_x = port_radius * cos(angle_fluid_out_top); // ~ -17.3 (Left side)
                 t1_y = port_radius * sin(angle_fluid_out_top); // ~ -10

                 t2_x = port_radius * cos(angle_fluid_in_bot);  // ~ 17.3 (Right side)
                 t2_y = port_radius * sin(angle_fluid_in_bot);  // ~ -10

                 t3_x = port_radius * cos(angle_fluid_in_top);  // ~ 17.3 (Right side)
                 t3_y = port_radius * sin(angle_fluid_in_top);  // ~ 10

                 t4_x = port_radius * cos(angle_fluid_out_bot); // ~ -17.3 (Left side)
                 t4_y = port_radius * sin(angle_fluid_out_bot); // ~ 10


                 // Side Port Entry (1/4" NPT)
                 translate([side_x_left, -20, port_z]) rotate([0,90,0])
                 threaded_rod(d=npt_thread_d, l=30, pitch=npt_thread_pitch, anchor=BOTTOM);
                 translate([side_x_right, -20, port_z]) rotate([0,-90,0])
                 threaded_rod(d=npt_thread_d, l=30, pitch=npt_thread_pitch, anchor=BOTTOM);

                 // Path 1: Left Side Y=-20 -> Out Top (t1)
                 // Direct path, Left to Left
                 hull() {
                     translate([side_x_left, -20, port_z]) sphere(d=cd);
                     translate([t1_x, t1_y, port_z]) sphere(d=cd);
                 }
                 hull() {
                     translate([t1_x, t1_y, port_z]) sphere(d=cd);
                     translate([t1_x, t1_y, 0.1]) cylinder(h=0.1, d=cd); // Up to surface
                 }
                 // Path 2: Right Side Y=-20 -> In Bot (t2)
                 // Direct path, Right to Right
                 hull() {
                     translate([side_x_right, -20, port_z]) sphere(d=cd);
                     translate([t2_x, t2_y, port_z]) sphere(d=cd);
                 }
                 #hull() {
                     translate([t2_x, t2_y, port_z]) sphere(d=cd);
                     translate([t2_x, t2_y, 0.1]) cylinder(h=0.1, d=cd);
                 }



                 // Path 3: Right Side Y=20 -> In Top (t3)
                 // Direct path, Right to Right
                 hull() {
                     translate([side_x_right, 20, port_z]) sphere(d=cd);
                     translate([t3_x, t3_y, port_z]) sphere(d=cd);
                 }
                 hull() {
                     translate([t3_x, t3_y, port_z]) sphere(d=cd);
                     translate([t3_x, t3_y, 0.1]) cylinder(h=0.1, d=cd);
                 }
                 translate([side_x_right, 20, port_z]) rotate([0,-90,0])
                 threaded_rod(d=npt_thread_d, l=30, pitch=npt_thread_pitch, anchor=BOTTOM);


                 // Path 4: Left Side Y=20 -> Out Bot (t4)
                 // Direct path, Left to Left
                 hull() {
                     translate([side_x_left, 20, port_z]) sphere(d=cd);
                     translate([t4_x, t4_y, port_z]) sphere(d=cd);
                 }
                 hull() {
                     translate([t4_x, t4_y, port_z]) sphere(d=cd);
                     translate([t4_x, t4_y, 0.1]) cylinder(h=0.1, d=cd);
                 }
                 translate([side_x_left, 20, port_z]) rotate([0,90,0])
                 threaded_rod(d=npt_thread_d, l=30, pitch=npt_thread_pitch, anchor=BOTTOM);
               }
                 
               
                 // Port Pass-throughs
            tag("remove") {
                for(a = [angle_fluid_in_top, angle_fluid_out_top, angle_fluid_in_bot, angle_fluid_out_bot, angle_elec_cis, angle_elec_trans]) {
            
                    rotate([0,0,a]) translate([port_radius, 0]) cylinder(h=100, d=6, center=true);
                }
            }
            // Electrode Ports
             tag("remove")
             position(CENTER) {
                for(a = [angle_elec_cis, angle_elec_trans]) {
                    zrot(a) right(port_radius) cyl(h=lid_thick*3, d=4, center=true);
                }
             }

             // Connectivity (Back Side) - Moved to Positive Y Axis
             attach(BACK) {
                // DIN 5 MIDI (Panel Mount)
                tag("remove") translate([-25, 0, 0])
                cyl(h=wall*10, d=16, anchor=CENTER) ;

                // USB-C (Panel Mount Cutout)
                tag("remove") translate([0, 0, 0])
                cuboid([12, 6, wall*10], rounding=2, edges="Z", anchor=CENTER);

                // Barrel Jack (Panel Mount)
                tag("remove") translate([25, 0, 0])
                cyl(h=wall*10, d=12, anchor=CENTER) ;
             }

             // O-Ring Groove
             tag("remove") position(BOTTOM) {
                 path_rect = rect([base_w - 8, base_l - 8], rounding=3);
                 down(0.01) // Ensure cut
                 path_sweep(circle(d=seal_cs+0.2), path_rect, closed=true);
             }

             // Lid Mounting Holes (Through Holes + Counterbore)
             tag("remove") {
                 for(x = [-1, 1], y = [-1, 1]) {
                     translate([x * (base_w/2), y * (base_l/2), 0])
                     cylinder(h=lid_thick*3, d=3.5, center=true);

                     translate([x * (base_w/2), y * (base_l/2), 0])
                     position(TOP) down(5) cylinder(h=10, d=6, anchor=BOTTOM);
                 }
             }
        }

        // 2. Additive Features

        // PCB Mounts (Underside)
        // Positioned relative to TOP anchor of main block.
        // Attached to the underside of the ceiling (-ceiling_thick).
        // Added 0.1 overlap
        translate([0,0,-ceiling_thick+0.1]) {
            translate([0,0,0]) {
                // 1mm Standoffs for PCB (80x60 centered)
                for(mx = [-pcb_w/2 + 2, pcb_w/2 - 2], my = [-pcb_l/2 + 2, pcb_l/2 - 2]) {
                    translate([mx, my, 0])
                    diff("remove") // Ensure local screw hole removal
                    cyl(h=1, d=6, anchor=TOP) {
                        attach(BOTTOM) tag("remove") cyl(h=5, d=2.5, anchor=BOTTOM); // Mounting screw hole
                    }
                }
            }
        }

        // Indexing Lip (Bottom of Lid)
        // Fits inside Case Inner Bucket: base_w - 2*wall
        // Added 0.1 overlap
        translate([0,0,-lid_thick+0.1]) {
            difference() {
                 cuboid([base_w - 2*wall - 0.4, base_l - 2*wall - 0.4, seal_lip_h], rounding=2, edges="Z", anchor=TOP);
                 up(0.01) // ensure manifold
                 cuboid([base_w - 2*wall - 0.4 - 3, base_l - 2*wall - 0.4 - 3, seal_lip_h + 0.1], rounding=2, edges="Z", anchor=TOP);
            }
        }
    }
}

// 2. Reader Module Assembly
module Reader_Module_Assembly() {
    lid_thick = 25; // Matched to Housing_Lid_Reader

    Housing_Case_Reader();

    // Calculate Top Surface Z
    // Baseplate is height 'wall' (5mm).
    // Lid sits on top of Baseplate. Lid has thickness 25mm.
    // Lid anchor=TOP, so translation needs to bring its TOP to (wall + lid_thick).
    top_z = wall + lid_thick;

    translate([0,0, top_z + Explode_Factor*0.4]) Housing_Lid_Reader();

    // Stack & Cap on top of Lid
    // Stack sits directly on the TOP surface of the Lid
    translate([0,0, top_z + Explode_Factor]) {
        Cartridge_Stack_3D();
         // Torque Cap (Inner + Outer)
         // Cap screws onto the neck. Neck starts at Lid surface.
         // Cap rests on top of the Neck/Stack.
         // Position Cap so it "floats" above for Explode view or engaged for Assembly.
         // Neck Height = neck_h. Cap sits near the top.
        translate([0,0, neck_h - 10 + Explode_Factor*1.5]) { // Arbitrary engaging position
             Torque_Cap_Assembly();
        }
    }

    // PCB (Attached to Lid Underside)
    // Lid bottom is at z = top_z - lid_thick = wall.
    // Standoffs at -10 (ceiling) - 1 (standoff) = -11 relative to Lid Top.
    // PCB Top should be at top_z - 11.
    // PCB is 1.6 thick.
    // So PCB bottom at top_z - 11 - 1.6 = top_z - 12.6.
    translate([0,0, top_z - 12.6 + Explode_Factor*0.4]) {
        color("Green") linear_extrude(1.6)PCB_Main_Reader_2D();
    }
}

module PCB_Main_Reader_2D() {
    difference() {
        square([pcb_w, pcb_l], center=true);

        // Mounting Holes (Matches Standoffs in Lid)
        // Standoffs at: +/- (pcb_w/2 - 2), +/- (pcb_l/2 - 2)
        for(mx = [-pcb_w/2 + 2, pcb_w/2 - 2], my = [-pcb_l/2 + 2, pcb_l/2 - 2]) {
            translate([mx, my]) circle(d=3.2);
        }

        // Connectivity Cutouts (Back Edge)
        // To clear panel mount connectors
        // Cut 10mm deep from the back edge (Y=30 -> Y=20)
        translate([-25, 25]) square([18, 10.1], center=true); // DIN 5
        translate([0, 25]) square([14, 10.1], center=true);   // USB-C
        translate([25, 25]) square([14, 10.1], center=true);  // Barrel Jack
    }
}
