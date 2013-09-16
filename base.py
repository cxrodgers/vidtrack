import my, my.misc, numpy as np, os, glob


class FileSchema:
    """Object to encapsulate the file schema for a single vidtrack session
    
    Returns filenames upon request, checks for existing files, etc.
    
    Each session is associated with a directory called 'full_path'.
    Within this directory is a set of image files, named something like
    '0035.png' where the number should be the behavioral trial number.
    
    Other files:
        video_filename : something ending in 'mp4'
        database_filename : session_name.pdict containing a pickled dict
    """
    def __init__(self, full_path):
        self.full_path = os.path.abspath(full_path)
        self.name = os.path.split(self.full_path)[1]
        self.IMAGE_CONSTRUCTION_STR = r'%04d.png'
        self.IMAGE_REGEX_STR = r'(\d+).png'
        
        # Find the video filename
        video_candidates = glob.glob(os.path.join(self.full_path, '*.mp4'))
        if len(video_candidates) == 0:
            self.video_filename = None
        elif len(video_candidates) == 1:
            self.video_filename = video_candidates[0]
        else:
            print "warning: multiple video files in %s" % self.full_path
            self.video_filename = video_candidates[0]
        
        # Find the image files
        self.image_numbers = self._load_image_numbers()
        self.image_filenames = map(self.trial2image_filename,   
            self.image_numbers)
        self.image_full_filenames = map(
            lambda s: os.path.join(self.full_path, s), self.image_filenames)
    
    def trial2image_filename(self, trial_number):
        return self.IMAGE_CONSTRUCTION_STR % trial_number
    
    def _load_image_numbers(self):
        all_files = glob.glob(os.path.join(self.full_path, '*.png'))
        image_numbers = np.array(my.misc.apply_and_filter_by_regex(
            self.IMAGE_REGEX_STR, all_files, sort=True))
        return image_numbers
    
    @property
    def n2v_sync_filename(self):
        return os.path.join(self.full_path, 'N2V_SYNC')
    
    @property
    def v2n_sync_filename(self):
        return os.path.join(self.full_path, 'V2N_SYNC')
    
    @property
    def db_filename(self):
        return os.path.join(self.full_path, self.name + '.pdict')


class Session:
    """Object to handle reading and writing from vidtrack sessions
    
    Generally this is initialized from an existing session.
    To create a session, see create_session
    """
    def __init__(self, full_path=None, file_schema=None):
        """Initialize from a file schema (preferred)"""
        if file_schema is None:
            self.file_schema = FileSchema(full_path=full_path)
        else:
            self.file_schema = file_schema

    def write_n2v_sync(self, n2v_sync):
        """Write sync info as plaintext"""
        np.savetxt(self.file_schema.n2v_sync_filename, n2v_sync)
    
    def write_v2n_sync(self, v2n_sync):
        """Write sync info as plaintext"""
        np.savetxt(self.file_schema.v2n_sync_filename, v2n_sync)
    
    def save_db(self, db):
        """Save a new copy of the database"""
        my.misc.pickle_dump(db, self.file_schema.db_filename)
    
    def load_db(self, db):
        """Return current copy of the database"""
        return my.misc.pickle_load(self.file_schema.db_filename)

    @property
    def n2v_sync(self):
        res = None
        try:
            res = np.loadtxt(self.file_schema.n2v_sync_filename,
                dtype=np.float)
        except IOError:
            pass
        return res
    
    @property
    def v2n_sync(self):
        res = None
        try:
            res = np.loadtxt(self.file_schema.v2n_sync_filename,
                dtype=np.float)
        except IOError:
            pass
        return res    

def create_session(full_path, video_filename=None, v2n_sync=None, 
    n2v_sync=None, db=None):
    """Factory to create new vidtrack session"""
    # Create directory
    if not os.path.exists(full_path):
        os.mkdir(full_path)
    
    # Create schema and session
    fs = FileSchema(full_path)
    session = Session(file_schema=fs)
    
    # Link video
    if video_filename is not None:
        video_filename = os.path.abspath(video_filename)
        short_filename = os.path.split(video_filename)[1]
        new_video_filename = os.path.join(full_path, short_filename)
        os.system('ln -s %s %s' % (video_filename, new_video_filename))
    
    # Write syncs
    if v2n_sync is not None:
        session.write_v2n_sync(v2n_sync)
    if n2v_sync is not None:
        session.write_n2v_sync(n2v_sync)

    return session