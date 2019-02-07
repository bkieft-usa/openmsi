

var flareIdx=0;

var flareGlobal = {};

flareGlobal.maxWidth = 800;
flareGlobal.margin = {top: 15, right: 20, bottom: 30, left: 20},
    flareGlobal.width = flareGlobal.maxWidth - flareGlobal.margin.left - flareGlobal.margin.right,
    flareGlobal.barHeight = 20,
    flareGlobal.barWidth = flareGlobal.width * .8;

flareGlobal.numButtons = 7;

flareGlobal.duration = 400;
flareGlobal.root;

flareGlobal.tree = d3.layout.tree()
    .size([0, 100]);

flareGlobal.diagonal = d3.svg.diagonal()
    .projection(function(d) { return [d.y, d.x]; });

flareGlobal.svg = d3.select("#svgDivFlare").append("svg")
    .attr("width", flareGlobal.width + flareGlobal.margin.left + flareGlobal.margin.right)
    .attr("height", "10000px")
    .append("g")
    .attr("transform", "translate(" + flareGlobal.margin.left + "," + flareGlobal.margin.top + ")");

var flareGradient = flareGlobal.svg.append("svg:defs")
    .append("svg:linearGradient")
    .attr("id", "flareGradient")
    .attr("x1", "0%")
    .attr("y1", "0%")
    .attr("x2", "100%")
    .attr("y2", "100%")
    .attr("spreadMethod", "pad");

flareGradient.append("svg:stop")
    .attr("offset", "0%")
    .attr("stop-color", "#FFFFFF")
    .attr("stop-opacity", 1);

flareGradient.append("svg:stop")
    .attr("offset", "100%")
    .attr("stop-color", "#888")
    .attr("stop-opacity", 1);

var flareGradientMouseOver = flareGlobal.svg.append("svg:defs")
    .append("svg:linearGradient")
    .attr("id", "flareGradientMouseOver")
    .attr("x1", "0%")
    .attr("y1", "0%")
    .attr("x2", "100%")
    .attr("y2", "100%")
    .attr("spreadMethod", "pad");

flareGradientMouseOver.append("svg:stop")
    .attr("offset", "0%")
    .attr("stop-color", "#FFF")
    .attr("stop-opacity", 1);

flareGradientMouseOver.append("svg:stop")
    .attr("offset", "100%")
    .attr("stop-color", "#CCC")
    .attr("stop-opacity", 1);

//    $('#flareGraphModal').modal('show');


function isEncoded(str){
    return decodeURIComponent(str) !== str;
}

function getflare(key) {
    var childKey = 'children';
    var depthKey = '_children';
    var myURL = [api_root + 'qmetadata/?file='+encodeURIComponent(key) +'&mtype=file&'+childKey+'=children&depth=2'];
    if (isEncoded(key)){
         myURL = [api_root + 'qmetadata/?file='+ key +'&mtype=file&'+childKey+'=children&depth=2'];
    }


    $.ajax({
        dataType: 'json',
        url: myURL,
        success: function( flare ) {
            flare.x0 = 0;
            flare.y0 = 0;
//            var i = 0;
//            var j = 0;
//            for (i = 0; i < flare[childKey].length; i++)
//            {
////                console.log(JSON.stringify(flare[childKey][i][depthKey]))
//                var tempObj1 = flare[childKey][i][childKey];
////                console.log(tempObj1.length)
//                for (j = 0; j<flare[childKey][i][childKey].length; j++ )
//                {
//                    var keys = [];
//                    for (var k in flare[childKey][i][childKey][j][depthKey]) {
//                        keys.push(k);
//                    }
//                    console.log(keys);
//                }
//
//            }

            updateFlare( root = flare );
            $("#svgDivFlare svg").fadeTo('slow',1);
        },
        error: function(xhr, status, error) {
            // check status && error
            console.log('ERROR')
//       window.location.href = '/openmsi/client/login';
            console.log(xhr)
            console.log(status)
            console.log(error)
        }
    });


}


