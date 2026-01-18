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

        // Feet / Sensor Enclosures (Bottom)
        // Replaces Female Interlocks with Threaded Sensor Feet
         attach(BOTTOM) {
            for(x = [-1, 1], y = [-1, 1]) {
                 translate([x * (base_w/2 - feet_inset), y * (base_l/2 - feet_inset), 0])
                 threaded_rod(d=12, l=2.8, pitch=1.5, anchor=TOP);
            }
        }

        // Connectivity (Back Wall)
        attach(BACK) {
            // DIN 5 MIDI (Panel Mount)
            tag("remove") translate([-20, 0, reader_h/2]) rotate([90,0,0])
            cyl(h=wall*3, d=16, anchor=CENTER) ;

            // USB-C (Panel Mount Cutout)
            tag("remove") translate([20, 0, reader_h/2]) rotate([90,0,0])
            cuboid([12, 6, wall*3], rounding=2, edges="Z", anchor=CENTER);
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

            // Cable Slot through the Lid
            tag("remove") Cable_Slot();

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
                threaded_rod(d=neck_od, l=neck_h, pitch=cap_thread_pitch, anchor=BOTTOM);

                // Neck Bore (Hexagonal Socket)
                // Starts at TOP (Lid Surface) and goes UP to clear the neck, preserving the shelf below.
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
                 // Side Port Entry (1/4" NPT)
                 translate([side_x, -30, port_z]) rotate([0,90,0])
                 threaded_rod(d=npt_thread_d, l=15, pitch=npt_thread_pitch, anchor=BOTTOM);


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
                 translate([side_x, -10, port_z]) rotate([0,90,0])
                 threaded_rod(d=npt_thread_d, l=15, pitch=npt_thread_pitch, anchor=BOTTOM);


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
                 translate([side_x, 10, port_z]) rotate([0,90,0])
                 threaded_rod(d=npt_thread_d, l=15, pitch=npt_thread_pitch, anchor=BOTTOM);


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
                 translate([side_x, 30, port_z]) rotate([0,90,0])
                 threaded_rod(d=npt_thread_d, l=15, pitch=npt_thread_pitch, anchor=BOTTOM);
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

             // Connectivity (Right Side) - Duplicated from Pump Case Back
             attach(RIGHT) {
                // DIN 5 MIDI (Panel Mount)
                tag("remove") translate([-25, 0, 0])
                cyl(h=wall*3, d=16, anchor=CENTER) ;

                // USB-C (Panel Mount Cutout)
                tag("remove") translate([0, 0, 0])
                cuboid([12, 6, wall*3], rounding=2, edges="Z", anchor=CENTER);

                // Barrel Jack (Panel Mount)
                tag("remove") translate([25, 0, 0])
                cyl(h=wall*3, d=12, anchor=CENTER) ;
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

// 2. Reader Module Assembly
module Reader_Module_Assembly() {
    Housing_Case_Reader();
    translate([0,0,reader_h + Explode_Factor*0.4]) Housing_Lid_Reader();

    // Stack & Cap on top of Lid
    // Stack sits directly on the TOP surface of the Lid (which is at z = reader_h)
    translate([0,0, reader_h + Explode_Factor]) {
        Cartridge_Stack_3D();
         // Torque Cap (Inner + Outer)
         // Cap screws onto the neck. Neck starts at Lid surface.
         // Cap rests on top of the Neck/Stack.
         // Position Cap so it "floats" above for Explode view or engaged for Assembly.
         // Neck Height = neck_h. Cap sits near the top.
        translate([0,0, neck_h - 10 + Explode_Factor*1.5]) { // Arbitrary engaging position
             Torque_Cap_Inner();
             translate([0,0,-2]) Torque_Cap_Outer();
        }
    }

    // PCB (Attached to Lid Underside)
    // Lid bottom is at z = reader_h
    // Standoffs 1mm down. PCB top at reader_h - 1.
    translate([0,0, reader_h]) {
        color("Green") linear_extrude(1.6)PCB_Solid_Hex();
    }
}
