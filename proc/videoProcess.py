

__Author = 'Farsheed Ashouri'
__Copyright = 'Vishka Studio'

########### Usage #############
# This tool must be used in a crontab
#Example:
# * * * * * python /home/farsheed/web2py/web2py.py -S vixenserver -M -N -R applications/vixenserver/proc/videoProcess.py

## Imports:

########## Requirements ##############
# 1- Linux operating system with python 2.6+
# 2- Non-free compiled version of ffmpeg
# 3- mplayer for playing videos
#


import os
import sys
from subprocess import Popen, PIPE, call  # everything nedded to handle external commands
import time
import uuid
import datetime
import logging


class main(object):
    '''In this class, wI have everything need to process videos uploaded
        To vixen server.

        Usage:
    '''
    def __init__(self):
        '''Constructor'''
        #logging.info("Starting to process")
        #self.unlock()
        if not self.is_busy():
            #==== Run commands go here ...
            self.run()
            #====
            self.unlock()  # At the end we must release the lock

    def get_ffmpeg_bin(self):
        '''Retuen full path of ffmpeg bin folder'''
        ffmpegpath = os.path.abspath('%s/exec/ffmpeg/bin' %
                                   request.folder)
        return ffmpegpath

    def run(self):
        ''' Run every needed function in order'''
        self.process_shots()  # process all videos and shots...
        seqs = self.find_changed_sequences()  # find dirty sequences
        for sequence in seqs:
            self.gen_seq_preview(
                sequence)  # generate preview for each dirty one.
        self.do_project_previews()

    def lock(self):
        '''Unlock the process'''
        bdb = db(db.process.name == 'crontab').select().first()
        if bdb:
            bdb.update_record(islocked=True)
            db.commit()

    def unlock(self):
        '''Unlock the process'''
        bdb = db(db.process.name == 'crontab').select().first()
        if bdb:
            bdb.update_record(islocked=False)
            db.commit()

    def is_busy(self):
        '''Check if another process is under way'''
        bdb = db(db.process.name == 'crontab').select().first()
        if not bdb:
            bdb = db.process.insert(name='crontab', islocked=True)
            db.commit()
        elif bdb.islocked:
            logging.warn("Another Process is active. Goodbye.")
            return True
        else:
            logging.info("Not any other process found. Starting ...")
            self.lock()

    def get_upload_folder(self):
        upload_folder = '%s/static/uploads' % request.folder
        return os.path.abspath(upload_folder)

    def process(self, execfn):
        '''General external process'''
        p = Popen(execfn, shell=True, env=os.environ, stdout=PIPE,
                  universal_newlines=True)  # process
        (stdout, stderr) = p.communicate()
        if not stderr:  # if there is no error
            return stdout
        else:
            logging.error(stderr)

    def play(self, video_path):
        '''Play a video with mplayer'''
        arg = 'nice mplayer "%s"' % video_path
        pr = self.process(arg)
        return pr

    def duration(self, path):
        '''Find video duration'''
        arg = '''nice "%s/ffprobe" -show_format "%s" 2>&1''' % (self.get_ffmpeg_bin(), path)
        pr = self.process(arg)
        dupart = pr.split('duration=')  # text processing output of a file
        if pr and len(dupart) > 1:
            du = dupart[1].split()[0]
            try:
                return float(du)
            except ValueError:
                logging.error("Can not find duration of %s video file. "
                              % path)
                return

    def thumb(self, path, text=None):
        '''generate a thumbnail from a video file and return a vfile db'''
        upf = self.get_upload_folder()
        fid = uuid.uuid4()
        fmt = 'png'
        name = '%s/%s.%s' % (upf, fid, fmt)
        arg = '''nice "%s/ffmpeg" -threads 2 -i "%s" -an -r 1 -vframes 1 -sameq -s 256x144 -y "%s"''' \
            % (self.get_ffmpeg_bin(), path, name)
        pr = self.process(arg)
        newt = db.vfile.insert(uuid=fid, ext='png')
        return newt

    def get_font_path(self, mode='L'):
        ''' get font path'''
        fontpath = os.path.abspath('%s/static/fonts/Ubuntu-L.ttf' %
                                   request.folder)
        if mode == 'M':
            fontpath = os.path.abspath('%s/static/fonts/Ubuntu-M.ttf' %
                                       request.folder)
        return fontpath

    def get_draw_arg(self, text, rate, pos, timecode=None):
        '''Ffmpeg needs a custom format for adding text file.'''
        draw = None
        dtest = list()
        fontpath = self.get_font_path()
        tlist = None
        if text:
            tlist = text.split('\n')
            for i in tlist:
                dtest.append('''drawtext=fontsize=18:box=1:fontfile='%s':text='%s':boxcolor='eeeeee99':fontcolor='515151ee':shadowx=1:shadowy=2:shadowcolor='f8f8f899':x=20:y=%s''' %
                             (fontpath, i, (tlist.index(i) + pos) * 25))
        if timecode:
            fontpath = self.get_font_path(mode='M')
            dtest.append('''drawtext=fontsize=18:box=1:fontfile='%s':rate=%s:timecode='00\\:00\\:00\\:00':boxcolor='eeeeee99':fontcolor='313131ff':shadowx=1:shadowy=2:shadowcolor='f8f8f899':x=20:y=%s''' %
                         (fontpath, rate, (pos - 1) * 25))

        draw = '-vf "[in]%s[out]"' % (','.join(dtest))
        if text or timecode:
            return draw
        else:
            return ''

    def getTimecode(self, frame, rate):
        '''Get standard timecode'''
        seconds = frame / rate
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        timecode = "%02d:%02d:%04f" % (h, m, s)
        return timecode

    def convert(self, path, rate=24, delete=False,
                ss=0, t=2000000, fmt='mpg', timecode=None, text=None,
                logo=None, cache=None, pos=1, mayarate=None):
        '''convert given file to mpg video'''
        if not mayarate:
            mayarate = rate
        newname = '%s/%s.%s' % (self.get_upload_folder(), uuid.uuid4(), fmt)
        draw = self.get_draw_arg(text, rate, pos, timecode)
        #ss = self.getTimecode(ss, rate)
        #t = self.getTimecode(t, rate)
        ss = ss / float(rate)
        t = t / float(rate)
        arg = 'nice "%s/ffmpeg" -threads 2 -r %s -i %s -ss %s -t %s -s hd480 %s -an -sameq -r %s -y %s' % \
            (self.get_ffmpeg_bin(), mayarate, path, ss, t, draw, rate, newname)

        if cache:
            arg = 'nice "%s/ffmpeg" -threads 2 -i %s -ss %s -t %s %s -s hd480 -an -sameq -y %s' % \
                (self.get_ffmpeg_bin(), path, ss, t, draw, newname)
        pr = self.process(arg)
        if os.path.isfile(newname) and os.path.getsize(newname):
            return newname

    def video_split(self, fdb, rate=24):
        '''split a video to new videos based on cuts list'''
        if not fdb.cuts:
            return  # no cuts
        else:
            cuts = fdb.cuts  # list of integer numbers
            path = self.get_video_path(fdb)
            newvids = list()
            ## [1.0, 100.0, 140.0, 203.0]
            for i in cuts:
                try:
                    next_cut = cuts[cuts.index(i) + 1]
                except IndexError:
                    next_cut = 1000000.0  # a big number cuse it's last shot
                t = (next_cut - i)
                ss = (i - cuts[0])
                newvid = self.convert(path, rate=rate, ss=ss, t=t)
                newvids.append(newvid)
            return newvids

    def generate_cache(self, fdb):
        '''Generate a cache mpg video file'''
        path = self.get_video_path(fdb)
        cache = self.convert(path, cache=True)
        fdb.update_record(cache=os.path.basename(cache))
        db.commit()
        return cache

    def combine(self, pathlist, timecode=None, rate=24, text=None,
                logo=False, pos=1):
        '''Combine mpg files from a list'''
        flist = '"' + '" "'.join(pathlist) + '"'
        med = uuid.uuid4()
        mid_name = '%s/%s.mpg' % (self.get_upload_folder(), med)
        arg = 'cat %s > %s' % (flist, mid_name)  # combine it
        pr = self.process(arg)
        mpg = self.convert(mid_name, rate=rate, fmt='mpg', timecode=timecode,
                           text=text, logo=logo, pos=pos)
        if os.path.isfile(mpg) and os.path.getsize(mpg):
            return mpg

    def find_new_videos(self):
        '''find unprocessed videos'''
        vids = list()
        dirts = db(db.shot.dirty == True).select()
        for i in dirts:
            if i.preview:
                vids.append(i.preview)
        return vids

    def get_video_path(self, fdb):
        '''generate file path based on given vfile db'''
        upload_folder = self.get_upload_folder()
        dstpath = '%s/%s' % (upload_folder, fdb.name)
        if os.path.isfile(dstpath) and os.path.getsize(dstpath):
            return os.path.abspath(dstpath)

    def get_video_cache(self, fdb):
        '''generate file path based on given vfile db'''
        upload_folder = self.get_upload_folder()
        if fdb.cache:  # if file has a cache file:
            dstpath = '%s/%s' % (upload_folder, fdb.cache)
            if os.path.isfile(dstpath) and os.path.getsize(dstpath):
                return os.path.abspath(dstpath)
            else:
                fdb.update_record(cache=None)
                db.commit()
                self.get_video_cache(fdb)  # run it again
        else:  # cache file is empty:
            cache = self.generate_cache(fdb)
            return cache

    def add_video_to_db(self, path, isfinished=True, cache=None):
        '''Add new generated video to database - return a db'''
        fid = uuid.uuid4()  # a uniqe id for new video
        if cache:
            cache = os.path.basename(cache)
        newprocess = db.process.insert(name=fid, isfinished=isfinished)
        newfile = db.vfile.insert(uuid=fid, cache=cache,
                name=os.path.basename(path), isvideo=True, process=newprocess)  # create a new file
        return newfile

    def gen_seq_preview(self, sdb):
        '''Generate a sequence preview (most recently changed)'''
        rate = sdb.project.fps
        cpathes = list()  # a list for our cache filed videos(for combining) ...
        name = None
        if sdb.preview:
            sdb.preview.process.update_record(islocked=True, isfinished=False)
            db.commit()
        if not sdb.ignore_shots:  # calculate preview from shots
            shots = db(db.shot.sequence == sdb).select(orderby=db.shot.number)
            for shot in shots:
                #print shot.number
                if shot.preview:
                    cpath = self.get_video_cache(shot.preview)
                    if cpath:  # cache is available
                        cpathes.append(cpath)

            if cpathes:
                final_mpg = self.combine(cpathes, rate=rate)  # combine shots
                name = self.convert(final_mpg, rate=rate, fmt='m4v')  # convert to m4v
                du = self.duration(final_mpg)
                frames = 0  # init frames
                if du:
                    frames = int(du * sdb.project.fps) + 1
        else:  # use sequence's own video to generate preview
            path = self.get_video_path(sdb.preview)
            final_mpg = self.convert(path, rate=rate, timecode=True, \
                    text='Seq%s' % sdb.number, pos=2)  # Papercity | Seq2
            du = self.duration(final_mpg)
            frames = 0
            if du:
                frames = int(du * rate) + 1
            name = self.convert(final_mpg, rate=rate, fmt='m4v', logo=1)
            newt = self.thumb(final_mpg)
            if sdb.preview.cuts:  # video must cut down to smaller ones:
                newvids = self.video_split(sdb.preview, rate)
                for i in newvids:
                    newvid = self.add_video_to_db(path=i, isfinished=False)
                    num = newvids.index(i) + 1
                    subshot = db((db.shot.number == num) & \
                            (db.shot.sequence == sdb)).select().first()
                    if subshot:
                        subshot.update_record(preview=newvid, dirty=True)
                        db.commit()
                if newvids:  # ook! we need to process again!
                    sdb.update_record(ignore_shots=False, dirty=True)
                    sdb.project.update_record(dirty=True)
                    #self.unlock()
                    db.commit()  # save changes
                    return self.run()  # start again

        if name:  # if new video converted and ready:
            newfile = self.add_video_to_db(path=name, cache=final_mpg)
            newt = self.thumb(final_mpg)
            self.add_to_previews(sdb, newfile)
            sdb.update_record(chart1=None, frames=frames, preview=newfile,
                    thumb=newt, dirty=False, \
                    modification_date=datetime.datetime.now())
            sdb.project.update_record(chart1=None, dirty=True)  # empty the chart
            db.commit()
        else:
            sdb.preview.process.update_record(islocked=False, isfinished=True)
            db.commit()

    def find_changed_sequences(self):
        '''find changed sequences based on a list of changed files'''
        seqs = db(db.sequence.dirty == True).select()
        return seqs

    def find_changed_projects(self):
        '''find changed sequences based on a list of changed files'''
        prs = db(db.project.dirty == True).select()
        return prs

    def get_project_sequences(self, project):
        '''Get sequences of a specific project'''
        seqs = db(
            db.sequence.project == project).select(orderby=db.sequence.number)
        return seqs

    def do_project_previews(self):
        '''Find dirty projects and generate videos for them'''
        prs = self.find_changed_projects()
        for project in prs:
            if project.preview:
                project.preview.process.update_record(islocked=True, isfinished=False)
                db.commit()

            rate = project.fps
            interm = list()
            seqs = self.get_project_sequences(project)
            for seq in seqs:
                if seq.preview:
                    movie = self.get_video_cache(seq.preview)
                    if movie:
                        interm.append(movie)

            if interm:
                mpg = self.combine(interm, rate=rate,
                                   text='\\%F\n' + project.name.title(),
                                   timecode=True, pos=15)
                newprev = self.convert(mpg, rate=rate, fmt='m4v', logo=1)
                du = self.duration(newprev)
                frames = 0
                if du:
                    frames = int(du * project.fps) + 1
                fid = uuid.uuid4()
                if newprev:
                    newprocess = db.process.insert(name=fid, isfinished=True)
                    newfile = self.add_video_to_db(path=newprev, cache=mpg)
                    newt = self.thumb(mpg)
                    self.add_to_previews(project, newfile)
                    project.update_record(
                        modification_date=datetime.datetime.now(),
                        preview=newfile, thumb=newt, frames=frames, dirty=False)
                    db.commit()

            if project.preview:
                project.preview.process.update_record(islocked=False, isfinished=True)
                db.commit()

    def add_to_previews(self, target, preview):
        '''Add this preview to proviews list'''
        old_prevs = target.previews
        if not old_prevs:
            new_prevs = [preview]
        else:
            new_prevs = old_prevs + [preview]
        target.update_record(previews=new_prevs)
        db.commit()

    def process_shots(self):
        vids = self.find_new_videos()
        tmp = list()
        for video in vids:
            path = self.get_video_path(video)
            video.process.update_record(islocked=True, isfinished=False)
            db.commit()
            shots = db(db.shot.preview == video).select()  # find related shots
            for shot in shots:
                shot.sequence.update_record(dirty=True)
                shot.sequence.project.update_record(dirty=True)
                db.commit()
                if path:
                    rate = shot.sequence.project.fps
                    mayarate = shot.sequence.project.mayafps
                    midname = self.convert(
                        path, rate=rate,  delete=True, fmt='mpg',
                        timecode=True, text='Seq%s|Shot%s' % \
                        (shot.sequence.number, shot.number), pos=2)  # Papercity | Seq2 | Shot6
                    du = self.duration(midname)
                    frames = 0
                    if du:
                        frames = int(du * rate) + 1
                    newname = self.convert(midname, fmt='m4v', rate=rate, logo=1)  # add to playable format using handbrake
                    newt = self.thumb(midname)
                    if newname:
                        pr = db.process.insert(isfinished=True)
                        newp = self.add_video_to_db(
                            path=newname, cache=midname)
                        self.add_to_previews(shot, newp)
                        shot.update_record(preview=newp,
                                dirty=False, frames=frames, thumb=newt,
                                modification_date=datetime.datetime.now())
                        shot.sequence.update_record(dirty=True)
                        db.commit()

                else:
                    shot.update_record(preview=None, dirty=False)  # clean the preview (cause it is not available)
                    db.commit()
            video.process.update_record(islocked=False, isfinished=True)
            db.commit()


if __name__ == '__main__':
    main()  # run the process
