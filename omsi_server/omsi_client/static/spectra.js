//new spectrum graphing without SimpleGraph
// excellent svg help http://alignedleft.com/tutorials/d3/an-svg-primer/


// .axis {
//  shape-rendering: crispEdges;
// }
// .x.axis .minor {
//  stroke-opacity: .5;
// }
// .x.axis.line, .x.axis path, .y.axis line, .y.axis path {
//  fill: none;
//  stroke: #000;
// }



function draw_spectrum(pointnum){
	var data = omsi_globals.d3data[pointnum-1];
	var xmin = data[0].x;
	var xmax = data[data.length-1].x;
	ViewModel.manRangeMin(xmin);
       ViewModel.manRangeMax(xmax);
	document.getElementById("graph" + pointnum).innerHTML = ""; // wipe out the contents of the div
	"use strict";
    var x_extent = [xmin, xmax];
    var y_extent = d3.extent(data, function(d){ return d.y });
    var x_scale = d3.scale.linear()
   		.domain(x_extent)
    		.range([0, omsi_globals.chart_dimensions.width]);
     var y_scale = d3.scale.linear()
    		.domain(y_extent)
    		.range([omsi_globals.chart_dimensions.height, 0]);
    	omsi_globals.y_scale = y_scale;
    var svg_group = d3.select("#graph" + pointnum)
    		.append("svg")
			.attr("width", omsi_globals.container_dimensions.width)
            .attr("height", omsi_globals.container_dimensions.height)
            .append("g")
                .attr("transform", "translate(" + omsi_globals.margins.left + "," + omsi_globals.margins.top + ")");
    		
    	var x_axis = d3.svg.axis()
    		.scale(x_scale);
    	var y_axis = d3.svg.axis()
    		.scale(y_scale)
    		.orient("left");
    		
            // .axis path,
            //             .axis line {
            //                 fill: none;
            //                 stroke: #2C3539;
            //                 shape-rendering: crispEdges;
            //             }
            // 
            //             .axis text {
            //                 font-family: sans-serif;
            //                 font-size: 11px;
            //             }
            
            
            
    svg_group.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + omsi_globals.chart_dimensions.height + ")")
        .attr("fill","#2C3539")
        .attr("stroke","#2C3539")
    	.attr("stroke-width","1")
        // .attr("font-family","sans-serif")
        // .attr("font-size","100%")
    	.attr("shape-rendering","crispEdges")
        .call(x_axis);

    svg_group.append("g")
        .attr("class", "y axis")
        .attr("fill","#2C3539")
        .attr("stroke","#2C3539")
    	.attr("stroke-width","1")
        // .attr("font-family","sans-serif")
    	.attr("shape-rendering","crispEdges")
        .call(y_axis);
   			
   d3.select("#graph" + pointnum + " .x.axis")
   		.append("text")
   			.text(omsi_globals.zaxisSpectrum)
   			.attr("x", (omsi_globals.chart_dimensions.width/2))
   			.attr("y", omsi_globals.margins.bottom-4)
   			.attr("fill","#2C3539")
            .attr("stroke","#2C3539")
            .attr("shape-rendering","crispEdges")
        	.attr("font-family","sans-serif")
            // .attr("font-size","100%") 
        	.attr("stroke-width","1");
   			
   d3.select("#graph" + pointnum + " .y.axis")
   		.append("text")
   			.text("intensity (AU)")
   			.attr("fill","#2C3539")
            .attr("stroke","#2C3539")
        	.attr("stroke-width","1")
        	.attr("shape-rendering","crispEdges")
        	
   			.attr("transform", "rotate(-90, -60, 0) translate(" + -(omsi_globals.chart_dimensions.height) + ")");
   			
    var line = d3.svg.line()
        .x(function(d){return x_scale(d.x)})
        .y(function(d){return y_scale(d.y)})
    d3.select("#graph" + pointnum + " svg g")
    		.append("path")
            .attr("d", line(data))
            .attr("fill","none")
            .attr("stroke","steelblue")
        	.attr("stroke-width","1")
            .attr("class", "dist_line");

    svg_group.append("rect")
           .attr("class", "overlay")
           .attr("id", "rect"+pointnum)
           .attr("fill","none")
           // .attr("stroke-width","1")
           // .attr("stroke","#000")
           .attr("width", omsi_globals.chart_dimensions.width)
           .attr("height", omsi_globals.chart_dimensions.height)
           .call(dragit);

    d3.selectAll("text").attr("fill","#2C3539"); //fill all text in #2C3539
    



}
 
