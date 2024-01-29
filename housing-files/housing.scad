include <NopSCADlib/core.scad>
include <NopSCADlib/vitamins/iecs.scad>

length = 220;
width = 150;
height = 80;
wall = 2.5;
radius = 10;

// define AC built-in plug with fuse holder
//iec = IEC_fused_inlet;
iec_in = IEC_320_C14_switched_fused_inlet;
iec_in_h = iec_body_h(iec_in) + 6;
iec_in_w = iec_body_w(iec_in);

iec_out = IEC_outlet;
iec_out_h = iec_body_h(iec_out) + 1;
iec_out_w = iec_body_w(iec_out);


module GroudPlateRoundCorners(a, b, r) {
    translate([0, r]) square([a,b-2*r]);
    translate([r, 0]) square([a-2*r,b]);
    translate([r, r]) circle(r);
    translate([a-r, r]) circle(r);
    translate([r, b-r]) circle(r);
    translate([a-r, b-r]) circle(r);
}

module housing_base() {
    color("LightGrey")
    difference() {
        linear_extrude(height = height)
            GroudPlateRoundCorners(length, width, radius);

        translate([0, 0, wall])
            linear_extrude(height = height)
                offset(-wall) GroudPlateRoundCorners(length, width, radius);
        
        translate([60+iec_in_w+radius, 0, iec_in_h/2+wall]) rotate([90, 180, 0]) iec_holes(iec_in, 70);

        translate([iec_out_w+radius, 0, iec_out_h/2+wall]) rotate([90, 180, 0]) iec_holes(iec_out, 70);
    }    
}

module housing() {
    housing_base();
    translate([60+iec_in_w+radius, 0, iec_in_h/2+wall]) rotate([90, 180, 0]) iec_assembly(iec_in, wall);
    translate([iec_out_w+radius, 0, iec_out_h/2+wall]) rotate([90, 180, 0]) iec_assembly(iec_out, wall);
}

if($preview)
    housing();
else
    housing_base();