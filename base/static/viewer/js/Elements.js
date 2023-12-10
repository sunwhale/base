import * as THREE from "./build/three.module.js";
import {Prism, Tet} from "./TriangularBasedGeometries.js";
import {abs, add, det, matInverse, multiply, multiplyScalar, sum, transpose,} from "./math.js";

function newPrism(n = 1) {
    const tr = new Prism();
    tr.divide(n - 1);
    const coordinates = tr.giveCoords().flat();
    const vertices = new Float32Array(coordinates);
    const geometry = new THREE.BufferGeometry();
    // const geometry = new THREE.BoxGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
    geometry.computeVertexNormals();
    return geometry;
}

function newTet(n = 1) {
    const tr = new Tet();
    tr.divide(n - 1);
    const coordinates = tr.giveCoords().flat();
    const vertices = new Float32Array(coordinates);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
    geometry.computeVertexNormals();
    return geometry;
}

class Element {
    coords;
    dofIDs;
    Ue;
    geometry;
    lineGeometry;
    domain;
    _domain;
    lineDomain;
    ndim;
    modifier;
    lineModifier;
    nodeCoords;
    qpCoords;

    constructor(coords, conns, dofIDs) {
        this.coords = coords;
        this.conns = conns;
        this.dofIDs = dofIDs;
        this.Ue = [];
        this.nvn = dofIDs.length;
        this.scaledJacobian = undefined;
        this.res = 1;
    }

    get _xcenter() {
        let x = 0;
        let y = 0;
        let z = 0;
        let n = this.coords.length;
        for (let i = 0; i < n; i++) {
            let node_coord = this.coords[i];
            x += node_coord[0];
            y += node_coord[1];
            z += node_coord[2];
        }
        return [x / n, y / n, z / n];
    }

    setUe(U, isDeformed = false) {
        this.Ue = [];
        for (const conn of this.dofIDs) {
            const u = [];
            for (const id of conn) {
                u.push(U[id]);
            }
            this.Ue.push(u);
        }
        this.updateCoordinates(this.Ue, isDeformed);
    }

    setFrame(frame) {
        this.fieldOutputs = frame["fieldOutputs"]
        this.elementFieldOutputs = {}
        for (let key in this.fieldOutputs) {
            const output = [];
            for (const id of this.conns) {
                output.push(this.fieldOutputs[key][id]);
            }
            this.elementFieldOutputs[key] = output.flat();
        }
    }

    updateCoordinates(Ue, isDeformed) {
        this.X = [];
        this.XLines = [];
        this.U = [];
        this.ULines = [];
        this._U = [];
        this._ULines = [];

        const domainLength = this._domain.length;
        const lineDomainLength = this.lineDomain.length;

        for (let i = 0; i < domainLength; i++) {
            const z = this._domain[i];
            const [XX, P] = this.T(z);
            const X = [...XX[0], ...(new Array(3 - this.ndim).fill(0.0))];
            const U = multiply(Ue, transpose([P]));
            const _U = [...U, ...(new Array(3 - this.ndim).fill(0.0))];
            this.X.push(X);
            this.U.push(U);
            this._U.push(_U);
        }

        for (let i = 0; i < lineDomainLength; i++) {
            const z = this.lineDomain[i];
            const [XX, P] = this.T(z);
            const XLines = [...XX[0], ...(new Array(3 - this.ndim).fill(0.0))];
            const ULines = multiply(Ue, transpose([P]));
            const _ULines = [...ULines, ...(new Array(3 - this.ndim).fill(0.0))];
            this.XLines.push(XLines);
            this.ULines.push(ULines);
            this._ULines.push(_ULines);
        }

        if (!isDeformed) {
            this._U = new Array(domainLength).fill([0.0, 0.0, 0.0]);
            this._ULines = new Array(lineDomainLength).fill([0.0, 0.0, 0.0]);
        }
    }

    variableAsDisplacement(variable) {
        this._U = [];
        this._ULines = [];
        for (let i = 0; i < this.U.length; i++) {
            const _U = [];
            for (let j = 0; j < 3; j++) {
                if (j === variable) {
                    _U.push(this.U[i][0]);
                } else {
                    _U.push(0.0);
                }
            }
            this._U.push(_U);
        }
        for (let i = 0; i < this.ULines.length; i++) {
            const _U = [];
            for (let j = 0; j < 3; j++) {
                if (j === variable) {
                    _U.push(this.ULines[i][0]);
                } else {
                    _U.push(0.0);
                }
            }
            this._ULines.push(_U);
        }
    }

    setGeometryCoords(dispAmpFactor, norm) {
        dispAmpFactor = dispAmpFactor || 1.0;
        norm = norm || 1.0;

        const parentGeometry = this.geometry;
        const lineGeometry = this.lineGeometry;
        const {position: parentPosition} = parentGeometry.attributes;
        const {position: linePosition} = lineGeometry?.attributes || {};

        this._domain.forEach((_, i) => {
            const X = this.X[i];
            const U = this._U[i];
            const modifier = this.modifier[i];

            parentPosition.setXYZ(
                i,
                X[0] * norm + modifier[0] + U[0] * dispAmpFactor * norm,
                X[1] * norm + modifier[1] + U[1] * dispAmpFactor * norm,
                X[2] * norm + modifier[2] + U[2] * dispAmpFactor * norm
            );
        });

        parentPosition.needsUpdate = true;
        parentGeometry.computeVertexNormals();

        if (lineGeometry) {
            this.lineDomain.forEach((_, i) => {
                const X = this.XLines[i];
                const U = this._ULines[i];
                const modifier = this.lineModifier[i];

                linePosition.setXYZ(
                    i,
                    X[0] * norm + modifier[0] + U[0] * dispAmpFactor * norm,
                    X[1] * norm + modifier[1] + U[1] * dispAmpFactor * norm,
                    X[2] * norm + modifier[2] + U[2] * dispAmpFactor * norm
                );
            });

            linePosition.needsUpdate = true;
            lineGeometry.computeVertexNormals();
        }
    }


