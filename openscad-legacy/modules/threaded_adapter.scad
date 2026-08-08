include <../libraries/BOSL2/std.scad>
include <../libraries/BOSL2/threading.scad>

// Male Luer Lock to G1/8 (or 1/8") Thread Adapter
// Dimensions based on provided reference image
module Threaded_Luer_Adapter(render_threads=true) {
    overall_len = 20.2;
    bore_d = 2.0;

    thread_len = 6.0;
    thread_od = 9.4; // Image says 9.4mm G1/8 thread
    thread_pitch = 0.907; // ~28 TPI

    hex_w = 12.0; // flat to flat
    hex_len = 5.5; // overall_len - thread_len - collar_len

    collar_len = 8.7;
    collar_od = 11.0;
    collar_id = 8.0;

    luer_slip_base_d = 4.4;
    luer_slip_tip_d = 3.9;

    difference() {
        union() {
            // 1. Threaded section (Bottom)
            if (render_threads) {
                // Threaded rod centers on Z=0, so shift it up
                translate([0, 0, thread_len/2])
                    threaded_rod(d=thread_od, l=thread_len, pitch=thread_pitch, $fn=36);
            } else {
                cylinder(d=thread_od, h=thread_len, center=false, $fn=36);
            }

            // 2. Hex flange (Middle)
            translate([0, 0, thread_len])
                cylinder(d=hex_w/cos(30), h=hex_len, center=false, $fn=6);

            // 3. Top Section (Luer Lock Collar + inner cone)
            translate([0, 0, thread_len + hex_len]) {
                // Outer collar (hollow)
                difference() {
                    cylinder(d=collar_od, h=collar_len, center=false, $fn=36);
                    translate([0,0, -0.1])
                        cylinder(d=collar_id, h=collar_len + 0.2, center=false, $fn=36);
                }

                // Add some ridges to make the collar look knurled/grippy, as is typical for these fittings
                // or just keep it smooth as per the image

                // Inner Luer cone
                cylinder(d1=luer_slip_base_d, d2=luer_slip_tip_d, h=collar_len, center=false, $fn=36);

                // Inner lock threads (simplified as a single spiral or ring for visual)
                if (render_threads) {
                    translate([0, 0, 1])
                        tube(od=collar_id, id=collar_id-1, h=0.8, $fn=36);
                }
            }
        }

        // Central bore
        translate([0, 0, -0.1])
            cylinder(d=bore_d, h=overall_len + 0.2, center=false, $fn=24);
    }
}

// Render by default if file is run directly
Threaded_Luer_Adapter();
