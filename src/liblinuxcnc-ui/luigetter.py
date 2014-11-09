#!/usr/bin/python
#    Copyright 2014 Jeff Epler <jepler@unpythonic.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import errno
import os
import sys
import time


def autogenerated_header(fd, commentchar):
    print >>fd, "%s Autogenerated file; do not edit" % (commentchar,)
    print >>fd, "%s generated by %s on %s" % (commentchar, __file__, time.asctime())

getters = {}
class LuiGetter:
    def __init__(self, cname, ctype, dotname, doc1, doc2="", deprecated=False):
        getters[cname] = self
        self.dotname = dotname
        self.cname = cname
        self.ctype = ctype
        self.doc1 = doc1
        self.doc2 = doc2
        self.deprecated = " (deprecated)" if deprecated else ""

    def do_makefile(self, fd):
        print >>fd, """\
manpages: ../docs/man/man3/lui_get_%(cname)s.3lui
../docs/man/man3/lui_get_%(cname)s.3lui: liblinuxcnc-ui/luigetter.py
\t$(LUIGETTER) manfile $@ %(cname)s

objects/liblinuxcnc-ui/lui_get_%(cname)s.cc: liblinuxcnc-ui/luigetter.py
objects/liblinuxcnc-ui/lui_get_%(cname)s.cc: liblinuxcnc-ui/luigetter.py
\t$(LUIGETTER) cfile $@ %(cname)s

LIBLINUXCNC_UI_SRC += objects/liblinuxcnc-ui/lui_get_%(cname)s.cc""" % self.__dict__

    def do_hfile(self, fd):
        print >>fd, "%(ctype)s lui_get_%(cname)s(lui_t *lui);" % self.__dict__

    def do_cfile(self, fd):
        autogenerated_header(fd, "//")
        print >>fd, """\
#include "linuxcnc-ui-private.h"
#include <string.h>

#define STATIC_ASSERT(COND,MSG) \\
    typedef char static_assertion_##MSG[(COND)?1:-1] \\
    __attribute__((unused))

%(ctype)s lui_get_%(cname)s(lui_t *lui) {
    %(ctype)s result;
    STATIC_ASSERT(sizeof(result) == sizeof(lui->status->%(dotname)s),
        matching_result_size);
    if(!lui->status)
        memset(&result, 0, sizeof(result));
    else
        memcpy(&result, &lui->status->%(dotname)s,
            sizeof(lui->status->%(dotname)s));
    return result;
}""" % self.__dict__

    def do_manfile(self, fd):
        autogenerated_header(fd, '.\\"')
        print >>fd, '.TH LinuxCNC "1" "%s" "LinuxCNC Documentation" "The Enhanced Machine Controller' % (time.strftime("%F", time.localtime()))
        print >>fd, '''\
.SH NAME
lui_get_%(cname)s \- get %(doc1)s%(deprecated)s
.SH SYNOPSIS
.nf
.B #include <linuxcnc-ui.h>
.sp
.BI "%(ctype)s lui_get_%(cname)s(lui_t *" lui );
.fi
.SH DESCRIPTION
After a successful call to \\fBlui_status_nml_update\\fR, retrieves the
given value from the task controller.

%(doc2)s''' % self.__dict__

class LuiGetterSimple(LuiGetter):
    def do_cfile(self, fd):
        autogenerated_header(fd, "//")
        print >>fd, """\
#include "linuxcnc-ui-private.h"
#include <string.h>

%(ctype)s lui_get_%(cname)s(lui_t *lui) {
    if(!lui->status)
        return (%(ctype)s)0;
    else
        return (%(ctype)s)lui->status->%(dotname)s;
}""" % self.__dict__


