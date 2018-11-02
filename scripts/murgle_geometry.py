import xml.etree.ElementTree
import glob
import os

class GeometryMurgler(object):
    def __init__(self, tracker_geometry, geometry_dir_name, src_dir):
        self.geometry = tracker_geometry
        self.dir = geometry_dir_name
        self.src_dir = src_dir
        self.tracker = None

    def murgle(self):
        self.tracker = 0
        if self.geometry["tracker"] == "tkd":
            self.tracker = 1
        self.move_tracker(self.geometry["position"], self.geometry["rotation"])
        self.tracker_material_density(self.geometry["density"])
        self.scale_field(self.geometry["scale"])
       
    def rescale(self, line, new_scale):
        words = line.split(" ")
        value = float(words[-1])*new_scale
        words[-1] = str(value)
        line = " ".join(words)
        return line

    def scale_field(self, scale):
        solenoid = ["SSU", "SSD"][self.tracker]
        fin = open(self.dir+"/ParentGeometryFile.dat")
        lines = [line.rstrip() for line in fin.readlines()]
        fin.close()
        for coil, new_scale in scale.iteritems():
            subname = solenoid+coil+"Current"
            for i, line in enumerate(lines):
                if line.find(subname) > 0 and line.find("Substitution") > 0:
                    lines[i] = self.rescale(line, new_scale)

        fout = open(self.dir+"/ParentGeometryFile.dat.tmp", "w")
        for line in lines:
            fout.write(line+'\n')
        fout.close()
        os.rename(self.dir+"/ParentGeometryFile.dat.tmp", self.dir+"/ParentGeometryFile.dat")


    def get_element_recursive_child(self, element_src, tag, required_attributes):
        """
        Get element which has a child with given tag and attributes
        - element_src: check recursively for children in this elements
        - tag: string tag. Returns element_src if one of its children has tag
        - required_attributes: dictionary. Returns element_src if one of its 
          children has all attributes in required_attributes with matching value
          If you don't want to check value, set to None.
        """
        for child in element_src:
            if child.tag == tag:
                for key in required_attributes:
                    if key not in child.attrib:
                        continue
                    if required_attributes[key] == None or \
                       required_attributes[key] == child.attrib[key]:
                        return element_src
            else:
                volume = self.get_element_recursive_child(child, tag, required_attributes)
                if volume != None:
                    return volume

    def get_element_recursive(self, element_src, tag, required_attributes):
        """
        Get element which has given tag and attributes
        - element_src: check recursively for children in this elements
        - tag: string tag. Returns element_src with this tag
        - required_attributes: dictionary. Returns element_src if it has all 
          attributes in required_attributes with matching value
          If you don't want to check value, set to None.
        """
        if element_src.tag == tag:
            for key in required_attributes:
                if key not in element_src.attrib:
                    continue
                if required_attributes[key] == None or \
                    required_attributes[key] == element_src.attrib[key]:
                    return element_src
        else:
            for child in element_src:
                element = self.get_element_recursive(child, tag, required_attributes)
                if element != None:
                    return element
      

    def move_tracker(self, position, rotation):
        """
        Apply a translation and rotation to the tracker
        - position: translate the tracker by the given distance, in addition to
          any default translation
        - rotation: rotate the tracker by the given angle, in addition to any
          default rotation
        """
        if self.tracker == 0:
            src_filename = self.dir+"/SolenoidUS.gdml"
            target_filename = self.src_dir+"/Tracker0.gdml"
        else:
            src_filename = self.dir+"/SolenoidDS.gdml"
            target_filename = self.src_dir+"/Tracker1.gdml"
        tree = xml.etree.ElementTree.parse(src_filename)
        volume = self.get_element_recursive_child(tree.getroot(), "file", {"name":target_filename})
        if volume == None:
            raise RuntimeError("Failed to find tag "+target_filename+" in "+src_filename)
        for child in volume:
            delta = {}
            if child.tag == "position":
                delta = position
            elif child.tag == "rotation":
                delta = rotation
            else:
                continue
            attrib = child.attrib
            for axis in delta:
                new_value = float(attrib[axis])+delta[axis]
                attrib[axis] = repr(new_value)
            child.attrib = attrib
        tree.write(src_filename+".tmp")
        os.rename(src_filename+".tmp", src_filename)

    def tracker_material_density(self, density):
        # HACKING this stuff in ~/data/geometry
        src_filename_glob = self.dir+"/Tracker"+str(self.tracker)+"View?Station?_Doublet.gdml"
        for src_filename in glob.glob(src_filename_glob):
            tree = xml.etree.ElementTree.parse(src_filename)
            volume = self.get_element_recursive(tree.getroot(), "material", {"name":"RenCast6400"})
            if volume == None:
                raise RuntimeError("Failed to find tag RenCast6400 in "+src_filename)
            for child in volume:
                if child.tag == "D":
                    child.attrib["value"] = repr(density)
            tree.write(src_filename+".tmp")
            os.rename(src_filename+".tmp", src_filename)