//functions to control d3 plot interactions

//drag listeners for zooming
var dragrect;
	
var dragit = d3.behavior.drag()
	.on("dragstart", function(){
		omsi_globals.startx = Math.round(d3.mouse(this)[0]);
		var pointnum = this.id.charAt(this.id.length-1);
		dragrect = d3.select("#graph" + pointnum + " svg g")
			.append("rect")
				.attr("x", omsi_globals.startx)
				.attr("y", 0)
				.attr("width", 1)
				.attr("height", omsi_globals.chart_dimensions.height)
				.attr("fill", "gray")
				.attr("opacity", ".1");
	})
	.on("drag", function(){
		var currx = d3.mouse(this)[0];
		if(omsi_globals.startx > currx){
			 dragrect.transition()
			 	.attr("x", currx)
			 	.attr("width", Math.abs(currx - omsi_globals.startx))
			 	.delay(0)
			 	.duration(10);
		}
		else dragrect.transition()
				.attr("width", Math.abs(currx - omsi_globals.startx))
				.delay(0)
				.duration(10);
	})
	.on("dragend", function(){
		dragrect.remove();
		var pointnum = this.id.charAt(this.id.length-1);
		var startx = omsi_globals.startx;
		var endx = Math.round(d3.mouse(this)[0]);
		//make sure the drag covered more than one pixel. If not, fade out the rect
		if(Math.abs(startx - endx)< 1){
			dragrect.transition().attr("width", 0); 
			return;
		}
		//people can drag both directions, so figure out which is lower and which is higher
		var lowerx = Math.min(startx, endx);
		var higherx = Math.max(startx, endx);
		//we'll scale as a proportion of the current x scale (not indices, which are more regular than the data)
		var currxmin = omsi_globals.d3data[pointnum-1][0].x;
		var currxmax = omsi_globals.d3data[pointnum-1][omsi_globals.d3data[pointnum-1].length-1].x;
		var chartwidth = omsi_globals.chart_dimensions.width;
		var newmin = ((lowerx/chartwidth) * (currxmax - currxmin)) + currxmin;
		var newmax = ((higherx/chartwidth) * (currxmax - currxmin)) + currxmin;

        // if(omsi_globals.zoomlinked != true) updateZoom(pointnum, newmin, newmax);
        // else{
        // updateZoom(1, newmin, newmax);
        // updateZoom(2, newmin, newmax);
        updateManualZoomText(pointnum,newmin,newmax);
        // }
	});
		
function updateManualZoomText(pointnum,newmin,newmax){
    // updateManualZoomText(pointnum,omsi_globals.d3xranges[pointnum-1][0],omsi_globals.d3xranges[pointnum-1][1]);
    ViewModel.manRangeMin(newmin);
    ViewModel.manRangeMax(newmax);
}

