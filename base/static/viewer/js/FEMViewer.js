import * as THREE from "./build/three.module.js";
import {ResourceTracker} from "./ResourceTracker.js";
import GUI from "./build/lil-gui.esm.js";
import {OrbitControls} from "./build/OrbitControls.js";
import * as BufferGeometryUtils from "./build/BufferGeometryUtils.js";
import {AxisGridHelper} from "./build/minigui.js";
import {Legend} from "./build/Legend.js";
import {CONFIG_DICT} from "./ConfigDicts.js";
import {Geometree, Quadrant3D} from "./Octree.js";
import {max, min, transpose} from "./math.js";
import {NotificationBar} from "./NotificationBar.js";
import {themes, types} from "./Constants.js"

function allowUpdate() {
    return new Promise((f) => {
        setTimeout(f, 0);
    });
}

let style = getComputedStyle(document.body);
let TEXT_COLOR = style.getPropertyValue("--gui-text-color").trim();
let BACKGROUND_COLOR = style.getPropertyValue("--gui-background-color").trim();
let TITLE_BACKGROUND_COLOR = style.getPropertyValue("--gui-title-background-color").trim();
let PLOT_GRID_COLOR = style.getPropertyValue("--plot-grid-color").trim();
let FONT_FAMILY = style.getPropertyValue("--font-family").trim();
let FOCUS_COLOR = style.getPropertyValue("--focus-color").trim();
let LINES_COLOR = style.getPropertyValue("--gui-text-color").trim();

let PLOT_STYLE = {
    margin: {t: 0},
    paper_bg_color: BACKGROUND_COLOR,
    plot_bg_color: BACKGROUND_COLOR,
    font: {
        color: TEXT_COLOR,
        family: FONT_FAMILY,
    },
    x_axis: {
        grid_color: PLOT_GRID_COLOR,
    },
    y_axis: {
        grid_color: PLOT_GRID_COLOR,
    },
};

const styleElement = document.createElement("style");
document.body.appendChild(styleElement);

class FEMViewer {
    constructor(container, magnification, rot, axis = false, iz = 1.05) {
        if (!magnification) {
            magnification = 0;
        }
        // FEM
        this.selectedNodes = [];

        this.container = container;
        let canvas = document.createElement("canvas");
        canvas.setAttribute("class", "box side-pane");
        canvas.setAttribute("willReadFrequently", "true");
        this.container.appendChild(canvas);
        this.canvas = canvas;

        this.loaderIcon = document.createElement("div");
        this.loaderIcon.setAttribute("class", "loaderIcon");
        this.container.appendChild(this.loaderIcon);

        this.theme = themes["默认"];
        this.element_views = new Set();
        this.refreshing = true;
        this.wireframe = false;
        this.corriendo = false;
        this.animationFrameID = undefined;
        this.min_search_radius = -Infinity;
        this.max_color_value = 0;
        this.min_color_value = 0;
        this.initial_zoom = iz;
        this.solution_as_displacement = false;
        this.axis = axis;
        this.max_color_value_slider = undefined;
        this.min_color_value_slider = undefined;
        this.resource_tracker = new ResourceTracker();
        this.raycaster = new THREE.Raycaster();
        this.notiBar = new NotificationBar(this.container);

        this.before_load = () => {
            this.loaderIcon.style.display = "";
        };
        this.after_load = () => {
            this.loaderIcon.style.display = "none";
        };
        this.rot = rot;
        this.resolution = 1;
        this.nodes = [];
        this.selectedNodesMesh = {};
        this.element_sets = {"Bottom": [1, 2, 3]}
        this.nvn = -1;
        this.dictionary = [];
        this.types = [];
        this.solutions = [];
        this.U = [];
        this.step = 0;
        this.size = 0.0;
        this.elements = [];
        this.info = "";
        this.ndim = -1;
        this.border_elements = [];
        this.config_dict = CONFIG_DICT["Elasticity"];
        this.dimensions = ["x", "y", "z"];

        // THREE JS
        this.renderer = new THREE.WebGLRenderer({
            canvas,
            antialias: true,
            alpha: true,
        });
        this.renderer.autoClear = false;

        this.delta = 0;
        this.interval = 1 / 24;
        this.clock = new THREE.Clock();
        this.bufferGeometries = [];
        this.bufferLines = [];
        this.model = new THREE.Object3D();

        this.invisibleModel = new THREE.Object3D();
        this.colors = false;
        this.animate = false;
        this.magnification = magnification;
        this.animate_mult = 1.0;
        this.side = 1.0;
        this.draw_lines = true;
        this.colormap = "彩虹图";
        this.show_model = true;
        this.octreeMesh = undefined;
        this.showOctree = false;

        this.MenuClosed = true;
        this.legend = new Legend(this.colormap);
        this.filename = "";

        this.gui = new GUI({title: "JSViewer 查看器", container: this.container});
        this.gui
            .add(this, "goBack")
            .name("返回");

        this.loaded = false;
        this.colorOptions = "nocolor";
        // this.clickMode = "无";

        this.settings();
        this.createListeners();
    }

