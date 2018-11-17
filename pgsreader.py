class InvalidSegmentException(Exception):
    '''raised when a segment does not match PGS specification'''

def i(b, s, l):
    return int(b[s:s+l].hex(), base=16)

class PGSReader:

    def __init__(self, filepath):
        with open(filepath, 'rb') as f:
            self.bytes = f.read()

    def make_segment(self, bytes_):
        cls = SEGMENT_TYPE[bytes_[10]]
        return cls(bytes_)
    
    @classmethod
    def get_segments(cls, bytes_):
        segments = []
        while bytes_:
            size = 13 + int(bytes_[11:13].hex(), base=16)
            segments.append(bytes_[:size])
            bytes_ = bytes_[size:]
        return segments

    @property
    def segments(self):
        if not hasattr(self, '_segments'):
            seg_bytes = self.get_segments(self.bytes)
            self._segments = [self.make_segment(s) for s in seg_bytes]
        return self._segments


class BaseSegment:

    SEGMENT = {
        int('0x14', base=16): 'PDS',
        int('0x15', base=16): 'ODS',
        int('0x16', base=16): 'PCS',
        int('0x17', base=16): 'WDS',
        int('0x80', base=16): 'END'
    }
    
    def __init__(self, bytes_):
        self.bytes = bytes_
        if bytes_[:2] != b'PG':
            raise InvalidSegmentException
        self._pts = i(bytes_, 2, 4)/90
        self._dts = i(bytes_, 6, 4)/90
        self._type = self.SEGMENT[bytes_[10]]
        self._size = i(bytes_, 11, 2)
        self.data = bytes_[13:]

    def __len__(self):
        return self._size

    @property
    def pts(self): return self._pts

    @property
    def presentation_timestamp(self): return self._pts

    @property
    def dts(self): return self._dts

    @property
    def decoding_timestamp(self): return self._dts

    @property
    def type(self): return self._type

    @property
    def segment_type(self): return self._type

    @property
    def size(self): return self._size

class PresentationCompositionSegment(BaseSegment):

    class CompositionObject:

        def __init__(self, bytes_):
            self.bytes = bytes_
            self.object_id = i(bytes_, 0, 2)
            self.window_id = bytes_[2]
            self.cropped = bool(bytes_[3])
            self.x_offset = i(bytes_, 4, 2)
            self.y_offset = i(bytes_, 6, 2)
            if self.cropped:
                self.crop_x_offset = i(bytes_, 8, 2)
                self.crop_y_offset = i(bytes_, 10, 2)
                self.crop_width = i(bytes_, 12, 2)
                self.crop_height = i(bytes_, 14, 2)

    STATE = {
        int('0x00', base=16): 'Normal',
        int('0x40', base=16): 'Acquisition Point',
        int('0x80', base=16): 'Epoch Start'
    }

    def __init__(self, bytes_):
        BaseSegment.__init__(self, bytes_)
        self.width = i(self.data, 0, 2)
        self.height = i(self.data, 2, 2)
        self.frame_rate = self.data[4]
        self._num = i(self.data, 5, 2)
        self._state = self.STATE[self.data[7]]
        self.palette_update = bool(self.data[8])
        self.palette_id = self.data[9]
        self._num_comps = self.data[10]

    @property
    def composition_number(self): self._num

    @property
    def composition_state(self): return self._state

    @property
    def composition_objects(self):
        if not hasattr(self, '_composition_objects'):
            self._composition_objects = self.get_composition_objects()
            if len(self._composition_objects) != self._num_comps:
                print('Warning: Number of composition objects asserted '
                      'does not match the amount found.')
        return self._composition_objects

    def get_composition_objects(self):
        bytes_ = self.data[11:]
        comps = []
        while bytes_:
            length = 8*(1 + bool(bytes_[3]))
            comps.append(self.CompositionObject(bytes_[:length]))
            bytes_ = bytes_[length:]
        return comps

class WindowDefinitionSegment(BaseSegment):

    def __init__(self, bytes_):
        BaseSegment.__init__(self, bytes_)
        self.window_id = self.data[0]
        self.x_offset = i(self.data, 1, 2)
        self.y_offset = i(self.data, 3, 2)
        self.width = i(self.data, 5, 2)
        self.height = i(self.data, 7, 2)

class PaletteDefinitionSegment(BaseSegment):

    def __init__(self, bytes_):
        BaseSegment.__init__(self, bytes_)
        self.palette_id = self.data[0]
        self.version = self.data[1]
        self.entry_id = self.data[2]
        self.y = self.data[3]
        self.cr = self.data[4]
        self.cb = self.data[5]
        self.alpha = self.data[6]

    @property
    def luminance(self): return self.y

    @property
    def color_diff_red(self): return self.cr

    @property
    def color_diff_blue(self): return self.cb

    @property
    def transparency(self): return self.alpha

class ObjectDefinitionSegment(BaseSegment):

    SEQUENCE = {
        int('0x40', base=16): 'Last',
        int('0x80', base=16): 'First',
        int('0xc0', base=16): 'First and last'
    }
    
    def __init__(self, bytes_):
        BaseSegment.__init__(self, bytes_)
        self.id = i(self.data, 0, 2)
        self.version = self.data[2]
        self.in_sequence = self.SEQUENCE[self.data[3]]
        self.data_len = i(self.data, 4, 3)
        self.width = i(self.data, 7, 2)
        self.height = i(self.data, 9, 2)
        self.img_data = self.data[11:]
        if len(self.img_data) != self.data_len:
            print('Warning: Image data length asserted does not match the '
                  'length found.')

class EndSegment(BaseSegment):

    @property
    def is_end(self): return True
        
SEGMENT_TYPE = {
    int('0x14', base=16): PaletteDefinitionSegment,
    int('0x15', base=16): ObjectDefinitionSegment,
    int('0x16', base=16): PresentationCompositionSegment,
    int('0x17', base=16): WindowDefinitionSegment,
    int('0x80', base=16): EndSegment
}
