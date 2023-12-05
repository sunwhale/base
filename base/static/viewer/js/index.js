import {FEMViewer, themes} from "./FEMViewer.js";

let magnification = 0;
let rot = false;
let mode = 0;
let axis = 1;
let zoom = 1;
let lines = true;

// let path_str = "2D_SINGLE_TRIANGLE";
// let path_str = "2D_SINGLE_SQUARE";
// let path_str = "2D_BEAM_PLANE_STRESS";
// let path_str = "3D_SPHERE_LIGHT_MODEL";
// let path_str = "3D_SPHERE_HEAVY_MODEL";
// let path_str = "2D_PLANE_STRESS";
// let path_str = "2D_PLATE";
// let path_str = "3D_DRAGON_LIGHT_MODEL";
// let path_str = "3D_DRAGON_HEAVY_MODEL";
// let path_str = "3D_BEAM_BRICKS";
// let path_str = "2D_";
let path_str = "3D_";

let queryString = window.location.search;
let show_menu = true;
let theme = "默认";
let theme_param = "默认";
if (queryString !== "") {
    queryString = queryString.split("?")[1];
    let parameters = new URLSearchParams(queryString);
    let function_param = parameters.get("mesh");
    let magnification_param = parameters.get("magnification");
    let rot_param = parameters.get("rot");
    let mode_param = parameters.get("mode");
    let axis_param = parameters.get("axis");
    let zoom_param = parameters.get("zoom");
    let lines_param = parameters.get("lines");
    theme_param = parameters.get("theme");
    if (theme_param) {
        theme = theme_param;
    }
    show_menu = parameters.get("menu");
    if (function_param) {
        path_str = function_param;
    }
    if (magnification_param) {
        magnification = parseFloat(magnification_param);
    }
    if (rot_param) {
        rot = true;
    }
    if (mode_param) {
        mode = parseFloat(mode_param);
    }
    if (axis_param) {
        axis = parseInt(axis_param);
    }
    if (zoom_param) {
        zoom = 1 + parseFloat(zoom_param);
    } else {
        zoom = 1.05;
    }
    if (lines_param) {
        lines = false;
    }
}

let path = `./resources/${path_str}.json`;
if (path_str.startsWith("https://")) {
    path = path_str;
}
console.log(path);

const container = document.getElementById("models-container");
container.style.background = "linear-gradient(to bottom, #263750, #8594aa)";

const O = new FEMViewer(container, magnification, rot, axis === 1, zoom);
O.theme = themes[theme] || {};
O.updateStylesheet();
O.updateColors();
O.updateMaterial();
O.draw_lines = lines;
await O.loadJSON(path);
O.step = mode;
await O.init();
if (!show_menu) {
    O.MenuClosed = false;
    O.updateMenuClosed();
}
console.log(O);
O.after_load();
