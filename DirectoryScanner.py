import os
import platform
import json
import sys
import getopt

class DirScan():

    def __init__(self,root_dir:str,include_filter:tuple = (),exclude_dir:list = [],include_file = True, sep = os.sep) -> None:
        if(os.path.isdir(root_dir) == False):
            raise  RuntimeError("Failed to find directory")
        self.root_dir = root_dir
        self.include_filter = include_filter
        self.exclude_dir = exclude_dir
        self.dir_list = []
        self.include_file = include_file
        self.sep = sep
        pass

    def __scan_dir(self) -> None:
        self.dir_list = []
        for root, _ , files in os.walk(self.root_dir):
            if files == []:
                continue

            for file in files:
                sep_replace = root.replace(os.sep,self.sep)
                if self.include_file == True:
                    file_dir = ''.join([sep_replace,self.sep,file])
                else:
                    file_dir = ''.join([sep_replace])

                if file_dir not in self.dir_list:
                    self.dir_list.append(file_dir)

    def __filter_files(self) -> None:
        self.file_filter = []
        if self.include_file == False:
            self.file_filter = self.dir_list
            return
        if self.include_filter == ():
            self.file_filter = self.dir_list
            return
        for dir_to_file in self.dir_list:
            if dir_to_file.endswith(self.include_filter) == False:
                continue
            self.file_filter.append(dir_to_file)

    def __filter_dir(self) -> None:
        self.dir_filter = []
        for file in self.file_filter:
            isExcluded = False
            for exclude in self.exclude_dir:
                if exclude in file:
                    isExcluded = True
                    break
            if isExcluded == True:
                continue
            self.dir_filter.append(file)

    def scan(self):
        self.__scan_dir()
        self.__filter_files()
        self.__filter_dir()
        return self.dir_filter

    def scan_to_file(self,file_name:str) -> None:
        if file_name == None or file_name == '':
            raise ValueError("No file name given")
        scan_dirs = self.scan()
        with open(file_name,"w") as f:
            for dir in scan_dirs:
                f.write(dir + '\n')

class vsCode(DirScan):

    def __init__(self, root_dir: str, exclude_dir: list = []) -> None:
        include_filter =    (
                    ".c",
                    ".cpp",
                    ".h",
                    ".hpp",
                    ".S",
                    ".s"
                    ".ASM"
                    ".asm"
                    )
        super().__init__(root_dir, include_filter, exclude_dir, include_file = False,sep = '/')

    def create_cpp_config(self,append_file_path:str = '') -> None:
        filter_dirs = self.scan()
        filter_dirs = [x + '/*' for x in filter_dirs]

        if append_file_path == '':
            include_path = {"configurations":[{"name":platform.system(),"includePath":[]}],"version":4}
            include_path['configurations'][0]["includePath"] = filter_dirs
            vs_code = json.dumps(include_path,indent=4)
            with open("c_cpp_properties.json","w") as f:
                f.write(vs_code)
            return
        
        with open(append_file_path,'r') as f:
            file = f.read()

        include_path = json.loads(file)
        include_path['configurations'][0]["includePath"].extend(filter_dirs) 
        vs_code = json.dumps(include_path,indent=4)

        with open(append_file_path,"w") as f:
                f.write(vs_code)

