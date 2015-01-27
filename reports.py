import time

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, BaseDocTemplate, Image

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Frame, Spacer, PageBreak, Flowable
from reportlab.platypus.paragraph import FragLine
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import utils

class Line(Flowable):
    """Line flowable --- draws a line in a flowable"""

    def __init__(self, width, height=0):
        Flowable.__init__(self)
        self.width = width
        self.height = height
 
    def __repr__(self):
        return "Line(w=%s)" % self.width
 
    def draw(self):
        """ draw the line """
        self.canv.line(0, self.height, self.width, self.height)

class Report(object):
    def __init__(self, filename, size=A4):
        self.doc = SimpleDocTemplate(filename,pagesize=size,
                        rightMargin=72,leftMargin=72,
                        topMargin=72,bottomMargin=18)
        self.elements = []
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        self.width, self.height = size
    
    def add_spacer(self, height=0.25*inch):
        """ Add white space between elements """
        self.elements.append(Spacer(self.width, height))
    
    def add_text(self, text, fontsize=12, text_style='Normal'):
        """ Add text to the report """
        if text_style == 'Normal':
            style = self.styles['Normal']
        elif text_style == 'Center':
            style = self.styles['Center']
        else:
            # Not defined yet
            style = self.styles['Normal']
        self.elements.append(Paragraph("<font size=%d>%s</font>" % (fontsize,text), style))
        
    def add_line(self):
        """ Add horizontal line between items """
        self.elements.append(Line(self.width-2*self.doc.leftMargin))
    
    def add_new_page(self):
        """ Insert empty page """
        self.elements.append(PageBreak())
        
    def add_image(self, filename, height=6*inch):
        """ Insert an image to the report """
        img = utils.ImageReader(filename)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        self.elements.append(Spacer(self.width, 0.25*inch))
        self.elements.append(Image(filename, width=(height/aspect), height=height))
    
    def title_page(self, title, subtitle=""):
        """ Creates title (first) page """
        self.add_text(title, 18, 'Center')
        self.add_spacer()
        if subtitle:
            self.add_text(subtitle, 14, 'Center')
            self.add_spacer()
        self.add_line()
        self.add_spacer(0.5*inch)
        self.add_text(time.strftime("%Y-%m-%d %H:%M"))
        self.add_new_page()
        
    def header(self, title):
        """ Creates page header """
        self.add_text(title, 12)
        self.add_spacer(0.1*inch)
        self.add_line()
        self.add_spacer(0.1*inch)
        
    def save(self):
        self.doc.build(self.elements)

