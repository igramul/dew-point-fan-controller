$fn=50;

include <NopSCADlib/core.scad>
include <NopSCADlib/vitamins/iecs.scad>
include <NopSCADlib/vitamins/rockers.scad>
include <NopSCADlib/vitamins/leds.scad>
include <NopSCADlib/vitamins/pcbs.scad>
include <NopSCADlib/vitamins/displays.scad>
include <NopSCADlib/vitamins/toggles.scad>

include <socket_mount.scad>

length = 220;
width = 150;
height = 80;
wall = 2.5;
radius = 10;

tolerance = 0.5;

cover_height = 20;
cover_height_brim = 5;
cover_tolerance = tolerance;

panel_font = "FrutigerNextLT:style=Bold";

// define AC built-in plug with fuse holder
iec_in = IEC_fused_inlet;
iec_in_h = iec_body_h(iec_in) + 1;
iec_in_w = iec_body_w(iec_in);

iec_out = IEC_outlet;
iec_out_h = iec_body_h(iec_out) + 1;
iec_out_w = iec_body_w(iec_out);

rocker_main = small_rocker;
rocker_y_pos = rocker_height(rocker_main)/2+radius+20;
rocker_z_pos = rocker_width(rocker_main)/2+wall+20;


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


module TouchButtomSymbol(r, h,) {
    difference() {
        cylinder(r=r,     h=h, center=true);
        cylinder(r=r*3/5, h=h, center=true);
    }
    cylinder(r=r/5,     h=h, center=true);
}


module housing_base() {
    color("LightGrey") {
        difference() {
            linear_extrude(height = height)
                housing_GroudPlate();

            translate([0, 0, wall])
                linear_extrude(height = height)
                    offset(-wall) housing_GroudPlate();
            
            translate([iec_in_w+radius, 0, iec_in_h/2+wall])
                rotate([90, 180, 0]) iec_holes(iec_in, 70);

            translate([60+iec_out_w+radius, 0, iec_out_h/2+wall])
                rotate([90, 180, 0]) iec_holes(iec_out, 70);
            
            translate([0, rocker_y_pos, rocker_z_pos])
                rotate([0, -90, 0]) rocker_hole(rocker_main, 10);
            
            // remove side wall for ventilation slot
            translate([length, width/2, height/2])
                cube([10, width*0.8, height*0.6], center=true);
        }
        
        // socket mount für USB 5V power supply
        translate([80, width-wall, 0]) rotate([90, 0, -90]) SocketMount();
        
        // mounting holes for fan relay board
        translate([length/2+40, width/2-20, wall])
            rotate([0, 0, 0]) pcb_base(HW803_1WAY_RELAY, 10, 0);
        
        translate([length+3, width/2, height/2]) rotate([0, 0, 45]) 
            cube([2, 15, height*0.8], center=true);
        
    }
}


module housing() {
    housing_base();
    
    translate([iec_in_w+radius, 0, iec_in_h/2+wall])
        rotate([90, 180, 0]) iec_assembly(iec_in, wall);
    
    translate([60+iec_out_w+radius, 0, iec_out_h/2+wall])
        rotate([90, 180, 0]) iec_assembly(iec_out, wall);
    
    translate([0, rocker_y_pos, rocker_z_pos])
        rotate([0, -90, 0]) rocker(rocker_main, "red");
    
    translate([length/2+40, width/2-20, wall+10])
        rotate([0, 0, 0]) pcb(HW803_1WAY_RELAY);

    
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
            translate([0, 0, cover_height_brim - cover_height - 1]) 
                linear_extrude(height = cover_height - wall + 1) 
                    offset(-10) housing_GroudPlate();
            
            // LCD hole
            translate([length / 2, width / 2, cover_height_brim]) rotate([180, 0, 0]) 
                display_aperture(LCD2004A, clearance = tolerance);
            
            // reset button hole
            translate([length / 2 + 45, width / 2 + 40, cover_height_brim - wall])
                cylinder (d = 7.5, h=10);
            
            // WLAN LED bezel hole
            translate([length / 2 - 45, width / 2 + 40, cover_height_brim - wall])
                cylinder (d = 8.5, h=10);
            
