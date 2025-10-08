import win32com.client as win32
import pythoncom


def check_available_com_objects():
    pythoncom.CoInitialize()

    # 测试Word是否可用
    word = win32.Dispatch("Word.Application")
    print("✓ Word.Application 可用")

    # 测试其他可能的数学软件
    com_objects = [
        "Equation.DSMT4",  # Word公式编辑器
        "Mathematica",  # Mathematica
        "MathType.Application",  # Maple
    ]

    test_obj = win32.Dispatch("MathType.Application")




if __name__ == "__main__":
    check_available_com_objects()