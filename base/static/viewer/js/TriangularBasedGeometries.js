import {add, cross, dot, multiplyScalar, subtraction} from "./math.js";

class Triangle {
    constructor(coords) {
        this.coords = coords || [
            [0.0, 0.0, 0.5],
            [1.0, 0.0, 0.5],
            [0.0, 1.0, 0.5],
        ];
        let l1 = subtraction(coords[1], coords[0]); // 1号边向量
        let l2 = subtraction(coords[2], coords[0]); // 2号边向量
        let crossNormal = cross(l1, l2);
        let crossNormalMag = dot(crossNormal, crossNormal) ** 0.5;
        this.normal = multiplyScalar(crossNormal, 1 / crossNormalMag); // 三角形法向量
        this.divided = false;
        this.children = [];
    }

    extrude(h, a) {
        // 法向拉伸
        let newCoordsUp = [];
        for (const c of this.coords) {
            let up = add(multiplyScalar(this.normal, h / 2), c);
            newCoordsUp.push(up);
        }
        let newCoordsDown = [];
        for (const c of this.coords) {
            let down = add(multiplyScalar(this.normal, -h / 2), c);
            newCoordsDown.push(down);
        }
        let newCoordsInter = [];
        newCoordsInter.push(
            newCoordsUp[0],
            newCoordsDown[0],
            newCoordsUp[1]
        );
        newCoordsInter.push(
            newCoordsDown[0],
            newCoordsDown[1],
            newCoordsUp[1]
        );
        newCoordsInter.push(
            newCoordsUp[1],
            newCoordsDown[1],
            newCoordsUp[2]
        );
        newCoordsInter.push(
            newCoordsDown[1],
            newCoordsDown[2],
            newCoordsUp[2]
        );

        if (!a) {
            newCoordsInter.push(
                newCoordsUp[2],
                newCoordsDown[2],
                newCoordsUp[0]
            );
            newCoordsInter.push(
                newCoordsDown[2],
                newCoordsDown[0],
                newCoordsUp[0]
            );
        }

        return [
            ...[...newCoordsUp].reverse(),
            ...newCoordsDown,
            ...newCoordsInter,
        ];
    }

    divide(n = 1) {
        if (n === 0) {
            return;
        }

        let trianglesToDivide = [this];

        while (n > 0) {
            const newTriangles = [];

            for (const triangle of trianglesToDivide) {
                triangle.subdivide();
                newTriangles.push(...triangle.children);
            }

            trianglesToDivide = newTriangles;
            n--;
        }
    }

    subdivide() {
        // 将1个三角形从各边中点拆分为4个
        this.divided = true;
        const c = this.coords;
        let mid1 = this.calculateMidPoint(c[0], c[1]);
        let mid2 = this.calculateMidPoint(c[0], c[2]);
        let mid3 = this.calculateMidPoint(c[1], c[2]);

        let Ta = new Triangle([c[0], mid1, mid2]);
        let Tb = new Triangle([mid3, mid2, mid1]);
        let Tc = new Triangle([mid1, c[1], mid3]);
        let Td = new Triangle([mid2, mid3, c[2]]);
        this.children = [Ta, Tb, Tc, Td];
    }

    calculateMidPoint(p1, p2) {
        return [
            p2[0] / 2 + p1[0] / 2,
            p2[1] / 2 + p1[1] / 2,
            p2[2] / 2 + p1[2] / 2,
        ];
    }

    giveCoords(reverse = false) {
        let result = [];
        if (!this.divided) {
            if (reverse) {
                return [...this.coords].reverse();
            } else {
                return this.coords;
            }
        }
        for (const ch of this.children) {
            result = result.concat(ch.giveCoords(reverse));
        }
        return result;
    }
}

class Prism {
    constructor() {
        this.topTriang = new Triangle([
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
        ]);
        let ct = this.topTriang.coords;
        this.bottomTriang = new Triangle([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]);
        let cb = this.bottomTriang.coords;
        this.sideTriangles = [
            cb[2],
            cb[0],
            ct[2],
            ct[2],
            cb[0],
            ct[0],
            ct[2],
            cb[1],
            cb[2],
            ct[2],
            ct[1],
            cb[1],
            cb[0],
            cb[1],
            ct[1],
            ct[0],
            cb[0],
            ct[1],
        ];
    }

    giveCoords() {
        let coords = this.topTriang.giveCoords();
        coords = coords.concat(this.bottomTriang.giveCoords(true));
        coords = coords.concat(this.sideTriangles);
        return coords.flat();
    }

    divide(n) {
        this.topTriang.divide(n);
        this.bottomTriang.divide(n);
        this.sideTriangles = [];
        let h = 1 / 2 ** n;
        for (let i = 0; i < 2 ** n; i++) {
            const left = i * h;
            const right = (i + 1) * h;
            const t1 = [
                [left, 0.0, 1.0],
                [left, 0.0, 0.0],
                [right, 0.0, 1.0],
            ];
            const t2 = [
                [left, 0.0, 0.0],
                [right, 0.0, 0.0],
                [right, 0.0, 1.0],
            ];

            const t3 = [
                [0.0, left, 1.0],
                [0.0, right, 1.0],
                [0.0, left, 0.0],
            ];
            const t4 = [
                [0.0, left, 0.0],
                [0.0, right, 1.0],
                [0.0, right, 0.0],
            ];

            const t5 = [
                [left, 1 - left, 1.0],
                [right, 1 - right, 0.0],
                [left, 1 - left, 0.0],
            ];
            const t6 = [
                [left, 1 - left, 1.0],
                [right, 1 - right, 1.0],
                [right, 1 - right, 0.0],
            ];
            this.sideTriangles = this.sideTriangles.concat(t1);
            this.sideTriangles = this.sideTriangles.concat(t2);
            this.sideTriangles = this.sideTriangles.concat(t3);
            this.sideTriangles = this.sideTriangles.concat(t4);
            this.sideTriangles = this.sideTriangles.concat(t5);
            this.sideTriangles = this.sideTriangles.concat(t6);
        }
    }
}

class Tet {
    constructor() {
        this.topTriang = new Triangle([
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]);
        this.bottomTriang = new Triangle([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]);

        this.leftTriang = new Triangle([
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0],
        ]);
        this.rightTriang = new Triangle([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1],
        ]);
    }

    giveCoords() {
        let coords = this.topTriang.giveCoords();
        coords = coords.concat(this.bottomTriang.giveCoords(true));
        coords = coords.concat(this.leftTriang.giveCoords());
        coords = coords.concat(this.rightTriang.giveCoords());
        return coords.flat();
    }

    divide(n) {
        this.topTriang.divide(n);
        this.bottomTriang.divide(n);
        this.leftTriang.divide(n);
        this.rightTriang.divide(n);
    }
}

export {Triangle, Tet, Prism};
