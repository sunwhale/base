import {FEMViewer, themes} from "./FEMViewer.js";

let magnification = 0;
let rot = false;
let step = 0;
let axis = 0;
let zoom = 1;
let lines = true;
let url = "";

let queryString = window.location.search;
let show_menu = true;
let theme = "默认";
let theme_param = "默认";
if (queryString !== "") {
    queryString = queryString.split("?")[1];
    let parameters = new URLSearchParams(queryString);
    let magnification_param = parameters.get("magnification");
    let rot_param = parameters.get("rot");
    let step_param = parameters.get("step");
    let axis_param = parameters.get("axis");
    let zoom_param = parameters.get("zoom");
    let lines_param = parameters.get("lines");
    let url_param = parameters.get("url");
    if (url_param) {
        url = url_param;
    }
    if (theme_param) {
        theme = theme_param;
    }
    if (magnification_param) {
        magnification = parseFloat(magnification_param);
    }
    if (rot_param) {
        rot = true;
    }
    if (step_param) {
        step = parseInt(step_param);
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

const container = document.getElementById("models-container");
container.style.background = "linear-gradient(to bottom, #263750, #8594aa)";

const O = new FEMViewer(container, magnification, rot, axis === 1, zoom);
O.theme = themes[theme] || {};
O.updateStyleSheet();
O.updateColors();
O.updateMaterial();
O.draw_lines = lines;
O.step = step;
try {
    await O.loadXML(url);
} catch (error) {
    console.log(error)
}
try {
    await O.init();
} catch (error) {
    O.guiFolder.destroy();
    O.settingsFolder.destroy();
    console.log(error)
}
if (!show_menu) {
    O.MenuClosed = false;
    O.updateMenuClosed();
}
O.after_load();