    J(_coord) {
        const dN = transpose(this.shape_gradients(_coord));
        return [multiply(dN, this.nodeCoords), dN];
    }

    T(_coord) {
        let N = this.shape_values(_coord);
        return [multiply([N], this.nodeCoords), N];
    }

    get sJ() {
        if (this.scaledJacobian) {
            return this.scaledJacobian;
        }
        let max_qp_jacobi_det = -Infinity;
        let min_qp_jacobi_det = Infinity;
        for (const qp_coord of this.qpCoords) {
            const [qp_jacobi, _] = this.J(qp_coord);
            const qp_jacobi_det = det(qp_jacobi);
            max_qp_jacobi_det = Math.max(max_qp_jacobi_det, qp_jacobi_det);
            min_qp_jacobi_det = Math.min(min_qp_jacobi_det, qp_jacobi_det);
        }
        this.scaledJacobian = min_qp_jacobi_det / Math.abs(max_qp_jacobi_det);
        return min_qp_jacobi_det / Math.abs(max_qp_jacobi_det);
    }

    inverseMapping(xo) {
        console.log(xo)
        const x0 = [];
        for (let i = 0; i < this.ndim; i++) {
            x0.push(xo[i]);
        }
        let p = undefined;
        let zi = new Array(this.ndim).fill(1 / 3);
        let li = -1;
        if (this instanceof Triangular) {
            li = 0;
        }
        for (let i = 0; i < 100; i++) {
            let [puntos, pp] = this.T(zi);
            p = pp;
            let punot = puntos[0];
            let xi = add(x0, multiplyScalar(punot, -1));
            let [J, _] = this.J(zi);
            let _J = matInverse(J);
            let dz = multiply(_J, transpose([xi])).flat();
            zi = add(zi, dz);
            if (sum(abs(dz)) < 0.00001) {
                break;
            }
            for (let j = 0; j < zi.length; j++) {
                zi[j] = Math.max(zi[j], li);
                zi[j] = Math.min(zi[j], 1);
            }
        }
        return zi;
    }

    set_properties(p) {
        this.properties = p;
    }

    giveSolutionPoint(coord, colorMode) {
        let result = 0;
        let solution = Array(this.Ue[0].length).fill(0.0);
        let N = this.shape_values(coord)
        if (colorMode in this.elementFieldOutputs) {
            let variable = [this.elementFieldOutputs[colorMode]]
            for (let i = 0; i < this.elementFieldOutputs[colorMode].length; i++) {
                solution[i] = variable[0][i];
            }
            for (let i = 0; i < N.length; i++) {
                result += N[i] * solution[i];
            }
        } else if (colorMode === "|U|") {
            let variable = this.Ue
            for (let i = 0; i < this.Ue[0].length; i++) {
                let disp_magnitude = 0.0;
                for (let j = 0; j < this.nvn; j++) {
                    let ui = variable[j][i];
                    disp_magnitude += ui ** 2;
                }
                solution[i] = disp_magnitude ** 0.5;
            }
            for (let i = 0; i < N.length; i++) {
                result += N[i] * solution[i];
            }
        } else if (colorMode === "U1") {
            let variable = this.Ue
            for (let i = 0; i < this.Ue[0].length; i++) {
                solution[i] = variable[0][i];
            }
            for (let i = 0; i < N.length; i++) {
                result += N[i] * solution[i];
            }
        } else if (colorMode === "U2") {
            let variable = this.Ue
            for (let i = 0; i < this.Ue[0].length; i++) {
                solution[i] = variable[1][i];
            }
            for (let i = 0; i < N.length; i++) {
                result += N[i] * solution[i];
            }
        } else if (colorMode === "U3") {
            let variable = this.Ue
            for (let i = 0; i < this.Ue[0].length; i++) {
                solution[i] = variable[2][i];
            }
            for (let i = 0; i < N.length; i++) {
                result += N[i] * solution[i];
            }
        } else if (colorMode === "scaled_jacobi") {
            result = this.sJ;
        } else if (colorMode[0] === "PROP") {
            let prop_name = colorMode[1];
            result = this.properties[prop_name];
        }
        return result;
    }

    setMaxDispNode(colorMode) {
        this.colors = Array(this.domain.length).fill(0.0);
        for (let i = 0; i < this._domain.length; i++) {
            const z = this._domain[i];
            this.colors[i] = this.giveSolutionPoint(
                z,
                colorMode
            );
        }
    }

    shape_values(_coord) {
        return undefined;
    }

    shape_gradients(_coord) {
        return undefined;
    }
}

class Element3D extends Element {
    constructor(coords, conns, dofIDs) {
        super(coords, conns, dofIDs);
    }
}

class Brick extends Element3D {
    order;

