/****************************************************************************
** Meta object code from reading C++ file 'visualization_manager.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.2.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../../../../src/rviz/src/rviz/visualization_manager.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'visualization_manager.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.2.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
struct qt_meta_stringdata_rviz__VisualizationManager_t {
    QByteArrayData data[13];
    char stringdata[178];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    offsetof(qt_meta_stringdata_rviz__VisualizationManager_t, stringdata) + ofs \
        - idx * sizeof(QByteArrayData) \
    )
static const qt_meta_stringdata_rviz__VisualizationManager_t qt_meta_stringdata_rviz__VisualizationManager = {
    {
QT_MOC_LITERAL(0, 0, 26),
QT_MOC_LITERAL(1, 27, 9),
QT_MOC_LITERAL(2, 37, 0),
QT_MOC_LITERAL(3, 38, 13),
QT_MOC_LITERAL(4, 52, 12),
QT_MOC_LITERAL(5, 65, 7),
QT_MOC_LITERAL(6, 73, 8),
QT_MOC_LITERAL(7, 82, 13),
QT_MOC_LITERAL(8, 96, 5),
QT_MOC_LITERAL(9, 102, 16),
QT_MOC_LITERAL(10, 119, 21),
QT_MOC_LITERAL(11, 141, 9),
QT_MOC_LITERAL(12, 151, 25)
    },
    "rviz::VisualizationManager\0preUpdate\0"
    "\0configChanged\0statusUpdate\0message\0"
    "onUpdate\0onToolChanged\0Tool*\0"
    "updateFixedFrame\0updateBackgroundColor\0"
    "updateFps\0updateDefaultLightVisible\0"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_rviz__VisualizationManager[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
       9,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       3,       // signalCount

 // signals: name, argc, parameters, tag, flags
       1,    0,   59,    2, 0x06,
       3,    0,   60,    2, 0x06,
       4,    1,   61,    2, 0x06,

 // slots: name, argc, parameters, tag, flags
       6,    0,   64,    2, 0x09,
       7,    1,   65,    2, 0x09,
       9,    0,   68,    2, 0x08,
      10,    0,   69,    2, 0x08,
      11,    0,   70,    2, 0x08,
      12,    0,   71,    2, 0x08,

 // signals: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::QString,    5,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void, 0x80000000 | 8,    2,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,

       0        // eod
};

void rviz::VisualizationManager::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        VisualizationManager *_t = static_cast<VisualizationManager *>(_o);
        switch (_id) {
        case 0: _t->preUpdate(); break;
        case 1: _t->configChanged(); break;
        case 2: _t->statusUpdate((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 3: _t->onUpdate(); break;
        case 4: _t->onToolChanged((*reinterpret_cast< Tool*(*)>(_a[1]))); break;
        case 5: _t->updateFixedFrame(); break;
        case 6: _t->updateBackgroundColor(); break;
        case 7: _t->updateFps(); break;
        case 8: _t->updateDefaultLightVisible(); break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        void **func = reinterpret_cast<void **>(_a[1]);
        {
            typedef void (VisualizationManager::*_t)();
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&VisualizationManager::preUpdate)) {
                *result = 0;
            }
        }
        {
            typedef void (VisualizationManager::*_t)();
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&VisualizationManager::configChanged)) {
                *result = 1;
            }
        }
        {
            typedef void (VisualizationManager::*_t)(const QString & );
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&VisualizationManager::statusUpdate)) {
                *result = 2;
            }
        }
    }
}

const QMetaObject rviz::VisualizationManager::staticMetaObject = {
    { &DisplayContext::staticMetaObject, qt_meta_stringdata_rviz__VisualizationManager.data,
      qt_meta_data_rviz__VisualizationManager,  qt_static_metacall, 0, 0}
};


const QMetaObject *rviz::VisualizationManager::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *rviz::VisualizationManager::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_rviz__VisualizationManager.stringdata))
        return static_cast<void*>(const_cast< VisualizationManager*>(this));
    return DisplayContext::qt_metacast(_clname);
}

int rviz::VisualizationManager::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = DisplayContext::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 9)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 9;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 9)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 9;
    }
    return _id;
}

// SIGNAL 0
void rviz::VisualizationManager::preUpdate()
{
    QMetaObject::activate(this, &staticMetaObject, 0, 0);
}

// SIGNAL 1
void rviz::VisualizationManager::configChanged()
{
    QMetaObject::activate(this, &staticMetaObject, 1, 0);
}

// SIGNAL 2
void rviz::VisualizationManager::statusUpdate(const QString & _t1)
{
    void *_a[] = { 0, const_cast<void*>(reinterpret_cast<const void*>(&_t1)) };
    QMetaObject::activate(this, &staticMetaObject, 2, _a);
}
QT_END_MOC_NAMESPACE
