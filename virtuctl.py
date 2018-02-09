import os
import subprocess

# You need to set appropriate PATH and CDS_AUTO_64BIT to run virtuoso

def setenv():
    """Sample to set environment variables"""
    os.environ['PATH'] = os.environ['PATH'] + ':/opt/eda/cadence/current/IC61/tools/bin:/opt/eda/cadence/current/IC61/tools/dfII/bin:/opt/eda/cadence/current/MMSIM13/bin'
    os.environ['CDS_AUTO_64BIT'] = 'ALL'
    os.environ['CDS_Netlisting_Mode'] = 'Analog'
    os.environ['CDS_LIC_FILE'] = '5280@vdec-cad1:5280@vdec-cad2:5280@vdec-cad3:5280@celtic.vdc.ss.titech.ac.jp'
    os.environ['CDS_INST_DIR'] = '/opt/eda/cadence/current/IC61'
    # If you use anagix tools:
    os.environ['PATH'] = os.environ['PATH'] + ':/usr/local/anagix_tools/bin'

def exec_command( command ):
    """Execute command in shell; returns command output""" 
    print('command to execute: "' + command + '"')
    print(subprocess.getoutput( command ))

alb_virtuctl_in_skill = '''
(defun virtuctl_get_cells (lib_name)
  lib = ddGetObj(lib_name)
  f=outfile("##cells")
  (foreach cell lib->cells
    fprintf(f " %s" cell->name))
  close(f)) 

(defun alb_open (libName cellName viewName @optional (mode "read"))
  (let ((cells (dbGetOpenCellViews))
	(found nil))
    (printf "Opened cells; ")
    (foreach cell cells
	    (printf "%s " cell->cellName)
	     (if (and (equal cell->cellName cellName)
		      (equal cell->libName libName))
		 (let ((win  (geGetCellViewWindow cell)))
		   (if win
		       (progn (hiRaiseWindow win)
			      (setq found win))))))
    (printf "\n")
    (or found
	(ddsServOpen libName cellName viewName mode))))

(defun alb_replace (cell new @optional (lib nil))
  (foreach inst getCurrentWindow()->cellView->instances
	   (when inst->cellName == cell
		 newlib = (lib || inst->libName)
		 inst->master = dbOpenCellViewByType(newlib new "symbol")
		 (printf "%s replaced w/ %s/%s for %s" cell inst->libName inst->cellName inst->name)
		 ))
  (schHiCheckAndSave))
'''

global virtuoso_dir
virtuoso_dir = None

def startup( dir='.', port=8125 ):
    """Start virtuoso under dir; port is used to communicate with it""" 
    import os
    import subprocess
    from time import sleep
    global virtuoso_dir

    os.environ['SKILLSERVPORT'] = str(port)
    print("SKILL SERVPORT is set to '%s'" % port) 
    cwd = os.getcwd()
    os.chdir(dir)
    try:
        virtuoso_dir = dir
        if not os.path.isfile('.cdsinit'):
            file = open('.cdsinit', 'w')
            file.write('print(".cdsinit will be executed")\n')
            file.write('load("~/.cdsinit")\n')
            file.write('load("/usr/local/anagix_tools/etc/skillServer.il")\n')
            file.close()
            
        if subprocess.getoutput('printenv DISPLAY') is '':
            print("ERROR: please set DISPLAY environment variable using os.environ['DISPLAY'] = ''")
        else:
            subprocess.Popen('virtuoso')
            with open("##alb_skills.il", "w") as f:
                f.write(alb_virtuctl_in_skill)
            while not virtuoso_is_alive(): sleep(0.5)
            exec_skill("load(\\\"##alb_skills.il\\\")") # defun virtuctl_get_cells etc.
    finally:
        os.chdir(cwd)

def openview(lib, cell, view):
    """Open lib/cell/view in active virtuoso session (can communicate w/ port)"""
    if virtuoso_is_alive():
        command = 'alb_open(\\"%s\\" \\"%s\\" \\"%s\\" \\"edit\\"); session=asiGetCurrentSession()'
        return(exec_skill(command % (lib, cell, view)))
    else:
        print("Please startup virtuoso first")

def exec_skill(command):
    """Execute skill command in active virtuoso session (can communicate w/ port)"""
    port = skillservport()
    ret = exec_command(('skillClient localhost %s ' % port) + '"' + command + '"')

def skillservport():
    """Returns an active port number which is usually set when startup() is called""" 
    port = 8123
    if not os.environ.get('SKILLSERVPORT') is None:
        port = os.environ['SKILLSERVPORT']
    return port

def virtuoso_is_alive():
    """Return 1 if virtuso session is active (can communicate w/ port)"""
    import os
    port = skillservport()
    ret = os.system('skillClient localhost %s "printf(\\\"Hello\\\")"' % port)
    if ret:
        return 0
    else:
        return 1

def netlist_and_run(): 
    """Netlist and Run in an active virtuoso session"""
    exec_skill("sevNetlistAndRun(stringToSymbol(_vivaGetSessionName()))")

import re
def text2csv(infile, output):
    """Convert ocnPrint output file to csv format"""
    with open(infile, "r") as f:
        content = f.readlines()
        
        with open(output, "w+") as f:
            for row in content[5:]: # skip first 4 lines
                #    print(row)
                csvline = re.sub(' +', ', ', re.sub(' *$', '', row))
                f.write(csvline)