    createListeners() {
        window.addEventListener("resize", this.render.bind(this));

        document.addEventListener("visibilitychange", (e) =>
            this.handleVisibilityChange(e)
        );

        this.notiBar.addButton("");
        this.notiBar.addButton("fa fa-refresh", this.reload.bind(this));
        this.playButton = this.notiBar.addButton(
            "fa fa-pause",
            this.toggleRefresh.bind(this)
        );
    }

    updateMenuClosed() {
        this.gui.show(this.MenuClosed);
        if (this.MenuClosed) {
            document
                .getElementById("notification-container")
                .setAttribute("style", "");
        } else {
            document
                .getElementById("notification-container")
                .setAttribute("style", "visibility: hidden");
        }
    }

    updateStyleSheet() {
        let style = "";
        const styleSheet = this.theme;
        for (let prop in styleSheet) {
            const value = styleSheet[prop];
            style += `\t${prop}: ${value};\n`;
        }
        if (style) {
            style = ":root {\n" + style + "}";
            styleElement.innerHTML = style;
        } else {
            styleElement.innerHTML = "";
        }
    }

    updateColors() {
        style = getComputedStyle(document.body);
        TEXT_COLOR = style.getPropertyValue("--gui-text-color").trim();
        BACKGROUND_COLOR = style
            .getPropertyValue("--gui-background-color")
            .trim();
        TITLE_BACKGROUND_COLOR = style
            .getPropertyValue("--gui-title-background-color")
            .trim();
        PLOT_GRID_COLOR = style.getPropertyValue("--plot-grid-color").trim();
        FONT_FAMILY = style.getPropertyValue("--font-family").trim();
        FOCUS_COLOR = style.getPropertyValue("--focus-color").trim();
        LINES_COLOR = style.getPropertyValue("--gui-text-color").trim();

        PLOT_STYLE = {
            margin: {t: 0},
            paper_bg_color: BACKGROUND_COLOR,
            plot_bg_color: BACKGROUND_COLOR,
            font: {
                color: TEXT_COLOR,
                family: FONT_FAMILY,
            },
            x_axis: {
                grid_color: PLOT_GRID_COLOR,
            },
            y_axis: {
                grid_color: PLOT_GRID_COLOR,
            },
        };
    }

    updateTheme() {
        this.updateStyleSheet();
        this.updateColors();
        this.updateMaterial();
        this.updateGeometry();
    }

    updateResolution() {
        for (const e of this.elements) {
            e.res = this.resolution;
            e.initGeometry();
            this.updateSpecificBufferGeometry(e.index);
        }
        this.updateSolution();
    }

    updateRefresh() {
        this.controls.enabled = this.refreshing;
        if (this.refreshing) {
            this.playButton.setAttribute(
                "class",
                "fa fa-pause notification-action"
            );
        } else {
            this.playButton.setAttribute(
                "class",
                "fa fa-play notification-action"
            );
        }
    }

    toggleRefresh() {
        this.refreshing = !this.refreshing;
        this.updateRefresh();
        if (this.refreshing) {
            this.animationFrameID = requestAnimationFrame(
                this.update.bind(this)
            );
        } else {
            cancelAnimationFrame(this.animationFrameID);
        }
        return this.refreshing;
    }

    createOctree() {
        this.notiBar.setMessage("创建八叉树...");
        let nnodes = this._nodes.map((x) => {
            return x["_xcenter"];
        });
        let nodes = transpose(nnodes);
        let center_x = (max(nodes[0]) + min(nodes[0])) / 2;
        let size_x = (max(nodes[0]) - min(nodes[0])) / 2;
        let center_y = (max(nodes[1]) + min(nodes[1])) / 2;
        let size_y = (max(nodes[1]) - min(nodes[1])) / 2;
        let center_z = (max(nodes[2]) + min(nodes[2])) / 2;
        let size_z = (max(nodes[2]) - min(nodes[2])) / 2;

        let FF = 1.01;
        let dimension = [size_x * FF, size_y * FF, size_z * FF];
        let bounding = new Quadrant3D([center_x, center_y, center_z], dimension);
        this.OctTree = new Geometree(bounding, 10);
        for (let i = 0; i < this._nodes.length; i++) {
            let p = {
                _xcenter: this._nodes[i]["_xcenter"].slice(),
                id: this._nodes[i]["id"],
            };
            this.OctTree.add_point(p);
            this.notiBar.sendMessage("八叉树创建完成");
        }
        const geo_list = this.OctTree.giveContours(this.norm);
        const geo = BufferGeometryUtils.mergeBufferGeometries(geo_list, true);
        this.octreeMesh = new THREE.LineSegments(geo, this.line_material);
    }

