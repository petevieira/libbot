import gobject
import gtk

import bot_procman.sheriff as sheriff

COL_CMDS_TV_OBJ, \
COL_CMDS_TV_EXEC, \
COL_CMDS_TV_FULL_GROUP, \
COL_CMDS_TV_DISPLAY_NAME, \
COL_CMDS_TV_HOST, \
COL_CMDS_TV_STATUS_ACTUAL, \
COL_CMDS_TV_CPU_USAGE, \
COL_CMDS_TV_MEM_VSIZE, \
COL_CMDS_TV_AUTO_RESPAWN, \
NUM_CMDS_ROWS = range(10)

class SheriffCommandModel(gtk.TreeStore):
    def __init__(self, _sheriff):
        super(SheriffCommandModel, self).__init__( \
                gobject.TYPE_PYOBJECT,
                gobject.TYPE_STRING, # command executable
                gobject.TYPE_STRING, # group name
                gobject.TYPE_STRING, # display name
                gobject.TYPE_STRING, # host name
                gobject.TYPE_STRING, # status actual
                gobject.TYPE_STRING, # CPU usage
                gobject.TYPE_INT,    # memory vsize
                gobject.TYPE_BOOLEAN,# auto-respawn
                )

        self.sheriff = _sheriff
        self.group_row_references = {}

    def _find_or_make_group_row_reference(self, group_name):
        if not group_name:
            return None
        if group_name in self.group_row_references:
            return self.group_row_references[group_name]
        else:
            name_parts = group_name.split("/")
            if len(name_parts) > 1:
                parent_name = "/".join(name_parts[:-1])
                parent_row_ref = self._find_or_make_group_row_reference(parent_name)
                parent = self.get_iter(parent_row_ref.get_path())
            else:
                parent = None

            # add the group name to the command name column if visible
            # otherwise, add it to the nickname column
            new_row = (None,                    # COL_CMDS_TV_OBJ
                      "",                       # COL_CMDS_TV_EXEC
                      group_name,               # COL_CMDS_TV_FULL_GROUP
                      name_parts[-1],           # COL_CMDS_TV_DISPLAY_NAME
                      "",                       # COL_CMDS_TV_HOST
                      "",                       # COL_CMDS_TV_STATUS_ACTUAL
                      "",                       # COL_CMDS_TV_CPU_USAGE
                      0,                        # COL_CMDS_TV_MEM_VSIZE
                      False,                    # COL_CMDS_TV_AUTO_RESPAWN
                      )
            ts_iter = self.append(parent, new_row)
            trr = gtk.TreeRowReference (self, self.get_path (ts_iter))
            self.group_row_references[group_name] = trr
            return trr

    def get_known_group_names (self):
        return self.group_row_references.keys()

    def _delete_group_row_reference(self, trr):
        model_iter = self.get_iter(trr.get_path())
        group_name = self.get_value(model_iter, COL_CMDS_TV_FULL_GROUP)
        del self.group_row_references[group_name]
        self.remove(model_iter)

    def _is_group_row(self, model_iter):
        return self.iter_to_command(model_iter) is None

    def _update_cmd_row(self, model, path, model_iter, cmd, cmd_deps, to_reparent):
        cpu_str = "%.2f" % (cmd.cpu_usage * 100)
        mem_usage = int(cmd.mem_vsize_bytes / 1024)

        if cmd.nickname.strip():
            display_name = cmd.nickname
        else:
            display_name = "<unnamed>"

        model.set(model_iter,
                COL_CMDS_TV_EXEC, cmd.name,
                COL_CMDS_TV_DISPLAY_NAME, display_name,
                COL_CMDS_TV_STATUS_ACTUAL, cmd.status (),
                COL_CMDS_TV_HOST, cmd_deps[cmd].name,
                COL_CMDS_TV_CPU_USAGE, cpu_str,
                COL_CMDS_TV_MEM_VSIZE, mem_usage,
                COL_CMDS_TV_AUTO_RESPAWN, cmd.auto_respawn)

        # check that the command is in the correct group in the
        # treemodel
        correct_grr = self._find_or_make_group_row_reference(cmd.group)
        correct_parent_iter = None
        correct_parent_path = None
        actual_parent_path = None
        if correct_grr and correct_grr.get_path() is not None:
            correct_parent_iter = model.get_iter(correct_grr.get_path())
        actual_parent_iter = model.iter_parent(model_iter)

        if correct_parent_iter:
            correct_parent_path = model.get_path(correct_parent_iter)
        if actual_parent_iter:
            actual_parent_path = model.get_path(actual_parent_iter)

        if correct_parent_path != actual_parent_path:
            # schedule the command to be moved
            to_reparent.append((gtk.TreeRowReference(model, path), correct_grr))