class LuiGetterInplaceArray(LuiGetter):
    def __init__(self, *args, **kw):
        LuiGetter.__init__(self, *args, **kw)
        self.doc2 += """
.SH VALIDITY
The returned value is valid until the next call to
 \\fBlui_status_nml_update\\fR."""

    def do_cfile(self, fd):
        autogenerated_header(fd, "//")
        print >>fd, """\
#include "linuxcnc-ui-private.h"
#include <string.h>

%(ctype)s lui_get_%(cname)s(lui_t *lui) {
    if(!lui->status)
        return NULL;
    else
        return lui->status->%(dotname)s;
}""" % self.__dict__

class LuiGetterCounted(LuiGetter):
    def __init__(self, cname, ctype, dotname, count, *args, **kw):
        self.count = count
        LuiGetter.__init__(self, cname, ctype, dotname, *args, **kw)
        self.doc2 += """
.SH VALIDITY
The returned value is valid until the next call to
 \\fBlui_status_nml_update\\fR."""

    def do_hfile(self, fd):
        print >>fd, """\
%(ctype)s lui_get_%(cname)s(lui_t *lui, size_t *);
size_t lui_get_%(cname)s_count(lui_t *lui);
%(ctype)s lui_get_%(cname)s_idx(lui_t *lui, size_t);""" % self.__dict__


    def do_cfile(self, fd):
        autogenerated_header(fd, "//")
        print >>fd, """\
#include "linuxcnc-ui-private.h"
#include <string.h>

#define STATIC_ASSERT(COND,MSG) \\
    typedef char static_assertion_##MSG[(COND)?1:-1] \\
    __attribute__((unused))

%(ctype)s lui_get_%(cname)s(lui_t *lui, size_t *count) {
    if(!lui->status) {
        if(count) *count = 0;
        return NULL;
    } else {
        if(count) *count = (%(count)s);
        %(ctype)s result = (%(ctype)s)lui->status->%(dotname)s;
        STATIC_ASSERT(sizeof(*result) == sizeof(*lui->status->%(dotname)s),
            matching_result_size);
        return result;
    }
}

size_t lui_get_%(cname)s_count(lui_t *lui) {
    return %(count)s;
}

%(ctype)s lui_get_%(cname)s_idx(lui_t *lui, size_t idx) {
    if(!lui->status)
        return NULL;
    if(idx < 0) return NULL;
    if(idx >= (%(count)s)) return NULL;
    return (%(ctype)s)(&((lui->status->%(dotname)s)[idx]));
}
""" % self.__dict__


    def do_manfile(self, fd):
        autogenerated_header(fd, '.\\"')
        print >>fd, '.TH LinuxCNC "1" "%s" "LinuxCNC Documentation" "The Enhanced Machine Controller' % (time.strftime("%F", time.localtime()))
        print >>fd, '''\
.SH NAME
lui_get_%(cname)s \- get %(doc1)s%(deprecated)s
.SH SYNOPSIS
.nf
.B #include <linuxcnc-ui.h>
.sp
.BI "%(ctype)s lui_get_%(cname)s(lui_t *" lui, "size_t * " count );
.sp 0
.BI "size_t lui_get_%(cname)s_count(lui_t *" lui );
.sp 0
.BI "%(ctype)s lui_get_%(cname)s_idx(lui_t *" lui, size_t i );
.fi
.SH DESCRIPTION
After a successful call to \\fBlui_status_nml_update\\fR, lui_get_%(cname)s
retrieves a pointer to an array of values.  The number of values is returned
via the out-parameter count; the valid indices are 0 through (count-1)
inclusive.

After a successful call to \\fBlui_status_nml_update\\fR,
lui_get_%(cname)s_count returns the number of items.  This count may
change at calls to \\fBlui_status_nml_update\\fR.

After a successful call to \\fBlui_status_nml_update\\fR,
lui_get_%(cname)s_idx returns a poointer to the i'th value.  If i is out
of range, NULL is returned.
"

%(doc2)s''' % self.__dict__

