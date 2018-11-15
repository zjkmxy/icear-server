from __future__ import print_function
import os, sys, signal
sys.path.insert(0, 'fast-style-transfer')

# adding import path for the directory above this sctip (for deeplab modules)
myPath = os.path.dirname(sys.argv[0])
rootPath = os.path.join(myPath,'..')
uploadPath =  os.path.join(rootPath, "upload")
resultsPath = os.path.join(rootPath, "results")
modelsDir = os.path.join(rootPath, 'ce-models');

sys.path.append(rootPath)

import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path, random, string
import uuid
from tornado.options import define, options
from queue import Queue
from threading import Thread
from datetime import datetime
import re
import time
import datetime
from PIL import Image
import tensorflow as tf
import numpy as np
import transform, numpy as np, vgg, pdb, os
import scipy.misc
import tensorflow as tf
from utils import save_img, get_img, exists, list_files
from collections import defaultdict
import time
import json
import subprocess
import numpy
import glob
from moviepy.video.io.VideoFileClip import VideoFileClip
import moviepy.video.io.ffmpeg_writer as ffmpeg_writer

BATCH_SIZE = 4
DEVICE = '/gpu:0'

port = 8889
# ipaddress = "131.179.142.7"
ipaddress = "127.0.0.1"
hostUrl = "http://"+ipaddress+":"+str(port)
define("port", default=port, help="run on the given port", type=int)

allModels = []
sampleImg = None
sampleImgW = None
sampleImgH = None
quit = False
debug = False

workerQueues = {}

#******************************************************************************
def timestampMs():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/upload", UploadHandler),
            (r"/result/(.*)", tornado.web.StaticFileHandler, {"path" : "./results"}),
            (r"/info", InfoHandler),
            (r"/status", StatusHandler)
        ]
        tornado.web.Application.__init__(self, handlers)
        
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        global allModels
        self.render("upload_form_1.html", imageWidth = sampleImgW, imageHeight = sampleImgH, models=allModels)
        
class UploadHandler(tornado.web.RequestHandler):
    def post(self):
        global workerQueues, debug
        print("New upload request "+str(self.request))

        modelName = self.get_argument('style', True)
        if isinstance(modelName, bool):
            modelName = 'mixed-media-7'
            print("Style was not specified. Using default "+modelName)
        
        if modelName in workerQueues:
            if workerQueues[modelName].qsize() > 0:
                print("Pending request in progress... REPLY 423")
                self.set_status(423)
                self.finish("service is not available. try again later")
                return

        fileData = self.request.files['file'][0]
        original_fname = fileData['filename']
        extension = os.path.splitext(original_fname)[1]
        fileID = str(uuid.uuid4())
        fname = os.path.join(uploadPath, fileID)
        imageFile = open(fname, 'wb')
        imageFile.write(fileData['body'])

        if modelName in workerQueues:
            workerQueues[modelName].put(fileID)
            print("Submitted request " + fileID + " for segmentation processing with style "+modelName);
            self.finish(hostUrl+"/result/"+fileID+".png")
        else:
            print("Submitted style is not supported: ", modelName)
            self.set_status(406)
            self.finish("Style not supported: "+ str(modelName))

class InfoHandler(tornado.web.RequestHandler):
    def get(self):
        global allModels, sampleImgW, sampleImgH
        infoString = json.dumps({ \
            'models': [os.path.basename(x) for x in allModels], \
            'res': { 'w': sampleImgW, 'h' : sampleImgH} \
            })
        self.finish(infoString)

class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        self.finish("ok")

