import math

# ==============================================================================
# SENTINEL NANOPORE READER - Python Port Constants
# ==============================================================================

# [View Settings]
EXPLODE_FACTOR = 0

# [Torque Mechanism Settings]
TORQUE_STIFFNESS = 1.2
TORQUE_TEETH_COUNT = 24
TOOTH_HEIGHT = 1.0
CAP_THREAD_PITCH = 8.0

# [Sealed Top Option]
SEALED_TOP_MODE = False

# [Stack Dimensions & Modularity]
PP_H = 3.0           # Bottom Pusher Plate (TPU/Seal) - matches golden STL bounds
PLATE_THICK = 4.0    # Plate 1 (Base) & Plate 3 (Top), 4mm PP Sheet
GASKET_THICK = 1.5875 # Gaskets (1/16")
PTFE_THICK = 1.6     # PCB/PTFE assembly thickness
CARRIER_THICK = PTFE_THICK # PCB + Carrier assembly
PUCK_H = 6.0           # Pressure Puck height

# [Compression & Sealing Physics]
TORQUE_LIMIT = 0.5 # Torque limit of the cap in Nm
FRICTION_K = 0.2   # Friction coefficient (dry plastic threads)
E_SILICONE = 1.5   # Young's Modulus for Silicone (~40A) in MPa
E_TPU = 25.0       # Young's Modulus for TPU (~85A) in MPa

HEX_DIAM = 60.0
HEX_SIDE = HEX_DIAM / 2.0
A_HEX_GROSS = (3 * math.sqrt(3) / 2) * (HEX_SIDE * HEX_SIDE)
A_PORTS = 4 * math.pi * (2 * 2)
A_CENTER = math.pi * (10 * 10)
A_STACK = A_HEX_GROSS - A_PORTS - A_CENTER

F_CLAMP = TORQUE_LIMIT / (FRICTION_K * (75.0 / 1000.0))

DELTA_H_SILICONE = (F_CLAMP * GASKET_THICK) / (E_SILICONE * A_STACK)
DELTA_H_TPU_BOTTOM = (F_CLAMP * PP_H) / (E_TPU * A_STACK)
DELTA_H_TPU_TOP = (F_CLAMP * PUCK_H) / (E_TPU * A_STACK)

TOTAL_STACK_HEIGHT_UNCOMPRESSED = PP_H + PLATE_THICK + GASKET_THICK + PTFE_THICK + GASKET_THICK + PLATE_THICK + PUCK_H
TOTAL_STACK_HEIGHT = TOTAL_STACK_HEIGHT_UNCOMPRESSED

TOTAL_STACK_HEIGHT_COMPRESSED = TOTAL_STACK_HEIGHT_UNCOMPRESSED - (2 * DELTA_H_SILICONE) - DELTA_H_TPU_BOTTOM - DELTA_H_TPU_TOP

NECK_CLEARANCE = 10.0
NECK_H = TOTAL_STACK_HEIGHT_UNCOMPRESSED + NECK_CLEARANCE
CAP_H = NECK_H + 5.0

CAP_TOP_THICK = 5.0
CAP_RETENTION_H = 2.0
CAP_INNER_H = CAP_H - CAP_TOP_THICK - 5.0

# [Dimensions - Round Cartridge]
PLATE_DIAM = 60.0
SCREW_BCD = 50.0
SCREW_HOLE = 3.2
M3_INSERT_HOLE = 4.2

# [Dimensions - Hexagonal Cartridge]
HEX_WALL = 3.0
POGO_Y = -15.0
POGO_X_SPACING = 5.0

# [Active Cartridge Settings]
PCB_THICK = 1.6
PCB_THIN = 0.8
OPAMP_H = 1.75
SHOW_COMPONENTS = True
CARRIER_DIAM = 20.0

# [Nanopore Wafer / Mold Settings]
USE_NANOPORE_WAFER_GASKET = True
SHOW_MOLD = False
WAFER_SIZE = 4.0
WAFER_THICK = 0.5
WAFER_RECESS = 0.15
WAFER_ROTATION = 45.0
WAFER_HOLE_SIZE = 3.0
PCB_WAFER_HOLE_SIZE = 6.20  # Opened 45-deg square hole matching KiCad Edge.Cuts (6.20 x 6.20 mm diamond)
PLUG_DIAMETER = 2.0         # Central nanopore sensing aperture
PRIMARY_GASKET_DIAM = 60.0  # Full 60mm corner-to-corner hex matching PCB & DXF
PCB_THICKNESS = 0.8
PROTRUSION_SIZE = 6.0       # 6.0 x 6.0 mm silicone encapsulation protrusion
PROTRUSION_ROTATION = 45.0  # 45 degrees rotated matching PCB cutout

