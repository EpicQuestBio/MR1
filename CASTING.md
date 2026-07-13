Casting your own PDMS (Polydimethylsiloxane) is an excellent engineering decision and strongly aligns with the highest-performing baselines in nanopore research, such as the Delrin Fluid Cell (DFC) architecture mentioned in your documentation.

By casting PDMS, you avoid the conductive fillers of EPDM, eliminate the carbon char of laser cutting, and gain a gasket that can form a highly conformal, reversible seal against your PTFE PCB.

However, because you are building a system designed to measure picoamperes or femtoamperes, your mechanical fabrication must meet electrical precision standards. In this domain, a physical leak is an electrical leak. Here are the critical engineering guidelines you must follow when casting PDMS for an ultra-low-noise flow cell:

1. Mold Surface Finish (The Micro-Capillary Problem)
PDMS has a near-perfect sub-micron replication fidelity. It will mirror the exact surface texture of whatever you cast it in.

The Trap: If you 3D print your mold using standard FDM (filament) or unpolished SLA (resin), the cured PDMS gasket will inherit those microscopic layer lines. When compressed against your flat PTFE PCB, these micro-ridges act as capillary channels. Saline buffer will wick into these channels, creating a conductive path that ruins your baseline noise or causes a short circuit between the fluid and your guard traces.
The Solution: Your mold must be optically smooth. Use CNC-milled polished aluminum, cast acrylic, or glass as the base of your mold. If you must use a 3D-printed resin mold, it must be sanded down to high grit (2000+) and ideally clear-coated or polished before casting.
2. Vacuum Degassing (Preventing Capacitive Voids)
When you mix the two-part PDMS (like the industry-standard Dow Sylgard 184), you will introduce thousands of micro-bubbles.

The Trap: If a microscopic air bubble cures on the sealing edge of your gasket, it will collapse under compression and cause a leak. Worse, if bubbles are suspended in the bulk of the PDMS near the active pore, they act as tiny dielectric voids. As mechanical vibrations hit the flow cell, these bubbles compress and expand, changing the localized capacitance. This translates into microphonic noise spikes on your amplifier.
The Solution: You must use a vacuum chamber to degas the mixed PDMS before pouring it into the mold, or degas it while it is resting in the mold (before baking). Pull a vacuum until the foam rises and collapses, ensuring the liquid is perfectly clear.
3. Tuning the Durometer (Stiffness)
Standard Sylgard 184 is mixed at a 10:1 ratio (Base to Curing Agent).

The Optimization: If your fluidic channels are very narrow, a 10:1 PDMS gasket might be too soft; when you clamp the polypropylene backer plate down, the PDMS might bulge inward and occlude your microfluidic channel.
You can tune the stiffness by altering the ratio. A 5:1 mix ratio will yield a significantly harder, less compliant elastomer that holds its geometric shape better under clamping pressure, which is often preferable for precision flow cells.
4. Thermal Curing and Outgassing
While PDMS will cure at room temperature in about 48 hours, thermal curing is highly recommended for sensitive biological applications.

Baking the mold in an oven at 60°C to 80°C for 2–4 hours not only speeds up the manufacturing cycle but also helps drive off unreacted low-molecular-weight siloxanes. If left in the matrix, these unreacted monomers can slowly leach into your buffer and potentially destabilize lipid bilayers or interact with biological pores.
By using degassed, optically-smooth cast PDMS, you provide your high-impedance amplifier with the perfect, highly resistive dielectric barrier it needs to resolve those delicate femtoampere translocation events.