    constructor(coords, conns, dofIDs) {
        super(coords, conns, dofIDs);
        this.type = "B1V";
        this.nodeCoords = coords;
        this.ndim = 3;
        this.initGeometry();
        this.qpCoords = [
            [-0.77459667, -0.77459667, -0.77459667],
            [-0.77459667, -0.77459667, 0],
            [-0.77459667, -0.77459667, 0.77459667],
            [-0.77459667, 0, -0.77459667],
            [-0.77459667, 0, 0],
            [-0.77459667, 0, 0.77459667],
            [-0.77459667, 0.77459667, -0.77459667],
            [-0.77459667, 0.77459667, 0],
            [-0.77459667, 0.77459667, 0.77459667],
            [0, -0.77459667, -0.77459667],
            [0, -0.77459667, 0],
            [0, -0.77459667, 0.77459667],
            [0, 0, -0.77459667],
            [0, 0, 0],
            [0, 0, 0.77459667],
            [0, 0.77459667, -0.77459667],
            [0, 0.77459667, 0],
            [0, 0.77459667, 0.77459667],
            [0.77459667, -0.77459667, -0.77459667],
            [0.77459667, -0.77459667, 0],
            [0.77459667, -0.77459667, 0.77459667],
            [0.77459667, 0, -0.77459667],
            [0.77459667, 0, 0],
            [0.77459667, 0, 0.77459667],
            [0.77459667, 0.77459667, -0.77459667],
            [0.77459667, 0.77459667, 0],
            [0.77459667, 0.77459667, 0.77459667],
        ];
        this.qpWeights = [
            0.17146776, 0.27434842, 0.17146776, 0.27434842, 0.43895748,
            0.27434842, 0.17146776, 0.27434842, 0.17146776, 0.27434842,
            0.43895748, 0.27434842, 0.43895748, 0.70233196, 0.43895748,
            0.27434842, 0.43895748, 0.27434842, 0.17146776, 0.27434842,
            0.17146776, 0.27434842, 0.43895748, 0.27434842, 0.17146776,
            0.27434842, 0.17146776,
        ];
    }

    shape_values(_coord) {
        const x = _coord[0];
        const y = _coord[1];
        const z = _coord[2];
        return [
            0.125 * (1 - x) * (1 - y) * (1 - z),
            0.125 * (1 + x) * (1 - y) * (1 - z),
            0.125 * (1 + x) * (1 + y) * (1 - z),
            0.125 * (1 - x) * (1 + y) * (1 - z),
            0.125 * (1 - x) * (1 - y) * (1 + z),
            0.125 * (1 + x) * (1 - y) * (1 + z),
            0.125 * (1 + x) * (1 + y) * (1 + z),
            0.125 * (1 - x) * (1 + y) * (1 + z),
        ];
    }

    shape_gradients(_coord) {
        const x = _coord[0];
        const y = _coord[1];
        const z = _coord[2];
        return [
            [
                -0.125 * (1 - z) * (1 - y),
                -0.125 * (1 - z) * (1 - x),
                -0.125 * (1 - x) * (1 - y),
            ],
            [
                0.125 * (1 - y) * (1 - z),
                -0.125 * (1 + x) * (1 - z),
                -0.125 * (1 + x) * (1 - y),
            ],
            [
                0.125 * (1 + y) * (1 - z),
                0.125 * (1 + x) * (1 - z),
                -0.125 * (1 + x) * (1 + y),
            ],
            [
                -0.125 * (1 + y) * (1 - z),
                0.125 * (1 - x) * (1 - z),
                -0.125 * (1 - x) * (1 + y),
            ],
            [
                -0.125 * (1 - y) * (1 + z),
                -0.125 * (1 - x) * (1 + z),
                0.125 * (1 - x) * (1 - y),
            ],
            [
                0.125 * (1 - y) * (1 + z),
                -0.125 * (1 + x) * (1 + z),
                0.125 * (1 + x) * (1 - y),
            ],
            [
                0.125 * (1 + y) * (1 + z),
                0.125 * (1 + x) * (1 + z),
                0.125 * (1 + x) * (1 + y),
            ],
            [
                -0.125 * (1 + y) * (1 + z),
                0.125 * (1 - x) * (1 + z),
                0.125 * (1 - x) * (1 + y),
            ],
        ];
    }

    transformation(geo) {
        const qpCoords = [];
        this.lineDomain = [];
        this.lineModifier = [];
        this.modifier = [];
        for (let i = 0; i < geo.attributes.position.count; i++) {
            const x = geo.attributes.position.getX(i);
            const y = geo.attributes.position.getY(i);
            const z = geo.attributes.position.getZ(i);
            qpCoords.push([x * 2, y * 2, z * 2]);
            this.modifier.push([0.0, 0.0, 0.0]);
        }
        for (let i = 0; i < this.lineGeometry.attributes.position.count; i++) {
            const x = this.lineGeometry.attributes.position.getX(i);
            const y = this.lineGeometry.attributes.position.getY(i);
            const z = this.lineGeometry.attributes.position.getZ(i);
            this.lineDomain.push([2 * x, 2 * y, 2 * z]);
            this.lineModifier.push([0.0, 0.0, 0.0]);
        }
        return qpCoords;
    }

