registerKeyboardHandler = function(callback) {
    var callback = callback;
    d3.select(window).on("keydown", callback);  
};

// 
// function redraw_newscale(elemid2,xscale,yscale)
// {
    // this.chart = document.getElementById(elemid2);
    //  this.vis = d3.select(this.chart).append("svg")
    //  }

SimpleGraph = function(elemid, options) {
    var self = this;
    this.chart = document.getElementById(elemid);
    this.cx = $("#"+elemid).width();
	this.cy = $("#"+elemid).height();
	console.log(this.cx);
	console.log(this.cy);
    // this.cx = this.chart.clientWidth;
    // this.cy = this.chart.clientHeight;
    this.options = options || {};
    this.options.xmax = options.xmax || 30;
    this.options.xmin = options.xmin || 0;
    this.options.ymax = options.ymax || 10;
    this.options.ymin = options.ymin || 0;
    
    this.options.downsampled1 = options.downsampled1;
    this.options.raw1 = options.raw1;
    this.points1 = options.downsampled1;
    this.peaks1 = options.peaks1;
    
    this.options.downsampled2 = options.downsampled2;
    this.options.raw2 = options.raw2;
    this.points2 = options.downsampled2;
    this.peaks2 = options.peaks2;

    // setup the raw data as vectors to use in the downsampling
    this.raw_xdata = [];
    for (var i = 0; i<this.options.raw1.length;i++)
    {
        this.raw_xdata.push(this.options.raw1[i].x);                    
    }
    this.down_xdata1 = [];
       for (var i = 0; i<this.options.downsampled1.length;i++)
       {
           this.down_xdata1.push(this.options.downsampled1[i].x);                    
       }
       this.down_xdata2 = [];
          for (var i = 0; i<this.options.downsampled2.length;i++)
          {
              this.down_xdata2.push(this.options.downsampled2[i].x);                    
          }
    
    this.raw_ydata1 = [];
    for (var i = 0; i<this.options.raw1.length;i++)
    {
        this.raw_ydata1.push(this.options.raw1[i].y);                    
    }
    
    this.raw_ydata2 = [];
       for (var i = 0; i<this.options.raw2.length;i++)
       {
           this.raw_ydata2.push(this.options.raw2[i].y);                    
       }
    
 

    this.padding = {
        "top":    this.options.title  ? 25 : 25,
        "right":                 20,
        "bottom": this.options.xlabel ? 45 : 45,
        "left":   this.options.ylabel ? 70 : 45
    };

    this.size = {
        "width":  this.cx - this.padding.left - this.padding.right,
        "height": this.cy/2 - this.padding.bottom - this.padding.top
    };
    // alert(this.size.height + " " +this.cy);
    // x-scale
    this.x = d3.scale.linear()
    .domain([this.options.xmin, this.options.xmax])
    .range([0, this.size.width]);

    // drag x-axis logic
    this.downx = Math.NaN;

    // y-scale (inverted domain)
    this.y1 = d3.scale.linear()
    .domain([this.options.ymax, this.options.ymin])
    .nice()
    .range([0, this.size.height])
    .nice();
    
    // y-scale (inverted domain)
    this.y2 = d3.scale.linear()
    .domain([this.options.ymax, this.options.ymin])
    .nice()
    .range([0, this.size.height])
    .nice();
    

    // drag y-axis logic
    // this.downy = Math.NaN;

    // this.dragged = this.selected = null;

    this.line1 = d3.svg.line()
    .x(function(d, i) { return this.x(this.points1[i].x); })
    .y(function(d, i) { return this.y1(this.points1[i].y); });

    this.line2 = d3.svg.line()
    .x(function(d, i) { return this.x(this.points2[i].x); })
    .y(function(d, i) { return this.y2(this.points2[i].y); });

    // var xrange =  (this.options.xmax - this.options.xmin),
    // yrange2 = (this.options.ymax - this.options.ymin) / 2,
    // yrange4 = yrange2 / 2,
    // datacount = this.size.width/30;

    // this.points = d3.range(datacount).map(function(i) { 
        //   return { x: i * xrange / datacount, y: this.options.ymin + yrange4 + Math.random() * yrange2 }; 
        // }, self);

    this.vis = d3.select(this.chart).append("svg")
    .attr("width",  this.cx)
    .attr("height", this.size.height + this.padding.top + this.padding.bottom)
    .append("g")
    .attr("transform", "translate(" + this.padding.left + "," + this.padding.top+ ")");
    // .attr("transform", "translate(" + this.padding.left + "," + this.padding.top + ")");
    
    var plot2shift = this.padding.top;//this.padding.bottom+this.padding.top;
    this.vis2 = d3.select(this.chart).append("svg")
     .attr("width",  this.cx)
     .attr("height", this.size.height + this.padding.top + this.padding.bottom)
     .append("g")
     .attr("transform", "translate(" + this.padding.left + "," + plot2shift + ")");
     // .attr("transform", "translate(" + this.padding.left + "," + this.padding.top + ")");


    this.plot = this.vis.append("rect")
    .attr("width", this.size.width)
    .attr("height", this.size.height )
    .style("fill", "#EEEEEE")
    // .attr("transform", "translate(" + this.padding.left + "," + 100 + ")")
    // .attr("pointer-events", "all")
    // .on("mousedown.drag", self.plot_drag())
    // .on("touchstart.drag", self.plot_drag())
    // this.plot.call(d3.behavior.zoom().scaleExtent([1,10]).x(this.x).y(this.y1).on("zoom", this.redraw()));

    this.plot2 = this.vis2.append("rect")
    .attr("width", this.size.width)
    .attr("height", this.size.height )
    .style("fill", "#EEEEEE")
    // .attr("transform", "translate(" + 0 + "," + this.padding.top + ")")
    // .attr("pointer-events", "all")
    // .on("mousedown.drag", self.plot_drag())
    // .on("touchstart.drag", self.plot_drag())
    // .call(d3.behavior.zoom().scaleExtent([1,100]).on("zoom", redraw()))
	
    // this.plot2.call(d3.behavior.zoom().scaleExtent([1,10]).x(this.x).y(this.y2).on("zoom", this.redraw()));

    this.vis.append("svg")
    .attr("top", 0)
    .attr("left", 0)
    .attr("width", this.size.width)
    .attr("height", this.size.height)
    .attr("viewBox", "0 0 "+this.size.width+" "+this.size.height)
    .attr("class", "line")
    .append("path")
    .attr("class", "line")
    .attr("d", this.line1(this.points1));
    
    this.vis2.append("svg")
    .attr("top", 0)
    .attr("left", 0)
    .attr("width", this.size.width)
    .attr("height", this.size.height)
    .attr("viewBox", "0 0 "+this.size.width+" "+this.size.height)
    .attr("class", "line")
    .append("path")
    .attr("class", "line")
    .attr("d", this.line2(this.points2));

    // add Chart Title
    if (this.options.title) {
        this.vis.append("text")
        .attr("class", "axis")
        // .text(this.options.title + " 1")
        .text("Point #1 Spectrum")
        .attr("x", this.size.width/2)
        .attr("dy","-0.8em")
        .style("text-anchor","middle");
    }
    // 
    // Add the x-axis label
    if (this.options.xlabel) {
        this.vis.append("g").append("text")
        .attr("class", "axis")
        .text(this.options.xlabel)
        .attr("x", this.size.width/2)
        .attr("y", this.size.height)
        .attr("dy","2.4em")
        .style("text-anchor","middle");
    }
    // 
    var titleshift = this.size.height/2;
    // add y-axis label
    if (this.options.ylabel) {
        this.vis.append("g").append("text")
        .attr("class", "axis")
        .text(this.options.ylabel)
        .style("text-anchor","middle")
        .attr("transform","translate(" + -45 + " " + titleshift+") rotate(-90)");
    }

    // add labels to chart2
    // add Chart Title
    if (this.options.title) {
        this.vis2.append("text")
        .attr("class", "axis")
        // .text(this.options.title)
        .text("Point #2 Spectrum")
        .attr("x", this.size.width/2)
        .attr("dy","-0.8em")
        .style("text-anchor","middle");
    }
    // 
    // Add the x-axis label
    if (this.options.xlabel) {
        this.vis2.append("g").append("text")
        .attr("class", "axis")
        .text(this.options.xlabel)
        .attr("x", this.size.width/2)
        .attr("y", this.size.height)
        .attr("dy","2.4em")
        .style("text-anchor","middle");
    }
    // 
    var titleshift = this.size.height/2;
    // add y-axis label
    if (this.options.ylabel) {
        this.vis2.append("g").append("text")
        .attr("class", "axis")
        .text(this.options.ylabel)
        .style("text-anchor","middle")
        .attr("transform","translate(" + -45 + " " + titleshift+") rotate(-90)");
    }


    // d3.select(this.chart)
    //    .on("mousemove.drag", self.mousemove())
    //    .on("touchmove.drag", self.mousemove())
    //    .on("mouseup.drag",   self.mouseup())
    //    .on("touchend.drag",  self.mouseup());
    // 
    this.redraw()();
};

