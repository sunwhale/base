import {FEMViewer, themes} from "./FEMViewer.js";

let magnif = 0;
let rot = false;
let mode = 0;
let axis = 6;
let zoom = 1;
let lines = true;

let path_str = "3D_FEMUR_LIGHT_MODEL";
let queryString = window.location.search;
let vis_param = 0;
let theme = "Default";
let theme_param = "Default";
if (queryString !== "") {
    queryString = queryString.split("?")[1];
    let parametros = new URLSearchParams(queryString);
    let funcion_param = parametros.get("mesh");
    let magnif_param = parametros.get("magnif");
    let rot_param = parametros.get("rot");
    let mode_param = parametros.get("mode");
    let axis_param = parametros.get("axis");
    let zoom_param = parametros.get("zoom");
    let lines_param = parametros.get("lines");
    theme_param = parametros.get("theme");
    if (theme_param) {
        theme = theme_param;
    }
    vis_param = parametros.get("menu");
    if (funcion_param) {
        path_str = funcion_param;
    }
    if (magnif_param) {
        magnif = parseFloat(magnif_param);
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

const O = new FEMViewer(container, magnif, rot, axis === 1, zoom);
O.theme = themes[theme] || {};
O.updateStylesheet();
O.updateColors();
O.updateMaterial();
O.draw_lines = lines;
await O.loadJSON(path);
O.step = mode;
await O.init();
if (vis_param === 1) {
    O.menuCerrado = false;
    O.updateMenuCerrado();
}

console.log(O);
O.after_load();