    initGeometry() {
        this.geometry = new THREE.BoxGeometry(
            1,
            1,
            1,
            2 ** (this.res - 1),
            2 ** (this.res - 1),
            2 ** (this.res - 1)
        );
        this.lineGeometry = new THREE.EdgesGeometry(this.geometry);
        this.domain = this.transformation(this.geometry);
        this._domain = this.domain;
        this.colors = Array(this.modifier.length).fill(0.0);
        this.geometry.setAttribute(
            "color",
            new THREE.Float32BufferAttribute(
                new Array(this.modifier.length * 3),
                3
            )
        );
    }
}

class Tetrahedral extends Element3D {
    order;

    constructor(coords, conns, dofIDs) {
        super(coords, conns, dofIDs);
        this.type = "TE1V";
        this.ndim = 3;
        this.nodeCoords = coords;
        this.initGeometry();
        this.qpCoords = [
            [0.01583591, 0.3280547, 0.3280547],
            [0.3280547, 0.01583591, 0.3280547],
            [0.3280547, 0.3280547, 0.01583591],
            [0.3280547, 0.3280547, 0.3280547],
            [0.67914318, 0.10695227, 0.10695227],
            [0.10695227, 0.67914318, 0.10695227],
            [0.10695227, 0.10695227, 0.67914318],
            [0.10695227, 0.10695227, 0.10695227],
        ];
        this.qpWeights = [
            0.023088, 0.023088, 0.023088, 0.023088, 0.01857867, 0.01857867,
            0.01857867, 0.01857867,
        ];
    }

    shape_values(_coord) {
        let x = _coord[0];
        let y = _coord[1];
        let z = _coord[2];
        return [1 - x - y - z, x, y, z];
    }

    shape_gradients(_coord) {
        return [
            [-1.0, -1.0, -1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ];
    }

    transformation(geo) {
        this.modifier = [];
        this.lineDomain = [];
        this.lineModifier = [];
        const qpCoords = [];
        for (let i = 0; i < geo.attributes.position.count; i++) {
            const x = geo.attributes.position.getX(i);
            const y = geo.attributes.position.getY(i);
            const z = geo.attributes.position.getZ(i);
            this.modifier.push([0.0, 0.0, 0.0]);
            qpCoords.push([x, y, z]);
        }
        for (let i = 0; i < this.lineGeometry.attributes.position.count; i++) {
            const x = this.lineGeometry.attributes.position.getX(i);
            const y = this.lineGeometry.attributes.position.getY(i);
            const z = this.lineGeometry.attributes.position.getZ(i);
            this.lineDomain.push([x, y, z]);
            this.lineModifier.push([0.0, 0.0, 0.0]);
        }
        return qpCoords;
    }

    initGeometry() {
        this.geometry = newTet(this.res);
        this.lineGeometry = new THREE.EdgesGeometry(this.geometry);
        this.domain = this.transformation(this.geometry);
        this._domain = this.domain;
        this.colors = Array(this.modifier.length).fill(0.0);
        this.geometry.setAttribute(
            "color",
            new THREE.Float32BufferAttribute(
                new Array(this.modifier.length * 3),
                3
            )
        );
    }
}

class Lineal extends Element3D {
    order;

    constructor(coords, conns, dofIDs, thick) {
        super(coords, conns, dofIDs);
        this.thick = thick;
        this.type = "L1V";
        this.ndim = 1;
        const c = [];
        for (let i = 0; i < coords.length; i++) {
            const x = coords[i][0];
            c.push([x]);
        }
        this.nodeCoords = c;
        this.initGeometry();
        this.qpCoords = [[-0.77459667], [0], [0.77459667]];
        this.qpWeights = [0.55555556, 0.88888889, 0.55555556];
    }

    shape_values(_coord) {
        let x = _coord[0]
        return [0.5 * (1.0 - x), 0.5 * (1.0 + x)];
    }

    shape_gradients(_coord) {
        return [[-0.5], [0.5]];
    }

    transformation(geo) {
        this.modifier = [];
        this.lineDomain = [];
        this.lineModifier = [];
        this._domain = [];
        const qpCoords = [];
        for (let i = 0; i < geo.attributes.position.count; i++) {
            const x = geo.attributes.position.getX(i);
            const y = geo.attributes.position.getY(i);
            const z = geo.attributes.position.getZ(i);
            qpCoords.push([x * 2, y * 2, z * 2]);
            this._domain.push([x * 2]);
            this.modifier.push([
                0.0,
                (this.thick / 20) * (y + 0.5),
                (this.thick / 20) * (z + 0.5),
            ]);
        }
        for (let i = 0; i < this.lineGeometry.attributes.position.count; i++) {
            const x = this.lineGeometry.attributes.position.getX(i);
            const y = this.lineGeometry.attributes.position.getY(i);
            const z = this.lineGeometry.attributes.position.getZ(i);
            this.lineDomain.push([x * 2]);
            this.lineModifier.push([
                0.0,
                (this.thick / 20) * (y + 0.5),
                (this.thick / 20) * (z + 0.5),
            ]);
        }
        return qpCoords;
    }

    initGeometry() {
        this.geometry = new THREE.BoxGeometry(
            1,
            1,
            1,
            2 ** (this.res - 1),
            1,
            1
        );
        this.lineGeometry = new THREE.EdgesGeometry(this.geometry);
        this.domain = this.transformation(this.geometry);
        this.colors = Array(this.modifier.length).fill(0.0);
        this.geometry.setAttribute(
            "color",
            new THREE.Float32BufferAttribute(
                new Array(this.modifier.length * 3),
                3
            )
        );
    }
}

class Triangular extends Element3D {
    order;

