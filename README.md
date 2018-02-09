# virtuctl.py
Use virtuoso interactively from Juyter Notebook
Help on module virtuctl:

NAME
    virtuctl

FUNCTIONS
    exec_command(command)
        Execute command in shell; returns command output

    exec_skill(command)
        Execute skill command in active virtuoso session (can communicate w/ port)

    get_outputs(nets, outfile, start, stop, step, results_dir='asiGetResultsDir(session)', type='tran')
        ocnPrint nets waveform to outfile which must have suffix '.txt'

    get_variables()

    netlist_and_run()
        Netlist and Run in an active virtuoso session

    openview(lib, cell, view)
        Open lib/cell/view in active virtuoso session (can communicate w/ port)

    replace(cell, new, lib=None)
        Replace all cell instances with lib/new; lib defaults to current one if not given

    setenv()
        Sample to set environment variables
    
    setvars(names, globals()
        Set virtuoso session variables (names given) with Python variable values

    show_cells(library, pattern=None)
        Returns a list of cells under the library

    show_instances()
        Show list of library, cell and instances used in current cellview

    skillservport()
        Returns an active port number which is usually set when startup() is called

    startup(dir='.', port=8125)
        Start virtuoso under dir; port is used to communicate with it

    text2csv(infile, output)
        Convert ocnPrint output file to csv format

    virtuoso_is_alive()
        Return 1 if virtuso session is active (can communicate w/ port)

DATA
    alb_virtuctl_in_skill = '\n(defun virtuctl_get_cells (lib_name)\n  lib...
    get_instances_in_skill = '\nf=outfile("##instances") \ncv=getCurrentWi...
    get_variables_in_skill = '\nsession=asiGetCurrentSession()\nvars = asi...
    virtuoso_dir = None
