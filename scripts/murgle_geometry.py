

class GeometryMurgler(object):
    def __init__(self, tracker_geometry):
        pass

    def scale_field(self, scale, coils):
        pass

    def tilt_field(self, tilt, coils):
        pass

    def offset_field(self, offset, coils):
        pass

    def tracker_material_density(self, density):
        pass

    def replace_line(self, filename_src, filename_tgt, keywords, new_line):
        """
        Find a line containing at least one of each keyword; replace with
        new_line.
        - filename_src: string filename. Source text is read from filename_src
        - filename_tgt: string filename. Replaced text is written to filename_tgt
        - keywords: list of string keywords replace all lines containing at 
          least one instance of each keyword
        - new_line: put "new_line" in place of given line
        """
        pass