    async loadXML(xml_path) {
        this.filename = xml_path
        const response = await fetch(xml_path)
        if (response.ok) {
            const totalSize = response.headers.get('Content-Length');

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');

            const processData = async () => {
                const chunks = [];
                let receivedSize = 0;

                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;

                    chunks.push(value);
                    receivedSize += value.length;

                    const progress = (receivedSize / totalSize) * 100;
                    this.notiBar.setProgressBar("传输数据...", progress);
                }

                const buffer = new Uint8Array(receivedSize);
                let offset = 0;

                for (const chunk of chunks) {
                    buffer.set(chunk, offset);
                    offset += chunk.length;
                }

                const xmlData = decoder.decode(buffer);

                let parser = new DOMParser();
                let xmlDoc = parser.parseFromString(xmlData, "text/xml");

                this.config_dict = CONFIG_DICT["GENERAL"];

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
                let disp_dimension;
                let U;
                let fieldOutputs = {};
                const point_data = xmlDoc.getElementsByTagName("PointData")[0]
                const point_data_info = point_data.getElementsByTagName("DataArray")
                for (let output of point_data_info) {
                    if (output.getAttribute("Name") === "Displacement") {
                        this.config_dict = {
                            ...CONFIG_DICT["Displacement"],
                        };
                        disp_dimension = parseInt(output.getAttribute("NumberOfComponents"))
                        const dispStr = output.textContent;
                        const dispStrArray = dispStr.trim().split(/\s+/);
                        U = dispStrArray.map(function (item) {
                            return parseFloat(item);
                        });
                    } else {
                        const outputName = output.getAttribute("Name")
                        const outputStr = output.textContent;
                        const outputStrArray = outputStr.trim().split(/\s+/);
                        fieldOutputs[outputName] = outputStrArray.map(function (item) {
                            return parseFloat(item);
                        })
                    }
                }
                this.norm = 1.0 / max(nodes.flat());
                this.nodes = nodes;
                this.nvn = disp_dimension;
                this.ndim = dimension;
                this.dictionary = connectivities;
                this.types = [];
                this.solutions = [U];
                this.frames = [{"fieldOutputs": fieldOutputs}];

                for (let i = 0; i < typesIntArray.length; i++) {
                    if (typesIntArray[i] === 12) {
                        this.types.push('B1V')
                    } else if (typesIntArray[i] === 9 && connectivities[i].length === 3) {
                        this.types.push('T1V')
                    } else if (typesIntArray[i] === 9 && connectivities[i].length === 4) {
                        this.types.push('C1V')
                    } else if (typesIntArray[i] === 9 && connectivities[i].length === 8) {
                        this.types.push('C2V')
                    }

                }

                this.prop_dict = {};
                this.prop_dict_names = {};
                this.loaded = true;

                const secon_coords = this.nodes[0].map((_, colIndex) =>
                    this.nodes.map((row) => row[colIndex])
                );

                let size_x = max(secon_coords[0].flat()) - min(secon_coords[0].flat());
                let size_y = max(secon_coords[1].flat()) - min(secon_coords[1].flat());
                let size_z = max(secon_coords[2].flat()) - min(secon_coords[2].flat());

                let center_x = (max(secon_coords[0]) + min(secon_coords[0])) / 2;
                let center_y = (max(secon_coords[1]) + min(secon_coords[1])) / 2;
                let center_z = (max(secon_coords[2]) + min(secon_coords[2])) / 2;
                this.center = [
                    center_x - size_x / 2,
                    center_y - size_y / 2,
                    center_z - size_z / 2,
                ];

                this.size = max(this.nodes.flat()) - min(this.nodes.flat());
                this._nodes = [];
                for (let kk = 0; kk < this.nodes.length; kk++) {
                    this._nodes.push({_xcenter: this.nodes[kk], id: kk});
                }
                let h = this.size / 20;
                let kk = 0;
                for (const n of this.nodes) {
                    if (this.ndim === 1 || this.ndim === 2) {
                        let node = [n[0], n[1], n[2] + h];
                        this._nodes.push({_xcenter: node, id: kk});
                        if (this.ndim === 1) {
                            node = [n[0], n[1] + h, n[2] + h];
                            this._nodes.push({_xcenter: node, id: kk});
                            node = [n[0], n[1] + h, n[2]];
                            this._nodes.push({_xcenter: node, id: kk});
                        }
                    }
                    kk++;
                }
            };
            await processData();
            this.notiBar.resetMessage();
        } else {
            let errorMsg = "错误："
            if (response.status === 404) {
                errorMsg += "数据文件不存在！\n";
            }
            errorMsg += response.url + "\n" + response.status + " " + response.statusText
            window.alert(errorMsg);
            this.notiBar.setMessage("数据文件传输失败!");
        }
    }

    async updateShowOctree() {
        if (this.showOctree) {
            if (!this.octreeMesh) {
                await this.createOctree();
            }
            this.model.add(this.octreeMesh);
        } else {
            this.model.remove(this.octreeMesh);
        }
        await this.updateShowModel();
    }

    reset() {
        this.solution_as_displacement = false;
        this.variable_as_displacement = 2;
        this.toggleSolutionAsDisp();
        const track = this.resource_tracker.track.bind(this.resource_tracker);

        track(this.model);
        track(this.invisibleModel);

        for (let i = 0; i < this.elements.length; i++) {
            this.elements[i].geometry.dispose();
            this.bufferGeometries.pop().dispose();
            this.bufferLines.pop().dispose();
        }
        this.mergedGeometry.dispose();
        this.mergedLineGeometry.dispose();
        this.renderer.renderLists.dispose();
        this.material.dispose();
        this.line_material.dispose();
        this.resource_tracker.dispose();

        if (this.octreeMesh) {
            track(this.octreeMesh);
        }

        for (const sn of this.selectedNodes) {
            for (const smm of this.selectedNodesMesh[sn]) {
                this.model.remove(smm);
                smm.material.dispose();
                smm.geometry.dispose();
            }
        }

        this.selectedNodes = [];
        this.selectedNodesMesh = {};

        this.show_model = true;
        this.showOctree = false;

        this.element_views = new Set();
        this.wireframe = false;
        this.corriendo = false;
        this.animationFrameID = undefined;
        this.animate = false;
        this.colorOptions = "nocolor";
        this.config_dict = CONFIG_DICT["GENERAL"];
        this.min_search_radius = -Infinity;
        this.bufferGeometries = [];
        this.bufferLines = [];

        this.nodes = [];
        this.dictionary = [];
        this.solutions = [];
        this.U = [];
        this.step = 0;
        this.elements = [];
        this.types = [];
        this.magnification = 0.0;
        this.max_abs_disp = undefined;
        this.border_elements = [];
        this.scene.remove(this.model);
        this.scene.remove(this.invisibleModel);
        delete this.mergedGeometry;
        delete this.mergedLineGeometry;
        this.resource_tracker.untrack(this.model);
        this.resource_tracker.untrack(this.invisibleModel);
        if (this.octreeMesh) {
            this.resource_tracker.untrack(this.octreeMesh);
        }
        this.octreeMesh = undefined;
    }

    settings() {
        THREE.Object3D.DefaultUp = new THREE.Vector3(0, 0, 1);
        // Scene settings
        this.scene = new THREE.Scene();
        // Camera settings
        const fov = 40;
        const aspect = window.innerWidth / window.innerHeight; // the canvas default
        const near = 0.01;
        const far = 200;
        this.camera = new THREE.PerspectiveCamera(fov, aspect, near, far);
        this.camera.position.set(25, 25, 25);
        this.camera.lookAt(0, 0, 0);
        this.scene.add(this.camera);

        // Controls
        this.controls = new OrbitControls(this.camera, this.canvas);
        this.controls.target.set(0, 0, 0);
        this.controls.update();

        // Lights
        const color = 0xffffff;
        const intensity = 0.8;
        this.light1 = new THREE.PointLight(color, intensity);
        this.light2 = new THREE.AmbientLight(0xffffff, 0.0);
        this.camera.add(this.light1);
        this.scene.add(this.light2);

        // Legend
        this.orthoCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, 2);
        this.orthoCamera.position.set(-0.9, 0, 1);
        this.uiScene = new THREE.Scene();
        this.sprite = new THREE.Sprite(
            new THREE.SpriteMaterial({
                map: new THREE.CanvasTexture(this.legend.createCanvas()),
            })
        );
        this.uiScene.add(this.sprite);
        this.gh = new AxisGridHelper(this.scene, 0);
        this.gh.visible = this.axis;

        this.guiSettingsBasic();
    }

    async updateShowModel() {
        this.mesh.visible = this.show_model;
        this.contour.visible = this.show_model;
        this.draw_lines = this.show_model;
        this.gh.visible = true;
        for (const ch of this.model.children) {
            if (ch.visible) {
                this.gh.visible = false;
                break;
            }
        }
    }

    guiSettingsBasic() {
        if (this.settingsFolder) {
            this.settingsFolder.destroy();
        }
        this.settingsFolder = this.gui.addFolder("设置");
        this.settingsFolder.close();

        this.settingsFolder.add(this.gh, "visible").listen().name("坐标轴");

        this.settingsFolder.add(this, "rot").name("自动旋转").listen();

        this.settingsFolder
            .add(this, "wireframe")
            .listen()
            .onChange(() => {
                this.updateMaterial();
                this.updateGeometry();
            })
            .name("线框模式");
        this.settingsFolder
            .add(this, "draw_lines")
            .onChange(this.updateLines.bind(this))
            .name("显示线条")
            .listen();

        // this.settingsFolder
        //     .add(this, "showOctree")
        //     .onChange(this.updateShowOctree.bind(this))
        //     .listen()
        //     .name("显示八叉树");

        this.settingsFolder
            .add(this, "show_model")
            .name("显示模型")
            .onChange(this.updateShowModel.bind(this))
            .listen();

        if (this.config_dict["isDeformed"]) {
        } else {
            if (this.ndim !== 3) {
                this.settingsFolder
                    .add(this, "solution_as_displacement")
                    .listen()
                    .name("变形图")
                    .onFinishChange(this.toggleSolutionAsDisp.bind(this));
            }
        }

        // this.settingsFolder
        //     .add(this, "clickMode", [
        //         "查看单元",
        //         "删除单元",
        //         "发现节点",
        //         "发现区域",
        //     ])
        //     .listen()
        //     .name("左键点击");

        this.settingsFolder
            .add(this, "resolution", {
                "低 (1)": 1,
                "中 (2)": 2,
                "高 (4)": 3,
                "极高 (8)": 4,
                "最高 (16)": 5,
            })
            .listen()
            .onChange(this.updateResolution.bind(this))
            .name("分辨率");

        this.settingsFolder
            .add(this, "theme", themes, "默认")
            .name("风格")
            .listen()
            .onChange(this.updateTheme.bind(this));
    }

    toggleSolutionAsDisp() {
        this.config_dict["isDeformed"] = this.solution_as_displacement;
        this.guiSettings();
        if (!this.solution_as_displacement) {
            this.magnification = 0.0;
            this.updateSolutionAsDisplacement();
        } else {
            this.updateVariableAsSolution();
        }
    }

    updateVariableAsSolution() {
        this.animate = false;
        this.animate_mult = 1;
        this.magnification = 0.4 / this.max_abs_disp;
        this.updateDispSlider();
        this.updateSolutionAsDisplacement();
    }

    guiSettings() {
        // GUI
        if (this.disp_gui_sol_disp_folder) {
            this.disp_gui_sol_disp_folder.destroy();
        }
        if (this.solution_as_displacement) {
            this.disp_gui_sol_disp_folder = this.gui.addFolder(
                "Solution as displacement"
            );
            this.disp_gui_sol_disp_folder
                .add(this, "variable_as_displacement", {
                    x: 0,
                    y: 1,
                    z: 2,
                })
                .listen()

                .name("坐标方向")
                .onChange(this.updateVariableAsSolution.bind(this));
            this.variable_as_displacement = 2;
        }

        if (this.disp_gui_disp_folder) {
            this.disp_gui_disp_folder.destroy();
        }
        if (this.config_dict["isDeformed"]) {
            this.disp_gui_disp_folder = this.gui.addFolder("位移");
            this.disp_gui_disp_folder
                .add(this, "animate")
                .name("动画")
                .listen()
                .onChange(() => {
                    this.notiBar.setMessage("动画播放中");
                    if (!this.animate) {
                        this.animate_mult = 1.0;
                        this.updateMeshCoords();
                        this.updateGeometry();
                        this.notiBar.resetMessage();
                    }
                });
            this.magnificationSlider = this.disp_gui_disp_folder
                .add(this, "magnification", 0, 1)
                .name("位移缩放倍数")
                .listen()
                .onChange(() => {
                    this.updateMeshCoords();
                    this.updateGeometry();
                });
        }
    }

    async reload() {
        cancelAnimationFrame(this.animationFrameID);
        this.animate = false;
        this.reset();
        this.before_load();
        this.notiBar.setMessage("重新加载模型...");
        await this.loadXML(this.filename);
        // await this.loadJSON(this.filename);
        this.notiBar.resetMessage();
        await this.init(false);
        this.after_load();
    }

    updateLegend() {
        this.legend.setColorMap(this.colormap);
        const map = this.sprite.material.map;
        this.legend.setMax(this.max_color_value);
        this.legend.setMin(this.min_color_value);
        this.legend.updateCanvas(map.image);
        map.needsUpdate = true;
        this.updateMaterial();
        this.updateColorValues();
        this.updateGeometry();
    }

    updateColorVariable() {
        let msg;
        const co = this.colorOptions;
        if (co !== "nocolor") {
            this.colors = true;
            msg =
                "" +
                this.color_select_option.$select.value +
                "";
        } else {
            this.colors = false;
            msg = "";
        }
        for (const e of this.elements) {
            e.setMaxDispNode(
                this.colorOptions
            );
        }

        let max_disp = -Infinity;
        let min_disp = Infinity;
        for (const e of this.elements) {
            const variable = e.colors;
            max_disp = Math.max(max_disp, ...variable);
            min_disp = Math.min(min_disp, ...variable);
        }

        // 保留8位有效数字
        max_disp = parseFloat(max_disp.toFixed(8))
        min_disp = parseFloat(min_disp.toFixed(8))

        let delta = max_disp - min_disp;
        if (delta === 0) {
            delta = 1;
        }

        this.max_color_value = max_disp;
        this.min_color_value = min_disp;

        this.max_color_value_slider.step(delta / 1000.0);
        this.min_color_value_slider.step(delta / 1000.0);

        this.min_color_value_slider.min(min_disp);
        this.min_color_value_slider.max(max_disp);

        this.max_color_value_slider.min(min_disp);
        this.max_color_value_slider.max(max_disp);

        let max_str = this.max_color_value.toPrecision(4);
        let min_str = this.min_color_value.toPrecision(4);

        // 防止接近于零的数值无法显示
        if (max_str === "0.0000") {
            max_str = this.max_color_value.toExponential(4);
        }
        if (min_str === "0.0000") {
            min_str = this.min_color_value.toExponential(4);
        }

        msg += " 最大值=" + max_str + " 最小值=" + min_str;
        this.notiBar.setMessage(msg);
        this.updateLegend();
    }

    viewFront() {
        this.camera.position.set(1, 0, 0);
        this.camera.lookAt(0, 0, 0);
        this.zoomExtents();
    }

    viewTop() {
        this.camera.position.set(0, 0, 1);
        this.camera.lookAt(0, 0, 0);
        this.zoomExtents();
    }

    viewIso() {
        this.camera.position.set(1, 1, 1);
        this.camera.lookAt(0, 0, 0);
        this.zoomExtents();
    }

    updateCamera() {
        this.camera.updateProjectionMatrix();
    }

    async renderMath() {
        //function f() {
        //	renderMathInElement(document.body, {
        //		throwOnError: false,
        //	});
        //}
        //setTimeout(f, 100);
    }

    updateMaterial() {
        if (this.colors) {
            this.material = new THREE.MeshBasicMaterial({
                vertexColors: true,
                wireframe: this.wireframe,
                side: THREE.DoubleSide,
            });
            this.light1.intensity = 0.0;
            this.light2.intensity = 1.0;
        } else {
            if (this.theme["emissive"]) {
                this.material = new THREE.MeshLambertMaterial({
                    color: FOCUS_COLOR,
                    emissive: FOCUS_COLOR,
                    wireframe: this.wireframe,
                    side: THREE.DoubleSide,
                });
                this.light1.intensity = 1.0;
                this.light2.intensity = 0.0;
            } else {
                this.material = new THREE.MeshBasicMaterial({
                    color: FOCUS_COLOR,
                    wireframe: this.wireframe,
                    side: THREE.DoubleSide,
                });
                this.light1.intensity = 0.0;
                this.light2.intensity = 1.0;
            }
        }
        this.line_material = new THREE.LineBasicMaterial({
            color: LINES_COLOR,
            linewidth: 3,
        });
    }

    handleVisibilityChange() {
        if (document.visibilityState === "hidden") {
            this.clock.stop();
        } else {
            this.clock.start();
        }
    }

    update() {
        this.delta += this.clock.getDelta();
        if (this.delta > this.interval) {
            // The draw or time dependent code are here
            this.render(this.delta);
            this.delta = this.delta % this.interval;
        }
        this.animationFrameID = requestAnimationFrame(this.update.bind(this));
        this.refreshing = true;
        this.updateRefresh();
    }

    resizeRendererToDisplaySize() {
        const canvas = this.renderer.domElement;
        const pixelRatio = window.devicePixelRatio;
        const width = (canvas.clientWidth * pixelRatio) | 0;
        const height = (canvas.clientHeight * pixelRatio) | 0;
        const needResize = canvas.width !== width || canvas.height !== height;
        if (needResize) {
            this.renderer.setSize(width, height, false);
        }
        this.sprite.scale.x = 256.0 / this.container.clientWidth;
        this.sprite.scale.y = 512.0 / this.container.clientHeight;
        return needResize;
    }

    updateMeshCoords() {
        for (let i = 0; i < this.elements.length; i++) {
            const e = this.elements[i];
            if (this.draw_lines) {
                e.setGeometryCoords(this.magnification * this.animate_mult, this.norm);
            } else {
                e.setGeometryCoords(this.magnification * this.animate_mult, this.norm);
            }
        }
        if (this.colors) {
            this.updateColorValues();
        }
    }

    updateSpecificBufferGeometry(i) {
        this.bufferGeometries[i] = this.elements[i].geometry;
        this.bufferLines[i] = this.elements[i].lineGeometry;
        this.invisibleModel.children[i].geometry = this.elements[i].geometry;
    }

    updateColorValues() {
        for (let i = 0; i < this.elements.length; i++) {
            const e = this.elements[i];
            const colors = this.bufferGeometries[i].attributes.color;
            for (let j = 0; j < e.domain.length; j++) {
                let value = e.colors[j];
                const color = this.legend.getColor(value);
                colors.setXYZ(j, color.r, color.g, color.b);
            }
        }
    }

    updateGeometry() {
        if (this.octreeMesh) {
            this.octreeMesh.material = this.line_material;
            this.octreeMesh.material.needsUpdate = true;
        }
        for (const sn of this.selectedNodes) {
            for (const smm of this.selectedNodesMesh[sn]) {
                smm.material = this.line_material;
                smm.material.needsUpdate = true;
            }
        }

        this.mergedGeometry.dispose();
        this.mergedGeometry = BufferGeometryUtils.mergeBufferGeometries(
            this.bufferGeometries,
            false
        );
        this.mesh.geometry = this.mergedGeometry;
        this.mesh.material = this.material;
        this.mesh.material.needsUpdate = true;

        if (this.draw_lines) {
            this.mergedLineGeometry.dispose();
            this.mergedLineGeometry = BufferGeometryUtils.mergeBufferGeometries(
                this.bufferLines,
                false
            );
            this.contour.geometry = this.mergedLineGeometry;
            this.contour.material = this.line_material;
            this.contour.material.needsUpdate = true;
        }
        for (const ev of this.element_views) {
            ev.updateGeometry();
        }
    }

    rotateModel() {
        // this.model.rotation.z += 0.005;
        // 旋转相机的位置和目标点
        let r = (this.camera.position.x ** 2 + this.camera.position.y ** 2) ** 0.5
        this.camera.position.x = Math.sin(this.clock.elapsedTime * 0.1) * r;
        this.camera.position.y = Math.cos(this.clock.elapsedTime * 0.1) * r;
        this.camera.lookAt(0, 0, 0);
        this.renderer.render(this.scene, this.camera);
    }

    async render(time) {
        if (typeof time == "number") {
            time = time || 0;
        } else {
            time = 0.0;
        }
        this.animate_mult += time * this.side;
        // +-1 振动
        // if (this.animate_mult > 1) {
        //     this.side = -1.0;
        //     this.animate_mult = 1.0;
        // } else if (this.animate_mult < -1) {
        //     this.side = 1.0;
        //     this.animate_mult = -1.0;
        // }
        // 0-1 振动
        if (this.animate_mult > 1) {
            this.side = -1.0;
            this.animate_mult = 1.0;
        } else if (this.animate_mult < 0) {
            this.side = 1.0;
            this.animate_mult = 0.0;
        }
        if (!this.animate) {
            this.animate_mult = 1.0;
        }
        if (this.rot) {
            this.rotateModel();
        } else {
            if (this.animate) {
                this.updateMeshCoords();
                this.updateGeometry();
            }
        }
        if (this.resizeRendererToDisplaySize()) {
            const canvas = this.renderer.domElement;
            this.camera.aspect = canvas.clientWidth / canvas.clientHeight;
            this.camera.updateProjectionMatrix();
            this.zoomExtents();
        }
        this.renderer.render(this.scene, this.camera);
        if (this.colors && this.MenuClosed) {
            this.renderer.render(this.uiScene, this.orthoCamera);
        }
    }

    zoomExtents() {
        let vFoV = this.camera.getEffectiveFOV();
        let hFoV = this.camera.fov * this.camera.aspect;

        let FoV = Math.min(vFoV, hFoV);

        let dir = new THREE.Vector3();
        this.camera.getWorldDirection(dir);

        let bs = this.mesh.geometry.boundingSphere;
        if (bs !== null) {
            let bsWorld = bs.center.clone();
            this.mesh.localToWorld(bsWorld);
            let th = (FoV / 2 * Math.PI) / 180.0;
            let sina = Math.sin(th);
            let R = bs.radius;
            let FL = R / sina;

            let cameraDir = new THREE.Vector3();
            this.camera.getWorldDirection(cameraDir);

            let cameraOffs = cameraDir.clone();
            cameraOffs.multiplyScalar(-FL * this.initial_zoom);
            let newCameraPos = bsWorld.clone().add(cameraOffs);

            this.camera.position.copy(newCameraPos);
            this.camera.lookAt(bsWorld);
            this.controls.target.copy(bsWorld);
            this.controls.update();
        }
    }

    updateLines() {
        if (this.draw_lines) {
            this.model.add(this.contour);
        } else {
            this.model.remove(this.contour);
        }
        this.updateGeometry();
    }

    guiViews() {
        if (this.viewsFolder) {
            this.viewsFolder.destroy();
        }
        this.viewsFolder = this.gui.addFolder("视图");
        this.viewsFolder.close();
        this.viewsFolder
            .add(this, "viewFront")
            .name("正视图");
        this.viewsFolder
            .add(this, "viewTop")
            .name("俯视图");
        this.viewsFolder
            .add(this, "viewIso")
            .name("等轴视图");
    }

    goBack() {
        history.go(-1);
    }

    guiSolutions() {
        if (this.guiFolder) {
            this.guiFolder.destroy();
        }
        this.guiFolder = this.gui.addFolder("云图");
        let variableSelectDict = {};
        for (let key in this.frames[this.step]["fieldOutputs"]) {
            variableSelectDict[key] = key;
        }
        this.color_select_option = this.guiFolder
            .add(this, "colorOptions", {
                "无": "nocolor",
                "|U|": "|U|",
                "U1": "U1",
                "U2": "U2",
                "U3": "U3",
                ...variableSelectDict,
                "单元雅克比": "scaled_jacobi",
                // ...this.config_dict["dict"],
                ...this.prop_dict_names,
            })
            .name("变量")
            .listen()
            .onChange(this.updateColorVariable.bind(this))
            .onFinishChange(this.renderMath.bind(this));
        this.guiFolder
            .add(this, "colormap", [
                "彩虹图",
                "冷热图",
                "热力图",
                "灰度图",
            ])
            .listen()
            .name("颜色")
            .onChange(this.updateLegend.bind(this));
        this.max_color_value_slider = this.guiFolder
            .add(this, "max_color_value", 0.0, 1.0)
            .name("最大值")
            .listen()
            .onChange(this.updateLegend.bind(this));
        this.min_color_value_slider = this.guiFolder
            .add(this, "min_color_value", 0.0, 1.0)
            .name("最小值")
            .listen()
            .onChange(this.updateLegend.bind(this));
        // this.guiFolder
        //     .add(this, "step", this.solutions_info_str)
        //     .onChange(this.updateSolution.bind(this))
        //     .listen()
        //     .name("帧");
    }

    async init(animate = false) {
        this.guiSolutions();
        this.guiSettings();
        this.guiViews();
        this.guiSettingsBasic();

        this.animate = animate;
        if (!this.config_dict["isDeformed"]) {
            this.animate = false;
        }
        await this.createElements();
        this.createLines();
        console.log(this.bufferGeometries)
        this.mergedGeometry = BufferGeometryUtils.mergeBufferGeometries(
            this.bufferGeometries,
            true
        );
        this.notiBar.setMessage("创建材料...");
        await allowUpdate();
        this.updateMaterial();
        this.mergedLineGeometry = BufferGeometryUtils.mergeBufferGeometries(
            this.bufferLines,
            true
        );
        this.contour = new THREE.LineSegments(
            this.mergedLineGeometry,
            this.line_material
        );
        this.model.add(this.contour);

        this.mesh = new THREE.Mesh(this.mergedGeometry, this.material);
        this.notiBar.setMessage("生成网格...");
        await allowUpdate();
        this.updateU();
        this.model.add(this.mesh);

        this.scene.add(this.model);
        this.scene.add(this.invisibleModel);

        this.updateLines();
        if (!this.corriendo) {
            this.corriendo = true;
            this.animationFrameID = requestAnimationFrame(
                this.update.bind(this)
            );
            this.refreshing = true;
            this.updateRefresh();
        }
        this.renderer.render(this.scene, this.camera);
        this.zoomExtents();

        this.notiBar.setMessage("绘制模型...");
        await allowUpdate();

        this.notiBar.setMessage("加载完成");
        await allowUpdate();
    }

    setStep(step) {
        this.step = step;
        this.updateU();
        this.updateMeshCoords();
        this.updateGeometry();
    }

    updateDispSlider() {
        const max_disp = max(this.U);
        const min_disp = min(this.U);
        this.max_abs_disp =
            Math.max(Math.abs(max_disp), Math.abs(min_disp)) * this.norm;
        if (this.config_dict["isDeformed"]) {
            this.magnificationSlider.min(0.0);
            this.magnificationSlider.max(0.4 / this.max_abs_disp);
        }
    }

    updateU() {
        this.U = this.solutions[this.step].flat();
        let frame = this.frames[this.step];
        this.updateDispSlider();

        for (const e of this.elements) {
            e.setUe(
                this.U,
                this.config_dict["isDeformed"]
            );
            e.setFrame(
                frame
            );
            if (this.solution_as_displacement) {
                e.variableAsDisplacement(this.variable_as_displacement);
            }
        }
        this.updateMeshCoords();
        this.updateColorVariable();
    }

    nextSolution() {
        this.step += 1 * (this.step < this.solutions.length - 1);
        this.updateSolution();
    }

    updateSolution() {
        this.updateU();
        this.updateGeometry();
    }

    updateSolutionAsDisplacement() {
        for (const e of this.elements) {
            if (this.solution_as_displacement) {
                e.variableAsDisplacement(this.variable_as_displacement);
            }
        }
        this.updateMeshCoords();
        this.updateGeometry();
    }

    prevSolution() {
        this.step -= 1 * (this.step > 0);
        this.updateSolution();
    }

    async createElements() {
        this.bufferGeometries = [];
        this.elements = new Array(this.dictionary.length).fill(0.0);
        let times = 0;
        for (let i = 0; i < this.dictionary.length; i++) {
            const conns = this.dictionary[i];
            const dofIDs = [];
            for (let i = 0; i < this.nvn; i++) {
                const a = [];
                for (const gdl of conns) {
                    a.push(gdl * this.nvn + i);
                }
                dofIDs.push(a);
            }
            const coords = [];
            for (const node of conns) {
                coords.push(this.nodes[node]);
            }
            this.elements[i] = new types[this.types[i]](
                coords,
                conns,
                dofIDs,
                this.size * this.norm / 100.0
            );

            let d = 0;
            for (const c of coords) {
                let sx = c[0] - this.elements[i]._xcenter[0];
                let sy = c[1] - this.elements[i]._xcenter[1];
                let sz = c[2] - this.elements[i]._xcenter[2];
                d = Math.max(d, sx ** 2 + sy ** 2 + sz ** 2);
            }

            this.min_search_radius = Math.max(
                this.min_search_radius,
                2 * d ** 0.5
            );
            this.elements[i].index = i;
            const p = {};
            for (const [key, value] of Object.entries(this.prop_dict)) {
                let result = undefined;
                if (value[1] instanceof Array) {
                    result = value[1][i];
                } else {
                    result = value[1];
                }
                p[key] = result;
            }
            this.elements[i].set_properties(p);
            // console.log(this.elements[i].geometry)
            this.bufferGeometries.push(this.elements[i].geometry);
            const messh = new THREE.Mesh(
                this.elements[i].geometry,
                this.material
            );
            messh.visible = false;
            messh.userData = {elementId: i};
            this.invisibleModel.add(messh);

            let percentage = (i / this.dictionary.length) * 100;
            if (percentage > times) {
                times += 1;
                this.notiBar.setProgressBar("加载模型...", percentage);
                await allowUpdate();
            }
        }
    }

    createLines() {
        this.bufferLines = [];
        for (const e of this.elements) {
            this.bufferLines.push(e.lineGeometry);
        }
    }
}

export {FEMViewer, themes};
