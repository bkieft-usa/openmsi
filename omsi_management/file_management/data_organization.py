import os
import sys
import warnings
from omsi.dataformat import *
import argparse


def main(argv=None):
    if argv is None:
        argv = sys.argv

    datareport = DataOrganizationReport()
    datareport.print_report()


class DataOrganizationReport(object):
    """
    Compile report of data organization.
    """
    def __init__(self):
        self.warning_records = []
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.data_organization = DataOrganization()
            self.warning_records += w

    def compile_report(self):
        """
        Generate string with the report.
        """
        report = ""
        report += "Original Data User Directories \n"
        report += "------------------------------ \n"
        report += " \n"
        for f in self.data_organization.original_data_user_dirs:
            report += unicode(f) + " \n"
        report += " \n"
        report += "Original Data Files \n"
        report += "------------------- \n"
        for f in self.data_organization.original_data_files:
            report += unicode(f) + " \n"
        report += " \n"
        report += "System Data User Directories \n"
        report += "---------------------------- \n"
        for f in self.data_organization.system_data_user_dirs:
            report += unicode(f) + " \n"
        report += " \n"
        report += "System Data User Files \n"
        report += "---------------------- \n"
        for f in self.data_organization.system_data_files:
            report += unicode(f) + " \n"
        report += " \n"
        report += "WARNINGS \n"
        report += "-------- \n"
        for warn in self.warning_records:
            report += unicode(warn) + " \n"
        
        report += "FILE MAPS \n"
        report += "--------- \n"
        report += str(self.data_organization.original_to_system_file_map)
        report += "\n\n"
        report += str(self.data_organization.system_to_original_file_map)
        report += "\n"
        for si, oi in enumerate(self.data_organization.system_to_original_file_map):
           if oi < 0:
               report += str(self.data_organization.system_data_files[si]) + "\n"

        return report

    def print_report(self):
        """
        Print the report to st.out
        """
        print self.compile_report()

    def save_report(self, outdir):
        """
        Save rst file of the report.

        :param outdir: Name of the output directory where all files should be saved.
        """
        outfile = open(os.path.join(os.path.abspath(outdir), "data_organization_summary.rst"), 'w')
        outfile.write(self.compile_report())
        outfile.close()


