include <NopSCADlib/core.scad>
include <NopSCADlib/vitamins/iecs.scad>

length = 220;
width = 150;
height = 100;
wall = 2.5;
radius = 10;

// define AC built-in plug with fuse holder
iec = IEC_fused_inlet;
iec_h = iec_body_h(iec) + 1;
iec_w = iec_body_w(iec) + 1;

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
        
        translate([iec_w+radius, 0, iec_h/2+wall]) rotate([90, 0, 0]) iec_holes(iec, 70);
    }    
}

module housing() {
    housing_base();
    translate([iec_w+radius, 0, iec_h/2+wall]) rotate([90, 0, 0]) iec_assembly(iec, wall);
}

if($preview)
    housing();
else
    housing_base();