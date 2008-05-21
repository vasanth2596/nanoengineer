# Copyright 2004-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
CS_draw_primitives.py - Public entry points for ColorSorter drawing primitives.

These functions all call ColorSorter.schedule_* methods, which record object
data for sorting, including the object color and an eventual call on the
appropriate drawing worker function.

@version: $Id$
@copyright: 2004-2008 Nanorex, Inc.  See LICENSE file for details. 

History:

Originated by Josh as drawer.py .

Various developers extended it since then.

Brad G. added ColorSorter features.

At some point Bruce partly cleaned up the use of display lists.

071030 bruce split some functions and globals into draw_grid_lines.py
and removed some obsolete functions.

080210 russ Split the single display-list into two second-level lists (with and
without color) and a set of per-color sublists so selection and hover-highlight
can over-ride Chunk base colors.  ColorSortedDisplayList is now a class in the
parent's displist attr to keep track of all that stuff.

080311 piotr Added a "drawpolycone_multicolor" function for drawing polycone
tubes with per-vertex colors (necessary for DNA display style)

080313 russ Added triangle-strip icosa-sphere constructor, "getSphereTriStrips".

080420 piotr Solved highlighting and selection problems for multi-colored
objects (e.g. rainbow colored DNA structures).

080519 russ pulled the globals into a drawing_globals module and broke drawer.py
into 10 smaller chunks: glprefs.py setup_draw.py shape_vertices.py
ColorSorter.py CS_workers.py CS_ShapeList.py CS_draw_primitives.py drawers.py
gl_lighting.py gl_buffers.py
"""

from OpenGL.GL import GL_BACK
from OpenGL.GL import GL_CULL_FACE
from OpenGL.GL import glDisable
from OpenGL.GL import glEnable
from OpenGL.GL import GL_FILL
from OpenGL.GL import GL_FRONT
from OpenGL.GL import GL_LIGHTING
from OpenGL.GL import GL_LINE
from OpenGL.GL import glPolygonMode

from geometry.VQT import norm, vlen, V, Q, A

import utilities.debug as debug # for debug.print_compact_traceback

from graphics.drawing.ColorSorter import ColorSorter
from graphics.drawing.drawers import drawPoint

try:
    from OpenGL.GLE import gleGetNumSides, gleSetNumSides
except:
    print "GLE module can't be imported. Now trying _GLE"
    from OpenGL._GLE import gleGetNumSides, gleSetNumSides

import foundation.env as env #bruce 051126

# Check if the gleGet/SetNumSides function is working on this install, and if
# not, alias it to an effective no-op. Checking method is as recommended in
# an OpenGL exception reported by Brian [070622]:
#   OpenGL.error.NullFunctionError: Attempt to call an
#   undefined function gleGetNumSides, check for
#   bool(gleGetNumSides) before calling
# The underlying cause of this (described by Brian) is that the computer's OpenGL
# has the older gleGetNumSlices (so it supports the functionality), but PyOpenGL
# binds (only) to the newer gleGetNumSides. Given the PyOpenGL we're using,
# there's no way to access gleGetNumSlices, but in the future we might patch it
# to let us do that when this happens. I [bruce 070629] think Brian said this is
# only an issue on Macs.
if not bool(gleGetNumSides):
    print "fyi: gleGetNumSides is not supported by the OpenGL pre-installed on this computer."
    gleGetNumSides = int
    gleSetNumSides = int

def drawsphere(color, pos, radius, detailLevel, opacity = 1.0):
    """
    Schedule a sphere for rendering whenever ColorSorter thinks is appropriate.
    """
    ColorSorter.schedule_sphere(color, 
                                pos, 
                                radius, 
                                detailLevel, 
                                opacity = opacity)

def drawwiresphere(color, pos, radius, detailLevel = 1):
    """
    Schedule a wireframe sphere for rendering whenever ColorSorter thinks is appropriate.
    """
    ColorSorter.schedule_wiresphere(color, pos, radius, detailLevel = detailLevel)

def drawcylinder(color, pos1, pos2, radius, capped = 0, opacity = 1.0):
    """Schedule a cylinder for rendering whenever ColorSorter thinks is
    appropriate."""
    if 1:
        #bruce 060304 optimization: don't draw zero-length or almost-zero-length cylinders.
        # (This happens a lot, apparently for both long-bond indicators and for open bonds.
        #  The callers hitting this should be fixed directly! That might provide a further
        #  optim by making a lot more single bonds draw as single cylinders.)
        # The reason the threshhold depends on capped is in case someone draws a very thin
        # cylinder as a way of drawing a disk. But they have to use some positive length
        # (or the direction would be undefined), so we still won't permit zero-length then.
        cyllen = vlen(pos1 - pos2)
        if cyllen < (capped and 0.000000000001 or 0.0001):
            # uncomment this to find the callers that ought to be optimized
##            if env.debug(): #e optim or remove this test; until then it's commented out
##                print "skipping drawcylinder since length is only %5g" % (cyllen,), \
##                      "  (color is (%0.2f, %0.2f, %0.2f))" % (color[0], color[1], color[2])
            return
    ColorSorter.schedule_cylinder(color, pos1, pos2, radius, 
                                  capped = capped, opacity = opacity)

def drawcylinder_wireframe(color, end1, end2, radius): #bruce 060608
    "draw a wireframe cylinder (not too pretty, definitely could look nicer, but it works)"
    # display polys as their edges (see drawer.py's drawwirecube or Jig.draw for related code)
    # (probably we should instead create a suitable lines display list,
    #  or even use a wire-frame-like texture so various lengths work well)
    glPolygonMode(GL_FRONT, GL_LINE)
    glPolygonMode(GL_BACK, GL_LINE)
    glDisable(GL_LIGHTING)
    glDisable(GL_CULL_FACE) # this makes motors look too busy, but without it, they look too weird (which seems worse)
    try:
        drawcylinder(color, end1, end2, radius) ##k not sure if this color will end up controlling the edge color; we hope it will
    except:
        debug.print_compact_traceback("bug, ignored: ")
    # the following assumes that we are never called as part of a jig's drawing method,
    # or it will mess up drawing of the rest of the jig if it's disabled
    glEnable(GL_CULL_FACE)
    glEnable(GL_LIGHTING)
    glPolygonMode(GL_FRONT, GL_FILL)
    glPolygonMode(GL_BACK, GL_FILL) # could probably use GL_FRONT_AND_BACK
    return

def drawDirectionArrow(color, 
                       tailPoint, 
                       arrowBasePoint, 
                       tailRadius,
                       scale,  
                       flipDirection = False,
                       opacity = 1.0,
                       numberOfSides = 20
                       ):
    """
    Draw a directional arrow staring at <tailPoint> with an endpoint decided
    by the vector between <arrowBasePoint> and <tailPoint> 
    and the glpane scale <scale>
    @param color : The arrow color
    @type  color: Array
    @param tailPoint: The point on the arrow tail where the arrow begins. 
    @type   tailPoint: V
    @param arrowBasePoint: A point on the arrow where the arrow head begins(??
    @type  arrowBasePoint: V
    @param tailRadius: The radius of the arrow tail (cylinder radius 
                       representing the arrow tail)
    @type  tailRaius: float
    @param opacity: The opacity decides the opacity (or transparent display)
                    of the rendered arrow. By default it is rendered as a solid 
                    arrow. It varies between 0.0 to 1.0 ... 1.0 represents the 
                    solid arrow renderring style
    @type opacity: float
    @param numberOfSides: The total number of sides for the arrow head 
                        (a glePolycone) The default value if 20 (20 sided 
                        polycone)
    @type  numberOfSides: int
    """

    vec = arrowBasePoint - tailPoint
    vec = scale*0.07*vec
    arrowBase =  tailRadius*3.0
    arrowHeight =  arrowBase*1.5
    axis = norm(vec)

    #as of 2008-03-03 scaledBasePoint is not used so commenting out. 
    #(will be removed after more testing)
    ##scaledBasePoint = tailPoint + vlen(vec)*axis
    drawcylinder(color, tailPoint, arrowBasePoint, tailRadius, capped = True, 
                 opacity = opacity)

    ##pos = scaledBasePoint
    pos = arrowBasePoint
    arrowRadius = arrowBase
    gleSetNumSides(numberOfSides)
    drawpolycone(color, [[pos[0] - 1 * axis[0], 
                          pos[1] - 1 * axis[1],
                          pos[2] - 1 * axis[2]],
                         [pos[0],# - axis[0], 
                          pos[1], #- axis[1], 
                          pos[2]], #- axis[2]],
                         [pos[0] + arrowHeight * axis[0], 
                          pos[1] + arrowHeight * axis[1],
                          pos[2] + arrowHeight * axis[2]],
                         [pos[0] + (arrowHeight + 1) * axis[0], 
                          pos[1] + (arrowHeight + 1) * axis[1],
                          pos[2] + (arrowHeight + 1) * axis[2]]], # Point array (the two end
                 # points not drawn)
                 [arrowRadius, arrowRadius, 0, 0], # Radius array
                 opacity = opacity
                 )
    #reset the gle number of sides to the gle default of '20'
    gleSetNumSides(20)

def drawpolycone(color, pos_array, rad_array, opacity = 1.0):
    """Schedule a polycone for rendering whenever ColorSorter thinks is
    appropriate."""
    ColorSorter.schedule_polycone(color, pos_array, rad_array, opacity = opacity)

def drawpolycone_multicolor(color, pos_array, color_array, rad_array, opacity = 1.0):
    """Schedule a polycone for rendering whenever ColorSorter thinks is
    appropriate. Accepts color_array for per-vertex coloring. """
    ColorSorter.schedule_polycone_multicolor(color, pos_array, color_array, rad_array, opacity = opacity)

def drawsurface(color, pos, radius, tm, nm):
    """
    Schedule a surface for rendering whenever ColorSorter thinks is
    appropriate.
    """
    ColorSorter.schedule_surface(color, pos, radius, tm, nm)

def drawsurface_wireframe(color, pos, radius, tm, nm): 
    glPolygonMode(GL_FRONT, GL_LINE)
    glPolygonMode(GL_BACK, GL_LINE)
    glDisable(GL_LIGHTING)
    glDisable(GL_CULL_FACE) 
    try:
        drawsurface(color, pos, radius, tm, nm) 
    except:
        debug.print_compact_traceback("bug, ignored: ")
    glEnable(GL_CULL_FACE)
    glEnable(GL_LIGHTING)
    glPolygonMode(GL_FRONT, GL_FILL)
    glPolygonMode(GL_BACK, GL_FILL) 
    return

def drawline(color, 
             endpt1, 
             endpt2, 
             dashEnabled = False, 
             stipleFactor = 1,
             width = 1, 
             isSmooth = False):
    """
    Draw a line from endpt1 to endpt2 in the given color.  Actually, schedule
    it for rendering whenever ColorSorter thinks is appropriate.

    @param endpt1: First endpoint.
    @type  endpt1: point

    @param endpt2: Second endpoint.
    @type  endpt2: point

    @param dashEnabled: If dashEnabled is True, it will be dashed.
    @type  dashEnabled: boolean

    @param stipleFactor: The stiple factor.
    @param stipleFactor: int

    @param width: The line width in pixels. The default is 1.
    @type  width: int or float

    @param isSmooth: Enables GL_LINE_SMOOTH. The default is False.
    @type  isSmooth: boolean

    @note: Whether the line is antialiased is determined by GL state variables
    which are not set in this function.

    @warning: Some callers pass dashEnabled as a positional argument rather 
    than a named argument.    
    """
    ColorSorter.schedule_line(color, endpt1, endpt2, dashEnabled,
                              stipleFactor, width, isSmooth)

def drawTag(color, basePoint, endPoint, pointSize = 20.0):
    """
    Draw a tag (or a 'flag') as a line ending with a circle (like a balloon 
    with a string). Note: The word 'Flag' is intentionally not used in the 
    method nameto avoid potential confusion with a boolean flag.

    @param color: color of the tag 
    @type color: A
    @param basePoint: The base point of the tag 
    @type basePoint: V
    @param endPoint: The end point of the tag 
    @type endPoint: V
    @param pointSize: The pointSize of the point to be drawin at the <endPoint>
    @type  pointSize: float

    @see: GraphicsMode._drawTags where it is called (an example)

    """
    drawline(color, basePoint, endPoint)
    drawPoint(color, endPoint, pointSize = 20.0)