//zooming
function updateZoom(pointnum, newmin, newmax){
	//decide if it's time to switch to raw data or not
	var sourcedata = [];
	var newdata = [];
	var iranges = [];
	//switch to raw data if down to less than threshold width
	if(newmax - newmin < omsi_globals.threshold) sourcedata = omsi_globals.plotpoints[pointnum-1].raw; 
	else sourcedata = omsi_globals.plotpoints[pointnum-1].downsampled;
	for(i=0; i<sourcedata.length; i++){
		if(sourcedata[i].x <= newmax && sourcedata[i].x >= newmin){
			newdata.push(sourcedata[i]);
			iranges.push(i);
		}
	}
    // console.log(newdata.length)
    // console.log(newmin+" "+newmax)
	if(newdata.length > 0){
		//update the global variables to be read by d3
		omsi_globals.d3data[pointnum-1] = newdata;
		omsi_globals.d3xranges[pointnum-1] = [newdata[0].x, newdata[newdata.length-1].x];
		omsi_globals.d3iranges[pointnum-1] = [iranges[0], iranges[iranges.length-1]];


		//update the scales
		var new_x_scale = d3.scale.linear()
	   		.domain(omsi_globals.d3xranges[pointnum-1])
    		.range([0, omsi_globals.chart_dimensions.width]);
	    var new_x_axis = d3.svg.axis()
    		.scale(new_x_scale);
    	var new_y_extent = d3.extent(newdata,  function(d){ return d.y });
		var new_y_scale = d3.scale.linear()
    		.domain(new_y_extent)
    		.range([omsi_globals.chart_dimensions.height, 0]);
    	var new_y_axis = d3.svg.axis()
    		.scale(new_y_scale)
    		.orient("left");
	    		
    	//update the path
    	var new_line = d3.svg.line()
    		.x(function(d){return new_x_scale(d.x)})
    		.y(function(d){return new_y_scale(d.y)});
	    		
		d3.selectAll("#graph" + pointnum + " path")
			.remove()
	
		d3.select("#graph" + pointnum + " .x.axis")
			.call(new_x_axis)
	
		d3.select("#graph" + pointnum + " .y.axis")
			.call(new_y_axis)				    				
	
	    d3.select("#graph" + pointnum + " svg g")
    		.append("path")
    		.attr("fill","none")
            .attr("stroke","steelblue")
        	.attr("stroke-width","1")
			.attr("d", new_line(newdata))
	}
	else{
		zoom_error("", pointnum);
		return;
	} 
    // ViewModel["manRange" + pointnum + "Min"](omsi_globals.d3xranges[pointnum-1][0]);
    // ViewModel["manRange" + pointnum + "Max"](omsi_globals.d3xranges[pointnum-1][1]);
}

// SEPARATE OUT THE ZOOM FUNCTION FROM THE UPDATE OF THE BOX
// WHEN YOU CALL ZOOM WITH MOUSE, YOU NEED BOTH
// WHEN YOU CALL ZOOM WITH BOX, YOU ONLY NEED ZOOM

//unzooming
d3.selectAll("#unzoom1").on("click", function(){
    // if(omsi_globals.zoomlinked == true){
        unzoom(1);
        unzoom(2);
		updateManualZoomText(1,omsi_globals.d3xranges[0][0],omsi_globals.d3xranges[0][1]);
		
    // }
    // else{
        // var pointnum = this.id.charAt(this.id.length-1);
        // unzoom(pointnum);
    // } 
});

var unzoom = function(pointnum){
	//grab the full set of plot points and load it into the global array to be read by d3
	var fullpointset = omsi_globals.plotpoints[pointnum-1].downsampled;
	omsi_globals.d3data[pointnum-1] = fullpointset;
	omsi_globals.d3xranges[pointnum-1] = [fullpointset[0].x, fullpointset[fullpointset.length - 1].x];
	omsi_globals.d3iranges[pointnum-1] = [0, fullpointset.length-1];
	draw_spectrum(pointnum);
    // ViewModel["manRange" + pointnum + "Min"](omsi_globals.d3xranges[pointnum-1][0]);
    // ViewModel["manRange" + pointnum + "Max"](omsi_globals.d3xranges[pointnum-1][1]);
}

//panning
var pan = function(pointnum, dir){
	var proportion = .50 //proportion of current range to shift left or right
	var irange = omsi_globals.d3iranges[pointnum-1];
	var mzrange = omsi_globals.d3xranges[pointnum-1];
	var mzdiff = mzrange[1] - mzrange[0];
	if(mzdiff < omsi_globals.threshold){
		var sourcedata = omsi_globals.plotpoints[pointnum-1].raw
	}
	else var sourcedata = omsi_globals.plotpoints[pointnum-1].downsampled;
	var newmzrange;
	if(dir == "right"){
		newmzrange = [mzrange[0] + mzdiff * proportion, mzrange[1] + mzdiff * proportion];
	}
	else{ //dir == "left"
		newmzrange =  [mzrange[0] - mzdiff * proportion, mzrange[1] - mzdiff * proportion];
	}
	if(newmzrange[0] <= sourcedata[0].x && mzrange[0] == sourcedata[0].x) zoom_error("left", pointnum);
	if(newmzrange[1] >= sourcedata[sourcedata.length-1].x && mzrange[1] == sourcedata[sourcedata.length-1].x) zoom_error("right", pointnum);
	updateZoom(1, newmzrange[0], newmzrange[1]);
	updateZoom(2, newmzrange[0], newmzrange[1]);
	
	updateManualZoomText(1,omsi_globals.d3xranges[0][0],omsi_globals.d3xranges[0][1]);
	
};