class LuiGetterShadowCounted(LuiGetterCounted):
    def do_cfile(self, fd):
        autogenerated_header(fd, "//")
        print >>fd, """\
#include "linuxcnc-ui-private.h"
#include <string.h>

#define STATIC_ASSERT(COND,MSG) \\
    typedef char static_assertion_##MSG[(COND)?1:-1] \\
    __attribute__((unused))

%(ctype)s lui_get_%(cname)s(lui_t *lui, size_t *count) {
    if(!lui->status) {
        if(count) *count = 0;
        return NULL;
    } else {
        if(count) *count = (%(count)s);
        %(ctype)s result = (%(ctype)s)lui->%(dotname)s;
        STATIC_ASSERT(sizeof(*result) == sizeof(*lui->%(dotname)s),
            matching_result_size);
        return result;
    }
}

size_t lui_get_%(cname)s_count(lui_t *lui) {
    return %(count)s;
}

%(ctype)s lui_get_%(cname)s_idx(lui_t *lui, size_t idx) {
    if(!lui->status)
        return NULL;
    if(idx < 0) return NULL;
    if(idx >= (%(count)s)) return NULL;
    return (%(ctype)s)(&((lui->%(dotname)s)[idx]));
}
""" % self.__dict__




# "unused" comments below apply to in-tree python scripts using linuxcncmodule
# stat
LuiGetterSimple('echo_serial_number', 'int', 'echo_serial_number',
    'last serial number received by task',
    deprecated=True)
LuiGetterSimple('status', 'int', 'status',
    'execution status of current command',
    '.SH RETURN VALUE\none of RCS_DONE, RCS_EXEC, or RCS_ERROR',
    deprecated=True)

# task
LuiGetterSimple('task_mode', 'lui_task_mode_t', 'task.mode',
    'state of the task controller (MDI, manual, auto).',
    '.SH RETURN VALUE\nOne of the values of lui_task_mode_t.')
LuiGetterSimple('task_state', 'lui_task_state_t', 'task.state',
    'state of the machine (estop, machine off, machine on).',
    '.SH RETURN VALUE\nOne of the values of lui_task_mode_t.')
LuiGetterSimple('exec_state', 'lui_exec_state_t', 'task.execState',
    'execution state of the machine',
    '.SH RETURN VALUE\nOne of the values of lui_exec_state_t.')
LuiGetterSimple('interp_state', 'lui_interp_state_t', 'task.interpState',
    'execution state of the interpreter',
    '.SH RETURN VALUE\nOne of the values of lui_interp_state_t.')
# read_line unused
LuiGetterSimple('motion_line', 'int', 'task.motionLine',
    'line number of last motion command issued by interpreter')
LuiGetterSimple('current_line', 'int', 'task.currentLine',
    'line number of currently execution motion')
LuiGetterInplaceArray('file', 'char *', 'task.file',
    'path to part program')
# command unused
LuiGetterSimple('program_units', 'lui_linear_units_t', 'task.programUnits',
    'The interpreter\'s current linear units (set by G20/G21)',
    '.SH RETURN VALUE\nOne of the values of lui_linear_units_t')
# interpreter_errorcode unused
LuiGetterSimple('optional_stop', 'bool', 'task.optional_stop_state',
    'current state of the "optional stop" toggle')
LuiGetterSimple('block_delete', 'bool', 'task.block_delete_state',
    'current state of the "block delete" toggle')
LuiGetterSimple('task_paused', 'bool', 'task.task_paused',
    'current state of the "pause" toggle')
# input_timeout unused
LuiGetterSimple('rotation_xy', 'double', 'task.rotation_xy',
    'the interpreter\'s current XY rotation in degrees')
LuiGetterSimple('delay_left', 'double', 'task.delayLeft',
    'the remaining time in an ongoing dwell, in seconds')
LuiGetterSimple('queued_mdi_commands', 'int', 'task.queuedMDIcommands',
    'the number of queued MDI commands')

