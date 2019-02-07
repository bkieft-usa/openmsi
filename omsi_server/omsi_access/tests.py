"""
For more detailed information on how to implement tests in DJANGO see: https://docs.djangoproject.com/en/dev/topics/testing/overview/

ToDO: 
    
    * Add tests for different combinations of viewerOptions for analysis data
    * Generate seperate set of unittests for the analysis
    * Add tests for all different kinds of analysis 
    * Write test dataset at the beginning of the tests to allow for value checking
    * Check returned JSON object for correctness of the returned data
"""

from django.test import TestCase

"""Define the analysis dataset that should be used. As parameters may be defined in
   any order in the URL, one may add additional parameters (e.g., viewerOption) here
   to include them in all tests.
"""
test_data = "file=/work2/bowen/TEST_DEP3.h5&expIndex=0&dataIndex=0"
test_data_qcube = test_data
#test_data_qcube = "file=/work2/bowen/TEST_Links.h5&expIndex=0&anaIndex=0&anaDataName=peak_cube"
#test_data_qcube = "file=/work2/bowen/TEST_Links.h5&expIndex=0&anaIndex=1&anaDataName=ho"


#---------------------------------------------------------------#
#---------------------------------------------------------------#
#--  Test retrieval of spectra from raw MSI data              --#
#---------------------------------------------------------------#
#---------------------------------------------------------------#
class qspectrum(TestCase):
    """Test the retrieval of spectra from omsi data using the qspectrum URL pattern using a variety of data selection mechanisms"""
    
    def test_spectra_range_range1(self):
        """Test cases for selecting a set of spectra using two range selections in x and y."""
       
        #Retrieve PNG of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:5&col=4:6&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_spectra_range_range2(self):
        """Test cases for selecting a set of spectra using two range selections in x and y."""

        #Retrieve JSON of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:5&col=4:6&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_spectra_range_range3(self):
        """Test cases for selecting a set of spectra using two range selections in x and y."""

        #Retrieve JSON of unreduced object 
        testCall = "/qspectrum/?"+test_data+"&row=3:5&col=4:6&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_spectra_range_all1(self):
        """Test cases for selecting a set of spectra using a range selection for x and an all : selection for y"""       
        #Retrieve PNG of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:5&col=:&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_range_all2(self):
        #Retrieve JSON of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:5&col=:&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_range_all3(self):
        #Retrieve JSON of unreduced object 
        testCall = "/qspectrum/?"+test_data+"&row=3:5&col=:&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
       
    def test_spectra_range_index1(self):
        """Test cases for selecting a set of spectra using a range selection for x and an all : selection for y"""       
        #Retrieve PNG of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:5&col=3&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_range_index2(self):
        """Test cases for selecting a set of spectra using a range selection for x and an all : selection for y"""       
        #Retrieve JSON of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:5&col=3&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_range_index3(self):
        """Test cases for selecting a set of spectra using a range selection for x and an all : selection for y"""       
        #Retrieve JSON of unreduced object 
        testCall = "/qspectrum/?"+test_data+"&row=3:5&col=3&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
       
    def test_spectra_indexlist_range1(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and a range selection for y"""       
        #Retrieve PNG of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=4:8&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_indexlist_range2(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and a range selection for y"""       
        #Retrieve JSON of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=4:8&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_spectra_indexlist_range3(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and a range selection for y"""       
        #Retrieve JSON of unreduced object 
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=4:8&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
   
    def test_spectra_indexlist_all1(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and a all : selection for y"""       
        #Retrieve PNG of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=:&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_indexlist_all2(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and a all : selection for y"""       
        #Retrieve JSON of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=:&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_indexlist_all3(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and a all : selection for y"""       
        #Retrieve JSON of unreduced object 
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=:&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_indexlist_index1(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and an index selection for y"""       
        #Retrieve PNG of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=3&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_spectra_indexlist_index2(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and an index selection for y"""       
        #Retrieve JSON of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=3&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_indexlist_index3(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and an index selection for y"""       
        #Retrieve JSON of unreduced object 
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=3&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
       
    def test_spectra_indexlist_indexlist1(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and an indexlist selection for y"""       
        #Retrieve PNG of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=[4,8,12]&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_indexlist_indexlist2(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and an indexlist selection for y"""       
        #Retrieve JSON of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=[4,8,12]&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_spectra_indexlist_indexlist3(self):
        """Test cases for selecting a set of spectra using a indexlist selection for x and an indexlist selection for y"""       
        #Retrieve JSON of unreduced object 
        testCall = "/qspectrum/?"+test_data+"&row=[3,4,5]&col=[4,8,12]&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))


    def test_spectra_index_index1(self):
        """Test cases for selecting a set of spectra using a index selection for x and a index selection for y"""       
        #Retrieve PNG of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3&col=4&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_index_index2(self):
        """Test cases for selecting a set of spectra using a index selection for x and a index selection for y"""      
        #Retrieve JSON of mean spectrum
        testCall = "/qspectrum/?"+test_data+"&row=1&col=2&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_spectra_index_index3(self):
        """Test cases for selecting a set of spectra using a index selection for x and a index selection for y"""      
        #Retrieve JSON of unreduced object 
        testCall = "/qspectrum/?"+test_data+"&row=5&col=6&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        


#---------------------------------------------------------------#
#---------------------------------------------------------------#
#--  Test retrieval of difference spectra from raw MSI data   --#
#---------------------------------------------------------------#
#---------------------------------------------------------------#
class qspectrum_difference(TestCase):
    """Test the retrieval of difference spectra from omsi data using the qspectrum URL pattern using a variety of data selection mechanisms.
    
        For simplicity we here use range+range selections for the first spectrum and different combinations of selection for the
        second spectrum if possible. The selections for the first spectrum are tested in qspectrum_rawspectra.
    """
    
    def test_diffspectra_range_range1(self):
        """Test cases for selecting difference spectra using two range selections in x2 and y2."""
        #Retrieve PNG of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=PNG&reduction=mean&row2=4:7&col2=5:8&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
 
    def test_diffspectra_range_range2(self):
        """Test cases for selecting difference spectra using two range selections in x2 and y2."""
        #JSON object of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&reduction=mean&row2=4:7&col2=5:8&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_diffspectra_range_range3(self):
        """Test cases for selecting difference spectra using two range selections in x2 and y2."""
       #JSON object of unreduced multiple difference spectra
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&row2=4:7&col2=5:8"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    
    def test_diffspectra_range_all1(self):
        """Test cases for selecting difference spectra using a range + all selection  in x2 and y2."""
        #Retrieve PNG of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=PNG&reduction=mean&row2=4:7&col2=:&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_diffspectra_range_all2(self):
        """Test cases for selecting difference spectra using a range + all selection  in x2 and y2."""
        #JSON object of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&reduction=mean&row2=4:7&col2=:&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_diffspectra_range_all3(self):
        """Test cases for selecting difference spectra using a range + all selection  in x2 and y2."""
        #JSON object of unreduced multiple difference spectra
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=:&format=JSON&row2=4:7&col2=:"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
       
    def test_diffspectra_range_index1(self):
        """Test cases for selecting difference spectra using a range + index selection in x2 and y2."""
        #Retrieve PNG of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=PNG&reduction=mean&row2=4:7&col2=4&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_diffspectra_range_index2(self):
        """Test cases for selecting difference spectra using a range + index selection in x2 and y2."""
        #JSON object of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&reduction=mean&row2=4:7&col2=3&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_diffspectra_range_index3(self):
        """Test cases for selecting difference spectra using a range + index selection in x2 and y2."""
        #JSON object of unreduced multiple difference spectra
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:5&format=JSON&row2=4:7&col2=1"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
       
    def test_diffspectra_indexlist_range1(self):
        """Test cases for selecting difference spectra using a indexlist+range selection in x2 and y2."""
        #Retrieve PNG of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=PNG&reduction=mean&row2=[4,5,6]&col2=4:7&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_diffspectra_indexlist_range2(self):
        """Test cases for selecting difference spectra using a indexlist+range selection in x2 and y2."""
        #JSON object of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&reduction=mean&row2=[4,5,6]&col2=4:7&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_diffspectra_indexlist_range3(self):
        """Test cases for selecting difference spectra using a indexlist+range selection in x2 and y2."""
        #JSON object of unreduced multiple difference spectra
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&row2=[4,5,6]&col2=4:7"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
   
    def test_diffspectra_indexlist_all1(self):
        """Test cases for selecting difference spectra using a indexlist+range selection in x2 and y2."""
        #Retrieve PNG of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=PNG&reduction=mean&row2=[4,5,6]&col2=:&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_diffspectra_indexlist_all2(self):
        """Test cases for selecting difference spectra using a indexlist+range selection in x2 and y2."""
        #JSON object of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&reduction=mean&row2=[4,5,6]&col2=:&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_diffspectra_indexlist_all3(self):
        """Test cases for selecting difference spectra using a indexlist+range selection in x2 and y2."""
        #JSON object of unreduced multiple difference spectra
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=:&format=JSON&row2=[4,5,6]&col2=:"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
       
    def test_diffspectra_indexlist_index1(self):
        """Test cases for selecting difference spectra using a indexlist+index selection in x2 and y2."""
        #Retrieve PNG of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=PNG&reduction=mean&row2=[4,5,6]&col2=2&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_diffspectra_indexlist_index2(self):
        """Test cases for selecting difference spectra using a indexlist+index selection in x2 and y2."""
        #JSON object of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&reduction=mean&row2=[4,5,6]&col2=3&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_diffspectra_indexlist_index3(self):
        """Test cases for selecting difference spectra using a indexlist+index selection in x2 and y2."""
        #JSON object of unreduced multiple difference spectra
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=3&format=JSON&row2=[4,5,6]&col2=3"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
       
    def test_diffspectra_indexlist_indexlist1(self):
        """Test cases for selecting difference spectra using a indexlist+indexlist selection in x2 and y2."""
        #Retrieve PNG of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=PNG&reduction=mean&row2=[4,5,6]&col2=[4,5,6]&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_diffspectra_indexlist_indexlist2(self):
        """Test cases for selecting difference spectra using a indexlist+indexlist selection in x2 and y2."""
        #JSON object of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&reduction=mean&row2=[4,5,6]&col2=[4,5,6]&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_diffspectra_indexlist_indexlist3(self):
        """Test cases for selecting difference spectra using a indexlist+indexlist selection in x2 and y2."""
        #JSON object of unreduced multiple difference spectra
        testCall = "/qspectrum/?"+test_data+"&row=[7,8,9]&col=[10,11,12]&format=JSON&row2=[4,5,6]&col2=[4,5,6]"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
       
    def test_diffspectra_index_index1(self):
        """Test cases for selecting difference spectra using a index+index selection in x2 and y2."""
        #Retrieve PNG of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=PNG&reduction=mean&row2=3&col2=4&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
   
    def test_diffspectra_index_index2(self):
        """Test cases for selecting difference spectra using a index+index selection in x2 and y2."""
        #JSON object of mean difference spectrum
        testCall = "/qspectrum/?"+test_data+"&row=3:6&col=4:7&format=JSON&reduction=mean&row2=4&col2=5&reduction2=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
  
    def test_diffspectra_index_index3(self):
        """Test cases for selecting difference spectra using a index+index selection in x2 and y2."""
        #JSON object of unreduced multiple difference spectra
        testCall = "/qspectrum/?"+test_data+"&row=3&col=4&format=JSON&row2=7&col2=8"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        


#---------------------------------------------------------------#
#---------------------------------------------------------------#
#--  Test retrieval of general data                           --#
#---------------------------------------------------------------#
#---------------------------------------------------------------#
class qslice(TestCase):
    """Test the retrieval of data slices from omsi data using the qslice URL pattern using a variety of selection mechanisms"""
    
    def test_slice_range1(self):
        """Test selection of raw data slices via an indexlist"""
        #PNG image of mean slice
        testCall = "/qslice/?"+test_data+"&mz=0:5&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_slice_range2(self):
        """Test selection of raw data slices via an indexlist"""
        #JSON object of mean slice 
        testCall = "/qslice/?"+test_data+"&mz=0:5&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response) )

    def test_slice_range3(self):
        """Test selection of raw data slices via an indexlist"""
        #JSON object of unreduced slices
        testCall = "/qslice/?"+test_data+"&mz=0:5&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response) )
    
    def test_slice_indexlist1(self):
        """Test selection of raw data slices via a range selection"""
        #PNG image of mean slice
        testCall = "/qslice/?"+test_data+"&mz=[1,5,8]&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_slice_indexlist2(self):
        #JSON object of mean slice 
        testCall = "/qslice/?"+test_data+"&mz=[1,5,8]&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response) )
        
    def test_slice_indexlist3(self):
        #JSON object of unreduced slices
        testCall = "/qslice/?"+test_data+"&mz=[1,5,8]&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response) )
        
    def test_slice_index1(self):
        """Test selection of raw data slices via an index selection"""
        #PNG image of mean slice
        testCall = "/qslice/?"+test_data+"&mz=10:20&format=PNG&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_slice_index2(self):
        #JSON object of mean slice 
        testCall = "/qslice/?"+test_data+"&mz=10:20&format=JSON&reduction=mean"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response) )
    
    def test_slice_index3(self):
        #JSON object of unreduced slices
        testCall = "/qslice/?"+test_data+"&mz=10:20&format=JSON"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response) )
        