def fstWorker(requestQueue, sampleImg, checkpoint_dir, device_t='/gpu:0'):
    global sampleImgH, sampleImgW
    modelName = os.path.basename(checkpoint_dir)
    print("Starting worker with model "+modelName+" on GPU "+device_t + "...")

    def printWorker(msg):
         print(str(timestampMs())+" [gpu-worker-"+ modelName+"] " + msg)

    img_shape = get_img(sampleImg).shape

    g = tf.Graph()
    batch_size = 1 # min(len(paths_out), batch_size)
    curr_num = 0
    soft_config = tf.ConfigProto(allow_soft_placement=True)
    soft_config.gpu_options.allow_growth = True
    with g.as_default(), g.device(device_t), \
            tf.Session(config=soft_config) as sess:
        batch_shape = (batch_size,) + img_shape
        img_placeholder = tf.placeholder(tf.float32, shape=batch_shape,
                                         name='img_placeholder')

        preds = transform.net(img_placeholder)
        saver = tf.train.Saver()
        if os.path.isdir(checkpoint_dir):
            ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
            if ckpt and ckpt.model_checkpoint_path:
                saver.restore(sess, ckpt.model_checkpoint_path)
            else:
                raise Exception("No checkpoint found at "+checkpoint_dir)
        else:
            saver.restore(sess, checkpoint_dir)

        while not quit:
            printWorker("Waiting for requests...")
            fileId = requestQueue.get()
            if fileId == "quit-"+modelName:
                printWorker("Received quit command")
                break
            
            t1 = timestampMs()
            printWorker("Received request for style transfer: "+fileId)
            path = os.path.join(uploadPath, fileId)

            printWorker("Reading image "+path)
            img = get_img(path)

            if img.shape[0] != sampleImgH or img.shape[1] != sampleImgW:
                print("Incoming image " + str(img.shape[0]) + "x" + str(img.shape[1])+ " size does not match configured size " + str(sampleImgH) + "x" + str(sampleImgW))
            else:
                printWorker("Running style transfer...")
                X = np.zeros(batch_shape, dtype=np.float32)
                X[0] = img
                _preds = sess.run(preds, feed_dict={img_placeholder:X})

                pathOutTmp = os.path.join(resultsPath, fileId+"-tmp.png")
                save_img(pathOutTmp, _preds[0])

                pathOut = os.path.join(resultsPath, fileId+".png")
                os.rename(pathOutTmp, pathOut)
                t2 = timestampMs()

                printWorker("Saved result at "+pathOut)
                printWorker("Processing took "+str(t2-t1)+"ms")

    printWorker("Completed")

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('--checkpoint', type=str,
                        dest='checkpoint_dir',
                        help='dir or .ckpt file to load checkpoint from',
                        metavar='CHECKPOINT', required=True)

    parser.add_argument('--in-path', type=str,
                        dest='in_path',help='dir or file to transform',
                        metavar='IN_PATH', required=True)

    help_out = 'destination (dir or file) of transformed file or files'
    parser.add_argument('--out-path', type=str,
                        dest='out_path', help=help_out, metavar='OUT_PATH',
                        required=True)

    parser.add_argument('--device', type=str,
                        dest='device',help='device to perform compute on',
                        metavar='DEVICE', default=DEVICE)

    parser.add_argument('--batch-size', type=int,
                        dest='batch_size',help='batch size for feedforwarding',
                        metavar='BATCH_SIZE', default=BATCH_SIZE)

    parser.add_argument('--allow-different-dimensions', action='store_true',
                        dest='allow_different_dimensions', 
                        help='allow different image dimensions')

    return parser

def check_opts(opts):
    exists(opts.checkpoint_dir, 'Checkpoint not found!')
    exists(opts.in_path, 'In path not found!')
    if os.path.isdir(opts.out_path):
        exists(opts.out_path, 'out dir not found!')
        assert opts.batch_size > 0

####
def signal_handler(signum, frame):
    global is_closing
    print('Received stop signal, exiting...')
    tornado.ioloop.IOLoop.instance().stop()
    quit = True

def main():
    global allModels, sampleImg, sampleImgW, sampleImgH, port, workerQueues, debug
    signal.signal(signal.SIGINT, signal_handler)
    if len(sys.argv) > 1 and sys.argv[1] == 'debug':
        debug = True
        port = 8890
        print("**********DEBUG MODE************************************************************")
        print("Portnumber: "+str(port))
    # allModels = ["mixed-media-7"]
    modelsList = os.listdir(modelsDir)
    # this is a hack for pre-trained author's models
    # they are just single files with extension .ckpt
    authorModels = glob.glob(os.path.join(modelsDir, '*', '*.ckpt'))
    allModels = []
    for m in modelsList:
        files = os.listdir(os.path.join(modelsDir, m))
        if len(files) > 1: # that's our models
            allModels.append(m)
        elif len(files) == 1:
            allModels.append(os.path.join(m, files[0]))

    # TODO: this can be expanded to utilize more than one GPU
    nGpus = 1
    for m in allModels:
        k = os.path.basename(m)
        workerQueues[k] = Queue()
        print("Added queue for "+k)

    workers = {}
    nWorkers = len(allModels)
    #sampleImgName = 'sample1620x1080.jpg'
    #sampleImgName = 'sample1920x1080.jpg'
    # sampleImgName = 'sample1280x720.jpg'
    sampleImgName = 'sample420x236.jpg'
    # sampleImgName = 'sample840x560.jpg'
    # sampleImgName = 'sample420x280.jpg'
    sampleImg = os.path.join(rootPath, sampleImgName)
    pat = '\D*(?P<w>[0-9]+)x(?P<h>[0-9]+).jpg'
    r  = re.compile(pat)
    m = r.match(sampleImg)
    if m:
        sampleImgW = int(m.group('w'))
        sampleImgH = int(m.group('h'))

    for i in range(0,nWorkers):
        modelName = allModels[i]
        # k = os.path.basename(modelName)
        k = os.path.basename(modelName)
        allModels[i] = k
        checkpoint = os.path.join(modelsDir, modelName)
        worker = Thread(target=fstWorker, args=(workerQueues[k], sampleImg, checkpoint, ))
        worker.start()
        workers[k] = worker

    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()
    
    print("Will terminate GPU workers...")

    for m in allModels:
        k = os.path.basename(m)
        workerQueues[k].put("quit-"+str(k))

if __name__ == "__main__":
    main()