#                print "moving %s (%s) (%s)" % (cmd.name,
#                        correct_parent_path, actual_parent_path)

    def _update_group_row(self, model, path, model_iter, cmd_deps):
        # row represents a procman group
        children = self.get_group_row_child_commands_recursive(model_iter)
        if not children:
            return

        # aggregate command status
        statuses = [ child.status () for child in children ]
        stopped_statuses = [sheriff.STOPPED_OK, sheriff.STOPPED_ERROR]
        if all ([s == statuses[0] for s in statuses]):
            status_str = statuses[0]
        elif all ([s in stopped_statuses for s in statuses]):
            status_str = "Stopped (Mixed)"
        else:
            status_str = "Mixed"

        # aggregate host information
        child_deps = set([ cmd_deps[child] for child in children \
                if child in cmd_deps ])
        if len(child_deps) == 1:
            dep_str = child_deps.pop().name
        else:
            dep_str = "Mixed"

        # aggregate CPU and memory usage
        cpu_total = sum ([cmd.cpu_usage for cmd in children])
        mem_total = sum ([cmd.mem_vsize_bytes / 1024 \
                for cmd in children])
        cpu_str = "%.2f" % (cpu_total * 100)

        model.set (model_iter,
                COL_CMDS_TV_STATUS_ACTUAL, status_str,
                COL_CMDS_TV_HOST, dep_str,
                COL_CMDS_TV_CPU_USAGE, cpu_str,
                COL_CMDS_TV_MEM_VSIZE, mem_total)

    def _update_row(self, model, path, model_iter, user_data):
        cmds, cmd_deps, cmd_rows_to_remove, to_reparent = user_data
        cmd = self.iter_to_command(model_iter)
        if cmd:
            if cmd in cmds:
                self._update_cmd_row(model, path, model_iter, cmd, cmd_deps, to_reparent)
                cmds.remove(cmd)
            else:
                cmd_rows_to_remove.append(gtk.TreeRowReference(model, path))
        else:
            self._update_group_row(model, path, model_iter, cmd_deps)

    def repopulate(self):
        cmds = set()
        cmd_deps = {}
        for deputy in self.sheriff.get_deputies ():
            for cmd in deputy.get_commands ():
                cmd_deps [cmd] = deputy
                cmds.add (cmd)
        cmd_rows_to_remove = []
        to_reparent = []

        # update every command and group row.  On return, the cmds set will
        # contain commands that were not updated (i.e., commands that need to
        # be added into the model)
        self.foreach(self._update_row,
                (cmds, cmd_deps, cmd_rows_to_remove, to_reparent))

        # reparent rows that are in the wrong group
        for trr, newparent_rr in to_reparent:
            orig_iter = self.get_iter(trr.get_path ())
            rowdata = self.get (orig_iter, *range(NUM_CMDS_ROWS))
            self.remove (orig_iter)

            newparent_iter = None
            if newparent_rr:
                newparent_iter = self.get_iter(newparent_rr.get_path())
            self.append(newparent_iter, rowdata)

        # remove rows that have been marked for deletion
        for trr in cmd_rows_to_remove:
            self.remove(self.get_iter(trr.get_path()))

        # remove group rows with no children
        groups_to_remove = []
        def _check_for_lonely_groups(model, path, model_iter, user_data):
            is_group = self._is_group_row(model_iter)
            if is_group and not model.iter_has_child(model_iter):
                groups_to_remove.append(gtk.TreeRowReference(model, path))
        self.foreach(_check_for_lonely_groups, None)
        for trr in groups_to_remove:
            self._delete_group_row_reference(trr)

        # create new rows for new commands
        for cmd in cmds:
            deputy = cmd_deps[cmd]
            parent = self._find_or_make_group_row_reference(cmd.group)

            new_row = (cmd,        # COL_CMDS_TV_OBJ
                cmd.name,          # COL_CMDS_TV_EXEC
                "",                # COL_CMDS_TV_FULL_GROUP
                cmd.nickname,      # COL_CMDS_TV_DISPLAY_NAME
                deputy.name,       # COL_CMDS_TV_HOST
                cmd.status (),     # COL_CMDS_TV_STATUS_ACTUAL
                "0",               # COL_CMDS_TV_CPU_USAGE
                0,                 # COL_CMDS_TV_MEM_VSIZE
                cmd.auto_respawn,  # COL_CMDS_TV_AUTO_RESPAWN
                )
            if parent:
                self.append(self.get_iter(parent.get_path()), new_row)
            else:
                self.append(None, new_row)

    def rows_to_commands(self, rows):
        col = COL_CMDS_TV_OBJ
        selected = set()
        for path in rows:
            cmds_iter = self.get_iter (path)
            cmd = self.get_value(cmds_iter, col)
            if cmd:
                selected.add(cmd)
            else:
                for child in self.get_group_row_child_commands_recursive(cmds_iter):
                    selected.add(child)
        return selected

    def iter_to_command(self, model_iter):
        return self.get_value(model_iter, COL_CMDS_TV_OBJ)

    def path_to_command(self, path):
        return self.iter_to_command(self.get_iter(path))

    def get_group_row_child_commands_recursive(self, group_iter):
        child_iter = self.iter_children(group_iter)
        children = []
        while child_iter:
            child_cmd = self.iter_to_command(child_iter)
            if child_cmd:
                children.append (child_cmd)
            else:
                children += self.get_group_row_child_commands_recursive(child_iter)
            child_iter = self.iter_next(child_iter)
        return children
