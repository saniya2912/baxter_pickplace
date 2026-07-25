/****************************************************************************
** Meta object code from reading C++ file 'views_panel.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.2.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../../../../src/rviz/src/rviz/views_panel.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'views_panel.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.2.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
struct qt_meta_stringdata_rviz__ViewsPanel_t {
    QByteArrayData data[10];
    char stringdata[148];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    offsetof(qt_meta_stringdata_rviz__ViewsPanel_t, stringdata) + ofs \
        - idx * sizeof(QByteArrayData) \
    )
static const qt_meta_stringdata_rviz__ViewsPanel_t qt_meta_stringdata_rviz__ViewsPanel = {
    {
QT_MOC_LITERAL(0, 0, 16),
QT_MOC_LITERAL(1, 17, 21),
QT_MOC_LITERAL(2, 39, 0),
QT_MOC_LITERAL(3, 40, 14),
QT_MOC_LITERAL(4, 55, 15),
QT_MOC_LITERAL(5, 71, 14),
QT_MOC_LITERAL(6, 86, 13),
QT_MOC_LITERAL(7, 100, 16),
QT_MOC_LITERAL(8, 117, 23),
QT_MOC_LITERAL(9, 141, 5)
    },
    "rviz::ViewsPanel\0onTypeSelectorChanged\0"
    "\0selected_index\0onDeleteClicked\0"
    "renameSelected\0onZeroClicked\0"
    "onCurrentChanged\0setCurrentViewFromIndex\0"
    "index\0"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_rviz__ViewsPanel[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
       6,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: name, argc, parameters, tag, flags
       1,    1,   44,    2, 0x08,
       4,    0,   47,    2, 0x08,
       5,    0,   48,    2, 0x08,
       6,    0,   49,    2, 0x08,
       7,    0,   50,    2, 0x08,
       8,    1,   51,    2, 0x08,

 // slots: parameters
    QMetaType::Void, QMetaType::Int,    3,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::QModelIndex,    9,

       0        // eod
};

void rviz::ViewsPanel::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        ViewsPanel *_t = static_cast<ViewsPanel *>(_o);
        switch (_id) {
        case 0: _t->onTypeSelectorChanged((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 1: _t->onDeleteClicked(); break;
        case 2: _t->renameSelected(); break;
        case 3: _t->onZeroClicked(); break;
        case 4: _t->onCurrentChanged(); break;
        case 5: _t->setCurrentViewFromIndex((*reinterpret_cast< const QModelIndex(*)>(_a[1]))); break;
        default: ;
        }
    }
}

const QMetaObject rviz::ViewsPanel::staticMetaObject = {
    { &Panel::staticMetaObject, qt_meta_stringdata_rviz__ViewsPanel.data,
      qt_meta_data_rviz__ViewsPanel,  qt_static_metacall, 0, 0}
};


const QMetaObject *rviz::ViewsPanel::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *rviz::ViewsPanel::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_rviz__ViewsPanel.stringdata))
        return static_cast<void*>(const_cast< ViewsPanel*>(this));
    return Panel::qt_metacast(_clname);
}

int rviz::ViewsPanel::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = Panel::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 6)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 6;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 6)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 6;
    }
    return _id;
}
QT_END_MOC_NAMESPACE