class qcube(TestCase):
    """Test the retrieval of data from omsi data using the qcube URL pattern using a variety of selection mechanisms"""
    
    def test_cube_range_range_range1(self):
        """Test selection of raw data using three range selections"""
        #JSON without reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=5:10&mz=10:20"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_range_range_range2(self):
        #JSON with reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=5:10&mz=10:20&reduction=mean&axis=2"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_range_range_range3(self):
        #JSON with multiple reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=5:10&mz=10:20&reduction=mean&axis=2&reduction2=max&axis2=1&reduction3=median&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
        
    def test_cube_range_index_index1(self):
        """Test selection of raw data via a range and two index selections"""
        #JSON without reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=5&mz=10"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
     
    def test_cube_range_index_index2(self):
        #JSON with reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=5&mz=10&reduction=mean&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
        
    def test_cube_range_index_all1(self):
        """Test selection of raw data via range, index and all selection"""
        #JSON without reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=5&mz=:"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_range_index_all2(self):
        #JSON with reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=5&mz=:&reduction=mean&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_range_index_all3(self):
        #JSON with multiple reduction. Reduction 2 is omitted and Reduction 1 and 3 are applied
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=5&mz=:&reduction=mean&axis=0&reduction3=max&axis3=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        

    def test_cube_range_indexlist_all1(self):
        """Test selection of raw data via range, index and all selection"""
        #JSON without reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=[4,5]&mz=:"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_range_indexlist_all2(self):
        #JSON with reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=[5]&mz=:&reduction=mean&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_range_indexlist_all3(self):
        #JSON with multiple reduction. 
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=[5]&mz=:&reduction=mean&axis=2&reduction2=max&axis=1&reduction3=max&axis3=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        

    def test_cube_range_indexlist_indexlist1(self):
        """Test selection of raw data via range, index and all selection"""
        #JSON without reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=[5,6]&mz=[4,5]"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_range_indexlist_indexlist2(self):
        """Test selection of raw data via range, index and all selection"""
        #JSON with reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=[5,5]&mz=[3,4]&reduction=mean&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_range_indexlist_indexlist3(self):
        """Test selection of raw data via range, index and all selection"""
        #JSON with multiple reduction. Reduction 2 is omitted and Reduction 1 and 3 are applied
        testCall = "/qcube/?"+test_data_qcube +"&row=1:4&col=[5,5]&mz=[2,4]&reduction=mean&axis=0&reduction3=max&axis3=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))


    def test_cube_indexlist_indexlist_indexlist1(self):
        """Test selection of raw data via three indexlist selections"""
        #JSON without reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,3,4]&col=[5,6,7]&mz=[4,5,10]"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_indexlist_indexlist_indexlist2(self):
        """Test selection of raw data via three indexlist selections"""
        #JSON with reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,4,5]&col=[5,5,6]&mz=[3,5,8]&reduction=mean&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_indexlist_indexlist_indexlist3(self):
        """Test selection of raw data via three indexlist selections"""
        #JSON with multiple reduction. Reduction 2 is omitted and Reduction 1 and 3 are applied
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,3,4]&col=[5,5,7]&mz=[3,5,8]&reduction=mean&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
        
    def test_cube_indexlist_indexlist_range1(self):
        """Test selection of raw data via indexlist, indexlist and range selection"""
        #JSON without reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,3,4]&col=[5,6,7]&mz=4:6"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
     
    def test_cube_indexlist_indexlist_range2(self):
        """Test selection of raw data via indexlist, indexlist and range selection"""
        #JSON with reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,4,5]&col=[5,5,5]&mz=5:8&reduction=mean&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_indexlist_indexlist_range3(self):
        """Test selection of raw data via indexlist, indexlist and range selection"""
        #JSON with multiple reduction. Reduction 2 is omitted and Reduction 1 and 3 are applied
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,3,4]&col=[5,5,5]&mz=3:5&reduction=mean&axis=0&reduction3=max&axis3=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        

    def test_cube_indexlist_index_range1(self):
        """Test selection of raw data via indexlist, index and range selection"""
        #JSON without reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,3,4]&col=1&mz=4:6"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_indexlist_index_range2(self):
        """Test selection of raw data via indexlist, index and range selection"""
        #JSON with reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,4,5]&col=5&mz=5:8:&reduction=mean&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_indexlist_index_range3(self):
        """Test selection of raw data via indexlist, index and range selection"""
        #JSON with multiple reduction. Reduction 2 is omitted and Reduction 1 and 3 are applied
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,3,4]&col=4&mz=3:5&reduction=mean&axis=0&reduction3=max&axis3=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
        
    def test_cube_indexlist_index_range1(self):
        """Test selection of raw data via indexlist, index and range selection"""
        #JSON without reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,3,4]&col=[1,5,6]&mz=4"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_indexlist_index_range2(self):
        """Test selection of raw data via indexlist, index and range selection"""
        #JSON with reduction
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,4,5]&col=[1,5,6]&mz=5&reduction=mean&axis=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_cube_indexlist_index_range3(self):
        """Test selection of raw data via indexlist, index and range selection"""
        #JSON with multiple reduction. Reduction 2 is omitted and Reduction 1 and 3 are applied
        testCall = "/qcube/?"+test_data_qcube +"&row=[1,3,4]&col=[1,5,6]&mz=6&reduction=mean&axis=0&reduction3=max&axis3=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))


