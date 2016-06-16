#!/bin/sh

export HOME=$SNAP_APP_USER_DATA
export HACKDIR=$SNAP_APP_USER_DATA
export NETHACKOPTIONS=$SNAP_APP_USER_DATA/.nethackrc

export I18NPATH=$SNAP_APP_PATH/usr/share/i18n
export LOCPATH=$SNAP_APP_USER_DATA

APPLANG=en_US
APPENC=UTF-8
APPLOC="$APPLANG.$APPENC"

# generate a locale so we get properly working charsets and graphics
if [ ! -e $SNAP_APP_USER_DATA/$APPLOC ]; then
  localedef --prefix=$SNAP_APP_USER_DATA -f $APPENC -i $APPLANG $SNAP_APP_USER_DATA/$APPLOC
fi

export LC_ALL=$APPLOC
export LANG=$APPLOC
export LANGUAGE=${APPLANG%_*}

$SNAP/usr/bin/nikola "$@"