//
// SimpleGraph methods
//
// 
// SimpleGraph.prototype.plot_drag = function() {
//     var self = this;
//     return function() {
//         registerKeyboardHandler(self.keydown());
//         d3.select('body').style("cursor", "move");
//         if (d3.event.altKey) {
//             var p = d3.svg.mouse(self.vis.node());
//             var newpoint = {};
//             newpoint.x = self.x.invert(Math.max(0, Math.min(self.size.width,  p[0])));
//             newpoint.y = self.y.invert(Math.max(0, Math.min(self.size.height, p[1])));
//             self.points.push(newpoint);
//             self.points.sort(function(a, b) {
//                 if (a.x < b.x) { return -1 };
//                 if (a.x > b.x) { return  1 };
//                 return 0
//             });
//             self.selected = newpoint;
//             self.update();
//             d3.event.preventDefault();
//             d3.event.stopPropagation();
//         }    
//     }
// };

SimpleGraph.prototype.update = function() {
    var self = this;
    var lines1 = this.vis.select("path").attr("d", this.line1(this.points1));
    // var circle1 = this.vis.select("svg").selectAll("circle")
    // .data(this.peaks1, function(d) { return d; }); //peaks
    
    var lines2 = this.vis2.select("path").attr("d", this.line2(this.points2));
    // var circle2 = this.vis2.select("svg").selectAll("circle")
    // .data(this.peaks2, function(d) { return d; }); //peaks
    // 
    // circle1.enter().append("circle")
    // .attr("class", function(d) { return d === self.selected ? "selected" : null; })
    // .attr("cx",    function(d) { return self.x(d.x); })
    // .attr("cy",    function(d) { return self.y1(d.y); })
    // .attr("r", 5.0)
    // .style("cursor", "ns-resize");
    // // .on("mousedown.drag",  self.datapoint_drag())
    // // .on("touchstart.drag", self.datapoint_drag());
    // 
    // circle2.enter().append("circle")
    //  .attr("class", function(d) { return d === self.selected ? "selected" : null; })
    //  .attr("cx",    function(d) { return self.x(d.x); })
    //  .attr("cy",    function(d) { return self.y1(d.y); })
    //  .attr("r", 5.0)
    //  .style("cursor", "ns-resize");
    //  // .on("mousedown.drag",  self.datapoint_drag())
    //  // .on("touchstart.drag", self.datapoint_drag());
    // 
    // circle1
    // .attr("class", function(d) { return d === self.selected ? "selected" : null; })
    // .attr("cx",    function(d) { 
    //     return self.x(d.x); })
    //     .attr("cy",    function(d) { return self.y1(d.y); });
    //     
    // circle2
    // .attr("class", function(d) { return d === self.selected ? "selected" : null; })
    // .attr("cx",    function(d) { 
    //     return self.x(d.x); })
    //     .attr("cy",    function(d) { return self.y1(d.y); });
    // 
    //     circle1.exit().remove();
    //     circle2.exit().remove();
    // 
    //     if (d3.event && d3.event.keyCode) {
    //         d3.event.preventDefault();
    //         d3.event.stopPropagation();
    //     }
}
/////
// SimpleGraph.prototype.datapoint_drag = function() {
//     var self = this;
//     return function(d) {
//         registerKeyboardHandler(self.keydown());
//         document.onselectstart = function() { return false; };
//         self.selected = self.dragged = d;
//         self.update();
// 
//     }
// };
// 
// SimpleGraph.prototype.mousemove = function() {
//     var self = this;
//     return function() {
//         var p = d3.svg.mouse(self.vis[0][0]),
//         t = d3.event.changedTouches;
// 
//         if (self.dragged) {
//             self.dragged.y = self.y.invert(Math.max(0, Math.min(self.size.height, p[1])));
//             self.update();
//         };
//         if (!isNaN(self.downx)) {
//             d3.select('body').style("cursor", "ew-resize");
//             var rupx = self.x.invert(p[0]),
//             xaxis1 = self.x.domain()[0],
//             xaxis2 = self.x.domain()[1],
//             xextent = xaxis2 - xaxis1;
//             if (rupx != 0) {
//                 var changex, new_domain;
//                 changex = self.downx / rupx;
//                 new_domain = [xaxis1, xaxis1 + (xextent * changex)];
//                 self.x.domain(new_domain);
//                 self.redraw()();
//             }
//             d3.event.preventDefault();
//             d3.event.stopPropagation();
//         };
//         if (!isNaN(self.downy)) {
//             d3.select('body').style("cursor", "ns-resize");
//             var rupy = self.y.invert(p[1]),
//             yaxis1 = self.y.domain()[1],
//             yaxis2 = self.y.domain()[0],
//             yextent = yaxis2 - yaxis1;
//             if (rupy != 0) {
//                 var changey, new_domain;
//                 changey = self.downy / rupy;
//                 new_domain = [yaxis1 + (yextent * changey), yaxis1];
//                 self.y.domain(new_domain);
//                 self.redraw()();
//             }
//             d3.event.preventDefault();
//             d3.event.stopPropagation();
//         }
//     }
// };
// 
// SimpleGraph.prototype.mouseup = function() {
//     var self = this;
//     return function() {
//         document.onselectstart = function() { return true; };
//         d3.select('body').style("cursor", "auto");
//         d3.select('body').style("cursor", "auto");
//         if (!isNaN(self.downx)) {
//             self.redraw()();
//             self.downx = Math.NaN;
//             d3.event.preventDefault();
//             d3.event.stopPropagation();
//         };
//         if (!isNaN(self.downy)) {
//             self.redraw()();
//             self.downy = Math.NaN;
//             d3.event.preventDefault();
//             d3.event.stopPropagation();
//         }
//         if (self.dragged) { 
//             self.dragged = null 
//         }
//     }
// }
// 
// SimpleGraph.prototype.keydown = function() {
//     var self = this;
//     return function() {
//         if (!self.selected) return;
//         switch (d3.event.keyCode) {
//             case 8: // backspace
//             case 46: { // delete
//                 var i = self.points1.indexOf(self.selected);
//                 self.points1.splice(i, 1);
//                 self.selected = self.points1.length ? self.points1[i > 0 ? i - 1 : 0] : null;
//                 self.update();
//                 break;
//             }
//         }
//     }
// };

