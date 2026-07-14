// ==============================================================================
// SENTINEL NANOPORE READER - REV 12 (Modular Split)
// Features: Torque-Lock Cap + Round Stack + Bottom Integration + Internal Layout
// ==============================================================================
include <libraries/BOSL2/std.scad>
include <libraries/BOSL2/threading.scad>

/* [Render Mode] */
// Select "Assembly" for 3D view, or a specific layer for export
Output_Mode = "Assembly"; // [Assembly, Plate_1_Base_DXF, Plate_2_Channel_DXF, Plate_3_Top_DXF, Gasket_Main_DXF, Gasket_Top_DXF, Gasket_Bottom_DXF, Gasket_Mold_Top_STL, Gasket_Mold_Bottom_STL, Housing_Pump_Case_STL, Housing_Pump_Lid_STL, Housing_Reader_Case_STL, Housing_Reader_Lid_STL, Torque_Cap_Outer_STL, Torque_Cap_Inner_STL, Pressure_Puck_STL, Bottom_Pusher_Plate_STL, PCB_DXF, PCB_Amplifier_DXF, PCB_Nanopore_Carrier_DXF, PCB_Main_Reader_DXF]

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
pp_h = 4.0;           // Bottom Pusher Plate (TPU/Seal)
plate_thick = 4.0;    // Plate 1 (Base) & Plate 3 (Top), 4mm PP Sheet
gasket_thick = 1.5875; // Gaskets (1/16")
ptfe_thick = 1.6;     // PCB/PTFE assembly thickness
carrier_thick = ptfe_thick;// PCB + Carrier assembly
puck_h = 6;           // Pressure Puck height

/* [Compression & Sealing Physics] */
torque_limit = 0.5; // Torque limit of the cap in Nm
friction_k = 0.2;   // Friction coefficient (dry plastic threads)
E_silicone = 1.5;   // Young's Modulus for Silicone (~40A) in MPa
E_tpu = 25;         // Young's Modulus for TPU (~85A) in MPa

// Calculate Contact Area (A)
// Area of 60mm hex (corner-to-corner) minus central holes.
// Hex area: (3 * sqrt(3) / 2) * (hex_diam/2)^2
// Assuming hex_diam is corner-to-corner, side length a = hex_diam/2.
// Area = (3 * sqrt(3) / 2) * (30^2) = 2338.26 mm^2
hex_side = 60 / 2;
A_hex_gross = (3 * sqrt(3) / 2) * (hex_side * hex_side);
// Subtract area of 4 port holes (d=4) and central carrier (d=20)
A_ports = 4 * PI * (2 * 2);
A_center = PI * (10 * 10);
A_stack = A_hex_gross - A_ports - A_center; // Effective surface area in mm^2

// Calculate Axial Clamping Force (F)
// F = T / (k * d). thread diameter in meters is neck_od / 1000
F_clamp = torque_limit / (friction_k * (75 / 1000)); // Newtons

// Calculate Deflection (delta_h = F * h_0 / (E * A))
// F is in N, E is in MPa (N/mm^2), A is in mm^2. delta_h will be in mm.
delta_h_silicone = (F_clamp * gasket_thick) / (E_silicone * A_stack);
delta_h_tpu_bottom = (F_clamp * pp_h) / (E_tpu * A_stack);
delta_h_tpu_top = (F_clamp * puck_h) / (E_tpu * A_stack);

// Calculate Heights
// Uncompressed height
total_stack_height_uncompressed = pp_h + plate_thick + gasket_thick + ptfe_thick + gasket_thick + plate_thick + puck_h;
total_stack_height = total_stack_height_uncompressed;

// Compressed height (Gap G)
total_stack_height_compressed = total_stack_height_uncompressed - (2 * delta_h_silicone) - delta_h_tpu_bottom - delta_h_tpu_top;

// Output to console
echo(str("--- Compression & Sealing Physics ---"));
echo(str("Effective Area (A): ", A_stack, " mm^2"));
echo(str("Axial Clamping Force (F): ", F_clamp, " N"));
echo(str("Silicone Deflection (per layer): ", delta_h_silicone, " mm (", (delta_h_silicone/gasket_thick)*100, "%)"));
echo(str("Bottom TPU Deflection: ", delta_h_tpu_bottom, " mm"));
echo(str("Top TPU Deflection: ", delta_h_tpu_top, " mm"));
echo(str("Total Uncompressed Stack Height: ", total_stack_height_uncompressed, " mm"));
echo(str("Total Compressed Stack Height (Gap G): ", total_stack_height_compressed, " mm"));
echo(str("---------------------------------------"));

// Neck Height: Dynamic to fit stack
// Stack sits on Lid Surface. Neck surrounds it.
// Neck needs to be tall enough to contain the stack + thread engagement.
// We add clearance.
neck_clearance = 10;
neck_h = total_stack_height_uncompressed + neck_clearance;
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

/* [Nanopore Wafer / Mold Settings] */
Use_Nanopore_Wafer_Gasket = true; // Use the cast gasket with embedded nanopore wafer
Show_Mold = false;                // Show 2-part mold for visual reference
wafer_size = 4.0;                 // 4x4mm square wafer
wafer_thick = 0.5;                // 0.5mm thickness of the silicon wafer
wafer_recess = 0.5;               // 0.5mm sealing lip thickness over the front face (PCB side)
wafer_hole_size = 3.0;            // Square hole size in the amplifier board (for overlap & sealing)
plug_diameter = 3.0;              // Round plugs in the mold to protect the nanopore
primary_gasket_diam = 50.0;       // Primary gasket body diameter, sitting inside the clamping interface
PCB_Thickness = 0.8;              // Z-height (thickness) of the active PCB (matching pcb_thin)
protrusion_size = 6.0;            // Square size of the silicone protrusion around the wafer seat

/* [Internal Sealing & Potting] */
oring_id = 10;
oring_cs = 1.78;
Show_Potting = true;
Show_O_Rings = true;

// Port Locations (Radius from center)
port_radius = 20; // Expanded for Luer Lock (1/4-28 UNF) fittings
luer_thread_pitch = 0.907; // 1/4-28 UNF Pitch
luer_thread_d = 6.35;      // 1/4-28 UNF Major Diameter

npt_1_8_thread_pitch = 0.9407; // 27 TPI
npt_1_8_thread_d = 10.287; // 1/8" NPT Major Outer Diameter
npt_1_8_tap_d = 8.7; // Tap drill size

angle_fluid_in_bot = -30;
angle_fluid_in_top = 210;
angle_fluid_out_bot = 150;
angle_fluid_out_top = 30;

fluid_Port_d = 4;
pipette_access_d = npt_1_8_tap_d;

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
