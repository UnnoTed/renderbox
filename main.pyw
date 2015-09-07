"""
renderb0x

Developed by sk1LLb0X
"""
VERSION = 0.1

import os, sys, json, urllib, signal, threading, Queue, winsound, shutil, re, wave, contextlib, subprocess, platform

from PyQt4.QtCore import pyqtSignature, QString, Qt, QVariant, SIGNAL, SLOT, QThread
from PyQt4.QtGui import *
from PyQt4 import QtCore

from ui.main import Ui_Form as main_Form
from ui.render import Ui_Render as render_Form

os_arch = "x64" if platform.machine().endswith('64') == True else "x86"
videos = {}
currentFID = "a1"

ffmpeg_cmdline = 'ffmpeg_{arch} -f image2 -r {fps} -i {frame} -i {audio} -r {fps} -b:a 128k -b:v {bitrate}k -minrate {bitrate}k -maxrate {bitrate}k {render_path}\\{id}_{fileName}.mp4'

cfg = {}
try:
  with open("config.json") as file:
    cfg = json.load(file)
except IOError:
  with open("config.json", "w") as file:
    file.write("{}")
    file.close()
    cfg = {}

def saveConfig():
  with open("config.json", "w") as file:
    json.dump(cfg, file, indent = 2, sort_keys = True)

# "global" window
window = None

class RenderProcess(QThread):
  def __init__(self, parent = None):
    super(RenderProcess, self).__init__(parent)

  def setArgs(self, args):
    self.args = args

  def run(self):
    duration = 0.0
    p = subprocess.Popen(self.args, shell = True, stderr = subprocess.PIPE, stdout = subprocess.PIPE)
    self.rProc = p

    while True:
      text = p.stderr.read(128)

      self.emit(SIGNAL("ffmpegLog(QString)"), str(text))

      if not text:
        break

      try:
        current_frame_str = re.search(r'frame=((\s)+)?(?P<frame>\S+) fps=', text)
        self.emit(SIGNAL("updateProgressBar(int)"), int(current_frame_str.groupdict()['frame']))
      except:
        pass

    self.emit(SIGNAL("doneRendering()"))


class RenderWindow(QWidget, render_Form):
  def __init__(self, parent = None):
    QWidget.__init__(self, parent)
    self.setupUi(self)
    self.btn_cancel.clicked.connect(self.cancelRendering)

    self.currentFile = 0

  def cancelRendering(self):
    p = self.rendering.rProc

    # tried p.kill(), os.kill and p.terminate, none of those worked, only taskkill did.
    subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid = p.pid))
    self.hide()

  def start(self):
    self.render_list.clear()
    self.renderLog.setPlainText('')
    for key, val in enumerate(self.info):
      self.render_list.addItem(self.info[key]['file'] if self.currentFile != key else self.info[key]['file'] + ' - Rendering...')

    self.rendering = RenderProcess()

    self.file_name.setText(self.info[self.currentFile]['file'])
    self.file_size.setText(str(self.info[self.currentFile]['size']) + 'MB')
    self.file_audio.setText(self.info[self.currentFile]['audio'])
    self.file_frames.setText(str(self.info[self.currentFile]['frames']))
    self.message = "{file} rendered successfuly!".format(file = self.info[self.currentFile]['file'])

    self.rendering.setArgs(self.args)

    self.connect(self.rendering, SIGNAL("updateProgressBar(int)"), self.updateProgressBar)
    self.connect(self.rendering, SIGNAL("doneRendering()"), self.doneRendering)
    self.connect(self.rendering, SIGNAL("ffmpegLog(QString)"), self.updateLog)

    self.rendering.start()

  def updateProgressBar(self, val):
    self.progressBar.setMaximum(int(self.info[self.currentFile]['frames']))
    self.progressBar.setValue(val)

  def updateLog(self, text):
    text = str(self.renderLog.toPlainText()) + str(text)
    self.renderLog.setPlainText(text)
    self.renderLog.verticalScrollBar().setValue(self.renderLog.verticalScrollBar().maximum())

  # creates a new thread to play the sound without freezing the main window
  def PlaySound(self, soundName):
    soundThread = threading.Thread(target = winsound.PlaySound, args = ("sounds\{sound}.wav".format(sound = soundName), winsound.SND_FILENAME))
    soundThread.start()

  def doneRendering(self):
    self.progressBar.setValue(int(self.info[self.currentFile]['frames']))
    self.PlaySound('done')
    QMessageBox.information(self, "Done", self.message)
    if self.auto_close.isChecked():
      self.hide()
    self.progressBar.setValue(0)
    window.btn_render.setEnabled(True)

""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""" main class """""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""

