/****************************************************************************
** Meta object code from reading C++ file 'view_manager.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.2.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../../../../src/rviz/src/rviz/view_manager.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'view_manager.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.2.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
struct qt_meta_stringdata_rviz__ViewManager_t {
    QByteArrayData data[9];
    char stringdata[132];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    offsetof(qt_meta_stringdata_rviz__ViewManager_t, stringdata) + ofs \
        - idx * sizeof(QByteArrayData) \
    )
static const qt_meta_stringdata_rviz__ViewManager_t qt_meta_stringdata_rviz__ViewManager = {
    {
QT_MOC_LITERAL(0, 0, 17),
QT_MOC_LITERAL(1, 18, 13),
QT_MOC_LITERAL(2, 32, 0),
QT_MOC_LITERAL(3, 33, 14),
QT_MOC_LITERAL(4, 48, 17),
QT_MOC_LITERAL(5, 66, 28),
QT_MOC_LITERAL(6, 95, 12),
QT_MOC_LITERAL(7, 108, 18),
QT_MOC_LITERAL(8, 127, 3)
    },
    "rviz::ViewManager\0configChanged\0\0"
    "currentChanged\0copyCurrentToList\0"
    "setCurrentViewControllerType\0new_class_id\0"
    "onCurrentDestroyed\0obj\0"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_rviz__ViewManager[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
       5,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       2,       // signalCount

 // signals: name, argc, parameters, tag, flags
       1,    0,   39,    2, 0x06,
       3,    0,   40,    2, 0x06,

 // slots: name, argc, parameters, tag, flags
       4,    0,   41,    2, 0x0a,
       5,    1,   42,    2, 0x0a,
       7,    1,   45,    2, 0x08,

 // signals: parameters
    QMetaType::Void,
    QMetaType::Void,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void, QMetaType::QString,    6,
    QMetaType::Void, QMetaType::QObjectStar,    8,

       0        // eod
};

void rviz::ViewManager::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        ViewManager *_t = static_cast<ViewManager *>(_o);
        switch (_id) {
        case 0: _t->configChanged(); break;
        case 1: _t->currentChanged(); break;
        case 2: _t->copyCurrentToList(); break;
        case 3: _t->setCurrentViewControllerType((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 4: _t->onCurrentDestroyed((*reinterpret_cast< QObject*(*)>(_a[1]))); break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        void **func = reinterpret_cast<void **>(_a[1]);
        {
            typedef void (ViewManager::*_t)();
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&ViewManager::configChanged)) {
                *result = 0;
            }
        }
        {
            typedef void (ViewManager::*_t)();
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&ViewManager::currentChanged)) {
                *result = 1;
            }
        }
    }
}

const QMetaObject rviz::ViewManager::staticMetaObject = {
    { &QObject::staticMetaObject, qt_meta_stringdata_rviz__ViewManager.data,
      qt_meta_data_rviz__ViewManager,  qt_static_metacall, 0, 0}
};


const QMetaObject *rviz::ViewManager::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *rviz::ViewManager::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_rviz__ViewManager.stringdata))
        return static_cast<void*>(const_cast< ViewManager*>(this));
    return QObject::qt_metacast(_clname);
}

int rviz::ViewManager::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QObject::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 5)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 5;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 5)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 5;
    }
    return _id;
}

// SIGNAL 0
void rviz::ViewManager::configChanged()
{
    QMetaObject::activate(this, &staticMetaObject, 0, 0);
}

// SIGNAL 1
void rviz::ViewManager::currentChanged()
{
    QMetaObject::activate(this, &staticMetaObject, 1, 0);
}
struct qt_meta_stringdata_rviz__ViewControllerContainer_t {
    QByteArrayData data[1];
    char stringdata[31];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    offsetof(qt_meta_stringdata_rviz__ViewControllerContainer_t, stringdata) + ofs \
        - idx * sizeof(QByteArrayData) \
    )
static const qt_meta_stringdata_rviz__ViewControllerContainer_t qt_meta_stringdata_rviz__ViewControllerContainer = {
    {
QT_MOC_LITERAL(0, 0, 29)
    },
    "rviz::ViewControllerContainer\0"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_rviz__ViewControllerContainer[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
       0,    0, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

       0        // eod
};

void rviz::ViewControllerContainer::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    Q_UNUSED(_o);
    Q_UNUSED(_id);
    Q_UNUSED(_c);
    Q_UNUSED(_a);
}

const QMetaObject rviz::ViewControllerContainer::staticMetaObject = {
    { &Property::staticMetaObject, qt_meta_stringdata_rviz__ViewControllerContainer.data,
      qt_meta_data_rviz__ViewControllerContainer,  qt_static_metacall, 0, 0}
};


const QMetaObject *rviz::ViewControllerContainer::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *rviz::ViewControllerContainer::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_rviz__ViewControllerContainer.stringdata))
        return static_cast<void*>(const_cast< ViewControllerContainer*>(this));
    return Property::qt_metacast(_clname);
}

int rviz::ViewControllerContainer::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = Property::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    return _id;
}
QT_END_MOC_NAMESPACE