LuiGetterCounted('active_gcodes', 'int *', 'task.activeGCodes',
    'ACTIVE_G_CODES',
    'active modal g-codes',
    '.SH RETURN VALUE\n'
    'The active modal g-codes multiplied by ten, so G1 is denoted by\n'
    'the value 10, and G33.1 is denoted by the value 331.  -1 represents\n'
    'a lack of a modal code.\n'
    '.SH NOTES\n'
    'This representation of active modal g-codes is chosen because\n'
    'most multiples of 0.1 cannot be exactly represented as binary\n'
    'floating-point numbers.\n'
    '\n'
    'Internally, the interpreter organizes modal codes in groups (e.g.,\n'
    'G1 and G2 are in the same group).  It is possible for no modal code\n'
    'in a group to be active.\n.  It is in this case that the value -1 is\n'
    'returned as an array element.')

# At the time of writing, ACTIVE_M_CODES is 10,
# activeMCodes[0] is the sequence number and [9] is not used.
# Don't present the sequence number as though it were an mcode
LuiGetterCounted('active_mcodes', 'int *', 'task.activeMCodes+1',
    8,
    'active modal m-codes'
    '.SH RETURN VALUE\n'
    'Unlike modal g-codes, these values are not multiplied by 10, so M5\n'
    'is denoted by the value 5.  -1 represents a lack of a modal code.\n'
    '\n'
    'Internally, the interpreter organizes modal codes in groups (e.g.,\n'
    'M3 and M5 are in the same group).  It is possible for no modal code\n'
    'in a group to be active.\n.  It is in this case that the value -1 is\n'
    'returned as an array element.')

LuiGetterSimple('interpreter_spindle_speed', 'double', 'task.activeSettings[2]',
    'the last commanded S value'
    '.SH NOTES\n'
    'This is the last S-value commanded in gcode.  Using the start/stop\n'
    'and increase/decrease "manual" spindle controls does not affect this\n'
    'value.')
LuiGetterSimple('interpreter_feed_number', 'double', 'task.activeSettings[1]',
    'the last commanded F value'
    '.SH NOTES\n'
    'This is the last F-value commanded in gcode, in interpreter units.'    
    'Using the feed-affecting controls such as feed override and max velocity\n'
    'does not affect this value.')

# motion
LuiGetterSimple('linear_units', 'double', 'motion.traj.linearUnits',
    'the machine\'s linear units',
    '.SH RETURN VALUE\n'
    'Multiply linear position values (XYZ UVW) by this value to obtain inches.\n')
LuiGetterSimple('angular_units', 'double',
    'motion.traj.angularUnits',
    'the machine\'s angular units',
    '.SH RETURN VALUE\n'
    'Multiply angular position values (ABC) by this value to obtain degrees.\n')
# cycle_time unused
LuiGetterSimple('axes', 'int',
    'motion.traj.axes',
    'the number of the highest existing axis plus one',
    '.SH RETURN VALUE\n'
    'Possible return values include 3 for an XYZ or XZ machine,\n'
    '8 for an XYUV machine, etc.  To determine the axes that actually\n'
    'exist, use lui_get_axis_mask\n')
LuiGetterSimple('axis_mask', 'int',
    'motion.traj.axis_mask',
    'a bitmask representing axes that exist on the machine',
    '.SH RETURN VALUE\n'
    'Axes are numbered starting with X=0 and in the order XYZ ABC UVW.\n'
    'Possible return values include 7 for an XYZ machine,\n'
    '5 for an XZ machine, etc.')
LuiGetterSimple('traj_mode', 'lui_traj_mode_t', 'motion.traj.mode',
    'whether motions are planned in joint or world coordinates')
LuiGetterSimple('enabled', 'bool', 'motion.traj.enabled',
    'whether the machine is enabled'
    '.SH BUGS\n'
    'How is this different than task_state == lui_task_state_on?')
# inpos unused
LuiGetterSimple('queue_length', 'int', 'motion.traj.queue',
    'length of the realtime motion queue')
