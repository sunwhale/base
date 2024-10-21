# -*- coding: utf-8 -*-
"""

"""


def insert_list_at_index(A: list, B: list, index: int) -> None:
    for i in range(len(A)):
        B.insert(index + i, A[i])


def add_phasefield_layer(inp_filepath: str,
                         dof: int,
                         properties: int,
                         variables: int,
                         properties_str: str) -> None:
    with open(inp_filepath, 'r') as file:
        lines = file.readlines()

    elements = {}
    element_type = 'NONE'
    element_id_max = 1
    element_end_index = 0

    reading_elements = False

    for line_id, line in enumerate(lines):
        line = line.strip()
        if line.startswith('*Element') and line.split(',')[0].replace(' ', '') == '*Element':
            reading_elements = True
            type_start_index = line.find('type=')
            if type_start_index != -1:
                type_start_index += len('type=')
                type_end_index = line.find(',', type_start_index)
                if type_end_index == -1:
                    element_type = line[type_start_index:].strip()
                else:
                    element_type = line[type_start_index:type_end_index].strip()
            elements[element_type] = []
            continue
        elif reading_elements and '*' in line:
            reading_elements = False
            element_end_index = line_id

        if reading_elements and ',' in line:
            element_data = line.split(',')
            element_id = int(element_data[0])
            if element_id > element_id_max:
                element_id_max = element_id
            element_nodes = list(map(int, element_data[1:]))
            elements[element_type].append((element_id, element_nodes))

    phasefield_elements = {}

    for element_type, element_data in elements.items():
        if element_type in ['CPS4', 'CPE4', 'CPE4RT']:
            phasefield_elements['QUAD4'] = [(a[0] + element_id_max, a[1]) for a in element_data]
            dim = 2
        if element_type == 'CPS3' or element_type == 'CPE3':
            phasefield_elements['TRI3'] = [(a[0] + element_id_max, a[1]) for a in element_data]
            dim = 2
        if element_type == 'C3D8' or element_type == 'C3D8R':
            phasefield_elements['HEX8'] = [(a[0] + element_id_max, a[1]) for a in element_data]
            dim = 3

    phasefield_lines = []

    for element_type, element_data in phasefield_elements.items():
        phasefield_lines.append(
            f"*User element, nodes={len(element_data[0][1])}, type={element_type}, properties={properties}, coordinates={dim}, variables={variables}\n")
        phasefield_lines.append(f"{dof}\n")
        phasefield_lines.append(f"*Uel property, elset=ESET-{element_type}\n")
        phasefield_lines.append(f"{properties_str}\n")
        for element in element_data:
            line = f'{element[0]}, '
            for e in element[1]:
                line += f'{e}, '
            line = line[:-2] + '\n'
            phasefield_lines.append(line)

    for element_type, element_data in phasefield_elements.items():
        phasefield_lines.append(f"*Elset, elset=ESET-{element_type}\n")
        line = ''
        for i, element in enumerate(element_data):
            line += f'{element[0]}, '
            if (i + 1) % 10 == 0:
                line = line[:-2] + '\n'
                phasefield_lines.append(line)
                line = ''
        if line != '':
            line = line[:-2] + '\n'
            phasefield_lines.append(line)

    insert_list_at_index(phasefield_lines, lines, element_end_index)

    with open(inp_filepath[:-4] + '_uel.inp', 'w') as file:
        for line_id, line in enumerate(lines):
            file.write(line)


if __name__ == "__main__":
    add_phasefield_layer(inp_filepath='rectangle_hole_quad4.inp',
                         dof=4,
                         properties=3,
                         variables=12,
                         properties_str='<LC>, <GC>, <THICK>')