SimpleGraph.prototype.redraw = function() {
    var self = this;
    return function() {
        // $('.axisval').html(self.options.title + " " + self.x.domain()[0] + " " + self.x.domain()[1]);
        // $('.axisval').html(self.options.title + " " + self.x.domain()[0] + " " + self.x.domain()[1]);
        // alert($('.axisval').html());
        
        //block the axes to prevent over-zooming
        self.x.domain([Math.max(self.x.domain()[0], self.options.xmin), Math.min(self.x.domain()[1], self.options.xmax)]);
       
        


        
        
         /// set downsampled data or raw data dependent on level of zoom
        if ((self.x.domain()[1]-self.x.domain()[0])<300)
        {
            
            /// get max number within a certain range of the x-axis
            idx1 = getNearestNumber(self.raw_xdata,self.x.domain()[0]);
            idx2 = getNearestNumber(self.raw_xdata,self.x.domain()[1]);

            // self.points1 = [{x:self.options.raw1[idx1].x,y:self.options.raw1[idx1].y}];//self.options.raw1;
            // self.points2 = [{x:self.options.raw2[idx1].x,y:self.options.raw2[idx1].y}];//self.options.raw2;
             self.points1 = [];//[{x:self.options.raw1[idx1].x,y:self.options.raw1[idx1].y}];//self.options.raw1;
                self.points2 = [];//[{x:self.options.raw2[idx1].x,y:self.options.raw2[idx1].y}];//self.options.raw2;
            for (var i = idx1; i<idx2; i++)
            {
                self.points1.push({x:self.raw_xdata[i],y:self.raw_ydata1[i]});
                self.points2.push({x:self.raw_xdata[i],y:self.raw_ydata2[i]});
                            }
                            my1 = d3.max(self.points1, function(d) {
                                            return d.y;
                                    });
                            self.y1.domain([my1*1.05,0]);//Math.max(ydata)]);
                               my2 = d3.max(self.points2, function(d) {
                                                return d.y;
                                        });
                                self.y2.domain([my2*1.05,0]);//Math.max(ydata)]);
                            
        }
        else
        {
            idx1_1 = getNearestNumber(self.down_xdata1,self.x.domain()[0]);
            idx2_1 = getNearestNumber(self.down_xdata1,self.x.domain()[1]);
            idx1_2 = getNearestNumber(self.down_xdata2,self.x.domain()[0]);
            idx2_2 = getNearestNumber(self.down_xdata2,self.x.domain()[1]);
            self.points1 = self.options.downsampled1;
            self.points2 = self.options.downsampled2;
            var temp_ydata = [];
            for (var i = idx1_1; i<=idx2_1;i++)
            {
                temp_ydata.push(self.points1[i].y);
    
            }
            max_y = Math.max.apply(Math, temp_ydata);
            self.y1.domain([max_y*1.05,0]);//Math.max(ydata)]);
    
            var temp_ydata2 = [];
            for (var i = idx1_2; i<=idx2_2;i++)
            {
                try
                {
                    temp_ydata2.push(self.points2[i].y);
                }
                catch(err)
                {
                    temp_ydata2.push(0);
                }
            }
            max_y2 = Math.max.apply(Math, temp_ydata2);
            self.y2.domain([max_y2*1.05,0]);//Math.max(ydata)]);
        }

        
        


        var tx = function(d) { 
            return "translate(" + self.x(d) + ",0)"; 
        },
        ty1 = function(d) { 
            return "translate(0," + self.y1(d) + ")";          
        },
         ty2 = function(d) { 
                return "translate(0," + self.y2(d) + ")";          
            },
        stroke = function(d) { 
            return d ? "#ccc" : "#666"; 
        },




        fx = self.x.tickFormat(10),
        fy1 = self.y1.tickFormat(10);
        fy2 = self.y2.tickFormat(10);

        // Regenerate x-ticks…
        var gx = self.vis.selectAll("g.x")
        .data(self.x.ticks(10), String)
        .attr("transform", tx);

        gx.select("text")
        .text(fx);

        var gxe = gx.enter().insert("g", "a")
        .attr("class", "x")
        .attr("transform", tx);

        gxe.append("line")
        .attr("stroke", stroke)
        .attr("y1", 0)
        .attr("y2", self.size.height);

        gxe.append("text")
        .attr("class", "axis")
        .attr("y", self.size.height)
        .attr("dy", "1em")
        .attr("text-anchor", "middle")
        .text(fx)
        .style("cursor", "ew-resize");
        // .on("mouseover", function(d) { d3.select(this).style("font-weight", "bold");})
        // .on("mouseout",  function(d) { d3.select(this).style("font-weight", "normal");});
        // .on("mousedown.drag",  self.xaxis_drag())
        // .on("touchstart.drag", self.xaxis_drag());

        gx.exit().remove();
        
        // Regenerate x-ticks axis2…
        var gx2 = self.vis2.selectAll("g.x")
        .data(self.x.ticks(10), String)
        .attr("transform", tx);

        gx2.select("text")
        .text(fx);

        var gxe2 = gx2.enter().insert("g", "a")
        .attr("class", "x")
        .attr("transform", tx);

        gxe2.append("line")
        .attr("stroke", stroke)
        .attr("y1", 0)
        .attr("y2", self.size.height);

        gxe2.append("text")
        .attr("class", "axis")
        .attr("y", self.size.height)
        .attr("dy", "1em")
        .attr("text-anchor", "middle")
        .text(fx)
        .style("cursor", "ew-resize")
        // .on("mouseover", function(d) { d3.select(this).style("font-weight", "bold");})
        // .on("mouseout",  function(d) { d3.select(this).style("font-weight", "normal");});
        // .on("mousedown.drag",  self.xaxis_drag())
        // .on("touchstart.drag", self.xaxis_drag());

        gx2.exit().remove();

        // Regenerate y-ticks…
        var gy = self.vis.selectAll("g.y")
        .data(self.y1.ticks(10), String)
        .attr("transform", ty1);

        gy.select("text")
        .text(fy1);

        var gye = gy.enter().insert("g", "a")
        .attr("class", "y")
        .attr("transform", ty1)
        .attr("background-fill", "#FFEEB6");

        gye.append("line")
        .attr("stroke", stroke)
        .attr("x1", 0)
        .attr("x2", self.size.width);

        gye.append("text")
        .attr("class", "axis")
        .attr("x", -3)
        .attr("dy", ".35em")
        .attr("text-anchor", "end")
        .text(fy1)
        .style("cursor", "ns-resize");
        // .on("mouseover", function(d) { d3.select(this).style("font-weight", "bold");})
        // .on("mouseout",  function(d) { d3.select(this).style("font-weight", "normal");});
        // .on("mousedown.drag",  self.yaxis_drag())
        // .on("touchstart.drag", self.yaxis_drag());
        // .on("mouseup", function() {data smoothing and redraw})
        gy.exit().remove();
        
        
        // Regenerate y-ticks on 2nd axis…
        var gy2 = self.vis2.selectAll("g.y")
        .data(self.y2.ticks(10), String)
        .attr("transform", ty2);

        gy2.select("text")
        .text(fy2);

        var gye2 = gy2.enter().insert("g", "a")
        .attr("class", "y")
        .attr("transform", ty2)
        .attr("background-fill", "#FFEEB6");

        gye2.append("line")
        .attr("stroke", stroke)
        .attr("x1", 0)
        .attr("x2", self.size.width);

        gye2.append("text")
        .attr("class", "axis")
        .attr("x", -3)
        .attr("dy", ".35em")
        .attr("text-anchor", "end")
        .text(fy2)
        .style("cursor", "ns-resize");
        // .on("mouseover", function(d) { d3.select(this).style("font-weight", "bold");})
        // .on("mouseout",  function(d) { d3.select(this).style("font-weight", "normal");});
        // .on("mousedown.drag",  self.yaxis_drag())
        // .on("touchstart.drag", self.yaxis_drag());
        // .on("mouseup", function() {data smoothing and redraw})
        gy2.exit().remove();
        
        
        
        // self.plot.call(d3.behavior.zoom().x(self.x).y(self.y).on("zoom", self.redraw()));
        self.plot.call(d3.behavior.zoom().x(self.x).on("zoom", self.redraw()));
        self.plot2.call(d3.behavior.zoom().x(self.x).on("zoom", self.redraw()));
// scaleExtent([1,10]).
        self.update();   


    }
}
// 
// SimpleGraph.prototype.xaxis_drag = function() {
//     var self = this;
//     return function(d) {
//         document.onselectstart = function() { return false; };
//         var p = d3.svg.mouse(self.vis[0][0]);
//         self.downx = self.x.invert(p[0]);
//     }
// };
// 
// SimpleGraph.prototype.yaxis_drag = function(d) {
//     var self = this;
//     return function(d) {
//         document.onselectstart = function() { return false; };
//         var p = d3.svg.mouse(self.vis[0][0]);
//         self.downy = self.y.invert(p[1]);
// }
// };

function getNearestNumber(a, n){
    if((l = a.length) < 2)
    return l - 1;
    for(var l, p = Math.abs(a[--l] - n); l--;)
    if(p < (p = Math.abs(a[l] - n)))
    break;
    return l + 1;
}