    constructor(coords, conns, dofIDs, thick) {
        super(coords, conns, dofIDs);
        this.type = "T1V";
        this.ndim = 2;
        this.thick = thick;

        const c = [];
        for (let i = 0; i < coords.length; i++) {
            const x = coords[i][0];
            const y = coords[i][1];
            c.push([x, y]);
        }
        this.nodeCoords = c;
        this.initGeometry();
        const A0 = 1 / 3;
        const A1 = 0.05971587178977;
        const A2 = 0.797426985353087;
        const B1 = 0.470142064105115;
        const B2 = 0.101286507323456;
        const W0 = 0.1125;
        const W1 = 0.066197076394253;
        const W2 = 0.062969590272413;
        const X = [A0, A1, B1, B1, B2, B2, A2];
        const Y = [A0, B1, A1, B1, A2, B2, B2];
        this.qpCoords = [];
        for (let i = 0; i < X.length; i++) {
            this.qpCoords.push([X[i], Y[i]]);
        }
        this.qpWeights = [W0, W1, W1, W1, W2, W2, W2];
    }

    shape_values(_coord) {
        let x = _coord[0]
        let y = _coord[1]
        return [1 - x - y, x, y];
    }

    shape_gradients(_coord) {
        return [
            [-1.0, -1.0],
            [1.0, 0.0],
            [0.0, 1.0],
        ];
    }

    transformation(geo) {
        this._domain = [];
        this.modifier = [];
        this.lineDomain = [];
        this.lineModifier = [];
        const qpCoords = [];
        for (let i = 0; i < geo.attributes.position.count; i++) {
            const x = geo.attributes.position.getX(i);
            const y = geo.attributes.position.getY(i);
            const z = geo.attributes.position.getZ(i);
            qpCoords.push([x, y, z]);
            this._domain.push([x, y]);
            this.modifier.push([0.0, 0.0, (this.thick / 20) * z]);
        }
        for (let i = 0; i < this.lineGeometry.attributes.position.count; i++) {
            const x = this.lineGeometry.attributes.position.getX(i);
            const y = this.lineGeometry.attributes.position.getY(i);
            const z = this.lineGeometry.attributes.position.getZ(i);
            this.lineDomain.push([x, y]);
            this.lineModifier.push([0.0, 0.0, (this.thick / 20) * z]);
        }
        return qpCoords;
    }

    initGeometry() {
        this.geometry = newPrism(this.res);
        this.lineGeometry = new THREE.EdgesGeometry(this.geometry);
        this.domain = this.transformation(this.geometry);
        this.colors = Array(this.modifier.length).fill(0.0);
        this.geometry.setAttribute(
            "color",
            new THREE.Float32BufferAttribute(
                new Array(this.modifier.length * 3),
                3
            )
        );
    }
}

class Quadrilateral extends Element3D {
    order;

    constructor(coords, conns, dofIDs, thick) {
        super(coords, conns, dofIDs);
        this.thick = thick;
        this.type = "C1V";
        this.ndim = 2;

        const c = [];
        for (let i = 0; i < coords.length; i++) {
            const x = coords[i][0];
            const y = coords[i][1];
            c.push([x, y]);
        }
        this.nodeCoords = c;
        this.initGeometry();
        this.qpCoords = [
            [-0.77459667, -0.77459667],
            [-0.77459667, 0],
            [-0.77459667, 0.77459667],
            [0, -0.77459667],
            [0, 0],
            [0, 0.77459667],
            [0.77459667, -0.77459667],
            [0.77459667, 0],
            [0.77459667, 0.77459667],
        ];
        this.qpWeights = [
            0.30864198, 0.49382716, 0.30864198, 0.49382716, 0.79012346,
            0.49382716, 0.30864198, 0.49382716, 0.30864198,
        ];
    }

    shape_values(_coord) {
        let x = _coord[0]
        let y = _coord[1]
        return [
            0.25 * (1.0 - x) * (1.0 - y),
            0.25 * (1.0 + x) * (1.0 - y),
            0.25 * (1.0 + x) * (1.0 + y),
            0.25 * (1.0 - x) * (1.0 + y),
        ];
    }

    shape_gradients(_coord) {
        let x = _coord[0]
        let y = _coord[1]
        return [
            [-0.25 * (1.0 - y), -0.25 * (1.0 - x)],
            [0.25 * (1.0 - y), -0.25 * (1.0 + x)],
            [0.25 * (1.0 + y), 0.25 * (1.0 + x)],
            [-0.25 * (1.0 + y), 0.25 * (1.0 - x)],
        ];
    }

    transformation(geo) {
        this._domain = [];
        this.modifier = [];
        this.lineDomain = [];
        this.lineModifier = [];
        const qpCoords = [];
        for (let i = 0; i < geo.attributes.position.count; i++) {
            const x = geo.attributes.position.getX(i);
            const y = geo.attributes.position.getY(i);
            const z = geo.attributes.position.getZ(i);
            qpCoords.push([x * 2, y * 2, 2 * z]);
            this._domain.push([x * 2, y * 2]);
            this.modifier.push([0.0, 0.0, (this.thick / 20) * (z + 0.5)]);
        }
        for (let i = 0; i < this.lineGeometry.attributes.position.count; i++) {
            const x = this.lineGeometry.attributes.position.getX(i);
            const y = this.lineGeometry.attributes.position.getY(i);
            const z = this.lineGeometry.attributes.position.getZ(i);
            this.lineDomain.push([x * 2, y * 2]);
            this.lineModifier.push([0.0, 0.0, (this.thick / 20) * (z + 0.5)]);
        }
        return qpCoords;
    }

