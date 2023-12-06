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
let path_str = "2D_";
// let path_str = "3D_";

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

fetch("./resources/job-1-0.vtu")
    .then(response => response.text())
    .then(xmlData => {
        var parser = new DOMParser();
        var xmlDoc = parser.parseFromString(xmlData, "text/xml");

        const points = xmlDoc.getElementsByTagName("Points")[0]
        const points_info = points.getElementsByTagName("DataArray")[0]
        const dimension = parseInt(points_info.getAttribute("NumberOfComponents"))
        const pointsStr = points.textContent;
        const pointsStrArray = pointsStr.trim().split(/\s+/);
        const pointsFloatArray = pointsStrArray.map(function (item) {
            return parseFloat(item);
        });
        let nodes = []
        for (let i = 0; i < pointsFloatArray.length; i += dimension) {
            nodes.push(pointsFloatArray.slice(i, i + dimension));
        }

        const cells = xmlDoc.getElementsByTagName("Cells")[0]
        const cells_info = cells.getElementsByTagName("DataArray")
        let offsetsIntArray;
        if (cells_info[1].getAttribute("Name") === "offsets") {
            const offsetsStr = cells_info[1].textContent;
            const offsetsStrArray = offsetsStr.trim().split(/\s+/);
            offsetsIntArray = offsetsStrArray.map(function (item) {
                return parseInt(item);
            });
        }
        let typesIntArray;
        if (cells_info[2].getAttribute("Name") === "types") {
            const typesStr = cells_info[2].textContent;
            const typesStrArray = typesStr.trim().split(/\s+/);
            typesIntArray = typesStrArray.map(function (item) {
                return parseInt(item);
            });
        }
        let connectivityIntArray;
        let connectivities = [];
        if (cells_info[0].getAttribute("Name") === "connectivity") {
            const connectivityStr = cells_info[0].textContent;
            const connectivityStrArray = connectivityStr.trim().split(/\s+/);
            connectivityIntArray = connectivityStrArray.map(function (item) {
                return parseInt(item);
            });
            for (let i = 0; i < offsetsIntArray.length; i++) {
                if (i === 0) {
                    connectivities.push(connectivityIntArray.slice(0, offsetsIntArray[i]));
                } else {
                    connectivities.push(connectivityIntArray.slice(offsetsIntArray[i - 1], offsetsIntArray[i]));
                }
            }
        }

        const point_data = xmlDoc.getElementsByTagName("PointData")[0]
        const point_data_info = point_data.getElementsByTagName("DataArray")

        for (let output of point_data_info){
            console.log(output.getAttribute("Name"))
        }

        console.log(point_data_info)

        console.log(nodes)
        console.log(connectivities)
    });

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
