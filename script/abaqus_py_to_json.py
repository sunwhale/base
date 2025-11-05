import re
import ast
import json


def parse_value(node):
    """安全地解析AST节点值，处理特殊字符串和一元操作"""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Name):
        # 处理类似ON, OFF, JOHNSON_COOK等标识符
        return node.id
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.UnaryOp):
        # 处理一元操作(如负数)
        if isinstance(node.op, ast.USub):  # 负号
            operand = parse_value(node.operand)
            if isinstance(operand, (int, float)):
                return -operand
            elif isinstance(operand, str):
                return f"-{operand}"
        elif isinstance(node.op, ast.UAdd):  # 正号(通常不需要处理)
            return parse_value(node.operand)
    elif isinstance(node, ast.Tuple):
        return tuple(parse_value(e) for e in node.elts)
    elif isinstance(node, ast.List):
        return [parse_value(e) for e in node.elts]
    elif isinstance(node, ast.NameConstant):  # Python 3.7及以下版本
        return node.value
    else:
        raise ValueError(f"Unsupported node type: {type(node).__name__}")


def parse_material_code(code):
    material_dict = {}

    lines = [line.strip() for line in code.split('\n') if line.strip()]

    for line in lines:
        # 处理嵌套属性
        if '.' in line.split('(')[0]:
            parts = line.split('.')
            main_key = parts[0]
            sub_key = parts[1].split('(')[0]
        else:
            main_key = line.split('(')[0]
            sub_key = None

        # 提取参数部分
        args_str = line[line.find('(') + 1:line.rfind(')')]

        try:
            # 构造AST
            func_str = f"f({args_str})"  # 使用虚拟函数名
            tree = ast.parse(func_str, mode='eval')

            args = []
            kwargs = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # 处理位置参数
                    for arg in node.args:
                        args.append(parse_value(arg))

                    # 处理关键字参数
                    for kw in node.keywords:
                        kwargs[kw.arg] = parse_value(kw.value)
                    break
        except Exception as e:
            raise ValueError(f"Failed to parse line: {line}\nError: {str(e)}") from e

        # 构建参数字典
        params = {}
        if args:
            # 处理table参数的特殊情况
            if len(args) == 1 and isinstance(args[0], (list, tuple)):
                # 将元组转换为列表
                params['table'] = [list(item) if isinstance(item, tuple) else item
                                   for item in args]
            else:
                params['args'] = args
        if kwargs:
            params.update(kwargs)

        # 添加到字典
        if sub_key is None:
            material_dict[main_key] = params
        else:
            if main_key not in material_dict:
                material_dict[main_key] = {}
            material_dict[main_key][sub_key] = params

    return material_dict


def dump_json(file_path, data, encoding='utf-8'):
    """
    Write JSON data to file.
    """
    with open(file_path, 'w', encoding=encoding) as f:
        return json.dump(data, f, ensure_ascii=False)


# 测试代码
# input_code = """
# Density(table=((4.44e-09,),))
# Elastic(temperatureDependency=ON, table=((112000.0, 0.34, 20.0),))
# Expansion(table=((9.4e-06, 100.0),), zero=20.0, temperatureDependency=ON)
# InelasticHeatFraction()
# Plastic(hardening=JOHNSON_COOK, scaleStress=None, table=((875.0, 793.0, 0.385, 0.71, 1560.0, 20.0),))
# plastic.RateDependent(type=JOHNSON_COOK, table=((1.0, 0.1), ))
# Conductivity(temperatureDependency=ON, table=((6.8, 20.0),))
# SpecificHeat(temperatureDependency=ON, table=((565000000.0, 20.0),))
# JohnsonCookDamageInitiation(table=((-0.09, 0.27, -0.48, 0.014, 3.87, 1560.0, 20.0, 1.0),))
# johnsonCookDamageInitiation.DamageEvolution(type=DISPLACEMENT, table=((1.0,),))
# """
# input_code = """
# Density(table=((1.485e-08,),))
# Elastic(table=((640000.0, 0.22),))
# Expansion(table=((4.7e-06,),))
# InelasticHeatFraction()
# Conductivity(table=((79.6,),))
# SpecificHeat(table=((176000000.0,),))
# """
# input_code = """
# TangentialBehavior(formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF, pressureDependency=OFF, temperatureDependency=OFF, dependencies=0, table=((0.4,),), shearStressLimit=None, maximumElasticSlip=FRACTION, fraction=0.005, elasticSlipStiffness=None)
# NormalBehavior(pressureOverclosure=HARD, allowSeparation=ON, constraintEnforcementMethod=DEFAULT)
# HeatGeneration(conversionFraction=1.0, secondaryFraction=0.5)
# """
# 九院
# input_code = """
# Density(table=((1.8e-09, ), ))
# Viscoelastic(domain=TIME, time=PRONY, table=((3.5626, 889.458, 0.0015), (1.9001, 474.4, 0.0334), (1.489, 371.75, 0.7342), (0.6154, 153.641667, 16.1529), (0.7216, 180.15, 355.3628)))
# """
# input_code = """
# Density(table=((1e-09, ), ))
# Viscoelastic(domain=TIME, time=PRONY, table=((0.78109, 49.69185, 0.009746), (0.171674, 49.69185, 0.062089), (0.042971, 49.69185, 0.473872)))
# """
# input_code = """
# Density(table=((1.1e-09, ), ))
# Elastic(table=((30.0, 0.495), ))
# Expansion(table=((8.6e-05, ), ))
# """
input_code = """
Density(table=((1.6e-09, ), ))
Elastic(type=ENGINEERING_CONSTANTS, table=((134000.0, 9650.0, 9650.0, 0.28, 0.02, 0.34, 6500.0, 3400.0, 6500.0), ))
Expansion(table=((1.1e-06, ), ))
"""
material_dict = parse_material_code(input_code)
dump_json('material.json', material_dict)
from pprint import pprint

pprint(material_dict)