    initGeometry() {
        this.geometry = new THREE.BoxGeometry(
            1,
            1,
            1,
            2 ** (this.res - 1),
            2 ** (this.res - 1),
            1
        );
        this.lineGeometry = new THREE.EdgesGeometry(this.geometry);
        this.domain = this.transformation(this.geometry);
        this.colors = Array(this.modifier.length).fill(0.0);
        this.geometry.setAttribute(
            "color",
            new THREE.Float32BufferAttribute(
                new Array(this.modifier.length * 3),
                3
            )
        );
    }
}

class LinealO2 extends Lineal {
    constructor(coords, conns, dofIDs, thick) {
        super(coords, conns, dofIDs, thick);
        this.type = "L2V";
    }

    shape_values(_coord) {
        let x = _coord[0]
        return [
            0.5 * (1.0 - x) - 0.5 * (1.0 - x * x),
            1.0 - x * x,
            0.5 * (1.0 + x) - 0.5 * (1.0 - x * x),
        ];
    }

    shape_gradients(_coord) {
        let x = _coord[0]
        return [[-0.5 + x], [-2.0 * x], [0.5 + x]];
    }
}

class TetrahedralO2 extends Tetrahedral {
    constructor(coords, conns, dofIDs) {
        super(coords, conns, dofIDs);
        this.type = "TE2V";
    }

    shape_values(_coord) {
        let x = _coord[0];
        let y = _coord[1];
        let z = _coord[2];
        let L1 = 1 - x - y - z;
        let L2 = x;
        let L3 = y;
        let L4 = z;
        return [
            L1 * (2 * L1 - 1),
            L2 * (2 * L2 - 1),
            L3 * (2 * L3 - 1),
            L4 * (2 * L4 - 1),
            4 * L1 * L2,
            4 * L2 * L3,
            4 * L3 * L1,
            4 * L1 * L4,
            4 * L2 * L4,
            4 * L3 * L4,
        ];
    }

    shape_gradients(_coord) {
        let x = _coord[0];
        let y = _coord[1];
        let z = _coord[2];
        return [
            [4 * x + 4 * y + 4 * z - 3, 4 * x + 4 * y + 4 * z - 3, 4 * x + 4 * y + 4 * z - 3,],
            [4 * x - 1, 0, 0],
            [0, 4 * y - 1, 0],
            [0, 0, 4 * z - 1],
            [-8 * x - 4 * y - 4 * z + 4, -4 * x, -4 * x],
            [4 * y, 4 * x, 0],
            [-4 * y, -4 * x - 8 * y - 4 * z + 4, -4 * y],
            [-4 * z, -4 * z, -4 * x - 4 * y - 8 * z + 4],
            [4 * z, 0, 4 * x],
            [0, 4 * z, 4 * y],
        ];
    }
}

class BrickO2 extends Brick {
    constructor(coords, conns, dofIDs) {
        super(coords, conns, dofIDs);
        this.type = "B2V";
    }

    shape_values(_coord) {
        let x = _coord[0];
        let y = _coord[1];
        let z = _coord[2];
        return [
            0.125 * ((1 - x) * (1 - y) * (1 - z) * (-x - y - z - 2)),
            0.125 * ((1 + x) * (1 - y) * (1 - z) * (x - y - z - 2)),
            0.125 * ((1 + x) * (1 + y) * (1 - z) * (x + y - z - 2)),
            0.125 * ((1 - x) * (1 + y) * (1 - z) * (-x + y - z - 2)),
            0.125 * ((1 - x) * (1 - y) * (1 + z) * (-x - y + z - 2)),
            0.125 * ((1 + x) * (1 - y) * (1 + z) * (x - y + z - 2)),
            0.125 * ((1 + x) * (1 + y) * (1 + z) * (x + y + z - 2)),
            0.125 * ((1 - x) * (1 + y) * (1 + z) * (-x + y + z - 2)),
            0.125 * (2 * (1 - x ** 2) * (1 - y) * (1 - z)),
            0.125 * (2 * (1 + x) * (1 - y ** 2) * (1 - z)),
            0.125 * (2 * (1 - x ** 2) * (1 + y) * (1 - z)),
            0.125 * (2 * (1 - x) * (1 - y ** 2) * (1 - z)),
            0.125 * (2 * (1 - x) * (1 - y) * (1 - z ** 2)),
            0.125 * (2 * (1 + x) * (1 - y) * (1 - z ** 2)),
            0.125 * (2 * (1 + x) * (1 + y) * (1 - z ** 2)),
            0.125 * (2 * (1 - x) * (1 + y) * (1 - z ** 2)),
            0.125 * (2 * (1 - x ** 2) * (1 - y) * (1 + z)),
            0.125 * (2 * (1 + x) * (1 - y ** 2) * (1 + z)),
            0.125 * (2 * (1 - x ** 2) * (1 + y) * (1 + z)),
            0.125 * (2 * (1 - x) * (1 - y ** 2) * (1 + z)),
        ];
    }