function updateFlare(source) {
            $('#loading').hide();

    // Compute the flattened node list. TODO use d3.layout.hierarchy.
    var nodes = flareGlobal.tree.nodes(root);

//    var height = Math.max(50000, nodes.length * flareGlobal.barHeight + flareGlobal.margin.top + flareGlobal.margin.bottom);
    var height = nodes.length * flareGlobal.barHeight + flareGlobal.margin.top + flareGlobal.margin.bottom;
//    console.log(height)
//    $('.modalFlare').css('height',height+200);
    $('#svgDivFlare').parent().css('height',height+200);
//     window.innerHeight = 1000;
//        $('.modalFlare').outerHeight("1000px");

//      $('.modal-body').css('height',height+200);

    d3.select("flareGlobal.svg")
        .attr("height", height);
//        .attr("outerHeight",'100%');
//    d3.select("flareGlobal.svg")
//            .attr("height", "1000px");

//    d3.select(self.frameElement)
//            .style("height", height+"px");

    // Compute the "layout".
    nodes.forEach(function(n, flareIdx) {
        n.x = flareIdx * flareGlobal.barHeight;
    });

    // Update the nodes…
    var node = flareGlobal.svg.selectAll("g.node")
        .data(nodes, function(d) { return d.id || (d.id = ++flareIdx); });



    var nodeEnter = node.enter().append("g")
        .attr("class", "node")
        .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
        .style("opacity", 1e-6);

    // Enter any new nodes at the parent's previous position.
    //label rectangle
    nodeEnter.append("rect")
        .attr("y", -flareGlobal.barHeight / 2)
        .attr("height", flareGlobal.barHeight)
        .attr("width", flareGlobal.barWidth)
        .attr("rx",5)
        .attr("ry",5)
        .style("fill-opacity",1)
        .style("fill", color)
        .on("click", flareClick);



    nodeEnter.append("text")
        .attr("dy", 3.5)
        .attr("dx", 5.5)
        .on("click", flareClick)
        .style("fill",textColor)
        .style("font-size","13px")
        .text(function(d) {
            var myStr = d.value ? d.name + " = " + d.value : d.name
            var maxStrLength = d.downURL ? 65 : d._children ? 90 : d.children ? 90 : 90;
            if (myStr.length > maxStrLength)
            {
                myStr = myStr.substring(0,maxStrLength)+"...";

            }
            return myStr
        });

    //Long text pop-out info
    nodeEnter.filter(function(d) {
        var myStr = d.value ? d.name + " = " + d.value : d.name
        return myStr.length>90;
         }).append("svg:a")
        .append("rect")
        .attr("y", -flareGlobal.barHeight / 2+2)
        .attr("x", flareGlobal.barWidth - 1*flareGlobal.barWidth/flareGlobal.numButtons)
        .attr("rx",5)
        .attr("ry",5)
        .attr("stroke","#25383c")
        .attr("stroke-width",0.5)
        .on("mouseover", function(d) {
            d3.select(this)
                // .style({'stroke-opacity':1,'stroke':'#F00'});
                .style("fill", "url(#flareGradientMouseOver)")
        })
        .on("mouseout", function(d) {
            d3.select(this)
                // .style({'stroke-opacity':0.4,'stroke':'#eee'});
                .style("fill", "url(#flareGradient)")
//                        .style({'fill':'url(#flareGlobal.gradient)'});
        })
        .on("click", function(d) {
            var myStr = d.value ? d.name + " = " + d.value : d.name
            $('#flareLongTextText').text(myStr.replace(/\n/g, "<br />"));
             $('#flareLongTextModal').modal('show');
        })
        .style("fill", "url(#flareGradient)")
        .attr("height", flareGlobal.barHeight-4)
        .attr("width", flareGlobal.barWidth/flareGlobal.numButtons-5);

    //Long-text button text
    nodeEnter.filter(function(d) { var myStr = d.value ? d.name + " = " + d.value : d.name
        return myStr.length>90;}).append("text")
        .attr("dy", 3.5)
        .attr("dx", flareGlobal.barWidth - 1*flareGlobal.barWidth/flareGlobal.numButtons+flareGlobal.barWidth/flareGlobal.numButtons/2-5)
        .attr("text-anchor", "middle")
        .style("font-weight","bold")
        .style("fill","#333")
        .text("Full Text");

    //Download rectangle
    nodeEnter.filter(function(d) { return d.downURL; }).append("svg:a")
        .attr("xlink:href", function(d){return d.downURL;})
        .append("rect")
        .attr("y", -flareGlobal.barHeight / 2+2)
        .attr("x", flareGlobal.barWidth - flareGlobal.barWidth/flareGlobal.numButtons)
        .attr("rx",5)
        .attr("ry",5)
        .attr("stroke","#25383c")
        .attr("stroke-width",0.5)
        .on("mouseover", function(d) {
            d3.select(this)
                // .style({'stroke-opacity':1,'stroke':'#F00'});
                .style("fill", "url(#flareGradientMouseOver)")
        })
        .on("mouseout", function(d) {
            d3.select(this)
                // .style({'stroke-opacity':0.4,'stroke':'#eee'});
                .style("fill", "url(#flareGradient)")
//                        .style({'fill':'url(#flareGlobal.gradient)'});
        })
        .style("fill", "url(#flareGradient)")
        .attr("height", flareGlobal.barHeight-4)
        .attr("width", flareGlobal.barWidth/flareGlobal.numButtons-5);

    //Download text
    nodeEnter.filter(function(d) { return d.downURL; }).append("text")
        .attr("dy", 3.5)
        .attr("dx", flareGlobal.barWidth - flareGlobal.barWidth/flareGlobal.numButtons+flareGlobal.barWidth/flareGlobal.numButtons/2-5)
        .attr("text-anchor", "middle")
        .style("font-weight","bold")
        .style("fill","#333")
        .attr("xlink:href", function(d){return d.downURL;})
        .text("Download");

    //Viewer rectangle
    nodeEnter.filter(function(d) { return d.viewURL; }).append("svg:a")
        .attr("xlink:href", function(d){return d.viewURL;})
        .append("rect")
        .attr("y", -flareGlobal.barHeight / 2+2)
        .attr("x", flareGlobal.barWidth - flareGlobal.barWidth/flareGlobal.numButtons)
        .attr("rx",5)
        .attr("ry",5)
        .attr("stroke","grey")
        .attr("stroke-width",0.5)
        .on("mouseover", function(d) {
            d3.select(this)
                // .style({'stroke-opacity':1,'stroke':'#F00'});
                .style("fill", "url(#flareGradientMouseOver)")
        })
        .on("mouseout", function(d) {
            d3.select(this)
                // .style({'stroke-opacity':0.4,'stroke':'#eee'});
                .style("fill",'url(#flareGradient)');
        })
        .style("fill", 'url(#flareGradient)')
        .attr("height", flareGlobal.barHeight-4)
        .attr("width", flareGlobal.barWidth/flareGlobal.numButtons-5);

    //Viewer Text
    nodeEnter.filter(function(d) { return d.viewURL; }).append("text")
        .attr("dy", 3.5)
        .attr("dx", flareGlobal.barWidth - flareGlobal.barWidth/flareGlobal.numButtons+flareGlobal.barWidth/flareGlobal.numButtons/2-5)
        .attr("text-anchor", "middle")
        .style("font-weight","bold")
        .style("fill","#333")
        .attr("xlink:href", function(d){return d.viewURL;})
        .text("View");

    //Permissions Rectangle
    nodeEnter.filter(function(d) { return d.manageURL; }).append("svg:a")
        .attr("xlink:href", function(d){return d.manageURL;}).append("rect")
        .attr("y", -flareGlobal.barHeight / 2+2)
        .attr("x", flareGlobal.barWidth - 2*flareGlobal.barWidth/flareGlobal.numButtons)
        .attr("rx",5)
        .attr("ry",5)
        .attr("stroke","grey")
        .attr("stroke-width",0.5)
        .on("mouseover", function(d,flareIdx) {
            d3.select(this)
                // .style({'stroke-opacity':1,'stroke':'#F00'});
                .style("fill", "url(#flareGradientMouseOver)")
        })
        .on("mouseout", function(d,flareIdx) {
            d3.select(this)
                // .style({'stroke-opacity':0.4,'stroke':'#eee'});
                .style("fill",'url(#flareGradient)');
        })
        .style("fill",'url(#flareGradient)')
        .attr("height", flareGlobal.barHeight-4)
        .attr("width", flareGlobal.barWidth/flareGlobal.numButtons-5);
    //Permissions Text
    nodeEnter.filter(function(d) { return d.manageURL; }).append("text")
        .attr("dy", 3.5)
        .attr("dx",flareGlobal.barWidth - 2*flareGlobal.barWidth/flareGlobal.numButtons+flareGlobal.barWidth/flareGlobal.numButtons/2-5)
        .attr("text-anchor", "middle")
        .style("font-weight","bold")
        .style("fill","#333")
        .attr("xlink:href", function(d){return d.manageURL;})
        .text("Manage");
    //
    // nodeEnter.filter(function(d) { return !d.children; }).append("text")
    //        .attr("dy", ".3em")
    //        .style("text-anchor", "middle")
    //        .text(function(d) { return d.name.substring(0, d.r / 3); });

    // Transition nodes to their new position.
    nodeEnter.transition()
        .duration(flareGlobal.duration)
        .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; })
        .style("opacity", 1);

    node.transition()
        .duration(flareGlobal.duration)
        .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; })
        .style("opacity", 1)
        .select("rect")
        .style("fill", color);

    // nodeEnter.append("input").attr("type","button")
    // http://jsfiddle.net/eQmYX/41/

    // Transition exiting nodes to the parent's new position.
    node.exit().transition()
        .duration(flareGlobal.duration)
        .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
        .style("opacity", 1e-6)
        .remove();

    // Update the links…
    var link = flareGlobal.svg.selectAll("path.link")
        .data(flareGlobal.tree.links(nodes), function(d) { return d.target.id; });

    // Enter any new links at the parent's previous position.
    link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", function(d) {
            var o = {x: source.x0, y: source.y0};
            return flareGlobal.diagonal({source: o, target: o});
        })
        .transition()
        .duration(flareGlobal.duration)
        .attr("d", flareGlobal.diagonal);

    // Transition links to their new position.
    link.transition()
        .duration(flareGlobal.duration)
        .attr("d", flareGlobal.diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition()
        .duration(flareGlobal.duration)
        .attr("d", function(d) {
            var o = {x: source.x, y: source.y};
            return flareGlobal.diagonal({source: o, target: o});
        })
        .remove();

    // Stash the old positions for transition.
    nodes.forEach(function(d) {
        d.x0 = d.x;
        d.y0 = d.y;
    });
}

