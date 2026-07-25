/****************************************************************************
** Meta object code from reading C++ file 'display.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.2.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../../../../src/rviz/src/rviz/display.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'display.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.2.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
struct qt_meta_stringdata_rviz__Display_t {
    QByteArrayData data[22];
    char stringdata[250];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    offsetof(qt_meta_stringdata_rviz__Display_t, stringdata) + ofs \
        - idx * sizeof(QByteArrayData) \
    )
static const qt_meta_stringdata_rviz__Display_t qt_meta_stringdata_rviz__Display = {
    {
QT_MOC_LITERAL(0, 0, 13),
QT_MOC_LITERAL(1, 14, 10),
QT_MOC_LITERAL(2, 25, 0),
QT_MOC_LITERAL(3, 26, 14),
QT_MOC_LITERAL(4, 41, 7),
QT_MOC_LITERAL(5, 49, 9),
QT_MOC_LITERAL(6, 59, 4),
QT_MOC_LITERAL(7, 64, 10),
QT_MOC_LITERAL(8, 75, 7),
QT_MOC_LITERAL(9, 83, 11),
QT_MOC_LITERAL(10, 95, 7),
QT_MOC_LITERAL(11, 103, 4),
QT_MOC_LITERAL(12, 108, 15),
QT_MOC_LITERAL(13, 124, 17),
QT_MOC_LITERAL(14, 142, 5),
QT_MOC_LITERAL(15, 148, 4),
QT_MOC_LITERAL(16, 153, 4),
QT_MOC_LITERAL(17, 158, 20),
QT_MOC_LITERAL(18, 179, 21),
QT_MOC_LITERAL(19, 201, 31),
QT_MOC_LITERAL(20, 233, 7),
QT_MOC_LITERAL(21, 241, 7)
    },
    "rviz::Display\0timeSignal\0\0rviz::Display*\0"
    "display\0ros::Time\0time\0setEnabled\0"
    "enabled\0queueRender\0setIcon\0icon\0"
    "onEnableChanged\0setStatusInternal\0"
    "level\0name\0text\0deleteStatusInternal\0"
    "clearStatusesInternal\0"
    "associatedPanelVisibilityChange\0visible\0"
    "disable\0"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_rviz__Display[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
      10,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       1,       // signalCount

 // signals: name, argc, parameters, tag, flags
       1,    2,   64,    2, 0x06,

 // slots: name, argc, parameters, tag, flags
       7,    1,   69,    2, 0x0a,
       9,    0,   72,    2, 0x0a,
      10,    1,   73,    2, 0x0a,
      12,    0,   76,    2, 0x0a,
      13,    3,   77,    2, 0x08,
      17,    1,   84,    2, 0x08,
      18,    0,   87,    2, 0x08,
      19,    1,   88,    2, 0x08,
      21,    0,   91,    2, 0x08,

 // signals: parameters
    QMetaType::Void, 0x80000000 | 3, 0x80000000 | 5,    4,    6,

 // slots: parameters
    QMetaType::Void, QMetaType::Bool,    8,
    QMetaType::Void,
    QMetaType::Void, QMetaType::QIcon,   11,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Int, QMetaType::QString, QMetaType::QString,   14,   15,   16,
    QMetaType::Void, QMetaType::QString,   15,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,   20,
    QMetaType::Void,

       0        // eod
};

void rviz::Display::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        Display *_t = static_cast<Display *>(_o);
        switch (_id) {
        case 0: _t->timeSignal((*reinterpret_cast< rviz::Display*(*)>(_a[1])),(*reinterpret_cast< ros::Time(*)>(_a[2]))); break;
        case 1: _t->setEnabled((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 2: _t->queueRender(); break;
        case 3: _t->setIcon((*reinterpret_cast< const QIcon(*)>(_a[1]))); break;
        case 4: _t->onEnableChanged(); break;
        case 5: _t->setStatusInternal((*reinterpret_cast< int(*)>(_a[1])),(*reinterpret_cast< const QString(*)>(_a[2])),(*reinterpret_cast< const QString(*)>(_a[3]))); break;
        case 6: _t->deleteStatusInternal((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 7: _t->clearStatusesInternal(); break;
        case 8: _t->associatedPanelVisibilityChange((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 9: _t->disable(); break;
        default: ;
        }
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        switch (_id) {
        default: *reinterpret_cast<int*>(_a[0]) = -1; break;
        case 0:
            switch (*reinterpret_cast<int*>(_a[1])) {
            default: *reinterpret_cast<int*>(_a[0]) = -1; break;
            case 1:
                *reinterpret_cast<int*>(_a[0]) = qRegisterMetaType< ros::Time >(); break;
            case 0:
                *reinterpret_cast<int*>(_a[0]) = qRegisterMetaType< rviz::Display* >(); break;
            }
            break;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        void **func = reinterpret_cast<void **>(_a[1]);
        {
            typedef void (Display::*_t)(rviz::Display * , ros::Time );
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&Display::timeSignal)) {
                *result = 0;
            }
        }
    }
}

const QMetaObject rviz::Display::staticMetaObject = {
    { &BoolProperty::staticMetaObject, qt_meta_stringdata_rviz__Display.data,
      qt_meta_data_rviz__Display,  qt_static_metacall, 0, 0}
};


const QMetaObject *rviz::Display::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *rviz::Display::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_rviz__Display.stringdata))
        return static_cast<void*>(const_cast< Display*>(this));
    return BoolProperty::qt_metacast(_clname);
}

int rviz::Display::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = BoolProperty::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 10)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 10;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 10)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 10;
    }
    return _id;
}

// SIGNAL 0
void rviz::Display::timeSignal(rviz::Display * _t1, ros::Time _t2)
{
    void *_a[] = { 0, const_cast<void*>(reinterpret_cast<const void*>(&_t1)), const_cast<void*>(reinterpret_cast<const void*>(&_t2)) };
    QMetaObject::activate(this, &staticMetaObject, 0, _a);
}
QT_END_MOC_NAMESPACE