    shape_gradients(_coord) {
        let x = _coord[0];
        let y = _coord[1];
        let z = _coord[2];
        return [
            [
                (1 / 8) *
                (-(1 - x) * (1 - y) * (1 - z) +
                    (1 - z) * (y - 1) * (-x - y - z - 2)),
                (1 / 8) *
                (-(1 - x) * (1 - y) * (1 - z) +
                    (1 - z) * (x - 1) * (-x - y - z - 2)),
                (1 / 8) *
                (-(1 - x) * (1 - y) * (1 - z) -
                    (1 - x) * (1 - y) * (-x - y - z - 2)),
            ],
            [
                (1 / 8) *
                ((1 - y) * (1 - z) * (x + 1) +
                    (1 - y) * (1 - z) * (x - y - z - 2)),
                (1 / 8) *
                (-(1 - y) * (1 - z) * (x + 1) +
                    (1 - z) * (-x - 1) * (x - y - z - 2)),
                (1 / 8) *
                (-(1 - y) * (1 - z) * (x + 1) -
                    (1 - y) * (x + 1) * (x - y - z - 2)),
            ],
            [
                (1 / 8) *
                ((1 - z) * (x + 1) * (y + 1) +
                    (1 - z) * (y + 1) * (x + y - z - 2)),
                (1 / 8) *
                ((1 - z) * (x + 1) * (y + 1) +
                    (1 - z) * (x + 1) * (x + y - z - 2)),
                (1 / 8) *
                (-(1 - z) * (x + 1) * (y + 1) -
                    (x + 1) * (y + 1) * (x + y - z - 2)),
            ],
            [
                (1 / 8) *
                (-(1 - x) * (1 - z) * (y + 1) +
                    (1 - z) * (-y - 1) * (-x + y - z - 2)),
                (1 / 8) *
                ((1 - x) * (1 - z) * (y + 1) +
                    (1 - x) * (1 - z) * (-x + y - z - 2)),
                (1 / 8) *
                (-(1 - x) * (1 - z) * (y + 1) -
                    (1 - x) * (y + 1) * (-x + y - z - 2)),
            ],
            [
                (1 / 8) *
                (-(1 - x) * (1 - y) * (z + 1) +
                    (1 - y) * (-z - 1) * (-x - y + z - 2)),
                (1 / 8) *
                (-(1 - x) * (1 - y) * (z + 1) -
                    (1 - x) * (z + 1) * (-x - y + z - 2)),
                (1 / 8) *
                ((1 - x) * (1 - y) * (z + 1) +
                    (1 - x) * (1 - y) * (-x - y + z - 2)),
            ],
            [
                (1 / 8) *
                ((1 - y) * (x + 1) * (z + 1) +
                    (1 - y) * (z + 1) * (x - y + z - 2)),
                (1 / 8) *
                (-(1 - y) * (x + 1) * (z + 1) -
                    (x + 1) * (z + 1) * (x - y + z - 2)),
                (1 / 8) *
                ((1 - y) * (x + 1) * (z + 1) +
                    (1 - y) * (x + 1) * (x - y + z - 2)),
            ],
            [
                (1 / 8) *
                ((x + 1) * (y + 1) * (z + 1) +
                    (y + 1) * (z + 1) * (x + y + z - 2)),
                (1 / 8) *
                ((x + 1) * (y + 1) * (z + 1) +
                    (x + 1) * (z + 1) * (x + y + z - 2)),
                (1 / 8) *
                ((x + 1) * (y + 1) * (z + 1) +
                    (x + 1) * (y + 1) * (x + y + z - 2)),
            ],
            [
                (1 / 8) *
                (-(1 - x) * (y + 1) * (z + 1) -
                    (y + 1) * (z + 1) * (-x + y + z - 2)),
                (1 / 8) *
                ((1 - x) * (y + 1) * (z + 1) +
                    (1 - x) * (z + 1) * (-x + y + z - 2)),
                (1 / 8) *
                ((1 - x) * (y + 1) * (z + 1) +
                    (1 - x) * (y + 1) * (-x + y + z - 2)),
            ],
            [
                (1 / 8) * (-4 * x * (1 - y) * (1 - z)),
                (1 / 8) * ((2 - 2 * x ** 2) * (z - 1)),
                (1 / 8) * ((2 - 2 * x ** 2) * (y - 1)),
            ],
            [
                (1 / 8) * (2 * (1 - y ** 2) * (1 - z)),
                (1 / 8) * (-2 * y * (1 - z) * (2 * x + 2)),
                (1 / 8) * ((2 * x + 2) * (y ** 2 - 1)),
            ],
            [
                (1 / 8) * (-4 * x * (1 - z) * (y + 1)),
                (1 / 8) * ((1 - z) * (2 - 2 * x ** 2)),
                (1 / 8) * ((2 - 2 * x ** 2) * (-y - 1)),
            ],
            [
                (1 / 8) * (-2 * (1 - y ** 2) * (1 - z)),
                (1 / 8) * (-2 * y * (1 - z) * (2 - 2 * x)),
                (1 / 8) * ((2 - 2 * x) * (y ** 2 - 1)),
            ],
            [
                (1 / 8) * (-2 * (1 - y) * (1 - z ** 2)),
                (1 / 8) * ((2 - 2 * x) * (z ** 2 - 1)),
                (1 / 8) * (-2 * z * (1 - y) * (2 - 2 * x)),
            ],
            [
                (1 / 8) * (2 * (1 - y) * (1 - z ** 2)),
                (1 / 8) * ((2 * x + 2) * (z ** 2 - 1)),
                (1 / 8) * (-2 * z * (1 - y) * (2 * x + 2)),
            ],
            [
                (1 / 8) * (2 * (1 - z ** 2) * (y + 1)),
                (1 / 8) * ((1 - z ** 2) * (2 * x + 2)),
                (1 / 8) * (-2 * z * (2 * x + 2) * (y + 1)),
            ],
            [
                (1 / 8) * (-2 * (1 - z ** 2) * (y + 1)),
                (1 / 8) * ((1 - z ** 2) * (2 - 2 * x)),
                (1 / 8) * (-2 * z * (2 - 2 * x) * (y + 1)),
            ],
            [
                (1 / 8) * (-4 * x * (1 - y) * (z + 1)),
                (1 / 8) * ((2 - 2 * x ** 2) * (-z - 1)),
                (1 / 8) * ((1 - y) * (2 - 2 * x ** 2)),
            ],
            [
                (1 / 8) * (2 * (1 - y ** 2) * (z + 1)),
                (1 / 8) * (-2 * y * (2 * x + 2) * (z + 1)),
                (1 / 8) * ((1 - y ** 2) * (2 * x + 2)),
            ],
            [
                (1 / 8) * (-4 * x * (y + 1) * (z + 1)),
                (1 / 8) * ((2 - 2 * x ** 2) * (z + 1)),
                (1 / 8) * ((2 - 2 * x ** 2) * (y + 1)),
            ],
            [
                (1 / 8) * (-2 * (1 - y ** 2) * (z + 1)),
                (1 / 8) * (-2 * y * (2 - 2 * x) * (z + 1)),
                (1 / 8) * ((1 - y ** 2) * (2 - 2 * x)),
            ],
        ];
    }
}

class TriangularO2 extends Triangular {
    constructor(coords, conns, dofIDs, thick) {
        super(coords, conns, dofIDs, thick);
        this.type = "T2V";
        let c = [coords[0], coords[1], coords[2]];
        let gdl = [-1, -1, -1];
        this.auxE = new Triangular(c, gdl, 0.2);
    }

