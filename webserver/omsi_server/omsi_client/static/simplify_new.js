/*
 Copyright (c) 2012, Vladimir Agafonkin
 Simplify.js is a high-performance polyline simplification library
 mourner.github.com/simplify-js
*/


	function getSquareDistance(p1, p2) { // square distance between 2 points

		var dx = p1.x - p2.x,
	//	    dz = p1.z - p2.z,
		    dy = p1.y - p2.y;

		return dx * dx +
	//	       dz * dz +
		       dy * dy;
	}

  // 
	function simplifyRadialDistance(points, sqTolerance) { // distance-based simplification

		var i,
		    len = points.length,
		    point,
		    prevPoint = points[0],
		    temp,
		    newPoints = [prevPoint];
            
		for (i = 1; i < len; i++) {
			point = points[i];
            temp = getSquareDistance(point, prevPoint);
			if (temp > sqTolerance || isNaN(temp)) {
				newPoints.push(point);
				prevPoint = point;
			}
		}

		if (prevPoint !== point) {
			newPoints.push(point);
		}
		return newPoints;
	}


	
	function simplify(points, tolerance) {


            var newPoints = simplifyRadialDistance(points, tolerance);
	
		return newPoints;
	};
