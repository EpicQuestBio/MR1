# TODO List

- [x] **Fix Pogo Pin Path:** `Gasket_Main` (Gasket 1) is located between the Base Plate and the Channel Plate (where the Interposer sits). It currently lacks pogo pin holes, while Gasket 2 (above the Channel Plate) has them. This seems inverted. Need to swap `pogo=true` to Gasket 1 and verify if Gasket 2 needs them.
- [x] **Clean up Interposer Rotation:** The code in `Cartridge_Stack_3D` has verbose comments about flipping the interposer. Verify the rotation logic (`rotate([180, 0, 180])` vs `rotate([0, 180, 0])`) and clean up the code.
- [x] **Refine Fluid Routing in Lid:** `Housing_Lid_Reader` uses vertical pass-throughs for fluid ports, but the comment mentions "Internal Routing Channels" connecting side ports to the central manifold are needed. This requires proper CSG modeling.
- [x] **Pump Mounting Configuration:** `Housing_Pump_Case` has hardcoded mountings for "Diitao" pumps. Make this more modular or configurable.
- [ ] **Verify Sealed Top Mode:** Check if `Sealed_Top_Mode` correctly seals the top pipette access while maintaining fluid channels.
- [ ] **Standardize Pogo Pin Holes:** Pogo pin holes are hardcoded. Consider making them parametric or moving to a configuration section.
