/****************************************************************************
** Meta object code from reading C++ file 'range_display.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.2.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../../../../../src/rviz/src/rviz/default_plugin/range_display.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'range_display.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.2.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
struct qt_meta_stringdata_rviz__RangeDisplay_t {
    QByteArrayData data[5];
    char stringdata[76];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    offsetof(qt_meta_stringdata_rviz__RangeDisplay_t, stringdata) + ofs \
        - idx * sizeof(QByteArrayData) \
    )
static const qt_meta_stringdata_rviz__RangeDisplay_t qt_meta_stringdata_rviz__RangeDisplay = {
    {
QT_MOC_LITERAL(0, 0, 18),
QT_MOC_LITERAL(1, 19, 18),
QT_MOC_LITERAL(2, 38, 0),
QT_MOC_LITERAL(3, 39, 19),
QT_MOC_LITERAL(4, 59, 15)
    },
    "rviz::RangeDisplay\0updateBufferLength\0"
    "\0updateColorAndAlpha\0updateQueueSize\0"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_rviz__RangeDisplay[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
       3,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: name, argc, parameters, tag, flags
       1,    0,   29,    2, 0x08,
       3,    0,   30,    2, 0x08,
       4,    0,   31,    2, 0x08,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,

       0        // eod
};

void rviz::RangeDisplay::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        RangeDisplay *_t = static_cast<RangeDisplay *>(_o);
        switch (_id) {
        case 0: _t->updateBufferLength(); break;
        case 1: _t->updateColorAndAlpha(); break;
        case 2: _t->updateQueueSize(); break;
        default: ;
        }
    }
    Q_UNUSED(_a);
}

const QMetaObject rviz::RangeDisplay::staticMetaObject = {
    { &MessageFilterDisplay<sensor_msgs::Range>::staticMetaObject, qt_meta_stringdata_rviz__RangeDisplay.data,
      qt_meta_data_rviz__RangeDisplay,  qt_static_metacall, 0, 0}
};


const QMetaObject *rviz::RangeDisplay::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *rviz::RangeDisplay::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_rviz__RangeDisplay.stringdata))
        return static_cast<void*>(const_cast< RangeDisplay*>(this));
    return MessageFilterDisplay<sensor_msgs::Range>::qt_metacast(_clname);
}

int rviz::RangeDisplay::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = MessageFilterDisplay<sensor_msgs::Range>::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 3)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 3;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 3)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 3;
    }
    return _id;
}
QT_END_MOC_NAMESPACE
