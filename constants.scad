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
Explode_Factor = 1; // [0:1:100]
Cross_Section = true;

/* [Torque Mechanism Settings] */
// How "stiff" the torque fingers appear (visual only)
Torque_Stiffness = 1.2;
Torque_Teeth_Count = 24;
tooth_height = 40;

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
pcb_thick = 1.6;      // THICK, standard RIGID FR4
pcb_thin = 0.8;      // THIN RIGID FR4
carrier_thick = 2.6;  // Reduced height for thin PCB + components
opamp_h = 1.75;       // SOIC-8 Height
Show_Components = true;
carrier_diam = 20;    // Diameter of the inner round Nanopore Carrier

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
