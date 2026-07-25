/****************************************************************************
** Meta object code from reading C++ file 'interactive_marker_display.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.2.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../../../../../src/rviz/src/rviz/default_plugin/interactive_marker_display.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'interactive_marker_display.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.2.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
struct qt_meta_stringdata_rviz__InteractiveMarkerDisplay_t {
    QByteArrayData data[16];
    char stringdata[266];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    offsetof(qt_meta_stringdata_rviz__InteractiveMarkerDisplay_t, stringdata) + ofs \
        - idx * sizeof(QByteArrayData) \
    )
static const qt_meta_stringdata_rviz__InteractiveMarkerDisplay_t qt_meta_stringdata_rviz__InteractiveMarkerDisplay = {
    {
QT_MOC_LITERAL(0, 0, 30),
QT_MOC_LITERAL(1, 31, 11),
QT_MOC_LITERAL(2, 43, 0),
QT_MOC_LITERAL(3, 44, 22),
QT_MOC_LITERAL(4, 67, 14),
QT_MOC_LITERAL(5, 82, 20),
QT_MOC_LITERAL(6, 103, 24),
QT_MOC_LITERAL(7, 128, 15),
QT_MOC_LITERAL(8, 144, 46),
QT_MOC_LITERAL(9, 191, 8),
QT_MOC_LITERAL(10, 200, 14),
QT_MOC_LITERAL(11, 215, 21),
QT_MOC_LITERAL(12, 237, 5),
QT_MOC_LITERAL(13, 243, 11),
QT_MOC_LITERAL(14, 255, 4),
QT_MOC_LITERAL(15, 260, 4)
    },
    "rviz::InteractiveMarkerDisplay\0"
    "updateTopic\0\0updateShowDescriptions\0"
    "updateShowAxes\0updateShowVisualAids\0"
    "updateEnableTransparency\0publishFeedback\0"
    "visualization_msgs::InteractiveMarkerFeedback&\0"
    "feedback\0onStatusUpdate\0StatusProperty::Level\0"
    "level\0std::string\0name\0text\0"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_rviz__InteractiveMarkerDisplay[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
       7,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: name, argc, parameters, tag, flags
       1,    0,   49,    2, 0x09,
       3,    0,   50,    2, 0x09,
       4,    0,   51,    2, 0x09,
       5,    0,   52,    2, 0x09,
       6,    0,   53,    2, 0x09,
       7,    1,   54,    2, 0x09,
      10,    3,   57,    2, 0x09,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, 0x80000000 | 8,    9,
    QMetaType::Void, 0x80000000 | 11, 0x80000000 | 13, 0x80000000 | 13,   12,   14,   15,

       0        // eod
};

void rviz::InteractiveMarkerDisplay::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        InteractiveMarkerDisplay *_t = static_cast<InteractiveMarkerDisplay *>(_o);
        switch (_id) {
        case 0: _t->updateTopic(); break;
        case 1: _t->updateShowDescriptions(); break;
        case 2: _t->updateShowAxes(); break;
        case 3: _t->updateShowVisualAids(); break;
        case 4: _t->updateEnableTransparency(); break;
        case 5: _t->publishFeedback((*reinterpret_cast< visualization_msgs::InteractiveMarkerFeedback(*)>(_a[1]))); break;
        case 6: _t->onStatusUpdate((*reinterpret_cast< StatusProperty::Level(*)>(_a[1])),(*reinterpret_cast< const std::string(*)>(_a[2])),(*reinterpret_cast< const std::string(*)>(_a[3]))); break;
        default: ;
        }
    }
}

const QMetaObject rviz::InteractiveMarkerDisplay::staticMetaObject = {
    { &Display::staticMetaObject, qt_meta_stringdata_rviz__InteractiveMarkerDisplay.data,
      qt_meta_data_rviz__InteractiveMarkerDisplay,  qt_static_metacall, 0, 0}
};


const QMetaObject *rviz::InteractiveMarkerDisplay::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *rviz::InteractiveMarkerDisplay::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_rviz__InteractiveMarkerDisplay.stringdata))
        return static_cast<void*>(const_cast< InteractiveMarkerDisplay*>(this));
    return Display::qt_metacast(_clname);
}

int rviz::InteractiveMarkerDisplay::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = Display::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 7)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 7;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 7)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 7;
    }
    return _id;
}
QT_END_MOC_NAMESPACE