class MainWindow(QWidget, main_Form):

  def __init__(self, parent = None):
    QWidget.__init__(self, parent)
    self.setupUi(self)

    self.RenderWindow = RenderWindow()

    self.setWindowTitle("renderb0x v" + str(VERSION))

    # buttons
    self.btn_select_path.clicked.connect(self.selectPath)
    self.btn_select_render_path.clicked.connect(self.selectRenderPath)
    self.btn_refresh_list.clicked.connect(self.refreshPath)
    self.btn_render.clicked.connect(self.renderVideo)

    self.video_fps.textChanged.connect(self.changeFPS)
    self.video_bitrate.textChanged.connect(self.changeBitRate)

    if cfg.get('render_path', None):
      self.video_render_path.setText(str(cfg["render_path"]))

    if cfg.get("path", None):
      self.setPath(cfg["path"])

    if cfg.get("fps", None):
      self.video_fps.setText(str(cfg["fps"]))

    if cfg.get("bitrate", None):
      self.video_bitrate.setText(str(cfg["bitrate"]))
    else:
      self.video_bitrate.setText('30000')

    self.video_id.currentIndexChanged.connect(self.updateVideoID)
    self.btn_render.setEnabled(True)

    # fps
    self.fps_auto.stateChanged.connect(self.updateFPS)

    # cmd line
    self.video_cmd_line.textChanged.connect(self.updateCustomCmdLine)
    self.video_cmd_default.stateChanged.connect(self.customCmdLine)
    self.video_cmd_line.setReadOnly(True)

    if cfg.get("path", None) and cfg.get("render_path", None):
      self.btn_render.setEnabled(True)
    else:
      self.btn_render.setEnabled(False)

    self.video_delete_btn.clicked.connect(self.deleteVideos)

  def selectRenderPath(self):
    rPath = str(QFileDialog.getExistingDirectory(self, "Select the output path!"))
    cfg['render_path'] = rPath
    saveConfig()
    self.video_render_path.setText(str(cfg["render_path"]))

    if cfg.get("path", None) and cfg.get("render_path", None):
      self.btn_render.setEnabled(True)
    else:
      self.btn_render.setEnabled(False)

  def updateCustomCmdLine(self):
    if self.video_cmd_default.isChecked() != True:
      cfg['ffmpeg_cmdline'] = str(self.video_cmd_line.text())
      saveConfig()

  def customCmdLine(self, state):
    if state == 2: # checked
      self.video_cmd_line.setText(ffmpeg_cmdline)
      self.video_cmd_line.setReadOnly(True)
    else:
      if cfg.get('ffmpeg_cmdline', None):
        self.video_cmd_line.setText(cfg["ffmpeg_cmdline"])
      self.video_cmd_line.setReadOnly(False)

  def updateFPS(self, state):
    if state == 2: # checked
      self.video_fps.setText(str(self.getFPS(currentFID)))
      self.video_fps.setReadOnly(True)
    else:
      self.video_fps.setReadOnly(False)

  def changeFPS(self):
    cfg["fps"] = float(self.video_fps.text())
    saveConfig()

  def changeBitRate(self):
    cfg["bitrate"] = float(self.video_bitrate.text())
    saveConfig()

  def selectPath(self):
    filePath = str(QFileDialog.getExistingDirectory(self, "Select the first frame ([a-z][0-9]_0000.(tga or jpg))"))
    self.setPath(filePath)

    if cfg.get("path", None) and cfg.get("render_path", None):
      self.btn_render.setEnabled(True)
    else:
      self.btn_render.setEnabled(False)

  def refreshPath(self):
    if cfg.get("path", None):
      self.setPath(cfg["path"])

  def setPath(self, filePath):
    if len(filePath) > 0: # == cancel btn
      # block signals to prevent errors
      self.video_id.blockSignals(True)

      cfg["path"] = filePath
      saveConfig()

      self.video_path.setText(filePath)

      global currentFID
      currentFID = False

      fileRegex = re.compile(r'[a-z][0-9]{1,2}_[0]{4,5}.(jpg|tga)')
      filesRegex = re.compile(r'[a-z][0-9]{1,2}_[0-9]{4,5}')

      global videos
      videos = {}
      self.video_id.clear()

      for f in os.listdir(filePath):
        if os.path.isfile(os.path.join(filePath, f)):
          if fileRegex.search(f):
            choose = str(fileRegex.search(f).group(0))[0:3]
            fid = choose
            if choose[2] == '_':
              fid = choose[0:2]

            currentFID = fid

            videos[fid] = {'frames':[], 'audio': fid + '_.wav', 'ext': str(fileRegex.search(f).group(1))}
            self.video_id.addItem(fid, fid)

          if currentFID and filesRegex.search(f):
            videos[currentFID]["frames"].append(f)

      if len(videos) > 0:
        # get some id
        currentFID = videos.keys()[0]
        self.updateVideoID(0)

        """# update lineEdits
        self.video_audio.setText('{id}_.wav'.format(id = currentFID))
        self.video_first_frame.setText(videos[currentFID]["frames"][0])
        self.video_last_frame.setText('{id}_{total}.jpg'.format(total = len(videos[currentFID]["frames"]), id = currentFID))

        if self.auto_fps():
          self.video_fps.setText(str(self.getFPS(currentFID)))"""

      # unblock signals
      self.video_id.blockSignals(False)

  def getFPS(self, id):
    duration = 0.0

    with contextlib.closing(wave.open(cfg["path"] + '\\{id}_.wav'.format(id = id), 'r')) as f:
      frames = f.getnframes()
      rate = f.getframerate()
      duration = len(videos[id]["frames"]) / (frames / float(rate * f.getnchannels())) / 2

    return float('{0:.3f}'.format(duration))

  def deleteVideos(self):
    #TODO: ask before delete

    fid = str(self.video_id.currentText())
    if len(fid) > 0 and videos.get(fid):
      for i in videos[fid]["frames"]:
        os.remove(cfg["path"] + "\\" + i)

  def updateVideoID(self, index):
    fid = str(self.video_id.currentText())

    global currentFID
    currentFID = fid

    if len(fid) > 0 and videos.get(fid):
      audio = '{id}_.wav'.format(id = fid)
      self.video_audio.setText(audio)
      self.video_first_frame.setText(videos[fid]["frames"][0])

      total = len(videos[fid]["frames"]) if len(videos[fid]["frames"]) >= 1000 else '0' + str(len(videos[fid]["frames"]))

      self.video_last_frame.setText('{id}_{total}.{ext}'.format(total = total, id = fid, ext = videos[fid]["ext"]))
      self.file_id.setText(fid + '_')

      self.video_cmd_line.setText(ffmpeg_cmdline)

      if self.auto_fps():
        self.video_fps.setText(str(self.getFPS(fid)))

  def renameFrames(self, fid):
    p = cfg["path"]
    reggae = re.compile(r'[0-9]{4,5}')

    sortedFrames = []

    fileName = '{id}_{fix}{sequence}.{ext}'
    filePath = '{path}\\{name}'

    for i in videos[fid]['frames']:
      m = reggae.search(str(i))
      vi = str(m.group(0))
      f = fileName.format(id = fid, fix = ('0' if len(vi) < 5 else ''), sequence = vi, ext = videos[fid]["ext"])
      sortedFrames.append(f)

    sortedFrames = sorted(sortedFrames)
    for i in sortedFrames:
      m = reggae.search(str(i))
      vi = str(m.group(0))
      f = fileName.format(id = fid, fix = ('0' if len(vi) < 5 else ''), sequence = vi, ext = videos[fid]["ext"])

      currentFrame = filePath.format(path = p, name = (fid + '_' + (vi[1:] if int(vi[0]) == 0 else vi) + '.' + videos[fid]["ext"]))
      newFrame = filePath.format(path = p, name = f)
      os.rename(currentFrame, newFrame)

  def renderVideo(self):
    fid = str(self.video_id.currentText())
    if len(fid) > 0 and videos.get(fid):

      sequence = 4
      
      if len(videos[fid]['frames']) >= 10000:
        sequence = 5

      frameLength = re.compile(r'_[0-9]{5}.(jpg|tga)')

      if sequence == 5 and not frameLength.search(videos[fid]['frames'][0]):
        self.renameFrames(fid)


      img = cfg["path"] + '\\{id}_%0{sequence}d.{ext}'.format(id = fid, sequence = sequence, ext = videos[fid]["ext"])
      audio = cfg["path"] + '\\{id}_.wav'.format(id = fid)


      fileName = self.video_render_name.text()
      if os.path.isfile('{render_path}\\{id}_{fileName}.mp4'.format(render_path = cfg["render_path"], fileName = fileName, id = fid)):
        #TODO: ask to remove the file
        os.remove('{render_path}\\{id}_{fileName}.mp4'.format(render_path = cfg["render_path"], fileName = fileName, id = fid))

      fps = self.getFPS(fid)

      args = ffmpeg_cmdline.format(id = fid, render_path = cfg["render_path"], arch = os_arch, fileName = fileName, frame = img, audio = audio, fps = cfg["fps"], bitrate = cfg["bitrate"]).split(' ')

      print args
      print platform.machine()

      self.RenderWindow.info = [{
        'file': fid + '_' + fileName + '.mp4',
        'size': '',
        'frames': len(videos[fid]["frames"]),
        'audio': fid + '_.wav'
      }]

      self.RenderWindow.args = args
      self.btn_render.setEnabled(False)

      self.RenderWindow.show()
      self.RenderWindow.start()

  def auto_fps(self):
    if self.fps_auto.isChecked():
      return True

    return False

#END: class: MainWindow

if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = MainWindow()
  window.show()
  sys.exit(app.exec_())