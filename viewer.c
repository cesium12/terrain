#include <GL/glut.h>
#include <math.h>
#include <stdlib.h>
#include <Python.h>
#include <numpy/ndarrayobject.h>
#include <stdio.h>

inline GLdouble MIN(GLdouble a, GLdouble b) { return a < b ? a : b; };
inline GLdouble MAX(GLdouble a, GLdouble b) { return a > b ? a : b; };

#define HEIGHT(x, y) ({ \
        PyObject *item = PyArray_GETITEM(heightmap, PyArray_GETPTR2(heightmap, x, y)); \
        double value = PyFloat_AsDouble(item); \
        Py_DECREF(item); \
        value; \
    })
#define VERTEX2(x, y) glVertex3f(x, y, HEIGHT(x, y))
#define VERTEX3 glVertex3f

GLdouble angle = M_PI_4,
         pitch = -0.7,
         camerax = -20,
         cameray = -20,
         cameraz = 50,
         delta = 1,
         adelta = 0.04,
         depth = 1000,
         fovy = 50,
         waterh = 0.5;
int mouseb = -1, mousex, mousey, winw, winh, mapw, maph;
PyObject *heightmap;

void draw(void) {
    int x, y;
    double diff;
    
    glBegin(GL_QUADS);
    GLfloat c1[4] = { 0, 0, 1, 1 };
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, c1);
    VERTEX3(0, 0, waterh);
    VERTEX3(0, maph - 1, waterh);
    VERTEX3(mapw - 1, maph - 1, waterh);
    VERTEX3(mapw - 1, 0, waterh);
    
    GLfloat c2[4] = { 34 / 255., 139 / 255., 34 / 255., 1 };
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, c2);
    for(x = 0; x < mapw - 1; ++x)
        for(y = 0; y < maph - 1; ++y) {
            diff = HEIGHT(x, y) - HEIGHT(x + 1, y + 1);
            glNormal3f(diff, diff, 2);
            VERTEX2(x, y);
            VERTEX2(x, y + 1);
            VERTEX2(x + 1, y + 1);
            VERTEX2(x + 1, y);
        }
    
    GLfloat c3[4] = { 160 / 255., 82 / 255., 45 / 255., 1 };
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, c3);
    glNormal3i(0, -1, 0);
    for(x = 0; x < mapw - 1; ++x) {
        VERTEX3(x, 0, waterh);
        VERTEX2(x, 0);
        VERTEX2(x + 1, 0);
        VERTEX3(x + 1, 0, waterh);
    }
    glNormal3i(1, 0, 0);
    for(y = 0; y < maph - 1; ++y) {
        VERTEX3(mapw - 1, y, waterh);
        VERTEX2(mapw - 1, y);
        VERTEX2(mapw - 1, y + 1);
        VERTEX3(mapw - 1, y + 1, waterh);
    }
    glNormal3i(0, 1, 0);
    for(x = 0; x < mapw - 1; ++x) {
        VERTEX3(x, maph - 1, waterh);
        VERTEX3(x + 1, maph - 1, waterh);
        VERTEX2(x + 1, maph - 1);
        VERTEX2(x, maph - 1);
    }
    glNormal3i(-1, 0, 0);
    for(y = 0; y < maph - 1; ++y) {
        VERTEX3(0, y, waterh);
        VERTEX3(0, y + 1, waterh);
        VERTEX2(0, y + 1);
        VERTEX2(0, y);
    }
    glEnd();
}

void keyboard(unsigned char key, int x, int y) {
    switch(key) {
        case 'w':
            camerax += cos(angle) * cos(pitch) * delta;
            cameray += sin(angle) * cos(pitch) * delta;
            cameraz += sin(pitch);
            break;
        case 's':
            camerax -= cos(angle) * cos(pitch) * delta;
            cameray -= sin(angle) * cos(pitch) * delta;
            cameraz -= sin(pitch);
            break;
        case 'a':
            camerax -= sin(angle) * cos(pitch) * delta;
            cameray += cos(angle) * cos(pitch) * delta;
            break;
        case 'd':
            camerax += sin(angle) * cos(pitch) * delta;
            cameray -= cos(angle) * cos(pitch) * delta;
            break;
        case 'q':
            exit(0);
    }
    glutPostRedisplay();
}

