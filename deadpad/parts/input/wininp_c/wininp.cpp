// clang ./deadpad\parts\input\wininp_c\wininp.cpp -shared -o ./deadpad\parts\input\wininp_c\wininp.dll -I "C:\Users\William\anaconda3\Include" -L "C:\Users\William\anaconda3\libs"
#include <Python.h>
#include <windows.h>
#include <iostream>


extern "C" {

PyObject *get_key(PyObject *self, PyObject *noargs) {
    HANDLE hout = GetStdHandle(STD_OUTPUT_HANDLE);
    HANDLE hin = GetStdHandle(STD_INPUT_HANDLE);
    long event_type = 0, col = 0, row = 0, event_state = 0; // event_type is the event number: aka wether it is scroll up, down, move mouse

    // start mouse input
        // get originals
        CONSOLE_CURSOR_INFO orig_cci;
        GetConsoleCursorInfo(hout, &orig_cci);
        DWORD orig_cmode;
        GetConsoleMode(hin, &orig_cmode);
        CONSOLE_CURSOR_INFO cci;
        cci.dwSize = 25;
        cci.bVisible = FALSE;
        // set the cursor settings
        SetConsoleCursorInfo(hout, &cci);
        // change console mode to enable mouse
        SetConsoleMode(hin, ENABLE_PROCESSED_INPUT | ENABLE_WINDOW_INPUT | ENABLE_MOUSE_INPUT);
    // end start mouse input

    INPUT_RECORD InputRecord[1];
    DWORD Events;
    
    GetNumberOfConsoleInputEvents(hin, &Events);
    if (Events > 0) {
        Py_BEGIN_ALLOW_THREADS
        ReadConsoleInput(hin, InputRecord, 1, &Events);
        Py_END_ALLOW_THREADS
        if (InputRecord[Events-1].EventType == MOUSE_EVENT) {
            // position:
            col = InputRecord[Events-1].Event.MouseEvent.dwMousePosition.X;
            row = InputRecord[Events-1].Event.MouseEvent.dwMousePosition.Y;
            // state:
            event_state = InputRecord[Events-1].Event.MouseEvent.dwButtonState;
            event_type = InputRecord[Events-1].Event.MouseEvent.dwEventFlags;
        } else if (InputRecord[Events-1].EventType == KEY_EVENT ) {
            char key[2];
            key[0] = InputRecord[Events-1].Event.KeyEvent.uChar.AsciiChar;
            key[1] = '\0';
            FlushConsoleInputBuffer(hin);
            // std::cout << key;
            // stop mouse input
                // set the cursor settings
                SetConsoleCursorInfo(hout, &orig_cci);
                // change console mode to enable mouse
                SetConsoleMode(hin, orig_cmode);
            // stop mouse input end
            return PyUnicode_FromString(key);
        }  else if (InputRecord[Events-1].EventType == CTRL_C_EVENT ) {
            FlushConsoleInputBuffer(hin);
            // stop mouse input
                // set the cursor settings
                SetConsoleCursorInfo(hout, &orig_cci);
                // change console mode to enable mouse
                SetConsoleMode(hin, orig_cmode);
            // stop mouse input end
            return PyUnicode_FromString("ctrl-c\0");
        }
    } else {
        FlushConsoleInputBuffer(hin);
        // stop mouse input
            // set the cursor settings
            SetConsoleCursorInfo(hout, &orig_cci);
            // change console mode to enable mouse
            SetConsoleMode(hin, orig_cmode);
        // stop mouse input end
        return Py_BuildValue("");
    }

    FlushConsoleInputBuffer(hin);

    // stop mouse input
        // set the cursor settings
        SetConsoleCursorInfo(hout, &orig_cci);
        // change console mode to enable mouse
        SetConsoleMode(hin, orig_cmode);
    // stop mouse input end

    return Py_BuildValue("iiii", event_type, col, row, event_state); 
}

static PyMethodDef methods[] = {
    { "get_key", get_key, METH_NOARGS, "Returns a tuple containing `(event_type, col, row, event_state)` or the key pressed." },
    { NULL, NULL, 0, NULL }
};

static struct PyModuleDef MODULE = {
    PyModuleDef_HEAD_INIT,
    "wininp",
    "A c extension used to get mouse input on windows.",
    -1,
    methods
};

PyMODINIT_FUNC PyInit_wininp() {
    return PyModule_Create(&MODULE);
}

} // end extern "C"