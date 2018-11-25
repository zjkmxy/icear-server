import os, errno
from queue import Queue
from threading import Thread
import numpy as np
import tensorflow as tf
import fast_style_transfer.transform as transform
from fast_style_transfer.utils import save_img, get_img
import imageio

DEVICE_PREFIX = '/gpu:'


class FstRequest:
    def __init__(self, prefix, model_name, input_file_name, result_file_name):
        self.prefix = prefix
        self.model_name = model_name
        self.input_file_name = input_file_name
        self.result_file_name = result_file_name


class Fst:
    def __init__(self, gpu_ids, root_path, img_shape, storage):
        self.on_finished = None
        self.img_shape = img_shape
        self.storage = storage

        # Set paths.
        self.root_path = root_path
        # self.upload_path = os.path.join(root_path, "upload")
        # self.result_path = os.path.join(root_path, "results")
        # os.makedirs(self.upload_path, exist_ok=True)
        # os.makedirs(self.result_path, exist_ok=True)
        self.models_dir = os.path.join(root_path, "ce-models")
        if not os.path.exists(self.models_dir):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.models_dir)

        # Load models
        self.models = {}
        for m in os.listdir(self.models_dir):
            if m[0] == '.':
                continue
            files = os.listdir(os.path.join(self.models_dir, m))
            if len(files) > 0:
                self.models[m] = os.path.join(self.models_dir, m, files[0])

        # Set up workers
        self.request_queue = Queue()
        self.workers = [_Worker(self.request_queue, gpu_id, self) for gpu_id in gpu_ids]
        for worker in self.workers:
            worker.start()

    def shutdown(self):
        for _ in self.workers:
            self.request_queue.put(None)
        for worker in self.workers:
            worker.join()

    def send(self, request):
        # type: (FstRequest) -> bool
        if request.model_name not in self.models:
            return False
        # img_path = os.path.join(self.upload_path, request.prefix, request.input_file_name)
        img_path = request.input_file_name
        # img = get_img(img_path)
        img = self.load_img(img_path)
        if img.shape[0] != self.img_shape[0] or img.shape[1] != self.img_shape[1]:
            return False

        self.request_queue.put(request)
        return True

    def join_all(self):
        self.request_queue.join()

    def load_img(self, path):
        return imageio.imread(self.storage.get(path), pilmode="RGB")

    def save_img(self, path, img):
        img = np.clip(img, 0, 255).astype(np.uint8)
        self.storage.put(path, imageio.imwrite(imageio.RETURN_BYTES, img, "PNG-PIL"))


class _Worker(Thread):
    def __init__(self, request_queue, gpu_id, manager):
        # type: (Queue, int, Fst) -> None
        super(_Worker, self).__init__()
        self.request_queue = request_queue
        self.initialized = False
        self.gpu_id = gpu_id
        self.manager = manager

        self.cur_model = None
        self.sess = None
        batch_size = 1
        self.batch_shape = (batch_size,) + self.manager.img_shape
        self.img_placeholder = None
        self.preds = None

    def run(self):
        g = tf.Graph()
        device_t = DEVICE_PREFIX + str(self.gpu_id)
        soft_config = tf.ConfigProto(allow_soft_placement=True)
        soft_config.gpu_options.allow_growth = True
        with g.as_default(), g.device(device_t), tf.Session(config=soft_config) as sess:
            self.sess = sess
            self.img_placeholder = tf.placeholder(tf.float32,
                                                  shape=self.batch_shape,
                                                  name='img_placeholder')
            self.preds = transform.net(self.img_placeholder)

            while True:
                req = self.request_queue.get()
                if req is None:
                    break
                if req.model_name in self.manager.models:
                    self._process(req)
                if self.manager.on_finished is not None:
                    self.manager.on_finished(req.prefix, req.model_name)
                self.request_queue.task_done()

    def _load_model(self, model_file):
        saver = tf.train.Saver()
        saver.restore(self.sess, model_file)

    def _process(self, req):
        # type: (FstRequest) -> None
        if req.model_name != self.cur_model:
            self._load_model(self.manager.models[req.model_name])
        # img_path = os.path.join(self.manager.upload_path, req.prefix, req.input_file_name)
        # ret_path = os.path.join(self.manager.result_path, req.prefix, req.result_file_name)
        img_path = req.input_file_name
        ret_path = req.result_file_name
        # Prepare image.
        # img = get_img(img_path)
        img = self.manager.load_img(img_path)
        x = np.zeros(self.batch_shape, dtype=np.float32)
        x[0] = img
        _preds = self.sess.run(self.preds, feed_dict={self.img_placeholder: x})
        # os.makedirs(os.path.dirname(ret_path), exist_ok=True)
        # save_img(ret_path, _preds[0])
        self.manager.save_img(ret_path, _preds[0])
