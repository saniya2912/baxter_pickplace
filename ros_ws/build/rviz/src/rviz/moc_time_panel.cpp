/****************************************************************************
** Meta object code from reading C++ file 'time_panel.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.2.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../../../../src/rviz/src/rviz/time_panel.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'time_panel.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.2.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
struct qt_meta_stringdata_rviz__TimePanel_t {
    QByteArrayData data[20];
    char stringdata[215];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    offsetof(qt_meta_stringdata_rviz__TimePanel_t, stringdata) + ofs \
        - idx * sizeof(QByteArrayData) \
    )
static const qt_meta_stringdata_rviz__TimePanel_t qt_meta_stringdata_rviz__TimePanel = {
    {
QT_MOC_LITERAL(0, 0, 15),
QT_MOC_LITERAL(1, 16, 12),
QT_MOC_LITERAL(2, 29, 0),
QT_MOC_LITERAL(3, 30, 7),
QT_MOC_LITERAL(4, 38, 16),
QT_MOC_LITERAL(5, 55, 5),
QT_MOC_LITERAL(6, 61, 18),
QT_MOC_LITERAL(7, 80, 19),
QT_MOC_LITERAL(8, 100, 6),
QT_MOC_LITERAL(9, 107, 14),
QT_MOC_LITERAL(10, 122, 14),
QT_MOC_LITERAL(11, 137, 7),
QT_MOC_LITERAL(12, 145, 16),
QT_MOC_LITERAL(13, 162, 12),
QT_MOC_LITERAL(14, 175, 9),
QT_MOC_LITERAL(15, 185, 4),
QT_MOC_LITERAL(16, 190, 4),
QT_MOC_LITERAL(17, 195, 6),
QT_MOC_LITERAL(18, 202, 6),
QT_MOC_LITERAL(19, 209, 4)
    },
    "rviz::TimePanel\0pauseToggled\0\0checked\0"
    "syncModeSelected\0index\0syncSourceSelected\0"
    "experimentalToggled\0update\0onDisplayAdded\0"
    "rviz::Display*\0display\0onDisplayRemoved\0"
    "onTimeSignal\0ros::Time\0time\0load\0"
    "Config\0config\0save\0"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_rviz__TimePanel[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
      10,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: name, argc, parameters, tag, flags
       1,    1,   64,    2, 0x09,
       4,    1,   67,    2, 0x09,
       6,    1,   70,    2, 0x09,
       7,    1,   73,    2, 0x09,
       8,    0,   76,    2, 0x09,
       9,    1,   77,    2, 0x09,
      12,    1,   80,    2, 0x09,
      13,    2,   83,    2, 0x09,
      16,    1,   88,    2, 0x09,
      19,    1,   91,    2, 0x09,

 // slots: parameters
    QMetaType::Void, QMetaType::Bool,    3,
    QMetaType::Void, QMetaType::Int,    5,
    QMetaType::Void, QMetaType::Int,    5,
    QMetaType::Void, QMetaType::Bool,    3,
    QMetaType::Void,
    QMetaType::Void, 0x80000000 | 10,   11,
    QMetaType::Void, 0x80000000 | 10,   11,
    QMetaType::Void, 0x80000000 | 10, 0x80000000 | 14,   11,   15,
    QMetaType::Void, 0x80000000 | 17,   18,
    QMetaType::Void, 0x80000000 | 17,   18,

       0        // eod
};

void rviz::TimePanel::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        TimePanel *_t = static_cast<TimePanel *>(_o);
        switch (_id) {
        case 0: _t->pauseToggled((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 1: _t->syncModeSelected((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 2: _t->syncSourceSelected((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 3: _t->experimentalToggled((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 4: _t->update(); break;
        case 5: _t->onDisplayAdded((*reinterpret_cast< rviz::Display*(*)>(_a[1]))); break;
        case 6: _t->onDisplayRemoved((*reinterpret_cast< rviz::Display*(*)>(_a[1]))); break;
        case 7: _t->onTimeSignal((*reinterpret_cast< rviz::Display*(*)>(_a[1])),(*reinterpret_cast< ros::Time(*)>(_a[2]))); break;
        case 8: _t->load((*reinterpret_cast< const Config(*)>(_a[1]))); break;
        case 9: _t->save((*reinterpret_cast< Config(*)>(_a[1]))); break;
        default: ;
        }
    }
}

const QMetaObject rviz::TimePanel::staticMetaObject = {
    { &Panel::staticMetaObject, qt_meta_stringdata_rviz__TimePanel.data,
      qt_meta_data_rviz__TimePanel,  qt_static_metacall, 0, 0}
};


const QMetaObject *rviz::TimePanel::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *rviz::TimePanel::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_rviz__TimePanel.stringdata))
        return static_cast<void*>(const_cast< TimePanel*>(this));
    return Panel::qt_metacast(_clname);
}

int rviz::TimePanel::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = Panel::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 10)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 10;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 10)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 10;
    }
    return _id;
}
QT_END_MOC_NAMESPACE