# active_queue unused
LuiGetterSimple('queue_full', 'bool', 'motion.traj.queueFull',
    'whether the realtime motion queue is full')
# id unused
LuiGetterSimple('paused', 'bool', 'motion.traj.paused',
    'whether the realtime motion loop is paused')
# velocity, acceleration unused
LuiGetterSimple('max_velocity', 'double', 'motion.traj.maxVelocity',
    'the maximum velocity of any linear axis')
# max_acceleration unused
# probe_tripped, probing unused
LuiGetterSimple('kinematics_type', 'lui_kinematics_type_t', 'motion.traj.kinematics_type',
    'the machine\'s kinematics type')
# motion_type unused
LuiGetterSimple('distance_to_go', 'double', 'motion.traj.distance_to_go',
    'the distaince remaining in the current move',
    '.SH RETURN VALUE\n'
    'For a purely linear move, the linear distance remaining.  For radial\n'
    'and mixed moves, I\'m unsure of the interpretation of the value')
LuiGetterSimple('current_vel', 'double', 'motion.traj.current_vel',
    'the current machine velocity',
    '.SH RETURN VALUE\n'
    'For a purely linear move, the linear velocity.  For radial\n'
    'and mixed moves, I\'m unsure of the interpretation of the value')
LuiGetterSimple('feed_override_enabled', 'bool', 'motion.traj.feed_override_enabled',
    'whether the feed override toggle is enabled')
LuiGetterSimple('spindle_override_enabled', 'bool', 'motion.traj.spindle_override_enabled',
    'whether the spindle override toggle is enabled')
LuiGetterSimple('adaptive_feed_enabled', 'bool', 'motion.traj.adaptive_feed_enabled',
    'whether the adaptive feed toggle is enabled')
LuiGetterSimple('feed_hold_enabled', 'bool', 'motion.traj.feed_hold_enabled',
    'whether the feed hold toggle is enabled')
LuiGetter('position', 'lui_position_t', 'motion.traj.position',
    'commanded position of the machine, in machine units',
    '.SH RETURN VALUE\n'
    'The nine-component commanded cartesian position of the machine.')
LuiGetter('actual', 'lui_position_t', 'motion.traj.actualPosition',
    'feedback position of the machine, in machine units',
    '.SH RETURN VALUE\n'
    'The nine-component feedback cartesian position of the machine.')

# spindle
LuiGetterSimple('spindle_speed', 'double', 'motion.spindle.speed',
    'commanded spindle speed in rpm')
LuiGetterSimple('spindle_direction', 'int', 'motion.spindle.direction',
    'commanded spindle direction')
LuiGetterSimple('spindle_brake', 'int', 'motion.spindle.brake',
    'whether the spindle brake is commanded to engage')
# spindle_increasing unused
LuiGetterSimple('spindle_enabled', 'bool', 'motion.spindle.enabled',
    'whether the spindle is enabled')
LuiGetterSimple('pocket_prepped', 'int', 'io.tool.pocketPrepped',
    'number of the prepared tool',
    '.SH BUGS\n'
    'For "nonrandom" TCs, this number is physical line number\n'
    'in the tool table (Tn).\n'
    'For "random" TCs, this number is the pocket number (Pn).',
    deprecated=True)
LuiGetterSimple('tool_in_spindle', 'int', 'io.tool.toolInSpindle',
    'tool number of the tool in the spindle')
LuiGetterCounted('tool_table', 'lui_tool_info_t *', 'io.tool.toolTable',
    'sizeof(lui->status->io.tool.toolTable) / sizeof(lui->status->io.tool.toolTable[0])',
    'information about tools in the tool table')

# other io
LuiGetterSimple('mist', 'bool', 'io.coolant.mist',
    'whether the mist coolant is commanded to run')
LuiGetterSimple('flood', 'bool', 'io.coolant.flood',
    'whether the flood coolant is commanded to run')