void special(int key, int x, int y) {
    switch(key) {
        case GLUT_KEY_UP:
            pitch = MIN(M_PI_2 - adelta, pitch + adelta);
            break;
        case GLUT_KEY_DOWN:
            pitch = MAX(adelta - M_PI_2, pitch - adelta);
            break;
        case GLUT_KEY_LEFT:
            angle += adelta;
            break;
        case GLUT_KEY_RIGHT:
            angle -= adelta;
            break;
    }
    glutPostRedisplay();
}

void click(int button, int state, int x, int y) {
    if(button == 3 || button == 4) {
        int step = 14 - 4 * button;
        camerax += cos(angle) * cos(pitch) * step;
        cameray += sin(angle) * cos(pitch) * step;
        cameraz += sin(pitch) * step;
        glutPostRedisplay();
    } else if(state == GLUT_DOWN) {
        mouseb = button;
        mousex = x;
        mousey = y;
    } else
        mouseb = -1;
}

void move(int x, int y) {
    if(mouseb == -1)
        return;
    double scale;
    switch(mouseb) {
        case GLUT_RIGHT_BUTTON:
            scale = fovy * M_PI / 180 / winh;
            angle += (x - mousex) * scale;
            pitch = MAX(adelta - M_PI_2, MIN(M_PI_2 - adelta, pitch + (y - mousey) * scale));
            break;
        case GLUT_LEFT_BUTTON:
            scale = 0.2;
            camerax -= sin(angle) * (x - mousex) * scale;
            cameray += cos(angle) * (x - mousex) * scale;
            camerax -= cos(angle) * sin(pitch) * (y - mousey) * scale;
            cameray -= sin(angle) * sin(pitch) * (y - mousey) * scale;
            cameraz += cos(pitch) * (y - mousey) * scale;
            break;
    }
    mousex = x;
    mousey = y;
    glutPostRedisplay();
}

void reshape(int w, int h) {
    winw = w;
    winh = h;
    glViewport(0, 0, w, h);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluPerspective(fovy, ((float) w) / h, 1, depth);
}

void display(void) {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    gluLookAt(camerax, cameray, cameraz,
              camerax + cos(angle) * cos(pitch),
              cameray + sin(angle) * cos(pitch),
              cameraz + sin(pitch),
              0, 0, 1);
    GLfloat s[4] = { 1, 1, 1, 1 };
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, s);
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 100);
    draw();
    glutSwapBuffers();
}

PyObject *show(PyObject *self, PyObject *map) {
    heightmap = map;
    mapw = PyArray_DIM(map, 0);
    maph = PyArray_DIM(map, 1);
    
    int argc = 0;
    glutInit(&argc, NULL);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
    glutInitWindowSize(2000, 1000);
    glutCreateWindow("");
    glEnable(GL_NORMALIZE);
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_LIGHTING);
    glEnable(GL_LIGHT0);
    GLfloat a[4] = { 1, 1, 1, 1 };
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, a);
    GLfloat p[4] = { 10, 4, 10, 1 };
    glLightfv(GL_LIGHT0, GL_POSITION, p);
    GLfloat d[4] = { 1, 1, 1, 1 };
    glLightfv(GL_LIGHT0, GL_DIFFUSE, d);
    glutDisplayFunc(display);
    glutKeyboardFunc(keyboard);
    glutMouseFunc(click);
    glutMotionFunc(move);
    glutSpecialFunc(special);
    glutReshapeFunc(reshape);
    glutMainLoop();
    
    Py_INCREF(Py_None);
    return Py_None;
}

void initviewer(void) {
    static struct PyMethodDef methods[] = {
        { "show", (PyCFunction) show, METH_O, ""   },
        {   NULL, (PyCFunction) NULL,      0, NULL }
    };
    Py_InitModule("viewer", methods);
    if(PyErr_Occurred())
        Py_FatalError("couldn't initialize module");
}