class MakeFile(DirScan):

    def __init__(self, root_dir: str, root_dir_macro: str = 'ROOT_DIR', exclude_dir: list = []) -> None:
        include_filter =    (
                            ".c",
                            ".cpp",
                            ".h",
                            ".hpp",
                            ".S",
                            ".s"
                            ".ASM"
                            ".asm"
                            )
        self.root_dir_macro = root_dir_macro
        super().__init__(root_dir, include_filter, exclude_dir, include_file = True, sep = '/')
        self.root_dir = root_dir.replace('\\','/')

    def create_Makefile(self):
        filter_dirs = self.scan()
        root_var = "".join(['$(',self.root_dir_macro,')'])
        strip_root_dirs = [x.replace(self.root_dir,root_var) for x in filter_dirs]
        root_path = "".join([self.root_dir_macro,' := ', self.root_dir,"\n\n"])

        src_files  = "SRC_FILES += \\\n"
        inc_folder = "INC_FOLDERS += \\\n"

        for src in strip_root_dirs:
            if src.endswith((".c",".cpp",".S",".s",".ASM",".asm")) != True:
                continue

            # .join does not want to work here
            # "    ".join([scr,' \\\n']) results in   
            # scr "    " ' \\\n' for some reason
            # expected to work like below
            src_dir = "    " + src + " \\\n"

            # same story here as above
            src_files += src_dir

        src_files += '\n'

        for inc in strip_root_dirs:
            if inc.endswith((".h",".hpp")) != True:
                continue
            last_sep = inc.rfind('/')
            inc_folder += "    " + inc[:last_sep] + " \\\n"

        inc_folder += '\n'

        with open("Makefile","w") as f:
            f.write(root_path)
            f.write(src_files)
            f.write(inc_folder)


def print_help():
    print('help')
    exit()

def vs_Code(argv):
    exclude_dir = ['.git']
    try:
        opts, _ = getopt.getopt(argv,"d:e:f")
    except:
        print_help()
        print("Error")
    
    root_dir = '.'
    exclude_dir = ['.git']
    file_name = ''

    for opt,arg in opts:
        if opt in ["-d"]:
            root_dir = arg
            continue
        if opt in ["-e"]:
            exclude_dir = arg.split(',')
            continue
        if opt in ["-f"]:
            file_name = arg
            continue

    scan = vsCode(root_dir = root_dir, exclude_dir = exclude_dir)
    scan.create_cpp_config(file_name)
    

def makefile(argv):
    exclude_dir = ['.git']
    try:
        opts, _ = getopt.getopt(argv,"d:m:i")
    except:
        print_help()
        print("Error")

    root_dir = '.'
    root_makro = 'ROOT_DIR'
    exclude_dir = ['.git']

    for opt,arg in opts:
        if opt in ["-d"]:
            root_dir = arg
            continue
        if opt in ["-e"]:
            exclude_dir = arg.split(',')
            continue
        if opt in ["-m"]:
            root_makro = arg
            continue
        
    scan = MakeFile(root_dir, root_makro, exclude_dir = exclude_dir)
    scan.create_Makefile()

def dir_scan(argv):
    exclude_dir = ['.git']
    try:
        opts, _ = getopt.getopt(argv,"d:f:i:e:l:s")
    except:
        print_help()
        print("Error")

    root_dir = '.'
    file_name = 'paths.txt'
    include_filter = ()
    exclude_dir = ['.git']
    include_file = True
    sep = os.sep

    for opt,arg in opts:
        if opt in ["-d"]:
            root_dir = arg
            continue
        if opt in ["-f"]:
            file_name = arg
            continue
        if opt in ["-i"]:
            include_filter = tuple(arg.split(','))
            continue
        if opt in ["-e"]:
            exclude_dir = arg.split(',')
            continue
        if opt in ["-l"]:
            if arg == '0':
                include_file = True
                continue
            if arg == '1':
                continue
            print_help()
        if opt in ["-s"]:
            sep = arg
            continue
            
            
    scan = DirScan(root_dir,include_filter,exclude_dir,include_file,sep)
    scan.scan_to_file(file_name)


def main(type,argv):

    
    type_list = [['vsCode'],['Makefile']]

    if type in type_list:
        if type == ['vsCode']:
            vs_Code(argv)
            return

        if type == ['makefile']:
            makefile(argv)
            return
        if type == ['dirScan']:
            dir_scan(argv)
            return

        print_help()

    else:
        print_help()
    
    pass


if __name__ == "__main__":
    main(sys.argv[1:2],sys.argv[2:])
