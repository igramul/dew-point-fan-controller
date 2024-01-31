$fn=50;

include <NopSCADlib/core.scad>
include <NopSCADlib/vitamins/iecs.scad>
include <NopSCADlib/vitamins/leds.scad>
include <NopSCADlib/vitamins/pcbs.scad>
include <NopSCADlib/vitamins/displays.scad>
include <NopSCADlib/vitamins/toggles.scad>

use <NopSCADlib/vitamins/pcb.scad>

length = 220;
width = 150;
height = 80;
wall = 2.5;
radius = 10;

tolerance = 0.5;

cover_height = 20;
cover_height_brim = 5;
cover_tolerance = tolerance;

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

module housing_GroudPlate() {
    GroudPlateRoundCorners(length, width, radius);
}



module housing_base() {
    color("LightGrey")
    difference() {
        linear_extrude(height = height)
            housing_GroudPlate();

        translate([0, 0, wall])
            linear_extrude(height = height)
                offset(-wall) housing_GroudPlate();
        
        translate([60+iec_in_w+radius, 0, iec_in_h/2+wall]) rotate([90, 180, 0]) iec_holes(iec_in, 70);

        translate([iec_out_w+radius, 0, iec_out_h/2+wall]) rotate([90, 180, 0]) iec_holes(iec_out, 70);
    }    
}


module housing() {
    housing_base();
    translate([60+iec_in_w+radius, 0, iec_in_h/2+wall]) rotate([90, 180, 0]) iec_assembly(iec_in, wall);
    translate([iec_out_w+radius, 0, iec_out_h/2+wall]) rotate([90, 180, 0]) iec_assembly(iec_out, wall);
}


module housing_cover_base() {
    color("Grey") {
        difference() {
            union() {
                linear_extrude(height = cover_height_brim) housing_GroudPlate();        
                translate([0, 0, cover_height_brim - cover_height])
                    linear_extrude(height = cover_height)
                        offset(-(wall + cover_tolerance)) housing_GroudPlate();
            }
            translate([0, 0, cover_height_brim - cover_height - 1]) linear_extrude(height = cover_height - wall + 1) offset(-10) housing_GroudPlate();
            translate([length / 2, width / 2, cover_height_brim]) rotate([180, 0, 0]) display_aperture(LCD2004A, clearance = tolerance);
            translate([30, width / 2, cover_height_brim - wall]) toggle_hole(MS332F);
            translate([45, width / 2, cover_height_brim - wall]) cylinder (r = led_hole_radius(LED5mm), h=10);
        }
        translate([length / 2, width / 2, cover_height_brim - 2]) rotate([180, 0, 0]) pcb_base(LCD2004APCB, display_thickness(LCD2004A)-2, 0);
    }
}

module housing_cover() {
    housing_cover_base();
    translate([length / 2, width / 2, cover_height_brim]) rotate([180, 0, 0]) display(LCD2004A);
    translate([30, width / 2, cover_height_brim - wall]) toggle(MS332F, thickness = wall);
    translate([45, width / 2, cover_height_brim - wall]) led(LED5mm, "green");
    pcb(RPI_Pico);
}



if($preview) {
    //housing();
    housing_cover();
} else {
    //housing_base();
    housing_cover_base();
}