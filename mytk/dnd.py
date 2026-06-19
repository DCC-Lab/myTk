"""Drag-and-drop support for myTk — accept files dropped from the OS.

Tk has no native OS-level drag-and-drop. This wraps the **tkdnd** Tcl extension
(via the ``tkinterdnd2`` package) and retrofits it onto myTk's existing root
window, so any widget can opt in with :meth:`Base.accept_dropped_files` without
the app having to create a special drag-aware root.

tkdnd ships as a compiled library built against a specific Tcl major version, so
the right ``tkinterdnd2`` release is chosen from the running Tcl: the 0.4.x line
for Tcl 8.x, the latest for Tcl 9.x. If the extension still cannot be loaded
(for instance an incompatible build is already installed), drag-and-drop is
simply reported as unavailable and the calling code carries on without it.
"""

from .modulesmanager import ModulesManager

# Roots that already have tkdnd loaded, so we only retrofit each one once.
_dnd_ready_roots = set()


def _tkinterdnd2_spec(root):
    """pip spec for a ``tkinterdnd2`` whose tkdnd matches the running Tcl."""
    patchlevel = root.tk.call("info", "patchlevel")  # e.g. "8.6.17" / "9.0.1"
    major = int(patchlevel.split(".")[0])
    # 0.5.0+ bundles a Tcl-9 build; the 0.4.x line bundles a Tcl-8 build.
    return "tkinterdnd2" if major >= 9 else "tkinterdnd2==0.4.2"


def ensure_tkdnd(root, ask_for_confirmation=True):
    """Load tkdnd onto ``root``, installing a compatible tkinterdnd2 if needed.

    Returns the imported ``tkinterdnd2`` module when drag-and-drop is available
    on this root, or ``None`` if it could not be enabled (missing or
    incompatible extension). Importing the package also patches Tk's widget
    classes with the ``drop_target_register`` / ``dnd_bind`` methods.
    """
    spec = _tkinterdnd2_spec(root)
    ModulesManager.install_and_import_modules_if_absent(
        {spec: "tkinterdnd2"}, ask_for_confirmation=ask_for_confirmation
    )
    tkdnd = ModulesManager.imported.get(spec)
    if tkdnd is None:
        return None
    if root not in _dnd_ready_roots:
        try:
            tkdnd.TkinterDnD._require(root)
        except Exception:
            return None  # e.g. tkdnd built for a different Tcl major version
        _dnd_ready_roots.add(root)
    return tkdnd


def dropped_paths(root, event_data):
    """Parse a tkdnd ``<<Drop>>`` payload into a list of filesystem paths.

    tkdnd hands over a Tcl list (paths with spaces are brace-wrapped);
    ``splitlist`` turns it back into individual paths. Some file managers
    (notably GNOME/GTK) deliver ``file://`` URIs, sometimes percent-encoded
    and with trailing newlines, instead of plain paths, so each entry is
    normalized back to a local filesystem path. Blank entries are dropped.
    """
    from urllib.parse import unquote, urlparse

    paths = []
    for entry in root.tk.splitlist(event_data):
        entry = entry.strip()
        if not entry:
            continue
        if entry.startswith("file://"):
            entry = unquote(urlparse(entry).path)
        paths.append(entry)
    return paths
