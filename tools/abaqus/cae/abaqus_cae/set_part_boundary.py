# -*- coding: mbcs -*-
try:
    from abaqus import *
    from abaqusConstants import *
    from caeModules import *
    from driverUtils import executeOnCaeStartup
except ImportError:
    print("Without abaqus environment.")


def set_part_boundary(model_name='Model-1',
                      part_name='PART-1',
                      dimension=2,
                      tol=1e-6):
    try:
        p = mdb.models[model_name].parts[part_name]

        v_x = []
        v_y = []
        v_z = []
        for v in p.vertices:
            v_x.append(v.pointOn[0][0])
            v_y.append(v.pointOn[0][1])
            v_z.append(v.pointOn[0][2])

        x0 = min(v_x)
        x1 = max(v_x)
        y0 = min(v_y)
        y1 = max(v_y)
        z0 = min(v_z)
        z1 = max(v_z)

        if dimension == 2:
            p.Set(edges=p.edges.getByBoundingBox(x0-tol, y0-tol, z0, x0+tol, y1+tol, z0), name='X0')
            p.Set(edges=p.edges.getByBoundingBox(x1-tol, y0-tol, z0, x1+tol, y1+tol, z0), name='X1')
            p.Set(edges=p.edges.getByBoundingBox(x0-tol, y0-tol, z0, x1+tol, y0+tol, z0), name='Y0')
            p.Set(edges=p.edges.getByBoundingBox(x0-tol, y1-tol, z0, x1+tol, y1+tol, z0), name='Y1')

            p.Set(vertices=p.vertices.getByBoundingBox(x0-tol, y0-tol, z0, x0+tol, y0+tol, z0), name='X0Y0')
            p.Set(vertices=p.vertices.getByBoundingBox(x0-tol, y1-tol, z0, x0+tol, y1+tol, z0), name='X0Y1')
            p.Set(vertices=p.vertices.getByBoundingBox(x1-tol, y0-tol, z0, x1+tol, y0+tol, z0), name='X1Y0')
            p.Set(vertices=p.vertices.getByBoundingBox(x1-tol, y1-tol, z0, x1+tol, y1+tol, z0), name='X1Y1')

        elif dimension == 3:
            p.Set(faces=p.faces.getByBoundingBox(x0-tol, y0-tol, z0-tol, x0+tol, y1+tol, z1+tol), name='X0')
            p.Set(faces=p.faces.getByBoundingBox(x1-tol, y0-tol, z0-tol, x1+tol, y1+tol, z1+tol), name='X1')
            p.Set(faces=p.faces.getByBoundingBox(x0-tol, y0-tol, z0-tol, x1+tol, y0+tol, z1+tol), name='Y0')
            p.Set(faces=p.faces.getByBoundingBox(x0-tol, y1-tol, z0-tol, x1+tol, y1+tol, z1+tol), name='Y1')
            p.Set(faces=p.faces.getByBoundingBox(x0-tol, y0-tol, z0-tol, x1+tol, y1+tol, z0+tol), name='Z0')
            p.Set(faces=p.faces.getByBoundingBox(x0-tol, y0-tol, z1-tol, x1+tol, y1+tol, z1+tol), name='Z1')

            p.Set(vertices=p.vertices.getByBoundingBox(x0-tol, y0-tol, z0-tol, x0+tol, y0+tol, z0+tol), name='X0Y0Z0')
            p.Set(vertices=p.vertices.getByBoundingBox(x0-tol, y1-tol, z0-tol, x0+tol, y1+tol, z0+tol), name='X0Y1Z0')
            p.Set(vertices=p.vertices.getByBoundingBox(x1-tol, y0-tol, z0-tol, x1+tol, y0+tol, z0+tol), name='X1Y0Z0')
            p.Set(vertices=p.vertices.getByBoundingBox(x1-tol, y1-tol, z0-tol, x1+tol, y1+tol, z0+tol), name='X1Y1Z0')
            p.Set(vertices=p.vertices.getByBoundingBox(x0-tol, y0-tol, z1-tol, x0+tol, y0+tol, z1+tol), name='X0Y0Z1')
            p.Set(vertices=p.vertices.getByBoundingBox(x0-tol, y1-tol, z1-tol, x0+tol, y1+tol, z1+tol), name='X0Y1Z1')
            p.Set(vertices=p.vertices.getByBoundingBox(x1-tol, y0-tol, z1-tol, x1+tol, y0+tol, z1+tol), name='X1Y0Z1')
            p.Set(vertices=p.vertices.getByBoundingBox(x1-tol, y1-tol, z1-tol, x1+tol, y1+tol, z1+tol), name='X1Y1Z1')
        else:
            print("Dimension error.")

    except:
        p = mdb.models[model_name].parts[part_name]

        n_x = []
        n_y = []
        n_z = []
        for n in p.nodes:
            n_x.append(n.coordinates[0])
            n_y.append(n.coordinates[1])
            n_z.append(n.coordinates[2])

        x0 = min(v_x)
        x1 = max(v_x)
        y0 = min(v_y)
        y1 = max(v_y)
        z0 = min(v_z)
        z1 = max(v_z)

        if dimension == 2:
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y0-tol, z0, x0+tol, y1+tol, z0), name='X0')
            p.Set(nodes=p.nodes.getByBoundingBox(x1-tol, y0-tol, z0, x1+tol, y1+tol, z0), name='X1')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y0-tol, z0, x1+tol, y0+tol, z0), name='Y0')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y1-tol, z0, x1+tol, y1+tol, z0), name='Y1')

            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y0-tol, z0, x0+tol, y0+tol, z0), name='X0Y0')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y1-tol, z0, x0+tol, y1+tol, z0), name='X0Y1')
            p.Set(nodes=p.nodes.getByBoundingBox(x1-tol, y0-tol, z0, x1+tol, y0+tol, z0), name='X1Y0')
            p.Set(nodes=p.nodes.getByBoundingBox(x1-tol, y1-tol, z0, x1+tol, y1+tol, z0), name='X1Y1')

        elif dimension == 3:
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y0-tol, z0-tol, x0+tol, y1+tol, z1+tol), name='X0')
            p.Set(nodes=p.nodes.getByBoundingBox(x1-tol, y0-tol, z0-tol, x1+tol, y1+tol, z1+tol), name='X1')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y0-tol, z0-tol, x1+tol, y0+tol, z1+tol), name='Y0')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y1-tol, z0-tol, x1+tol, y1+tol, z1+tol), name='Y1')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y0-tol, z0-tol, x1+tol, y1+tol, z0+tol), name='Z0')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y0-tol, z1-tol, x1+tol, y1+tol, z1+tol), name='Z1')

            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y0-tol, z0-tol, x0+tol, y0+tol, z0+tol), name='X0Y0Z0')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y1-tol, z0-tol, x0+tol, y1+tol, z0+tol), name='X0Y1Z0')
            p.Set(nodes=p.nodes.getByBoundingBox(x1-tol, y0-tol, z0-tol, x1+tol, y0+tol, z0+tol), name='X1Y0Z0')
            p.Set(nodes=p.nodes.getByBoundingBox(x1-tol, y1-tol, z0-tol, x1+tol, y1+tol, z0+tol), name='X1Y1Z0')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y0-tol, z1-tol, x0+tol, y0+tol, z1+tol), name='X0Y0Z1')
            p.Set(nodes=p.nodes.getByBoundingBox(x0-tol, y1-tol, z1-tol, x0+tol, y1+tol, z1+tol), name='X0Y1Z1')
            p.Set(nodes=p.nodes.getByBoundingBox(x1-tol, y0-tol, z1-tol, x1+tol, y0+tol, z1+tol), name='X1Y0Z1')
            p.Set(nodes=p.nodes.getByBoundingBox(x1-tol, y1-tol, z1-tol, x1+tol, y1+tol, z1+tol), name='X1Y1Z1')
        else:
            print("Dimension error.")
            
        print("The boundaries are set with nodes.")


if __name__ == "__main__":
    set_part_boundary(model_name='Model-1',
                      part_name='PART-1',
                      dimension=3,
                      tol=1e-6)