import os, errno, io
from queue import Queue
from threading import Thread
import numpy as np
import tensorflow as tf
from deeplab_resnet import DeepLabResNetModel, decode_labels, dense_crf
from PIL import Image


class DeepLabRequest:
    def __init__(self, prefix, input_file_name, result_file_name):
        self.prefix = prefix
        self.input_file_name = input_file_name
        self.result_file_name = result_file_name


class DeepLab:
    def __init__(self, gpu_ids, root_path, img_mean, storage):
        self.on_finished = None
        self.storage = storage

        self.img_mean = np.array(img_mean, dtype=np.float32)
        self.root_path = root_path
        # self.upload_path = os.path.join(root_path, "upload")
        # self.result_path = os.path.join(root_path, "results")
        # os.makedirs(self.upload_path, exist_ok=True)
        # os.makedirs(self.result_path, exist_ok=True)
        self.weights_model_path = os.path.join(root_path, "deeplab_resnet.ckpt")
        if not os.path.exists(self.weights_model_path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.weights_model_path)

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
        # type: (DeepLabRequest) -> bool
        self.request_queue.put(request)
        return True

    def join_all(self):
        self.request_queue.join()

    def load_img(self, path):
        jpg_data = self.storage.get(path)
        jpg_tensor = tf.placeholder(dtype=tf.string)
        return jpg_tensor, jpg_data

    def save_img(self, path, img):
        ret = io.BytesIO()
        img.save(ret, format='PNG')
        self.storage.put(path, ret.getvalue())


class _Worker(Thread):
    def __init__(self, request_queue, gpu_id, manager):
        # type: (Queue, int, DeepLab) -> None
        super(_Worker, self).__init__()
        self.request_queue = request_queue
        self.initialized = False
        self.gpu_id = gpu_id
        self.manager = manager
        self.sess = None

    def run(self):
        while True:
            req = self.request_queue.get()
            if req is None:
                break
            self._process(req)
            if self.manager.on_finished is not None:
                self.manager.on_finished(req.prefix, "deeplab")
            self.request_queue.task_done()

    def _process(self, req):
        # type: (DeepLabRequest) -> None
        # img_path = os.path.join(self.manager.upload_path, req.prefix, req.input_file_name)
        # ret_path = os.path.join(self.manager.result_path, req.prefix, req.result_file_name)
        # Prepare image.
        # img_rgb = tf.image.decode_jpeg(tf.read_file(img_path), channels=3)
        jpg_tensor, jpg_data = self.manager.load_img(req.input_file_name)
        img_rgb = tf.image.decode_jpeg(jpg_tensor, channels=3)
        # Convert RGB to BGR.
        img_r, img_g, img_b = tf.split(img_rgb, 3, axis=2)
        img_bgr = tf.cast(tf.concat([img_b, img_g, img_r], 2), dtype=tf.float32)
        # Extract mean.
        img_bgr -= self.manager.img_mean

        # Create network.
        net = DeepLabResNetModel({'data': tf.expand_dims(img_bgr, dim=0)}, is_training=False)
        tf.get_variable_scope().reuse_variables()

        # Which variables to load.
        restore_var = tf.global_variables()

        # Predictions.
        raw_output = net.layers['fc1_voc12']
        raw_output_up = tf.image.resize_bilinear(raw_output, tf.shape(img_bgr)[0:2, ])

        # CRF.
        raw_output_up = tf.nn.softmax(raw_output_up)
        raw_output_up = tf.py_func(dense_crf, [raw_output_up, tf.expand_dims(img_rgb, dim=0)], tf.float32)
        raw_output_up = tf.argmax(raw_output_up, dimension=3)
        pred = tf.expand_dims(raw_output_up, dim=3)

        if not self.initialized:
            # Set up TF session and initialize variables.
            config = tf.ConfigProto(device_count={'GPU': self.gpu_id})
            config.gpu_options.allow_growth = True
            self.sess = tf.Session(config=config)
            init = tf.global_variables_initializer()

            self.sess.run(init)

            # Load weights.
            loader = tf.train.Saver(var_list=restore_var)
            loader.restore(self.sess, self.manager.weights_model_path)
            self.initialized = True

        # Perform inference.
        preds = self.sess.run(pred, feed_dict={jpg_tensor: jpg_data})

        msk = decode_labels(preds)
        im = Image.fromarray(msk[0])
        mask_path = req.result_file_name
        # os.makedirs(os.path.dirname(mask_path), exist_ok=True)
        # im.save(mask_path)
        self.manager.save_img(mask_path, im)
