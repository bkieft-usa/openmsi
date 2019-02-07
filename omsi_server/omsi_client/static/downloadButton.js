$(document).on("click", "#saveButton", function () {
     var myURL = api_root + "openmsi/client/viewer/" + "?file=" + encodeURIComponent(omsi_globals.filename) + "&"+omsi_globals.useIndex + "&expIndex=0&channel1Value=" + omsi_globals.channel1Value + "&channel1RangeValue=" + omsi_globals.channel1Range + "&channel2Value="+omsi_globals.channel2Value + "&channel2RangeValue="+omsi_globals.channel2Range + "&channel3Value=" + omsi_globals.channel3Value + "&channel3RangeValue="+omsi_globals.channel3Range  + "&rangeValue=" + omsi_globals.channel1Range + "&cursorCol1=" + omsi_globals.points[0].x + "&cursorRow1=" + omsi_globals.points[0].y + "&cursorCol2=" + omsi_globals.points[1].x + "&cursorRow2=" + omsi_globals.points[1].y +"&enableClientCache=false";
           $(".modal-body #fileName").val( omsi_globals.filename );
           $(".modal-body #viewURL").val( myURL );
      
       var theImage = omsi_globals.canvas.toDataURL('image/png');
          $(".modal-body #msi-img").attr('src', theImage);
          $(".modal-body #saveImageButton").attr('href', theImage);
          $(".modal-body #saveImageButton").attr('download', "Image.png");
                          
          var $container = $('#graph1'),
                   // Canvg requires trimmed content
           content = $container.html().trim(),
           // canvas = document.getElementById('svg-canvas');
           
           canvas = $(".modal-body #svg-canvas1")[0];
        
           // Draw svg on canvas
           canvg(canvas, content);
               
           $(".modal-body #saveSVGSpectra1Button").attr('href', 'data:application/svg;charset=utf-8,' + encodeURIComponent($('#graph1').html()));
           $(".modal-body #saveSVGSpectra1Button").attr('download', "Spectra1.svg");
           $(".modal-body #saveSVGSpectra2Button").attr('href', 'data:application/svg;charset=utf-8,' + encodeURIComponent($('#graph2').html()));
           $(".modal-body #saveSVGSpectra2Button").attr('download', "Spectra2.svg");
           $( ".modal-body #saveSpectra1Button" ).click(function() {
               var inMem = document.createElement('canvas');
               // // The larger size
               inMem.width = canvas.width*1.5; 
               inMem.height = canvas.height*1.5; 
        
               canvg(inMem, content, { 'ignoreMouse:': true,
               'ignoreAnimation': true,
               'ignoreDimensions': true,
               'scaleWidth': inMem.width,
               'scaleHeight': inMem.height});
        
               var theImage = inMem.toDataURL('image/png');
               $(".modal-body #saveSpectra1Button").attr('href', theImage);
               $(".modal-body #saveSpectra1Button").attr('download', "Spectra1.png");
           });
           var $container2 = $('#graph2'),
           // Canvg requires trimmed content
           content2 = $container2.html().trim(),
           canvas2 = $(".modal-body #svg-canvas2")[0];
           // Draw svg on canvas
           canvg(canvas2, content2);  
                                  
           $( ".modal-body #saveSpectra2Button" ).click(function() {
               var inMem2 = document.createElement('canvas');
               // inMem.setAttribute("style","width:1000px;height:1000px;");
               // // The larger size
               inMem2.width = canvas.width*1.5; //canvas.width*4;
               inMem2.height = canvas.height*1.5; //canvas.height*4;
        
               canvg(inMem2, content2, { 'ignoreMouse:': true,
               'ignoreAnimation': true,
               'ignoreDimensions': true,
               'scaleWidth': inMem2.width,
               'scaleHeight': inMem2.height});//, { 'scaleWidth': 1000, 'scaleHeight': 1000});//, {scaleWidth: 1000, scaleHeight: 700});
        
               var theImage2 = inMem2.toDataURL('image/png');
               $(".modal-body #saveSpectra2Button").attr('href', theImage2);
               $(".modal-body #saveSpectra2Button").attr('download', "Spectra2.png"); 
           });
});