LuiGetterSimple('estop', 'bool', 'io.aux.estop',
    'whether the external estop input is asserted')
LuiGetterSimple('lube', 'bool', 'io.lube.on',
    'whether automatic lubrication is enabled')
LuiGetterSimple('lube_level', 'bool', 'io.lube.level',
    'whether the lube level sensor has tripped')

# offsets and such
LuiGetterSimple('g5x_index', 'int', 'task.g5x_index',
    'the number of the active g5x index',
    'This is the P-number that would be issued with G10 L2 to affect the\n'
    'offset.')
LuiGetter('g5x_offset', 'lui_position_t', 'task.g5x_offset',
    'the value of the active g5x offset, in machine units')
LuiGetter('g92_offset', 'lui_position_t', 'task.g92_offset',
    'the value of the active g92 offset, in machine units')
LuiGetter('tool_offset', 'lui_position_t', 'task.toolOffset',
    'the value of the active tool offset, in machine units')
LuiGetter('distance_to_go', 'lui_position_t', 'motion.traj.dtg',
    'distance to go in the current move, in user units')
LuiGetter('probed_position', 'lui_position_t', 'motion.traj.probedPosition',
    'distance to go in the current move, in user units')
LuiGetterCounted('digital_outputs', 'int *', 'motion.synch_di', 'EMC_MAX_DIO',
    'value of motion\'s digital outputs')
LuiGetterCounted('digital_inputs', 'int *', 'motion.synch_do', 'EMC_MAX_DIO',
    'value of motion\'s digital inputs')
LuiGetterCounted('analog_outputs', 'double *', 'motion.analog_input',
    'EMC_MAX_DIO',
    'value of motion\'s analog outputs')
LuiGetterCounted('analog_inputs', 'double *', 'motion.analog_output',
    'EMC_MAX_DIO',
    'value of motion\'s analog inputs')

LuiGetterShadowCounted('homed', 'int*', 'shadow_homed', 'EMC_AXIS_MAX',
    'Nonzero if the joint is homed, zero if it is not')
LuiGetterShadowCounted('on_limit', 'int*', 'shadow_limit', 'EMC_AXIS_MAX',
    'Indicates which of the joint\'s limit switches (if any) are active:\n'
    '1 = negative hard limit, 2 = positive hard limit,\n'
    '4 = negative soft limit, 8 = positive soft limit,\n')
LuiGetterShadowCounted('joint_commanded', 'double*', 'shadow_joint_commanded',
    'EMC_AXIS_MAX',
    'Commanded position for each joint')
LuiGetterShadowCounted('joint_actual', 'double*', 'shadow_joint_actual',
    'EMC_AXIS_MAX',
    'Feedback position for each joint')

def make_output_dir(f):
    dirname = os.path.dirname(f)
    if not dirname: return
    if not os.path.isdir(dirname):
        try: os.makedirs(dirname)
        except os.error as e:
            if e.errno != errno.EEXIST: raise

def main(args):
    if args[0] == 'makefile':
        make_output_dir(args[1])
        with open(args[1], "w") as f:
            autogenerated_header(f, "#")
            for g in getters.values():
                g.do_makefile(f)

    elif args[0] == 'cfile':
        g = getters[args[2]]
        make_output_dir(args[1])
        with open(args[1], "w") as f:
            g.do_cfile(f)

    elif args[0] == 'manfile':
        g = getters[args[2]]
        make_output_dir(args[1])
        with open(args[1], "w") as f:
            g.do_manfile(f)

    elif args[0] == 'hfile':
        make_output_dir(args[1])
        with open(args[1], "w") as f:
            autogenerated_header(f, "//")
            print >>f, "#include <stdbool.h>"
            print >>f, "#include <stddef.h>"
            for g in getters.values():
                g.do_hfile(f)

    else:
        raise SystemExit, "Unknown target %r" % args[1]

if __name__ == '__main__':
    main(sys.argv[1:])