    shape_values(_coord) {
        let x = _coord[0]
        let y = _coord[1]
        return [
            2.0 * (x + y - 1.0) * (x + y - 0.5),
            2.0 * x * (x - 0.5),
            2.0 * y * (y - 0.5),
            -4.0 * (x + y - 1.0) * x,
            4.0 * x * y,
            -4.0 * y * (x + y - 1.0),
        ];
    }

    shape_gradients(_coord) {
        let x = _coord[0]
        let y = _coord[1]
        return [
            [4.0 * x + 4.0 * y - 3.0, 4.0 * y + 4.0 * x - 3.0],
            [4.0 * x - 1.0, 0.0],
            [0.0, 4.0 * y - 1.0],
            [-8.0 * x - 4.0 * (y - 1.0), -4.0 * x],
            [4.0 * y, 4.0 * x],
            [-4.0 * y, -8.0 * y - 4.0 * x + 4.0],
        ];
    }

    inverseMapping(xo, giveP) {
        return this.auxE.inverseMapping(xo, giveP);
    }
}

class QuadrilateralO2 extends Quadrilateral {
    constructor(coords, conns, dofIDs, thick) {
        super(coords, conns, dofIDs, thick);
        this.type = "C2V";
    }

    shape_values(_coord) {
        let x = _coord[0]
        let y = _coord[1]
        return [
            0.25 * (1.0 - x) * (1.0 - y) * (-1.0 - x - y),
            0.25 * (1.0 + x) * (1.0 - y) * (-1.0 + x - y),
            0.25 * (1.0 + x) * (1.0 + y) * (-1.0 + x + y),
            0.25 * (1.0 - x) * (1.0 + y) * (-1.0 - x + y),
            0.5 * (1.0 - x ** 2.0) * (1.0 - y),
            0.5 * (1.0 + x) * (1.0 - y ** 2.0),
            0.5 * (1.0 - x ** 2.0) * (1.0 + y),
            0.5 * (1.0 - x) * (1.0 - y ** 2.0),
        ];
    }

    shape_gradients(_coord) {
        let x = _coord[0]
        let y = _coord[1]
        return [
            [
                -0.25 * (y - 1.0) * (2.0 * x + y),
                -0.25 * (x - 1.0) * (2.0 * y + x),
            ],
            [
                -0.25 * (y - 1.0) * (2.0 * x - y),
                0.25 * (x + 1.0) * (2.0 * y - x),
            ],
            [
                0.25 * (y + 1.0) * (2.0 * x + y),
                0.25 * (x + 1.0) * (2.0 * y + x),
            ],
            [
                0.25 * (y + 1.0) * (2.0 * x - y),
                -0.25 * (x - 1.0) * (2.0 * y - x),
            ],
            [(y - 1.0) * x, 0.5 * (x ** 2.0 - 1.0)],
            [-0.5 * (y ** 2.0 - 1.0), -y * (x + 1.0)],
            [-(y + 1.0) * x, -0.5 * (x ** 2.0 - 1.0)],
            [0.5 * (y ** 2.0 - 1.0), y * (x - 1.0)],
        ];
    }
}

export {
    Brick,
    BrickO2,
    Tetrahedral,
    TetrahedralO2,
    Lineal,
    Triangular,
    TriangularO2,
    Quadrilateral,
    QuadrilateralO2,
    LinealO2,
    Element,
    Element3D,
};