#---------------------------------------------------------------#
#---------------------------------------------------------------#
#--  Test retrieval of spectra from raw MSI data              --#
#---------------------------------------------------------------#
#---------------------------------------------------------------#
class qmetadata(TestCase):
    """Test the retrieval of spectra from omsi data using the qspectrum URL pattern using a variety of data selection mechanisms"""
    
    def test_metadata_filelist(self):
        """Test retrieval of list of available files"""
       
        testCall = "/qmetadata/?mtype=filelist"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_metadata_file(self):
        """Test retrieval of file metadata"""
       
        testCall = "/qmetadata/?"+test_data+"&mtype=file"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
    
    def test_metadata_experiment(self):
        """Test retrieval of experiment metadata """
       
        testCall = "/qmetadata/?"+test_data+"&mtype=experiment"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_metadata_experimentFull(self):
        """Test retrieval of full experiment metadata"""
       
        testCall = "/qmetadata/?"+test_data+"&mtype=experimentFull"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_metadata_analysis(self):
        """Test retrieval of analsis metadata"""
       
        testCall = "/qmetadata/?"+test_data+"&mtype=analysis&anaIndex=0"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_metadata_instrument(self):
        """Test retrieval of instrument metadata"""
       
        testCall = "/qmetadata/?"+test_data+"&mtype=instrument"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))
        
    def test_metadata_methods(self):
        """Test retrieval of method metadata"""
       
        testCall = "/qmetadata/?"+test_data+"&mtype=method"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

    def test_metadata_dataset(self):
        """Test retrieval of dataset metadata"""
       
        testCall = "/qmetadata/?"+test_data+"&mtype=dataset"
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))


class qmz(TestCase):
    """Test the retrieval m/z axis information using the qmz url pattern"""

    def test_qmz(self):
        """Test retrieval of file metadata"""
       
        testCall = "/qmz/?"+test_data
        response = self.client.get( testCall )
        self.assertEqual(response.status_code, 200, msg=testCall+str(response))

