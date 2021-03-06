Step-by-Step
============

This document is used to list steps of reproducing Intel Optimized TensorFlow image recognition models tuning zoo result.

> **Note**: 
> Most of those models are both supported in Intel optimized TF 1.15.x and Intel optimized TF 2.x. We use 1.15.2 as an example.

# Prerequisite

### 1. Installation
  Recommend python 3.6 or higher version.

  ```Shell
  pip install -r requirements.txt
  
  ```

### 2. Prepare Dataset

  TensorFlow [models](https://github.com/tensorflow/models) repo provides [scripts and instructions](https://github.com/tensorflow/models/tree/master/research/slim#an-automated-script-for-processing-imagenet-data) to download, process and convert the ImageNet dataset to the TF records format.
  We also prepared related scripts in `imagenet_prepare` directory. To download the raw images, the user must create an account with image-net.org. If you have downloaded the raw data and preprocessed the validation data by moving the images into the appropriate sub-directory based on the label (synset) of the image. we can use below command ro convert it to tf records format.

  ```shell
  cd examples/tensorflow/image_recognition
  # convert validation subset
  bash prepare_dataset.sh --output_dir=./data --raw_dir=/PATH/TO/img_raw/val/ --subset=validation
  # convert train subset
  bash prepare_dataset.sh --output_dir=./data --raw_dir=/PATH/TO/img_raw/train/ --subset=train
  ```

### 3. Prepare pre-trained model
  In this version, Intel® Low Precision Optimization Tool just support PB file as input for TensorFlow backend, so we need prepared model pre-trained pb files. For some models pre-trained pb can be found in [IntelAI Models](https://github.com/IntelAI/models/tree/v1.6.0/benchmarks#tensorflow-use-cases), we can found the download link in README file of each model. And for others models in Google [models](https://github.com/tensorflow/models/tree/master/research/slim#pre-trained-models), we can get the pb files by convert the checkpoint files. We will give a example with Inception_v1 to show how to get the pb file by a checkpoint file.

  1. Download the checkpoint file from [here](https://github.com/tensorflow/models/tree/master/research/slim#pre-trained-models)
  ```shell
  wget http://download.tensorflow.org/models/inception_v1_2016_08_28.tar.gz
  tar -xvf inception_v1_2016_08_28.tar.gz
  ```

  2. Exporting the Inference Graph
  ```shell
  git clone https://github.com/tensorflow/models
  cd models/research/slim
  python export_inference_graph.py \
          --alsologtostderr \
          --model_name=inception_v1 \
          --output_file=/tmp/inception_v1_inf_graph.pb
  ```
  > Please note: The ImageNet dataset has 1001, the VGG and ResNet V1 final layers have only 1000 outputs rather than 1001. So we need add the `--labels_offset=1` flag in the inference graph exporting command.

  3. Use [Netron](https://lutzroeder.github.io/netron/) to get the input/output layer name of inference graph pb, for Inception_v1 the output layer name is `InceptionV1/Logits/Predictions/Reshape_1`

  4. Freezing the exported Graph, please use the tool `freeze_graph.py` in [tensorflow v1.15.2](https://github.com/tensorflow/tensorflow/blob/v1.15.2/tensorflow/python/tools/freeze_graph.py) repo 
  ```shell
  python freeze_graph.py \
          --input_graph=/tmp/inception_v1_inf_graph.pb \
          --input_checkpoint=./inception_v1.ckpt \
          --input_binary=true \
          --output_graph=./frozen_inception_v1.pb \
          --output_node_names=InceptionV1/Logits/Predictions/Reshape_1
  ```

# Run

> *Note*: 
> The model name with `*` means it comes from [models](https://github.com/tensorflow/models/tree/master/research/slim#pre-trained-models), please follow the step [Prepare pre-trained model](#3-prepare-pre-trained-model) to get the pb files.
> The densenet-series comes from [tensorflow-densenet](https://github.com/pudae/tensorflow-densenet), please also follow the step [Prepare pre-trained model](#3-prepare-pre-trained-model) to get the pb files or use openvino download tools.
   ```shell
   git clone https://github.com/openvinotoolkit/open_model_zoo.git
   cd open_model_zoo/tools/downloader
   pip install -r requirements.in
   python downloader.py --name densenet-{121|161|169}-tf -o /PATH/TO/MODEL
   ```

### 1. ResNet50 V1.0

  Download pre-trained PB
  ```shell
  wget https://storage.googleapis.com/intel-optimized-tensorflow/models/v1_6/resnet50_fp32_pretrained_model.pb
  ```

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=resnet50v1.0 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/resnet50_fp32_pretrained_model.pb --output_model=./ilit_resnet50_v1.pb
  ```

### 2. ResNet50 V1.5

  Download pre-trained PB
  ```shell
  wget https://zenodo.org/record/2535873/files/resnet50_v1.pb
  ```

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=resnet50v1.5 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/resnet50_v1.pb --output_model=./ilit_resnet50_v15.pb
  ```

### 3. ResNet101

  Download pre-trained PB
  ```shell
  wget https://storage.googleapis.com/intel-optimized-tensorflow/models/v1_6/resnet101_fp32_pretrained_model.pb
  ```

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=resnet101 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/resnet101_fp32_pretrained_model.pb --output_model=./ilit_resnet101.pb
  ```

### 4. MobileNet V1

  Download pre-trained PB
  ```shell
  wget https://storage.googleapis.com/intel-optimized-tensorflow/models/v1_6/mobilenet_v1_1.0_224_frozen.pb
  ```

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=mobilenetv1 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/mobilenet_v1_1.0_224_frozen.pb --output_model=./ilit_mobilenetv1.pb
  ```

### 5. MobileNet V2*

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=mobilenetv2 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/frozen_mobilenet_v2.pb --output_model=./ilit_mobilenetv2.pb
  ```

### 6. Inception V1*

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=inception_v1 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/frozen_inception_v1.pb --output_model=./ilit_inceptionv1.pb
  ```

### 7. Inception V2*

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=inception_v2 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/frozen_inception_v2.pb --output_model=./ilit_inceptionv2.pb
  ```

### 8. Inception V3

  Download pre-trained PB
  ```shell
  wget https://storage.googleapis.com/intel-optimized-tensorflow/models/v1_6/inceptionv3_fp32_pretrained_model.pb
  ```

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=inception_v3 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/inceptionv3_fp32_pretrained_model.pb --output_model=./ilit_inceptionv3.pb
  ```

### 9. Inception V4

  Download pre-trained PB
  ```shell
  wget https://storage.googleapis.com/intel-optimized-tensorflow/models/v1_6/inceptionv4_fp32_pretrained_model.pb
  ```

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=inception_v4 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/inceptionv4_fp32_pretrained_model.pb --output_model=./ilit_inceptionv4.pb
  ```

### 10. Inception ResNet V2*

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=inception_resnet_v2 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/frozen_inception_resnet_v2.pb --output_model=./ilit_irv2.pb
  ```

### 11. VGG 16*

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=vgg16 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/frozen_vgg16.pb --output_model=./ilit_vgg16.pb
  ```

### 12. VGG 19*

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=vgg19 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/frozen_vgg19.pb --output_model=./ilit_vgg19.pb
  ```

### 13. ResNet v2 50

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=resnetv2_50 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/frozen_resnet50v2_50.pb --output_model=./ilit_resnetv2_50.pb
  ```

### 14. ResNet v2 101

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=resnetv2_101 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/frozen_resnetv2_101.pb --output_model=./ilit_resnetv2_101.pb
  ```

### 15. ResNet v2 152

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=resnetv2_152 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/frozen_resnetv2_152.pb --output_model=./ilit_resnetv2_152.pb
  ```

### 16. Densenet-121

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=densenet121 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/densenet121.pb --output_model=./ilit_densenet121
  ```

### 17. Densenet-161

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=densenet161 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/densenet161.pb --output_model=./ilit_densenet161
  ```

### 18. Densenet-169

  ```Shell
  cd examples/tensorflow/image_recognition
  bash run_tuning.sh --topology=densenet169 --dataset_location=/PATH/TO/imagenet/ \
          --input_model=/PATH/TO/densenet169.pb --output_model=./ilit_densenet169
  ```

Examples of enabling Intel® Low Precision Optimization Tool auto tuning on TensorFlow ResNet50 V1.5
=======================================================

This is a tutorial of how to enable a TensorFlow image recognition model with Intel® Low Precision Optimization Tool.

# User Code Analysis

Intel® Low Precision Optimization Tool supports two usages:

1. User specifies fp32 "model", calibration dataset "q_dataloader", evaluation dataset "eval_dataloader" and metric in tuning.metric field of model-specific yaml config file.

2. User specifies fp32 "model", calibration dataset "q_dataloader" and a custom "eval_func" which encapsulates the evaluation dataset and metric by itself.

As ResNet50 V1.5 is a typical image recognition model, use Top-K as metric which is built-in supported by Intel® Low Precision Optimization Tool. So here we integrate Tensorflow [ResNet50 V1.5](https://github.com/IntelAI/models/tree/v1.6.0/models/image_recognition/tensorflow/resnet50v1_5/inference) in [IntelAI Models](https://github.com/IntelAI/models/tree/v1.6.0) with Intel® Low Precision Optimization Tool by the first use case for simplicity. 

### Write Yaml config file

In examples directory, there is a template.yaml. We could remove most of items and only keep mandotory item for tuning. 


```
# resnet50_v1_5.yaml

framework:
  - name: tensorflow
    inputs: input_tensor
    outputs: softmax_tensor

calibration:                                         
  - iterations: 5, 10
    algorithm:
        activation: minmax

tuning:
    metric:  
      - topk: 1
    accuracy_criterion:
      - relative: 0.01  
    timeout: 0
    random_seed: 9527
```

Here we choose topk built-in metric and set accuracy target as tolerating 0.01 relative accuracy loss of baseline. The default tuning strategy is basic strategy. The timeout 0 means early stop as well as a tuning config meet accuracy target.

### prepare

There are three preparation steps in here:
1. Prepare environment
```shell
pip install intel-tensorflow==1.15.2 ilit
```
2. Get the model source code
```shell
git clone -b v1.6.0 https://github.com/IntelAI/models intelai_models
cd intelai_models/models/image_recognition/tensorflow/resnet50v1_5/inference
```
3. Prepare the ImageNet dataset and pretrainined PB file
```shell
wget https://zenodo.org/record/2535873/files/resnet50_v1.pb
```
4. Add load graph and dataloader part in `eval_image_classifier_inference.py`, which needed in Intel® Low Precision Optimization Tool
```python
def load_graph(model_file):
  """This is a function to load TF graph from pb file

  Args:
      model_file (string): TF pb file local path

  Returns:
      graph: TF graph object
  """
  graph = tf.Graph()
  graph_def = tf.compat.v1.GraphDef()

  import os
  file_ext = os.path.splitext(model_file)[1]

  with open(model_file, "rb") as f:
    if file_ext == '.pbtxt':
      text_format.Merge(f.read(), graph_def)
    else:
      graph_def.ParseFromString(f.read())
  with graph.as_default():
    tf.import_graph_def(graph_def, name='')

  return graph

class Dataloader(object):
  """This is a example class that wrapped the model specified parameters,
    such as dataset path, batch size.
    And more importantly, it provides the ability to iterate the dataset.
  Yields:
      tuple: yield data and label 2 numpy array
  """
  def __init__(self, data_location, subset, input_height, input_width,
                batch_size, num_cores, resize_method='crop'):
    self.batch_size = batch_size
    self.subset = subset
    self.dataset = datasets.ImagenetData(data_location)
    self.total_image = self.dataset.num_examples_per_epoch(self.subset)
    self.preprocessor = self.dataset.get_image_preprocessor()(
        input_height,
        input_width,
        batch_size,
        num_cores,
        resize_method)
    self.n = int(self.total_image / self.batch_size)

  def __iter__(self):
    images, labels, filenames = self.preprocessor.minibatch(self.dataset, subset=self.subset, cache_data=False)
    with tf.compat.v1.Session() as sess:
        for i in range(self.n):
            yield sess.run([images, labels])
```

### code update

After completed preparation steps, we just need add a tuning part in `eval_classifier_optimized_graph` class.

```python
  def auto_tune(self):
    """This is Intel® Low Precision Optimization Tool tuning part to generate a quantized pb

    Returns:
        graph: it will return a quantized pb
    """
    import ilit
    fp32_graph = load_graph(self.args.input_graph)
    tuner = ilit.Tuner(self.args.config)
    dataloader = Dataloader(self.args.data_location, 'validation',
                            RESNET_IMAGE_SIZE, RESNET_IMAGE_SIZE, self.args.batch_size,
                            num_cores=self.args.num_cores,
                            resize_method='crop')
    q_model = tuner.tune(
                        fp32_graph,
                        q_dataloader=dataloader,
                        eval_func=None,
                        eval_dataloader=dataloader)
    return q_model
```

Finally, add one line in `__main__` function of `eval_image_-classifier_inference.py` to use Intel® Low Precision Optimization Tool by yourself as below.
```python
q_graph = evaluate_opt_graph.auto_tune()
```
We can use below cmd to test it.
```shell
python eval_image_classifier_inference.py -b 10 -a 28 -e 1 -m resnet50_v1_5 \
        -g /PATH/TO/resnet50_v1.pb -d /PATH/TO/imagenet/
```
The tune() function will return a best quantized model during timeout constrain.