class DataOrganization(object):
    """
    Class used to help with the management of original data, converted files,
    and raw and converted data backed up on hpss.

    :ivar orginal_data_dirs: List of strings indicating the base directory where
                           original data files are stored.
    :ivar original_data_user_dirs: List of strings of user directors containing
                           original data files.
    :ivar original_data_files: List of dictionaries of original data files. Each dict
                           describes the: 'path', 'format_name', 'format_class', and
                           'user' of the file.
    :ivar system_data_dirs: List of strings of system data directories with 
                           converted data files.
    :ivar system_data_user_dirs: List of strings of user directories containing
                           converted data files.
    :ivar system_data_files: List of dictionaries of converted data files. Each
                           dict describes the 'path' and 'user' of the file.
    """
    def __init__(self, 
                 original_data_dirs="/project/projectdirs/openmsi/original_data",
                 system_data_dirs="/project/projectdirs/openmsi/omsi_data_private"):
        # Define all instance attributes.
        self.original_data_dirs = []
        self.original_data_user_dirs = []
        self.original_data_files = []
        self.system_data_dirs = []
        self.system_data_user_dirs = []
        self.system_data_files = []
        self.original_to_system_file_map = [] 
        self.system_to_original_file_map = []        

        # Initialize the original data location settings
        if isinstance(original_data_dirs, str) or isinstance(original_data_dirs, unicode):
            self.set_original_data_dirs([original_data_dirs])
        elif isinstance(original_data_dirs, list):
            self.set_system_data_dirs(original_data_dirs)
        else:
            raise ValueError("original_data_dirs must be a string or list of strings. " +
                             "Given "+str(type(original_data_dirs)))

        # Initialize the converted system data locations
        if isinstance(system_data_dirs, str) or isinstance(system_data_dirs, unicode):
            self.set_system_data_dirs([system_data_dirs])
        elif isinstance(system_data_dirs, list):
            self.set_system_data_dirs(system_data_dirs)
        else:
            raise ValueError("system_data_dirs must be a string or list of strings. " +
                             "Given "+str(type(original_data_dirs)))
       
        # Match the original and system data files to figure our which files have been converted
        self.__construct_original_and_system_file_maps__()  


    def __construct_original_and_system_file_maps__(self):
        """
        The function assumes that the self.system_data_files and self.original_data_files
        attributes have been initialized.
        """
        self.original_to_system_file_map = [-1]*len(self.original_data_files)
        self.system_to_original_file_map = [-1]*len(self.system_data_files)
        for oi, ov in enumerate(self.original_data_files):
             vs = ov['path'].lstrip(ov['user_dir'])
             vs = os.path.join(ov['user'], vs).rstrip('/')+'.h5'
             print "--------- "+vs
             for si, sv in enumerate(self.system_data_files):
                print "              "+sv['path']
                if sv['path'].endswith(vs):
                   self.original_to_system_file_map[oi] = si
                   self.system_to_original_file_map[si] = oi
          
 

    def set_original_data_dirs(self, data_dirs):
        """
        Define the list of original data locations. This also updates the list
        of original user data directories.

        :param data_dirs: List of strings of the original data locations.
        """
        # 1) Set the original data directories
        self.original_data_dirs = data_dirs
        # 2) Set the original data user directories
        self.original_data_user_dirs = []
        for currdir in self.original_data_dirs:
            self.original_data_user_dirs += [os.path.abspath(os.path.join(currdir, udir))
                                             for udir in os.listdir(currdir)
                                             if os.path.isdir(os.path.abspath(os.path.join(currdir, udir)))]
        # 3) Populate the self.original_data_files attribute
        self.__construct_original_filelist_from_user_dirs()

    def set_system_data_dirs(self, data_dirs):
        """
        Define the list of converted system data locations. This also updates the list
        of system user data directories.

        :param data_dirs: List of strings of the system data locations.
        """
        # 1) Set the system data directories
        self.system_data_dirs = data_dirs
        # 2) Set the system data user directories
        self.system_data_user_dirs = []
        for currdir in self.system_data_dirs:
            self.system_data_user_dirs += [os.path.abspath(os.path.join(currdir, udir))
                                           for udir in os.listdir(currdir)
                                           if os.path.isdir(os.path.abspath(os.path.join(currdir, udir)))]
        # 3) Populate the self.system_data_files attribute
        self.__construct_system_filelist_from_user_dirs__()

    def __construct_original_filelist_from_user_dirs(self):
        """
        This function is used to construct the dict of original user files
        based on the list of original data user directories. This function populates
        the self.original_data_files attribute and does not return any data.
        """
        # 1) Clear the list. The del construct ensures that all references to the list also see the empty list
        del self.original_data_files[0:len(self.original_data_files)]
        # 2) Repopulate the list of original data files
        formats = file_reader_base.file_reader_base.available_formats().items()
        for userdir in self.original_data_user_dirs:
            username = os.path.basename(userdir)
            for filedir in os.listdir(userdir):
                currdir = os.path.abspath(os.path.join(userdir, filedir))
                #print "OF : "+currdir
                currdescription = None
                for formatname, formatclass in formats:
                    if formatclass.is_valid_dataset(name=currdir):
                        currdescription = {'path': currdir,
                                           'format_name': formatname,
                                           'format_class': formatclass,
                                           'user': username,
                                           'user_dir': userdir}
                        break
                if currdescription is not None:
                    self.original_data_files.append(currdescription)
                else:
                    warnings.warn('Unrecognized file in user directory: '+currdir)

    def __construct_system_filelist_from_user_dirs__(self):
        """
        This function is used to construct the dict of converted system user files
        based on the list of system user directories. This function populates
        the self.original_data_files attribute and does not return any data.
        """
        # 1) Clear the list. The del construct ensures that all references to the list also see the empty list
        del self.system_data_files[0:len(self.system_data_files)]
        # 2) Repopulate the list of system data files
        for userdir in self.system_data_user_dirs:
            username = os.path.basename(userdir)
            for filename in os.listdir(userdir):
                currpath = os.path.abspath(os.path.join(userdir, filename))
                #print "SF : "+currpath
                if os.path.isfile(currpath):
                    if omsi_file.omsi_file.is_valid_dataset(name=currpath):
                        self.system_data_files.append({'path': currpath,
                                                       'user': username,
                                                       'user_dir': userdir})
                    else:
                        warnings.warn("Non OMSI file found in system user dir at: "+currpath)
                else:
                    warnings.warn("Unsupported subdirectory found in system user dir at: "+currpath)


if __name__ == "__main__":
    main()

