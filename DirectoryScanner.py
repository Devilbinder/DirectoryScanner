import os
import platform
import json

class DirScan():
    def __init__(self,root_dir:str,include_filter:list = [],exclude_dir:list = [],include_file = True, sep = os.sep) -> None:
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
                    file_dir = ''.join([sep_replace,file])
                else:
                    file_dir = ''.join([sep_replace])

                if file_dir not in self.dir_list:
                    self.dir_list.append(file_dir)

    def __filter_files(self) -> None:
        self.file_filter = []
        if self.include_file == False:
            self.file_filter = self.dir_list
            return
        if self.include_filter == []:
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

    def __init__(self, root_dir: str, include_filter: list = [], exclude_dir: list = []) -> None:
        super().__init__(root_dir, include_filter, exclude_dir, include_file = False,sep = '/')

    def create_cpp_config(self,append_file_path:str = '') -> None:
        filter_dirs = super().scan()
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

if __name__ == "__main__":

    exclude_dir = ['.git']

    scan = vsCode("I:\\workspace\\python\\dir_scanner\\pico-sdk", exclude_dir = exclude_dir)
    scan.create_cpp_config('./.vscode/c_cpp_properties.json')
    scan.scan_to_file('paths.txt')
    pass