// Toggle children on flareClick.
function flareClick(d) {
    if (d.children) {
        d._children = d.children;
        d.children = null;
        console.log('closing')
//        if (d.hasOwnProperty('downURL')) {
//        console.log('title')
//                        window.setTimeout(slowRecover, 300);
//    $('#flareGraphModal').modal('show');


//    }
    } else {
        d.children = d._children;
        d._children = null;
        console.log('opening')
//        if (d.hasOwnProperty('downURL')) {
//        console.log('title')
//                        $('#svgDiv').css('z-index','1000')
//            $('body').css('background-color', 'rgba(0, 0 , 0, 0.05)');
//            $('button').prop('disabled', true);
//            $('.switch').css('opacity', 0.5);
//                $('#flareGraphModal').modal('hide');
//    }
    }
    updateFlare(d);

    // $("div#activeTextText").html("<p>" + d.name + "</p>");

}

function slowRecover() {
    $('#svgDivFlare').css('z-index','10');
//            $('body').css('background-color', 'rgba(0, 0 , 0, 0)');
    $('button').prop('disabled', false);
    $('.switch').css('opacity', 1);
}

function color(d) {
    return d.downURL ? "#6e6e6e" : d._children ? "#999" : d.children ? "#999" : "#eee";
}

// Three text colors for the graphic
function textColor(d) {
    return d.downURL ? "#fff" : d._children ? "#fff" : d.children ? "#fff" : "#3a87ad";
}

function sortUnorderedList(ul, sortDescending) {
    if(typeof ul == "string")
        ul = document.getElementById(ul);

    // Idiot-proof, remove if you want
    if(!ul) {
        alert("The UL object is null!");
        return;
    }

    // Get the list items and setup an array for sorting
    var lis = ul.getElementsByTagName("LI");
    var vals = [];

    // Populate the array
    for(var i = 0, l = lis.length; i < l; i++)
        vals.push(lis[i].innerHTML);

    // Sort it
    vals.sort();

    // Sometimes you gotta DESC
    if(sortDescending)
        vals.reverse();

    // Change the list on the page
    for(var i = 0, l = lis.length; i < l; i++)
        lis[i].innerHTML = vals[i];
}
