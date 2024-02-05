socket_width = 50;
socket_height = 25;

module SocketHole() {
    w = socket_width;
    h = socket_height;

    linear_extrude(height = 5)
    offset(0.5) polygon([[0,0], [w,0], [w,h], [0,h]]);
    translate([0, 0, 5])

    linear_extrude(height = 4-0.5)
    offset(0.25) polygon([[2.5+5, 0.5], [w-2.5-5, 0.5], [w-2.5, 0.5+5], [w-2.5, h-0.5-5], [w-2.5-5, h-0.5], [2.5+5, h-0.5], [2.5, h-0.5-5], [2.5, 0.5+5]]);

    translate([-5, -4, 9-0.5]) cube([socket_width+10, socket_height+8, 40]);
}


module SocketMount() {
    difference() {
        cube([60, 38, 15]);
        translate([5, 9, 0]) SocketHole();
    }
}

//SocketMount();