def get_outputs( nets, outfile, start, stop, step, results_dir='asiGetResultsDir(session)', type='tran' ):
    """ocnPrint nets waveform to outfile which must have suffix '.txt'"""
    """print range must be specified w/ start, stop and step"""
    global virtuoso_dir
    from time import sleep
    waveforms =' '.join( map(lambda n: ('getData(\\"%s\\" ?resultsDir %s ?result \\"%s\\")' % (n, results_dir, type)),
                              nets))
    cwd = os.getcwd()
    os.chdir(virtuoso_dir)
    try:
        if os.path.exists(outfile): os.remove(outfile) 
        command = ('ocnPrint(%s ?output \\"%s\\" ?from %f ?to %f ?step %f ?numberNotation \'none)' %(waveforms, outfile, start, stop, step))
        exec_skill(command)
        while not os.path.exists(outfile): sleep(0.1)
        print(outfile + ' created!')
        if os.path.exists(outfile):
            csvfile = re.sub('.txt', '.csv', outfile)
            if os.path.exists(csvfile): os.remove(csvfile)
            text2csv(outfile, csvfile)
            os.chdir(cwd)
            return(csvfile)
    finally:
        os.chdir(cwd)
        return()

def get_variables(): # not used
    exec_skill("session=asiGetCurrentSession()")
    exec_skill("vars = asiGetDesignVarList(session)")
    exec_skill("f=outfile(\\\"result\\\"")
    exec_skill("fprint(f \\\"%L\\\" vars)")
    exec_skill("f.close")
    with open("result", 'r') as f:
        return(f.readlines())
    
get_variables_in_skill = '''
session=asiGetCurrentSession()
vars = asiGetDesignVarList(session)
f=outfile("##variables")
fprintf(f "%L" vars)
close(f)
'''

def setvars(names, gl=globals()):
    """Set virtuoso session variables (names given) with Python variable values"""
    import re
    global virtuoso_dir
    from time import sleep

    cwd = os.getcwd()
    os.chdir(virtuoso_dir)
    try:
        if os.path.exists('##variables'): os.remove('##variables')

        with open("getvars.il", "w") as f:
            f.write(get_variables_in_skill)

        exec_skill("load(\\\"getvars.il\\\")")
        while not os.path.exists('##variables'): sleep(0.1)

        with open("##variables") as f:
            vars = f.read()
            for name in re.sub(' *', '', names).split(','):
                vars = re.sub(('"%s" "[^"]*"' %name), ('"%s" "%f"' %(name, eval(name, gl))), vars)

        with open("setvars.il", 'w') as f:
            f.write("asiSetDesignVarList(session nil)\n")
            f.write("vars='%s\n" %vars)
            f.write("asiSetDesignVarList(session vars)\n")
        exec_skill("load(\\\"setvars.il\\\")")
    finally:
        os.chdir(cwd)
    return(vars)

def show_cells(library, pattern=None):
    """Returns a list of cells under the library"""
    from time import sleep
    global virtuoso_dir
    result_file = "%s/##cells" % virtuoso_dir
    if os.path.exists(result_file): os.remove(result_file)
    exec_skill("virtuctl_get_cells(\\\"%s\\\")" %library)
    while not os.path.exists(result_file): sleep(0.1)
    with open(result_file) as f:
        cells = f.read()[1:].split(' ')
        if pattern:
            import re
            matched_list = []
            for cell in cells:
                if re.search(pattern, cell):
                    matched_list.append(cell)
            return matched_list
        return(cells)

get_instances_in_skill = '''
f=outfile("##instances") 
cv=getCurrentWindow()->cellView 
foreach(inst cv->instances 
  fprintf(f "%s %s %s\\n" inst->name inst->libName inst->cellName))
close(f)
'''

def show_instances():
    """Show list of library, cell and instances used in current cellview"""
    from time import sleep
    global virtuoso_dir

    with open("%s/get_instances.il" % virtuoso_dir, "w") as f:
        f.write(get_instances_in_skill)
    result_file = "%s/##instances" % virtuoso_dir
    if os.path.exists(result_file): os.remove(result_file)
    exec_skill("load(\\\"get_instances.il\\\")")
    while not os.path.exists(result_file): sleep(0.1)

    with open(result_file, 'r')  as f:
        results = f.readlines()

    instances = {}
    for line in results:
        (inst, lib, cell) = line[:-1].split(' ')
        if not lib in instances.keys():
            instances[lib] = {cell: [inst]}
        else:
            if not cell in instances[lib].keys():
                instances[lib][cell] = [inst]
            else:
                instances[lib][cell].append(inst)

    for lib in instances.keys():
        for cell in instances[lib].keys():
            print("%s/%s: " %(lib, cell), end='')
            print(instances[lib][cell])

def replace (cell, new, lib=None):
    '''Replace all cell instances with lib/new; lib defaults to current one if not given'''
    libstr = ''
    if lib: libstr = "\\\"%s\\\"" % lib
    exec_skill("alb_replace(\\\"%s\\\" \\\"%s\\\" %s)" % (cell, new, libstr))
    
