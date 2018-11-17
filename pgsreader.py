class InvalidSegmentException(Exception):
    '''raised when a segment does not match PGS specification'''

class PGSReader:

    def __init__(self, filepath):
        with open(filepath, 'rb') as f:
            self.bytes = f.read()

    def make_segment(self, bytes_):
        cls = SEGMENT_TYPE[bytes_[10]]
        return cls(bytes_)
    
    def get_segments(self, bytes_):
        segments = []
        while bytes_:
            size = 13 + int(bytes_[11:13].hex(), base=16)
            segments.append(self.make_segment(bytes_[:size]))
            bytes_ = bytes_[size:]
        return segments

    @property
    def segments(self):
        if not hasattr(self, '_segments'):
            self._segments = self.get_segments(self.bytes)
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
        self.pts = int(bytes_[2:6].hex(), base=16)/90
        self.dts = int(bytes_[6:10].hex(), base=16)/90
        self.type = self.SEGMENT[bytes_[10]]
        self.size = int(bytes_[11:13].hex(), base=16)
        self.data = bytes_[13:]

    def __len__(self):
        return self.size

    @property
    def presentation_timestamp(self): return self.pts

    @property
    def decoding_timestamp(self): return self.dts

    @property
    def segment_type(self): return self.type

class PresentationCompositionSegment(BaseSegment):

    class CompositionObject:

        def __init__(self, bytes_):
            self.bytes = bytes_
            self.object_id = int(bytes_[0:2].hex(), base=16)
            self.window_id = bytes_[2]
            self.cropped = bool(bytes_[3])
            self.x_offset = int(bytes_[4:6].hex(), base=16)
            self.y_offset = int(bytes_[6:8].hex(), base=16)
            if self.cropped:
                self.crop_x_offset = int(bytes_[8:10].hex(), base=16)
                self.crop_y_offset = int(bytes_[10:12].hex(), base=16)
                self.crop_width = int(bytes_[12:14].hex(), base=16)
                self.crop_height = int(bytes_[14:16].hex(), base=16)

    STATE = {
        int('0x00', base=16): 'Normal',
        int('0x40', base=16): 'Acquisition Point',
        int('0x80', base=16): 'Epoch Start'
    }

    def __init__(self, bytes_):
        BaseSegment.__init__(self, bytes_)
        self.width = int(self.data[0:2].hex(), base=16)
        self.height = int(self.data[2:4].hex(), base=16)
        self.frame_rate = self.data[4]
        self._num = int(self.data[5:7].hex(), base=16)
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
        self.x_offset = int(self.data[1:3].hex(), base=16)
        self.y_offset = int(self.data[3:5].hex(), base=16)
        self.width = int(self.data[5:7].hex(), base=16)
        self.height = int(self.data[7:9].hex(), base=16)

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
        self.id = int(self.data[0:2].hex(), base=16)
        self.version = self.data[2]
        self.in_sequence = self.SEQUENCE[self.data[3]]
        self.data_len = int(self.data[4:7].hex(), base=16)
        self.width = int(self.data[7:9].hex(), base=16)
        self.height = int(self.data[9:11].hex(), base=16)
        self.img_data = self.data[7:]
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
