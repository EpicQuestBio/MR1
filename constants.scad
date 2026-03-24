// ==============================================================================
// SENTINEL NANOPORE READER - REV 12 (Modular Split)
// Features: Torque-Lock Cap + Round Stack + Bottom Integration + Internal Layout
// ==============================================================================
include <libraries/BOSL2/std.scad>
include <libraries/BOSL2/threading.scad>

/* [Render Mode] */
// Select "Assembly" for 3D view, or a specific layer for export
Output_Mode = "Assembly"; // [Assembly, Plate_1_Base_DXF, Plate_2_Channel_DXF, Plate_3_Top_DXF, Gasket_Main_DXF, Gasket_Top_DXF, Gasket_Bottom_DXF, Housing_Pump_Case_STL, Housing_Pump_Lid_STL, Housing_Reader_Case_STL, Housing_Reader_Lid_STL, Torque_Cap_Outer_STL, Torque_Cap_Inner_STL, Pressure_Puck_STL, Bottom_Pusher_Plate_STL, PCB_DXF, PCB_Amplifier_DXF, PCB_Nanopore_Carrier_DXF, PCB_Main_Reader_DXF]

/* [View Settings] */
Explode_Factor = 100; // [0:1:100]
Cross_Section = false;

/* [Torque Mechanism Settings] */
// How "stiff" the torque fingers appear (visual only)
Torque_Stiffness = 1.2;
Torque_Teeth_Count = 24;
tooth_height = 1;
cap_thread_pitch = 8; // Robust thread pitch for 90mm cap (approx 3 turns)

/* [Sealed Top Option] */
Sealed_Top_Mode = false; // [true, false]

/* [Stack Dimensions & Modularity] */
// Define component thicknesses for dynamic calculation
pp_h = 3;           // Bottom Pusher Plate (TPU/Seal)
plate_thick = 4;    // Plate 1 (Base) & Plate 3 (Top)
gasket_thick = 0.8; // Gaskets
carrier_thick = 2.6;// PCB + Carrier assembly
puck_h = 6;         // Pressure Puck height

// Calculate Total Stack Height (Active Components)
// Pusher + Plate1 + Gasket + Carrier + Gasket + Plate3
total_stack_height = pp_h + plate_thick + gasket_thick + carrier_thick + gasket_thick + plate_thick;

// Neck Height: Dynamic to fit stack
// Stack sits on Lid Surface. Neck surrounds it.
// Neck needs to be tall enough to contain the stack + thread engagement.
// We add clearance.
neck_clearance = 10;
neck_h = total_stack_height + neck_clearance;
cap_h = neck_h + 5; // Tall enough to handle threads

cap_top_thick = 5;
cap_retention_h = 2;
cap_inner_h = cap_h - cap_top_thick - 5;

/* [Dimensions - Round Cartridge] */
plate_diam = 60;
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
opamp_h = 1.75;       // SOIC-8 Height
Show_Components = true;
carrier_diam = 20;    // Diameter of the inner round Nanopore Carrier

/* [Internal Sealing & Potting] */
oring_id = 10;
oring_cs = 1.78;
Show_Potting = true;
Show_O_Rings = true;

// Port Locations (Radius from center)
port_radius = 20; // Expanded for Luer Lock (1/4-28 UNF) fittings
luer_thread_pitch = 0.907; // 1/4-28 UNF Pitch
luer_thread_d = 6.35;      // 1/4-28 UNF Major Diameter

angle_fluid_in_bot = -30;
angle_fluid_in_top = 210;
angle_fluid_out_bot = 150;
angle_fluid_out_top = 30;

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
reader_h = 30;
// Pump Module (Bottom) Height
pump_h = 65;

neck_od = 75;
neck_id = 61;
wall = 5;
feet_inset = 12.5; // Offset from edge for feet (bumped out for visibility)

// Sealing & Lids
seal_cs = 1.78;      // O-ring cross section
seal_radius = 0.3;   // Knife edge radius
seal_lip_h = 2.5;    // Indexing lip height
pump_lid_thick = wall + 2; // Increased to 7mm for deeper foot dimples
reader_lid_thick = wall + 2; // Increased to 7mm for deeper foot dimples


// Internal Component Placeholders
pcb_w = 80; pcb_l = 60;
pump_w = 42; pump_l = 60;

/* [Pump Configuration] */
Pump_Type = "Diitao"; // [Diitao, Blank, Custom]
// Custom Pump Settings (if Pump_Type == "Custom")
pump_motor_d = 27.6;
pump_head_d = 31.7;
pump_mount_d = 28.0; // Diameter of mounting hole

/* [Global] */
$fn = 80;
fn_draft = 40;
fn_prod = 200;
g_fn = fn_draft;
epsilon = 0.01;
