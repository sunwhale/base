import {Color} from "../build/three.module.js";

class Legend {
    constructor(colormap, count = 32) {
        this.legend = [];
        this.map = [];
        this.n = 0;
        this.minV = 0;
        this.maxV = 1;

        this.setColorMap(colormap, count);
    }

    set(value) {
        if (value.isLegend === true) {
            this.copy(value);
        }

        return this;
    }

    setMin(min) {
        this.minV = min;

        return this;
    }

    setMax(max) {
        this.maxV = max;

        return this;
    }

    setColorMap(colormap, count = 32) {
        this.map = ColorMapKeywords[colormap] || ColorMapKeywords["彩虹色"];
        this.n = count;

        const step = 1.0 / this.n;

        this.legend.length = 0;

        for (let i = 0; i <= 1; i += step) {
            for (let j = 0; j < this.map.length - 1; j++) {
                if (i >= this.map[j][0] && i < this.map[j + 1][0]) {
                    const min = this.map[j][0];
                    const max = this.map[j + 1][0];

                    const minColor = new Color(this.map[j][1]);
                    const maxColor = new Color(this.map[j + 1][1]);

                    const color = minColor.lerp(
                        maxColor,
                        (i - min) / (max - min)
                    );

                    this.legend.push(color);
                }
            }
        }

        return this;
    }

    copy(legend) {
        this.legend = legend.legend;
        this.map = legend.map;
        this.n = legend.n;
        this.minV = legend.minV;
        this.maxV = legend.maxV;

        return this;
    }

    getColor(value) {
        if (value <= this.minV) {
            value = this.minV;
        } else if (value >= this.maxV) {
            value = this.maxV;
        }

        // 如果变量的最大和最小值相同，则取标尺的中间颜色
        if (this.maxV - this.minV === 0) {
            value = 0.5;
        } else{
            value = (value - this.minV) / (this.maxV - this.minV);
        }

        let colorPosition = Math.round(value * this.n);

        if (colorPosition === this.n) colorPosition -= 1;

        return this.legend[colorPosition];
    }

    addColorMap(name, arrayOfColors) {
        ColorMapKeywords[name] = arrayOfColors;

        return this;
    }

    createCanvas() {
        const canvas = document.createElement("canvas");
        canvas.width = 256;
        canvas.height = 512;
        this.updateCanvas(canvas);

        return canvas;
    }

    updateCanvas(canvas) {
        const ctx = canvas.getContext("2d", {alpha: true});

        ctx.clearRect(0, 0, canvas.width, canvas.height)

        const up_margin = 20

        const imageData = ctx.getImageData(0, 0, up_margin, canvas.height - up_margin * 2);

        const data = imageData.data;

        let k = 0;

        const step = 1.0 / canvas.height / up_margin;

        for (let i = 1; i >= 0; i -= step) {
            for (let j = this.map.length - 1; j >= 0; j--) {
                if (i < this.map[j][0] && i >= this.map[j - 1][0]) {
                    const min = this.map[j - 1][0];
                    const max = this.map[j][0];

                    const minColor = new Color(this.map[j - 1][1]);
                    const maxColor = new Color(this.map[j][1]);

                    const color = minColor.lerp(
                        maxColor,
                        (i - min) / (max - min)
                    );

                    data[k * 4] = Math.round(color.r * 255);
                    data[k * 4 + 1] = Math.round(color.g * 255);
                    data[k * 4 + 2] = Math.round(color.b * 255);
                    data[k * 4 + 3] = 255;

                    k += 1;
                }
            }
        }

        let font_size = 32
        let segment = 8

        ctx.font = '32px Arial';
        ctx.fillStyle = 'white';

        let y = font_size
        let value = this.maxV
        for (let i = 0; i < segment + 1; i++) {
            ctx.fillText(value.toPrecision(4), font_size, y);
            y += (canvas.height - 2 * up_margin) / segment
            value -= (this.maxV - this.minV) / segment
        }

        ctx.putImageData(imageData, 0, up_margin);

        return canvas;
    }
}

Legend.prototype.isLegend = true;

const ColorMapKeywords = {
    "彩虹色": [
        [0.0, 0x0000ff],
        [0.2, 0x00ffff],
        [0.5, 0x00ff00],
        [0.8, 0xffff00],
        [1.0, 0xff0000],
    ],
    "冷热图": [
        [0.0, 0x3c4ec2],
        [0.2, 0x9bbcff],
        [0.5, 0xdcdcdc],
        [0.8, 0xf6a385],
        [1.0, 0xb40426],
    ],
    "热力图": [
        [0.0, 0x000000],
        [0.2, 0x780000],
        [0.5, 0xe63200],
        [0.8, 0xffff00],
        [1.0, 0xffffff],
    ],
    "灰度图": [
        [0.0, 0x000000],
        [0.2, 0x404040],
        [0.5, 0x7f7f80],
        [0.8, 0xbfbfbf],
        [1.0, 0xffffff],
    ],
};

export {Legend, ColorMapKeywords};
