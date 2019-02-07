function getFileList(){
    // $('#viewerUnit').height($(window).height()*0.85);
    // if(window.innerWidth > 767) $('#imageCanvas').height($(window).height()*0.6).width($(window).width()*0.325);
    // else $('#imageCanvas').height(0.9*$(window).width*0.325/0.5).width($(window).width()*0.9);
    $('#imageCanvas').height(0.67*$(window).height()).width($(window).width()*0.345);
//    $.getJSON((api_root + 'qmetadata/?file=' + encodeURIComponent(omsi_globals.filename) + '&expIndex=0&mtype=file'),function(fileanalyses){
    $.getJSON((api_root + 'qmetadata/?file=' + encodeURIComponent(omsi_globals.filename) + '&mtype=file'),function(fileanalyses){

//        var numEntry = fileanalyses.num_exp; // number of entries in the file

//        if(fileanalyses.hasOwnProperty('manageURL')){
//            $('#managePermissionsButton').click(function() {
//                window.location = fileanalyses.manageURL;
//            });
//        }
//        else
//        {
//            $('#managePermissionsButton').hide();
//        }
//		console.log(JSON.stringify(fileanalyses.children[default_expIndex]))
//        var content = '';
//        for (var i = 0; i<numEntry; i++)
//        {
//            var numAna = fileanalyses.children[i].num_ana;
//            var numData = fileanalyses.children[i].num_msidata;
//            for (var j = 0; j<fileanalyses.children[i].children.length; j++)
//            {
//                console.log(fileanalyses.children[i].children[j].name)
//                console.log(fileanalyses.children[i].children[j].viewURL)
//                if (fileanalyses.children[i].children[j].hasOwnProperty('viewURL'))
//                {
//                    var label = fileanalyses.children[i].name + ' ' + fileanalyses.children[i].children[j].name
//                    var tempTooltip = 'tooltip';
//                    rel="tooltip" title='+tempTooltip+'
//                    content = content + '<li><a href='+fileanalyses.children[i].children[j].viewURL+'>'+label+'</a></li>';
//                }
//
//            }
//            for (var j = 0; j<numAna; j++)
//            {
////                console.log(fileanalyses.children[i].children[j].name)
////                console.log(fileanalyses.children[i].children[j].viewURL)
//                label = fileanalyses.children[i].name + ' ' + fileanalyses.children[i].children[j].name
//                content = content + '<li><a href='+fileanalyses.children[i].children[j].viewURL+'>'+label+'</a></li>';
//
//            }


//        }

//        filelist=fileanalyses.children[default_expIndex].ana_identifiers;

//        for (var i = 0; i<fileanalyses.children[default_expIndex].num_ana;i++)
//        {
//            content = content + '<li id = "anaIndex='+ i + '"><a>anaIndex=' + i + ', ' + filelist[i] + '</a></li>';
//        }
//        for (var i = 0;i<fileanalyses.children[default_expIndex].num_msidata; i++)
//        {
//            content = content + '<li id = "dataIndex='+ i + '"><a>dataIndex=' + i + '</a></li>';
//        }
//        $("#DataAndAnalysisList").html(content);


//        var anaId=omsi_globals.useIndex.replace("anaIndex=","analysis_");
        $("#SliceList").parents('.btn-group').find('.dropdown-toggle').html('Raw Peak Cube');
        $("#SpectrumList").parents('.btn-group').find('.dropdown-toggle').html('Raw Peak Cube');
//        $("#DataAndAnalysisList").parents('.btn-group').find('.dropdown-toggle').html(anaId+' <span class="caret"></span>');
        setImageAndSpectraPullDowns(fileanalyses.children[default_expIndex]);


//        $("#DataAndAnalysisList li").not('.emptyMessage').click(function() {
//
//            var selText = $(this).text();
//            $(this).parents('.btn-group').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');
//            omsi_globals.useIndex = this.id;
//            omsi_globals.qspectrum_viewerOption=0;
//            omsi_globals.qslice_viewerOption = 0;
//            // if (this.id>(filelist.length-1))
//            //          // userIndex is a variable that tells the qmz, qspectra, and qslice what command to put for getting spectra, images, and axes data
//            //          {
//            //              var elem = document.getElementById("redinput");
//            //              elem.value = "746.22";
//            //              elem.step = "0.25";
//            //              var elem = document.getElementById("greeninput");
//            //              elem.value = "621.98";
//            //              elem.step = "0.25";
//            //              var elem = document.getElementById("blueinput");
//            //              elem.value = "523.36";
//            //              elem.step = "0.25";
//            //              ViewModel.channel1Range('0.2');
//            //              ViewModel.channel2Range('0.2');
//            //              ViewModel.channel3Range('0.2');
//            //              ViewModel.channel1Value('746.22');
//            //              ViewModel.channel2Value('621.98');
//            //              ViewModel.channel3Value('523.36');
//            //          }
//            //          else
//            //          {
//            //              var elem = document.getElementById("redinput");
//            //              elem.step = "1";
//            //              var elem = document.getElementById("greeninput");
//            //              elem.step = "1";
//            //              var elem = document.getElementById("blueinput");
//            //              elem.step = "1";
//            //              ViewModel.channel1Range('0');
//            //              ViewModel.channel2Range('0');
//            //              ViewModel.channel3Range('0');
//            //              ViewModel.channel1Value('0');
//            //              ViewModel.channel2Value('1');
//            //              ViewModel.channel3Value('2');
//            //          }
//
//            setImageAndSpectraPullDowns(fileanalyses.children[default_expIndex]);
//            $('#panelAnalysis').slideToggle();
//            init(0);
//
//        });
    });
}
function setImageAndSpectraPullDowns(fileanalyses)
{
    // console.log(anaId);
    //dataIndex=0
    //anaIndex=1
    // var str="Visit Microsoft!";
    anaId=omsi_globals.useIndex.replace("anaIndex=","analysis_");
    if (anaId.substring(0,4)!="data"){
        var content = '';
        idx = findWithAttr(fileanalyses.children, "name", anaId)
        $("#SliceList").parents('.btn-group').find('.dropdown-toggle').html(fileanalyses.children[idx].qslice_viewerOptions[0]+' <span class="caret"></span>');
        $("#SpectrumList").parents('.btn-group').find('.dropdown-toggle').html(fileanalyses.children[idx].qspectrum_viewerOptions[0]+' <span class="caret"></span>');

        for (var i = 0; i<fileanalyses.children[idx].qspectrum_viewerOptions.length;i++)
        {
            content = content + '<li id = "spectrumOption='+ i + '"><a>' + fileanalyses.children[idx].qspectrum_viewerOptions[i] + '</a></li>';
        }
        $("#SpectrumList").html(content);
        content = '';
        for (var i = 0; i<fileanalyses.children[idx].qslice_viewerOptions.length;i++)
        {
            content = content + '<li id = "sliceOption='+ i + '"><a>' + fileanalyses.children[idx].qslice_viewerOptions[i] + '</a></li>';
        }
        $("#SliceList").html(content);
    }
    else
    {
        $("#SliceList").parents('.btn-group').find('.dropdown-toggle').html('Raw Peak Cube');
        $("#SliceList").html('');


        $("#SpectrumList").parents('.btn-group').find('.dropdown-toggle').html('Raw Peak Cube');
        $("#SpectrumList").html('');


    }
    $("#SpectrumList li").not('.emptyMessage').click(function() {
        // console.log($(this).attr('id'))
        var selText = $(this).text();
        $(this).parents('.btn-group').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');
        var idText = $(this).attr('id');
        var n = idText.split("=");
        omsi_globals.qspectrum_viewerOption = n[1];
        init(0);
    });
    $("#SliceList li").not('.emptyMessage').click(function() {
        // console.log($(this).attr('id'))
        var selText = $(this).text();
        $(this).parents('.btn-group').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');
        var idText = $(this).attr('id');
        var n = idText.split("=");
        omsi_globals.qslice_viewerOption = n[1];
        init(0);
    });
}