# [KiCad PCB Source of Truth Dimensions]
PCB_WIDTH = 55.0034   # Flat-to-flat width with finger grip notches
PCB_HEIGHT = 51.9616  # Vertical height (30 * sqrt(3))
HEX_CORNER_RADIUS = 30.0 # Outer corner radius (60mm hex diameter)
FINGER_GRIP_NOTCH_X = 25.0
FINGER_GRIP_NOTCH_R = 5.0
FLUID_CHANNEL_W = 1.4 # Microfluidic channel width (1.2 - 1.6 mm)
CHAMBER_DIAM = 4.5    # Central nanopore chamber diameter

# [Golden STL Envelope Dimensions]
INNER_CAP_OD = 81.4
INNER_CAP_H = 20.2
OUTER_CAP_OD = 95.0
OUTER_CAP_H = 30.2
READER_LID_SIZE = 100.0
READER_LID_TOTAL_H = 57.7
THREAD_DEPTH = 2.0
PIPETTE_HOLE_D = 25.0

# [Internal Sealing & Potting]
ORING_ID = 10.0
ORING_CS = 1.78
SHOW_POTTING = True
SHOW_O_RINGS = True

# Port Locations
PORT_RADIUS = 20.0
LUER_THREAD_PITCH = 0.907
LUER_THREAD_D = 6.35

NPT_1_8_THREAD_PITCH = 0.9407
NPT_1_8_THREAD_D = 10.287
NPT_1_8_TAP_D = 8.7

ANGLE_FLUID_IN_BOT = -30
ANGLE_FLUID_IN_TOP = 210
ANGLE_FLUID_OUT_BOT = 150
ANGLE_FLUID_OUT_TOP = 30

FLUID_PORT_D = 4.0
PIPETTE_ACCESS_D = NPT_1_8_TAP_D

ANGLE_ELEC_CIS = 90
ANGLE_ELEC_TRANS = 270

# [Interposer Dimensions]
I_WIDTH = 15.0
I_LENGTH = 15.0
I_THICKNESS = 1.0
CHIP_SIZE = 4.0
PAD_LENGTH = 3.0
NUM_PADS = 4
PAD_PITCH = 2.0
PAD_WIDTH = 1.0

# [Dimensions - Housing & Components]
BASE_W = 110.0
BASE_L = 110.0
READER_H = 30.0
PUMP_H = 65.0

NECK_OD = 75.0
NECK_ID = 61.0
WALL = 5.0
FEET_INSET = 12.5

SEAL_CS = 1.78
SEAL_RADIUS = 0.3
SEAL_LIP_H = 2.5
PUMP_LID_THICK = WALL + 2.0
READER_LID_THICK = WALL + 2.0

PCB_W = 80.0
PCB_L = 60.0
PUMP_W = 42.0
PUMP_L = 60.0

# [Pump Configuration]
PUMP_TYPE = "Diitao"
PUMP_MOTOR_D = 27.6
PUMP_HEAD_D = 31.7
PUMP_MOUNT_D = 28.0

EPSILON = 0.01

def get_mold_w():
    return HEX_DIAM + 20.0

def get_mold_h():
    return HEX_DIAM + 30.0

MOLD_T = 15.0
MOLD_W = get_mold_w()
MOLD_H = get_mold_h()
CAVITY_Z = MOLD_H / 2.0 - 10.0
BOLT_Y_OFFSET = MOLD_W / 2.0 - 6.0
BOLT_Z_OFFSET = MOLD_H / 2.0 - 6.0
RES_D = 18.0
RES_T = MOLD_T - 3.0
BOLT_D = 4.2
BOLT_HEAD_D = 7.5
BOLT_HEAD_DEPTH = 3.5


# [Printer Tolerances]
# Adjust these values based on the manufacturing method.
# For FDM printing, 0.2mm to 0.3mm is typical for moving parts/threads.
# For SLA/Resin printing, 0.05mm to 0.1mm is more typical.
PRINTER_TYPE = "FDM" # ["FDM", "Resin"]

if PRINTER_TYPE == "FDM":
    TOLERANCE = 0.2
else:
    TOLERANCE = 0.05

# [Routing Parameters]
TUBE_ID = 3.2 # 1/8" ID
TUBE_OD = 6.35 # 1/4" OD
MIN_BEND_RADIUS_TUBE = 10.0

WIRE_GAUGE = 0.64 # 22 AWG diameter approx 0.64mm
WIRE_OD = 1.6 # Wire with insulation approx
MIN_BEND_RADIUS_WIRE = 10.0

# Per-harness wire outer diameters with insulation (mm)
WIRE_USB_OD = 1.6       # 28 AWG shielded
WIRE_MOTOR_OD = 2.4     # 24 AWG shielded twisted pair
WIRE_POGO_OD = 1.2      # 30 AWG shielded
