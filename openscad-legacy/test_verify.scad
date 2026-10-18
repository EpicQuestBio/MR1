Output_Mode = "Housing_Reader_Lid_STL";
// ==============================================================================
// MR1 NANOPORE READER - REV 12 (Modular Split)
// Features: Torque-Lock Cap + Round Stack + Bottom Integration + Internal Layout
// ==============================================================================

include <constants.scad>
include <modules/common.scad>
include <modules/cartridge.scad>
include <modules/housing_pump.scad>
include <modules/torque_cap.scad>
include <modules/housing_reader.scad>


// ==============================================================================
// MAIN RENDER LOGIC
// ==============================================================================

if (Output_Mode == "Assembly") {

    difference() {
        union() {
            // Bottom Unit: Pump Module
            Pump_Module_Assembly();

            // Top Unit: Reader Module
            // Sits on top of Pump Module (Height pump_h + pump_lid_thick)
            translate([0,0, pump_h + pump_lid_thick + Explode_Factor]) {
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
                        translate([55+30, 20, pump_h + pump_lid_thick + reader_h - 5]) sphere(d=4); // Up to new port Z (-5 from top)
                    }
                    hull() {
                        translate([55+30, 20, pump_h + pump_lid_thick + reader_h - 5]) sphere(d=4);
                         translate([-55-10, 20, pump_h + pump_lid_thick + reader_h - 5]) sphere(d=4); // Over to Left
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
            translate([0, 0, pump_h + reader_h + neck_h + Explode_Factor*3.5 + 30]) text("Torque-Lock Cap", halign="center");
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
} else if (Output_Mode == "Gasket_Mold_Top_STL") {
    Gasket_Mold_3D(type="top");
} else if (Output_Mode == "Gasket_Mold_Bottom_STL") {
    Gasket_Mold_3D(type="bottom");
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