function addListeners() {
    document.getElementById("scaleplus").addEventListener("click", function(){
        omsi_globals.scale /= omsi_globals.scaleMultiplier;
        draw();
    }, false);

    document.getElementById("scaleminus").addEventListener("click", function(){
        omsi_globals.scale *= omsi_globals.scaleMultiplier;
        draw();
    }, false);
    document.getElementById("helpButton").addEventListener("click", function(){
        $('#canvashelp').modal('show');
    }, false);



    // add event listeners to handle screen drag and point selection
    omsi_globals.canvas.addEventListener("mousedown", function(evt){
        omsi_globals.mousedown = true;
        omsi_globals.startDragOffset.x = evt.pageX - omsi_globals.translatePos.x;
        omsi_globals.startDragOffset.y = evt.pageY - omsi_globals.translatePos.y;
        omsi_globals.startDrag.x = evt.pageX;
        omsi_globals.startDrag.y = evt.pageY;
        omsi_globals.dragindex = null;//clear drag index, which indicates the index of the selected point if one is beneath the cursor
        var npx = 16 / omsi_globals.scale; //the number of pixels' radius to consider a click on a given point
        var coord = pageToImgCoord(this,{x: evt.pageX, y: evt.pageY});
        var l = omsi_globals.points.length;
        for (i=0; i<l; i++){
            var theX = omsi_globals.points[i].x;
            var theY = omsi_globals.points[i].y;
            var coordx = coord.x;
            var coordy = coord.y;
            if (Math.sqrt(Math.pow(coordx-theX,2) + Math.pow(coordy - theY,2))<=npx){
                omsi_globals.dragindex = i;
            }
        }
    });

    omsi_globals.canvas.addEventListener("mouseup", function(evt){
        omsi_globals.mousedown = false;
        draw();

    });

    omsi_globals.canvas.addEventListener("mouseover", function(evt){
        omsi_globals.mousedown = false;
    });

    omsi_globals.canvas.addEventListener("mouseout", function(evt){
        omsi_globals.mousedown = false;
    });

    omsi_globals.canvas.addEventListener("mousemove", function(evt){
        if (omsi_globals.mousedown) {
            if(omsi_globals.dragindex != null){
                //the user previously moused down on a selected point (to drag it)
                var i = omsi_globals.dragindex;
                var coord = pageToImgCoord(this, {x: evt.pageX, y: evt.pageY});

                omsi_globals.points[omsi_globals.dragindex].x = coord.x;
                omsi_globals.points[omsi_globals.dragindex].y = coord.y;
                updateCoords();
                draw();
            }
            else{
                //the user isn't moving a selected point, just panning the image
                omsi_globals.translatePos.x = evt.pageX - omsi_globals.startDragOffset.x;
                omsi_globals.translatePos.y = evt.pageY - omsi_globals.startDragOffset.y;
                draw();
            }
        }
    });
    // omsi_globals.canvas.addEventListener("dblclick", function(evt){
    //   		addCoord(evt);
    //   });

    document.addEventListener("keydown", function(evt){
        //use shift + arrow keys to move selected points
        if(omsi_globals.dragindex != null){ //don't interfere with normal browser behavior if no points are selected
            switch(evt.keyCode){
                case 37: //left arrow
                    evt.preventDefault();
                    omsi_globals.points[omsi_globals.dragindex].x--; //changes the original point, too, since it was passed into this array by ref
                    draw();
                    updateCoords();
                    break;
                case 38: //up arrow
                    evt.preventDefault();
                    omsi_globals.points[omsi_globals.dragindex].y--;
                    draw();
                    updateCoords();
                    break;
                case 39: //right arrow
                    evt.preventDefault();
                    omsi_globals.points[omsi_globals.dragindex].x++;
                    draw();
                    updateCoords();
                    break;
                case 40: //down arrow
                    evt.preventDefault();
                    omsi_globals.points[omsi_globals.dragindex].y++;
                    draw();
                    updateCoords();
                    break;
                default: break; //do nothing;
            }
            return false;
        }
        else return false;
    });

    // $(document).keyup(function(evt){
    //               if(evt.keyCode == 13)
    //                   $(".manualzoom").popover("hide");
    //           })


}

// function handleStart(evt) {
//   evt.preventDefault();
//   log("touchstart.");
//   var el = document.getElementsByTagName("canvas")[0];
//   var ctx = el.getContext("2d");
//   var touches = evt.changedTouches;
//         
//   for (var i=0; i < touches.length; i++) {
//     log("touchstart:"+i+"...");
//     ongoingTouches.push(copyTouch(touches[i]));
//     var color = colorForTouch(touches[i]);
//     ctx.beginPath();
//     ctx.arc(touches[i].pageX, touches[i].pageY, 4, 0,2*Math.PI, false);  // a circle at the start
//     ctx.fillStyle = color;
//     ctx.fill();
//     log("touchstart:"+i+".");
//   }
// }

function findWithAttr(array, attr, value) {
    for(var i = 0; i < array.length; i += 1) {
        if(array[i][attr] === value) {
            return i;
        }
    }
}