            // 3 pos toggle hole
            translate([length / 2, width / 2 - 50, cover_height_brim - wall])
                toggle_hole(MS332F);
            
            // Auto LED bezel hole
            translate([length / 2 - 45, width / 2 - 50, cover_height_brim - wall])
                cylinder (d = 8.5, h=10);

            // Fan LED bezel hole
            translate([length / 2 + 45, width / 2 - 50, cover_height_brim - wall])
                cylinder (d = 8.5, h=10);
                                
            // Touch Button PCB hole
            translate([length / 2, width / 2 - 28, cover_height_brim - wall])
                cube([11.5, 16, 2.5], center=true);
                
            translate([length / 2, width / 2 -26, cover_height_brim])
                TouchButtomSymbol(r=5, h=0.8);

            translate([length / 2 - 0.61, width / 2 - 42.5, cover_height_brim - 0.4])
                linear_extrude(0.5) text("ON —", size=6, halign = "right", font = panel_font);
            translate([length / 2 - 0.61, width / 2 - 52.5, cover_height_brim - 0.4])
                linear_extrude(0.5) text("— AUTO —", size=6, halign = "right", font = panel_font);
            translate([length / 2 - 0.61, width / 2 - 62.5, cover_height_brim - 0.4])
                linear_extrude(0.5) text("OFF —", size=6, halign = "right", font = panel_font);
                
            translate([length / 2 + 3.3, width / 2 - 52.5, cover_height_brim - 0.4])
                linear_extrude(0.5) text("— FAN —", size=6, font = panel_font);

            translate([length / 2 - 40, width / 2 + 37.5, cover_height_brim - 0.4])
                linear_extrude(0.5) text("— WLAN", size=6, font = panel_font);
            translate([length / 2 + 40, width / 2 + 37.5, cover_height_brim - 0.4])
                linear_extrude(0.5) text("RESET —", size=6, halign = "right", font = panel_font);

        }
        

        // LCD PBC mount
        translate([length / 2, width / 2, cover_height_brim - 2]) rotate([180, 0, 0]) 
            pcb_base(LCD2004APCB, display_thickness(LCD2004A)-2, 0);

        // Touch Button PCB mount
        difference() {
            translate([length / 2, width / 2 - 26, cover_height_brim - wall - 1])
                cube([15, 10, 4], center=true);
            // Touch Button PCB hole
            translate([length / 2, width / 2 - 28, cover_height_brim - wall])
                cube([11.5, 16, 2.5], center=true);
        }
        
        // dividing wall
        translate([length-40, wall+cover_tolerance, (wall+cover_tolerance) - height]) 
            cube([wall, width - 2*(wall+cover_tolerance), height + cover_height_brim - (wall+cover_tolerance)]);
        
    }
}

module housing_cover() {
    housing_cover_base();
    translate([length / 2, width / 2, cover_height_brim]) rotate([180, 0, 0]) display(LCD2004A);

    //reset button
    translate([length / 2 + 45, width / 2 + 40, cover_height_brim - wall])
        rotate([0, 0, 90]) toggle(AP5236, thickness = wall);

    // WLAN LED
    translate([length / 2 - 45, width / 2 + 40, cover_height_brim - wall])
        led(LED5mm, "blue");

    // 3 pos toggle
    translate([length / 2, width / 2 - 50, cover_height_brim - wall])
        toggle(MS332F, thickness = wall);

    // Auto LED
    translate([length / 2 - 45, width / 2 - 50, cover_height_brim - wall])
        led(LED5mm, "orange");

    // Fan LED
    translate([length / 2 + 45, width / 2 - 50, cover_height_brim - wall])
        led(LED5mm, "green");

    // Touch Button PCB
    translate([length / 2, width / 2 - 28, cover_height_brim - wall + 2.5/2])
        rotate([0, 180, -90]) pcb(TTP223);
        
    translate([length / 2 - 72, width / 2, cover_height_brim - wall - 6])
        rotate([180, 0, 90]) pcb(PERF60x40);    
}



if($preview) {
    difference() {
        union() {
    //housing();
    translate([0, 0, height]) housing_cover();
        }
        //translate([length-20, 0, 0]) cube([height, height, height]);
    }
} else {
    housing_base();
    //housing_cover_base();
}