var panUnzoom = function(pointnum){
	var proportion = .50 //proportion of current range to shift left or right
	var irange = omsi_globals.d3iranges[pointnum-1];
	var mzrange = omsi_globals.d3xranges[pointnum-1];
	var mzdiff = mzrange[1] - mzrange[0];
	if(mzdiff < omsi_globals.threshold){
		var sourcedata = omsi_globals.plotpoints[pointnum-1].raw
	}
	else var sourcedata = omsi_globals.plotpoints[pointnum-1].downsampled;
	var newmzrange;
		newmzrange = [mzrange[0] - mzdiff * proportion, mzrange[1] + mzdiff * proportion];
    // if(newmzrange[0] <= sourcedata[0].x && mzrange[0] == sourcedata[0].x) zoom_error("left", pointnum);
    // if(newmzrange[1] >= sourcedata[sourcedata.length-1].x && mzrange[1] == sourcedata[sourcedata.length-1].x) zoom_error("right", pointnum);
	updateZoom(1, newmzrange[0], newmzrange[1]);
	updateZoom(2, newmzrange[0], newmzrange[1]);
	
	updateManualZoomText(1,omsi_globals.d3xranges[0][0],omsi_globals.d3xranges[0][1]);
	
};

function zoom_error(dir, pointnum){
	if(dir == "left") var errortext = "You are already at the lower limit of the data";
	else if(dir == "right") var errortext = "You are already at the upper limit of the data";
	else var errortext = "You have selected zero points";
	var errortext = d3.select("#graph" + pointnum + " svg")
		.append("text")
		.attr("x", 150)
		.attr("y", 50)
		.style("opacity", 0)
		.style("fill", "#993333")
		.text(errortext)
		.transition()
		.duration(1000)
		.style("opacity", 1)
		.each("end", function(){
			d3.select(this)
				.transition()
				.delay(2000)
				.duration(1000)
				.style("opacity", 0)
				.remove()
		});
}

d3.selectAll("#partialUnzoom")
    .on("click", function(){
            // unzoom(1);
            // unzoom(2);
            // var mzrange1 = omsi_globals.d3xranges[0];
            // var mzrange2 = omsi_globals.d3xranges[1];
            panUnzoom(1);
            panUnzoom(2);
    		updateManualZoomText(1,omsi_globals.d3xranges[0][0],omsi_globals.d3xranges[0][1]);
    		
            // updateZoom(1, mzrange1[0], 600);
            // updateZoom(2, mzrange1[0], 600);
            
        // updateZoom(1, omsi_globals.d3xranges[0][0], omsi_globals.d3xranges[0][1]);
        // updateZoom(2, omsi_globals.d3xranges[1][0], omsi_globals.d3xranges[1][1]);
    });

d3.selectAll("#panright1")
 	.on("click", function(){
		var pointnum = this.id.charAt(this.id.length-1);
        // if(omsi_globals.zoomlinked == true){
 			//zoom the other spectrum to match this one
 			if (pointnum == 1) var otherpointnum = 2;
 			else var otherpointnum = 1;
 			updateZoom(otherpointnum, omsi_globals.d3xranges[0][0], omsi_globals.d3xranges[0][1])
  			pan(1, "right");
 			pan(2, "right");
    		updateManualZoomText(1,omsi_globals.d3xranges[0][0],omsi_globals.d3xranges[0][1]);
    		
        // }
        // else {
            // pan(pointnum, "right");
        // }
});

d3.selectAll("#panleft1")
 	.on("click", function(){
		var pointnum = this.id.charAt(this.id.length-1);
        // if(omsi_globals.zoomlinked == true){
 			//zoom the other spectrum to match this one
 			if (pointnum == 1) var otherpointnum = 2;
 			else var otherpointnum = 1;
 			updateZoom(otherpointnum, omsi_globals.d3xranges[0][0], omsi_globals.d3xranges[0][1])
	 		pan(1, "left");
	 		pan(2, "left");
    		updateManualZoomText(1,omsi_globals.d3xranges[0][0],omsi_globals.d3xranges[0][1]);
    		
        // }
        // else {
            // pan(pointnum, "left");
        // }
});

