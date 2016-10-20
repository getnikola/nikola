#!/bin/sh

export HOME=$SNAP_USER_DATA

export I18NPATH=$SNAP/usr/share/i18n
export LOCPATH=$SNAP_USER_DATA

APPLANG=en_US
APPENC=UTF-8
APPLOC="$APPLANG.$APPENC"

# generate a locale so we get properly working charsets and graphics
if [ ! -e $SNAP_USER_DATA/$APPLOC ]; then
  localedef --prefix=$SNAP_USER_DATA -f $APPENC -i $APPLANG $SNAP_USER_DATA/$APPLOC
fi

export LC_ALL=$APPLOC
export LANG=$APPLOC
export LANGUAGE=${APPLANG%_*}

$SNAP/bin/nikola "$@"
