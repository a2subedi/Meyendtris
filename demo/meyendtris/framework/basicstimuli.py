from abc import ABC, abstractmethod
import meyendtris
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.ShowBase import ShowBase
from direct.showbase.Audio3DManager import Audio3DManager
import panda3d.core as pandac
import meyendtris.framework.eventmarkers.eventmarkers
from meyendtris.framework.latentmodule import LatentModule
import math, warnings, os
    
class BasicStimuli(LatentModule, ABC):
    """
    Derive from this class to implement your own module with stimuli, by overriding 
    the run() function. The only parts in your code that should consume significant amounts 
    of time are the calls to explicit time-consumption functions (see below), such as sleep().

    This class provides convenience functions for displaying psychological-type stimuli.
    This includes text, rectangles, crosshairs, images, sounds, and video.
    These functions are automatically available to any LatentModule. 
    """

    class destroy_helper:
        """Small helper class to destroy multiple objects using a destroy() call."""
        def __init__(self,objs):
            self.objs = objs
        def destroy(self):
            for o in self.objs:
                o.destroy()

    def __init__(self):
        self._base = meyendtris.__BASE__
        super().__init__(make_up_for_lost_time = False)
        self.audio3d = None
        self.implicit_markers = False
        self._to_destroy = []

    def marker(self,markercode):
        """
        Emit a marker. The markercode can be a string or a number. 
        Side note: strings will not work if a legacy marker sending protocol is enabled (such as DataRiver or the parallel port).
        """
        meyendtris.framework.eventmarkers.eventmarkers.send_marker(markercode)
       
    def write(self, 
              text,                     # the text to display
              duration=1.0,             # duration for which the text will be displayed
                                        # if this is a string, the stimulus will be displayed until the corresponding event is generated
                                        # if this is a list of [number,string], the stimulus will at least be displayed for <number> seconds, but needs to confirmed with the respective event
                                        # if this is 0, the write will be non-blocking and you have to .destroy() the return value of this function manually  
              block=True,               # whether to wait for the duration until the function returns
              # optional parameters:
              pos=(0,0),                # x/y position of the text on the screen
              roll=0,                   # roll angle of the text
              scale=0.07,               # size of the text; either a single float (e.g. 0.07) or a 2-tuple of floats for non-uniform scaling
              fg=None,                  # the (r,g,b,a) color of the text; usually each is a floats between 0 and 1
              bg=None,                  # the (r,g,b,a) color of the text background; if a is zero, no background will be created
              shadow=None,              # the (r,g,b,a) color of the text's shadow
              shadow_offset=(0.04,0.04), # offset of the drop shadow from the text
              frame=None,               # the (r,g,b,a) color of the text's frame, drawn around the background (if desired)
              align='center',           # either 'left', 'center', or 'right'
              wordwrap=None,            # optionally the width to wordwrap the text at
              draw_order=None,           # optional drawing order
              font=meyendtris.path_join('media/arial.ttf'), # optionally the font of the text (see loader.loadFont)
              parent=None,              # parent rendering context or Panda3d NodePath
              sort=0                    # sorting order of the text
              ):
        """Write a piece of text on the screen and keep it there for a particular duration."""
        
        if align == 'left':
            align = pandac.TextNode.ALeft
        elif align == 'right':
            align = pandac.TextNode.ARight
        else:
            align = pandac.TextNode.ACenter
        if duration == 0:
            block = False
        

        font = self._base.loader.loadFont(font)
        obj = OnscreenText(text=text,pos=(pos[0],pos[1]-scale/4),roll=roll,scale=scale,fg=fg,bg=bg,shadow=shadow,shadowOffset=shadow_offset,frame=frame,align=align,wordwrap=wordwrap,drawOrder=draw_order,font=font,parent=parent,sort=sort)
        self._to_destroy.append(obj)
        if self.implicit_markers:
            self.marker(254)
        if block:
            if type(duration) == list or type(duration) == tuple:
                self.sleep(duration[0])
                self.waitfor(duration[1])
            elif type(duration) == str:
                self.waitfor(duration)
            else:
                self.sleep(duration)
                
            self._destroy_object(obj,255)
        else:
            if duration > 0:
                self._base.taskMgr.doMethodLater(duration, self._destroy_object, 'ConvenienceFunctions, remove_text', extraArgs=[obj, 255])
            return obj

    def crosshair(self,
                  duration=1.0,     # duration for which this object will be displayed
                                    # if this is a string, the stimulus will be displayed until the corresponding event is generated
                                    # if this is a list of [number,string], the stimulus will at least be displayed for <number> seconds, but needs to confirmed with the respective event
                                    # if this is 0, the write will be non-blocking and you have to .destroy() the return value of this function manually  
                  block=True,       # whether this function should only return once the duration is over
                  # additional parameters
                  pos=(0,0),        # position of the crosshair
                  size=0.25,        # size of the crosshair
                  width=0.01,       # thickness of the rectangles
                  color=(0,0,0,1),  # color of the crosshair
                  parent=None       # the renderer to use for displaying the object
                  ):        
        """Draw a crosshair."""
        img = meyendtris.path_join('media/blank.tga')
        obj1 = OnscreenImage(image=img,pos=(pos[0],0,pos[1]),scale=(size,1,width),color=color,parent=parent)
        self._to_destroy.append(obj1)
        obj1.setTransparency(pandac.TransparencyAttrib.MAlpha)
        obj2 = OnscreenImage(image=img,pos=(pos[0],0,pos[1]),scale=(width,1,size),color=color,parent=parent)
        self._to_destroy.append(obj2)
        obj2.setTransparency(pandac.TransparencyAttrib.MAlpha)
        if self.implicit_markers:
            self.marker(252)
        if block:
            if type(duration) == list or type(duration) == tuple:
                self.sleep(duration[0])
                self.waitfor(duration[1])
            elif type(duration) == str:
                self.waitfor(duration)
            else:
                self.sleep(duration)
            self._destroy_object([obj1,obj2],253)
        else:
            if duration > 0:
                self._base.taskMgr.doMethodLater(duration, self._destroy_object, 'ConvenienceFunctions, remove_crosshair',extraArgs=[[obj1,obj2],253])
            return self.destroy_helper([obj1,obj2])
  
    def rectangle(self,
                  rect=(0,0,0,0),        # the bounds of the rectangle (left,right,top,bottom)
                  duration=1.0,     # duration for which this object will be displayed
                                    # if this is a string, the stimulus will be displayed until the corresponding event is generated
                                    # if this is a list of [number,string], the stimulus will at least be displayed for <number> seconds, but needs to confirmed with the respective event
                                    # if this is 0, the write will be non-blocking and you have to .destroy() the return value of this function manually  
                  block=True,       # whether this function should only return once the duration is over
                  # additional parameters
                  color=(1,1,1,1),  # the (r,g,b,a) color of the rectangle
                  parent=None,      # the renderer to use for displaying the object
                  depth=0,          # screen depth of the rectangle
                  ):
        """Draw a single-colored rectangle."""
        
        if duration == 0:
            block = False
        
        l=rect[0];r=rect[1];t=rect[2];b=rect[3]
        obj = OnscreenImage(image= meyendtris.path_join('media/blank.tga'),pos=((l+r)/2,depth,(b+t)/2),scale=((r-l)/2,1,(b-t)/2),color=color,parent=parent)
        self._to_destroy.append(obj)
        obj.setTransparency(pandac.TransparencyAttrib.MAlpha)
        if self.implicit_markers:
            self.marker(250)
        if block:
            if type(duration) == list or type(duration) == tuple:
                self.sleep(duration[0])
                self.waitfor(duration[1])
            elif type(duration) == str:
                self.waitfor(duration)
            else:
                self.sleep(duration)
            self._destroy_object(obj,251)
        else:
            if duration > 0:                            
                self._base.taskMgr.doMethodLater(duration, self._destroy_object, 'ConvenienceFunctions, remove_rect',extraArgs=[obj,251])
            return obj

    def frame(self,
              rect=(0,0,0,0),            # the inner bounds of the frame (left,right,top,bottom)
              thickness=(0.01,0.01),# thickness of the frame (left/right, top/bottom)
              duration=1.0,         # duration for which this object will be displayed
                                    # if this is a string, the stimulus will be displayed until the corresponding event is generated
                                    # if this is a list of [number,string], the stimulus will at least be displayed for <number> seconds, but needs to confirmed with the respective event
                                    # if this is 0, the write will be non-blocking and you have to .destroy() the return value of this function manually  
              block=True,           # whether this function should only return once the duration is over
              # additional parameters
              color=(1,1,1,1),      # the (r,g,b,a) color of the rectangle
              parent=None,          # the renderer to use for displaying the object
              ):
        """Display a frame on the screen and keep it there for a particular duration."""
                
        l=rect[0];r=rect[1];t=rect[2];b=rect[3]
        w=thickness[0];h=thickness[1]
        img = meyendtris.path_join('media/blank.tga')
        L = OnscreenImage(image=img,pos=(l-w/2,0,(b+t)/2),scale=(w/2,1,w+(b-t)/2),color=color,parent=parent)
        L.setTransparency(pandac.TransparencyAttrib.MAlpha)
        self._to_destroy.append(L)
        R = OnscreenImage(image=img,pos=(r+w/2,0,(b+t)/2),scale=(w/2,1,w+(b-t)/2),color=color,parent=parent)
        R.setTransparency(pandac.TransparencyAttrib.MAlpha)
        self._to_destroy.append(R)
        T = OnscreenImage(image=img,pos=((l+r)/2,0,t-h/2),scale=(h+(r-l)/2,1,h/2),color=color,parent=parent)
        T.setTransparency(pandac.TransparencyAttrib.MAlpha)
        self._to_destroy.append(T)
        B = OnscreenImage(image=img,pos=((l+r)/2,0,b+h/2),scale=(h+(r-l)/2,1,h/2),color=color,parent=parent)
        B.setTransparency(pandac.TransparencyAttrib.MAlpha)
        self._to_destroy.append(B)
        if self.implicit_markers:
            self.marker(242)
        if block:
            if type(duration) == list or type(duration) == tuple:
                self.sleep(duration[0])
                self.waitfor(duration[1])
            elif type(duration) == str:
                self.waitfor(duration)
            else:
                self.sleep(duration)
            self._destroy_object([L,R,T,B],243)
        else:
            if duration > 0:
                self._base.taskMgr.doMethodLater(duration,self._destroy_object, 'ConvenienceFunctions, remove_frame',extraArgs=[[L,R,T,B],243])    
            return self.destroy_helper([L,R,T,B])        

    def picture(self, 
              image,                    # the image to display (may be a file name, preferably a relative path)
              duration=1.0,             # duration for which this object will be displayed
                                        # if this is a string, the stimulus will be displayed until the corresponding event is generated
                                        # if this is a list of [number,string], the stimulus will at least be displayed for <number> seconds, but needs to confirmed with the respective event
                                        # if this is 0, the write will be non-blocking and you have to .destroy() the return value of this function manually  
              block=True,               # whether to wait for the duration until the function returns
              # optional parameters:
              pos=None,                 # the (x,z) or (x,y,z) position of the image on the screen; this may be a 3-tuple of floats; y should be zero
              hpr=None,                 # the (heading,pitch,roll) angles of the image; if this is a single number, it will be taken as the roll angle
              scale=None,               # the size of the image; this may be a single flot, a 3-tuple of floats, or a vector; y should be 1, if a 3-tuple is given
              color=None,               # the (r,g,b,a) coloring of the image
              parent=None,              # parent rendering context or Panda3d NodePath
              ):
        """Display a picture on the screen and keep it there for a particular duration."""        
        
        if pos is not None and type(pos) not in (int,float) and len(pos) == 2:
            pos = (pos[0],0,pos[1])
        if scale is not None and type(scale) not in (int,float) and len(scale) == 2:
            scale = (scale[0],1,scale[1])
        if hpr is not None and type(scale) not in (int,float) and len(hpr) == 1:
            hpr = (0,0,hpr)
        if duration == 0:
            block = False
            
        obj = OnscreenImage(image=image,pos=pos,hpr=hpr,scale=scale,color=color,parent=parent)
        self._to_destroy.append(obj)
        obj.setTransparency(pandac.TransparencyAttrib.MAlpha)
        if self.implicit_markers:
            self.marker(248)
        if block:
            if type(duration) == list or type(duration) == tuple:
                self.sleep(duration[0])
                self.waitfor(duration[1])
            elif type(duration) == str:
                self.waitfor(duration)
            else:
                self.sleep(duration)
            self._destroy_object(obj,249)
        else:
            if duration > 0:
                self._base.taskMgr.doMethodLater(duration, self._destroy_object, 'ConvenienceFunctions, remove_picture', extraArgs=[obj,249])
            return obj

    def sound(self,
              filename,         # the sound file name to play (preferably a relative path)
              block=False,      # optionally wait until the sound has finished playing before returning from this function
              # optional parameters
              volume=0.1,       # the volume of the sound (between 0 and 1)
              direction=0.0,    # the balance; may be a number between -1 (hard left) and 1 (hard right), or an angle if surround=True
              playrate=1.0,     # the playrate of the sound (changes pitch and time)
              timeoffset=0.0,   # time offset into the file
              looping=False,    # whether the sound should be looping; can be turned off by calling .stop() on the return value of this function
              loopcount=None,   # optionally the number of repeats if looping
              surround=False,   # if True, the direction will go from -Pi/2 to Pi/2
              ):
        """Play a sound in a particular location."""
        if surround:            
            if self.audio3d is None:
                self.audio3d = Audio3DManager(self._base.sfxManagerList[0], None)
            obj = self.audio3d.loadSfx(filename)
            self._to_destroy.append(obj)
            self.audio3d.setSoundVelocityAuto(obj)
        else:
            obj = self._base.loader.loadSfx(filename)
            self._to_destroy.append(obj)
            obj.setVolume(volume)
            obj.setBalance(direction)
        length = obj.length()
        if loopcount is not None:
            obj.setLoopCount(loopcount)
            length *= loopcount
        if looping:
            obj.setLoop(True)
            length = 100000
        if timeoffset > 0.0:
            obj.setTime(timeoffset)
            length -= timeoffset
        obj.setPlayRate(playrate)
        length *= playrate
        obj.play()
        if self.implicit_markers:
            self.marker(246)
        if block:
            self.sleep(length)
            self._destroy_object(obj,247)            
        else:
            self._base.taskMgr.doMethodLater(length, self._destroy_object, 'ConvenienceFunctions, end_sound', extraArgs=[None,247])
            return obj

    def movie(self,
              filename,                 # the video file to play (preferably a relative path)
              block=False,              # optionally wait until the movie has finished playing before returning from this function 
              # optional parameters:
              pos=None,                 # the (x,z) or (x,y,z) position of the video on the screen; this may be a 3-tuple of floats; y should be zero
              hpr=None,                 # the (heading,pitch,roll) angles of the video; if this is a single number, it will be taken as the roll angle
              scale=None,               # scaling of the video area; this may be a single float, an (x,z) value, or an (x,y,z) value; note that one of 
                                        # the scale axes is shrunken according to the value of the "aspect" property (which is auto-deduced unless manually overridden)
              color=None,               # the (r,g,b,a) coloring of the video
              parent=None,              # parent rendering context or Panda3d NodePath
              volume=0.1,               # the volume of the sound (between 0 and 1)
              direction=0.0,            # the balance; may be a number between -1 (hard left) and 1 (hard right)
              timeoffset=0.0,           # time offset into the file
              playrate=1.0,             # the playback rate of the movie (changes pitch & duration)
              looping=False,            # whether the video should be looping; can be turned off by calling .stop() on the return value of this function 
              loopcount=None,           # optionally the number of repeats if looping
              aspect=None,              # aspect ratio of the video (auto-deduced if None); example: for 16:9 this would be 16.0/9.0 
                                        # the smaller axis of the video area is automatically shrunken based on this number
              pixelscale=False,         # if this is True, aspect will be ignored and the image will be scaled according to the pixels in the image
                                        # for this you need to pass as parent a randerer that uses a pixel coordinate system (such as pixel2d)
              contentoffset=(0,0),      # [u,v] offset of the movie content within the viewport/texture
              contentscale=None,        # [u,v] scale of the movie content within the viewport/texture -- if None this is automatically deduced based on the
                                        # texture size and the size of the video content within the texture (note that it can be tricky to get this right due  
                                        # to possible padding introduced when the movie is loaded)
              bordercolor=(0,0,0,0),    # the border color of the movie texture (only visible when the contentoffset and contentscale are used
              ):
        """Play a movie. Note: Sound for movies only works with OpenAL (rather than FMOD) -- see documentation at http://www.panda3d.org/manual/index.php/Sound on how to select it."""

        # load the sound track if there is one
        try:
            snd = self._base.loader.loadSfx(filename)
            if snd.length() == 0.0:
                snd = None
        except:
            snd = None
        # ... and set basic sound properties
        if snd is not None:
            self._to_destroy.append(snd)
            snd.setVolume(volume)
            snd.setBalance(direction)

        # create the video texture and set basic properties
        tex = self._base.loader.loadTexture(filename)
        self._to_destroy.append(tex)
        tex.setBorderColor((bordercolor[0],bordercolor[1],bordercolor[2],bordercolor[3]))
        tex.setWrapU(pandac.Texture.WMBorderColor)
        tex.setWrapV(pandac.Texture.WMBorderColor)
        if snd is not None:
            tex.synchronizeTo(snd)

        # apply custom playback options and deduce the actual length
        if snd is not None:
            length = snd.length()
            playable = snd
        else:
            length = tex.getTime()
            playable = tex
        if playrate != 1.0:
            playable.setPlayRate(playrate)
            length /= playrate
        if loopcount is not None:
            playable.setLoopCount(loopcount)
            length = length*loopcount
        playable.setLoop(looping)
        if looping:
            length = 10000000
        if timeoffset > 0.0:
            playable.setTime(timeoffset)
            length -= timeoffset

        # deduce the aspect ratio
        if aspect is None:
           aspect = tex.getVideoWidth() / float(tex.getVideoHeight())
        # deduce the content scale based on the padding in the video        
        if contentscale is None:
            contentscale = (float(tex.getVideoWidth()) / tex.getXSize(), float(tex.getVideoHeight()) / tex.getYSize())
        # deduce the scale of the image
        if scale is None:
            scale = 1.0
        if type(scale) in (int,float):
            scale = [scale,scale]
        if len(scale) == 2:
            scale = (scale[0],1,scale[1])
        if pixelscale or parent == pixel2d:
            scale[0] *= tex.getVideoWidth()
            scale[2] *= tex.getVideoHeight()
        else:
            if aspect >= 1.0:
                scale[2] /= float(aspect)
            else:
                scale[0] *= float(aspect)
            
        # deduce position and rotation
        if pos is not None and type(pos) not in (int,float) and len(pos) == 2:
            pos = (pos[0],0,pos[1])
        if hpr is not None and type(scale) not in (int,float) and len(hpr) == 1:
            hpr = (0,0,hpr)
        
        # create the image and set up content parameters
        img = OnscreenImage(image=tex,pos=pos,hpr=hpr,scale=scale,color=color,parent=parent)
        self._to_destroy.append(img)
        img.setTransparency(pandac.TransparencyAttrib.MAlpha)
        img.setTexScale(pandac.TextureStage.getDefault(),contentscale[0],contentscale[1])
        img.setTexOffset(pandac.TextureStage.getDefault(),contentoffset[0],contentoffset[1])

        # start playback and assure its destruction
        playable.play()
        if self.implicit_markers:
            self.marker(244)            
        if block:
            self.sleep(length)
            self._destroy_object(img, 245)
        else:
            self._base.taskMgr.doMethodLater(length, self._destroy_object, 'ConvenienceFunctions, remove_movie', extraArgs=[[img,tex,snd],245])
            return playable

    def precache_sound(self,filename):
        """Pre-cache a sound file."""
        if filename is None:
            return
        return self._base.loader.loadSfx(filename)
    
    def precache_picture(self,filename):
        """Pre-cache a picture file."""
        if filename is None:
            return
        return self._base.loader.loadTexture(filename)

    def precache_model(self,filename):
        """Pre-cache a model file."""
        if filename is None:
            return
        return self._base.loader.loadModel(filename)
    
    def precache_movie(self,filename):
        """Pre-cache a movie file."""
        if filename is None:
            return
        try:
            self._base.loader.loadTexture(filename)
        except:
            pass
        try:
            return self._base.loader.loadSfx(filename)
        except:
            pass
    
    def uncache_sound(self,filename):
        """Un-cache a previously cached sound file."""
        if filename is None:
            return
        # get the handle
        h = self._base.loader.loadSfx(filename)
        # remove it
        self._base.loader.unloadSfx(h)

    def uncache_picture(self,filename):
        """Un-cache a previously cached picture file."""
        if filename is None:
            return
        # get the handle
        h = self._base.loader.loadTexture(filename)
        # remove it
        self._base.loader.unloadTexture(h)

    def uncache_movie(self,filename):
        """Un-cache a previously cached movie file."""
        if filename is None:
            return
        try:
            h = self._base.loader.loadTexture(filename)
            self._base.loader.unloadTexture(h)
        except:
            pass
        try:
            h = self._base.loader.loadSfx(filename)
            self._base.loader.unloadSfx(h)
        except:
            pass


    # =========================
    # === Advanced Features ===
    # =========================

    def log_setup_parameters(self,extra_msg = ''):
        """
        Log all setup parameters of this object as a string-formatted event marker.
        """
        self.marker('Experiment Control/Setup/Parameters/%s:"%s"%s' % (self.__class__, str(self.__dict__).replace('"','\\"'), extra_msg))

    def _destroy_object(self, obj, id=-1):
        """Internal helper to automatically destroy a stimulus object."""
        obj = list(obj) if isinstance(obj, tuple) else obj
        obj = [obj] if not isinstance(obj, list) else obj

        try:
            if id > 0 and self.implicit_markers:
                self.marker(id)
                
            for ele in obj:
                if ele is not None:
                    if hasattr(ele,'destroy'):
                        ele.destroy()
                    elif hasattr(ele,'stop'):
                        ele.stop()
                    else:
                        obj.remove(ele)
                    # remove from cancel list
                    self._to_destroy.remove(ele)
        except:
            warnings.warn("Error in destryoing objects")

    # ======================
    # === Core Interface ===
    # ======================

    @abstractmethod
    def run(self):
        """
        Override this function with your code.
        * Expect to receive a ModuleCancelled exception during any call to a time-consumption function (like sleep());
          this happens when the experimenter decides to cancel your current run.
        * Consider using try/finally in your run() function to clean up any on-screen (or audio) resources when the
          module is cancelled. This is especially true in the advanced use case of implementing parallel sub-tasks that
          are intended to be cancelled at some point by the main task.
        """